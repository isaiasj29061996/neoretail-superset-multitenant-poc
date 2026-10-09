"""PBIP evidence gates; no inferred DAX execution or numeric PBI expectations."""
import json
from pathlib import Path
import pytest
F=json.loads((Path(__file__).parent/'fixtures/pbip_f13_final_evidence_20261008.json').read_text('utf-8'))
@pytest.mark.parametrize('case',F['cases'],ids=lambda x:x['case'])
def test_hidden_filter_controlled_row_count_contract(case):
    # Complete DAX IF branches always 0 or 1; numeric payload is not read by COUNTROWS.
    assert case['dax_if_result']==int(bool(case['history_rows_after_retained_context']))
    assert case['hidden_comparator_eligibility']=='UNPROVEN'
def test_null_filter_is_visual_not_global_page_predicate():
    text=json.dumps(F['hidden_filter'])
    assert 'ComparisonKind' in text and 'null' in text and 'Filtro Historico Com Dados' in text
    assert 'REMOVEFILTERS(AP_CONVERSAO)' in F['hidden_dax']
    assert 'REMOVEFILTERS(DIM_CATALOGO_LOCAL[Rede])' in F['hidden_dax']
    assert 'REMOVEFILTERS(DIM_LOCAL[Rede])' in F['hidden_dax']
def test_bookmark_scope_does_not_restore_unlisted_kpi_states():
    b=F['bookmark'];o=b['options']
    assert b['displayName']=='LimpaFiltrosVGPN'
    assert o['applyOnlyToTargetVisuals'] and o['suppressDisplay'] and o['suppressActiveSection']
    assert len(o['targetVisualNames'])==8
    assert '1870d11a56820457d0aa' not in o['targetVisualNames']
    ap=b['explorationState']['sections'][F['main_page']]['visualContainers']['ad36f9b090253095ebe5']
    assert "'unidade'" in json.dumps(ap)
def test_sync_is_cross_page_not_same_page_dependency_invention():
    for group,members in F['sync_groups'].items():
        assert any(m['page']==F['main_page'] for m in members)
        assert any(m['page']!=F['main_page'] for m in members)
        assert all(m['sync']['filterChanges'] for m in members)
def test_direction_does_not_reverse_product_into_ap():
    r=F['relationships']
    assert any(x['toTable']=='AP_CONVERSAO' and x['fromTable']=='DIM_CONVERSAO' and x['crossFilteringBehavior']=='OneDirection' and x['isActive'] for x in r)
    assert any(x['toTable']=='DIM_CONVERSAO' and x['fromTable']=='DIM_ITENS' and x['crossFilteringBehavior']=='OneDirection' and x['isActive'] for x in r)
    assert any({x['fromTable'],x['toTable']}=={'DIM_LOCAL','DIM_CATALOGO_LOCAL'} and x['crossFilteringBehavior']=='BothDirections' and x['isActive'] for x in r)
def test_full_bookmark_inventory_has_one_relevant_not_117_active():
    assert F['counts']['bookmarks']==117
    assert F['counts']['relevant_bookmarks']==1
