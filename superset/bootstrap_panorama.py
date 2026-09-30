"""Create the NeoRetail Panorama Industria dashboard in Superset metadata.

The script creates physical-dataset metadata, charts and dashboard layout. The
serving marts are materialized before this script runs.
"""
from __future__ import annotations

import json
import uuid

from sqlalchemy import text
from superset.app import create_app

from bootstrap_overview import (
    HISTORY_SQL, M, _jinja_filter_predicates, metric, overview_native_filters,
    upsert_dataset,
)
from bootstrap_overview_quantity import Q, quantity_semantic_sql


DASHBOARD_TITLE = "NeoRetail V9 — Panorama Indústria"

WEEKLY_SQL = """
SELECT
  f.id_time AS data,
  f.id_customer,
  f.id_item,
  f.id_location,
  f.volume_unidade AS volume_unidades,
  f.faturamento,
  f.estoque_unidades,
  f.estoque_medio,
  f.qtd_perda_osa,
  f.qtd_problemas_osa,
  f.qtd_item_ativo_osa,
  f.qtd_itens_validos,
  f.rup,
  f.est_virtual,
  f.giro,
  f.avg_sales_price,
  f.avg_price_cost,
  f.status_item_geral::text AS tp_activity_level,
  NULL::numeric AS demanda_media,
  COALESCE(f.status_item_geral::text, 'Outros') AS activity_level,
  l.rede, l.bandeira, l.uf, l.cidade, l.tipo_local, l.loja, l.regiao,
  i.item, i.descricao_marca, i.hierarquia_1, i.hierarquia_2, i.hierarquia_3
FROM gold.fato_semanal f
LEFT JOIN gold.dim_local l
  ON l.id_customer = f.id_customer AND l.id_location = f.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer = f.id_customer AND i.id_item = f.id_item
""".strip()

LATEST_SQL = f"""
SELECT h.*
FROM ({HISTORY_SQL}) h
WHERE h.data = (SELECT MAX(mes_ano) FROM gold.fato_historico)
""".strip()

OPPORTUNITIES_SQL = """
SELECT
  m.*,
  l.regiao,
  MAX(m.data) OVER (PARTITION BY m.id_customer, DATE_TRUNC('month', m.data)) AS month_end_data,
  MAX(m.data) OVER (PARTITION BY m.id_customer, DATE_TRUNC('week', m.data)) AS week_end_data,
  MAX(m.data) OVER (PARTITION BY m.id_customer) AS customer_latest_data
FROM gold.vw_mart_visao_industria m
LEFT JOIN gold.dim_local l
  ON l.id_customer = m.id_customer AND l.id_location = m.id_location
""".strip()

OPPORTUNITIES_LATEST_SQL = f"""
SELECT o.*
FROM ({OPPORTUNITIES_SQL}) o
WHERE o.data = o.customer_latest_data
""".strip()

P = {
    **M,
    "loss_qty": metric("Perda OSA qtd", "SUM(qtd_perda_osa)"),
    "price": metric("Preço médio", "SUM(faturamento) / NULLIF(SUM(volume_unidades), 0)"),
    "coverage": metric("Cobertura de estoque", "SUM(estoque_unidades) / NULLIF(SUM(volume_unidades) / 4.33, 0)"),
    "rup": metric("Ruptura", "100.0 * SUM(rup) / NULLIF(SUM(qtd_item_ativo_osa), 0)"),
    "isv": metric("Item sem venda", "100.0 * SUM(est_virtual) / NULLIF(SUM(qtd_item_ativo_osa), 0)"),
    "roi_annual": metric("ROI anual", "1200.0 * ((CASE WHEN SUM(faturamento) > 0 THEN SUM(faturamento) ELSE SUM(volume_unidades * avg_sales_price) END) - SUM(volume_unidades * avg_price_cost)) / NULLIF(SUM(estoque_medio * avg_price_cost), 0)"),
}

GAP_TVD = metric("TVD", "SUM(COALESCE(tvd, 0))")
GAP_IVD = metric("IVD", "SUM(COALESCE(ivd, 0))")

COMPARISON_SCOPES = {
    "region": ("regiao", "uf", "cidade"),
    "retail": ("rede", "bandeira", "loja"),
    "hierarchy": ("hierarquia_1", "hierarquia_2", "item"),
}

KPI_DIMENSION_SCOPES = {
    "region": ("regiao", "uf", "cidade"),
    "retail": ("rede", "bandeira", "loja"),
    "hierarchy": ("hierarquia_1", "descricao_marca", "item"),
}

KPI_INDUSTRY_OPTIONS = (
    ("Venda R$", "currency"),
    ("Estoque qtd", "quantity"),
    ("%OSA", "percent"),
    ("%Ruptura", "percent"),
    ("%Item sem Venda", "percent"),
    ("Cobertura de estoque", "number"),
    ("Giro de estoque", "number"),
    ("%ROI", "percent"),
    ("TVD - Pré-Ruptura", "currency"),
    ("IVD - Excesso de estoque", "currency"),
)

def formatted_metric(label: str, expression: str, d3_format: str) -> dict:
    result = metric(label, expression)
    result["d3Format"] = d3_format
    return result


KPI_DIMENSION_VALUE = formatted_metric("KPI valor", "MAX(kpi_value)", ",.2f")
KPI_ORDER_METRIC_NAME = "AP KPI ordem"
KPI_MONTH_ORDER_METRIC_NAME = "AP Mês ordem"


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

_WEEKLY_SELLOUT = (
    "CASE WHEN SUM(faturamento_sum) > 0 "
    "THEN SUM(faturamento_sum) ELSE SUM(fallback_sellout_sum) END"
)
WEEKLY_P = {
    "sellout": metric("Venda sell out", _WEEKLY_SELLOUT),
    "cost": metric("Venda custo", "SUM(sales_cost_sum)"),
    "markup": metric(
        "Markup", f"100.0 * ({_WEEKLY_SELLOUT}) / NULLIF(SUM(sales_cost_sum), 0)"
    ),
    "stock_cost": metric("Estoque custo", "SUM(stock_cost_sum)"),
    "stock_qty": metric("Estoque qtd", "SUM(stock_qty_sum)"),
    "roi": metric(
        "ROI",
        f"100.0 * (({_WEEKLY_SELLOUT}) - SUM(sales_cost_sum)) "
        "/ NULLIF(SUM(stock_cost_sum), 0)",
    ),
    "coverage": metric(
        "Cobertura de estoque",
        "SUM(stock_qty_sum) / NULLIF(SUM(sales_qty_sum) / 4.33, 0)",
    ),
    "giro": metric(
        "Giro", "SUM(giro_sum_positive) / NULLIF(SUM(giro_count_positive), 0)"
    ),
    "osa": metric(
        "OSA",
        "100.0 * (1 - SUM(osa_problem_sum) / NULLIF(SUM(osa_active_sum), 0))",
    ),
    "rup": metric(
        "Ruptura", "100.0 * SUM(rupture_sum) / NULLIF(SUM(osa_active_sum), 0)"
    ),
    "isv": metric(
        "Item sem venda", "100.0 * SUM(isv_sum) / NULLIF(SUM(osa_active_sum), 0)"
    ),
}

WEEKLY_FILTER_COLUMNS = (
    "rede", "bandeira", "uf", "cidade", "tipo_local", "loja", "regiao",
    "tp_activity_level", "activity_level", "item", "descricao_marca",
    "hierarquia_1", "hierarquia_2", "hierarquia_3",
)


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


def _kpi_dimension_projection(scope_columns: tuple[str, ...]) -> str:
    return ",\n  ".join(
        column if column in scope_columns else f"NULL::text AS {column}"
        for column in WEEKLY_FILTER_COLUMNS
    )


def _kpi_default_projection(scope_columns: tuple[str, ...]) -> str:
    positions = {column: index + 1 for index, column in enumerate(scope_columns)}
    return ",\n  ".join(
        f"d.dimension_{positions[column]} AS {column}"
        if column in positions else f"NULL::text AS {column}"
        for column in WEEKLY_FILTER_COLUMNS
    )


def kpi_dimension_sql(scope: str) -> str:
    """AP_KPI_INDUSTRIA contract over history and opportunity marts."""
    first, second, third = KPI_DIMENSION_SCOPES[scope]
    # The PBI 'Região' bar opens at UF, then drills into Cidade. Keep the
    # existing region/UF/city mart intact: only shift the chart presentation.
    display_d_level = "d.drill_level-1" if scope == "region" else "d.drill_level"
    display_l_level = "l.drill_level-1" if scope == "region" else "l.drill_level"
    display_a_level = "a.drill_level-1" if scope == "region" else "a.drill_level"
    display_d_where = "AND d.drill_level>=1" if scope == "region" else ""
    display_l_where = "WHERE l.drill_level>=1" if scope == "region" else ""
    display_a_where = "WHERE a.drill_level>=1" if scope == "region" else ""
    history_predicates = _jinja_filter_predicates("h")
    opportunity_predicates = _jinja_filter_predicates("o")
    projection = _kpi_dimension_projection(KPI_DIMENSION_SCOPES[scope])
    default_projection = _kpi_default_projection(KPI_DIMENSION_SCOPES[scope])
    filter_checks = " or ".join(
        f"get_filters('{column}')" for column in WEEKLY_FILTER_COLUMNS
    )
    # 'Ano' and 'Mês' are separate cascading filters. Month labels include
    # the year, so selecting January 2025 and March 2026 is unambiguous.
    month_labels = "ARRAY['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro']"
    history_month_expr = f"TO_CHAR(h.data,'YYYY-MM') || ' · ' || ({month_labels})[EXTRACT(MONTH FROM h.data)::int]"
    opportunity_month_expr = f"TO_CHAR(o.data,'YYYY-MM') || ' · ' || ({month_labels})[EXTRACT(MONTH FROM o.data)::int]"
    allowed = [label for label, _ in KPI_INDUSTRY_OPTIONS]
    allowed_json = json.dumps(allowed, ensure_ascii=False)
    return f"""
{{% set kpi_filters = get_filters('comparison_kpi', remove_filter=True) %}}
{{% set year_filters = get_filters('comparison_year', remove_filter=True) %}}
{{% set month_filters = get_filters('comparison_year_month', remove_filter=True) %}}
{{% set measure_filters = get_filters('nm_measure', remove_filter=True) %}}
{{% set selected_kpi = kpi_filters[0].get('val')[0] if kpi_filters|length and kpi_filters[0].get('val')|length else 'Venda R$' %}}
{{% set allowed_kpis = {allowed_json} %}}
{{% if selected_kpi not in allowed_kpis %}}{{% set selected_kpi = 'Venda R$' %}}{{% endif %}}
{{% set selected_measure = measure_filters[0].get('val')[0] if measure_filters|length and measure_filters[0].get('val')|length else 'unidade' %}}
{{% set has_dimension_filter = {filter_checks} %}}
{{% set has_month_filter = month_filters|length > 0 %}}
{{% if selected_kpi in ['TVD - Pré-Ruptura','IVD - Excesso de estoque'] %}}
{{% if not has_dimension_filter and not has_month_filter %}}
SELECT
  d.data,d.comparison_year,d.id_customer,NULL::text AS comparison_year_month,'unidade'::text AS nm_measure,
  {default_projection},{display_d_level} AS drill_level,
  '{{{{ selected_kpi | replace("'", "''") }}}}'::text AS comparison_kpi,
  'currency'::text AS kpi_format,
  CASE WHEN '{{{{ selected_kpi | replace("'", "''") }}}}'='TVD - Pré-Ruptura' THEN d.tvd ELSE d.ivd END::float8 AS kpi_value
FROM gold.nr_panorama_kpi_dimension_gap_default d
WHERE d.comparison_scope='{scope}'
  {display_d_where}
  {{% for filter in year_filters %}}
  {{% if filter.get('op') == 'IN' %}} AND d.comparison_year IN {{{{ filter.get('val') | where_in }}}} {{% endif %}}
  {{% endfor %}}
{{% else %}}
WITH filtered AS (
  SELECT o.*
  FROM gold.nr_panorama_opportunities o
  WHERE 1=1
{opportunity_predicates}
  {{% for filter in year_filters %}}
  {{% if filter.get('op') == 'IN' %}} AND EXTRACT(YEAR FROM o.data)::int IN {{{{ filter.get('val') | where_in }}}} {{% endif %}}
  {{% endfor %}}
  {{% for filter in month_filters %}}
  {{% if filter.get('op') == 'IN' %}} AND {opportunity_month_expr} IN {{{{ filter.get('val') | where_in }}}} {{% endif %}}
  {{% if filter.get('op') == 'NOT IN' %}} AND {opportunity_month_expr} NOT IN {{{{ filter.get('val') | where_in }}}} {{% endif %}}
  {{% endfor %}}
), daily_nodes AS (
  SELECT
    o.data,EXTRACT(YEAR FROM o.data)::int AS comparison_year,o.id_customer,
    o.{first},o.{second},o.{third},
    CASE WHEN GROUPING(o.{second})=1 THEN 0 WHEN GROUPING(o.{third})=1 THEN 1 ELSE 2 END::int AS drill_level,
    SUM(o.tvd_simplificado)::float8 AS tvd,
    SUM(o.ivd_simplificado)::float8 AS ivd
  FROM filtered o
  GROUP BY o.data,EXTRACT(YEAR FROM o.data),o.id_customer,GROUPING SETS (
    (o.{first}),(o.{first},o.{second}),(o.{first},o.{second},o.{third})
  )
), latest AS (
  SELECT DISTINCT ON (comparison_year,id_customer,drill_level,{first},{second},{third}) *
  FROM daily_nodes
  ORDER BY comparison_year,id_customer,drill_level,{first},{second},{third},data DESC
)
SELECT
  l.data,l.comparison_year,l.id_customer,NULL::text AS comparison_year_month,'unidade'::text AS nm_measure,
  {projection},{display_l_level} AS drill_level,
  '{{{{ selected_kpi | replace("'", "''") }}}}'::text AS comparison_kpi,
  'currency'::text AS kpi_format,
  CASE WHEN '{{{{ selected_kpi | replace("'", "''") }}}}'='TVD - Pré-Ruptura' THEN l.tvd ELSE l.ivd END::float8 AS kpi_value
FROM latest l
{display_l_where}
{{% endif %}}
{{% else %}}
{{% if not has_dimension_filter and not has_month_filter and (selected_kpi != 'Estoque qtd' or selected_measure == 'unidade') %}}
SELECT
  d.data,d.comparison_year,d.id_customer,NULL::text AS comparison_year_month,
  '{{{{ selected_measure | replace("'", "''") }}}}'::text AS nm_measure,
  {default_projection},{display_d_level} AS drill_level,
  '{{{{ selected_kpi | replace("'", "''") }}}}'::text AS comparison_kpi,
  CASE
    WHEN '{{{{ selected_kpi | replace("'", "''") }}}}'='Venda R$' THEN 'currency'
    WHEN '{{{{ selected_kpi | replace("'", "''") }}}}'='Estoque qtd' THEN 'quantity'
    WHEN '{{{{ selected_kpi | replace("'", "''") }}}}' IN ('%OSA','%Ruptura','%Item sem Venda','%ROI') THEN 'percent'
    ELSE 'number'
  END::text AS kpi_format,
  CASE '{{{{ selected_kpi | replace("'", "''") }}}}'
    WHEN 'Venda R$' THEN d.sales_value
    WHEN 'Estoque qtd' THEN d.stock_quantity
    WHEN '%OSA' THEN d.osa_percent
    WHEN '%Ruptura' THEN d.rupture_percent
    WHEN '%Item sem Venda' THEN d.no_sales_percent
    WHEN 'Cobertura de estoque' THEN d.coverage
    WHEN 'Giro de estoque' THEN d.inventory_turnover
    WHEN '%ROI' THEN d.roi_percent
  END::float8 AS kpi_value
FROM gold.nr_panorama_kpi_dimension_history_default d
WHERE d.comparison_scope='{scope}'
  {display_d_where}
  {{% for filter in year_filters %}}
  {{% if filter.get('op') == 'IN' %}} AND d.comparison_year IN {{{{ filter.get('val') | where_in }}}} {{% endif %}}
  {{% endfor %}}
{{% else %}}
WITH filtered AS (
  SELECT h.*,c.conversion_rate
  FROM gold.nr_panorama_comparison_history_detail h
  LEFT JOIN gold.dim_conversao c
    ON c.id_customer=h.id_customer AND c.id_item::text=h.id_item::text
   AND c.nm_measure='{{{{ selected_measure | replace("'", "''") }}}}'
  WHERE 1=1
{history_predicates}
  {{% for filter in year_filters %}}
  {{% if filter.get('op') == 'IN' %}} AND EXTRACT(YEAR FROM h.data)::int IN {{{{ filter.get('val') | where_in }}}} {{% endif %}}
  {{% endfor %}}
  {{% for filter in month_filters %}}
  {{% if filter.get('op') == 'IN' %}} AND {history_month_expr} IN {{{{ filter.get('val') | where_in }}}} {{% endif %}}
  {{% if filter.get('op') == 'NOT IN' %}} AND {history_month_expr} NOT IN {{{{ filter.get('val') | where_in }}}} {{% endif %}}
  {{% endfor %}}
), monthly_nodes AS (
  SELECT
    h.data,EXTRACT(YEAR FROM h.data)::int AS comparison_year,h.id_customer,
    h.{first},h.{second},h.{third},
    CASE WHEN GROUPING(h.{second})=1 THEN 0 WHEN GROUPING(h.{third})=1 THEN 1 ELSE 2 END::int AS drill_level,
    SUM(COALESCE(h.faturamento,0))::float8 AS sellout_sum,
    SUM(COALESCE(h.volume_unidades,0))::float8 AS volume_sum,
    SUM(h.avg_sales_price)::float8 AS price_sum,
    COUNT(h.avg_sales_price)::bigint AS price_count,
    SUM(COALESCE(h.volume_unidades,0)*COALESCE(h.avg_price_cost,0))::float8 AS sales_cost_sum,
    SUM(COALESCE(h.estoque_medio,0)*COALESCE(h.avg_price_cost,0))::float8 AS stock_cost_sum,
    SUM(COALESCE(h.estoque_unidades,0))::float8 AS stock_qty_sum,
    SUM(COALESCE(h.demanda_media,0))::float8 AS demand_sum,
    SUM(h.giro) FILTER (WHERE h.giro>0)::float8 AS giro_sum,
    COUNT(h.giro) FILTER (WHERE h.giro>0)::bigint AS giro_count,
    SUM(COALESCE(h.qtd_problemas_osa,0))::float8 AS osa_problem_sum,
    SUM(COALESCE(h.qtd_item_ativo_osa,0))::float8 AS osa_active_sum,
    SUM(COALESCE(h.rup,0))::float8 AS rupture_sum,
    SUM(COALESCE(h.status_item_geral,0))::float8 AS status_sum,
    SUM(COALESCE(h.est_virtual,0))::float8 AS isv_sum,
    MAX(h.conversion_rate)::float8 AS conversion_factor
  FROM filtered h
  GROUP BY h.data,EXTRACT(YEAR FROM h.data),h.id_customer,GROUPING SETS (
    (h.{first}),(h.{first},h.{second}),(h.{first},h.{second},h.{third})
  )
), annual_nodes AS (
  SELECT
    MAKE_DATE(comparison_year,1,1) AS data,comparison_year,id_customer,
    {first},{second},{third},drill_level,
    SUM(sellout_sum)::float8 AS sellout_sum,
    SUM(volume_sum)::float8 AS volume_sum,
    SUM(price_sum)::float8 AS price_sum,
    SUM(price_count)::bigint AS price_count,
    SUM(sales_cost_sum)::float8 AS sales_cost_sum,
    SUM(stock_cost_sum)::float8 AS stock_cost_sum,
    SUM(stock_qty_sum)::float8 AS stock_qty_period_sum,
    SUM(demand_sum)::float8 AS demand_sum,
    SUM(giro_sum)::float8 AS giro_sum,
    SUM(giro_count)::bigint AS giro_count,
    SUM(osa_problem_sum)::float8 AS osa_problem_sum,
    SUM(osa_active_sum)::float8 AS osa_active_sum,
    SUM(rupture_sum)::float8 AS rupture_sum,
    SUM(status_sum)::float8 AS status_sum,
    SUM(isv_sum)::float8 AS isv_sum,
    (ARRAY_AGG(stock_qty_sum ORDER BY data DESC))[1]::float8 AS latest_stock_qty,
    (ARRAY_AGG(conversion_factor ORDER BY data DESC))[1]::float8 AS latest_conversion_factor,
    MAX(conversion_factor)::float8 AS conversion_factor
  FROM monthly_nodes
  GROUP BY comparison_year,id_customer,{first},{second},{third},drill_level
)
SELECT
  a.data,a.comparison_year,a.id_customer,NULL::text AS comparison_year_month,
  '{{{{ selected_measure | replace("'", "''") }}}}'::text AS nm_measure,
  {projection},{display_a_level} AS drill_level,
  '{{{{ selected_kpi | replace("'", "''") }}}}'::text AS comparison_kpi,
  CASE
    WHEN '{{{{ selected_kpi | replace("'", "''") }}}}'='Venda R$' THEN 'currency'
    WHEN '{{{{ selected_kpi | replace("'", "''") }}}}'='Estoque qtd' THEN 'quantity'
    WHEN '{{{{ selected_kpi | replace("'", "''") }}}}' IN ('%OSA','%Ruptura','%Item sem Venda','%ROI') THEN 'percent'
    ELSE 'number'
  END::text AS kpi_format,
  CASE '{{{{ selected_kpi | replace("'", "''") }}}}'
    WHEN 'Venda R$' THEN CASE WHEN a.sellout_sum>0 THEN a.sellout_sum WHEN a.latest_conversion_factor IS NOT NULL AND a.price_count>0 THEN (a.volume_sum*a.latest_conversion_factor)*(a.price_sum/a.price_count*a.latest_conversion_factor) END
    WHEN 'Estoque qtd' THEN a.latest_stock_qty*a.latest_conversion_factor
    WHEN '%OSA' THEN 100.0*(1-a.osa_problem_sum/NULLIF(a.osa_active_sum,0))
    WHEN '%Ruptura' THEN 100.0*a.rupture_sum/NULLIF(a.status_sum,0)
    WHEN '%Item sem Venda' THEN 100.0*a.isv_sum/NULLIF(a.status_sum,0)
    WHEN 'Cobertura de estoque' THEN a.stock_qty_period_sum/NULLIF(a.demand_sum,0)
    WHEN 'Giro de estoque' THEN a.giro_sum/NULLIF(a.giro_count,0)
    WHEN '%ROI' THEN CASE WHEN a.sellout_sum=0 OR a.sales_cost_sum=0 THEN 0 ELSE 100.0*(a.sellout_sum-a.sales_cost_sum)/NULLIF(a.stock_cost_sum,0) END
  END::float8 AS kpi_value
FROM annual_nodes a
{display_a_where}
{{% endif %}}
{{% endif %}}
""".strip()


def kpi_filter_options_sql() -> str:
    rows = ",\n      ".join(
        f"({index},'{label.replace(chr(39), chr(39) * 2)}','{fmt}')"
        for index, (label, fmt) in enumerate(KPI_INDUSTRY_OPTIONS, 1)
    )
    return f"""
WITH year_months AS (
  SELECT DISTINCT id_customer,
    EXTRACT(YEAR FROM data)::int AS comparison_year,
    EXTRACT(MONTH FROM data)::int AS comparison_month
  FROM gold.nr_panorama_inventory_monthly_default
), kpis(kpi_order,comparison_kpi,kpi_format) AS (
  VALUES {rows}
)
SELECT ym.id_customer, ym.comparison_year, ym.comparison_month,
  (ym.comparison_year::text || '-' || LPAD(ym.comparison_month::text,2,'0')
   || ' · ' || (ARRAY['janeiro','fevereiro','março','abril','maio','junho',
     'julho','agosto','setembro','outubro','novembro','dezembro'])[ym.comparison_month]
  )::text AS comparison_year_month,
  (ym.comparison_year * 100 + ym.comparison_month)::int AS comparison_year_month_sort,
  kpis.kpi_order,kpis.comparison_kpi,kpis.kpi_format
FROM year_months ym CROSS JOIN kpis
""".strip()


def kpi_dimension_params(dataset, title: str, columns: tuple[str, ...]) -> dict:
    return custom_params(
        dataset,title,[KPI_DIMENSION_VALUE],formats="number",
        groupby=[*columns,"drill_level","comparison_kpi","kpi_format"],
        variant="hierarchyrank",row_limit=10000,
        hierarchy_columns="|".join(columns),labels="KPI valor",
    )


def kpi_filter_bar_params(dataset) -> dict:
    """First-class chart row for Power BI-style local filters.

    Its own options query is not limited by the KPI native filter selections,
    so clearing or changing the year does not make options disappear.
    """
    params = custom_params(
        dataset, "Comparativo de KPIs por dimensão",
        [metric("AP KPI ordem", "MIN(kpi_order)")],
        groupby=[
            "comparison_year", "comparison_month",
            "comparison_year_month", "comparison_kpi",
        ],
        variant="kpifilters",
        row_limit=2000,
    )
    # Unlike all analytical charts, selector options are not temporal.
    params["x_axis"] = None
    params.pop("time_grain_sqla", None)
    return params


def kpi_native_filters(filter_dataset_id: int) -> list[dict]:
    common = {"enableEmptyFilter": False, "defaultToFirstItem": False, "creatable": False, "multiSelect": False, "searchAllOptions": True, "inverseSelection": False}
    return [
        {"id": "NATIVE_FILTER-panorama-kpi-year", "controlValues": common, "name": "Ano", "filterType": "filter_select", "targets": [{"datasetId": filter_dataset_id, "column": {"name": "comparison_year"}}], "defaultDataMask": {"extraFormData": {"filters": [{"col": "comparison_year", "op": "IN", "val": [2026]}]}, "filterState": {"label": "2026", "value": [2026]}, "ownState": {}}, "cascadeParentIds": [], "scope": {"excluded": [], "rootPath": ["ROOT_ID"]}, "type": "NATIVE_FILTER", "description": ""},
        {"id": "NATIVE_FILTER-panorama-kpi-month", "controlValues": {**common, "multiSelect": True, "sortAscending": True, "sortMetric": KPI_MONTH_ORDER_METRIC_NAME}, "sortMetric": KPI_MONTH_ORDER_METRIC_NAME, "name": "Mês", "filterType": "filter_select", "targets": [{"datasetId": filter_dataset_id, "column": {"name": "comparison_year_month"}}], "defaultDataMask": {"extraFormData": {}, "filterState": {}, "ownState": {}}, "cascadeParentIds": ["NATIVE_FILTER-panorama-kpi-year"], "scope": {"excluded": [], "rootPath": ["ROOT_ID"]}, "type": "NATIVE_FILTER", "description": "Selecione meses específicos dentro do ano. Sem seleção, considera todos os meses."},
        {"id": "NATIVE_FILTER-panorama-kpi-selector", "controlValues": {**common, "sortAscending": True, "sortMetric": KPI_ORDER_METRIC_NAME}, "sortMetric": KPI_ORDER_METRIC_NAME, "name": "Visualização por", "filterType": "filter_select", "targets": [{"datasetId": filter_dataset_id, "column": {"name": "comparison_kpi"}}], "defaultDataMask": {"extraFormData": {"filters": [{"col": "comparison_kpi", "op": "IN", "val": ["Venda R$"]}]}, "filterState": {"label": "Venda R$", "value": ["Venda R$"]}, "ownState": {}}, "cascadeParentIds": [], "scope": {"excluded": [], "rootPath": ["ROOT_ID"]}, "type": "NATIVE_FILTER", "description": ""},
    ]


def weekly_semantic_sql() -> str:
    checks = " or ".join(
        f"get_filters('{column}')" for column in WEEKLY_FILTER_COLUMNS
    )
    detail = """
SELECT
    id_customer, data, tp_activity_level, activity_level,
    rede, bandeira, uf, cidade, tipo_local, loja, regiao,
    item, descricao_marca, hierarquia_1, hierarquia_2, hierarquia_3,
    COALESCE(faturamento, 0)::double precision AS faturamento_sum,
    (COALESCE(volume_unidades, 0) * COALESCE(avg_sales_price, 0))::double precision AS fallback_sellout_sum,
    (COALESCE(volume_unidades, 0) * COALESCE(avg_price_cost, 0))::double precision AS sales_cost_sum,
    COALESCE(volume_unidades, 0)::double precision AS sales_qty_sum,
    (COALESCE(estoque_medio, 0) * COALESCE(avg_price_cost, 0))::double precision AS stock_cost_sum,
    COALESCE(estoque_unidades, 0)::double precision AS stock_qty_sum,
    CASE WHEN COALESCE(giro, 0) > 0 THEN giro ELSE 0 END::double precision AS giro_sum_positive,
    CASE WHEN COALESCE(giro, 0) > 0 THEN 1 ELSE 0 END::bigint AS giro_count_positive,
    COALESCE(qtd_problemas_osa, 0)::double precision AS osa_problem_sum,
    COALESCE(qtd_item_ativo_osa, 0)::double precision AS osa_active_sum,
    COALESCE(rup, 0)::double precision AS rupture_sum,
    COALESCE(est_virtual, 0)::double precision AS isv_sum
FROM gold.nr_panorama_weekly
""".strip()
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n"
        f"{detail}\n"
        "{% else %}\n"
        "SELECT * FROM gold.nr_panorama_weekly_summary\n"
        "{% endif %}"
    )


def weekly_sales_semantic_sql() -> str:
    """Real weekly fact, with dimensional filters applied before TOP 13."""
    checks = " or ".join(f"get_filters('{c}')" for c in WEEKLY_FILTER_COLUMNS)
    predicates = _jinja_filter_predicates("w", "status_item_geral", {
        "rede": "l.rede", "bandeira": "l.bandeira", "uf": "l.uf",
        "cidade": "l.cidade", "tipo_local": "l.tipo_local",
        "loja": "l.loja", "regiao": "l.regiao", "item": "i.item",
        "descricao_marca": "i.descricao_marca", "hierarquia_1": "i.hierarquia_1",
        "hierarquia_2": "i.hierarquia_2", "hierarquia_3": "i.hierarquia_3",
    })
    detail = f"""
WITH filtered AS (
  SELECT
    w.id_time AS data,w.cd_week,w.id_customer,w.id_item,w.id_location,
    w.volume_unidade AS volume_unidades,w.faturamento,w.qtd_perda_osa,
    w.avg_sales_price,w.avg_price_cost,w.status_item_geral::text AS tp_activity_level,
    COALESCE(w.status_item_geral::text,'Outros') AS activity_level,
    l.rede,l.bandeira,l.uf,l.cidade,l.tipo_local,l.loja,l.regiao,
    i.item,i.descricao_marca,i.hierarquia_1,i.hierarquia_2,i.hierarquia_3
  FROM gold.fato_semanal w
  LEFT JOIN gold.dim_local l ON l.id_customer=w.id_customer AND l.id_location=w.id_location
  LEFT JOIN gold.dim_itens i ON i.id_customer=w.id_customer AND i.id_item=w.id_item
  WHERE 1=1
{predicates}
), ranked_weeks AS (
  SELECT id_customer,data,cd_week,DENSE_RANK() OVER (
    PARTITION BY id_customer ORDER BY cd_week DESC
  ) week_rank
  FROM (SELECT DISTINCT id_customer,data,cd_week FROM filtered) x
), scoped AS (
  SELECT f.* FROM filtered f JOIN ranked_weeks r USING(id_customer,data,cd_week)
  WHERE r.week_rank<=13
), weekly AS (
  SELECT data,id_customer,MAX(cd_week) cd_week,
    SUM(COALESCE(faturamento,0))::float8 faturamento_sum,
    SUM(COALESCE(volume_unidades,0))::float8 volume_sum,
    SUM(COALESCE(avg_sales_price,0))::float8 fallback_price_sum,
    COUNT(avg_sales_price)::bigint fallback_price_count,
    SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 cost_sum,
    SUM(COALESCE(qtd_perda_osa,0))::float8 loss_sum,
    SUM(COALESCE(avg_sales_price,0)) FILTER (WHERE faturamento>0)::float8 price_sum,
    COUNT(avg_sales_price) FILTER (WHERE faturamento>0)::bigint price_count
  FROM scoped GROUP BY data,id_customer
), factors AS (
  SELECT s.data,s.id_customer,c.nm_measure,MAX(c.conversion_rate)::float8 conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM scoped) s
  JOIN gold.dim_conversao c ON c.id_customer=s.id_customer AND c.id_item::text=s.id_item
  GROUP BY s.data,s.id_customer,c.nm_measure
)
SELECT w.data,w.cd_week,w.id_customer,f.nm_measure,
  CASE WHEN w.faturamento_sum>0 THEN w.faturamento_sum
       WHEN f.conversion_factor IS NOT NULL AND w.fallback_price_count>0
       THEN (w.volume_sum*f.conversion_factor)
          *((w.fallback_price_sum/w.fallback_price_count)*f.conversion_factor)
       ELSE NULL END::float8 sellout_sum,
  w.cost_sum,(w.volume_sum*f.conversion_factor)::float8 sales_sum,
  (w.loss_sum*f.conversion_factor)::float8 loss_sum,
  (w.price_sum*f.conversion_factor)::float8 price_numerator,w.price_count,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,NULL::text tp_activity_level,
  NULL::text activity_level,NULL::text item,NULL::text descricao_marca,
  NULL::text hierarquia_1,NULL::text hierarquia_2,NULL::text hierarquia_3
FROM weekly w JOIN factors f USING(data,id_customer)
""".strip()
    default = """
WITH ranked AS (
  SELECT d.*,DENSE_RANK() OVER (
    PARTITION BY id_customer,nm_measure ORDER BY cd_week DESC
  ) week_rank
  FROM gold.nr_panorama_sales_weekly_default d
)
SELECT * FROM ranked WHERE week_rank<=13
""".strip()
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n" + detail + "\n"
        "{% else %}\n" + default + "\n{% endif %}"
    )


def monthly_sales_semantic_sql() -> str:
    """Monthly Sell Out with filters applied before the literal DAX fallback."""
    checks = " or ".join(f"get_filters('{c}')" for c in WEEKLY_FILTER_COLUMNS)
    predicates = _jinja_filter_predicates("h")
    detail = f"""
WITH filtered AS (
  SELECT h.* FROM gold.nr_overview_history h WHERE 1=1
{predicates}
), monthly AS (
  SELECT data,id_customer,
    SUM(COALESCE(faturamento,0))::float8 faturamento_sum,
    SUM(COALESCE(volume_unidades,0))::float8 volume_sum,
    SUM(COALESCE(avg_sales_price,0))::float8 fallback_price_sum,
    COUNT(avg_sales_price)::bigint fallback_price_count,
    SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 cost_sum
  FROM filtered GROUP BY data,id_customer
), factors AS (
  SELECT f.data,f.id_customer,c.nm_measure,MAX(c.conversion_rate)::float8 conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM filtered) f
  JOIN gold.dim_conversao c ON c.id_customer=f.id_customer AND c.id_item::text=f.id_item
  GROUP BY f.data,f.id_customer,c.nm_measure
)
SELECT m.data,m.id_customer,f.nm_measure,
  CASE WHEN m.faturamento_sum>0 THEN m.faturamento_sum
       WHEN f.conversion_factor IS NOT NULL AND m.fallback_price_count>0
       THEN (m.volume_sum*f.conversion_factor)
          *((m.fallback_price_sum/m.fallback_price_count)*f.conversion_factor)
       ELSE NULL END::float8 sellout_sum,
  m.cost_sum,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,NULL::text tp_activity_level,
  NULL::text activity_level,NULL::text item,NULL::text descricao_marca,
  NULL::text hierarquia_1,NULL::text hierarquia_2,NULL::text hierarquia_3
FROM monthly m JOIN factors f USING(data,id_customer)
""".strip()
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n" + detail + "\n"
        "{% else %}\nSELECT * FROM gold.nr_panorama_sales_monthly_default\n{% endif %}"
    )


def weekly_sales_card_semantic_sql() -> str:
    """Single-card dataset: weekly TOP 13 timeline plus monthly summary rows."""
    checks = " or ".join(f"get_filters('{column}')" for column in WEEKLY_FILTER_COLUMNS)
    weekly_predicates = _jinja_filter_predicates("w", "status_item_geral", {
        "rede": "l.rede", "bandeira": "l.bandeira", "uf": "l.uf",
        "cidade": "l.cidade", "tipo_local": "l.tipo_local",
        "loja": "l.loja", "regiao": "l.regiao", "item": "i.item",
        "descricao_marca": "i.descricao_marca", "hierarquia_1": "i.hierarquia_1",
        "hierarquia_2": "i.hierarquia_2", "hierarquia_3": "i.hierarquia_3",
    })
    monthly_predicates = _jinja_filter_predicates("h")
    detail = f"""
WITH weekly_filtered AS (
  SELECT
    w.id_time AS data,w.cd_week,w.id_customer,w.id_item,w.id_location,
    w.volume_unidade AS volume_unidades,w.faturamento,w.qtd_perda_osa,
    w.avg_sales_price,w.avg_price_cost,w.status_item_geral::text AS tp_activity_level,
    l.rede,l.bandeira,l.uf,l.cidade,l.tipo_local,l.loja,l.regiao,
    i.item,i.descricao_marca,i.hierarquia_1,i.hierarquia_2,i.hierarquia_3
  FROM gold.fato_semanal w
  LEFT JOIN gold.dim_local l ON l.id_customer=w.id_customer AND l.id_location=w.id_location
  LEFT JOIN gold.dim_itens i ON i.id_customer=w.id_customer AND i.id_item=w.id_item
  WHERE 1=1
{weekly_predicates}
), ranked_weeks AS (
  SELECT id_customer,data,cd_week,DENSE_RANK() OVER (
    PARTITION BY id_customer ORDER BY cd_week DESC
  ) week_rank
  FROM (SELECT DISTINCT id_customer,data,cd_week FROM weekly_filtered) x
), weekly_scoped AS (
  SELECT f.* FROM weekly_filtered f JOIN ranked_weeks r USING(id_customer,data,cd_week)
  WHERE r.week_rank<=13
), weekly AS (
  SELECT data,id_customer,MAX(cd_week) cd_week,
    SUM(COALESCE(faturamento,0))::float8 faturamento_sum,
    SUM(COALESCE(volume_unidades,0))::float8 volume_sum,
    SUM(COALESCE(avg_sales_price,0))::float8 fallback_price_sum,
    COUNT(avg_sales_price)::bigint fallback_price_count,
    SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 cost_sum,
    SUM(COALESCE(qtd_perda_osa,0))::float8 loss_sum,
    SUM(COALESCE(avg_sales_price,0)) FILTER (WHERE faturamento>0)::float8 price_sum,
    COUNT(avg_sales_price) FILTER (WHERE faturamento>0)::bigint price_count
  FROM weekly_scoped GROUP BY data,id_customer
), weekly_factors AS (
  SELECT s.data,s.id_customer,c.nm_measure,MAX(c.conversion_rate)::float8 conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM weekly_scoped) s
  JOIN gold.dim_conversao c ON c.id_customer=s.id_customer AND c.id_item::text=s.id_item
  GROUP BY s.data,s.id_customer,c.nm_measure
), monthly_filtered AS (
  SELECT
    f.mes_ano::date AS data,
    f.id_customer,
    f.id_item,
    f.id_location,
    f.volume_unidades,
    f.faturamento,
    f.estoque_unidades,
    f.estoque_medio,
    f.qtd_problemas_osa,
    f.qtd_item_ativo_osa,
    f.rup,
    f.est_virtual,
    f.giro,
    f.avg_sales_price,
    f.avg_price_cost,
    f.status_item_geral,
    f.tp_activity_level,
    CASE f.tp_activity_level
      WHEN 'F' THEN 'Fast Mover'
      WHEN 'S' THEN 'Slow Mover'
      WHEN 'US' THEN 'Ultra Slow Mover'
      WHEN 'N' THEN 'New Mover'
      ELSE COALESCE(f.tp_activity_level,'Outros')
    END AS activity_level,
    l.rede,l.bandeira,l.uf,l.cidade,l.tipo_local,l.loja,l.regiao,
    i.item,i.descricao_marca,i.hierarquia_1,i.hierarquia_2,i.hierarquia_3
  FROM gold.fato_historico f
  LEFT JOIN gold.dim_local l
    ON l.id_customer=f.id_customer AND l.id_location=f.id_location
  LEFT JOIN gold.dim_itens i
    ON i.id_customer=f.id_customer AND i.id_item=f.id_item
  WHERE 1=1
{monthly_predicates}
), monthly AS (
  SELECT data,id_customer,
    SUM(COALESCE(faturamento,0))::float8 faturamento_sum,
    SUM(COALESCE(volume_unidades,0))::float8 volume_sum,
    SUM(COALESCE(avg_sales_price,0))::float8 fallback_price_sum,
    COUNT(avg_sales_price)::bigint fallback_price_count,
    SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 cost_sum,
    SUM(COALESCE(qtd_perda_osa,0))::float8 loss_sum,
    SUM(COALESCE(avg_sales_price,0)) FILTER (WHERE faturamento>0)::float8 price_sum,
    COUNT(avg_sales_price) FILTER (WHERE faturamento>0)::bigint price_count
  FROM monthly_filtered GROUP BY data,id_customer
), monthly_factors AS (
  SELECT f.data,f.id_customer,c.nm_measure,MAX(c.conversion_rate)::float8 conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM monthly_filtered) f
  JOIN gold.dim_conversao c ON c.id_customer=f.id_customer AND c.id_item::text=f.id_item
  GROUP BY f.data,f.id_customer,c.nm_measure
)
SELECT
  'timeline'::text row_scope,w.data,w.cd_week,w.id_customer,f.nm_measure,
  CASE WHEN w.faturamento_sum>0 THEN w.faturamento_sum
       WHEN f.conversion_factor IS NOT NULL AND w.fallback_price_count>0
       THEN (w.volume_sum*f.conversion_factor)
          *((w.fallback_price_sum/w.fallback_price_count)*f.conversion_factor)
       ELSE NULL END::float8 sellout_sum,
  w.cost_sum,(w.volume_sum*f.conversion_factor)::float8 sales_sum,
  (w.loss_sum*f.conversion_factor)::float8 loss_sum,
  (w.price_sum*f.conversion_factor)::float8 price_numerator,w.price_count,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,NULL::text tp_activity_level,
  NULL::text activity_level,NULL::text item,NULL::text descricao_marca,
  NULL::text hierarquia_1,NULL::text hierarquia_2,NULL::text hierarquia_3
FROM weekly w JOIN weekly_factors f USING(data,id_customer)
UNION ALL
SELECT
  'summary'::text row_scope,m.data,NULL::text cd_week,m.id_customer,f.nm_measure,
  CASE WHEN m.faturamento_sum>0 THEN m.faturamento_sum
       WHEN f.conversion_factor IS NOT NULL AND m.fallback_price_count>0
       THEN (m.volume_sum*f.conversion_factor)
          *((m.fallback_price_sum/m.fallback_price_count)*f.conversion_factor)
       ELSE NULL END::float8 sellout_sum,
  m.cost_sum,(m.volume_sum*f.conversion_factor)::float8 sales_sum,
  (m.loss_sum*f.conversion_factor)::float8 loss_sum,
  (m.price_sum*f.conversion_factor)::float8 price_numerator,m.price_count,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,NULL::text tp_activity_level,
  NULL::text activity_level,NULL::text item,NULL::text descricao_marca,
  NULL::text hierarquia_1,NULL::text hierarquia_2,NULL::text hierarquia_3
FROM monthly m JOIN monthly_factors f USING(data,id_customer)
""".strip()
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n" + detail + "\n"
        "{% else %}\nSELECT * FROM gold.nr_panorama_sales_weekly_card_default\n{% endif %}"
    )



def monthly_inventory_semantic_sql() -> str:
    """Certified monthly Stock/Giro/ROI/OSA components over the serving mart."""
    checks = " or ".join(f"get_filters('{column}')" for column in WEEKLY_FILTER_COLUMNS)
    predicates = _jinja_filter_predicates("f", "tp_activity_level", {
        "rede": "l.rede", "bandeira": "l.bandeira", "uf": "l.uf",
        "cidade": "l.cidade", "tipo_local": "l.tipo_local",
        "loja": "l.loja", "regiao": "l.regiao", "item": "i.item",
        "descricao_marca": "i.descricao_marca", "hierarquia_1": "i.hierarquia_1",
        "hierarquia_2": "i.hierarquia_2", "hierarquia_3": "i.hierarquia_3",
    })
    detail = f"""
WITH filtered AS (
  SELECT
    f.mes_ano::date AS data,
    f.id_customer,
    f.id_item,
    f.id_location,
    f.volume_unidades,
    f.faturamento,
    f.estoque_unidades,
    f.estoque_medio,
    f.qtd_problemas_osa,
    f.qtd_item_ativo_osa,
    f.rup,
    f.est_virtual,
    f.giro,
    f.avg_sales_price,
    f.avg_price_cost,
    f.status_item_geral,
    f.tp_activity_level,
    CASE f.tp_activity_level
      WHEN 'F' THEN 'Fast Mover'
      WHEN 'S' THEN 'Slow Mover'
      WHEN 'US' THEN 'Ultra Slow Mover'
      WHEN 'N' THEN 'New Mover'
      ELSE COALESCE(f.tp_activity_level,'Outros')
    END AS activity_level,
    l.rede,l.bandeira,l.uf,l.cidade,l.tipo_local,l.loja,l.regiao,
    i.item,i.descricao_marca,i.hierarquia_1,i.hierarquia_2,i.hierarquia_3
  FROM gold.fato_historico f
  LEFT JOIN gold.dim_local l
    ON l.id_customer=f.id_customer AND l.id_location=f.id_location
  LEFT JOIN gold.dim_itens i
    ON i.id_customer=f.id_customer AND i.id_item=f.id_item
  WHERE 1=1
{predicates}
), monthly AS (
  SELECT
    data,id_customer,
    SUM(COALESCE(faturamento,0))::float8 AS faturamento_sum,
    SUM(COALESCE(volume_unidades,0))::float8 AS volume_sum,
    SUM(COALESCE(avg_sales_price,0))::float8 AS fallback_price_sum,
    COUNT(avg_sales_price)::bigint AS fallback_price_count,
    SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 AS sales_cost_sum,
    SUM(COALESCE(estoque_medio,0)*COALESCE(avg_price_cost,0))::float8 AS stock_cost_sum,
    SUM(COALESCE(estoque_unidades,0))::float8 AS stock_qty_base,
    SUM(giro) FILTER (WHERE giro>0)::float8 AS giro_num,
    COUNT(giro) FILTER (WHERE giro>0)::bigint AS giro_den,
    SUM(COALESCE(qtd_problemas_osa,0))::float8 AS osa_problem_sum,
    SUM(COALESCE(qtd_item_ativo_osa,0))::float8 AS osa_active_sum,
    SUM(COALESCE(rup,0))::float8 AS rupture_sum,
    SUM(COALESCE(status_item_geral,0))::float8 AS status_sum,
    SUM(COALESCE(est_virtual,0))::float8 AS isv_sum
  FROM filtered
  GROUP BY data,id_customer
), factors AS (
  SELECT f.data,f.id_customer,c.nm_measure,MAX(c.conversion_rate)::float8 AS conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM filtered) f
  JOIN gold.dim_conversao c
    ON c.id_customer=f.id_customer AND c.id_item::text=f.id_item::text
  GROUP BY f.data,f.id_customer,c.nm_measure
)
SELECT
  m.data,m.id_customer,f.nm_measure,
  CASE WHEN m.faturamento_sum>0 THEN m.faturamento_sum
       WHEN f.conversion_factor IS NOT NULL AND m.fallback_price_count>0
       THEN (m.volume_sum*f.conversion_factor)
          *((m.fallback_price_sum/m.fallback_price_count)*f.conversion_factor)
       ELSE NULL END::float8 AS sellout_sum,
  m.sales_cost_sum,m.stock_cost_sum,
  (m.stock_qty_base*f.conversion_factor)::float8 AS stock_qty_sum,
  m.giro_num,m.giro_den,
  m.osa_problem_sum,m.osa_active_sum,m.rupture_sum,m.status_sum,m.isv_sum,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,
  NULL::text tp_activity_level,NULL::text activity_level,NULL::text item,
  NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,
  NULL::text hierarquia_3
FROM monthly m
JOIN factors f USING(data,id_customer)
""".strip()
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n" + detail + "\n"
        "{% else %}\nSELECT * FROM gold.nr_panorama_inventory_monthly_default\n{% endif %}"
    )


def weekly_inventory_card_semantic_sql() -> str:
    """TOP-13 weekly inventory timeline plus monthly summary in one dataset."""
    checks = " or ".join(f"get_filters('{column}')" for column in WEEKLY_FILTER_COLUMNS)
    weekly_predicates = _jinja_filter_predicates("w")
    monthly_predicates = _jinja_filter_predicates("f", "tp_activity_level", {
        "rede": "l.rede", "bandeira": "l.bandeira", "uf": "l.uf",
        "cidade": "l.cidade", "tipo_local": "l.tipo_local",
        "loja": "l.loja", "regiao": "l.regiao", "item": "i.item",
        "descricao_marca": "i.descricao_marca", "hierarquia_1": "i.hierarquia_1",
        "hierarquia_2": "i.hierarquia_2", "hierarquia_3": "i.hierarquia_3",
    })
    detail = f"""
WITH weekly_filtered AS (
  SELECT w.* FROM gold.nr_panorama_inventory_weekly_detail w WHERE 1=1
{weekly_predicates}
), ranked_weeks AS (
  SELECT id_customer,data,cd_week,DENSE_RANK() OVER (
    PARTITION BY id_customer ORDER BY cd_week DESC
  ) AS week_rank
  FROM (SELECT DISTINCT id_customer,data,cd_week FROM weekly_filtered) x
), tenant_latest AS (
  SELECT id_customer,MAX(cd_week) AS latest_cd_week
  FROM gold.nr_panorama_inventory_weekly_detail
  GROUP BY id_customer
), weekly_scoped AS (
  SELECT f.*,l.latest_cd_week
  FROM weekly_filtered f
  JOIN ranked_weeks r USING(id_customer,data,cd_week)
  JOIN tenant_latest l USING(id_customer)
  WHERE r.week_rank<=13
), weekly AS (
  SELECT
    data,cd_week,id_customer,MAX(latest_cd_week) AS latest_cd_week,
    SUM(COALESCE(faturamento,0))::float8 AS faturamento_sum,
    SUM(COALESCE(volume_unidades,0))::float8 AS volume_sum,
    SUM(COALESCE(avg_sales_price,0))::float8 AS fallback_price_sum,
    COUNT(avg_sales_price)::bigint AS fallback_price_count,
    SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 AS sales_cost_sum,
    SUM(COALESCE(estoque_medio,0)*COALESCE(avg_price_cost,0))::float8 AS stock_cost_sum,
    SUM(COALESCE(estoque_unidades,0))::float8 AS stock_qty_base,
    SUM(giro) FILTER (WHERE giro IS NOT NULL)::float8 AS giro_num_raw,
    COUNT(giro)::bigint AS giro_den_raw,
    SUM(COALESCE(qtd_problemas_osa,0))::float8 AS osa_problem_sum,
    SUM(COALESCE(qtd_item_ativo_osa,0))::float8 AS osa_active_sum,
    SUM(COALESCE(rup,0))::float8 AS rupture_sum,
    SUM(COALESCE(status_item_geral,0))::float8 AS status_sum,
    SUM(COALESCE(est_virtual,0))::float8 AS isv_sum
  FROM weekly_scoped
  GROUP BY data,cd_week,id_customer
), weekly_factors AS (
  SELECT s.data,s.id_customer,c.nm_measure,MAX(c.conversion_rate)::float8 AS conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM weekly_scoped) s
  JOIN gold.dim_conversao c
    ON c.id_customer=s.id_customer AND c.id_item::text=s.id_item::text
  GROUP BY s.data,s.id_customer,c.nm_measure
), monthly_filtered AS (
  SELECT h.* FROM gold.nr_overview_history h WHERE 1=1
{monthly_predicates}
), monthly AS (
  SELECT
    data,id_customer,
    SUM(COALESCE(faturamento,0))::float8 AS faturamento_sum,
    SUM(COALESCE(volume_unidades,0))::float8 AS volume_sum,
    SUM(COALESCE(avg_sales_price,0))::float8 AS fallback_price_sum,
    COUNT(avg_sales_price)::bigint AS fallback_price_count,
    SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 AS sales_cost_sum,
    SUM(COALESCE(estoque_medio,0)*COALESCE(avg_price_cost,0))::float8 AS stock_cost_sum,
    SUM(COALESCE(estoque_unidades,0))::float8 AS stock_qty_base,
    SUM(giro) FILTER (WHERE giro>0)::float8 AS giro_num,
    COUNT(giro) FILTER (WHERE giro>0)::bigint AS giro_den,
    SUM(COALESCE(qtd_problemas_osa,0))::float8 AS osa_problem_sum,
    SUM(COALESCE(qtd_item_ativo_osa,0))::float8 AS osa_active_sum,
    SUM(COALESCE(rup,0))::float8 AS rupture_sum,
    SUM(COALESCE(status_item_geral,0))::float8 AS status_sum,
    SUM(COALESCE(est_virtual,0))::float8 AS isv_sum
  FROM monthly_filtered
  GROUP BY data,id_customer
), monthly_factors AS (
  SELECT f.data,f.id_customer,c.nm_measure,MAX(c.conversion_rate)::float8 AS conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM monthly_filtered) f
  JOIN gold.dim_conversao c
    ON c.id_customer=f.id_customer AND c.id_item::text=f.id_item::text
  GROUP BY f.data,f.id_customer,c.nm_measure
)
SELECT
  'timeline'::text AS row_scope,
  w.data,w.cd_week,w.id_customer,f.nm_measure,
  CASE WHEN w.faturamento_sum>0 THEN w.faturamento_sum
       WHEN f.conversion_factor IS NOT NULL AND w.fallback_price_count>0
       THEN (w.volume_sum*f.conversion_factor)
          *((w.fallback_price_sum/w.fallback_price_count)*f.conversion_factor)
       ELSE NULL END::float8 AS sellout_sum,
  w.sales_cost_sum,w.stock_cost_sum,
  (w.stock_qty_base*f.conversion_factor)::float8 AS stock_qty_sum,
  CASE WHEN w.cd_week=w.latest_cd_week THEN NULL ELSE w.giro_num_raw END::float8 AS giro_num,
  CASE WHEN w.cd_week=w.latest_cd_week THEN NULL ELSE w.giro_den_raw END::bigint AS giro_den,
  w.osa_problem_sum,w.osa_active_sum,w.rupture_sum,w.status_sum,w.isv_sum,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,
  NULL::text tp_activity_level,NULL::text activity_level,NULL::text item,
  NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,
  NULL::text hierarquia_3
FROM weekly w
JOIN weekly_factors f USING(data,id_customer)

UNION ALL

SELECT
  'summary'::text AS row_scope,
  m.data,NULL::text AS cd_week,m.id_customer,f.nm_measure,
  CASE WHEN m.faturamento_sum>0 THEN m.faturamento_sum
       WHEN f.conversion_factor IS NOT NULL AND m.fallback_price_count>0
       THEN (m.volume_sum*f.conversion_factor)
          *((m.fallback_price_sum/m.fallback_price_count)*f.conversion_factor)
       ELSE NULL END::float8 AS sellout_sum,
  m.sales_cost_sum,m.stock_cost_sum,
  (m.stock_qty_base*f.conversion_factor)::float8 AS stock_qty_sum,
  m.giro_num,m.giro_den,
  m.osa_problem_sum,m.osa_active_sum,m.rupture_sum,m.status_sum,m.isv_sum,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,
  NULL::text tp_activity_level,NULL::text activity_level,NULL::text item,
  NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,
  NULL::text hierarquia_3
FROM monthly m
JOIN monthly_factors f USING(data,id_customer)
""".strip()
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n" + detail + "\n"
        "{% else %}\nSELECT * FROM gold.nr_panorama_inventory_weekly_card_default\n{% endif %}"
    )


def monthly_gap_semantic_sql() -> str:
    """Power BI LASTNONBLANK TVD/IVD at monthly grain."""
    checks = " or ".join(f"get_filters('{column}')" for column in WEEKLY_FILTER_COLUMNS)
    predicates = _jinja_filter_predicates("o")
    detail = f"""
WITH filtered AS (
  SELECT o.* FROM gold.nr_panorama_opportunities o WHERE 1=1
{predicates}
), daily AS (
  SELECT
    id_customer,data,
    SUM(tvd_simplificado)::float8 AS tvd,
    SUM(ivd_simplificado)::float8 AS ivd
  FROM filtered
  GROUP BY id_customer,data
), tagged AS (
  SELECT d.*,DATE_TRUNC('month',data)::date AS period_start
  FROM daily d
), anchors AS (
  SELECT
    id_customer,period_start,
    MAX(data) FILTER (WHERE tvd IS NOT NULL) AS tvd_date,
    MAX(data) FILTER (WHERE ivd IS NOT NULL) AS ivd_date
  FROM tagged
  GROUP BY id_customer,period_start
)
SELECT
  a.period_start AS data,a.id_customer,
  tvd.tvd,ivd.ivd,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,
  NULL::text tp_activity_level,NULL::text activity_level,NULL::text item,
  NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,
  NULL::text hierarquia_3
FROM anchors a
LEFT JOIN daily tvd ON tvd.id_customer=a.id_customer AND tvd.data=a.tvd_date
LEFT JOIN daily ivd ON ivd.id_customer=a.id_customer AND ivd.data=a.ivd_date
""".strip()
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n" + detail + "\n"
        "{% else %}\nSELECT * FROM gold.nr_panorama_gap_monthly_default\n{% endif %}"
    )


def weekly_gap_card_semantic_sql() -> str:
    """TOP-13 weekly LASTNONBLANK TVD/IVD plus monthly summary rows."""
    checks = " or ".join(f"get_filters('{column}')" for column in WEEKLY_FILTER_COLUMNS)
    predicates = _jinja_filter_predicates("o")
    detail = f"""
WITH filtered AS (
  SELECT o.* FROM gold.nr_panorama_opportunities o WHERE 1=1
{predicates}
), daily AS (
  SELECT
    id_customer,data,
    SUM(tvd_simplificado)::float8 AS tvd,
    SUM(ivd_simplificado)::float8 AS ivd
  FROM filtered
  GROUP BY id_customer,data
), weekly_tagged AS (
  SELECT d.*,DATE_TRUNC('week',data)::date AS period_start FROM daily d
), weekly_anchors AS (
  SELECT
    id_customer,period_start,
    MAX(data) FILTER (WHERE tvd IS NOT NULL) AS tvd_date,
    MAX(data) FILTER (WHERE ivd IS NOT NULL) AS ivd_date
  FROM weekly_tagged
  GROUP BY id_customer,period_start
), weekly_values AS (
  SELECT
    a.id_customer,a.period_start AS data,tvd.tvd,ivd.ivd,
    DENSE_RANK() OVER (
      PARTITION BY a.id_customer ORDER BY a.period_start DESC
    ) AS week_rank
  FROM weekly_anchors a
  LEFT JOIN daily tvd ON tvd.id_customer=a.id_customer AND tvd.data=a.tvd_date
  LEFT JOIN daily ivd ON ivd.id_customer=a.id_customer AND ivd.data=a.ivd_date
), monthly_tagged AS (
  SELECT d.*,DATE_TRUNC('month',data)::date AS period_start FROM daily d
), monthly_anchors AS (
  SELECT
    id_customer,period_start,
    MAX(data) FILTER (WHERE tvd IS NOT NULL) AS tvd_date,
    MAX(data) FILTER (WHERE ivd IS NOT NULL) AS ivd_date
  FROM monthly_tagged
  GROUP BY id_customer,period_start
)
SELECT
  'timeline'::text AS row_scope,
  w.data,w.id_customer,w.tvd,w.ivd,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,
  NULL::text tp_activity_level,NULL::text activity_level,NULL::text item,
  NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,
  NULL::text hierarquia_3
FROM weekly_values w
WHERE w.week_rank<=13

UNION ALL

SELECT
  'summary'::text AS row_scope,
  a.period_start AS data,a.id_customer,tvd.tvd,ivd.ivd,
  NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,
  NULL::text tipo_local,NULL::text loja,NULL::text regiao,
  NULL::text tp_activity_level,NULL::text activity_level,NULL::text item,
  NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,
  NULL::text hierarquia_3
FROM monthly_anchors a
LEFT JOIN daily tvd ON tvd.id_customer=a.id_customer AND tvd.data=a.tvd_date
LEFT JOIN daily ivd ON ivd.id_customer=a.id_customer AND ivd.data=a.ivd_date
""".strip()
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n" + detail + "\n"
        "{% else %}\nSELECT * FROM gold.nr_panorama_gap_weekly_card_default\n{% endif %}"
    )


def sql_filter(expression):
    return {
        "clause": "WHERE",
        "comparator": "",
        "expressionType": "SQL",
        "filterOptionName": "filter_panorama_gap_period",
        "fromFormData": True,
        "sqlExpression": expression,
    }


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


def custom_params(dataset, title, metrics, *, grain="P1M", styles="bar|bar|line", formats="number", groupby=None, variant="panorama", row_limit=10000, labels=None, **extra):
    params = {
        "datasource": f"{dataset.id}__table", "viz_type": "neoretail-kpi-card",
        "x_axis": "data", "time_grain_sqla": grain, "time_range": "No filter",
        "metrics": metrics, "row_limit": row_limit, "card_title": title,
        "card_variant": variant, "help_text": title, "metric_labels": labels or "|".join(m["label"] for m in metrics),
        "metric_formats": formats, "metric_directions": "higher", "chart_styles": styles,
        "accent_color": "#7C4AD9", "show_tasks": False, "adhoc_filters": [], "groupby": groupby or [],
    }
    params.update(extra)
    return params


def table_params(dataset, groupby, metrics, page_length=12):
    return {
        "datasource": f"{dataset.id}__table", "viz_type": "table", "query_mode": "aggregate",
        "groupby": [groupby], "metrics": metrics, "adhoc_filters": [], "time_range": "No filter",
        "row_limit": 1000, "page_length": page_length, "include_search": True,
        "server_pagination": False, "order_desc": True, "table_timestamp_format": "%d/%m/%Y",
        "percent_metrics": [], "align_pn": False, "color_pn": False, "show_cell_bars": False,
    }


def comparison_pivot_params(dataset, rows, metrics):
    """Power BI matrix equivalent: hierarchy rows and mixed semantic metrics."""
    return {
        "datasource": f"{dataset.id}__table",
        "viz_type": "pivot_table_v2",
        "groupbyRows": list(rows),
        "groupbyColumns": [],
        "metrics": metrics,
        "adhoc_filters": [],
        "time_range": "Current year",
        # The AMBEV retail hierarchy has more than 2,000 leaf rows.  The PBIP
        # matrix has no Top N filter, so the Superset contract must not silently
        # truncate it at the former 1,000-row default.
        "row_limit": 10000,
        "order_desc": True,
        "aggregateFunction": "Sum",
        "rowOrder": "value_z_to_a",
        "colOrder": "key_a_to_z",
        "transposePivot": False,
        "combineMetric": False,
        "showRowTotals": True,
        "showColTotals": False,
        "expandRows": False,
        "valueFormat": "SMART_NUMBER",
        "date_format": "%m/%Y",
    }


class Layout:
    def __init__(self):
        self.nodes = {
            "ROOT_ID": {"id": "ROOT_ID", "type": "ROOT", "children": ["GRID_ID"]},
            "GRID_ID": {"id": "GRID_ID", "type": "GRID", "parents": ["ROOT_ID"], "children": []},
        }
        self.counter = 0

    def _id(self, prefix):
        self.counter += 1
        return f"{prefix}-{self.counter}"

    def tabs(self, parent, parents, title, entries, height=52):
        tabs_id = self._id("TABS")
        tab_ids = []
        self.nodes[tabs_id] = {"id": tabs_id, "type": "TABS", "parents": parents, "children": tab_ids, "meta": {"defaultText": title}}
        self.nodes[parent]["children"].append(tabs_id)
        for label, chart_rows in entries:
            tab_id = self._id("TAB")
            tab_ids.append(tab_id)
            self.nodes[tab_id] = {"id": tab_id, "type": "TAB", "parents": [*parents, tabs_id], "children": [], "meta": {"text": label}}
            for row_charts in chart_rows:
                # A compact, full-width control bar precedes the tall KPI
                # hierarchy charts. All other layouts retain their heights.
                row_height = row_charts.get("height", height) if isinstance(row_charts, dict) else height
                content = row_charts["charts"] if isinstance(row_charts, dict) else row_charts
                self.row(tab_id, [*parents, tabs_id, tab_id], content, row_height)
        return tabs_id

    def period_tabs(self, parent, parents, title, entries, height=52):
        """Render business views with an inner Mensal/Semanal selector."""
        outer_id = self._id("TABS")
        outer_tabs = []
        self.nodes[outer_id] = {"id": outer_id, "type": "TABS", "parents": parents, "children": outer_tabs, "meta": {"defaultText": title}}
        self.nodes[parent]["children"].append(outer_id)
        for label, periods in entries:
            tab_id = self._id("TAB")
            outer_tabs.append(tab_id)
            tab_parents = [*parents, outer_id]
            self.nodes[tab_id] = {"id": tab_id, "type": "TAB", "parents": tab_parents, "children": [], "meta": {"text": label}}
            self.tabs(tab_id, [*tab_parents, tab_id], f"Período de {label}", [
                (period.title(), [[*chart] if isinstance(chart, (list, tuple)) else [chart]])
                for period, chart in periods
            ], height)
        return outer_id

    def row(self, parent, parents, charts, height):
        row_id = self._id("ROW")
        children = []
        self.nodes[row_id] = {"id": row_id, "type": "ROW", "parents": parents, "children": children, "meta": {"background": "BACKGROUND_TRANSPARENT"}}
        self.nodes[parent]["children"].append(row_id)
        widths = [3, 9] if len(charts) == 2 and "Resumo" in charts[0].slice_name else [max(1, 12 // len(charts))] * len(charts)
        for chart, width in zip(charts, widths):
            chart_id = f"CHART-{chart.id}"
            children.append(chart_id)
            self.nodes[chart_id] = {"id": chart_id, "type": "CHART", "parents": [*parents, row_id], "children": [], "meta": {"chartId": chart.id, "height": height, "width": width, "sliceName": chart.slice_name, "uuid": str(chart.uuid)}}


def main():
    app = create_app()
    with app.app_context():
        from superset import db
        from superset.connectors.sqla.models import SqlaTable, SqlMetric
        from superset.models.core import Database
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice

        database = db.session.query(Database).filter(Database.database_name == "NeoRetail Gold - PostgreSQL Local").one()
        history = upsert_dataset(db.session, SqlaTable, database, "nr_overview_history", table_name="nr_overview_history")
        weekly = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_weekly_interactive",
            sql=weekly_semantic_sql(),
        )
        weekly_sales = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_sales_weekly_interactive",
            sql=weekly_sales_semantic_sql(),
        )
        weekly_sales_card = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_sales_weekly_card_interactive",
            sql=weekly_sales_card_semantic_sql(),
        )
        monthly_sales = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_sales_monthly_interactive",
            sql=monthly_sales_semantic_sql(),
        )
        monthly_quantity = upsert_dataset(
            db.session, SqlaTable, database, "nr_overview_quantity_interactive",
            sql=quantity_semantic_sql(),
        )
        monthly_inventory = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_inventory_monthly_interactive",
            sql=monthly_inventory_semantic_sql(),
        )
        weekly_inventory_card = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_inventory_weekly_card_interactive",
            sql=weekly_inventory_card_semantic_sql(),
        )
        gap_monthly = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_gap_monthly_interactive",
            sql=monthly_gap_semantic_sql(),
        )
        gap_weekly_card = upsert_dataset(
            db.session, SqlaTable, database, "nr_panorama_gap_weekly_card_interactive",
            sql=weekly_gap_card_semantic_sql(),
        )
        comparison_history = {
            scope: upsert_dataset(
                db.session,
                SqlaTable,
                database,
                f"nr_panorama_comparison_{scope}_history",
                sql=comparison_history_sql(scope),
            )
            for scope in COMPARISON_SCOPES
        }
        comparison_gap = {
            scope: upsert_dataset(
                db.session,
                SqlaTable,
                database,
                f"nr_panorama_comparison_{scope}_gap",
                sql=comparison_gap_sql(scope),
            )
            for scope in COMPARISON_SCOPES
        }
        kpi_dimensions = {
            scope: upsert_dataset(
                db.session, SqlaTable, database,
                f"nr_panorama_kpi_dimension_{scope}",
                sql=kpi_dimension_sql(scope),
            )
            for scope in KPI_DIMENSION_SCOPES
        }
        kpi_filter_options = upsert_dataset(
            db.session, SqlaTable, database,
            "nr_panorama_kpi_filter_options",
            sql=kpi_filter_options_sql(),
        )
        kpi_order_metric = db.session.query(SqlMetric).filter(
            SqlMetric.table_id == kpi_filter_options.id,
            SqlMetric.metric_name == KPI_ORDER_METRIC_NAME,
        ).one_or_none()
        if kpi_order_metric is None:
            kpi_order_metric = SqlMetric(
                table_id=kpi_filter_options.id,
                metric_name=KPI_ORDER_METRIC_NAME,
                expression="MIN(kpi_order)",
                metric_type="MIN",
                d3format=",d",
            )
            db.session.add(kpi_order_metric)
        else:
            kpi_order_metric.expression = "MIN(kpi_order)"
            kpi_order_metric.metric_type = "MIN"
            kpi_order_metric.d3format = ",d"
        month_order_metric = db.session.query(SqlMetric).filter(
            SqlMetric.table_id == kpi_filter_options.id,
            SqlMetric.metric_name == KPI_MONTH_ORDER_METRIC_NAME,
        ).one_or_none()
        if month_order_metric is None:
            month_order_metric = SqlMetric(
                table_id=kpi_filter_options.id,
                metric_name=KPI_MONTH_ORDER_METRIC_NAME,
                expression="MIN(comparison_year_month_sort)",
                metric_type="MIN",
                d3format=",d",
            )
            db.session.add(month_order_metric)
        else:
            month_order_metric.expression = "MIN(comparison_year_month_sort)"
            month_order_metric.metric_type = "MIN"
            month_order_metric.d3format = ",d"
        latest = upsert_dataset(db.session, SqlaTable, database, "nr_panorama_latest", table_name="nr_panorama_latest")
        mart = upsert_dataset(db.session, SqlaTable, database, "nr_panorama_opportunities", table_name="nr_panorama_opportunities")
        opportunities = mart
        opportunities_latest = upsert_dataset(db.session, SqlaTable, database, "nr_panorama_opportunities_latest", table_name="nr_panorama_opportunities_latest")
        gap_periodic = upsert_dataset(
            db.session,
            SqlaTable,
            database,
            "nr_panorama_gap_periodic",
            table_name="nr_panorama_gap_periodic",
        )
        filter_options = upsert_dataset(
            db.session, SqlaTable, database, "nr_filter_options", table_name="nr_filter_options"
        )
        conversion_options = upsert_dataset(
            db.session, SqlaTable, database, "nr_conversion_options",
            table_name="nr_conversion_options",
        )
        with database.get_sqla_engine() as engine:
            with engine.connect() as connection:
                weekly_max_date = connection.execute(
                    text("SELECT MAX(data) FROM gold.nr_panorama_weekly")
                ).scalar_one()
        weekly_recent = [sql_filter(
            f"data >= DATE '{weekly_max_date.isoformat()}' - INTERVAL '12 weeks'"
        )] if weekly_max_date else []

        charts = {}
        def add(
            key, dataset, title, params, viz="neoretail-kpi-card", legacy_titles=(),
        ):
            charts[key] = upsert_chart(
                db.session,
                Slice,
                dataset,
                f"[Panorama] {title}",
                params,
                viz,
                tuple(f"[Panorama] {item}" for item in legacy_titles),
            )

        value_semantics = "direct_average:0:1|direct_average:1:1|markup_blank:0:2"
        quantity_semantics = "direct_average:0:1|direct_sum:1:1|weighted_average:2:2"
        value_measures = [
            metric("Venda sell out", "SUM(sellout_sum)"),
            metric("Venda custo", "SUM(cost_sum)"),
        ]
        weekly_value_measures = [
            metric("Venda sell out semanal", "SUM(sellout_sum)"),
            metric("Venda custo semanal", "SUM(cost_sum)"),
        ]
        quantity_measures = [Q["sales"], Q["loss"], Q["price_num"], Q["price_count"]]
        weekly_quantity_measures = [
            metric("Venda quantidade semanal", "SUM(sales_sum)"),
            metric("Perda OSA semanal", "SUM(loss_sum)"),
            metric("Preço soma semanal", "SUM(price_numerator)"),
            metric("Preço linhas semanal", "SUM(price_count)"),
        ]

        params = custom_params(
            monthly_sales, "Evolutivo de vendas", value_measures, grain="P1M",
            styles="bar|bar|line", formats="currency|currency|percent",
            labels="Sell out Venda|Sell out Custo|Markup",
            metric_semantics=value_semantics, summary_count=3, timeline_limit=13,
        )
        add("sales_value_mensal", monthly_sales, "Evolutivo de vendas — Valor mensal", params)

        params = custom_params(
            weekly_sales_card, "Evolutivo de vendas", weekly_value_measures, grain="P1W",
            styles="bar|bar|line", formats="currency|currency|percent",
            labels="Sell out Venda|Sell out Custo|Markup",
            metric_semantics=value_semantics, summary_count=3, timeline_limit=13,
            summary_query_scope="summary", timeline_query_scope="timeline",
        )
        add("sales_value_semanal", weekly_sales_card, "Evolutivo de vendas — Valor semanal", params)

        params = custom_params(
            monthly_quantity, "Evolutivo de vendas", quantity_measures, grain="P1M",
            styles="bar|bar|line", formats="quantity|quantity|currency",
            labels="Sell out Volume|Perda OSA|Preço Médio",
            metric_semantics=quantity_semantics, summary_count=3, timeline_limit=13,
        )
        add("sales_quantity_mensal", monthly_quantity, "Evolutivo de vendas — Quantidade mensal", params)

        params = custom_params(
            weekly_sales_card, "Evolutivo de vendas", weekly_quantity_measures, grain="P1W",
            styles="bar|bar|line", formats="quantity|quantity|currency",
            labels="Sell out Volume|Perda OSA|Preço Médio",
            metric_semantics=quantity_semantics, summary_count=3, timeline_limit=13,
            summary_query_scope="summary", timeline_query_scope="timeline",
        )
        add("sales_quantity_semanal", weekly_sales_card, "Evolutivo de vendas — Quantidade semanal", params)

        # Panorama > Evolutivo de estoque.
        # The Report definition uses four outer views over the same business block:
        # Estoque, Giro x ROI, OSA and Falta x Excesso.

        # ESTOQUE
        stock_measures = [
            metric("Estoque preço custo", "SUM(stock_cost_sum)"),
            metric("Estoque quantidade", "SUM(stock_qty_sum)"),
        ]
        params = custom_params(
            monthly_inventory,
            "Evolutivo de estoque",
            stock_measures,
            grain="P1M",
            styles="bar|bar",
            formats="currency|quantity",
            labels="Estoque Preço Custo|Estoque Quantidade",
            semantic_profile="stock_bundle",
            summary_count=2,
            timeline_limit=13,
        )
        add("stock_mensal", monthly_inventory, "Evolutivo de estoque — Estoque mensal", params)

        params = custom_params(
            weekly_inventory_card,
            "Evolutivo de estoque",
            stock_measures,
            grain="P1W",
            styles="bar|bar",
            formats="currency|quantity",
            labels="Estoque Preço Custo|Estoque Quantidade",
            semantic_profile="stock_bundle",
            summary_count=2,
            timeline_limit=13,
            summary_query_scope="summary",
            timeline_query_scope="timeline",
        )
        add("stock_semanal", weekly_inventory_card, "Evolutivo de estoque — Estoque semanal", params)

        # GIRO x ROI
        # Report contract: Stock Cost as bar + ROI and Giro as lines.
        # ROI is recomputed from Sell Out / Venda Custo / Estoque Custo.
        # Giro is a weighted average over additive sum/count components.
        giro_roi_measures = [
            metric("Estoque preço custo", "SUM(stock_cost_sum)"),
            metric("Venda sell out", "SUM(sellout_sum)"),
            metric("Venda custo", "SUM(sales_cost_sum)"),
            metric("Estoque custo ROI", "SUM(stock_cost_sum)"),
            metric("Giro soma", "SUM(giro_num)"),
            metric("Giro linhas", "SUM(giro_den)"),
        ]
        giro_roi_semantics = "direct_average:0:1|roi:1:3|weighted_average:4:2"
        params = custom_params(
            monthly_inventory,
            "Evolutivo de estoque",
            giro_roi_measures,
            grain="P1M",
            styles="bar|line|line",
            formats="currency|percent|number",
            labels="Estoque Preço Custo|% ROI|Giro",
            metric_semantics=giro_roi_semantics,
            summary_count=3,
            summary_labels="U3M|Anual|U3M",
            metric_summary_modes="u3m|annual12|u3m",
            timeline_zero_blank_indices="1",
            timeline_limit=13,
        )
        add("giro_roi_mensal", monthly_inventory, "Evolutivo de estoque — Giro x ROI mensal", params)

        params = custom_params(
            weekly_inventory_card,
            "Evolutivo de estoque",
            giro_roi_measures,
            grain="P1W",
            styles="bar|line|line",
            formats="currency|percent|number",
            labels="Estoque Preço Custo|% ROI|Giro",
            metric_semantics=giro_roi_semantics,
            summary_count=3,
            summary_labels="U3M|Anual|U3M",
            metric_summary_modes="u3m|annual12|u3m",
            timeline_zero_blank_indices="1",
            timeline_limit=13,
            summary_query_scope="summary",
            timeline_query_scope="timeline",
        )
        add("giro_roi_semanal", weekly_inventory_card, "Evolutivo de estoque — Giro x ROI semanal", params)

        # OSA
        # %OSA = 1 - problems/active; Ruptura and ISV use STATUS_ITEM_GERAL as denominator.
        osa_measures = [
            metric("OSA problemas", "SUM(osa_problem_sum)"),
            metric("OSA ativos", "SUM(osa_active_sum)"),
            metric("Ruptura numerador", "SUM(rupture_sum)"),
            metric("Ruptura denominador", "SUM(status_sum)"),
            metric("ISV numerador", "SUM(isv_sum)"),
            metric("ISV denominador", "SUM(status_sum)"),
        ]
        osa_semantics = "one_minus_ratio:0:2|ratio_percent:2:2|ratio_percent:4:2"
        params = custom_params(
            monthly_inventory,
            "Evolutivo de estoque",
            osa_measures,
            grain="P1M",
            styles="line|line|line",
            formats="percent|percent|percent",
            labels="% OSA|% Ruptura|% ISV",
            metric_semantics=osa_semantics,
            summary_count=3,
            timeline_limit=13,
        )
        add("osa_mensal", monthly_inventory, "Evolutivo de estoque — OSA mensal", params)

        params = custom_params(
            weekly_inventory_card,
            "Evolutivo de estoque",
            osa_measures,
            grain="P1W",
            styles="line|line|line",
            formats="percent|percent|percent",
            labels="% OSA|% Ruptura|% ISV",
            metric_semantics=osa_semantics,
            summary_count=3,
            timeline_limit=13,
            summary_query_scope="summary",
            timeline_query_scope="timeline",
        )
        add("osa_semanal", weekly_inventory_card, "Evolutivo de estoque — OSA semanal", params)

        # FALTA x EXCESSO (Power BI selector TVD x IVD).
        gap_measures = [
            metric("TVD", "SUM(tvd)"),
            metric("IVD", "SUM(ivd)"),
        ]
        gap_semantics = "direct_average:0:1|direct_average:1:1"
        params = custom_params(
            gap_monthly,
            "Evolutivo de estoque",
            gap_measures,
            grain="P1M",
            styles="line|line",
            formats="currency|currency",
            labels="TVD - Risco|IVD - Excesso",
            metric_semantics=gap_semantics,
            summary_count=2,
            timeline_limit=13,
        )
        add("gap_mensal", gap_monthly, "Evolutivo de estoque — Falta x Excesso mensal", params)

        params = custom_params(
            gap_weekly_card,
            "Evolutivo de estoque",
            gap_measures,
            grain="P1W",
            styles="line|line",
            formats="currency|currency",
            labels="TVD - Risco|IVD - Excesso",
            metric_semantics=gap_semantics,
            summary_count=2,
            timeline_limit=13,
            summary_query_scope="summary",
            timeline_query_scope="timeline",
        )
        add("gap_semanal", gap_weekly_card, "Evolutivo de estoque — Falta x Excesso semanal", params)

        add(
            "kpi_control_bar", kpi_filter_options, "Controles dos KPIs",
            kpi_filter_bar_params(kpi_filter_options),
        )

        kpi_dimension_labels = (
            ("region", "Região"),
            ("retail", "Varejo"),
            ("hierarchy", "Hierarquia de item"),
        )
        for scope, dimension_label in kpi_dimension_labels:
            add(
                f"kpi_dimension_{scope}",
                kpi_dimensions[scope],
                f"Comparativo de KPIs — {dimension_label}",
                kpi_dimension_params(
                    kpi_dimensions[scope], dimension_label,
                    KPI_DIMENSION_SCOPES[scope][1:] if scope == "region"
                    else KPI_DIMENSION_SCOPES[scope],
                ),
            )

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

        detail_metrics = [P["sales_qty"], P["sellout"], P["cost"], P["markup"], P["price"], P["stock_cost"], P["stock_qty"], P["roi"], P["roi_annual"], P["giro"], P["osa"], P["rup"], P["isv"], P["osa_loss"]]
        detail_dims = (("regiao", "Região"), ("rede", "Rede"), ("hierarquia_1", "Categoria"), ("item", "Produto"), ("activity_level", "Nível de atividade"))
        for column, label in detail_dims:
            add(f"detail_{column}", latest, f"Análise detalhada — {label}", table_params(latest, column, detail_metrics, 20), "table")

        layout = Layout()
        grid_parents = ["ROOT_ID", "GRID_ID"]
        layout.period_tabs("GRID_ID", grid_parents, "Evolutivo de vendas", [
            ("Valor", [(period, charts[f"sales_value_{period}"]) for period in ("mensal", "semanal")]),
            ("Quantidade", [(period, charts[f"sales_quantity_{period}"]) for period in ("mensal", "semanal")]),
        ], 58)
        layout.period_tabs("GRID_ID", grid_parents, "Evolutivo de estoque", [
            (section, [(period, charts[f"{key}_{period}"]) for period in ("mensal", "semanal")])
            for section, key in (("Estoque", "stock"), ("Giro x ROI", "giro_roi"), ("OSA", "osa"), ("Falta x Excesso", "gap"))
        ], 58)
        layout.tabs("GRID_ID", grid_parents, "Comparativo de KPIs por dimensão", [
            (
                "KPIs",
                [
                    {"charts": [charts["kpi_control_bar"]], "height": 15},
                    [charts[f"kpi_dimension_{scope}"] for scope, _ in kpi_dimension_labels],
                ],
            )
        ], 52)
        layout.tabs("GRID_ID", grid_parents, "Comparativos", [
            (
                tab_label,
                [[charts[f"compare_{tab_key}_{scope}"] for scope, _ in comparison_dimensions]],
            )
            for tab_label, tab_key, _ in comparison_tabs
        ], 48)
        layout.tabs("GRID_ID", grid_parents, "Análise detalhada", [
            (label, [[charts[f"detail_{column}"]]]) for column, label in detail_dims
        ], 55)

        dashboard = db.session.query(Dashboard).filter(Dashboard.dashboard_title == DASHBOARD_TITLE).one_or_none()
        if dashboard is None:
            dashboard = Dashboard(dashboard_title=DASHBOARD_TITLE, slug="neoretail-v9-panorama-industria", published=True)
            db.session.add(dashboard)
        dashboard.published = True
        dashboard.position_json = json.dumps(layout.nodes, ensure_ascii=False)
        dashboard.css = ".dashboard-content { background: #e7f0f5 !important; } .dashboard-component-chart-holder { border-radius: 8px; background: #fff; } .dashboard-component-chart-holder > .header { display: none !important; } .dashboard-component-tabs .dashboard-component-tabs .ant-tabs-nav-list { margin-left: auto !important; }"
        filter_targets = {column: filter_options.id for column in WEEKLY_FILTER_COLUMNS}
        filter_targets["nm_measure"] = conversion_options.id
        comparison_dataset_ids = [
            dataset.id
            for dataset in (*comparison_history.values(), *comparison_gap.values())
        ]
        kpi_dimension_dataset_ids = [dataset.id for dataset in kpi_dimensions.values()]
        native_filters = overview_native_filters(
            [history.id, weekly.id, weekly_sales.id, weekly_sales_card.id,
             monthly_sales.id, monthly_quantity.id, monthly_inventory.id,
             weekly_inventory_card.id, gap_monthly.id, gap_weekly_card.id,
             *comparison_dataset_ids, *kpi_dimension_dataset_ids],
            filter_targets,
        )
        # General NeoRetail filters (rede, UF etc.) still govern the three KPI
        # charts, but must not be applied to their control bar, whose options
        # dataset deliberately contains only year/month/KPI columns.
        toolbar_id = charts["kpi_control_bar"].id
        for nf in native_filters:
            nf["scope"]["excluded"] = [
                *nf["scope"].get("excluded", []), toolbar_id,
            ]

        native_filters.extend(kpi_native_filters(kpi_filter_options.id))
        # KPI-only controls must not affect the other 32 business charts or
        # the toolbar itself. Superset's native filter scope uses numeric
        # chart ids, not CHART-* layout node ids.
        kpi_targets = {
            charts[f"kpi_dimension_{scope}"].id
            for scope, _ in kpi_dimension_labels
        }
        kpi_excluded = [
            chart.id for chart in charts.values()
            if chart.id not in kpi_targets
        ]
        for nf in native_filters[-3:]:
            nf["scope"] = {"rootPath": ["ROOT_ID"], "excluded": kpi_excluded}

        dashboard.json_metadata = json.dumps({"timed_refresh_immune_slices": [], "expanded_slices": {}, "refresh_frequency": 0, "color_scheme": "supersetColors", "native_filter_configuration": native_filters, "filter_bar_orientation": "HORIZONTAL"}, ensure_ascii=False)
        dashboard.slices = list(charts.values())
        db.session.commit()
        print(json.dumps({"dashboard_id": dashboard.id, "slug": dashboard.slug, "industry": {"id_customer": 142, "label": "AMBEV"}, "datasets": {"history": history.id, "weekly": weekly.id, "monthly_inventory": monthly_inventory.id, "weekly_inventory_card": weekly_inventory_card.id, "gap_monthly": gap_monthly.id, "gap_weekly_card": gap_weekly_card.id, "comparison_history": {key: value.id for key, value in comparison_history.items()}, "comparison_gap": {key: value.id for key, value in comparison_gap.items()}, "kpi_dimensions": {key: value.id for key, value in kpi_dimensions.items()}, "kpi_filter_options": kpi_filter_options.id, "latest": latest.id, "mart": mart.id, "opportunities": opportunities.id, "opportunities_latest": opportunities_latest.id, "gap_periodic": gap_periodic.id}, "chart_count": len(charts)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
