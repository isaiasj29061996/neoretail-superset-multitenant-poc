"""Record the unsupported conversion fixture independently; no altered expected values."""
import json
from pathlib import Path
from flask import g
from flask_login import login_user
from sqlalchemy import text
from superset.app import create_app
from validate_panorama_inventory_filters import filtered_source, compare_components
from validate_panorama_stock import MONTHLY_SOURCE
from validate_panorama_inventory_tabs import execute

app = create_app()
with app.test_request_context('/'):
    from superset import db, security_manager
    from superset.models.dashboard import Dashboard
    from superset.commands.chart.data.get_data_command import ChartDataCommand
    from superset.common.query_context_factory import QueryContextFactory
    admin = security_manager.find_user(username='admin')
    login_user(admin)
    g.user = admin
    dashboard = db.session.query(Dashboard).filter_by(slug='neoretail-v9-panorama-industria').one()
    chart = next(c for c in dashboard.slices if c.slice_name == '[Panorama] Evolutivo de estoque — Estoque mensal')
    item = '7891097010781 - Iog Ped Fruta Morango Bat 450G'
    report = {'tenant': 290, 'item': item, 'scenarios': []}
    with chart.table.database.get_sqla_engine() as engine, engine.connect() as connection:
        options = connection.execute(text('''
            SELECT c.nm_measure,count(*) AS mappings,MIN(c.conversion_rate) AS minimum,MAX(c.conversion_rate) AS maximum
            FROM gold.dim_itens i JOIN gold.dim_conversao c
              ON c.id_customer=i.id_customer AND c.id_item::text=i.id_item::text
            WHERE i.id_customer=290 AND i.item=:item GROUP BY c.nm_measure ORDER BY 1
        '''), {'item': item}).mappings().all()
        report['source_conversions'] = [dict(row) for row in options]
        for measure in ('hectolitro', 'quilograma'):
            expected = connection.execute(filtered_source(MONTHLY_SOURCE, 'item', 'IN'),
                {'customer': 290, 'dimension': item, 'measure': measure}).mappings().all()
            actual = execute(QueryContextFactory(), ChartDataCommand, chart, [
                {'col': 'id_customer', 'op': 'IN', 'val': [290]},
                {'col': 'item', 'op': 'IN', 'val': [item]},
                {'col': 'nm_measure', 'op': 'IN', 'val': [measure]},
            ])[0]['data']
            scenario = {'measure': measure, 'source_periods': len(expected), 'chart_periods': len(actual),
                        'chart_quantity_nulls': sum(row['Estoque quantidade'] is None for row in actual)}
            print(json.dumps({'scenario': scenario, 'source_sample': [dict(r) for r in expected[:1]], 'chart_sample': actual[:1]}, default=str), flush=True)
            if measure == 'quilograma':
                compare_components(expected, actual, {'Estoque preço custo': 'stock_cost_sum', 'Estoque quantidade': 'stock_qty_sum'}, 'independent quilograma check')
                scenario['source_chart_reconciled'] = True
            else:
                assert not expected and not actual
                assert 'hectolitro' not in {row['nm_measure'] for row in options}
                scenario['missing_source_conversion_returns_no_evidence'] = True
            report['scenarios'].append(scenario)
    Path('/generated/lactalis_inventory_conversion_diagnosis.json').write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
    print(json.dumps(report, default=str))
