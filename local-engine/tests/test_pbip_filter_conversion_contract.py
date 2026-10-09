"""Execute PBIP key-set/filter contracts with real dimension rows in memory.

No KPI values are expected here. Fixtures identify existing locations and factors;
duplicates are retained to prove that a bridge must filter keys, not multiply facts.
"""
import importlib
import json
import sqlite3
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'superset'))
FIXTURE=json.loads((Path(__file__).parent/'fixtures/pbip_filters_conversion_real_rows_20261008.json').read_text('utf-8'))

def module(name):return importlib.import_module('neoretail_bootstrap.pbip_overview.'+name)

@pytest.fixture
def db():
    conn=sqlite3.connect(':memory:');conn.execute("ATTACH DATABASE ':memory:' AS gold")
    columns='id_customer INTEGER,id_location TEXT,id_retailer TEXT,cnpj TEXT,rede TEXT,bandeira TEXT,tipo_local TEXT,uf TEXT'
    for table,key in [('dim_local','local'),('dim_catalogo_local','catalog')]:
        conn.execute('CREATE TABLE gold.'+table+'('+columns+')')
        for row in FIXTURE[key]:conn.execute('INSERT INTO gold.'+table+' VALUES(?,?,?,?,?,?,?,?)',tuple(row[k] for k in ['id_customer','id_location','id_retailer','cnpj','rede','bandeira','tipo_local','uf']))
    conn.execute('CREATE TABLE gold.dim_conversao(id_customer INTEGER,id_item TEXT,nm_measure TEXT,conversion_rate REAL)')
    for row in FIXTURE['factors']:conn.execute('INSERT INTO gold.dim_conversao VALUES(?,?,?,?)',(row['id_customer'],str(row['id_item']),row['nm_measure'],float(row['conversion_rate'])))
    conn.execute('CREATE TABLE gold.dim_itens(id_customer INTEGER,id_item TEXT,item TEXT,descricao_marca TEXT,hierarquia_1 TEXT,hierarquia_2 TEXT,hierarquia_3 TEXT)')
    for row in FIXTURE['items']:conn.execute('INSERT INTO gold.dim_itens VALUES(?,?,?,?,?,?,?)',tuple(str(row[k]) if k=='id_item' else row[k] for k in ['id_customer','id_item','item','descricao_marca','hierarquia_1','hierarquia_2','hierarquia_3']))
    yield conn
    conn.close()

def eligible(db, row, **kwargs):
    sql=module('filter_context').location_membership('f',**kwargs)
    return db.execute('SELECT '+sql+' FROM (SELECT ? id_customer,? id_location) f',(row['id_customer'],row['id_location'])).fetchone()[0]

def test_catalog_band_filters_local_through_shared_cnpj(db):
    local=FIXTURE['local'][0]
    catalog=next(r for r in FIXTURE['catalog'] if r['cnpj']==local['cnpj'] and r['bandeira']!=local['bandeira'])
    predicate="pc.bandeira = '"+catalog['bandeira'].replace("'","''")+"'"
    assert eligible(db,local,catalog_predicates=predicate)==1
    assert local['bandeira']!=catalog['bandeira']  # old direct local IN is false

def test_selector_catalog_band_is_not_substituted_by_local_band(db):
    for col in ('cidade','loja','regiao'):db.execute('ALTER TABLE gold.dim_local ADD COLUMN '+col+' TEXT')
    sql=module('filter_context').selector_options_sql().split(' UNION ALL ',1)[0].replace('::text','')
    local=FIXTURE['local'][0]
    sql+=" AND pl.id_location='"+local['id_location']+"'"
    options={r[0] for r in db.execute('SELECT bandeira FROM ('+sql+')')}
    expected={r['bandeira'] for r in FIXTURE['catalog'] if r['cnpj']==local['cnpj']}
    assert options==expected
    assert any(b!=local['bandeira'] for b in options)  # old local-source selector fails

def test_same_tenant_contracted_and_noncontracted_location(db):
    assert FIXTURE['gold_aux_retailer_equality']
    valid=FIXTURE['local'][0];invalid=FIXTURE['uncontracted_location']
    assert valid['id_customer']==invalid['id_customer']==290
    assert valid['id_retailer'] in FIXTURE['contracted_retailers']
    assert invalid['id_retailer'] not in FIXTURE['contracted_retailers']
    assert eligible(db,valid)==1 and eligible(db,invalid)==0

def test_page_local_rede_blank_is_excluded(db):
    row=FIXTURE['local'][0]
    db.execute('UPDATE gold.dim_local SET rede=NULL WHERE id_location=?',(row['id_location'],))
    assert eligible(db,row)==0

def test_many_to_many_catalog_duplicates_do_not_multiply_fact_keys(db):
    db.execute('INSERT INTO gold.dim_catalogo_local SELECT * FROM gold.dim_catalogo_local')
    selected=[r['id_location'] for r in FIXTURE['local'] if eligible(db,r)]
    assert selected==[r['id_location'] for r in FIXTURE['local']]

def test_bridge_intersection_supports_both_filter_directions(db):
    sql=module('filter_context').location_membership('f',local_predicates="pl.uf='MA'",catalog_predicates="pc.bandeira='MATEUS SUPERMERCADOS'")
    selected=[]
    for row in FIXTURE['local']:
        if db.execute('SELECT '+sql+' FROM (SELECT ? id_customer,? id_location) f',(290,row['id_location'])).fetchone()[0]:selected.append(row['id_location'])
    expected=[r['id_location'] for r in FIXTURE['local'] if r['uf']=='MA' and any(c['cnpj']==r['cnpj'] and c['bandeira']=='MATEUS SUPERMERCADOS' for c in FIXTURE['catalog'])]
    assert selected==expected and selected

def test_factor_is_from_dimension_not_monthly_fact_items(db):
    sql=module('conversion_context').dimension_factors_sql()
    assert 'fato_' not in sql and 'history_filtered' not in sql
    actual=db.execute('SELECT conversion_rate FROM ('+sql+") WHERE nm_measure='quilograma'").fetchone()[0]
    assert actual==max(float(r['conversion_rate']) for r in FIXTURE['factors'])

def test_wrong_product_restricted_max_fails_on_real_dimension_rows(db):
    old=db.execute("SELECT MIN(conversion_rate) FROM gold.dim_conversao WHERE nm_measure='quilograma'").fetchone()[0]
    correct=db.execute('SELECT conversion_rate FROM ('+module('conversion_context').dimension_factors_sql()+") WHERE nm_measure='quilograma'").fetchone()[0]
    assert old<correct
    # This is a SQL/context witness, never an observed Power BI KPI value.

def test_item_filter_cannot_flow_backwards_into_conversion_max(db):
    # Corrects a mistaken contract derivation, not an expected KPI value:
    # TOM confirms DIM_CONVERSAO -> DIM_ITENS, OneDirection, Many/Many.
    sql=module('conversion_context').dimension_factors_sql()
    assert 'dim_itens' not in sql
    actual=db.execute('SELECT conversion_rate FROM ('+sql+") WHERE nm_measure='quilograma'").fetchone()[0]
    assert actual==max(float(r['conversion_rate']) for r in FIXTURE['factors'])

def test_valor_has_no_invented_conversion_factor(db):
    sql=module('conversion_context').dimension_factors_sql()
    assert not db.execute('SELECT * FROM ('+sql+") WHERE nm_measure='valor'").fetchall()
    assert 'conversion_rate=1' not in sql.replace(' ','')

def test_missing_selected_mode_factor_stays_blank(db):
    sql=module('conversion_context').dimension_factors_sql()
    actual=db.execute('SELECT MAX(conversion_rate) FROM ('+sql+") WHERE nm_measure='modo_sem_fator'").fetchone()[0]
    assert actual is None

def test_sales_quantity_conversion_order_is_pbip_sumx():
    contract=json.loads((Path(__file__).parent/'fixtures/pbip_lactalis_overview_20261008.json').read_text('utf-8'))
    assert 'SUMX(' in contract['measures']['Venda Historico']['dax']
    assert 'VOLUME_UNIDADES] * Fator' in contract['measures']['Venda Historico']['dax']
    conversion=module('conversion_context')
    sql=conversion.quantity_by_activity_sql(conversion.dimension_factors_sql())
    assert 'SUM(h.volume_unidades*f.conversion_rate)' in sql
    assert 'SUM(h.volume_unidades)*' not in sql

def test_conversion_independent_giro_uses_history_and_ignores_ap():
    heads=module('headlines')
    sql=heads.giro_semantic_sql()
    assert "get_filters('nm_measure', remove_filter=True)" in sql
    detail=heads.giro_detail_sql()
    assert 'SUM(h.giro) FILTER(WHERE h.giro>0)' in detail
    assert 'COUNT(h.giro) FILTER(WHERE h.giro>0)' in detail
    assert 'dim_conversao' in detail and "pbip_conv.nm_measure='unidade'" in detail

def test_selected_conversion_filters_fact_items_without_join_multiplication(db):
    row=FIXTURE['items'][0]
    predicate=module('conversion_context').converted_item_membership('f',mode='quilograma')
    actual=db.execute('SELECT '+predicate+' FROM (SELECT 290 id_customer,? id_item) f',(str(row['id_item']),)).fetchone()[0]
    assert actual==1
    db.execute('INSERT INTO gold.dim_conversao SELECT * FROM gold.dim_conversao')
    assert db.execute('SELECT '+predicate+' FROM (SELECT 290 id_customer,? id_item) f',(str(row['id_item']),)).fetchone()[0]==1

def test_no_matching_conversion_item_is_excluded(db):
    predicate=module('conversion_context').converted_item_membership('f',mode='modo_sem_fator')
    row=FIXTURE['items'][0]
    assert db.execute('SELECT '+predicate+' FROM (SELECT 290 id_customer,? id_item) f',(str(row['id_item']),)).fetchone()[0]==0

@pytest.mark.parametrize('alias',['f','h','c','o'])
def test_conversion_membership_is_correlated_for_each_fact_alias(db,alias):
    predicate=module('conversion_context').converted_item_membership(alias,mode='quilograma')
    row=FIXTURE['items'][0]
    for key,expected in [(str(row['id_item']),1),('item_not_in_dimension',0)]:
        assert db.execute('SELECT '+predicate+' FROM (SELECT 290 id_customer,? id_item) '+alias,(key,)).fetchone()[0]==expected

def test_osa_input_changes_keep_frozen_formula_and_ignore_activity_for_causes():
    sql=module('semantics').osa_semantic_sql()
    assert 'SUM(qtd_problemas_osa)::bigint osa_problem_sum' in sql
    assert 'b.loss_qty_sum*f.conversion_rate*(b.price_sum/b.price_count)' in sql
    cause=sql.split('cause_filtered AS (',1)[1].split('loss_base AS',1)[0]
    assert 'gold.dim_conversao' in cause
    assert "get_filters('tp_activity_level'" not in cause

def test_tvd_ivd_apply_nonstore_filter_to_both_bridge_ends():
    predicate=module('filter_context').location_membership('f',exclude_nonstore=True)
    assert "pl.tipo_local NOT IN ('DEPÓSITO','CD','LOJA VIRTUAL')" in predicate
    assert "pc.tipo_local NOT IN ('DEPÓSITO','CD','LOJA VIRTUAL')" in predicate
