"""Overview ownership, compatibility and parity with the certified original."""
import ast
from datetime import date
import hashlib
import importlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import uuid

import pytest
from jinja2 import Environment, StrictUndefined

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'superset/neoretail_bootstrap/overview'
sys.path.insert(0, str(ROOT / 'superset'))
BASELINE = json.loads((Path(__file__).parent / 'fixtures/overview_modules_baseline.json').read_text())


def definitions(path):
    return {
        node.name if isinstance(node, ast.FunctionDef) else node.targets[0].id: node
        for node in ast.parse(path.read_text(encoding='utf-8')).body
        if isinstance(node, ast.FunctionDef)
        or isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
    }


def normalized_ast(node):
    if isinstance(node, ast.AST):
        return {'type': type(node).__name__, **{
            name: normalized_ast(value) for name, value in ast.iter_fields(node)
            if value is not None and value != []
        }}
    if isinstance(node, list):
        return [normalized_ast(value) for value in node]
    if node is Ellipsis:
        return {'literal': 'ellipsis'}
    return node


def ast_digest(node):
    return hashlib.sha256(json.dumps(normalized_ast(node), sort_keys=True).encode()).hexdigest()


def test_entrypoint_is_an_orchestrator_and_reexports_certified_contracts():
    path = ROOT / 'superset/bootstrap_overview.py'
    assert set(definitions(path)) == {'DASHBOARD_TITLE', 'main'}
    exports = {
        (node.module.removeprefix('neoretail_bootstrap.overview.'), alias.name)
        for node in ast.parse(path.read_text(encoding='utf-8')).body
        if isinstance(node, ast.ImportFrom)
        and (node.module or '').startswith('neoretail_bootstrap.overview.')
        for alias in node.names
    }
    assert {(case['module'], case['name']) for case in BASELINE['symbols']} <= exports
    assert all(name != '*' for _, name in exports)
    core_imports = {alias.asname or alias.name for node in ast.parse(path.read_text(encoding='utf-8')).body
                    if isinstance(node, ast.ImportFrom) and (node.module or '').startswith('neoretail_bootstrap.core.')
                    for alias in node.names}
    assert {'metric', 'chart_params', '_jinja_filter_predicates', 'upsert_dataset', 'upsert_chart'} <= core_imports


@pytest.mark.parametrize('path', sorted(PACKAGE.glob('*.py')), ids=lambda path: path.stem)
def test_overview_modules_use_core_without_bootstrap_or_framework_dependencies(path):
    allowed_siblings = {'semantics': {'filters'}, 'presentation': {'semantics', 'filters'}}
    for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules = [node.module or '']
            if node.level:
                assert node.level == 1 and node.module in allowed_siblings.get(path.stem, set())
        else:
            continue
        for module in modules:
            assert not any(part.startswith('bootstrap_') for part in module.split('.')), (path, module)
            assert module.split('.')[0] not in {'superset', 'sqlalchemy'}, (path, module)
            if module.startswith('neoretail_bootstrap.'):
                assert module.startswith('neoretail_bootstrap.core.'), (path, module)
    assert not {'metric', 'chart_params', '_jinja_filter_predicates', 'upsert_chart', 'upsert_dataset', 'Layout'} & set(definitions(path))


@pytest.mark.parametrize('case', BASELINE['symbols'], ids=lambda case: case['name'])
def test_moved_symbols_match_original_ast(case):
    assert ast_digest(definitions(PACKAGE / (case['module'] + '.py'))[case['name']]) == case['sha256']


@pytest.mark.parametrize('case', BASELINE['sql'], ids=lambda case: case['name'] + repr(case['args']))
def test_sql_templates_match_original_bytes(case):
    module = importlib.import_module('neoretail_bootstrap.overview.semantics')
    sql = getattr(module, case['name'])(*case['args'])
    assert hashlib.sha256(sql.encode()).hexdigest() == case['sha256']


@pytest.mark.parametrize('case', BASELINE['native_filters'], ids=lambda case: case['name'] + repr(case['args']))
def test_filter_defaults_cascades_targets_and_ids_match_original(case):
    module = importlib.import_module('neoretail_bootstrap.overview.filters')
    assert getattr(module, case['name'])(*case['args']) == case['expected']


def test_layout_preserves_exact_serialization_ids_uuids_and_titles():
    from neoretail_bootstrap.overview.presentation import position_json
    charts = [SimpleNamespace(id=10+i, slice_name='Chart '+str(i), uuid=uuid.UUID(int=i+1)) for i in range(8)]
    assert position_json(charts) == BASELINE['position_json']


def test_chart_composition_matches_original_statements():
    node = definitions(PACKAGE / 'presentation.py')['chart_specs']
    assert ast_digest(node.body[:-1]) == BASELINE['chart_block_ast']


@pytest.mark.parametrize('case', BASELINE['chart_specs'], ids=lambda case: repr(case['dates']))
def test_chart_specs_preserve_metrics_profiles_and_filters(case):
    from neoretail_bootstrap.overview.presentation import chart_specs
    datasets = [SimpleNamespace(id=i) for i in range(1, 5)]
    dates = [date.fromisoformat(value) if value else None for value in case['dates']]
    specs = chart_specs(*datasets, *dates)
    assert [[dataset.id, title, params] for dataset, title, params in specs] == case['expected']


@pytest.mark.parametrize('name', ['bootstrap_overview_quantity.py', 'bootstrap_panorama.py', 'bootstrap_osa_industry.py',
                                  'bootstrap_osa_industry_certified.py', 'bootstrap_stock_optimization.py'])
def test_consumers_use_canonical_overview_contracts(name):
    nodes = ast.walk(ast.parse((ROOT / 'superset' / name).read_text(encoding='utf-8')))
    imports = [node.module for node in nodes if isinstance(node, ast.ImportFrom)]
    assert 'bootstrap_overview' not in imports
    assert any((module or '').startswith('neoretail_bootstrap.overview.') for module in imports)


DIMENSIONS = ('rede', 'bandeira', 'uf', 'cidade', 'tipo_local', 'loja', 'regiao', 'tp_activity_level',
              'item', 'descricao_marca', 'hierarquia_1', 'hierarquia_2', 'hierarquia_3')


def render(template, filters):
    environment = Environment(undefined=StrictUndefined)
    environment.filters['where_in'] = lambda values: '(' + ', '.join("'" + str(value).replace("'", "''") + "'" for value in values) + ')'
    return environment.from_string(template).render(get_filters=lambda column, **kwargs: filters.get(column, []))


@pytest.mark.parametrize('function', ['overview_semantic_sql', 'osa_semantic_sql'])
@pytest.mark.parametrize('dimension', DIMENSIONS)
@pytest.mark.parametrize('operator', ['IN', 'NOT IN'])
def test_detail_filters_render_below_aggregation_with_valid_history_alias(function, dimension, operator):
    from neoretail_bootstrap.overview import semantics
    value = 'RJ' if dimension == 'uf' else '123' if dimension == 'item' else 'selected'
    sql = render(getattr(semantics, function)(), {
        'nm_measure': [{'op': 'IN', 'val': ['unidade']}],
        dimension: [{'op': operator, 'val': [value]}],
    })
    assert 'FROM gold.nr_overview_history h' in sql
    assert f"AND h.{dimension} {operator} ('{value}')" in sql


@pytest.mark.parametrize('function,mart', [('overview_semantic_sql', 'nr_overview_semantic_default'),
                                         ('osa_semantic_sql', 'nr_osa_semantic_default')])
def test_compact_paths_and_conversion_cardinality_guard_are_preserved(function, mart):
    from neoretail_bootstrap.overview import semantics
    template = getattr(semantics, function)()
    assert render(template, {'nm_measure': [{'op': 'IN', 'val': ['unidade']}]}).strip() == 'SELECT * FROM gold.' + mart
    assert 'WHERE 1=0' in render(template, {})
    assert 'WHERE 1=0' in render(template, {'nm_measure': [{'op': 'IN', 'val': ['unidade', 'hectolitro']}]})
