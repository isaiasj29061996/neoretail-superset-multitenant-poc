"""Run one explicitly scoped stage and retain its log, status and duration."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[1]
step = sys.argv[1]
allowed = {'00', '02', '02B', '03A', '03B', '03C', '03D', '04', '05', '06', '07', '08'}
if step not in allowed: raise SystemExit('Unsupported stage')
arguments = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(root / 'run-local-pipeline.ps1'), '-Step', step, '-Customer', '290']
if step == '02': arguments.append('-CustomerOnlyDimensions')
if step == '02B': arguments.extend(['-Family', 'customer_daily'])
env = {**os.environ, 'NEORETAIL_CUSTOMER': '290', 'SPARK_MASTER': 'local[4]'}
start = time.monotonic()
log = root / f'generated/lactalis_{step}_current.log'
with log.open('w', encoding='utf-8') as handle:
    result = subprocess.run(arguments, cwd=root, env=env, stdout=handle, stderr=subprocess.STDOUT)
record = {'step': step, 'id_customer': 290, 'exit_code': result.returncode, 'seconds': round(time.monotonic() - start, 2), 'log': log.name}
with (root / 'generated/lactalis_execution_current.jsonl').open('a', encoding='utf-8') as handle:
    handle.write(json.dumps(record) + '\n')
print(json.dumps(record))
raise SystemExit(result.returncode)
