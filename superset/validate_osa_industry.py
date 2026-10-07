"""Execute every OSA Industria chart query through Superset."""
import os
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
    failures = []
    for chart in sorted(dashboard.slices, key=lambda item: item.id):
        form = json.loads(chart.params)
        metrics = form.get('metrics', [])
        filters = [{'col': 'id_customer', 'op': 'IN', 'val': [int(os.getenv('NEORETAIL_VALIDATION_CUSTOMER', '142'))]}]
        if 'nm_measure' in {column.column_name for column in chart.table.columns}:
            filters.append({'col': 'nm_measure', 'op': 'IN', 'val': ['unidade']})
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
            g.form_data = {'queries': [queries[0]]}
            result = ChartDataCommand(factory.create(datasource={'id': chart.datasource_id, 'type': 'table'}, queries=queries, form_data=form)).run()
            counts = [len(item.get('data', [])) for item in result.get('queries', [])]
            errors = [item.get('error') for item in result.get('queries', []) if item.get('error')]
        except Exception as error:
            counts, errors = [], [f'{type(error).__name__}: {error}']
        print(json.dumps({'chart': chart.slice_name, 'rows': counts, 'errors': errors}, ensure_ascii=False))
        if errors: failures.append({'chart': chart.slice_name, 'errors': errors})
    if failures: raise AssertionError(failures)

    # Independently reconcile legacy producer columns with the original raw formulas.
    from math import isclose
    from sqlalchemy import text
    from bootstrap_osa_industry import LEGACY_SELLOUT, LEGACY_OSA_LOSS, LOSS_PERCENT_SUMMARY
    from bootstrap_overview import M
    legacy = next(c for c in dashboard.slices if c.table.table_name == 'nr_overview_summary')
    source_expressions = [M['osa']['sqlExpression'], M['sellout']['sqlExpression'], M['osa_loss']['sqlExpression']]
    source_expressions.append("100.0 * SUM(qtd_perda_osa) * AVG(avg_sales_price) / NULLIF(CASE WHEN SUM(faturamento)>0 THEN SUM(faturamento) ELSE SUM(volume_unidades*avg_sales_price) END,0)")
    # The established 31 producer normalizes additive NULL inputs to zero.
    # Reproduce that documented input contract over raw rows, not new semantics.
    for column in ('qtd_problemas_osa', 'qtd_item_ativo_osa', 'qtd_perda_osa', 'faturamento'):
        source_expressions = [e.replace('SUM(' + column + ')', 'SUM(COALESCE(' + column + ', 0))') for e in source_expressions]
    source_expressions = [e.replace('SUM(volume_unidades * avg_sales_price)', 'SUM(COALESCE(volume_unidades, 0) * COALESCE(avg_sales_price, 0))').replace('SUM(volume_unidades*avg_sales_price)', 'SUM(COALESCE(volume_unidades, 0) * COALESCE(avg_sales_price, 0))') for e in source_expressions]
    producer_expressions = [json.loads(legacy.params)['metrics'][0]['sqlExpression'], LEGACY_SELLOUT['sqlExpression'], LEGACY_OSA_LOSS['sqlExpression'], LOSS_PERCENT_SUMMARY['sqlExpression']]
    def monthly(connection, table, date, expressions):
        sql = f"SELECT {date}::date, " + ', '.join(expressions) + f" FROM gold.{table} WHERE id_customer=:tenant GROUP BY {date}::date ORDER BY {date}::date"
        return connection.execute(text(sql), {'tenant': int(os.getenv('NEORETAIL_VALIDATION_CUSTOMER', '142'))}).all()
    with legacy.table.database.get_sqla_engine() as engine, engine.connect() as connection:
        raw = monthly(connection, 'fato_historico', 'mes_ano', source_expressions)
        producer = monthly(connection, 'nr_overview_summary', 'data', producer_expressions)
    assert len(raw) == len(producer) and len(raw) > 0
    for expected, actual in zip(raw, producer):
        assert expected[0] == actual[0]
        for left, right in zip(expected[1:], actual[1:]):
            assert (left is None and right is None) or (left is not None and right is not None and isclose(float(left), float(right), rel_tol=1e-9, abs_tol=1e-7)), (expected[0], left, right)
    print(json.dumps({'legacy_original_formula_parity': True, 'months': len(raw), 'metrics': 4}))
