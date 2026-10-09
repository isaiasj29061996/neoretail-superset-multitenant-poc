"""Shared metadata helpers extracted without changing defaults."""
from __future__ import annotations

import json
import os
from .sql_sources import rewrite_gold_sources
def upsert_dataset(session, model, database, name, *, table_name=None, sql=None):
    schema = os.getenv("NEORETAIL_CONSUMPTION_SCHEMA", "gold")
    if schema not in ("gold", "serving"):
        raise ValueError("Unsupported consumption schema")
    if sql is not None:
        sql = rewrite_gold_sources(sql, schema)
    dataset = session.query(model).filter(model.table_name == name).one_or_none()
    needs_metadata = dataset is None
    if dataset is None:
        dataset = model(table_name=name, schema=schema, database=database)
        session.add(dataset)
    else:
        source_only = (
            dataset.schema == "gold" and schema == "serving"
            and sql == (rewrite_gold_sources(dataset.sql, schema) if dataset.sql is not None else None)
        )
        needs_metadata = (
            ((dataset.sql != sql or dataset.schema != schema) and not source_only)
            or (table_name is not None and dataset.table_name != table_name)
            or not dataset.columns
        )
    dataset.database = database
    dataset.schema = schema
    dataset.sql = sql
    if table_name:
        dataset.table_name = table_name
    session.flush()
    if needs_metadata:
        dataset.fetch_metadata()
        session.flush()
    return dataset


def upsert_overview_chart(session, Slice, dataset, title, params):
    chart = session.query(Slice).filter(Slice.slice_name == title).one_or_none()
    if chart is None:
        chart = Slice(slice_name=title)
        session.add(chart)
    chart.datasource_type = "table"
    chart.datasource_id = dataset.id
    chart.viz_type = "neoretail-kpi-card"
    chart.params = json.dumps(params, ensure_ascii=False)
    chart.description = "Visão geral NeoRetail V9 baseada no PBIX de referência."
    session.flush()
    return chart


def upsert_chart(
    session, Slice, dataset, title, params, viz_type="neoretail-kpi-card",
    legacy_titles=(),
):
    chart = session.query(Slice).filter(Slice.slice_name == title).one_or_none()
    if chart is None and legacy_titles:
        chart = session.query(Slice).filter(Slice.slice_name.in_(legacy_titles)).one_or_none()
    if chart is None:
        chart = Slice(slice_name=title)
        session.add(chart)
    chart.slice_name = title
    chart.datasource_type = "table"
    chart.datasource_id = dataset.id
    chart.viz_type = viz_type
    chart.params = json.dumps(params, ensure_ascii=False)
    chart.description = "Panorama da indústria NeoRetail V9 baseado no PBIX de referência."
    session.flush()
    return chart
