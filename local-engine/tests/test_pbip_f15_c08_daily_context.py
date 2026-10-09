"""Execute production TVD/IVD SQL on independent controlled relational cases."""
import sys,sqlite3,json,re
from pathlib import Path
import pytest
from jinja2 import Environment
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'superset'))
from neoretail_bootstrap.pbip_overview.daily_context import daily_context_sql

@pytest.fixture
def conn():
 c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row;c.execute("ATTACH DATABASE ':memory:' AS gold")
 c.create_function('date_trunc',2,lambda grain,d:d[:7]+'-01')
 c.executescript('''CREATE TABLE gold.dim_local(id_customer,id_location,id_retailer,cnpj,rede,bandeira,tipo_local,uf,cidade,loja,regiao);
 CREATE TABLE gold.dim_catalogo_local(id_customer,id_retailer,cnpj,rede,bandeira,tipo_local);
 CREATE TABLE gold.dim_itens(id_customer,id_item,item,descricao_marca,hierarquia_1,hierarquia_2,hierarquia_3);
 CREATE TABLE gold.dim_conversao(id_customer,id_item,nm_measure,conversion_rate);
 CREATE TABLE gold.fato_ivd_tvd(id_customer,id_time,id_item,id_location,tp_activity_level,tvd_simplificado,ivd_simplificado);
 CREATE TABLE gold.calculo_oportunidades(id_customer,id_item,id_location,max_tp_activity_level,regra_critico,tvd,ivd);
 CREATE TABLE gold.nr_pbip_calendar(id_customer,data);
 INSERT INTO gold.dim_local VALUES(290,'L','R','CNPJ','Rede local','MIX ATACADO','LOJA','MA','CITY','Loja','REG');
 INSERT INTO gold.dim_catalogo_local VALUES(290,'R','CNPJ','Rede catalogo','MATEUS SUPERMERCADOS','LOJA');''')
 for item in ['A','B','C']:
  c.execute('INSERT INTO gold.dim_itens VALUES(290,?,?,"BRAND","H1","H2","H3")',(item,item))
 for item,mode in [('A','unidade'),('B','quilograma'),('C','litro')]:c.execute('INSERT INTO gold.dim_conversao VALUES(290,?,?,999)',(item,mode))
 yield c;c.close()

def add(c,date,item,tvd,ivd=None,loc='L'):
 c.execute('INSERT INTO gold.fato_ivd_tvd VALUES(290,?,?,?,"F",?,?)',(date,item,loc,tvd,ivd))
 c.execute('INSERT INTO gold.nr_pbip_calendar SELECT 290,? WHERE NOT EXISTS(SELECT 1 FROM gold.nr_pbip_calendar WHERE data=?)',(date,date))

def run(c,metric='tvd',masks=None):
 masks=masks or {}
 env=Environment();env.filters['where_in']=lambda v:'('+','.join('NULL' if x is None else "'"+str(x).replace("'","''")+"'" for x in v)+')'
 sql=env.from_string(daily_context_sql(metric)).render(get_filters=lambda col,remove_filter=False:[{'op':'IN','val':masks[col]}] if col in masks else [])
 sql=re.sub(r'::(?:text|date|float8|bigint)','',sql)
 return [dict(r) for r in c.execute(sql)]

@pytest.mark.parametrize('mode,date,value',[('unidade','2026-09-10',17),('quilograma','2026-09-20',7),('litro','2026-09-05',3)])
def test_date_depends_on_ap_but_final_sum_clears_ap(conn,mode,date,value):
 add(conn,'2026-09-05','C',3);add(conn,'2026-09-10','A',10);add(conn,'2026-09-10','B',7);add(conn,'2026-09-20','B',7)
 r=run(conn,masks={'nm_measure':[mode]})
 assert [(x['data'],x['tvd']) for x in r]==[(date,value)]
 # At unit date the B row contributes despite AP=unit; conversion_rate=999 is ignored.

@pytest.mark.parametrize('values,expected',[( [None,None],None),([None,0],0),([0],0),([None,4],4),([],None),([None],None)])
def test_sum_null_vs_zero_in_lastnonblank(conn,values,expected):
 add(conn,'2026-09-01','A',2)
 for v in values:add(conn,'2026-09-30','A',v)
 r=run(conn,masks={'nm_measure':['unidade']})
 assert r[0]['data']==('2026-09-01' if expected is None else '2026-09-30')
 assert r[0]['tvd']==(2 if expected is None else expected)
 old=conn.execute('SELECT SUM(COALESCE(tvd_simplificado,0)) FROM gold.fato_ivd_tvd WHERE id_time="2026-09-30"').fetchone()[0]
 assert old==(0 if values and expected is None else expected)

def test_all_blank_or_no_rows_stays_blank(conn):
 assert run(conn)==[]
 add(conn,'2026-09-30','A',None,None)
 assert run(conn,masks={'nm_measure':['unidade']})==[]

def test_tvd_and_ivd_choose_independent_dates(conn):
 add(conn,'2026-09-01','A',5,8);add(conn,'2026-09-30','A',0,None)
 assert run(conn,'tvd')[0]['data']=='2026-09-30'
 assert run(conn,'ivd')[0]['data']=='2026-09-01'

def test_no_selection_keeps_page_not_valor_but_not_unit_default(conn):
 add(conn,'2026-09-10','A',1);add(conn,'2026-09-20','B',2)
 assert run(conn)[0]['data']=='2026-09-20'
 assert run(conn,masks={'nm_measure':['unidade']})[0]['data']=='2026-09-10'

def test_equal_dates_and_mode_without_latest_global_row(conn):
 add(conn,'2026-09-10','A',1);add(conn,'2026-09-10','B',2);add(conn,'2026-09-30','C',3)
 assert run(conn,masks={'nm_measure':['unidade']})[0]['data']==run(conn,masks={'nm_measure':['quilograma']})[0]['data']=='2026-09-10'

def test_product_filter_remains_after_all_ap(conn):
 add(conn,'2026-09-10','A',10);add(conn,'2026-09-10','B',7)
 masks={'nm_measure':['unidade'],'item':['A'],'rede':['Rede catalogo'],'bandeira':['MATEUS SUPERMERCADOS']}
 assert run(conn,masks=masks)[0]['tvd']==10
 assert run(conn,masks={**masks,'nm_measure':['quilograma']})==[]

def test_sibling_nonstore_filter_is_not_used_by_lastnonblank(conn):
 conn.execute('UPDATE gold.dim_local SET tipo_local="CD"')
 add(conn,'2026-09-20','A',10)
 r=run(conn,masks={'nm_measure':['unidade']})
 assert r[0]['data']=='2026-09-20' and r[0]['tvd'] is None

def test_u3m_is_three_monthly_dates_and_fixed_denominator(conn):
 add(conn,'2026-07-15','A',9);add(conn,'2026-08-15','A',None);add(conn,'2026-09-15','A',3)
 rows=run(conn,masks={'nm_measure':['unidade']})
 assert [(r['data'],r['tvd']) for r in rows]==[('2026-07-15',9),('2026-09-15',3)]
 assert sum(r['tvd'] for r in rows)/3==4

def test_date_candidates_respect_calendar_domain(conn):
 add(conn,'2026-09-01','A',2);add(conn,'2026-09-30','A',7)
 conn.execute('DELETE FROM gold.nr_pbip_calendar WHERE data="2026-09-30"')
 assert run(conn)[0]['data']=='2026-09-01'

def test_pbip_auxiliary_periods_are_three_month_evaluations():
 f=json.loads((Path(__file__).parent/'fixtures/pbip_f15_c08_dax_20261008.json').read_text('utf-8'))
 for name in ['TVD U3M','IVD U3M']:
  dax=f['measures'][name]['dax']
  assert dax.count('CALCULATE(')==3
  assert all("[M-"+str(i)+"] = TRUE()" in dax for i in [1,2,3])
  assert 'DIVIDE(M1 + M2 + M3, 3)' in dax

def test_pbip_lastnonblank_inner_sum_is_not_coalesced_or_ap_cleared():
 f=json.loads((Path(__file__).parent/'fixtures/pbip_f15_c08_dax_20261008.json').read_text('utf-8'))
 for name in ['TVD','IVD']:
  dax=f['measures'][name]['dax'];inner=dax.split('LASTNONBLANK(',1)[1].split('ALL(AP_CONVERSAO)',1)[0]
  assert 'CALCULATE(' in inner and 'SUM(FATOS_PARTICULAR_TVD_IVD['+name+'_SIMPLIFICADO])' in inner
  assert 'COALESCE' not in dax and 'ALL(' not in inner

def test_before_global_sql_has_wrong_unit_date_and_after_restores_sum_context(conn):
 from neoretail_bootstrap.pbip_overview.headlines import headline_detail_sql
 add(conn,'2026-09-10','A',10);add(conn,'2026-09-10','B',7);add(conn,'2026-09-20','B',7)
 env=Environment();env.filters['where_in']=lambda v:'('+','.join("'"+str(x)+"'" for x in v)+')'
 old=env.from_string(headline_detail_sql()).render(get_filters=lambda *a,**k:[])
 old=re.sub(r'::(?:text|date|float8|bigint)','',old)
 old_rows=[dict(x) for x in conn.execute(old)]
 assert max(x['data'] for x in old_rows)=='2026-09-20'
 assert run(conn,masks={'nm_measure':['unidade']})[0]['data']=='2026-09-10'
 assert run(conn,masks={'nm_measure':['unidade']})[0]['tvd']==17
