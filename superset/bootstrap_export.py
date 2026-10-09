"""Create/update NeoRetail export dashboards for daily and monthly history."""
from __future__ import annotations

import json

from sqlalchemy import text
from neoretail_bootstrap.core.sql_sources import consumption_sql
from superset.app import create_app


from neoretail_bootstrap.core.layout import Layout
from neoretail_bootstrap.core.metadata import upsert_dataset, upsert_chart
from neoretail_bootstrap.core.metrics import metric
from neoretail_bootstrap.export.options import INDICATORS, indicator_sql


DATABASE_NAME = "NeoRetail Gold - PostgreSQL Local"

# O seletor de indicador segue as fórmulas já usadas nos dashboards NeoRetail
# (Panorama/Visão geral), evitando criar uma nova definição de negócio só para
# a exportação.
EXPORT_VALUE = metric(
    "Valor",
    "CASE MAX(indicador) "
    "WHEN 'Venda' THEN SUM(COALESCE(venda_qtd, 0)) "
    "WHEN 'Cobertura estoque' THEN SUM(COALESCE(estoque_qtd, 0)) / NULLIF(SUM(COALESCE(venda_qtd, 0)) / 4.33, 0) "
    "WHEN 'Estoque' THEN SUM(COALESCE(estoque_qtd, 0)) "
    "WHEN 'Estoque em Trânsito' THEN SUM(COALESCE(estoque_transito_qtd, 0)) "
    "WHEN 'ISV (%)' THEN 100.0 * SUM(COALESCE(item_sem_venda, 0)) / NULLIF(SUM(COALESCE(osa_itens_ativos, 0)), 0) "
    "WHEN 'OSA (%)' THEN 100.0 * (1 - SUM(COALESCE(osa_problemas, 0)) / NULLIF(SUM(COALESCE(osa_itens_ativos, 0)), 0)) "
    "WHEN 'Perda OSA vol.' THEN SUM(COALESCE(perda_osa_qtd, 0)) "
    "WHEN 'Perda OSA R$' THEN SUM(COALESCE(perda_osa_qtd, 0)) * AVG(NULLIF(preco_referencia, 0)) "
    "WHEN 'Preço médio (R$)' THEN SUM(COALESCE(venda_valor, 0)) / NULLIF(SUM(COALESCE(venda_qtd, 0)), 0) "
    "ELSE SUM(COALESCE(venda_qtd, 0)) END",
)

EXPORT_SUMMARY_VALUE = metric(
    "Valor",
    "CASE MAX(indicador) "
    "WHEN 'Venda' THEN SUM(COALESCE(venda_qtd, 0)) "
    "WHEN 'Cobertura estoque' THEN SUM(COALESCE(estoque_qtd, 0)) / NULLIF(SUM(COALESCE(venda_qtd, 0)) / 4.33, 0) "
    "WHEN 'Estoque' THEN SUM(COALESCE(estoque_qtd, 0)) "
    "WHEN 'Estoque em Trânsito' THEN SUM(COALESCE(estoque_transito_qtd, 0)) "
    "WHEN 'ISV (%)' THEN 100.0 * SUM(COALESCE(item_sem_venda, 0)) / NULLIF(SUM(COALESCE(osa_itens_ativos, 0)), 0) "
    "WHEN 'OSA (%)' THEN 100.0 * (1 - SUM(COALESCE(osa_problemas, 0)) / NULLIF(SUM(COALESCE(osa_itens_ativos, 0)), 0)) "
    "WHEN 'Perda OSA vol.' THEN SUM(COALESCE(perda_osa_qtd, 0)) "
    "WHEN 'Perda OSA R$' THEN SUM(COALESCE(perda_osa_qtd, 0)) * "
    "SUM(COALESCE(price_reference_sum, 0)) / NULLIF(SUM(COALESCE(price_reference_count, 0)), 0) "
    "WHEN 'Preço médio (R$)' THEN SUM(COALESCE(venda_valor, 0)) / NULLIF(SUM(COALESCE(venda_qtd, 0)), 0) "
    "ELSE SUM(COALESCE(venda_qtd, 0)) END",
)

EXPORT_DETAIL_FILTER_COLUMNS = (
    "bandeira", "regiao", "uf", "cidade", "tipo_local",
    "cnpj_formatado", "cod_loja", "loja", "nivel_atividade",
    "descricao_marca", "hierarquia_1", "hierarquia_2", "hierarquia_3",
    "item", "unidade_medida",
)


def semantic_sql(source_table: str) -> str:
    allowed = json.dumps(list(INDICATORS), ensure_ascii=False)
    return f"""
{{% set indicator_filters = get_filters('indicador', remove_filter=True) %}}
{{% set requested = indicator_filters[0].get('val', ['Venda']) if indicator_filters else ['Venda'] %}}
{{% set selected = requested[0] if requested and requested[0] in {allowed} else 'Venda' %}}
SELECT
    source.*,
    '{{{{ selected | replace("'", "''") }}}}'::text AS indicador
FROM gold.{source_table} source
""".strip()


def retail_semantic_sql(source_table: str, summary_table: str) -> str:
    """Use the compact retailer mart until a dimensional filter needs detail."""
    allowed = json.dumps(list(INDICATORS), ensure_ascii=False)
    filter_checks = "\n".join(
        f"{{% if get_filters('{column}') %}}{{% set state.filtered = true %}}{{% endif %}}"
        for column in EXPORT_DETAIL_FILTER_COLUMNS
    )
    day_expression = "source.dia" if "daily" in source_table else "NULL::integer AS dia"
    return f"""
{{% set indicator_filters = get_filters('indicador', remove_filter=True) %}}
{{% set requested = indicator_filters[0].get('val', ['Venda']) if indicator_filters else ['Venda'] %}}
{{% set selected = requested[0] if requested and requested[0] in {allowed} else 'Venda' %}}
{{% set state = namespace(filtered=false) %}}
{filter_checks}
{{% if state.filtered %}}
SELECT
    source.id_customer, source.data, source.ano, source.mes_num, source.mes,
    {day_expression},
    source.rede, source.bandeira, source.regiao, source.uf, source.cidade,
    source.tipo_local, source.cnpj_formatado, source.cod_loja, source.loja,
    source.nivel_atividade, source.descricao_marca, source.hierarquia_1,
    source.hierarquia_2, source.hierarquia_3, source.item, source.unidade_medida,
    source.venda_qtd, source.venda_valor, source.estoque_qtd,
    source.estoque_transito_qtd, source.perda_osa_qtd, source.osa_problemas,
    source.osa_itens_ativos, source.ruptura, source.item_sem_venda,
    CASE WHEN source.preco_referencia <> 0 THEN source.preco_referencia ELSE 0 END::double precision
        AS price_reference_sum,
    CASE WHEN source.preco_referencia <> 0 THEN 1 ELSE 0 END::bigint
        AS price_reference_count,
    '{{{{ selected | replace("'", "''") }}}}'::text AS indicador
FROM gold.{source_table} source
{{% else %}}
SELECT
    source.id_customer, source.data, source.ano, source.mes_num, source.mes,
    source.dia,
    source.rede, NULL::text AS bandeira, NULL::text AS regiao,
    NULL::text AS uf, NULL::text AS cidade, NULL::text AS tipo_local,
    NULL::text AS cnpj_formatado, NULL::text AS cod_loja, NULL::text AS loja,
    NULL::text AS nivel_atividade, NULL::text AS descricao_marca,
    NULL::text AS hierarquia_1, NULL::text AS hierarquia_2,
    NULL::text AS hierarquia_3, NULL::text AS item,
    NULL::text AS unidade_medida,
    source.venda_qtd, source.venda_valor, source.estoque_qtd,
    source.estoque_transito_qtd, source.perda_osa_qtd, source.osa_problemas,
    source.osa_itens_ativos, source.ruptura, source.item_sem_venda,
    source.price_reference_sum, source.price_reference_count,
    '{{{{ selected | replace("'", "''") }}}}'::text AS indicador
FROM gold.{summary_table} source
{{% endif %}}
""".strip()




def pivot_params(dataset, rows, *, daily: bool, value_metric=EXPORT_VALUE):
    return {
        "datasource": f"{dataset.id}__table",
        "viz_type": "pivot_table_v2",
        "groupbyRows": rows,
        "groupbyColumns": ["data"],
        "metrics": [value_metric],
        "adhoc_filters": [],
        "time_range": "No filter",
        "row_limit": 100000,
        "order_desc": False,
        "aggregateFunction": "Sum",
        "rowOrder": "key_a_to_z",
        "colOrder": "key_a_to_z",
        "transposePivot": False,
        "combineMetric": True,
        "showRowTotals": True,
        "showColTotals": False,
        "valueFormat": "SMART_NUMBER",
        "date_format": "%d/%m/%Y" if daily else "%m/%Y",
    }


def export_filters(
    dataset_id: int,
    indicator_dataset_id: int,
    filter_dataset_id: int,
    *,
    daily: bool,
    default_date=None,
):
    definitions = [
        ("rede", "Rede", []),
        ("bandeira", "Bandeira", ["rede"]),
        ("uf", "UF", []),
        ("cidade", "Cidade", ["uf"]),
        ("tipo_local", "Tipo local", []),
        ("loja", "Loja", ["tipo_local"]),
        ("nivel_atividade", "Nível de atividade", []),
        ("descricao_marca", "Descrição marca", []),
        ("hierarquia_1", "Hierarquia 1", ["descricao_marca"]),
        ("hierarquia_2", "Hierarquia 2", ["hierarquia_1"]),
        ("hierarquia_3", "Hierarquia 3", ["hierarquia_2"]),
        ("item", "Item", ["hierarquia_3"]),
        ("unidade_medida", "Unidade de medida", []),
        ("indicador", "Indicador", []),
        ("ano", "Ano", []),
        ("mes", "Mês", ["ano"]),
    ]
    if daily:
        definitions.append(("dia", "Dia", ["mes"]))

    ids = {
        column: f"NATIVE_FILTER-export-{'dia' if daily else 'mes'}-{column}"
        for column, _, _ in definitions
    }
    result = []
    for column, label, parents in definitions:
        is_single = column in {"indicador", "ano", "mes", "dia"}
        default_mask = {"extraFormData": {}, "filterState": {}, "ownState": {}}
        default_value = None
        if column == "indicador":
            default_value = "Venda"
        elif default_date is not None and column == "ano":
            default_value = int(default_date.year)
        elif default_date is not None and daily and column == "mes":
            month_names = {
                1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
                5: "maio", 6: "junho", 7: "julho", 8: "agosto",
                9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
            }
            default_value = month_names[int(default_date.month)]

        if default_value is not None:
            default_mask = {
                "extraFormData": {
                    "filters": [{"col": column, "op": "IN", "val": [default_value]}]
                },
                "filterState": {
                    "label": str(default_value),
                    "value": [default_value],
                },
                "ownState": {},
            }
        result.append({
            "id": ids[column],
            "controlValues": {
                "enableEmptyFilter": False,
                "defaultToFirstItem": False,
                "creatable": False,
                "multiSelect": not is_single,
                "searchAllOptions": True,
                "inverseSelection": False,
            },
            "name": label,
            "filterType": "filter_select",
            "targets": [{
                "datasetId": (
                    indicator_dataset_id if column == "indicador"
                    else dataset_id if column in {"ano", "mes", "dia"}
                    else filter_dataset_id
                ),
                "column": {"name": column},
            }],
            "defaultDataMask": default_mask,
            "cascadeParentIds": [ids[parent] for parent in parents],
            "scope": {"excluded": [], "rootPath": ["ROOT_ID"]},
            "type": "NATIVE_FILTER",
            "description": "",
        })
    return result


def add_markdown(layout: Layout, text: str, height: int = 5):
    node_id = layout._id("MARKDOWN")
    layout.nodes[node_id] = {
        "id": node_id,
        "type": "MARKDOWN",
        "parents": ["ROOT_ID", "GRID_ID"],
        "children": [],
        "meta": {"code": text, "height": height, "width": 12},
    }
    layout.nodes["GRID_ID"]["children"].append(node_id)


def build_export_dashboard(
    session,
    Dashboard,
    Slice,
    dataset,
    retail_dataset,
    indicator_dataset_id: int,
    filter_dataset_id: int,
    *,
    daily: bool,
    default_date=None,
):
    period_key = "dia" if daily else "mes"
    period_label = "dia" if daily else "mês"
    title = f"NeoRetail V9 — Exportação — Histórico {period_label}"
    slug = f"neoretail-v9-exportacao-historico-{period_key}"

    definitions = {
        "varejo": ("Varejo", ["rede"]),
        "produto": ("Produto", ["hierarquia_1"]),
        "geral": (
            "Geral",
            [
                "rede", "bandeira", "regiao", "uf", "cidade", "tipo_local",
                "cnpj_formatado", "cod_loja", "loja", "descricao_marca",
                "hierarquia_1", "hierarquia_2", "hierarquia_3", "item",
            ],
        ),
        "resumo": (
            "Resumo",
            ["rede", "cnpj_formatado", "item", "unidade_medida"],
        ),
    }

    charts = {}
    for key, (label, rows) in definitions.items():
        chart_dataset = retail_dataset if key == "varejo" else dataset
        charts[key] = upsert_chart(
            session,
            Slice,
            chart_dataset,
            f"[Exportação {period_label}] {label}",
            pivot_params(
                chart_dataset,
                rows,
                daily=daily,
                value_metric=EXPORT_SUMMARY_VALUE if key == "varejo" else EXPORT_VALUE,
            ),
            "pivot_table_v2",
        )

    layout = Layout()
    add_markdown(
        layout,
        "É possível exportar até **100.000 registros por vez**. Utilize filtros para reduzir o volume de dados, se necessário.\n\n"
        "Para exportar, posicione o cursor do mouse sobre a tabela e clique no botão **'...'** no canto superior direito; depois escolha **Download CSV**.",
        height=11,
    )
    layout.tabs(
        "GRID_ID",
        ["ROOT_ID", "GRID_ID"],
        "Exportação de dados",
        [
            ("Varejo", [[charts["varejo"]]]),
            ("Produto", [[charts["produto"]]]),
            ("Geral", [[charts["geral"]]]),
            ("Resumo", [[charts["resumo"]]]),
        ],
        height=74,
    )

    dashboard = session.query(Dashboard).filter(
        Dashboard.dashboard_title == title
    ).one_or_none()
    if dashboard is None:
        dashboard = Dashboard(dashboard_title=title, slug=slug, published=True)
        session.add(dashboard)
    dashboard.slug = slug
    dashboard.published = True
    dashboard.position_json = json.dumps(layout.nodes, ensure_ascii=False)
    dashboard.css = (
        ".dashboard-content { background: #e7f0f5 !important; } "
        ".dashboard-component-chart-holder { border-radius: 8px; background: #fff; } "
        ".dashboard-component-tabs { background: #fff; border-radius: 8px; } "
        ".dashboard-component-markdown { overflow: visible !important; }"
    )
    dashboard.json_metadata = json.dumps({
        "timed_refresh_immune_slices": [],
        "expanded_slices": {},
        "refresh_frequency": 0,
        "color_scheme": "supersetColors",
        "native_filter_configuration": export_filters(
            dataset.id,
            indicator_dataset_id,
            filter_dataset_id,
            daily=daily,
            default_date=default_date,
        ),
        "filter_bar_orientation": "HORIZONTAL",
    }, ensure_ascii=False)
    dashboard.slices = list(charts.values())
    session.flush()
    return dashboard, charts


def main():
    app = create_app()
    with app.app_context():
        from superset import db
        from superset.connectors.sqla.models import SqlaTable
        from superset.models.core import Database
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice

        database = db.session.query(Database).filter(
            Database.database_name == DATABASE_NAME
        ).one()
        daily = upsert_dataset(
            db.session,
            SqlaTable,
            database,
            "nr_export_daily_semantic",
            sql=semantic_sql("nr_export_daily"),
        )
        monthly = upsert_dataset(
            db.session,
            SqlaTable,
            database,
            "nr_export_monthly_semantic",
            sql=semantic_sql("nr_export_monthly"),
        )
        daily_retail = upsert_dataset(
            db.session,
            SqlaTable,
            database,
            "nr_export_daily_retail_interactive",
            sql=retail_semantic_sql(
                "nr_export_daily", "nr_export_daily_retail_summary"
            ),
        )
        monthly_retail = upsert_dataset(
            db.session,
            SqlaTable,
            database,
            "nr_export_monthly_retail_interactive",
            sql=retail_semantic_sql(
                "nr_export_monthly", "nr_export_monthly_retail_summary"
            ),
        )
        indicators = upsert_dataset(
            db.session,
            SqlaTable,
            database,
            "nr_export_indicators",
            sql=indicator_sql(),
        )
        filter_options = upsert_dataset(
            db.session,
            SqlaTable,
            database,
            "nr_filter_options",
            table_name="nr_filter_options",
        )

        with database.get_sqla_engine() as engine:
            with engine.connect() as connection:
                daily_max_date = connection.execute(
                    text(consumption_sql("SELECT MAX(data) FROM gold.nr_export_daily"))
                ).scalar_one()
                monthly_max_date = connection.execute(
                    text(consumption_sql("SELECT MAX(data) FROM gold.nr_export_monthly"))
                ).scalar_one()

        daily_dashboard, daily_charts = build_export_dashboard(
            db.session,
            Dashboard,
            Slice,
            daily,
            daily_retail,
            indicators.id,
            filter_options.id,
            daily=True,
            default_date=daily_max_date,
        )
        monthly_dashboard, monthly_charts = build_export_dashboard(
            db.session,
            Dashboard,
            Slice,
            monthly,
            monthly_retail,
            indicators.id,
            filter_options.id,
            daily=False,
            default_date=monthly_max_date,
        )
        db.session.commit()

        print(json.dumps({
            "daily": {
                "dashboard_id": daily_dashboard.id,
                "slug": daily_dashboard.slug,
                "dataset": daily.id,
                "retail_dataset": daily_retail.id,
                "charts": {key: chart.id for key, chart in daily_charts.items()},
            },
            "monthly": {
                "dashboard_id": monthly_dashboard.id,
                "slug": monthly_dashboard.slug,
                "dataset": monthly.id,
                "retail_dataset": monthly_retail.id,
                "charts": {key: chart.id for key, chart in monthly_charts.items()},
            },
            "indicators": list(INDICATORS),
            "indicator_dataset": indicators.id,
            "filter_dataset": filter_options.id,
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
