import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
stage = sys.argv[1]
if not stage.replace('_', '').isalnum(): raise SystemExit('Invalid stage')
def command(args):
    run = subprocess.run(args, cwd=root, capture_output=True, text=True)
    if run.returncode: raise RuntimeError('Resource audit command failed: ' + args[0])
    return run.stdout
detail = command(['docker', 'system', 'df', '-v'])
(root / f'generated/lactalis_disk_{stage}.txt').write_text(detail, encoding='utf-8')
disk = json.loads(command(['powershell', '-NoProfile', '-Command', 'Get-PSDrive C | Select-Object Name,Used,Free | ConvertTo-Json -Compress']))
result = {'stage': stage, 'disk': disk,
          'local_lake_kib': command(['docker', 'compose', 'exec', '-T', 'local-engine', 'du', '-sk', '/data']).split()[0],
          'analytics_data_kib': command(['docker', 'compose', 'exec', '-T', 'analytics-db', 'du', '-sk', '/var/lib/postgresql/data']).split()[0]}
with (root / 'generated/lactalis_disk_current.jsonl').open('a', encoding='utf-8') as handle: handle.write(json.dumps(result) + '\n')
print(json.dumps(result))
if disk['Free'] < 30 * 1024 ** 3: raise SystemExit('DISK_GATE_FAILED: free C below 30 GiB')
