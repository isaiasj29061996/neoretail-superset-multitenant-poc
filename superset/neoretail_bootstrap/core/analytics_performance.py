"""Connection settings for the local interactive Analytics workload."""
import json
import re


def analytics_engine_extra(extra):
    """Disable per-query LLVM compilation while preserving connection options.

    PBIP plans measured compilation taking seconds for small result sets.
    This setting affects execution strategy only, for every tenant; it does
    not alter SQL, timezone, arithmetic, filters or row-level security.
    """
    result = json.loads(extra or '{}')
    engine = result.setdefault('engine_params', {})
    connect = engine.setdefault('connect_args', {})
    options = connect.get('options', '')
    options = re.sub(r'(?<!\S)-c\s*jit=\S+', '', options).strip()
    connect['options'] = (options + ' -c jit=off').strip()
    return json.dumps(result, sort_keys=True)
