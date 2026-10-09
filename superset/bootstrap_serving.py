"""One-time shared source migration; never called on a user's tenant switch."""
import argparse
import json
import os
from superset.app import create_app
from neoretail_bootstrap.core.metadata import upsert_dataset
from neoretail_bootstrap.serving.metadata import snapshot, structural
from neoretail_bootstrap.export.options import INDICATORS, indicator_sql


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    assert os.getenv('NEORETAIL_CONSUMPTION_SCHEMA') == 'serving'
    app=create_app()
    with app.app_context():
        from superset import db
        from superset.connectors.sqla.models import SqlaTable
        before=json.loads(json.dumps(snapshot(),default=str))
        changed=[]
        try:
            for dataset in db.session.query(SqlaTable).order_by(SqlaTable.id).all():
                if dataset.database.database_name != 'NeoRetail Gold - PostgreSQL Local': continue
                if dataset.schema not in ('gold','serving'): raise RuntimeError('Unexpected original schema')
                old=(dataset.schema,dataset.sql)
                original_expressions = {c.column_name:c.expression for c in dataset.columns}
                sql = dataset.sql
                if dataset.table_name == 'nr_export_indicators':
                    legacy = "SELECT indicador FROM (VALUES\n    " + ",\n    ".join(f"('{value}')" for value in INDICATORS) + "\n) AS options(indicador)"
                    from neoretail_bootstrap.core.sql_sources import consumption_sql
                    assert sql in (legacy, consumption_sql(indicator_sql())), 'Unexpected indicator source contract'
                    sql = indicator_sql()
                upsert_dataset(db.session,SqlaTable,dataset.database,dataset.table_name,sql=sql)
                if dataset.table_name == 'nr_export_indicators':
                    for column in dataset.columns:
                        if column.column_name in original_expressions:
                            column.expression = original_expressions[column.column_name]
                if old != (dataset.schema,dataset.sql): changed.append({'id':dataset.id,'name':dataset.table_name})
            after=json.loads(json.dumps(snapshot(),default=str))
            left = structural(before); right = structural(after)
            for old,new in zip(left['datasets'],right['datasets']):
                if old['name'] == 'nr_export_indicators':
                    added = [c for c in new['columns'] if c['name'] not in {c['name'] for c in old['columns']}]
                    assert not added or (len(added)==1 and added[0]['name']=='id_customer' and added[0]['expression'] is None)
                    new['columns'] = [c for c in new['columns'] if c not in added]
            assert left == right, 'Source migration changed structural metadata'
            if args.apply: db.session.commit()
            else: db.session.rollback()
        except Exception:
            db.session.rollback()
            raise
        print(json.dumps({'serving_migration':'committed' if args.apply else 'rolled_back', 'changed':changed},default=str),flush=True)

if __name__ == '__main__': main()
