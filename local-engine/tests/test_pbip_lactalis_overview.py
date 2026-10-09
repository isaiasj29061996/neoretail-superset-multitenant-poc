"""Contracts extracted from the supplied PBIP, not KPI numeric expectations."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = json.loads((Path(__file__).parent / 'fixtures/pbip_lactalis_overview_20261008.json').read_text('utf-8'))
def source(name): return (ROOT / name).read_text('utf-8')

def test_calendar_uses_import_anchor_not_latest_fact():
    assert 'DateTime.LocalNow()' in FIXTURE['tables']['0_0_AUX_ CALENDARIO']
    assert 'Date.AddDays([DATA_ATUALIZACAO]' in FIXTURE['tables']['0_0_CALENDARIO']
    assert 'semantic_anchor_date' in source('superset/frontend-plugin/plugin-chart-neoretail-kpi/src/transformProps.js')
    assert 'nr_pbip_calendar' in source('superset/bootstrap_overview.py')

def test_page_context_is_a_cnpj_semijoin_not_fact_multiplication():
    assert 'crossFilteringBehavior: bothDirections' in FIXTURE['relationships']
    assert 'DIM_LOCAL.CNPJ' in FIXTURE['relationships']
    contract = source('superset/neoretail_bootstrap/pbip_overview/context.py')
    assert 'EXISTS' in contract and 'cnpj' in contract and 'rede IS NOT NULL' in contract

def test_headline_activity_universe_is_not_chart_bar_allowlist():
    assert 'FATOS_PARTICULAR_HISTORICO[GIRO] > 0' in FIXTURE['measures']['Giro estoque']['dax']
    presentation = source('superset/neoretail_bootstrap/pbip_overview/presentation.py')
    assert 'headline_scope' in presentation
    assert "headline_scope = \"semantic_scope = 'all'\"" in presentation

def test_loss_u3m_retains_period_components():
    dax = FIXTURE['measures']['Qtd Perda OSA Mensal']['dax']
    assert 'AVERAGE(FATOS_MENSAL_CAUSA_OSA[PRECO_MEDIO])' in dax
    assert 'divide(calculate([Qtd Perda OSA Mensal]' in FIXTURE['measures']['Perda OSA Valor U3M']['dax']
    transform = source('superset/frontend-plugin/plugin-chart-neoretail-kpi/src/transformProps.js')
    assert "profile === 'pbip_osa_bundle'" in transform
    assert 'lossPriceCount' in transform

def test_osa_ratio_and_blank_contract():
    assert 'ISBLANK(Problemas)' in FIXTURE['measures']['% OSA Historico']['dax']
    assert 'divide' not in FIXTURE['measures']['% OSA U3M']['dax'].lower()
    semantic = source('superset/neoretail_bootstrap/pbip_overview/semantics.py')
    assert 'SUM(qtd_problemas_osa)' in semantic
    assert 'exclude_activity=True' in semantic

def test_roi_annual_uses_calendar_window_not_last_twelve_rows():
    assert 'DATESINPERIOD' in FIXTURE['measures']['ROI Anual']['dax']
    assert 'REMOVEFILTERS' in FIXTURE['measures']['ROI Anual']['dax']
    transform = source('superset/frontend-plugin/plugin-chart-neoretail-kpi/src/transformProps.js')
    assert 'annualCalendarRows' in transform
