"""Dependency boundaries and stable metadata identities for bootstrap core."""
import ast
from pathlib import Path
import sys
import uuid

import pytest
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "superset"))

from neoretail_bootstrap.core.chart_params import comparison_pivot_params
from neoretail_bootstrap.core.metadata import upsert_chart, upsert_dataset, upsert_overview_chart
from neoretail_bootstrap.core.metrics import formatted_metric, metric


# Phase 1 retains these explicit domain contracts; generic helpers belong in core.
DOMAIN_IMPORTS = {
    "bootstrap_overview_quantity": {"Q", "quantity_semantic_sql"},
}


def dependency_violations(source):
    violations = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            violations.extend(name.name for name in node.names if any(part.startswith('bootstrap_') for part in name.name.split('.')))
        elif isinstance(node, ast.ImportFrom):
            parts = (node.module or '').split('.')
            module = next((part for part in parts if part.startswith('bootstrap_')), '')
            if module:
                if parts[-1] != module:
                    violations.append(node.module)
                    continue
                violations.extend(f"{module}.{name.name}" for name in node.names if name.name not in DOMAIN_IMPORTS.get(module, set()))
    return violations


def test_bootstraps_only_import_explicit_domain_contracts_from_other_bootstraps():
    paths = [*sorted((ROOT / 'superset').glob('bootstrap_*.py')), ROOT / 'superset/osa_certified_matrices.py']
    errors = {path.name: dependency_violations(path.read_text(encoding='utf-8')) for path in paths}
    assert not {path: errors for path, errors in errors.items() if errors}


@pytest.mark.parametrize('source', [
    'from bootstrap_overview import metric',
    'from bootstrap_panorama import Layout as SharedLayout',
    'from bootstrap_new import helper',
    'from bootstrap_overview import *',
    'import bootstrap_panorama as p',
    'from bootstrap_overview.helpers import metric',
])
def test_architecture_guard_rejects_generic_and_implicit_dependencies(source):
    assert dependency_violations(source)


def test_core_is_independent_of_bootstraps_and_superset_runtime():
    for path in (ROOT / 'superset/neoretail_bootstrap/core').glob('*.py'):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            modules = [entry.name for entry in node.names] if isinstance(node, ast.Import) else [node.module or ''] if isinstance(node, ast.ImportFrom) else []
            assert all(module.split('.')[0] not in {'superset', 'sqlalchemy'} and not any(part.startswith('bootstrap_') for part in module.split('.')) for module in modules), path


def test_metric_identity_and_individual_formats_are_preserved():
    expected = {
        'expressionType': 'SQL', 'sqlExpression': 'SUM(valor)', 'label': 'Valor',
        'optionName': f"metric_{uuid.uuid5(uuid.NAMESPACE_DNS, 'Valor').hex[:12]}",
    }
    assert metric('Valor', 'SUM(valor)') == expected
    assert formatted_metric('Valor', 'SUM(valor)', '$,.2f') == {**expected, 'd3Format': '$,.2f'}
    dataset = type('Dataset', (), {'id': 42})()
    metrics = [formatted_metric('Markup', 'SUM(margem)', '.2%'), expected]
    params = comparison_pivot_params(dataset, ['uf', 'cidade'], metrics)
    assert params['columnFormats'] == {'Markup': '.2%'}
    assert params['datasource'] == '42__table'
    assert params['groupbyRows'] == ['uf', 'cidade']
    assert params['row_limit'] == 10000


Base = declarative_base()


class Dataset(Base):
    __tablename__ = 'datasets'
    id = Column(Integer, primary_key=True)
    table_name = Column(String, unique=True)
    schema = Column(String)
    sql = Column(String)
    columns = ()
    metadata_fetches = 0

    def __init__(self, *, database=None, **kwargs):
        super().__init__(**kwargs)
        self.database = database

    def fetch_metadata(self):
        self.metadata_fetches += 1
        self.columns = ('id_customer',)


class Chart(Base):
    __tablename__ = 'charts'
    id = Column(Integer, primary_key=True)
    slice_name = Column(String, unique=True)
    datasource_type = Column(String)
    datasource_id = Column(Integer)
    viz_type = Column(String)
    params = Column(String)
    description = Column(String)


@pytest.fixture
def session():
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_dataset_second_run_preserves_id_and_skips_unchanged_metadata(session):
    database = object()
    first = upsert_dataset(session, Dataset, database, 'certified', sql='SELECT 1')
    identity = first.id
    second = upsert_dataset(session, Dataset, database, 'certified', sql='SELECT 1')
    assert second.id == identity
    assert session.query(Dataset).count() == 1
    assert second.metadata_fetches == 1
    assert second.schema == 'gold'
    upsert_dataset(session, Dataset, database, 'certified', sql='SELECT 2')
    assert second.metadata_fetches == 2


@pytest.mark.parametrize('upsert', [upsert_chart, upsert_overview_chart])
def test_chart_second_run_preserves_id_and_serialized_params(session, upsert):
    dataset = type('Dataset', (), {'id': 42})()
    chart = upsert(session, Chart, dataset, 'Estoque', {'label': 'São Paulo'})
    identity, params, description = chart.id, chart.params, chart.description
    again = upsert(session, Chart, dataset, 'Estoque', {'label': 'São Paulo'})
    assert (again.id, again.params, again.description) == (identity, params, description)
    assert session.query(Chart).count() == 1
    assert 'São Paulo' in again.params


def test_legacy_chart_rename_preserves_existing_identity(session):
    old = Chart(slice_name='Estoque antigo')
    session.add(old)
    session.flush()
    identity = old.id
    dataset = type('Dataset', (), {'id': 42})()
    updated = upsert_chart(session, Chart, dataset, 'Estoque', {}, viz_type='table', legacy_titles=('Estoque antigo',))
    assert updated.id == identity
    assert updated.slice_name == 'Estoque'
    assert updated.viz_type == 'table'
    assert session.query(Chart).count() == 1
