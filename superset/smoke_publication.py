"""End-to-end smoke test for the NeoRetail publication endpoint."""
from __future__ import annotations

import os

from superset.app import create_app


def main():
    app = create_app()
    app.config["WTF_CSRF_ENABLED"] = False
    with app.app_context():
        from superset import db
        from superset.models.dashboard import Dashboard

        username = os.getenv("SUPERSET_ADMIN_USERNAME", "admin")
        user = app.appbuilder.sm.find_user(username=username)
        dashboard = db.session.query(Dashboard).filter(
            Dashboard.slug == "neoretail-v9-visao-geral-industria"
        ).one()
        if user is None or not any(role.name == "Admin" for role in user.roles):
            raise RuntimeError("Usuário administrador do Superset não encontrado.")
        user_id = user.id
        dashboard_id = dashboard.id

    anonymous_client = app.test_client()
    anonymous = anonymous_client.get(
        f"/api/neoretail/dashboard/{dashboard_id}/publication"
    )
    if anonymous.status_code != 403:
        raise RuntimeError("A rota de publicação aceitou uma sessão anônima.")
    client = app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True

    status = client.get(
        f"/api/neoretail/dashboard/{dashboard_id}/publication"
    )
    if status.status_code != 200:
        raise RuntimeError(f"Status de publicação falhou: {status.status_code}")
    publish = client.post(
        f"/api/neoretail/dashboard/{dashboard_id}/publish", json={}
    )
    if publish.status_code != 200:
        raise RuntimeError(
            f"Publicação falhou: {publish.status_code} {publish.get_data(as_text=True)}"
        )
    result = publish.get_json()
    if not result.get("published") or result.get("dashboardKey") != "overview":
        raise RuntimeError(f"Resposta de publicação inesperada: {result}")
    print({"status": "ok", "dashboardKey": result["dashboardKey"]})


if __name__ == "__main__":
    main()
