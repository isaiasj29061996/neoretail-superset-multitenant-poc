"""Panorama comparisons: existing certified contracts and chart composition."""
from __future__ import annotations

from neoretail_bootstrap.core.metrics import formatted_metric
from neoretail_bootstrap.core.chart_params import comparison_pivot_params
from neoretail_bootstrap.core.filters import _jinja_filter_predicates
from .filters import WEEKLY_FILTER_COLUMNS


COMPARISON_SCOPES = {
    "region": ("regiao", "uf", "cidade"),
    "retail": ("rede", "bandeira", "loja"),
    "hierarchy": ("hierarquia_1", "hierarquia_2", "item"),
}


_COMPARISON_SELLOUT = (
    "CASE WHEN SUM(faturamento_sum)>0 THEN SUM(faturamento_sum) ELSE NULL END"
)


_COMPARISON_SALES_QTY = (
    "CASE WHEN MAX(nm_measure)='valor' THEN SUM(faturamento_sum) "
    "WHEN MAX(conversion_factor) IS NULL THEN NULL "
    "ELSE SUM(volume_sum)*MAX(conversion_factor) END"
)


_COMPARISON_LOSS_QTY = (
    "CASE WHEN MAX(conversion_factor) IS NULL THEN NULL "
    "ELSE SUM(loss_sum)*MAX(conversion_factor) END"
)


_COMPARISON_PRICE = (
    "CASE WHEN MAX(conversion_factor) IS NULL OR SUM(price_count)=0 THEN NULL "
    "ELSE (SUM(price_sum)/SUM(price_count))*MAX(conversion_factor) END"
)


_COMPARISON_STOCK_QTY = (
    "CASE WHEN MAX(conversion_factor) IS NULL THEN NULL ELSE "
    "(ARRAY_AGG(stock_qty_base_sum ORDER BY data DESC))[1]*MAX(conversion_factor) END"
)


COMPARISON_METRICS = {
    "value": [
        formatted_metric("Sell out venda", _COMPARISON_SELLOUT, "$,.2f"),
        formatted_metric("Sell out custo", "SUM(sales_cost_sum)", "$,.2f"),
        formatted_metric(
            "Markup",
            f"CASE WHEN ({_COMPARISON_SELLOUT}) IS NULL OR SUM(sales_cost_sum)=0 "
            f"THEN 0 ELSE ({_COMPARISON_SELLOUT})/SUM(sales_cost_sum) END",
            ".2%",
        ),
    ],
    "quantity": [
        formatted_metric("Qtd venda", _COMPARISON_SALES_QTY, ",.2f"),
        formatted_metric("Qtd Perda OSA", _COMPARISON_LOSS_QTY, ",.2f"),
        formatted_metric("Preço Médio", _COMPARISON_PRICE, "$,.2f"),
    ],
    "stock": [
        formatted_metric("Estoque custo", "SUM(stock_cost_sum)", "$,.2f"),
        formatted_metric("Estoque qtd", _COMPARISON_STOCK_QTY, ",.2f"),
        formatted_metric(
            "ROI",
            f"CASE WHEN ({_COMPARISON_SELLOUT}) IS NULL OR SUM(sales_cost_sum)=0 "
            f"THEN 0 ELSE (({_COMPARISON_SELLOUT})-SUM(sales_cost_sum))"
            "/NULLIF(SUM(stock_cost_sum),0) END",
            ".2%",
        ),
        formatted_metric(
            "Giro", "SUM(giro_num)/NULLIF(SUM(giro_den),0)", ",.0f"
        ),
    ],
    "osa": [
        formatted_metric(
            "% OSA",
            "1-SUM(osa_problem_sum)/NULLIF(SUM(osa_active_sum),0)",
            ".2%",
        ),
        formatted_metric(
            "% RUP", "SUM(rupture_sum)/NULLIF(SUM(status_sum),0)", ".2%"
        ),
        formatted_metric(
            "% ISV", "SUM(isv_sum)/NULLIF(SUM(status_sum),0)", ".2%"
        ),
    ],
}


COMPARISON_GAP_METRICS = [
    formatted_metric(
        "R$ Pré-ruptura",
        "(ARRAY_AGG(tvd ORDER BY data DESC) FILTER (WHERE tvd IS NOT NULL))[1]",
        "$,.2f",
    ),
    formatted_metric(
        "R$ Excesso",
        "(ARRAY_AGG(ivd ORDER BY data DESC) FILTER (WHERE ivd IS NOT NULL))[1]",
        "$,.2f",
    ),
]


def _comparison_dimension_projection(scope_columns: tuple[str, ...]) -> str:
    return ",\n    ".join(
        column if column in scope_columns else f"NULL::text AS {column}"
        for column in WEEKLY_FILTER_COLUMNS
        if column not in ("tp_activity_level", "activity_level")
    )


def comparison_history_sql(scope: str) -> str:
    """PBIP comparison matrix over a physical history serving mart."""
    scope_columns = COMPARISON_SCOPES[scope]
    predicates = _jinja_filter_predicates("h")
    group_columns = ",".join(scope_columns)
    dimensions = _comparison_dimension_projection(scope_columns)
    return f"""
{{% set time_filter = get_time_filter('data', remove_filter=True) %}}
{{% set measure_filters = get_filters('nm_measure', remove_filter=True) %}}
WITH history_filtered AS (
  SELECT h.*
  FROM gold.nr_panorama_comparison_history_detail h
  WHERE 1=1
{predicates}
  {{% if time_filter.from_expr %}} AND h.data >= {{{{ time_filter.from_expr }}}} {{% endif %}}
  {{% if time_filter.to_expr %}} AND h.data < {{{{ time_filter.to_expr }}}} {{% endif %}}
  {{% if not time_filter.from_expr and not time_filter.to_expr %}}
    AND h.data >= DATE_TRUNC('year', CURRENT_DATE)
  {{% endif %}}
), expanded AS (
  SELECT h.*,o.nm_measure,c.conversion_rate
  FROM history_filtered h
  JOIN gold.nr_conversion_options o ON o.id_customer=h.id_customer
  LEFT JOIN gold.dim_conversao c
    ON c.id_customer=h.id_customer
   AND c.id_item::text=h.id_item::text
   AND c.nm_measure=o.nm_measure
  WHERE 1=1
  {{% if measure_filters|length == 0 %}} AND o.nm_measure='unidade' {{% endif %}}
  {{% for filter in measure_filters %}}
  {{% if filter.get('op') == 'IN' %}}
    AND o.nm_measure IN {{{{ filter.get('val') | where_in }}}}
  {{% elif filter.get('op') == 'NOT IN' %}}
    AND o.nm_measure NOT IN {{{{ filter.get('val') | where_in }}}}
  {{% endif %}}
  {{% endfor %}}
), monthly AS (
  SELECT
    data,id_customer,nm_measure,{group_columns},
    SUM(COALESCE(faturamento,0))::float8 AS faturamento_sum,
    SUM(COALESCE(volume_unidades,0))::float8 AS volume_sum,
    SUM(COALESCE(qtd_perda_osa,0))::float8 AS loss_sum,
    SUM(avg_sales_price) FILTER (WHERE faturamento>0)::float8 AS price_sum,
    COUNT(avg_sales_price) FILTER (WHERE faturamento>0)::bigint AS price_count,
    SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 AS sales_cost_sum,
    SUM(COALESCE(estoque_medio,0)*COALESCE(avg_price_cost,0))::float8 AS stock_cost_sum,
    SUM(COALESCE(estoque_unidades,0))::float8 AS stock_qty_base_sum,
    SUM(giro) FILTER (WHERE giro>0)::float8 AS giro_num,
    COUNT(giro) FILTER (WHERE giro>0)::bigint AS giro_den,
    SUM(COALESCE(qtd_problemas_osa,0))::float8 AS osa_problem_sum,
    SUM(COALESCE(qtd_item_ativo_osa,0))::float8 AS osa_active_sum,
    SUM(COALESCE(rup,0))::float8 AS rupture_sum,
    SUM(COALESCE(status_item_geral,0))::float8 AS status_sum,
    SUM(COALESCE(est_virtual,0))::float8 AS isv_sum,
    MAX(conversion_rate)::float8 AS conversion_factor
  FROM expanded
  GROUP BY data,id_customer,nm_measure,{group_columns}
)
SELECT
    data,id_customer,nm_measure,'{scope}'::text AS comparison_scope,
    NULL::text AS tp_activity_level,NULL::text AS activity_level,
    {dimensions},
    faturamento_sum,volume_sum,loss_sum,price_sum,price_count,
    sales_cost_sum,stock_cost_sum,stock_qty_base_sum,giro_num,giro_den,
    osa_problem_sum,osa_active_sum,rupture_sum,status_sum,isv_sum,
    conversion_factor
FROM monthly
""".strip()


def comparison_gap_sql(scope: str) -> str:
    """PBIP LASTNONBLANK matrix with a compact default and filtered fallback."""
    scope_columns = COMPARISON_SCOPES[scope]
    predicates = _jinja_filter_predicates("o")
    checks = " or ".join(
        f"get_filters('{column}')"
        for column in WEEKLY_FILTER_COLUMNS
        if column != "activity_level"
    )
    group_columns = ",".join(scope_columns)
    dimensions = _comparison_dimension_projection(scope_columns)
    return f"""
{{% set time_filter = get_time_filter('data', remove_filter=True) %}}
{{% set has_dimension_filter = {checks} %}}
{{% if has_dimension_filter %}}
WITH filtered AS (
  SELECT o.*
  FROM gold.nr_panorama_opportunities o
  WHERE 1=1
{predicates}
  {{% if time_filter.from_expr %}} AND o.data >= {{{{ time_filter.from_expr }}}} {{% endif %}}
  {{% if time_filter.to_expr %}} AND o.data < {{{{ time_filter.to_expr }}}} {{% endif %}}
  {{% if not time_filter.from_expr and not time_filter.to_expr %}}
    AND o.data >= DATE_TRUNC('year', CURRENT_DATE)
  {{% endif %}}
), daily AS (
  SELECT data,id_customer,{group_columns},
         SUM(tvd_simplificado)::float8 AS tvd,
         SUM(ivd_simplificado)::float8 AS ivd
  FROM filtered
  GROUP BY data,id_customer,{group_columns}
)
SELECT
    data,id_customer,'{scope}'::text AS comparison_scope,
    NULL::text AS tp_activity_level,NULL::text AS activity_level,
    {dimensions},tvd,ivd
FROM daily
{{% else %}}
SELECT
    o.data,o.id_customer,o.comparison_scope,
    NULL::text AS tp_activity_level,NULL::text AS activity_level,
    {dimensions},o.tvd,o.ivd
FROM gold.nr_panorama_comparison_gap_daily o
WHERE o.comparison_scope='{scope}'
{predicates}
  {{% if time_filter.from_expr %}} AND o.data >= {{{{ time_filter.from_expr }}}} {{% endif %}}
  {{% if time_filter.to_expr %}} AND o.data < {{{{ time_filter.to_expr }}}} {{% endif %}}
  {{% if not time_filter.from_expr and not time_filter.to_expr %}}
    AND o.data >= DATE_TRUNC('year', CURRENT_DATE)
  {{% endif %}}
{{% endif %}}
""".strip()


def register_comparison_charts(add, comparison_history, comparison_gap):
    comparison_dimensions = (
        ("region", "Região"),
        ("retail", "Varejo"),
        ("hierarchy", "Hierarquia de item"),
    )
    comparison_tabs = (
        ("Valor", "value", COMPARISON_METRICS["value"]),
        ("Quantidade", "quantity", COMPARISON_METRICS["quantity"]),
        ("R$ Estoque", "stock", COMPARISON_METRICS["stock"]),
        ("OSA", "osa", COMPARISON_METRICS["osa"]),
        ("Falta x Excesso", "gap", COMPARISON_GAP_METRICS),
    )
    for tab_label, tab_key, metrics in comparison_tabs:
        for scope, dimension_label in comparison_dimensions:
            dataset = (
                comparison_gap[scope]
                if tab_key == "gap"
                else comparison_history[scope]
            )
            title = (
                f"Comparativo — {dimension_label}"
                if tab_key == "value"
                else f"Comparativo {tab_label} — {dimension_label}"
            )
            legacy = (
                ()
                if tab_key == "value"
                else (f"Ranking {tab_label} — {dimension_label}",)
            )
            add(
                f"compare_{tab_key}_{scope}",
                dataset,
                title,
                comparison_pivot_params(
                    dataset, COMPARISON_SCOPES[scope], metrics
                ),
                "pivot_table_v2",
                legacy,
            )
    return comparison_dimensions, comparison_tabs
