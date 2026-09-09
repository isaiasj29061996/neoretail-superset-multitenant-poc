"""Cadastra e valida o PostgreSQL Analytics local no Superset."""

from __future__ import annotations

import os
from urllib.parse import quote_plus

from sqlalchemy import text
from superset.app import create_app


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} nao configurada")
    return value


def main() -> None:
    uri = os.getenv("ANALYTICS_SQLALCHEMY_URI", "").strip()
    if not uri:
        user = quote_plus(required("ANALYTICS_DB_USER"))
        password = quote_plus(required("ANALYTICS_DB_PASSWORD"))
        host = required("ANALYTICS_DB_HOST")
        port = required("ANALYTICS_DB_PORT")
        database_name = quote_plus(required("ANALYTICS_DB_NAME"))
        uri = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database_name}"
    app = create_app()
    with app.app_context():
        # O modelo depende do encrypted_field inicializado por create_app().
        from superset import db
        from superset.models.core import Database

        name = "NeoRetail Gold - PostgreSQL Local"
        try:
            database = (
                db.session.query(Database)
                .filter(Database.database_name == name)
                .one_or_none()
            )
        except ValueError as error:
            if "Invalid decryption key" not in str(error):
                raise
            # A POC may be restarted after SUPERSET_SECRET_KEY changes. Clear
            # only the encrypted connection fields for the local Analytics DB;
            # set_sqlalchemy_uri below immediately writes them with the active
            # key. No Analytics schema or business data is modified here.
            db.session.rollback()
            db.session.execute(text(
                "UPDATE dbs SET password = NULL, encrypted_extra = NULL, "
                "server_cert = NULL WHERE database_name = :name"
            ), {"name": name})
            db.session.flush()
            database = (
                db.session.query(Database)
                .filter(Database.database_name == name)
                .one_or_none()
            )
        if database is None:
            database = Database(database_name=name)
            db.session.add(database)

        # O setter separa a senha da URI mascarada conforme o modelo do
        # Superset. O flush mantem a instancia ligada a sessao para que a URI
        # possa ser descriptografada durante get_sqla_engine().
        database.set_sqlalchemy_uri(uri)
        database.expose_in_sqllab = True
        database.allow_ctas = False
        database.allow_cvas = False
        database.allow_dml = False
        database.allow_file_upload = False
        db.session.flush()

        # No Superset 6, get_sqla_engine() devolve um context manager que
        # fornece a Engine. A transacao deve ser aberta somente na Engine.
        with database.get_sqla_engine() as engine:
            with engine.begin() as connection:
                if connection.execute(text("SELECT 1")).scalar_one() != 1:
                    raise RuntimeError("SELECT 1 falhou no PostgreSQL Analytics")
                for schema in ("audit", "bronze", "silver", "gold"):
                    connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
                gold = connection.execute(
                    text(
                        "SELECT COUNT(*) FROM information_schema.schemata "
                        "WHERE schema_name = 'gold'"
                    )
                ).scalar_one()
                if gold != 1:
                    raise RuntimeError("Schema gold ausente no PostgreSQL Analytics")
        db.session.commit()
        print("PostgreSQL Analytics cadastrado no Superset e SELECT 1 validado.")


if __name__ == "__main__":
    main()
