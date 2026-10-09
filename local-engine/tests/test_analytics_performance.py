"""Performance configuration must preserve unrelated connection settings."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'superset'))
from neoretail_bootstrap.core.analytics_performance import analytics_engine_extra


@pytest.mark.parametrize('extra', [None, '', '{}'])
def test_empty_configuration_disables_jit(extra):
    assert json.loads(analytics_engine_extra(extra)) == {
        'engine_params': {'connect_args': {'options': '-c jit=off'}}
    }


@pytest.mark.parametrize('options', [
    '-c jit=on', '-cjit=on', '-c jit=off',
    '-c statement_timeout=90000 -c jit=on -c timezone=UTC',
])
def test_configuration_is_idempotent_and_keeps_other_settings(options):
    original = {'metadata_cache_timeout': 123, 'engine_params': {
        'pool_pre_ping': True, 'connect_args': {
            'application_name': 'neoretail', 'options': options,
        },
    }}
    once = analytics_engine_extra(json.dumps(original))
    assert analytics_engine_extra(once) == once
    result = json.loads(once)
    assert result['metadata_cache_timeout'] == 123
    assert result['engine_params']['pool_pre_ping'] is True
    assert result['engine_params']['connect_args']['application_name'] == 'neoretail'
    updated = result['engine_params']['connect_args']['options']
    assert updated.count('jit=off') == 1 and 'jit=on' not in updated
    if 'statement_timeout' in options:
        assert 'statement_timeout=90000' in updated and 'timezone=UTC' in updated
