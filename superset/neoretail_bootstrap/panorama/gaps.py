"""Panorama gaps: existing certified contracts and chart composition."""
from __future__ import annotations

from neoretail_bootstrap.core.metrics import metric
from neoretail_bootstrap.core.chart_params import custom_params
from neoretail_bootstrap.core.filters import _jinja_filter_predicates
from .filters import WEEKLY_FILTER_COLUMNS


GAP_TVD = metric("TVD", "SUM(COALESCE(tvd, 0))")


GAP_IVD = metric("IVD", "SUM(COALESCE(ivd, 0))")


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


def register_gap_charts(add, gap_monthly, gap_weekly_card):
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
