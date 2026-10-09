"""Use Embedded-issued JWTs and real Superset ChartData to test Lactalis RLS."""
import json
import sys
from pathlib import Path
import jwt
import requests
import yaml
from flask import g, request
from flask_login import login_user, logout_user
from superset.app import create_app


def main():
    credentials = json.load(sys.stdin)
    session = requests.Session()
    base = 'http://embedded-app:3000'
    response = session.post(base + '/api/login', json={'username': 'demo.multitenant', 'password': credentials['password']}, timeout=30)
    response.raise_for_status()
    credentials.clear()
    state = session.get(base + '/api/session', timeout=30).json()
    assert state['idCustomer'] == 290 and [c['idCustomer'] for c in state['availableCustomers']] == [290]
    for other in (142, 17066, 609):
        assert session.post(base + '/api/context', json={'idCustomer': other}, timeout=30).status_code == 403
    report = {'session_customer': 290, 'context_overrides_denied': [142, 17066, 609], 'dashboards': []}
    config = yaml.safe_load(Path('/app/config/tenants.yaml').read_text(encoding='utf-8'))
    app = create_app()
    with app.app_context():
        from superset import db, security_manager
        from superset.models.dashboard import Dashboard
        from superset.common.query_context_factory import QueryContextFactory
        from superset.commands.chart.data.get_data_command import ChartDataCommand
        for key, descriptor in config['dashboards'].items():
            dashboard = db.session.query(Dashboard).filter_by(slug=descriptor['slug']).one()
            response = session.post(base + '/api/guest-token', json={'dashboardKey': key, 'idCustomer': 142}, timeout=30)
            response.raise_for_status()
            token = response.json()['token']
            payload = jwt.decode(token, options={'verify_signature': False})
            assert payload['rls_rules'] == [{'clause': 'id_customer = 290'}]
            assert payload['resources'] == [{'type': 'dashboard', 'id': descriptor['embedded_id']}]
            entry = {'slug': descriptor['slug'], 'rls': 'id_customer = 290', 'probes': []}
            # Every dataset used by this dashboard must preserve tenant authority.
            datasets = {}
            for chart in dashboard.slices:
                datasets.setdefault(chart.datasource_id, chart)
            for chart in datasets.values():
                for target in (None, 290, 142, 17066):
                    with app.test_request_context('/', headers={app.config['GUEST_TOKEN_HEADER_NAME']: token}):
                        guest = security_manager.get_guest_user_from_request(request)
                        assert guest and security_manager.is_guest_user(guest)
                        login_user(guest)
                        g.user = guest
                        try:
                            form = {**json.loads(chart.params), 'dashboardId': dashboard.id, 'slice_id': chart.id,
                                    'datasource': f'{chart.datasource_id}__table', 'force': True}
                            filters = [] if target is None else [{'col': 'id_customer', 'op': 'IN', 'val': [target]}]
                            if 'nm_measure' in {c.column_name for c in chart.table.columns}:
                                filters.append({'col': 'nm_measure', 'op': 'IN', 'val': ['unidade']})
                            query = {'columns': ['id_customer'], 'metrics': [], 'row_limit': 10, 'time_range': 'No filter',
                                     'filters': filters}
                            form['extra_filters'] = filters
                            g.form_data = {'queries': [query]}
                            context = QueryContextFactory().create(datasource={'id': chart.datasource_id, 'type': 'table'},
                                queries=[query], form_data=form, force=True)
                            command = ChartDataCommand(context)
                            command.validate()
                            outputs = command.run()['queries']
                            assert outputs and not any(o.get('error') for o in outputs)
                            assert all('id_customer = 290' in o.get('query', '') for o in outputs)
                            rows = [r for o in outputs for r in o.get('data', [])]
                            assert all(int(r['id_customer']) == 290 for r in rows)
                            if target in (142, 17066): assert not rows
                            elif target is None: assert rows, (chart.slice_name, 'No Lactalis rows')
                            entry['probes'].append({'dataset': chart.datasource_id, 'requested': target, 'rows': len(rows)})
                        finally:
                            logout_user()
                            g.user = None
            with app.test_request_context('/', headers={app.config['GUEST_TOKEN_HEADER_NAME']: token.rsplit('.', 1)[0] + '.invalid'}):
                assert security_manager.get_guest_user_from_request(request) is None
            if key == 'osa_certified':
                measure = next(f for f in json.loads(dashboard.json_metadata)['native_filter_configuration'] if f['name'] == 'Medida')
                option_id = measure['targets'][0]['datasetId']
                with app.test_request_context('/', headers={app.config['GUEST_TOKEN_HEADER_NAME']: token}):
                    guest = security_manager.get_guest_user_from_request(request)
                    assert guest
                    login_user(guest)
                    g.user = guest
                    try:
                        form = {'dashboardId': dashboard.id, 'datasource': f'{option_id}__table', 'force': True,
                                'type': 'NATIVE_FILTER', 'native_filter_id': measure['id']}
                        g.form_data = {'queries': [{'filters': []}]}
                        context = QueryContextFactory().create(datasource={'id': option_id, 'type': 'table'},
                            queries=[{'columns': ['id_customer', 'nm_measure'], 'metrics': [], 'filters': [],
                                      'row_limit': 100, 'time_range': 'No filter'}], form_data=form, force=True)
                        command = ChartDataCommand(context)
                        command.validate()
                        outputs = command.run()['queries']
                        assert outputs and not any(o.get('error') for o in outputs)
                        assert all('id_customer = 290' in o.get('query', '') for o in outputs)
                        choices = [r for o in outputs for r in o.get('data', [])]
                        assert choices and all(int(r['id_customer']) == 290 for r in choices)
                        assert 'unidade' in {r['nm_measure'] for r in choices}
                        entry['measure_filter_guest_choices'] = sorted({r['nm_measure'] for r in choices})
                    finally:
                        logout_user()
                        g.user = None
            entry['tampered_signature_rejected'] = True
            report['dashboards'].append(entry)
            print(json.dumps(entry), flush=True)
    Path('/generated/lactalis_guest_current.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
