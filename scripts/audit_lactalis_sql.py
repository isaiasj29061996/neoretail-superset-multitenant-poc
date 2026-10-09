"""Current Analytics objects, full persisted tenant gate, sizes and indexes."""
import json
import os
from pathlib import Path
import psycopg2
from psycopg2 import sql

connection = psycopg2.connect(host=os.environ['ANALYTICS_DB_HOST'], port=os.environ['ANALYTICS_DB_PORT'],
    dbname=os.environ['ANALYTICS_DB_NAME'], user=os.environ['ANALYTICS_DB_USER'], password=os.environ['ANALYTICS_DB_PASSWORD'])
report = {'relations': [], 'top30': [], 'passed': True}
with connection, connection.cursor() as cursor:
    cursor.execute("SELECT schema_name FROM information_schema.schemata ORDER BY 1")
    report['schemas'] = [r[0] for r in cursor.fetchall()]
    if any(s.startswith('gold_') for s in report['schemas']): report['passed'] = False
    cursor.execute('SELECT pg_database_size(current_database())')
    report['database_bytes'] = cursor.fetchone()[0]
    cursor.execute("SELECT n.nspname,c.relname,c.relkind,c.oid FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('gold','audit','silver','bronze') AND c.relkind IN ('r','m','v') ORDER BY 1,2")
    relations = cursor.fetchall()
    for schema, name, kind, oid in relations:
        cursor.execute("SELECT attname FROM pg_attribute WHERE attrelid=%s AND attnum>0 AND NOT attisdropped", (oid,))
        columns = [r[0] for r in cursor.fetchall()]
        item = {'schema': schema, 'table': name, 'kind': kind, 'rls_column': 'id_customer' in columns}
        if kind in ('r', 'm'):
            cursor.execute('SELECT pg_total_relation_size(%s),pg_relation_size(%s),pg_indexes_size(%s)', (oid, oid, oid))
            item['total_bytes'], item['data_bytes'], item['index_bytes'] = cursor.fetchone()
            if 'id_customer' in columns:
                cursor.execute(sql.SQL('SELECT id_customer, count(*) FROM {}.{} GROUP BY 1').format(sql.Identifier(schema), sql.Identifier(name)))
                item['tenant_counts'] = cursor.fetchall()
                if any(row[0] != 290 for row in item['tenant_counts']): report['passed'] = False
            elif schema == 'gold': report['passed'] = False
        if kind == 'v' and schema == 'gold' and 'id_customer' not in columns: report['passed'] = False
        report['relations'].append(item)
        print(json.dumps(item), flush=True)
    report['top30'] = sorted([r for r in report['relations'] if 'total_bytes' in r], key=lambda r:r['total_bytes'], reverse=True)[:30]
    cursor.execute("SELECT schemaname,tablename,indexname FROM pg_indexes WHERE schemaname='gold' ORDER BY 1,2,3")
    report['indexes'] = cursor.fetchall()
Path('/workspace/generated/lactalis_sql_current.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({'passed': report['passed'], 'database_bytes': report['database_bytes'], 'schemas': report['schemas']}))
if not report['passed']: raise SystemExit('SQL_ISOLATION_GATE_FAILED')
