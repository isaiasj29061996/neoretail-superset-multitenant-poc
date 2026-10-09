"""Serving -> Superset -> actual guest RLS -> mock; stop at first failed gate."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[1]
for layer in ('bronze', 'silver', 'gold'):
    gate = json.loads((root / f'generated/lactalis_{layer}_isolation.json').read_text(encoding='utf-8'))
    if not gate['passed']: raise SystemExit(f'{layer} gate failed')
published = json.loads((root / 'generated/lactalis_marts_current.json').read_text(encoding='utf-8'))
expected = 1 + len(list((root / 'analytics-db/marts').glob('*.sql')))
if len(published) != expected or any(r['status'] != 'passed' for r in published):
    raise SystemExit('Serving publication incomplete')
env = {**os.environ, 'NEORETAIL_CUSTOMER': '290', 'SPARK_MASTER': 'local[4]', 'LLM_PROVIDER': 'mock'}
steps = [
    ('sql_isolation', ['docker', 'compose', 'exec', '-T', 'local-engine', 'python', '/repo/scripts/audit_lactalis_sql.py']),
    ('serving_disk', [sys.executable, 'scripts/lactalis_disk_snapshot.py', 'serving']),
    ('bootstrap', [sys.executable, 'scripts/run_lactalis_superset.py', 'bootstrap']),
    ('validate', [sys.executable, 'scripts/run_lactalis_superset.py', 'validate']),
    ('embedded', [sys.executable, 'scripts/run_lactalis_http.py', 'embedded']),
    ('guest', [sys.executable, 'scripts/run_lactalis_http.py', 'guest']),
    ('start_mock', ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'start.ps1', '-Assistant', '-HealthTimeoutSeconds', '900']),
    ('assistant', [sys.executable, 'scripts/run_lactalis_http.py', 'assistant']),
    ('assistant_smoke', [sys.executable, 'scripts/run_lactalis_http.py', 'assistant_smoke']),
]
if len(sys.argv) > 1:
    steps = steps[[label for label, _ in steps].index(sys.argv[1]):]
    if sys.argv[1] == 'validate' and len(sys.argv) > 2:
        steps[0][1].append(sys.argv[2])
for label, command in steps:
    started = time.monotonic()
    print('Running ' + label, flush=True)
    with (root / f'generated/lactalis_gate_{label}_current.log').open('w', encoding='utf-8') as handle:
        result = subprocess.run(command, cwd=root, env=env, stdout=handle, stderr=subprocess.STDOUT)
    record = {'gate': label, 'exit_code': result.returncode, 'seconds': round(time.monotonic()-started, 2)}
    with (root / 'generated/lactalis_runtime_gates_current.jsonl').open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(record) + '\n')
    print(json.dumps(record), flush=True)
    if result.returncode: raise SystemExit(result.returncode)
