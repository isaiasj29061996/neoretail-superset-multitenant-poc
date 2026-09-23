"""Validate the Export dashboards, indicator selector, and virtual SQL path."""
from __future__ import annotations

import json

from flask import g
from flask_login import login_user
from superset.app import create_app

from bootstrap_export import EXPORT_VALUE, INDICATORS


CUSTOMER_ID = 142
MONTHLY_SLUG = "neoretail-v9-exportacao-historico-mes"


def main() -> None:
    app = create_app()
    with app.test_request_context("/"):
        from superset import db, security_manager
        from superset.commands.chart.data.get_data_command import ChartDataCommand
        from superset.common.query_context_factory import QueryContextFactory
        from superset.connectors.sqla.models import SqlaTable
        from superset.models.dashboard import Dashboard

        admin = security_manager.find_user(username="admin") or db.session.query(
            security_manager.user_model
        ).first()
        login_user(admin)
        g.user = admin

        dashboard = db.session.query(Dashboard).filter(
            Dashboard.slug == MONTHLY_SLUG
        ).one()
        metadata = json.loads(dashboard.json_metadata or "{}")
        indicator_filter = next(
            item
            for item in metadata.get("native_filter_configuration", [])
            if item.get("name") == "Indicador"
        )
        indicator_dataset_id = indicator_filter["targets"][0]["datasetId"]
        indicator_dataset = db.session.get(SqlaTable, indicator_dataset_id)
        if indicator_dataset is None or indicator_dataset.table_name != "nr_export_indicators":
            raise AssertionError("O filtro Indicador não aponta para a dimensão isolada.")

        chart = next(
            item for item in dashboard.slices
            if item.slice_name == "[Exportação mês] Produto"
        )
        factory = QueryContextFactory()
        failures = []
        for indicator in INDICATORS:
            native_filter = {
                "col": "indicador", "op": "IN", "val": [indicator],
            }
            query = {
                "columns": ["ano", "mes"],
                "metrics": [EXPORT_VALUE],
                "filters": [
                    {"col": "id_customer", "op": "IN", "val": [CUSTOMER_ID]},
                    native_filter,
                ],
                "row_limit": 100,
            }
            try:
                g.form_data = {"extra_filters": [native_filter]}
                result = ChartDataCommand(factory.create(
                    datasource={"id": chart.datasource_id, "type": "table"},
                    queries=[query],
                    form_data={
                        **json.loads(chart.params),
                        "force": True,
                        "extra_filters": [native_filter],
                    },
                )).run()
                g.form_data = {}
                response = result.get("queries", [])[0]
                sql = response.get("query") or response.get("sql") or ""
                error = response.get("error")
                selected_literal = f"CAST('{indicator}' AS TEXT) AS indicador"
                if error or "CROSS JOIN" in sql.upper() or selected_literal not in sql:
                    failures.append({"indicator": indicator, "error": error, "sql": sql})
                print(json.dumps({
                    "indicator": indicator,
                    "rows": len(response.get("data", []) or []),
                    "cross_join": "CROSS JOIN" in sql.upper(),
                    "selected_in_sql": selected_literal in sql,
                    "error": error,
                }, ensure_ascii=False))
            except Exception as error:  # keep reporting all indicator paths
                failures.append({"indicator": indicator, "error": str(error)})

        if failures:
            raise SystemExit(json.dumps(failures, ensure_ascii=False))


if __name__ == "__main__":
    main()
