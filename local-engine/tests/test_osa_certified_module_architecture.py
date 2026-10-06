"""OSA ownership, compatibility and parity against the pre-extraction baseline."""
import ast
import hashlib
import importlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from jinja2 import Environment, StrictUndefined

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'superset/neoretail_bootstrap/osa_certified'
sys.path.insert(0, str(ROOT / 'superset'))
BASELINE = json.loads((Path(__file__).parent / 'fixtures/osa_certified_modules_baseline.json').read_text(encoding='utf-8'))
from neoretail_bootstrap.osa_certified import semantics, matrices, filters, presentation


def normalized_ast(node):
    if isinstance(node, ast.AST):
        return {'type': type(node).__name__, **{key: normalized_ast(value) for key, value in ast.iter_fields(node) if value is not None and value != []}}
    if isinstance(node, list):
        return [normalized_ast(value) for value in node]
    if node is Ellipsis:
        return {"literal": "ellipsis"}
    return node


def definitions(path):
    return {node.name if isinstance(node, ast.FunctionDef) else node.targets[0].id: node
            for node in ast.parse(path.read_text(encoding='utf-8')).body
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)}


@pytest.mark.parametrize('key', BASELINE['symbols'])
def test_original_symbols_remain_ast_identical(key):
    owner, name = key.split('.')
    if owner == 'matrices': module = 'matrices'
    elif name in ('DASHBOARD_TITLE', 'DASHBOARD_SLUG', 'PREFIX'):
        module = None
    elif name in ('DIMENSION_OVERRIDES', '_dimension_nulls', '_measure_filter', '_period_filter'): module = 'filters'
    elif name in ('_top_params', '_cause_params', '_matrix_params'): module = 'presentation'
    else: module = 'semantics'
    path = PACKAGE / (module + '.py') if module else ROOT / 'superset/bootstrap_osa_industry_certified.py'
    digest = hashlib.sha256(json.dumps(normalized_ast(definitions(path)[name]), sort_keys=True).encode()).hexdigest()
    assert digest == BASELINE['symbols'][key]


@pytest.mark.parametrize('name', BASELINE['sql'])
def test_sql_is_byte_identical(name):
    assert getattr(semantics, name)().encode() == BASELINE['sql'][name].encode()


@pytest.mark.parametrize('column', BASELINE['matrix_sql'])
def test_matrix_sql_is_byte_identical(column):
    assert matrices.matrix_period_sql(column).encode() == BASELINE['matrix_sql'][column].encode()


def test_specs_layout_filters_and_scales_match_original():
    datasets = [SimpleNamespace(id=i) for i in range(1, 6)]
    matrix_datasets = {key: SimpleNamespace(id=10+i) for i, key in enumerate(matrices.MATRIX_SCOPES)}
    specs = presentation.chart_specs(*datasets[:3], matrix_datasets)
    assert len(specs) == 14
    assert [[key, ds.id, title, params, viz] for key, ds, title, params, viz in specs] == BASELINE['specs']
    charts = {spec[0]: SimpleNamespace(id=100+i, uuid='chart-'+str(i), slice_name='[OSA Certificada] '+spec[2]) for i, spec in enumerate(specs)}
    assert presentation.position_json(charts) == BASELINE['layout']
    assert filters.native_filters(*datasets[:3], matrix_datasets, *datasets[3:], charts) == BASELINE['filters']
    assert presentation.CSS == BASELINE['css']
    assert len(filters.WEEKLY_FILTER_COLUMNS) == 14
    assert '100.0*' in semantics.monthly_overview_sql()
    assert matrices.TABLE_OSA['d3Format'] == '.2%'
    assert matrices.TABLE_OSA['sqlExpression'] == '1 - SUM(problem_base)/NULLIF(SUM(active_base),0)'
    assert 'IS NOT DISTINCT FROM' in matrices.matrix_period_sql('regiao')


BUILDERS = [semantics.monthly_overview_sql, semantics.weekly_overview_sql, semantics.cause_period_sql,
            *[lambda column=column: matrices.matrix_period_sql(column) for column in BASELINE['matrix_sql']]]
DIMENSIONS = ('rede', 'bandeira', 'uf', 'cidade', 'tipo_local', 'loja', 'regiao', 'tp_activity_level',
              'item', 'descricao_marca', 'hierarquia_1', 'hierarquia_2', 'hierarquia_3')


def render(sql, selected):
    env = Environment(undefined=StrictUndefined)
    env.filters['where_in'] = lambda values: '(' + ', '.join("'" + str(value).replace("'", "''") + "'" for value in values) + ')'
    return env.from_string(sql).render(get_filters=lambda column, **kwargs: selected.get(column, []))


@pytest.mark.parametrize('builder', BUILDERS)
@pytest.mark.parametrize('dimension', DIMENSIONS)
@pytest.mark.parametrize('operator', ['IN', 'NOT IN'])
def test_dimensional_filters_render_with_joined_aliases(builder, dimension, operator):
    value = 'RJ' if dimension == 'uf' else 'test-item' if dimension == 'item' else 'test'
    sql = render(builder(), {dimension: [{'op': operator, 'val': [value]}]})
    alias = 'l.'+dimension if dimension in DIMENSIONS[:7] else 'i.'+dimension
    if dimension == 'tp_activity_level':
        assert 'o.max_tp_activity_level '+operator in sql
    else:
        assert alias+' '+operator+" ('"+value+"')" in sql
        assert ('dim_local l' if alias.startswith('l.') else 'dim_itens i') in sql
    assert '{%' not in sql and '{{' not in sql


@pytest.mark.parametrize('builder', BUILDERS)
@pytest.mark.parametrize('operator', [None, 'IN', 'NOT IN'])
def test_measure_default_and_operators(builder, operator):
    selected = {} if operator is None else {'nm_measure': [{'op': operator, 'val': ['hectolitro']}]}
    sql = render(builder(), selected)
    assert ("m.nm_measure='unidade'" if operator is None else "m.nm_measure "+operator+" ('hectolitro')") in sql


def test_temporal_sources_and_default_scope_are_preserved():
    assert semantics.PERIODS == (('MTD', 1), ('Mês Anterior', 2), ('U3M', 3), ('YTD', 5))
    assert 'MAX(data)::date AS latest_data\n  FROM gold.fato_mensal_causa_osa' in semantics.cause_period_sql()
    assert 'MAX(mes_ano)::date AS latest_data\n  FROM gold.fato_historico' in matrices.matrix_period_sql('regiao')
    assert 'r.week_rank<=13' in semantics.weekly_overview_sql()
    assert filters._period_filter(42, [1, 2, 3, 4])['scope']['excluded'] == [1, 2, 3, 4]


def test_package_has_no_runtime_persistence_or_bootstrap_dependencies():
    for path in PACKAGE.glob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            modules = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module or ''] if isinstance(node, ast.ImportFrom) else []
            assert all(not name.startswith(('superset', 'sqlalchemy', 'bootstrap_')) for name in modules), path
            if isinstance(node, ast.ImportFrom): assert all(alias.name != '*' for alias in node.names)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {'commit', 'flush', 'execute', 'query', 'add'}


def test_explicit_compatibility_reexports():
    paths = {'bootstrap': ROOT / 'superset/bootstrap_osa_industry_certified.py', 'matrices': ROOT / 'superset/osa_certified_matrices.py'}
    for owner, path in paths.items():
        tree = ast.parse(path.read_text(encoding='utf-8'))
        exports = {alias.asname or alias.name for node in tree.body if isinstance(node, ast.ImportFrom) for alias in node.names}
        local = definitions(path)
        for key in BASELINE['symbols']:
            group, name = key.split('.')
            if group == owner: assert name in exports or name in local
        assert not any(isinstance(node, ast.ImportFrom) and any(alias.name == '*' for alias in node.names) for node in tree.body)
    assert set(definitions(paths['bootstrap'])) == {'DASHBOARD_TITLE', 'DASHBOARD_SLUG', 'PREFIX', 'main'}
    assert not definitions(paths['matrices'])
