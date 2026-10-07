"""Execute every overview chart query through Superset and report timings."""
import json
import os
from time import perf_counter

from flask import g
from flask_login import login_user
from superset.app import create_app


CUSTOMER_ID = int(os.getenv("NEORETAIL_VALIDATION_CUSTOMER", "142"))
FILTER_COLUMN = os.getenv('OVERVIEW_FILTER_COLUMN', '').strip()
FILTER_VALUE = os.getenv('OVERVIEW_FILTER_VALUE', '').strip()
CONVERSION_MEASURE = os.getenv('OVERVIEW_CONVERSION_MEASURE', 'unidade').strip()
app = create_app()
with app.test_request_context('/'):
    from superset import db, security_manager
    from superset.commands.chart.data.get_data_command import ChartDataCommand
    from superset.common.query_context_factory import QueryContextFactory
    from superset.models.dashboard import Dashboard

    admin = security_manager.find_user(username='admin') or db.session.query(
        security_manager.user_model
    ).first()
    login_user(admin)
    g.user = admin
    factory = QueryContextFactory()
    dashboard = db.session.query(Dashboard).filter(
        Dashboard.slug == 'neoretail-v9-visao-geral-industria'
    ).one()

    total_started = perf_counter()
    failures = []
    for chart in sorted(dashboard.slices, key=lambda item: item.id):
        form = json.loads(chart.params)
        grain = form.get('time_grain_sqla', 'P1M')
        axis = form['x_axis']
        metrics = [*form.get('metrics', [])]
        for name in ('metric', 'critical_metric', 'risk_metric'):
            if form.get(name):
                metrics.append(form[name])
        time_column = {
            'timeGrain': grain,
            'columnType': 'BASE_AXIS',
            'sqlExpression': axis,
            'label': axis,
            'expressionType': 'SQL',
            'isColumnReference': True,
        }
        filters = [{'col': 'id_customer', 'op': 'IN', 'val': [CUSTOMER_ID]}]
        datasource_columns = {column.column_name for column in chart.table.columns}
        if CONVERSION_MEASURE and 'nm_measure' in datasource_columns:
            filters.append({'col': 'nm_measure', 'op': 'IN', 'val': [CONVERSION_MEASURE]})
        if FILTER_COLUMN and FILTER_VALUE:
            filters.append({'col': FILTER_COLUMN, 'op': 'IN', 'val': [FILTER_VALUE]})
        common = {
            'time_range': 'No filter',
            'filters': filters,
            'extras': {'time_grain_sqla': grain},
            'metrics': metrics,
            'orderby': [[axis, True]],
            'row_limit': 10000,
        }
        queries = [{**common, 'columns': [time_column]}]
        if form.get('card_variant') == 'bars' and form.get('groupby'):
            queries.append({
                **common,
                'columns': [time_column, *form['groupby']],
            })

        started = perf_counter()
        try:
            # Jinja's get_filters() reads the Chart Data API request payload
            # (or g.form_data for async/cache execution), not QueryContext alone.
            # Populate the same shape so this validator exercises semantic
            # dataset routing exactly as a Native Filter request does.
            g.form_data = {'queries': [queries[0]]}
            context = factory.create(
                datasource={'id': chart.datasource_id, 'type': 'table'},
                queries=queries,
                form_data=form,
            )
            result = ChartDataCommand(context).run()
            counts = [len(item.get('data', [])) for item in result.get('queries', [])]
            sources = []
            for item in result.get('queries', []):
                sql = item.get('query') or item.get('sql') or ''
                if 'nr_overview_semantic_default' in sql:
                    sources.append('overview_semantic_default')
                elif 'history_filtered' in sql:
                    sources.append('overview_detail')
                elif 'nr_osa_semantic_default' in sql:
                    sources.append('osa_semantic_default')
                elif 'daily_summary' in sql:
                    sources.append('daily_summary')
                else:
                    sources.append('detail_or_unknown')
            errors = [
                item.get('error') for item in result.get('queries', [])
                if item.get('error')
            ]
        except Exception as error:
            counts = []
            sources = []
            errors = [f'{type(error).__name__}: {error}']
        elapsed = perf_counter() - started
        payload = {
            'chart': chart.slice_name,
            'dataset_id': chart.datasource_id,
            'seconds': round(elapsed, 4),
            'rows': counts,
            'sources': sources,
            'errors': errors,
        }
        print(json.dumps(payload, ensure_ascii=False))
        if errors:
            failures.append(payload)

    print(json.dumps({
        'dashboard': dashboard.slug,
        'customer_id': CUSTOMER_ID,
        'filter': {FILTER_COLUMN: FILTER_VALUE} if FILTER_COLUMN and FILTER_VALUE else None,
        'conversion_measure': CONVERSION_MEASURE,
        'total_seconds_sequential': round(perf_counter() - total_started, 4),
        'failures': len(failures),
    }, ensure_ascii=False))
    if failures:
        raise SystemExit(json.dumps(failures, ensure_ascii=False))
