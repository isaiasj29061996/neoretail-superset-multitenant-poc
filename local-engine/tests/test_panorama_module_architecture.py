"""Panorama dependency boundaries and parity with the certified pre-split source."""
import ast
import hashlib
import importlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'superset/neoretail_bootstrap/panorama'
sys.path.insert(0, str(ROOT / 'superset'))
BASELINE = json.loads((Path(__file__).parent / 'fixtures/panorama_phase2_baseline.json').read_text())


def definitions(path):
    return {
        node.name if isinstance(node, ast.FunctionDef) else node.targets[0].id: node
        for node in ast.parse(path.read_text(encoding='utf-8')).body
        if isinstance(node, ast.FunctionDef)
        or isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
    }


def normalized_ast(node):
    """Ignore optional empty AST fields added by newer Python parsers."""
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


def test_entrypoint_orchestrates_and_explicitly_reexports_existing_contracts():
    path = ROOT / 'superset/bootstrap_panorama.py'
    nodes = definitions(path)
    assert set(nodes) == {'main', 'DASHBOARD_TITLE', 'LATEST_SQL', 'P'}
    exports = {
        (node.module.removeprefix('neoretail_bootstrap.panorama.'), alias.name)
        for node in ast.parse(path.read_text(encoding='utf-8')).body
        if isinstance(node, ast.ImportFrom)
        and (node.module or '').startswith('neoretail_bootstrap.panorama.')
        for alias in node.names
    }
    assert {(case['module'], case['name']) for case in BASELINE['symbols']} <= exports
    assert all(name != '*' for _, name in exports)


@pytest.mark.parametrize('path', sorted(PACKAGE.glob('*.py')), ids=lambda path: path.stem)
def test_domains_do_not_depend_on_bootstraps_framework_or_other_domains(path):
    for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules = [node.module or '']
            if node.level:
                assert node.level == 1 and node.module == 'filters', (path, modules)
        else:
            continue
        for module in modules:
            assert not any(part.startswith('bootstrap_') for part in module.split('.')), (path, module)
            assert module.split('.')[0] not in {'superset', 'sqlalchemy'}, (path, module)
            if module.startswith('neoretail_bootstrap.'):
                assert module.startswith('neoretail_bootstrap.core.'), (path, module)
    assert not {'metric', 'formatted_metric', 'Layout', '_jinja_filter_predicates', 'upsert_chart', 'upsert_dataset'} & set(definitions(path))


@pytest.mark.parametrize('case', BASELINE['symbols'], ids=lambda case: case['module'] + '.' + case['name'])
def test_moved_certified_contracts_match_original_ast(case):
    node = definitions(PACKAGE / (case['module'] + '.py'))[case['name']]
    digest = hashlib.sha256(json.dumps(normalized_ast(node), sort_keys=True).encode()).hexdigest()
    assert digest == case['sha256']


@pytest.mark.parametrize('case', BASELINE['sql'], ids=lambda case: case['name'] + repr(case['args']))
def test_generated_sql_is_byte_identical_to_certified_baseline(case):
    module = importlib.import_module('neoretail_bootstrap.panorama.' + case['module'])
    sql = getattr(module, case['name'])(*case['args'])
    assert hashlib.sha256(sql.encode()).hexdigest() == case['sha256']


@pytest.mark.parametrize('name', ['bootstrap_osa_industry_certified.py', 'osa_certified_matrices.py', 'neoretail_bootstrap/osa_certified/filters.py', 'neoretail_bootstrap/osa_certified/matrices.py'])
def test_osa_consumers_import_weekly_contract_from_canonical_package(name):
    imports = [node for node in ast.parse((ROOT / 'superset' / name).read_text(encoding='utf-8')).body if isinstance(node, ast.ImportFrom)]
    assert any(node.module == 'neoretail_bootstrap.panorama.filters' and any(alias.name == 'WEEKLY_FILTER_COLUMNS' for alias in node.names) for node in imports)
    assert not any(node.module == 'bootstrap_panorama' for node in imports)
