"""Enable the four NeoRetail dashboards for SDK embedding.

Only Superset metadata is changed. Dashboard slugs and stable embedded UUIDs
come from the same catalog used by the portal.
"""
from __future__ import annotations

import json
import os
import uuid

import yaml
from superset.app import create_app


CATALOG_PATH = os.getenv("TENANTS_CONFIG", "/app/config/tenants.yaml")
ALLOWED_DOMAINS = os.getenv(
    "EMBED_ALLOWED_DOMAINS", "http://localhost:3000"
).split(",")

EMBEDDED_FIT_CSS = (
    " body { overflow-x: hidden !important; }"
)


def main():
    catalog = yaml.safe_load(open(CATALOG_PATH, encoding="utf-8"))
    app = create_app()
    with app.app_context():
        from superset import db
        from superset.models.dashboard import Dashboard
        from superset.models.embedded_dashboard import EmbeddedDashboard
        from superset.models.slice import Slice

        for chart_name in (
            "[OSA Indústria] Perda OSA por motivo",
            "[OSA Indústria] Perda por causa OSA",
        ):
            chart = db.session.query(Slice).filter(Slice.slice_name == chart_name).one_or_none()
            if chart is not None:
                params = json.loads(chart.params)
                params["time_range"] = "No filter"
                params.pop("adhoc_filters", None)
                chart.params = json.dumps(params, ensure_ascii=False)

        result = {}
        for key, definition in catalog["dashboards"].items():
            dashboard = db.session.query(Dashboard).filter(
                Dashboard.slug == definition["slug"]
            ).one_or_none()
            if dashboard is None:
                raise RuntimeError(
                    f"Dashboard '{definition['slug']}' não encontrado; execute os bootstraps primeiro."
                )

            metadata = json.loads(dashboard.json_metadata or "{}")
            metadata["native_filter_configuration"] = [
                native_filter
                for native_filter in metadata.get("native_filter_configuration", [])
                if not any(
                    target.get("column", {}).get("name") == "id_customer"
                    for target in native_filter.get("targets", [])
                )
            ]
            dashboard.json_metadata = json.dumps(metadata, ensure_ascii=False)
            if EMBEDDED_FIT_CSS not in (dashboard.css or ""):
                dashboard.css = (dashboard.css or "") + EMBEDDED_FIT_CSS

            embedded_uuid = uuid.UUID(str(definition["embedded_id"]))
            embedded = db.session.query(EmbeddedDashboard).filter(
                EmbeddedDashboard.dashboard_id == dashboard.id
            ).one_or_none()
            if embedded is None:
                embedded = EmbeddedDashboard(
                    uuid=embedded_uuid,
                    dashboard_id=dashboard.id,
                )
                db.session.add(embedded)
            else:
                embedded.uuid = embedded_uuid
            embedded.allow_domain_list = ",".join(
                domain.strip() for domain in ALLOWED_DOMAINS if domain.strip()
            )
            result[key] = {
                "dashboard_id": dashboard.id,
                "slug": dashboard.slug,
                "embedded_id": str(embedded_uuid),
                "allowed_domains": embedded.allowed_domains,
            }

        db.session.commit()
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
