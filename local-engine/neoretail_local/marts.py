"""Render the same versioned marts per tenant and publish explicit-column serving views."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import sys

import psycopg2
from psycopg2 import sql
from .customers import resolve_tenant, load_customer_registry
from .settings import Settings

ROOT = Path(os.getenv("NEORETAIL_REPO_ROOT", "/repo"))
sys.path.insert(0, str(ROOT / "superset"))
from neoretail_bootstrap.core.sql_sources import rewrite_gold_sources, in_caller_transaction


def build_marts(settings):
    # Re-resolve rather than accepting an arbitrary target schema argument.
    context = resolve_tenant(settings.customers_config_path, settings.id_customer, require_source=True)
    if context != settings.tenant_context: raise RuntimeError("Noncanonical mart context")
    files = sorted((ROOT / "analytics-db/views").glob("*.sql")) + sorted((ROOT / "analytics-db/marts").glob("*.sql"))
    if any("45_osa" in path.name for path in files):
        raise RuntimeError("Unversioned legacy OSA marts must not enter this runtime")
    report = []
    with psycopg2.connect(settings.psycopg_dsn) as connection:
        # Existing serving views depend on materialized views recreated by the
        # versioned scripts. Preserve and restore them within ONE transaction;
        # failure rolls back both marts and serving, without changing other Gold.
        with connection.cursor() as cursor:
            # Keep compilation out of this controlled bulk refresh. PostgreSQL
            # 16.15/alpine terminated with SIGSEGV on the final LACTALIS mart
            # with JIT enabled; this changes execution only, not the SQL contract.
            cursor.execute('SET LOCAL jit = off')
            cursor.execute("""SELECT DISTINCT v.relname, pg_get_viewdef(v.oid, true)
                FROM pg_class v JOIN pg_namespace vn ON vn.oid=v.relnamespace
                JOIN pg_rewrite r ON r.ev_class=v.oid
                JOIN pg_depend d ON d.objid=r.oid
                JOIN pg_class source ON source.oid=d.refobjid
                JOIN pg_namespace sn ON sn.oid=source.relnamespace
                WHERE vn.nspname='serving' AND v.relkind='v' AND sn.nspname=%s
                ORDER BY v.relname""", (context.gold_schema,))
            serving = cursor.fetchall()
            for name, _ in serving:
                cursor.execute(sql.SQL('DROP VIEW serving.{}').format(sql.Identifier(name)))
        for path in files:
            original = path.read_text(encoding="utf-8")
            rendered = in_caller_transaction(rewrite_gold_sources(original, context.gold_schema))
            with connection.cursor() as cursor:
                cursor.execute(rendered)
            report.append(path.name)
            print(json.dumps({"mart_file": path.name, "tenant": context.tenant_key, "schema": context.gold_schema}), flush=True)
        with connection.cursor() as cursor:
            for name, definition in serving:
                cursor.execute(sql.SQL('CREATE VIEW serving.{} AS ').format(sql.Identifier(name)) + sql.SQL(definition))
    print(json.dumps({'marts':'committed', 'tenant':context.tenant_key, 'serving_views_restored':len(serving)}), flush=True)
    return report


def publish_serving(settings, selectors, *, keep_published=False):
    contexts = [resolve_tenant(settings.customers_config_path, selector, require_source=True) for selector in selectors]
    if len({c.id_customer for c in contexts}) != len(contexts) or any(c.id_customer == 142 for c in contexts):
        raise RuntimeError("Serving requires distinct active POC tenants; AMBEV is baseline only")
    if not contexts: raise RuntimeError("No published tenant selected")
    with psycopg2.connect(settings.psycopg_dsn) as connection, connection.cursor() as cursor:
        if keep_published:
            # Refreshing one tenant must not detach the others from shared views.
            # Resolve actual dependencies through the registry, never raw schemas.
            cursor.execute("""SELECT DISTINCT sn.nspname
                FROM pg_class v JOIN pg_namespace vn ON vn.oid=v.relnamespace
                JOIN pg_rewrite r ON r.ev_class=v.oid
                JOIN pg_depend d ON d.objid=r.oid AND d.refclassid='pg_class'::regclass
                JOIN pg_class source ON source.oid=d.refobjid
                JOIN pg_namespace sn ON sn.oid=source.relnamespace
                WHERE vn.nspname='serving' AND v.relkind='v' AND sn.nspname<>'serving'
                ORDER BY sn.nspname""")
            registry = load_customer_registry(settings.customers_config_path)[1]
            registered = {context.gold_schema:context for context in registry}
            selected = {context.id_customer for context in contexts}
            for (schema,) in cursor.fetchall():
                if schema not in registered or registered[schema].id_customer == 142:
                    raise RuntimeError(f"Unregistered or legacy serving dependency: {schema}")
                selected.add(registered[schema].id_customer)
            contexts = [resolve_tenant(settings.customers_config_path, context.id_customer, require_source=True)
                        for context in registry if context.id_customer in selected]
        contracts = {}
        for context in contexts:
            cursor.execute("""
                SELECT c.relname,a.attname,pg_catalog.format_type(a.atttypid,a.atttypmod)
                FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                JOIN pg_attribute a ON a.attrelid=c.oid
                WHERE n.nspname=%s AND c.relkind IN ('r','v','m')
                  AND c.relname NOT LIKE '_stage_%%' AND a.attnum>0 AND NOT a.attisdropped
                ORDER BY c.relname,a.attnum
            """, (context.gold_schema,))
            relations = {}
            for name, column, pgtype in cursor.fetchall(): relations.setdefault(name, []).append((column, pgtype))
            required = {'nr_overview_history', 'nr_panorama_weekly', 'nr_stock_tasks',
                        'nr_export_daily', 'nr_export_monthly', 'nr_filter_options'}
            if not required <= relations.keys():
                raise RuntimeError(f"Incomplete marts for {context.tenant_key}: {sorted(required-relations.keys())}")
            for name, columns in relations.items():
                if "id_customer" not in [column for column, _ in columns]: raise RuntimeError(f"{name}: missing tenant")
                cursor.execute(
                    sql.SQL("SELECT 1 FROM {}.{} WHERE id_customer IS NULL OR id_customer <> %s LIMIT 1").format(
                        sql.Identifier(context.gold_schema), sql.Identifier(name)), (context.id_customer,))
                if cursor.fetchone(): raise RuntimeError(f"{name}: contaminated tenant data")
            contracts[context.tenant_key] = relations
        canonical = contracts[contexts[0].tenant_key]
        for context in contexts[1:]:
            if contracts[context.tenant_key] != canonical:
                raise RuntimeError(f"Serving column/type contracts differ: {context.tenant_key}")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS serving")
        for name, columns in canonical.items():
            explicit = sql.SQL(", ").join(sql.Identifier(column) for column, _ in columns)
            branches = [sql.SQL("SELECT {} FROM {}.{} WHERE id_customer = {}").format(
                explicit, sql.Identifier(c.gold_schema), sql.Identifier(name), sql.Literal(c.id_customer)) for c in contexts]
            cursor.execute(sql.SQL("CREATE OR REPLACE VIEW serving.{} AS {}").format(
                sql.Identifier(name), sql.SQL(" UNION ALL ").join(branches)))
    print(json.dumps({"serving": "committed", "tenant_ids": [c.id_customer for c in contexts], "relations": len(canonical)}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", "--customer", required=True)
    parser.add_argument("--serving-tenants", nargs="+")
    parser.add_argument("--keep-published-tenants", action="store_true")
    args = parser.parse_args()
    if args.keep_published_tenants and not args.serving_tenants:
        parser.error('--keep-published-tenants requires --serving-tenants')
    settings = Settings.from_env(require_blob=False, customer_selector=args.tenant)
    if args.serving_tenants:
        publish_serving(settings, args.serving_tenants, keep_published=args.keep_published_tenants)
    else:
        build_marts(settings)


if __name__ == "__main__":
    main()
