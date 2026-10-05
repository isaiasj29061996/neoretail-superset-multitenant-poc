"""Panorama kpis: existing certified contracts and chart composition."""
from __future__ import annotations

import json
from neoretail_bootstrap.core.metrics import metric, formatted_metric
from neoretail_bootstrap.core.chart_params import custom_params
from neoretail_bootstrap.core.filters import _jinja_filter_predicates
from .filters import WEEKLY_FILTER_COLUMNS, KPI_ORDER_METRIC_NAME, KPI_MONTH_ORDER_METRIC_NAME


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


KPI_DIMENSION_VALUE = formatted_metric("KPI valor", "MAX(kpi_value)", ",.2f")


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


def register_kpi_charts(add, kpi_filter_options, kpi_dimensions):
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
    return kpi_dimension_labels


def ensure_order_metrics(session, SqlMetric, kpi_filter_options):
    kpi_order_metric = session.query(SqlMetric).filter(
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
        session.add(kpi_order_metric)
    else:
        kpi_order_metric.expression = "MIN(kpi_order)"
        kpi_order_metric.metric_type = "MIN"
        kpi_order_metric.d3format = ",d"
    month_order_metric = session.query(SqlMetric).filter(
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
        session.add(month_order_metric)
    else:
        month_order_metric.expression = "MIN(comparison_year_month_sort)"
        month_order_metric.metric_type = "MIN"
        month_order_metric.d3format = ",d"
