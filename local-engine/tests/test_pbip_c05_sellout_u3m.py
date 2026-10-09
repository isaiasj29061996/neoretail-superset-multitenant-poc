import sqlite3,json,re,sys
from pathlib import Path
import pytest
from jinja2 import Environment
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'superset'))
from neoretail_bootstrap.pbip_overview.sellout_u3m import full_u3m_sql

@pytest.fixture
def db():
 c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row;c.execute("ATTACH DATABASE ':memory:' AS gold");c.create_function('date_trunc',2,lambda g,d:d[:7]+'-01')
 c.executescript('''CREATE TABLE gold.dim_local(id_customer,id_location,id_retailer,cnpj,rede,bandeira,uf,cidade,tipo_local,loja,regiao);
 CREATE TABLE gold.dim_catalogo_local(id_customer,id_retailer,cnpj,rede,bandeira,tipo_local);
 CREATE TABLE gold.dim_itens(id_customer,id_item);
 CREATE TABLE gold.dim_conversao(id_customer,id_item,nm_measure,conversion_rate);
 CREATE TABLE gold.nr_pbip_calendar(id_customer,data,data_at,u3m);
 CREATE TABLE gold.nr_pbip_overview_history(id_customer,data,id_item,id_location,regiao,faturamento,volume_unidades,avg_sales_price,item,tp_activity_level,descricao_marca,hierarquia_1,hierarquia_2,hierarquia_3);
 CREATE TABLE gold.frozen_monthly(data,id_customer,semantic_scope,sales_cost_sum,sales_qty_sum,stock_cost_sum,stock_qty_sum,giro_sum_positive,giro_count_positive,osa_problem_sum,osa_active_sum);
 INSERT INTO gold.dim_itens VALUES(290,'I');INSERT INTO gold.dim_conversao VALUES(290,'I','unidade',1);
 INSERT INTO gold.nr_pbip_calendar VALUES(290,'2026-07-01','2026-10-07',1),(290,'2026-08-01','2026-10-07',1),(290,'2026-09-01','2026-10-07',1);
 INSERT INTO gold.frozen_monthly VALUES('2026-07-01',290,'all',12,20,30,4,5,6,7,8);''')
 yield c;c.close()

def add(c,region,date,rev,volume,price):
 loc='L'+str(region)
 if not c.execute('SELECT 1 FROM gold.dim_local WHERE id_location=?',(loc,)).fetchone():
  c.execute('INSERT INTO gold.dim_local VALUES(290,?,"R",?,"LOCAL","LOCAL BAND","MA","CITY","LOJA",?,?)',(loc,loc,loc,region))
  c.execute('INSERT INTO gold.dim_catalogo_local VALUES(290,"R",?,"CAT","CAT BAND","LOJA")',(loc,))
 c.execute('INSERT INTO gold.nr_pbip_overview_history VALUES(290,?,"I",?,?,?,?,?,"ITEM","F","BRAND","H1","H2","H3")',(date,loc,region,rev,volume,price))

def run(c,masks=None):
 masks=masks or {'nm_measure':['unidade']};env=Environment();env.filters['where_in']=lambda v:'('+','.join("'"+str(x).replace("'","''")+"'" for x in v)+')'
 sql=env.from_string(full_u3m_sql('SELECT * FROM gold.frozen_monthly')).render(get_filters=lambda col,remove_filter=False:[{'op':'IN','val':masks[col]}] if col in masks else [])
 sql=re.sub(r'::(?:float8|text|date|bigint)','',sql)
 return dict(c.execute(sql).fetchone())

@pytest.mark.parametrize('revenue,expected',[(20,20),(0,40),(None,40),(-20,40)])
def test_exact_revenue_branch(db,revenue,expected):
 add(db,'R','2026-07-01',revenue,10,4);assert run(db)['sellout_sum']==expected

def test_region_iteration_not_global_revenue_branch(db):
 add(db,'POS','2026-07-01',100,10,4);add(db,'FALLBACK','2026-07-01',0,20,3)
 assert run(db)['sellout_sum']==160  # global revenue >0 incorrectly returns 100

def test_price_volume_change_full_context_not_sum_monthly(db):
 add(db,'R','2026-07-01',0,10,2);add(db,'R','2026-08-01',0,30,6)
 assert run(db)['sellout_sum']==160
 assert 10*2+30*6==200 and 160!=200

def test_conversion_applies_factor_twice_and_not_product_restricted(db):
 db.execute('INSERT INTO gold.dim_conversao VALUES(290,"OTHER","unidade",3)')
 add(db,'R','2026-07-01',0,10,4)
 assert run(db,{'nm_measure':['unidade'],'item':['ITEM']})['sellout_sum']==360

def test_blank_region_participates(db):
 add(db,None,'2026-07-01',0,10,4);add(db,'R','2026-07-01',100,1,1)
 assert run(db)['sellout_sum']==140

def test_blank_fallback_does_not_gain_defaults(db):
 add(db,'R','2026-07-01',None,None,None);assert run(db)['sellout_sum'] is None

def test_only_u3m_domain_and_frozen_costs_preserved(db):
 add(db,'R','2026-07-01',100,1,1);add(db,'R','2026-10-01',900,1,1)
 r=run(db);assert r['sellout_sum']==100 and r['sales_cost_sum']==12 and r['stock_cost_sum']==30

def test_no_selection_keeps_revenue_branch_and_blank_factor(db):
 add(db,'R','2026-07-01',100,1,1);assert run(db,{'item':['ITEM']})['sellout_sum']==100
 db.execute('UPDATE gold.nr_pbip_overview_history SET faturamento=0');assert run(db,{'item':['ITEM']})['sellout_sum'] is None
