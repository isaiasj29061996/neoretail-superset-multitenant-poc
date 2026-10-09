"""Snapshot and compare dashboard identities, metadata and RLS without writes."""
import argparse
import json
from pathlib import Path
from superset.app import create_app
from neoretail_bootstrap.core.sql_sources import consumption_sql
from neoretail_bootstrap.serving.metadata import snapshot
from neoretail_bootstrap.export.options import INDICATORS, indicator_sql


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    parser.add_argument('--baseline')
    parser.add_argument('--idempotent',action='store_true')
    args = parser.parse_args()
    app = create_app()
    with app.app_context(): current = json.loads(json.dumps(snapshot(),default=str))
    Path(args.output).write_text(json.dumps(current,default=str,indent=2),encoding='utf-8')
    if args.baseline:
        before = json.loads(Path(args.baseline).read_text(encoding='utf-8-sig'))
        if args.idempotent:
            assert before == current, 'Superset metadata is not idempotent'
        else:
            assert [(d['id'],d['uuid'],d['slug'],d['layout'],d['charts'],d['embedded']) for d in before['dashboards']] == [(d['id'],d['uuid'],d['slug'],d['layout'],d['charts'],d['embedded']) for d in current['dashboards']]
            assert before['charts'] == current['charts'], 'Chart metadata changed'
            assert before['rls'] == current['rls'], 'Persistent RLS changed'
            assert [d['id'] for d in before['datasets']] == [d['id'] for d in current['datasets']], 'Dataset catalog changed'
            for old,new in zip(before['datasets'],current['datasets']):
                assert (old['id'],old['uuid'],old['name'],old['metrics']) == (new['id'],new['uuid'],new['name'],new['metrics'])
                assert new['schema'] == 'serving'
                if old['name'] == 'nr_export_indicators' and old['sql'] != consumption_sql(indicator_sql()):
                    legacy = "SELECT indicador FROM (VALUES\n    " + ",\n    ".join(f"('{value}')" for value in INDICATORS) + "\n) AS options(indicador)"
                    assert old['sql'] == legacy
                    assert new['sql'] == consumption_sql(indicator_sql())
                    added = [c for c in new['columns'] if c['name'] not in {c['name'] for c in old['columns']}]
                    assert len(added)==1 and added[0]['name']=='id_customer' and added[0]['expression'] is None
                    assert old['columns'] == [c for c in new['columns'] if c not in added]
                else:
                    assert old['columns'] == new['columns'], new['name']
                    assert new['sql'] == (consumption_sql(old['sql']) if old['sql'] else old['sql']), new['name']
            # Defaults derived from latest source dates may change. Report them
            # explicitly; a changed target/cascade/layout is never accepted.
            changed_defaults=[]
            for old,new in zip(before['dashboards'],current['dashboards']):
                a=json.loads(old['metadata']); b=json.loads(new['metadata'])
                for left,right in zip(a.get('native_filter_configuration',[]),b.get('native_filter_configuration',[])):
                    la=left.copy(); rb=right.copy()
                    ld=la.pop('defaultDataMask',None); rd=rb.pop('defaultDataMask',None)
                    assert la == rb, (old['slug'],left['id'])
                    if ld != rd: changed_defaults.append({'dashboard':old['slug'],'filter':left['id'],'before':ld,'after':rd})
                assert len(a.get('native_filter_configuration',[])) == len(b.get('native_filter_configuration',[]))
                a.pop('native_filter_configuration',None); b.pop('native_filter_configuration',None)
                assert a == b, old['slug']
            print(json.dumps({'source_date_defaults_changed':changed_defaults},default=str))
    print(json.dumps({'metadata':'PASS','dashboards':len(current['dashboards']),'charts':len(current['charts']),
                      'datasets':len(current['datasets']),'idempotence':bool(args.idempotent)},default=str))

if __name__ == '__main__': main()
