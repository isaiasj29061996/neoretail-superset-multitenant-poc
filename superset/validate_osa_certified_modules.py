"""Read-only SQL/period checks and real Guest JWT checks for OSA extraction.

Candidate SQL is assigned only in a metadata transaction that is always rolled
back. No tenant, role, embedding or RLS configuration is changed. Guest tokens
are ephemeral and never printed. This exercises QueryContext/ChartData rather
than claiming that an administrative id_customer filter proves guest isolation.
It uses isolated request contexts, but shares the existing read-only data source;
it is not a second tenant data fixture or a browser embedding test.
"""
from datetime import date
import json

from flask import g, request
from flask_login import login_user, logout_user
from jinja2 import Environment, StrictUndefined
from sqlalchemy import text
from superset.app import create_app

from neoretail_bootstrap.osa_certified import semantics, matrices


DIMENSIONS = ('rede', 'bandeira', 'uf', 'cidade', 'tipo_local', 'loja', 'regiao',
              'tp_activity_level', 'item', 'descricao_marca', 'hierarquia_1', 'hierarquia_2', 'hierarquia_3')


def render(sql, selected):
    env = Environment(undefined=StrictUndefined)
    env.filters['where_in'] = lambda values: '(' + ', '.join("'" + str(value).replace("'", "''") + "'" for value in values) + ')'
    return env.from_string(sql).render(get_filters=lambda column, **kwargs: selected.get(column, []))


def check_periods(connection):
    # Includes a missing December, January rollover, and different cause/history
    # anchors. Future-in-month rows retain the original MTD/YTD semantics.
    dates = ['2025-10-01', '2025-11-01', '2026-01-01', '2026-01-20']
    cause = semantics.cause_period_sql().split('CROSS JOIN LATERAL (', 1)[1].split(') p\n', 1)[0]
    fragments = [matrices._period_rows('b', 'x'), cause]
    checks = 0
    for anchor in ('2026-01-15', '2025-12-15'):
        latest = date.fromisoformat(anchor)
        start = latest.replace(day=1)
        month_index = start.year * 12 + start.month - 1
        for fragment in fragments:
            sql = "WITH b(data) AS (VALUES " + ','.join("(DATE '"+value+"')" for value in dates) + "), x(latest_data) AS (VALUES (DATE '"+anchor+"')) SELECT b.data,p.osa_period FROM b CROSS JOIN x CROSS JOIN LATERAL ("+fragment+") p(osa_period,osa_period_order)"
            actual = {(str(row[0]), row[1]) for row in connection.execute(text(sql))}
            expected = set()
            for value in dates:
                day = date.fromisoformat(value)
                index = day.year * 12 + day.month - 1
                if index == month_index: expected.add((value, 'MTD'))
                if index == month_index-1: expected.add((value, 'Mês Anterior'))
                if index >= month_index-2 and day <= latest: expected.add((value, 'U3M'))
                if day.year == latest.year: expected.add((value, 'YTD'))
            assert actual == expected, (anchor, actual, expected)
            checks += 1
    return checks


def main():
    app = create_app()
    with app.app_context():
        from superset import db, security_manager
        from superset.models.dashboard import Dashboard
        from superset.connectors.sqla.models import SqlaTable
        from superset.commands.chart.data.get_data_command import ChartDataCommand
        from superset.common.query_context_factory import QueryContextFactory

        dashboard = db.session.query(Dashboard).filter_by(slug='neoretail-v9-osa-industria-certified').one()
        assert len(dashboard.slices) == 14
        datasets = {chart.table.table_name: chart.table for chart in dashboard.slices}
        builders = {
            'nr_osa_monthly_certified': semantics.monthly_overview_sql,
            'nr_osa_weekly_certified': semantics.weekly_overview_sql,
            'nr_osa_causes_certified': semantics.cause_period_sql,
            **{'nr_osa_matrix_'+key+'_certified': lambda column=column: matrices.matrix_period_sql(column)
               for key, (_, column) in matrices.MATRIX_SCOPES.items()},
        }
        original_sql = {name: datasets[name].sql for name in builders}
        report = {'explain_checks': 0, 'period_checks': 0, 'guest_checks': 0}
        try:
            table = next(iter(datasets.values()))
            with table.database.get_sqla_engine() as engine, engine.connect() as connection:
                connection.execute(text('SET TRANSACTION READ ONLY'))
                for builder in builders.values():
                    cases = [{}] + [{'nm_measure': [{'op': op, 'val': ['hectolitro']}]} for op in ('IN', 'NOT IN')]
                    cases += [{dim: [{'op': op, 'val': ['RJ' if dim == 'uf' else 'test-item']}]} for dim in DIMENSIONS for op in ('IN', 'NOT IN')]
                    for selected in cases:
                        connection.execute(text('EXPLAIN '+render(builder(), selected))).all()
                        report['explain_checks'] += 1
                report['period_checks'] = check_periods(connection)
                connection.connection.rollback()
            print('PASS SQL planning and temporal fixtures: '+json.dumps(report), flush=True)

            embedded = dashboard.embedded
            assert embedded, 'Guest validation requires existing embedding; it must not be created by this validator'
            resource_id = str(embedded[0].uuid)
            for customer in (142, -1):
                token = security_manager.create_guest_access_token(
                    user={'username': 'osa-refactor-validation'},
                    resources=[{'type': 'dashboard', 'id': resource_id}],
                    rls=[{'clause': 'id_customer = '+str(customer)}],
                )
                with app.test_request_context('/', headers={app.config['GUEST_TOKEN_HEADER_NAME']: token}):
                    guest = security_manager.get_guest_user_from_request(request)
                    assert guest and security_manager.is_guest_user(guest)
                    login_user(guest)
                    g.user = guest
                    try:
                        for name in builders:
                            # Each Guest request has its own session lifecycle.
                            # Reload and assign candidate SQL in that session so
                            # both authorized and denied tokens test the candidate.
                            dataset = db.session.query(SqlaTable).filter_by(table_name=name).one()
                            dataset.sql = builders[name]()
                            # No explicit id_customer query filter: isolation must
                            # originate from the verified Guest Token RLS rule.
                            query = {'columns': ['id_customer'], 'metrics': [], 'row_limit': 100,
                                     'filters': [{'col': 'nm_measure', 'op': 'IN', 'val': ['unidade']}]}
                            form = {'dashboardId': dashboard.id, 'datasource': str(dataset.id)+'__table', 'force': True}
                            g.form_data = form
                            context = QueryContextFactory().create(
                                datasource={'id': dataset.id, 'type': 'table'},
                                queries=[query], form_data=form, force=True,
                            )
                            assert context.datasource.sql == builders[name]()
                            result = ChartDataCommand(context).run()
                            outputs = result['queries']
                            assert outputs and not any(row.get('error') for row in outputs), name
                            rows = [row for output in outputs for row in output.get('data', [])]
                            assert rows if customer == 142 else not rows, (name, customer, len(rows))
                            assert all(int(row['id_customer']) == customer for row in rows), name
                            assert any('id_customer = '+str(customer) in output.get('query', '') for output in outputs), name
                            report['guest_checks'] += 1
                            print('PASS Guest RLS: '+name+' customer='+str(customer), flush=True)
                    finally:
                        logout_user()
                        g.user = None
        finally:
            db.session.rollback()
        # Guest request teardown may detach ORM objects. Verify database values
        # through a fresh scalar query rather than comparing stale Python state.
        restored = dict(db.session.query(SqlaTable.table_name, SqlaTable.sql).filter(
            SqlaTable.table_name.in_(list(builders)),
        ).all())
        assert restored == original_sql
        report['metadata_sql_restored'] = True
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
