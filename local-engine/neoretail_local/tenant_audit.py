"""Read-only complete lake and SQL identity audit for a registered tenant."""
import argparse
import json
from pathlib import Path
import pyarrow.parquet as pq
import pyarrow.compute as pc
import psycopg2
from psycopg2 import sql
from .settings import Settings

def audit(settings, layers):
    report = {'tenant':settings.id_customer, 'lake':[], 'sql':[]}
    for layer in layers:
        for directory in sorted((settings.data_root/'lake'/layer).iterdir()):
            partition = directory/settings.tenant_context.partition
            files = sorted(partition.rglob('*.parquet')) if partition.is_dir() else []
            if not files: continue
            ids = set(); nulls = 0; rows = 0; date_bounds = []
            for path in files:
                parquet = pq.ParquetFile(path)
                assert 'id_customer' in parquet.schema_arrow.names, path
                date_column = next((c for c in ('data','id_time','ID_TIME') if c in parquet.schema_arrow.names),None)
                missing_date_stats = False
                if date_column:
                    for group in range(parquet.metadata.num_row_groups):
                        row_group = parquet.metadata.row_group(group)
                        for index in range(row_group.num_columns):
                            column = row_group.column(index)
                            if column.path_in_schema != date_column: continue
                            stats = column.statistics
                            if stats and stats.has_min_max:
                                date_bounds.append((str(stats.min),str(stats.max)))
                            elif not stats or stats.num_values:
                                missing_date_stats = True
                    if missing_date_stats:
                        for batch in parquet.iter_batches(columns=[date_column],batch_size=65536):
                            bounds = pc.min_max(batch.column(0)).as_py()
                            if bounds['min'] is not None:
                                date_bounds.append((str(bounds['min']),str(bounds['max'])))
                for batch in parquet.iter_batches(columns=['id_customer'], batch_size=65536):
                    values = batch.column(0)
                    nulls += values.null_count; rows += len(values)
                    ids.update(pc.unique(values).to_pylist())
            assert nulls == 0 and ids <= {settings.id_customer}, (directory,ids,nulls)
            report['lake'].append({'layer':layer,'table':directory.name,'rows':rows,'ids':list(ids),'nulls':nulls,
                                   'date_min':min((b[0] for b in date_bounds),default=None),
                                   'date_max':max((b[1] for b in date_bounds),default=None)})
    with psycopg2.connect(settings.psycopg_dsn) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=%s AND c.relkind IN ('r','m','v') AND c.relname NOT LIKE '_stage_%%' ORDER BY c.relname", (settings.gold_schema,))
        names = [row[0] for row in cursor.fetchall()]
        for name in names:
            cursor.execute(sql.SQL('SELECT id_customer, COUNT(*) FROM {}.{} GROUP BY id_customer').format(sql.Identifier(settings.gold_schema),sql.Identifier(name)))
            counts = cursor.fetchall()
            assert all(identity == settings.id_customer for identity,_ in counts), (name,counts)
            report['sql'].append({'schema':settings.gold_schema,'table':name,'counts':counts})
    print(json.dumps(report), flush=True)
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tenant',required=True)
    parser.add_argument('--layers',nargs='+',choices=['bronze','silver','gold'],default=['bronze','silver','gold'])
    args = parser.parse_args()
    audit(Settings.from_env(require_blob=False,customer_selector=args.tenant), args.layers)

if __name__ == '__main__': main()
