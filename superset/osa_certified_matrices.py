"""Period-aware OSA matrix semantics extracted from the Power BI queries."""
from bootstrap_overview import _jinja_filter_predicates
from bootstrap_panorama import WEEKLY_FILTER_COLUMNS, formatted_metric


MATRIX_SCOPES = {
    "region": ("Região", "regiao"),
    "retail": ("Varejo", "rede"),
    "item": ("Hierarquia de item", "hierarquia_1"),
}

DIMENSION_OVERRIDES = {
    "rede": "l.rede", "bandeira": "l.bandeira", "uf": "l.uf",
    "cidade": "l.cidade", "tipo_local": "l.tipo_local",
    "loja": "l.loja", "regiao": "l.regiao",
    "item": "i.item", "descricao_marca": "i.descricao_marca",
    "hierarquia_1": "i.hierarquia_1", "hierarquia_2": "i.hierarquia_2",
    "hierarquia_3": "i.hierarquia_3",
}


def _measure_filter() -> str:
    return """
{% set measure_filters = get_filters('nm_measure', remove_filter=True) %}
{% if measure_filters|length == 0 %}
  AND m.nm_measure='unidade'
{% else %}
  {% for filter in measure_filters %}
    {% if filter.get('op') == 'IN' %}
      AND m.nm_measure IN {{ filter.get('val') | where_in }}
    {% elif filter.get('op') == 'NOT IN' %}
      AND m.nm_measure NOT IN {{ filter.get('val') | where_in }}
    {% endif %}
  {% endfor %}
{% endif %}
""".strip()


def _period_rows(alias: str, latest_alias: str) -> str:
    return f"""
    SELECT 'MTD'::text,1::int
      WHERE DATE_TRUNC('month',{alias}.data)=DATE_TRUNC('month',{latest_alias}.latest_data)
    UNION ALL
    SELECT 'Mês Anterior',2
      WHERE DATE_TRUNC('month',{alias}.data)=DATE_TRUNC('month',{latest_alias}.latest_data-INTERVAL '1 month')
    UNION ALL
    SELECT 'U3M',3
      WHERE {alias}.data>=DATE_TRUNC('month',{latest_alias}.latest_data)-INTERVAL '2 months'
        AND {alias}.data<={latest_alias}.latest_data
    UNION ALL
    SELECT 'YTD',5
      WHERE EXTRACT(YEAR FROM {alias}.data)=EXTRACT(YEAR FROM {latest_alias}.latest_data)
""".strip()


def matrix_period_sql(group_column: str) -> str:
    """Power BI matrix: value loss from monthly OSA; other metrics from history."""
    if group_column not in {"regiao", "rede", "hierarquia_1"}:
        raise ValueError(f"Unsupported OSA matrix dimension: {group_column}")

    history_predicates = _jinja_filter_predicates(
        "h", "tp_activity_level", DIMENSION_OVERRIDES,
    )
    cause_overrides = {
        **DIMENSION_OVERRIDES,
        "tp_activity_level": "o.max_tp_activity_level",
    }
    cause_predicates = _jinja_filter_predicates(
        "c", "o.max_tp_activity_level", cause_overrides,
    )
    group_expr = (
        f"l.{group_column}" if group_column in {"regiao", "rede"}
        else f"i.{group_column}"
    )
    output_dims = ",".join(
        f"h.{column}" if column == group_column else f"NULL::text AS {column}"
        for column in WEEKLY_FILTER_COLUMNS
    )
    measure_filter = _measure_filter()
    history_periods = _period_rows("b", "x")
    cause_periods = _period_rows("b", "x")

    return f"""
WITH latest AS (
  SELECT id_customer,MAX(mes_ano)::date AS latest_data
  FROM gold.fato_historico
  GROUP BY id_customer
), measures AS (
  SELECT DISTINCT id_customer,nm_measure
  FROM gold.nr_conversion_options m
  WHERE 1=1
{measure_filter}
), history_base AS (
  SELECT
    h.mes_ano::date AS data,h.id_customer,h.id_item,
    {group_expr}::text AS {group_column},
    h.qtd_perda_osa,h.qtd_problemas_osa,h.qtd_item_ativo_osa
  FROM gold.fato_historico h
  LEFT JOIN gold.dim_local l
    ON l.id_customer=h.id_customer AND l.id_location=h.id_location
  LEFT JOIN gold.dim_itens i
    ON i.id_customer=h.id_customer AND i.id_item=h.id_item
  WHERE 1=1
{history_predicates}
), history_period AS (
  SELECT b.*,p.osa_period,p.osa_period_order
  FROM history_base b
  JOIN latest x USING(id_customer)
  CROSS JOIN LATERAL (
{history_periods}
  ) AS p(osa_period,osa_period_order)
), history_agg AS (
  SELECT
    p.id_customer,p.osa_period,p.osa_period_order,p.{group_column},
    m.nm_measure,
    SUM(COALESCE(p.qtd_perda_osa,0))::float8 AS loss_base,
    SUM(COALESCE(p.qtd_problemas_osa,0))::float8 AS problem_base,
    SUM(COALESCE(p.qtd_item_ativo_osa,0))::float8 AS active_base,
    COALESCE(MAX(cv.conversion_rate),
      CASE WHEN m.nm_measure='valor' THEN 1.0 END)::float8 AS conversion_factor
  FROM history_period p
  JOIN measures m ON m.id_customer=p.id_customer
  LEFT JOIN gold.dim_conversao cv
    ON cv.id_customer=p.id_customer
   AND cv.id_item::text=p.id_item::text
   AND cv.nm_measure=m.nm_measure
  GROUP BY p.id_customer,p.osa_period,p.osa_period_order,p.{group_column},m.nm_measure
), cause_base AS (
  SELECT
    c.data,c.id_customer,c.id_item,
    {group_expr}::text AS {group_column},
    c.vl_perda_osa
  FROM gold.fato_mensal_causa_osa c
  LEFT JOIN gold.dim_local l
    ON l.id_customer=c.id_customer AND l.id_location=c.id_location
  LEFT JOIN gold.dim_itens i
    ON i.id_customer=c.id_customer AND i.id_item=c.id_item
  LEFT JOIN gold.calculo_oportunidades o
    ON o.id_customer=c.id_customer
   AND o.id_location::text=c.id_location::text
   AND o.id_item::text=c.id_item::text
  WHERE 1=1
{cause_predicates}
), cause_period AS (
  SELECT b.*,p.osa_period,p.osa_period_order
  FROM cause_base b
  JOIN latest x USING(id_customer)
  CROSS JOIN LATERAL (
{cause_periods}
  ) AS p(osa_period,osa_period_order)
), cause_agg AS (
  SELECT id_customer,osa_period,osa_period_order,{group_column},
         SUM(COALESCE(vl_perda_osa,0))::float8 AS loss_value
  FROM cause_period
  GROUP BY id_customer,osa_period,osa_period_order,{group_column}
)
SELECT
  h.id_customer,h.nm_measure,h.osa_period,h.osa_period_order,
  {output_dims},
  c.loss_value,
  (h.loss_base*h.conversion_factor)::float8 AS loss_qty,
  (h.problem_base*h.conversion_factor)::float8 AS problem_qty,
  h.problem_base,h.active_base
FROM history_agg h
LEFT JOIN cause_agg c
  ON c.id_customer=h.id_customer
 AND c.osa_period=h.osa_period
 AND c.{group_column} IS NOT DISTINCT FROM h.{group_column}
""".strip()


TABLE_VALUE = formatted_metric("Perda R$ OSA", "SUM(loss_value)", "$,.2f")
TABLE_QTY = formatted_metric("Perda OSA qtd", "SUM(loss_qty)", ",.2f")
TABLE_PROBLEMS = formatted_metric("Qtd Problema OSA", "SUM(problem_qty)", ",.2f")
TABLE_OSA = formatted_metric(
    "% OSA", "1 - SUM(problem_base)/NULLIF(SUM(active_base),0)", ".2%",
)
