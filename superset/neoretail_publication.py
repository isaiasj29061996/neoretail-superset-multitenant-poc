"""NeoRetail publication API mounted inside the Superset application."""
from __future__ import annotations

import json
import os
import re
import tempfile
import uuid
from pathlib import Path

import yaml
from flask import jsonify
from flask_login import current_user


CATALOG_PATH = Path(os.getenv("NEORETAIL_TENANTS_CONFIG", "/app/config/tenants.yaml"))
PUBLISHED_PATH = Path(os.getenv("NEORETAIL_PUBLISHED_CATALOG", "/generated/neoretail-published-dashboards.json"))
PRODUCT_URL = os.getenv("NEORETAIL_PRODUCT_URL", "http://localhost:3000")
ALLOWED_DOMAINS = [
    value.strip()
    for value in os.getenv("EMBED_ALLOWED_DOMAINS", PRODUCT_URL).split(",")
    if value.strip()
]


def _is_admin() -> bool:
    return bool(
        current_user.is_authenticated
        and any(getattr(role, "name", "") == "Admin" for role in current_user.roles)
    )


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _catalog():
    base = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))
    dynamic = _read_json(PUBLISHED_PATH, {"dashboards": {}})
    return base, dynamic


def _safe_key(value: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return key.removeprefix("neoretail-v9-") or "dashboard"


def _definition_for(dashboard, embedded_id: str):
    base, dynamic = _catalog()
    configured = next(
        (
            (key, value)
            for key, value in base.get("dashboards", {}).items()
            if value.get("slug") == dashboard.slug
        ),
        None,
    )
    if configured:
        key, definition = configured
        definition = dict(definition)
    else:
        key = _safe_key(dashboard.slug or dashboard.dashboard_title)
        existing_keys = {
            **base.get("dashboards", {}),
            **dynamic.get("dashboards", {}),
        }
        if key in existing_keys and existing_keys[key].get("slug") != dashboard.slug:
            key = f"{key}-{dashboard.id}"
        lowered = dashboard.dashboard_title.lower()
        section = "tasks" if "tarefa" in lowered else "panorama"
        definition = {
            "title": dashboard.dashboard_title,
            "menu_label": dashboard.dashboard_title,
            "section": section,
            "slug": dashboard.slug,
            "required_module": "tarefas" if section == "tasks" else "visao_industria",
            "embedded_height": 1600,
        }
    definition["embedded_id"] = embedded_id
    return key, definition, dynamic


def _write_dynamic_catalog(payload) -> None:
    PUBLISHED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=PUBLISHED_PATH.parent, delete=False
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(PUBLISHED_PATH)


def register_neoretail_publication(app) -> None:
    if "neoretail_publication_status" in app.view_functions:
        return

    @app.get("/api/neoretail/dashboard/<int:dashboard_id>/publication")
    def neoretail_publication_status(dashboard_id):
        if not _is_admin():
            return jsonify(message="Apenas administradores podem publicar no NeoRetail."), 403
        from superset import db
        from superset.models.dashboard import Dashboard
        from superset.models.embedded_dashboard import EmbeddedDashboard

        dashboard = db.session.get(Dashboard, dashboard_id)
        if dashboard is None:
            return jsonify(message="Dashboard não encontrado."), 404
        embedded = db.session.query(EmbeddedDashboard).filter(
            EmbeddedDashboard.dashboard_id == dashboard.id
        ).one_or_none()
        base, dynamic = _catalog()
        definitions = {
            **base.get("dashboards", {}),
            **dynamic.get("dashboards", {}),
        }
        match = next(
            ((key, value) for key, value in definitions.items() if value.get("slug") == dashboard.slug),
            None,
        )
        return jsonify(
            published=bool(dashboard.published and embedded and match),
            dashboardKey=match[0] if match else None,
            productUrl=f"{PRODUCT_URL}/app?dashboard={match[0]}" if match else None,
        )

    @app.post("/api/neoretail/dashboard/<int:dashboard_id>/publish")
    def neoretail_publish_dashboard(dashboard_id):
        if not _is_admin():
            return jsonify(message="Apenas administradores podem publicar no NeoRetail."), 403
        from superset import db
        from superset.models.dashboard import Dashboard
        from superset.models.embedded_dashboard import EmbeddedDashboard

        dashboard = db.session.get(Dashboard, dashboard_id)
        if dashboard is None:
            return jsonify(message="Dashboard não encontrado."), 404
        if not dashboard.slug:
            dashboard.slug = f"neoretail-dashboard-{dashboard.id}"

        embedded = db.session.query(EmbeddedDashboard).filter(
            EmbeddedDashboard.dashboard_id == dashboard.id
        ).one_or_none()
        if embedded is None:
            embedded = EmbeddedDashboard(
                uuid=uuid.uuid5(uuid.NAMESPACE_URL, f"neoretail:{dashboard.slug}"),
                dashboard_id=dashboard.id,
            )
            db.session.add(embedded)
        embedded.allow_domain_list = ",".join(ALLOWED_DOMAINS)
        dashboard.published = True

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
        db.session.commit()

        key, definition, dynamic = _definition_for(dashboard, str(embedded.uuid))
        dynamic.setdefault("version", 1)
        dynamic.setdefault("dashboards", {})[key] = definition
        _write_dynamic_catalog(dynamic)
        return jsonify(
            published=True,
            dashboardKey=key,
            embeddedId=str(embedded.uuid),
            productUrl=f"{PRODUCT_URL}/app?dashboard={key}",
            message="Dashboard publicado no NeoRetail.",
        )
