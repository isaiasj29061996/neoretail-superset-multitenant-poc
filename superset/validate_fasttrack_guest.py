"""Read-only real Guest JWT, chart, filter and warmed-cache checks on serving."""
import argparse
import json
import time
import sys
from pathlib import Path
import requests
import yaml
import jwt
from flask import g, request
from flask_login import login_user, logout_user
from superset.app import create_app
from profile_dashboard_performance import build_queries

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tenants', nargs='+', type=int, required=True)
    parser.add_argument('--embedded-credentials-stdin',action='store_true')
    parser.add_argument('--tokens-only',action='store_true')
    args = parser.parse_args()
    assert set(args.tenants) <= {17066, 290, 16868}
    app = create_app()
    with app.app_context():
        from superset import db, security_manager
        from superset.models.dashboard import Dashboard
        from superset.common.query_context_factory import QueryContextFactory
        from superset.commands.chart.data.get_data_command import ChartDataCommand
        dashboards = db.session.query(Dashboard).filter(Dashboard.slug.like('neoretail-v9-%')).all()
        descriptors = []
        for dashboard in dashboards:
            assert dashboard.embedded, dashboard.slug
            descriptors.append((dashboard.id, dashboard.slug, str(dashboard.embedded[0].uuid), [c.id for c in dashboard.slices]))
        from superset.models.slice import Slice
        from superset.connectors.sqla.models import SqlaTable
        native_targets = {}
        dashboard_filters = {}
        for dashboard in dashboards:
            dashboard_filters[dashboard.id] = json.loads(dashboard.json_metadata).get('native_filter_configuration', [])
            native_targets[dashboard.id] = [(f['id'], t['datasetId'], t['column']['name'])
                for f in json.loads(dashboard.json_metadata).get('native_filter_configuration',[])
                for t in f.get('targets',[]) if t.get('datasetId') and t.get('column',{}).get('name')]
        report = {'charts': [], 'isolation': [], 'cache': [], 'filters': [], 'periods': [], 'native_filters': [], 'denied_tokens': [], 'token_refreshes':0}
        factory = QueryContextFactory()
        tokens = {}
        baseline_chart_data = {}
        denied_tenants = sorted({142,-1,17066,290,16868} - set(args.tenants))
        resources = {dashboard_id:resource for dashboard_id,_,resource,_ in descriptors}
        embedded_sessions = {}
        if args.embedded_credentials_stdin:
            credentials = json.load(sys.stdin)
            base = 'http://embedded-app:'+str(credentials['port'])
            config = yaml.safe_load(Path('/app/config/tenants.yaml').read_text(encoding='utf-8'))
            dashboard_keys = {d['slug']:key for key,d in config['dashboards'].items()}
            keys_by_id = {identity:dashboard_keys[slug] for identity,slug,_,_ in descriptors}
            for tenant in args.tenants:
                session = requests.Session()
                response = session.post(base+'/api/login',json={'username':'demo.multitenant','password':credentials['password']},timeout=30)
                response.raise_for_status()
                response = session.post(base+'/api/context',json={'idCustomer':tenant},timeout=30)
                response.raise_for_status()
                state = session.get(base+'/api/session',timeout=30).json()
                assert state['idCustomer']==tenant
                assert [c['idCustomer'] for c in state['availableCustomers']]==[17066,290,16868]
                embedded_sessions[tenant] = session
            credentials.clear()
            report['positive_token_source'] = 'actual Embedded API'
        else:
            report['positive_token_source'] = 'Superset security manager'
        def issue(tenant,dashboard_id):
            if tenant in embedded_sessions:
                response = embedded_sessions[tenant].post(base+'/api/guest-token',
                    json={'dashboardKey':keys_by_id[dashboard_id],'idCustomer':142},timeout=30)
                response.raise_for_status()
                return response.json()['token']
            return security_manager.create_guest_access_token(
                user={'username':'fasttrack-guest'},
                resources=[{'type':'dashboard','id':resources[dashboard_id]}],
                rls=[{'clause':'id_customer = '+str(tenant)}])
        for tenant in [*args.tenants,*denied_tenants]:
            for dashboard_id, _, resource, _ in descriptors:
                tokens[tenant, dashboard_id] = issue(tenant,dashboard_id)
        if args.tokens_only:
            assert embedded_sessions, 'Token preflight requires the actual Embedded API'
            checked = 0
            for tenant in args.tenants:
                for dashboard_id,_,_,_ in descriptors:
                    token = tokens[tenant,dashboard_id]
                    with app.test_request_context('/',headers={app.config['GUEST_TOKEN_HEADER_NAME']:token}):
                        assert security_manager.get_guest_user_from_request(request)
                    payload = jwt.decode(token,options={'verify_signature':False})
                    assert payload['rls_rules']==[{'clause':'id_customer = '+str(tenant)}]
                    assert payload['resources']==[{'type':'dashboard','id':resources[dashboard_id]}]
                    checked += 1
            for session in embedded_sessions.values():
                session.post(base+'/api/logout',json={},timeout=30).raise_for_status()
                session.close()
            print('FASTTRACK_TOKEN_REPORT='+json.dumps({'token_preflight':'PASS','verified_embedded_tokens':checked,'tenants':args.tenants}),flush=True)
            return
        def execute(tenant, dashboard_id, chart_id, query=None, filters=None, force=False, datasource_id=None, renew=True, native_filter_id=None):
            expiry = jwt.decode(tokens[tenant,dashboard_id],options={'verify_signature':False})['exp']
            if renew and time.time() > expiry - 30:
                tokens[tenant,dashboard_id] = issue(tenant,dashboard_id)
                report['token_refreshes'] += 1
            with app.test_request_context('/', headers={app.config['GUEST_TOKEN_HEADER_NAME']:tokens[tenant, dashboard_id]}):
                guest = security_manager.get_guest_user_from_request(request)
                assert guest and security_manager.is_guest_user(guest)
                login_user(guest); g.user = guest
                try:
                    chart = db.session.get(Slice, chart_id)
                    dataset_id = datasource_id or chart.datasource_id
                    dataset = db.session.get(SqlaTable,dataset_id)
                    assert dataset.schema == 'serving', chart.slice_name
                    form = json.loads(chart.params)
                    defaults = []
                    default_time = None
                    if query is None:
                        for native in dashboard_filters[dashboard_id]:
                            # targets identify the options source; scope identifies
                            # affected charts, including charts on other datasets.
                            if chart_id in native.get('scope', {}).get('excluded', []):
                                continue
                            extra = native.get('defaultDataMask', {}).get('extraFormData', {})
                            defaults.extend(extra.get('filters', []))
                            default_time = extra.get('time_range', default_time)
                        requested_columns = {f['col'] for f in (filters or [])}
                        defaults = [f for f in defaults if f['col'] not in requested_columns]
                    queries = [query] if query else build_queries(form, dashboard_default_filters=defaults)[0]
                    if query is None and form.get('card_variant') == 'kpifilters':
                        queries = [{'columns':form.get('groupby', []), 'metrics':form.get('metrics', []),
                                    'filters':defaults, 'row_limit':2000, 'time_range':'No filter'}]
                    for item in queries:
                        if query is None:
                            # The historical profiler inserts baseline 142.
                            # Remove it: tenant isolation must come from JWT RLS.
                            item['filters'] = [f for f in item.get('filters', []) if f.get('col') != 'id_customer']
                            # The actual custom plugin uses its raw x_axis,
                            # not the profiler's approximate adhoc time column.
                            item['columns'] = [form.get('x_axis') if isinstance(c,dict) and c.get('label')==form.get('x_axis') else c for c in item.get('columns',[])]
                        item['filters'] = [*item.get('filters', []), *(filters or [])]
                        if default_time is not None:
                            item['time_range'] = default_time
                    form = {**form, 'dashboardId':dashboard_id, 'datasource':str(dataset_id)+'__table', 'force':force, 'extra_filters':[*defaults, *(filters or [])]}
                    if native_filter_id:
                        form.pop('slice_id',None)
                        form.update(type='NATIVE_FILTER',native_filter_id=native_filter_id)
                    else:
                        form['slice_id'] = chart_id
                    g.form_data = form
                    context = factory.create(datasource={'id':dataset_id,'type':'table'},
                        queries=queries, form_data=form, force=force)
                    command = ChartDataCommand(context)
                    command.validate()
                    outputs = command.run()['queries']
                    assert outputs and not any(r.get('error') for r in outputs), (chart.slice_name, outputs)
                    assert all('id_customer = '+str(tenant) in r.get('query','') for r in outputs), chart.slice_name
                    return outputs, chart.slice_name
                finally:
                    logout_user(); g.user = None
        for tenant in args.tenants:
            for dashboard_id, slug, _, chart_ids in descriptors:
                for chart_id in chart_ids:
                    outputs, name = execute(tenant, dashboard_id, chart_id, force=True)
                    if dashboard_id == descriptors[0][0] and chart_id == descriptors[0][3][0]:
                        baseline_chart_data[tenant] = json.dumps([o.get('data',[]) for o in outputs],sort_keys=True,default=str)
                    rows = sum(len(o.get('data',[])) for o in outputs)
                    report['charts'].append({'tenant':tenant,'dashboard':slug,'chart':name,'rows':rows})
                    print(json.dumps(report['charts'][-1]), flush=True)
                    if name.startswith('[OSA Certificada] Região'):
                        for period in ('MTD','U3M','YTD'):
                            changed, _ = execute(tenant,dashboard_id,chart_id,
                                filters=[{'col':'osa_period','op':'IN','val':[period]}],force=True)
                            rows = sum(len(o.get('data',[])) for o in changed)
                            assert rows, (tenant,name,period)
                            report['periods'].append({'tenant':tenant,'chart':name,'period':period,'rows':rows})
                    if 'Evolutivo de estoque' in name:
                        from sqlalchemy import text
                        chart = db.session.get(Slice, chart_id)
                        with chart.table.database.get_sqla_engine() as engine, engine.connect() as connection:
                            item = connection.execute(text('SELECT item FROM serving.nr_panorama_inventory_weekly_detail WHERE id_customer=:tenant AND item IS NOT NULL LIMIT 1'), {'tenant':tenant}).scalar()
                        assert item is not None
                        for column, value in [('uf','RJ'), ('item',item)]:
                            for operator in ('IN','NOT IN'):
                                filtered, _ = execute(tenant, dashboard_id, chart_id,
                                    filters=[{'col':column,'op':operator,'val':[value]}], force=True)
                                if 'semanal' in name.casefold() and 'Falta x Excesso' not in name:
                                    assert all('w.'+column in o['query'] and 'l.'+column not in o['query'] for o in filtered), (name,column,operator)
                                report['filters'].append({'tenant':tenant,'chart':name,'column':column,'operator':operator,
                                    'rows':sum(len(o.get('data',[])) for o in filtered)})
                # Every dashboard must have at least one populated chart.
                assert any(c['rows'] for c in report['charts'] if c['tenant']==tenant and c['dashboard']==slug), slug
                for filter_id, dataset_id, column in native_targets[dashboard_id]:
                    dataset = db.session.get(SqlaTable, dataset_id)
                    if 'id_customer' not in {c.column_name for c in dataset.columns}:
                        # Exercise the actual UI options query before asserting
                        # the stricter tenant identity projection contract.
                        execute(tenant,dashboard_id,chart_ids[0], datasource_id=dataset_id, native_filter_id=filter_id,
                            query={'columns':[column],'metrics':[],'row_limit':10,'filters':[]},force=True)
                        raise AssertionError(('native filter lacks tenant identity',dataset_id,column))
                    for requested in args.tenants:
                        outputs, _ = execute(tenant,dashboard_id,chart_ids[0], datasource_id=dataset_id, native_filter_id=filter_id,
                            query={'columns':['id_customer',column],'metrics':[],'row_limit':10,
                                   'filters':[{'col':'id_customer','op':'IN','val':[requested]}]})
                        rows = [r for o in outputs for r in o.get('data',[])]
                        assert all(int(r['id_customer']) == tenant == requested for r in rows), filter_id
                        if tenant != requested: assert not rows
                        report['native_filters'].append({'token':tenant,'requested':requested,'dashboard':slug,'filter':filter_id,'rows':len(rows)})
                seen = set()
                for chart_id in chart_ids:
                    chart = db.session.get(Slice, chart_id)
                    if chart.datasource_id in seen: continue
                    seen.add(chart.datasource_id)
                    for denied in denied_tenants:
                        outputs, name = execute(denied,dashboard_id,chart_id,
                            query={'columns':['id_customer'],'metrics':[],'row_limit':10,'filters':[]})
                        assert not any(o.get('data') for o in outputs), (denied,name)
                        report['denied_tokens'].append({'token':denied,'chart':name,'rows':0})
                    for target in args.tenants:
                        query = {'columns':['id_customer'], 'metrics':[], 'row_limit':10,
                                 'filters':[{'col':'id_customer','op':'IN','val':[target]}]}
                        outputs, name = execute(tenant, dashboard_id, chart_id, query=query)
                        rows = [r for o in outputs for r in o.get('data', [])]
                        assert all(int(r['id_customer']) == tenant == target for r in rows), (tenant,target,name)
                        if tenant != target: assert not rows
                        report['isolation'].append({'token':tenant,'requested':target,'chart':name,'rows':len(rows)})
        # Reuse still-valid tokens across context switches and compare the same
        # query before/after warming all tenant caches. No tenant filter supplied.
        dashboard_id, _, _, chart_ids = descriptors[0]
        for tenant in args.tenants:
            tokens[tenant,dashboard_id] = issue(tenant,dashboard_id)
            aggregate, _ = execute(tenant,dashboard_id,chart_ids[0],force=True,renew=False)
            assert json.dumps([o.get('data',[]) for o in aggregate],sort_keys=True,default=str) == baseline_chart_data[tenant]
            # Establish the current serving baseline before testing cache reuse;
            # a previous unpublished-tenant probe can have cached an empty result.
            outputs, _ = execute(tenant,dashboard_id,chart_ids[0],
                query={'columns':['id_customer'],'metrics':[],'row_limit':10,'filters':[]},force=True,renew=False)
            rows = [r for o in outputs for r in o.get('data', [])]
            assert rows and all(int(r['id_customer']) == tenant for r in rows)
        for tenant in [*args.tenants, *reversed(args.tenants)]:
            aggregate, _ = execute(tenant, dashboard_id, chart_ids[0], renew=False)
            assert json.dumps([o.get('data',[]) for o in aggregate],sort_keys=True,default=str) == baseline_chart_data[tenant], ('cached metrics from wrong context',tenant)
            outputs, name = execute(tenant, dashboard_id, chart_ids[0],
                query={'columns':['id_customer'],'metrics':[],'row_limit':10,'filters':[]}, renew=False)
            rows = [r for o in outputs for r in o.get('data', [])]
            assert rows and all(int(r['id_customer']) == tenant for r in rows)
            assert all(o.get('is_cached') for o in [*aggregate,*outputs]), ('cache reuse not exercised',tenant)
            report['cache'].append({'tenant':tenant,'chart':name,'rows':len(rows),
                                    'cache_keys':[o.get('cache_key') for o in outputs],
                                    'aggregate_cache_keys':[o.get('cache_key') for o in aggregate],
                                    'cached_aggregate_matches_tenant':True,'cache_hits_verified':True})
        keys = {}
        for item in report['cache']:
            keys.setdefault(item['tenant'], set()).update(k for k in item['cache_keys'] if k)
            keys[item['tenant']].update(k for k in item['aggregate_cache_keys'] if k)
        for tenant, tenant_keys in keys.items():
            for other, other_keys in keys.items():
                if tenant != other: assert not tenant_keys & other_keys
        original = tokens[args.tenants[0],dashboard_id]
        header,payload,signature = original.split('.')
        signature = ('A' if signature[0] != 'A' else 'B') + signature[1:]
        with app.test_request_context('/',headers={app.config['GUEST_TOKEN_HEADER_NAME']:'.'.join([header,payload,signature])}):
            assert security_manager.get_guest_user_from_request(request) is None
        report['tampered_signature_rejected'] = True
        for session in embedded_sessions.values():
            response = session.post(base+'/api/logout',json={},timeout=30)
            response.raise_for_status()
            session.close()
        print('FASTTRACK_REPORT='+json.dumps(report), flush=True)

if __name__ == '__main__': main()
