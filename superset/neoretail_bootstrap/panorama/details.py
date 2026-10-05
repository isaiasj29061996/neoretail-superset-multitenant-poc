"""Panorama details: existing certified contracts and chart composition."""
from __future__ import annotations

from neoretail_bootstrap.core.metrics import formatted_metric
from neoretail_bootstrap.core.chart_params import table_params
from neoretail_bootstrap.core.filters import _jinja_filter_predicates
from .filters import WEEKLY_FILTER_COLUMNS


DETAIL_DIMENSIONS = ("regiao", "rede", "hierarquia_1", "item", "activity_level")


def detail_semantic_sql(group_column: str) -> str:
    """Power BI-compatible latest snapshot + rolling ROI detail table.

    The default/unfiltered path comes from a compact materialized mart created
    during the serving refresh.  Cross-dimension filters fall back to the
    detailed history mart so filters are still applied before aggregation.
    ROI anual remains the DAX SUMX of monthly ROI values, not current ROI * 12.
    """
    if group_column not in DETAIL_DIMENSIONS:
        raise ValueError(f"Unsupported detail dimension: {group_column}")

    predicates = _jinja_filter_predicates("h")
    projection = ",\n  ".join(
        (
            f"c.{column}"
            if column == group_column
            else f"NULL::text AS {column}"
        )
        for column in WEEKLY_FILTER_COLUMNS
    )
    default_projection = ",\n  ".join(
        (
            f"d.dimension_value AS {column}"
            if column == group_column
            else f"NULL::text AS {column}"
        )
        for column in WEEKLY_FILTER_COLUMNS
    )
    cross_filter_checks = " or ".join(
        f"get_filters('{column}')"
        for column in WEEKLY_FILTER_COLUMNS
        if column != group_column
    )
    return f"""
{{% set has_detail_filter = {cross_filter_checks} %}}
{{% if not has_detail_filter %}}
SELECT
  d.id_customer,
  {default_projection},
  d.nm_measure,
  d.sales_qty_value,
  d.sellout_value,
  d.sales_cost_value,
  d.markup_value,
  d.price_value,
  d.stock_cost_value,
  d.stock_qty_value,
  d.roi_value,
  d.roi_annual_value,
  d.giro_value,
  d.osa_value,
  d.rupture_value,
  d.isv_value,
  d.osa_loss_value
FROM gold.nr_panorama_detail_default d
WHERE d.detail_scope='{group_column}'
{{% else %}}
{{% set measure_filters = get_filters('nm_measure', remove_filter=True) %}}
WITH customer_latest AS (
  SELECT id_customer, MAX(data)::date AS latest_data
  FROM gold.nr_panorama_comparison_history_detail
  GROUP BY id_customer
), raw AS (
  SELECT
    h.data::date AS data,
    h.id_customer,
    h.id_item::text AS id_item,
    h.volume_unidades,
    h.faturamento,
    h.estoque_unidades,
    h.qtd_perda_osa,
    h.rup,
    h.est_virtual,
    h.giro,
    h.qtd_problemas_osa,
    h.qtd_item_ativo_osa,
    h.status_item_geral,
    h.avg_sales_price,
    h.avg_price_cost,
    h.estoque_medio,
    h.tp_activity_level,
    CASE h.tp_activity_level
      WHEN 'F' THEN 'Fast Mover'
      WHEN 'S' THEN 'Slow Mover'
      WHEN 'US' THEN 'Ultra Slow Mover'
      WHEN 'U' THEN 'Ultra Slow Mover'
      WHEN 'N' THEN 'New Mover'
      ELSE COALESCE(h.tp_activity_level, 'Outros')
    END::text AS activity_level,
    h.rede,h.bandeira,h.uf,h.cidade,h.tipo_local,h.loja,h.regiao,
    h.item,h.descricao_marca,h.hierarquia_1,h.hierarquia_2,h.hierarquia_3
  FROM gold.nr_panorama_comparison_history_detail h
  JOIN customer_latest d
    ON d.id_customer=h.id_customer
   AND h.data::date > d.latest_data - INTERVAL '12 months'
   AND h.data::date <= d.latest_data
), history_filtered AS (
  SELECT h.*
  FROM raw h
  WHERE 1=1
{predicates}
  {{% for filter in get_filters('activity_level', remove_filter=True) %}}
  {{% if filter.get('op') == 'IN' %}}
    AND h.activity_level IN {{{{ filter.get('val') | where_in }}}}
  {{% elif filter.get('op') == 'NOT IN' %}}
    AND h.activity_level NOT IN {{{{ filter.get('val') | where_in }}}}
  {{% endif %}}
  {{% endfor %}}
), measures AS (
  SELECT DISTINCT id_customer,nm_measure
  FROM gold.nr_conversion_options
  WHERE 1=1
  {{% if measure_filters|length == 0 %}}
    AND nm_measure='unidade'
  {{% else %}}
    {{% for filter in measure_filters %}}
    {{% if filter.get('op') == 'IN' %}}
      AND nm_measure IN {{{{ filter.get('val') | where_in }}}}
    {{% elif filter.get('op') == 'NOT IN' %}}
      AND nm_measure NOT IN {{{{ filter.get('val') | where_in }}}}
    {{% endif %}}
    {{% endfor %}}
  {{% endif %}}
), factors AS (
  SELECT
    x.id_customer,x.{group_column},m.nm_measure,
    COALESCE(MAX(c.conversion_rate), CASE WHEN m.nm_measure='valor' THEN 1.0 END)::float8 AS conversion_factor
  FROM (
    SELECT DISTINCT id_customer,{group_column},id_item
    FROM history_filtered
  ) x
  JOIN measures m ON m.id_customer=x.id_customer
  LEFT JOIN gold.dim_conversao c
    ON c.id_customer=x.id_customer
   AND c.id_item::text=x.id_item
   AND c.nm_measure=m.nm_measure
  GROUP BY x.id_customer,x.{group_column},m.nm_measure
), monthly AS (
  SELECT
    h.data,h.id_customer,h.{group_column},f.nm_measure,
    MAX(f.conversion_factor)::float8 AS conversion_factor,
    SUM(COALESCE(h.faturamento,0))::float8 AS faturamento_sum,
    SUM(COALESCE(h.volume_unidades,0))::float8 AS volume_sum,
    SUM(COALESCE(h.volume_unidades,0)*COALESCE(h.avg_price_cost,0))::float8 AS sales_cost_sum,
    SUM(COALESCE(h.estoque_medio,0)*COALESCE(h.avg_price_cost,0))::float8 AS stock_cost_sum,
    SUM(COALESCE(h.estoque_unidades,0))::float8 AS stock_units_sum,
    SUM(COALESCE(h.qtd_perda_osa,0))::float8 AS loss_qty_sum,
    SUM(COALESCE(h.avg_sales_price,0)) FILTER (WHERE h.faturamento>0)::float8 AS price_sum,
    COUNT(h.avg_sales_price) FILTER (WHERE h.faturamento>0)::bigint AS price_count,
    SUM(COALESCE(h.giro,0)) FILTER (WHERE h.giro>0)::float8 AS giro_sum,
    COUNT(h.giro) FILTER (WHERE h.giro>0)::bigint AS giro_count,
    SUM(COALESCE(h.qtd_problemas_osa,0))::float8 AS osa_problem_sum,
    SUM(COALESCE(h.qtd_item_ativo_osa,0))::float8 AS osa_active_sum,
    SUM(COALESCE(h.rup,0))::float8 AS rupture_sum,
    SUM(COALESCE(h.status_item_geral,0))::float8 AS status_sum,
    SUM(COALESCE(h.est_virtual,0))::float8 AS isv_sum
  FROM history_filtered h
  JOIN factors f
    ON f.id_customer=h.id_customer
   AND f.{group_column} IS NOT DISTINCT FROM h.{group_column}
  GROUP BY h.data,h.id_customer,h.{group_column},f.nm_measure
), calculated AS (
  SELECT
    m.*,
    CASE
      WHEN m.faturamento_sum>0 THEN m.faturamento_sum
      WHEN m.conversion_factor IS NOT NULL AND m.price_count>0
      THEN (m.volume_sum*m.conversion_factor)
         * ((m.price_sum/m.price_count)*m.conversion_factor)
      ELSE NULL
    END::float8 AS sellout_value,
    CASE
      WHEN m.nm_measure='valor' THEN m.faturamento_sum
      WHEN m.conversion_factor IS NULL THEN NULL
      ELSE m.volume_sum*m.conversion_factor
    END::float8 AS sales_qty_value,
    CASE WHEN m.conversion_factor IS NULL OR m.price_count=0 THEN NULL
         ELSE (m.price_sum/m.price_count)*m.conversion_factor END::float8 AS price_value,
    CASE WHEN m.conversion_factor IS NULL THEN NULL
         ELSE m.stock_units_sum*m.conversion_factor END::float8 AS stock_qty_value,
    CASE WHEN m.conversion_factor IS NULL THEN NULL
         ELSE m.loss_qty_sum*m.conversion_factor END::float8 AS osa_loss_value
  FROM monthly m
), with_ratios AS (
  SELECT
    c.*,
    CASE WHEN c.sellout_value IS NULL OR c.sales_cost_sum=0 THEN 0
         ELSE c.sellout_value/c.sales_cost_sum END::float8 AS markup_value,
    CASE WHEN c.sellout_value IS NULL OR c.sales_cost_sum=0 THEN 0
         ELSE (c.sellout_value-c.sales_cost_sum)/NULLIF(c.stock_cost_sum,0) END::float8 AS roi_value,
    (c.giro_sum/NULLIF(c.giro_count,0))::float8 AS giro_value,
    (1-c.osa_problem_sum/NULLIF(c.osa_active_sum,0))::float8 AS osa_value,
    (c.rupture_sum/NULLIF(c.status_sum,0))::float8 AS rupture_value,
    (c.isv_sum/NULLIF(c.status_sum,0))::float8 AS isv_value
  FROM calculated c
), latest AS (
  SELECT id_customer,nm_measure,MAX(data) AS latest_data
  FROM with_ratios
  GROUP BY id_customer,nm_measure
), annual AS (
  SELECT
    r.id_customer,r.{group_column},r.nm_measure,
    SUM(r.roi_value) FILTER (
      WHERE r.data > l.latest_data - INTERVAL '12 months'
        AND r.data <= l.latest_data
    )::float8 AS roi_annual_value
  FROM with_ratios r
  JOIN latest l USING (id_customer,nm_measure)
  GROUP BY r.id_customer,r.{group_column},r.nm_measure
), current_rows AS (
  SELECT r.*
  FROM with_ratios r
  JOIN latest l USING (id_customer,nm_measure)
  WHERE r.data=l.latest_data
)
SELECT
  c.id_customer,
  {projection},
  c.nm_measure,
  c.sales_qty_value,
  c.sellout_value,
  c.sales_cost_sum AS sales_cost_value,
  c.markup_value,
  c.price_value,
  c.stock_cost_sum AS stock_cost_value,
  c.stock_qty_value,
  c.roi_value,
  a.roi_annual_value,
  c.giro_value,
  c.osa_value,
  c.rupture_value,
  c.isv_value,
  c.osa_loss_value
FROM current_rows c
LEFT JOIN annual a
  ON a.id_customer=c.id_customer
 AND a.{group_column} IS NOT DISTINCT FROM c.{group_column}
 AND a.nm_measure=c.nm_measure
{{% endif %}}
""".strip()


DETAIL_METRICS = [
    formatted_metric("Venda qtd", "MAX(sales_qty_value)", ",.2f"),
    formatted_metric("Venda sell out", "MAX(sellout_value)", "$,.2f"),
    formatted_metric("Venda custo", "MAX(sales_cost_value)", "$,.2f"),
    formatted_metric("Markup", "MAX(markup_value)", ".2%"),
    formatted_metric("Preço médio", "MAX(price_value)", "$,.2f"),
    formatted_metric("Estoque custo", "MAX(stock_cost_value)", "$,.2f"),
    formatted_metric("Estoque qtd", "MAX(stock_qty_value)", ",.2f"),
    formatted_metric("ROI", "MAX(roi_value)", ".2%"),
    formatted_metric("ROI anual", "MAX(roi_annual_value)", ".2%"),
    formatted_metric("Giro", "MAX(giro_value)", ",.2f"),
    formatted_metric("OSA", "MAX(osa_value)", ".2%"),
    formatted_metric("Ruptura", "MAX(rupture_value)", ".2%"),
    formatted_metric("Item sem venda", "MAX(isv_value)", ".2%"),
    formatted_metric("Perda OSA", "MAX(osa_loss_value)", ",.2f"),
]


def detail_table_params(dataset, groupby, page_length=20):
    params = table_params(dataset, groupby, DETAIL_METRICS, page_length)
    params["column_config"] = {
        "Markup": {"d3NumberFormat": ".2%"},
        "ROI": {"d3NumberFormat": ".2%"},
        "ROI anual": {"d3NumberFormat": ".2%"},
        "OSA": {"d3NumberFormat": ".2%"},
        "Ruptura": {"d3NumberFormat": ".2%"},
        "Item sem venda": {"d3NumberFormat": ".2%"},
        "Venda sell out": {"d3NumberFormat": "$,.2f"},
        "Venda custo": {"d3NumberFormat": "$,.2f"},
        "Preço médio": {"d3NumberFormat": "$,.2f"},
        "Estoque custo": {"d3NumberFormat": "$,.2f"},
    }
    return params


def register_detail_charts(add, detail_datasets):
    detail_dims = (("regiao", "Região"), ("rede", "Rede"), ("hierarquia_1", "Categoria"), ("item", "Produto"), ("activity_level", "Nível de atividade"))
    for column, label in detail_dims:
        detail_dataset = detail_datasets[column]
        add(
            f"detail_{column}",
            detail_dataset,
            f"Análise detalhada — {label}",
            detail_table_params(detail_dataset, column, 20),
            "table",
        )
    return detail_dims
