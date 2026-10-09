"""Run a bounded data phase; stop on any failed stage, isolation or disk gate."""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
phase = sys.argv[1]
steps = {'silver': ['03A', '03B', '03C', '03D', '04'], 'gold': ['05', '06', '07', '08']}[phase]
for step in steps:
    subprocess.run([sys.executable, str(root / 'scripts/run_lactalis_stage.py'), step], cwd=root, check=True)
subprocess.run(['docker', 'compose', 'exec', '-T', 'local-engine', 'python', '/repo/scripts/audit_lactalis_lake.py', '--layer', phase], cwd=root, check=True)
subprocess.run([sys.executable, str(root / 'scripts/lactalis_disk_snapshot.py'), phase], cwd=root, check=True)
