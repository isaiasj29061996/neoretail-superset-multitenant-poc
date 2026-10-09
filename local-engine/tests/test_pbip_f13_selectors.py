"""Selector key-set contracts; no production data or KPI expected values change."""
import importlib
import json
import sqlite3
import sys
from pathlib import Path
import pytest
from jinja2 import Environment

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'superset'))
DATA=json.loads((Path(__file__).parent/'fixtures/pbip_filters_conversion_real_rows_20261008.json').read_text('utf-8'))

def selectors():
    return importlib.import_module('neoretail_bootstrap.pbip_overview.selectors')

def render(sql, selections=None):
    selections=selections or {}
    env=Environment()
    env.filters['where_in']=lambda xs:'('+','.join('NULL' if x is None else "'"+str(x).replace("'","''")+"'" for x in xs)+')'
    return env.from_string(sql).render(get_filters=lambda col,**kwargs:[selections[col] if isinstance(selections[col],dict) else {'op':'IN','val':selections[col]}] if col in selections else []).replace('::text','').replace(' ILIKE ',' LIKE ')

@pytest.fixture
def db():
    conn=sqlite3.connect(':memory:');conn.execute("ATTACH ':memory:' AS gold")
    dims=('id_customer','id_location','id_retailer','cnpj','rede','bandeira','tipo_local','uf','cidade','loja','regiao')
    for table,key in [('dim_local','local'),('dim_catalogo_local','catalog')]:
        conn.execute('CREATE TABLE gold.'+table+'('+','.join(c+' '+('INTEGER' if c=='id_customer' else 'TEXT') for c in dims)+')')
        for row in DATA[key]:
            conn.execute('INSERT INTO gold.'+table+' VALUES('+','.join('?' for _ in dims)+')',tuple(row.get(c) for c in dims))
    conn.execute('CREATE TABLE gold.dim_itens(id_customer INTEGER,id_item TEXT,item TEXT,descricao_marca TEXT,hierarquia_1 TEXT,hierarquia_2 TEXT,hierarquia_3 TEXT)')
    for row in DATA['items']:
        conn.execute('INSERT INTO gold.dim_itens VALUES(?,?,?,?,?,?,?)',tuple(str(row[c]) if c=='id_item' else row[c] for c in ('id_customer','id_item','item','descricao_marca','hierarquia_1','hierarquia_2','hierarquia_3')))
    conn.execute('CREATE TABLE gold.dim_conversao(id_customer INTEGER,id_item TEXT,nm_measure TEXT,conversion_rate REAL)')
    for row in DATA['factors']:conn.execute('INSERT INTO gold.dim_conversao VALUES(?,?,?,?)',(row['id_customer'],str(row['id_item']),row['nm_measure'],float(row['conversion_rate'])))
    conn.execute('CREATE TABLE gold.dim_nivel_atividade(id_customer INTEGER,tp_activity_level TEXT,nm_activity_level TEXT)')
    pbip=json.loads((Path(__file__).parent/'fixtures/pbip_f13_selectors_pbip_20261008.json').read_text('utf-8'))
    for row in pbip['activity_gold_rows']:conn.execute('INSERT INTO gold.dim_nivel_atividade VALUES(?,?,?)',(row['id_customer'],row['tp_activity_level'],row['nm_activity_level']))
    yield conn
    conn.close()

def options(db,target,selections=None):
    sql=render(selectors().option_sql(target),selections)
    return {r[0] for r in db.execute('SELECT '+target+' FROM ('+sql+')')}

def test_before_native_local_selection_does_not_restrict_catalog():
    from neoretail_bootstrap.overview.filters import overview_native_filters
    old=overview_native_filters([3],53)
    band=next(x for x in old if x['targets'][0]['column']['name']=='bandeira')
    assert 'NATIVE_FILTER-neoretail-loja' not in band['cascadeParentIds']
    assert 'loja' in selectors().context_dependencies('bandeira')

def test_band_to_cnpj_to_local_real_witness(db):
    assert DATA['local'][0]['id_location']=='10060213'
    assert DATA['local'][0]['bandeira']=='MIX ATACADO'
    assert 'MA' in options(db,'uf',{'bandeira':['MATEUS SUPERMERCADOS']})
    assert options(db,'uf',{'bandeira':['MATEUS SUPERMERCADOS']})=={'MA'}

def test_local_to_cnpj_to_catalog(db):
    assert options(db,'bandeira',{'uf':['MA']})=={'MATEUS SUPERMERCADOS','MIX ATACADO'}

def test_duplicates_do_not_duplicate_options(db):
    expected=options(db,'bandeira',{'uf':['MA']})
    db.execute('INSERT INTO gold.dim_catalogo_local SELECT * FROM gold.dim_catalogo_local')
    sql=render(selectors().option_sql('bandeira'),{'uf':['MA']})
    rows=db.execute('SELECT bandeira FROM ('+sql+')').fetchall()
    assert len(rows)==len(set(rows))==len(expected)

def test_rede_null_and_contract_combined(db):
    db.execute("UPDATE gold.dim_local SET rede=NULL WHERE id_location='10060213'")
    assert options(db,'uf',{'bandeira':['MATEUS SUPERMERCADOS']})=={'MA'}
    db.execute("UPDATE gold.dim_local SET rede=NULL WHERE id_location='10060214'")
    assert options(db,'uf',{'bandeira':['MATEUS SUPERMERCADOS']})==set()

def test_uncontracted_catalog_key_is_not_an_option(db):
    row=DATA['uncontracted_location']
    assert row['id_retailer'] not in DATA['contracted_retailers']
    assert row['rede'] not in options(db,'rede')
    assert 'MATEUS SUPERMERCADOS' in options(db,'bandeira')

def test_ap_restricts_product_options(db):
    keys={str(x['id_item']) for x in DATA['factors'] if x['nm_measure']=='quilograma'}
    expected={x['item'] for x in DATA['items'] if str(x['id_item']) in keys}
    assert options(db,'item',{'nm_measure':['quilograma']})==expected
    assert options(db,'item',{'nm_measure':['hectolitro']})==set()

def test_product_never_filters_ap_options_or_factor(db):
    before=options(db,'nm_measure')
    assert options(db,'nm_measure',{'item':['absent']})==before
    from neoretail_bootstrap.pbip_overview.conversion_context import dimension_factors_sql
    sql=dimension_factors_sql()
    assert 'dim_itens' not in sql
    assert db.execute('SELECT MAX(conversion_rate) FROM ('+sql+')').fetchone()[0]==max(float(x['conversion_rate']) for x in DATA['factors'])

def test_multiple_selectors_intersect(db):
    assert options(db,'tipo_local',{'uf':['MA'],'bandeira':['MATEUS SUPERMERCADOS']})=={'LOJA'}
    assert options(db,'bandeira',{'uf':['PE'],'rede':['ARMAZMATEUS']})==set()

def test_no_selection_and_self_exclusion(db):
    assert options(db,'bandeira',{'bandeira':['impossible']})==options(db,'bandeira')
    assert options(db,'nm_measure')=={'quilograma'}

def test_async_search_is_not_discarded_like_own_selection(db):
    assert options(db,'bandeira',{'bandeira':{'op':'ILIKE','val':'%MATEUS%'}})=={'MATEUS SUPERMERCADOS'}
    assert options(db,'bandeira',{'bandeira':{'op':'ILIKE','val':'%does_not_exist%'}})==set()

def test_direction_groups_are_not_all_to_all():
    assert 'item' not in selectors().context_dependencies('rede')
    assert 'nm_measure' not in selectors().context_dependencies('bandeira')
    assert 'nm_measure' in selectors().context_dependencies('descricao_marca')
    assert 'item' not in selectors().context_dependencies('nm_measure')

def test_single_select_saved_unit_and_legacy_unchanged():
    filters=selectors().native_filters({c:53 for c in selectors().COLUMNS})
    mode=next(x for x in filters if x['targets'][0]['column']['name']=='nm_measure')
    assert not mode['controlValues']['multiSelect']
    assert mode['controlValues']['enableEmptyFilter']
    assert mode['defaultDataMask']['filterState']['value']==['unidade']
    assert all(x['cascadeParentIds']==[] for x in filters)

def test_activity_labels_preserve_existing_code_filter_contract():
    labels={'F':'Fast Mover','S':'Slow Mover'}
    filters=selectors().native_filters({c:53 for c in selectors().COLUMNS},labels)
    activity=next(x for x in filters if x['targets'][0]['column']['name']=='tp_activity_level')
    assert activity['controlValues']['pbipOptionValueCodes']=={'Fast Mover':['F'],'Slow Mover':['S']}
    assert activity['targets'][0]['column']['name']=='tp_activity_level'
    assert labels=={'F':'Fast Mover','S':'Slow Mover'}

def test_actual_duplicate_activity_names_group_both_codes(db):
    assert options(db,'tp_activity_level')=={'Fast Mover','Slow Mover','Ultra Slow Mover','New Mover','Não Informado'}
    pbip=json.loads((Path(__file__).parent/'fixtures/pbip_f13_selectors_pbip_20261008.json').read_text('utf-8'))
    labels={r['tp_activity_level']:r['nm_activity_level'] for r in pbip['activity_gold_rows']}
    f=next(x for x in selectors().native_filters({c:53 for c in selectors().COLUMNS},labels) if x['targets'][0]['column']['name']=='tp_activity_level')
    assert f['controlValues']['pbipOptionValueCodes']['Não Informado']==['I','W']

def test_item_hidden_measure_is_not_assumed_exists():
    pbip=json.loads((Path(__file__).parent/'fixtures/pbip_f13_selectors_pbip_20261008.json').read_text('utf-8'))
    literal=pbip['hidden_item_filter']['filters'][0]['filter']['Where'][0]['Condition']['Not']['Expression']['Comparison']
    assert literal['ComparisonKind']==0
    assert literal['Right']['Literal']['Value']=='null'
    assert literal['Left']['Measure']['Property']=='Filtro Historico Com Dados'
    dax=pbip['hidden_item_measure_full_tmdl']
    assert 'IF(TemDados > 0, 1, 0)' in dax
    assert 'REMOVEFILTERS(AP_CONVERSAO)' in dax
    assert 'REMOVEFILTERS(DIM_CATALOGO_LOCAL[Rede])' in dax
    assert 'REMOVEFILTERS(DIM_LOCAL[Rede])' in dax
    # Prove why NOT COUNTROWS>0 cannot be inferred from the measure name:
    # the measure returns zero for no rows, never BLANK. The serialized null
    # comparison still needs its own proven evaluator before zero is excluded.
    assert [1 if (rows or 0)>0 else 0 for rows in (None,0,1,10)]==[0,0,1,1]
    proof=selectors().ITEM_HIDDEN_FILTER
    assert proof['measure_returns']==[0,1]
    assert proof['serialized_operator']=='Not(ComparisonKind=0, Literal=null)'
    assert proof['status']=='UNPROVEN_NULL_COMPARISON'
    assert 'fato_' not in selectors().option_sql('item')

def test_page_opt_in_no_global_filter_config():
    from neoretail_bootstrap.overview.filters import overview_native_filters
    assert all('pbipContextParentIds' not in x['controlValues'] for x in overview_native_filters([3],53))
