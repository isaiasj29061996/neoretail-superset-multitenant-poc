"""Execute every OSA Industria chart query through Superset."""
import json

from flask import g
from flask_login import login_user
from superset.app import create_app

app = create_app()
with app.test_request_context('/'):
    from superset import db, security_manager
    from superset.commands.chart.data.get_data_command import ChartDataCommand
    from superset.common.query_context_factory import QueryContextFactory
    from superset.models.dashboard import Dashboard

    admin = security_manager.find_user(username='admin') or db.session.query(security_manager.user_model).first()
    login_user(admin)
    g.user = admin
    factory = QueryContextFactory()
    dashboard = db.session.query(Dashboard).filter(Dashboard.slug == 'neoretail-v9-osa-industria').one()
    for chart in sorted(dashboard.slices, key=lambda item: item.id):
        form = json.loads(chart.params)
        metrics = form.get('metrics', [])
        filters = [{'col': 'id_customer', 'op': 'IN', 'val': [259]}]
        variant = form.get('card_variant')
        extras = {}
        sql_filters = [item.get('sqlExpression') for item in form.get('adhoc_filters', []) if item.get('expressionType') == 'SQL' and item.get('sqlExpression')]
        if sql_filters:
            extras['where'] = ' AND '.join(f'({item})' for item in sql_filters)
        if form.get('viz_type') == 'neoretail-kpi-card' and variant in ('verticalbars', 'rankbars'):
            queries = [{'columns': form.get('groupby', []), 'metrics': metrics, 'filters': filters, 'extras': extras, 'granularity': form.get('x_axis'), 'time_range': form.get('time_range', 'No filter'), 'row_limit': form.get('row_limit', 100)}]
        elif form.get('viz_type') == 'neoretail-kpi-card':
            axis = form['x_axis']
            grain = form.get('time_grain_sqla', 'P1M')
            time_column = {'timeGrain': grain, 'columnType': 'BASE_AXIS', 'sqlExpression': axis, 'label': axis, 'expressionType': 'SQL', 'isColumnReference': True}
            queries = [{'columns': [time_column], 'metrics': metrics, 'filters': filters, 'extras': {**extras, 'time_grain_sqla': grain}, 'orderby': [[axis, True]], 'row_limit': form.get('row_limit', 10000)}]
        else:
            queries = [{'columns': form.get('groupby', []), 'metrics': metrics, 'filters': filters, 'row_limit': form.get('row_limit', 1000)}]
        try:
            result = ChartDataCommand(factory.create(datasource={'id': chart.datasource_id, 'type': 'table'}, queries=queries, form_data=form)).run()
            counts = [len(item.get('data', [])) for item in result.get('queries', [])]
            errors = [item.get('error') for item in result.get('queries', []) if item.get('error')]
        except Exception as error:
            counts, errors = [], [f'{type(error).__name__}: {error}']
        print(json.dumps({'chart': chart.slice_name, 'rows': counts, 'errors': errors}, ensure_ascii=False))
