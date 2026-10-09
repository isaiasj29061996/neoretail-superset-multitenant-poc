"""Metadata contracts shared by serving migration and its read-only audit."""
import copy

def snapshot():
    from superset import db
    from superset.models.dashboard import Dashboard
    from superset.models.slice import Slice
    from superset.connectors.sqla.models import SqlaTable
    from sqlalchemy import text
    dashboards = [{'id':d.id,'uuid':str(d.uuid),'slug':d.slug,'layout':d.position_json,
                   'metadata':d.json_metadata,'charts':sorted(c.id for c in d.slices),
                   'embedded':sorted(str(e.uuid) for e in d.embedded)}
                  for d in db.session.query(Dashboard).order_by(Dashboard.id)]
    charts = [{'id':c.id,'uuid':str(c.uuid),'name':c.slice_name,'datasource_id':c.datasource_id,
               'params':c.params,'description':c.description}
              for c in db.session.query(Slice).order_by(Slice.id)]
    datasets = []
    for d in db.session.query(SqlaTable).order_by(SqlaTable.id):
        datasets.append({'id':d.id,'uuid':str(d.uuid),'name':d.table_name,'schema':d.schema,'sql':d.sql,
            'metrics':sorted([{'id':m.id,'name':m.metric_name,'expression':m.expression,'description':m.description}
                              for m in d.metrics],key=lambda m:m['id']),
            'columns':sorted([{'id':c.id,'name':c.column_name,'type':c.type,'expression':c.expression}
                              for c in d.columns],key=lambda c:c['id'])})
    rls = [dict(row) for row in db.session.execute(text('SELECT * FROM row_level_security_filters ORDER BY id')).mappings()]
    return {'dashboards':dashboards,'charts':charts,'datasets':datasets,'rls':rls}

def structural(value):
    value=copy.deepcopy(value)
    for dataset in value['datasets']:
        dataset.pop('schema'); dataset.pop('sql')
    return value
