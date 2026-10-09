"""Apply current product SQL in order; preserve formulas and scoped Gold data."""
import json
import os
from pathlib import Path
import time
import sys
import psycopg2
from psycopg2 import sql

def refresh_plan(cursor, requested):
    """Topological order from actual pg_rewrite dependencies, never file numbers."""
    cursor.execute("""SELECT child.relname,parent.relname
      FROM pg_rewrite rw JOIN pg_class child ON child.oid=rw.ev_class
      JOIN pg_namespace ns ON ns.oid=child.relnamespace
      JOIN pg_depend d ON d.objid=rw.oid AND d.classid='pg_rewrite'::regclass
      JOIN pg_class parent ON parent.oid=d.refobjid AND d.refclassid='pg_class'::regclass
      WHERE ns.nspname='gold' AND child.relkind='m' AND parent.relkind='m'
        AND child.oid<>parent.oid""")
    dependencies={name:set() for name in requested}
    edges=cursor.fetchall()
    for child,parent in edges:
        if child in dependencies and parent in dependencies:dependencies[child].add(parent)
    ordered=[]
    while dependencies:
        ready=sorted(name for name,parents in dependencies.items() if not parents)
        if not ready:raise RuntimeError('Serving dependency cycle')
        ordered.extend(ready)
        for name in ready:dependencies.pop(name)
        for parents in dependencies.values():parents.difference_update(ready)
    return ordered,edges

root = Path('/repo')
paths = [root / 'analytics-db/views/20_mart_visao_industria.sql', *sorted((root / 'analytics-db/marts').glob('*.sql'))]
refresh_only = len(sys.argv)>1 and sys.argv[1]=='--refresh-only'
if len(sys.argv) > 1 and not refresh_only: paths = [p for p in paths if p.name == sys.argv[1]]
if not paths: raise SystemExit('Unknown SQL file')
connection = psycopg2.connect(host=os.environ['ANALYTICS_DB_HOST'], port=os.environ['ANALYTICS_DB_PORT'],
    dbname=os.environ['ANALYTICS_DB_NAME'], user=os.environ['ANALYTICS_DB_USER'], password=os.environ['ANALYTICS_DB_PASSWORD'])
connection.autocommit = True
report_path = Path('/workspace/generated/lactalis_marts_current.json')
report = json.loads(report_path.read_text(encoding='utf-8')) if len(sys.argv) > 1 and report_path.exists() else []
if len(sys.argv) > 1: report = [r for r in report if r['sql'] != sys.argv[1]]
try:
    with connection.cursor() as cursor:
        # Execution setting only: a prior local PG16 serving run suffered SIGSEGV.
        cursor.execute('SET jit = off')
        if refresh_only:
            requested=sys.argv[2:]
            if not requested or any(not n.startswith('nr_pbip_') for n in requested):
                raise RuntimeError('Refresh-only is restricted to named PBIP serving marts')
            plan,edges=refresh_plan(cursor,requested)
            cursor.execute('SELECT DISTINCT id_customer FROM gold.dim_customer')
            if {row[0] for row in cursor.fetchall()} != {290}:
                raise RuntimeError('Publication requires a Lactalis-only Gold scope')
            cursor.execute('BEGIN')
            try:
                for name in plan:
                    started=time.monotonic()
                    cursor.execute(sql.SQL('REFRESH MATERIALIZED VIEW gold.{}').format(sql.Identifier(name)))
                    report.append({'mart':name,'seconds':round(time.monotonic()-started,2),'status':'passed'})
                    print(json.dumps(report[-1]),flush=True)
                cursor.execute('COMMIT')
            except Exception:
                cursor.execute('ROLLBACK')
                raise
            Path('/workspace/generated/pbip_mart_refresh_current.json').write_text(json.dumps({'plan':plan,'edges':edges,'report':report},indent=2),'utf-8')
            raise SystemExit(0)
        if len(sys.argv)==1:
            # No destructive dependency-blind drop/recreate. Existing deployments
            # need an explicit migration or the safe refresh-only path above.
            cursor.execute("SELECT count(*) FROM pg_matviews WHERE schemaname='gold'")
            if cursor.fetchone()[0]:
                raise RuntimeError('Existing marts: choose explicit SQL migration or --refresh-only; numbered full replay is dependency-unsafe')
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
