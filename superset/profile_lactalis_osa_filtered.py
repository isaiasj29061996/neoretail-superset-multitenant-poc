"""Profile the exact failed ChartData SQL and execution-only JIT alternative."""
import json
from pathlib import Path
from flask import g
from flask_login import login_user
from sqlalchemy import text
from superset.app import create_app
from validate_overview_quantity import execute

app = create_app()
with app.test_request_context('/'):
    from superset import db, security_manager
    from superset.models.dashboard import Dashboard
    from superset.common.query_context_factory import QueryContextFactory
    from superset.commands.chart.data.get_data_command import ChartDataCommand
    login_user(security_manager.find_user(username='admin'))
    g.user = security_manager.find_user(username='admin')
    dashboard = db.session.query(Dashboard).filter_by(slug='neoretail-v9-osa-industria-certified').one()
    chart = next(c for c in dashboard.slices if c.slice_name == '[OSA Certificada] Visão geral — Valor mensal')
    result = execute(QueryContextFactory(), ChartDataCommand, chart, [
        {'col': 'id_customer', 'op': 'IN', 'val': [290]},
        {'col': 'nm_measure', 'op': 'IN', 'val': ['unidade']},
        {'col': 'rede', 'op': 'IN', 'val': ['CENCOSUD']},
    ])
    query = result['query']
    Path('/generated/lactalis_osa_filtered_query.sql').write_text(query, encoding='utf-8')
    report = {}
    with chart.table.database.get_sqla_engine() as engine, engine.connect() as connection:
        for mode in ('default', 'jit_off'):
            if mode == 'jit_off': connection.execute(text('SET jit = off'))
            plan = connection.execute(text('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) ' + query)).scalar_one()[0]
            report[mode] = plan
            print(json.dumps({'mode': mode, 'execution_ms': plan['Execution Time'], 'jit': plan.get('JIT'),
                              'shared_read_blocks': plan['Plan'].get('Shared Read Blocks'),
                              'temp_read_blocks': plan['Plan'].get('Temp Read Blocks')}), flush=True)
    Path('/generated/lactalis_osa_filtered_profile.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
