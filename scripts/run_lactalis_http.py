"""Run production HTTP probes without exposing login credentials or JWTs."""
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[1]
mode = sys.argv[1]
label = sys.argv[2] if len(sys.argv) > 2 else mode
if not label.replace('_', '').isalnum(): raise SystemExit('Invalid report label')
started = time.monotonic()
if mode == 'guest':
    password = subprocess.check_output(['docker', 'compose', 'exec', '-T', 'embedded-app', 'node', '-e',
        'process.stdout.write(process.env.DEMO_USER_PASSWORD)'], cwd=root, text=True, encoding='utf-8')
    command = ['docker', 'compose', 'exec', '-T', 'superset', '/app/.venv/bin/python', '/app/pythonpath/validate_lactalis_guest.py']
    content = json.dumps({'password': password})
elif mode == 'assistant':
    command = ['docker', 'compose', 'exec', '-T', 'embedded-app', 'node', '--input-type=module']
    content = (root / 'scripts/lactalis_assistant_runtime.mjs').read_text(encoding='utf-8')
else:
    path = 'embedded-app/smoke.mjs' if mode == 'embedded' else 'embedded-app/assistant/smoke.mjs'
    command = ['docker', 'compose', 'exec', '-T', '-e', 'NEORETAIL_VALIDATION_CUSTOMER=290', 'embedded-app', 'node', '--input-type=module']
    content = (root / path).read_text(encoding='utf-8')
with (root / f'generated/lactalis_http_{label}_current.log').open('w', encoding='utf-8') as log:
    result = subprocess.run(command, cwd=root, input=content, text=True, encoding='utf-8', stdout=log, stderr=subprocess.STDOUT)
record = {'probe': label, 'exit_code': result.returncode, 'seconds': round(time.monotonic() - started, 2)}
with (root / 'generated/lactalis_http_current.jsonl').open('a', encoding='utf-8') as summary:
    summary.write(json.dumps(record) + '\n')
print(json.dumps(record))
raise SystemExit(result.returncode)
