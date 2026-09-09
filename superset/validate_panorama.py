"""Execute every Panorama chart query through Superset and report row counts."""
import json
import os

from flask import g
from flask_login import login_user
from superset.app import create_app

app = create_app()
with app.test_request_context('/'):
    from superset import db, security_manager
    from superset.commands.chart.data.get_data_command import ChartDataCommand
    from superset.common.query_context_factory import QueryContextFactory
    from superset.models.slice import Slice

    admin = security_manager.find_user(username='admin') or db.session.query(security_manager.user_model).first()
    login_user(admin)
    g.user = admin
    factory = QueryContextFactory()
    charts = db.session.query(Slice).filter(Slice.slice_name.like('[Panorama]%')).order_by(Slice.id)
    match = os.environ.get('PANORAMA_MATCH')
    if match:
        charts = charts.filter(Slice.slice_name.ilike(f'%{match}%'))
    for chart in charts:
        form = json.loads(chart.params)
        metrics = form.get('metrics', [])
        filters = [{'col': 'id_customer', 'op': 'IN', 'val': [259]}]
        if form.get('viz_type') == 'neoretail-kpi-card':
            if form.get('card_variant') == 'rankbars':
                queries = [{'columns': form.get('groupby', []), 'metrics': metrics, 'filters': filters, 'row_limit': form.get('row_limit', 10)}]
            else:
                axis = form['x_axis']
                grain = form.get('time_grain_sqla', 'P1M')
                time_column = {'timeGrain': grain, 'columnType': 'BASE_AXIS', 'sqlExpression': axis, 'label': axis, 'expressionType': 'SQL', 'isColumnReference': True}
                queries = [{'columns': [time_column], 'metrics': metrics, 'filters': filters, 'extras': {'time_grain_sqla': grain}, 'orderby': [[axis, True]], 'row_limit': form.get('row_limit', 10000)}]
        else:
            queries = [{'columns': form.get('groupby', []), 'metrics': metrics, 'filters': filters, 'row_limit': form.get('row_limit', 1000)}]
        context = factory.create(datasource={'id': chart.datasource_id, 'type': 'table'}, queries=queries, form_data=form)
        try:
            result = ChartDataCommand(context).run()
            counts = [len(item.get('data', [])) for item in result.get('queries', [])]
            errors = [item.get('error') for item in result.get('queries', []) if item.get('error')]
        except Exception as error:  # validation utility: keep checking remaining charts
            counts, errors = [], [f'{type(error).__name__}: {error}']
        print(json.dumps({'chart': chart.slice_name, 'rows': counts, 'errors': errors}, ensure_ascii=False))
