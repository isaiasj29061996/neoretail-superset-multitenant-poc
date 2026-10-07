"""Apply current product SQL in order; preserve formulas and scoped Gold data."""
import json
import os
from pathlib import Path
import time
import sys
import psycopg2

root = Path('/repo')
paths = [root / 'analytics-db/views/20_mart_visao_industria.sql', *sorted((root / 'analytics-db/marts').glob('*.sql'))]
if len(sys.argv) > 1: paths = [p for p in paths if p.name == sys.argv[1]]
if not paths: raise SystemExit('Unknown SQL file')
connection = psycopg2.connect(host=os.environ['ANALYTICS_DB_HOST'], port=os.environ['ANALYTICS_DB_PORT'],
    dbname=os.environ['ANALYTICS_DB_NAME'], user=os.environ['ANALYTICS_DB_USER'], password=os.environ['ANALYTICS_DB_PASSWORD'])
connection.autocommit = True
report_path = Path('/workspace/generated/lactalis_marts_current.json')
report = json.loads(report_path.read_text(encoding='utf-8')) if len(sys.argv) > 1 else []
if len(sys.argv) > 1: report = [r for r in report if r['sql'] != sys.argv[1]]
try:
    with connection.cursor() as cursor:
        # Execution setting only: a prior local PG16 serving run suffered SIGSEGV.
        cursor.execute('SET jit = off')
        for path in paths:
            start = time.monotonic()
            print('Applying ' + path.name, flush=True)
            cursor.execute(path.read_text(encoding='utf-8'))
            item = {'sql': path.name, 'seconds': round(time.monotonic() - start, 2), 'status': 'passed'}
            report.append(item)
            Path('/workspace/generated/lactalis_marts_current.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
            print(json.dumps(item), flush=True)
finally:
    connection.close()
