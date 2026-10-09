"""PBIP SUMX product/BLANK contracts exercised through production SQL."""
import json
import re
import sqlite3
import sys
from pathlib import Path

import pytest
from jinja2 import Environment

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'superset'))
from neoretail_bootstrap.pbip_overview.cost_blank import (
    COST_OPERANDS, apply_cost_blank, cost_sum_sql, default_cost_blank_sql,
)
from neoretail_bootstrap.pbip_overview.conversion_context import overview_projection

CASES = [
    ('valid', [(2, 3)], 6), ('a_blank', [(None, 3)], None),
    ('b_blank', [(2, None)], None), ('both_blank', [(None, None)], None),
    ('mixed', [(2, 3), (None, 3), (2, None)], 6),
    ('all_blank', [(None, 3), (2, None)], None), ('empty', [], None),
    ('zero', [(0, 3)], 0), ('zero_plus_blank', [(0, 3), (None, 3)], 0),
    ('zero_times_blank', [(0, None)], None), ('negative', [(-2, 3)], -6),
]


@pytest.mark.parametrize('operand', COST_OPERANDS.values())
@pytest.mark.parametrize('case,rows,expected', CASES)
def test_raw_row_product_sum(operand, case, rows, expected):
    with sqlite3.connect(':memory:') as c:
        c.execute(f'CREATE TABLE history({operand},avg_price_cost)')
        c.executemany('INSERT INTO history VALUES(?,?)', rows)
        actual = c.execute('SELECT '+cost_sum_sql(operand)+' FROM history').fetchone()[0]
        assert actual == expected


@pytest.fixture
def context():
    c = sqlite3.connect(':memory:'); c.row_factory = sqlite3.Row
    c.execute("ATTACH DATABASE ':memory:' AS gold")
    columns = [v[2:] for v in overview_projection('b.sales_qty_sum').split(',')]
    c.execute('CREATE TABLE gold.nr_pbip_overview_semantic_v3('+','.join(columns)+')')
    c.executescript('''
CREATE TABLE gold.nr_pbip_overview_history(data,id_customer,tp_activity_level,id_location,id_item,volume_unidades,estoque_medio,avg_price_cost,item,descricao_marca,hierarquia_1,hierarquia_2,hierarquia_3);
CREATE TABLE gold.dim_local(id_customer,id_location,id_retailer,cnpj,rede,bandeira,uf,cidade,tipo_local,loja,regiao);
CREATE TABLE gold.dim_catalogo_local(id_customer,id_retailer,cnpj,rede,bandeira,tipo_local);
CREATE TABLE gold.dim_itens(id_customer,id_item);
CREATE TABLE gold.dim_conversao(id_customer,id_item,nm_measure,conversion_rate);
INSERT INTO gold.dim_local VALUES(290,'L','R','C','LOCAL','LOCAL BAND','MA','CITY','LOJA','LOJA','REGION');
INSERT INTO gold.dim_catalogo_local VALUES(290,'R','C','CAT','CAT BAND','LOJA');
INSERT INTO gold.dim_itens VALUES(290,'I'),(290,'J');
INSERT INTO gold.dim_conversao VALUES(290,'I','unidade',99),(290,'J','unidade',7),(290,'I','quilograma',44);
''')
    yield c, columns
    c.close()


def seed(context, rows, date='2026-10-01', item='I'):
    c, columns = context
    for a, b in rows:
        c.execute('INSERT INTO gold.nr_pbip_overview_history VALUES(?,290,\'F\',\'L\',?,?,?,?,?,\'BRAND\',\'H1\',\'H2\',\'H3\')', (date,item,a,a,b,item))
    old = sum((a or 0)*(b or 0) for a,b in rows)
    for scope, activity in [('all',None), ('activity','F')]:
        values = {'data':date,'id_customer':290,'tp_activity_level':activity,'semantic_scope':scope,'nm_measure':'unidade','sales_cost_sum':old,'stock_cost_sum':old,'sellout_sum':123,'stock_qty_sum':999,'sales_qty_sum':456}
        c.execute('INSERT INTO gold.nr_pbip_overview_semantic_v3 VALUES('+','.join('?' for _ in columns)+')', [values.get(k) for k in columns])


def run(context, masks=None):
    c,_ = context; masks = masks or {'nm_measure':['unidade']}
    selected = masks.get('nm_measure',[])
    env = Environment(); env.filters['where_in'] = lambda v:'('+','.join("'"+str(x).replace("'","''")+"'" for x in v)+')'
    q = env.from_string(default_cost_blank_sql()).render(
        selected=selected, conversion_filters=[{'val':selected or ['unidade']}],
        get_filters=lambda col,remove_filter=False:[{'op':'IN','val':masks[col]}] if col in masks else [],
    )
    q = re.sub(r'::(?:float8|text|bigint|date)', '', q)
    return [dict(r) for r in c.execute(q)]


@pytest.mark.parametrize('cost', COST_OPERANDS)
@pytest.mark.parametrize('case,rows,expected', CASES)
def test_frozen_default_mart_blank_repair(context, cost, case, rows, expected):
    seed(context, rows)
    result = run(context)
    assert len(result)==2
    assert all(r[cost]==expected for r in result)
    assert all(r['sellout_sum']==123 and r['stock_qty_sum']==999 and r['sales_qty_sum']==456 for r in result)


@pytest.mark.parametrize('cost', COST_OPERANDS)
@pytest.mark.parametrize('period,months,expected', [
    ('MTD',['2026-10-01'],None), ('previous',['2026-09-01'],0),
    ('U3M',['2026-07-01','2026-08-01','2026-09-01'],2),
])
def test_period_null_zero_and_fixed_division(context,cost,period,months,expected):
    seed(context,[(None,3)],'2026-10-01')
    seed(context,[(0,3)],'2026-09-01')
    seed(context,[(None,3)],'2026-08-01')
    seed(context,[(2,3)],'2026-07-01')
    rows=[r[cost] for r in run(context) if r['semantic_scope']=='all' and r['data'] in months]
    numbers=[x for x in rows if x is not None]
    actual=sum(numbers)/(3 if period=='U3M' else 1) if numbers else None
    assert actual==expected


def test_product_and_ap_preserve_key_filter_not_arithmetic_factor(context):
    seed(context,[(None,3)],item='I')
    c,_=context
    c.execute("INSERT INTO gold.nr_pbip_overview_history VALUES('2026-10-01',290,'F','L','J',0,0,3,'J','BRAND','H1','H2','H3')")
    # Old frozen zero remains real zero when a zero product is included.
    assert run(context)[0]['sales_cost_sum']==0
    assert run(context,{'nm_measure':['unidade'],'item':['I']})[0]['sales_cost_sum'] is None
    # AP changes eligible item keys; factor 44 is never multiplied into costs.
    c.execute("UPDATE gold.nr_pbip_overview_semantic_v3 SET nm_measure='quilograma'")
    assert run(context,{'nm_measure':['quilograma']})[0]['sales_cost_sum'] is None


def test_cost_source_change_is_limited_and_checked():
    from neoretail_bootstrap.pbip_overview.semantics import overview_semantic_sql
    sql=overview_semantic_sql()
    assert 'SUM(volume_unidades * avg_price_cost)' in sql
    assert 'SUM(estoque_medio * avg_price_cost)' in sql
    assert 'SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))' not in sql
    assert 'SUM(COALESCE(estoque_medio,0)*COALESCE(avg_price_cost,0))' not in sql
    with pytest.raises(ValueError): apply_cost_blank('unrelated SQL')
