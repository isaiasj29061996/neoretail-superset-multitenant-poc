"""Execute every overview chart query through Superset and report row counts."""
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
    dashboard = db.session.query(Dashboard).filter(Dashboard.slug == 'neoretail-v9-visao-geral-industria').one()
    for chart in sorted(dashboard.slices, key=lambda item: item.id):
        form = json.loads(chart.params)
        grain = form.get('time_grain_sqla', 'P1M')
        axis = form['x_axis']
        metrics = [*form.get('metrics', [])]
        for name in ('metric', 'critical_metric', 'risk_metric'):
            if form.get(name): metrics.append(form[name])
        time_column = {'timeGrain': grain, 'columnType': 'BASE_AXIS', 'sqlExpression': axis, 'label': axis, 'expressionType': 'SQL', 'isColumnReference': True}
        common = {'time_range': 'No filter', 'filters': [], 'extras': {'time_grain_sqla': grain}, 'metrics': metrics, 'orderby': [[axis, True]], 'row_limit': 10000}
        queries = [{**common, 'columns': [time_column]}]
        if form.get('card_variant') == 'bars' and form.get('groupby'):
            queries.append({**common, 'columns': [time_column, *form['groupby']]})
        context = factory.create(datasource={'id': chart.datasource_id, 'type': 'table'}, queries=queries, form_data=form)
        result = ChartDataCommand(context).run()
        counts = [len(item.get('data', [])) for item in result.get('queries', [])]
        errors = [item.get('error') for item in result.get('queries', []) if item.get('error')]
        print(json.dumps({'chart': chart.slice_name, 'rows': counts, 'errors': errors}, ensure_ascii=False))
