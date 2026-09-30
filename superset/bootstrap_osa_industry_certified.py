"""Build the isolated Power BI-aligned OSA Industry dashboard.

This dashboard intentionally lives beside the legacy OSA dashboard while the
new semantics are certified.  It does not mutate the legacy dashboard.

Power BI contracts reproduced here:
* monthly value: sellout, exact VL_PERDA_OSA, % loss, % OSA;
* monthly quantity: converted volume/loss, % loss, % OSA;
* weekly value/quantity counterparts;
* MTD/M-1/U3M/current-year loss-by-motive/cause views;
* three hierarchical matrices (region, retail, item hierarchy);
* tenant RLS through id_customer on every virtual dataset.
"""
from __future__ import annotations

import json

from superset.app import create_app

from bootstrap_overview import (
    _jinja_filter_predicates,
    metric,
    overview_native_filters,
    upsert_dataset,
)
from bootstrap_panorama import (
    Layout,
    WEEKLY_FILTER_COLUMNS,
    comparison_pivot_params,
    custom_params,
    formatted_metric,
    upsert_chart,
)
from osa_certified_matrices import (
    MATRIX_SCOPES,
    TABLE_OSA as MATRIX_OSA,
    TABLE_PROBLEMS as MATRIX_PROBLEMS,
    TABLE_QTY as MATRIX_QTY,
    TABLE_VALUE as MATRIX_VALUE,
    matrix_period_sql,
)


DASHBOARD_TITLE = "NeoRetail V9 — OSA Indústria — Certificada"
DASHBOARD_SLUG = "neoretail-v9-osa-industria-certified"
PREFIX = "[OSA Certificada]"

PERIODS = (
    ("MTD", 1),
    ("Mês Anterior", 2),
    ("U3M", 3),
    ("YTD", 5),
)

DIMENSION_OVERRIDES = {
    "rede": "l.rede",
    "bandeira": "l.bandeira",
    "uf": "l.uf",
    "cidade": "l.cidade",
    "tipo_local": "l.tipo_local",
    "loja": "l.loja",
    "regiao": "l.regiao",
    "item": "i.item",
    "descricao_marca": "i.descricao_marca",
    "hierarquia_1": "i.hierarquia_1",
    "hierarquia_2": "i.hierarquia_2",
    "hierarquia_3": "i.hierarquia_3",
}


def _dimension_nulls() -> str:
    return ",".join(f"NULL::text AS {column}" for column in WEEKLY_FILTER_COLUMNS)


def _measure_filter(alias: str = "o") -> str:
    return f"""
{{% set measure_filters = get_filters('nm_measure', remove_filter=True) %}}
{{% if measure_filters|length == 0 %}}
  AND {alias}.nm_measure='unidade'
{{% else %}}
  {{% for filter in measure_filters %}}
    {{% if filter.get('op') == 'IN' %}}
      AND {alias}.nm_measure IN {{{{ filter.get('val') | where_in }}}}
    {{% elif filter.get('op') == 'NOT IN' %}}
      AND {alias}.nm_measure NOT IN {{{{ filter.get('val') | where_in }}}}
    {{% endif %}}
  {{% endfor %}}
{{% endif %}}
""".strip()


def monthly_overview_sql() -> str:
    """Monthly OSA timeline using the exact Power BI fact families."""
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
    dims = _dimension_nulls()
    measure_filter = _measure_filter("m")
    return f"""
WITH history_filtered AS (
  SELECT
    h.mes_ano::date AS data,h.id_customer,h.id_item,h.id_location,
    h.volume_unidades,h.faturamento,h.qtd_perda_osa,
    h.qtd_problemas_osa,h.qtd_item_ativo_osa,h.avg_sales_price,
    h.tp_activity_level
  FROM gold.fato_historico h
  LEFT JOIN gold.dim_local l
    ON l.id_customer=h.id_customer AND l.id_location=h.id_location
  LEFT JOIN gold.dim_itens i
    ON i.id_customer=h.id_customer AND i.id_item=h.id_item
  WHERE 1=1
{history_predicates}
), cause_filtered AS (
  SELECT
    c.data,c.id_customer,c.id_item,c.id_location,
    c.qtd_perda_osa,c.vl_perda_osa,c.qtd_problemas_osa,
    c.qtd_itens_ativos,c.volume_unidades,c.faturamento,c.preco_medio
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
), measures AS (
  SELECT DISTINCT id_customer,nm_measure
  FROM gold.nr_conversion_options m
  WHERE 1=1
{measure_filter}
), hist_month AS (
  SELECT
    h.data,h.id_customer,
    SUM(COALESCE(h.faturamento,0))::float8 AS faturamento_sum,
    SUM(COALESCE(h.volume_unidades,0))::float8 AS volume_sum,
    SUM(COALESCE(h.qtd_perda_osa,0))::float8 AS loss_qty_sum,
    SUM(COALESCE(h.qtd_problemas_osa,0))::float8 AS problem_sum,
    SUM(COALESCE(h.qtd_item_ativo_osa,0))::float8 AS active_sum,
    SUM(h.avg_sales_price)::float8 AS sales_price_sum,
    COUNT(h.avg_sales_price)::bigint AS sales_price_count
  FROM history_filtered h
  GROUP BY h.data,h.id_customer
), cause_month AS (
  SELECT
    c.data,c.id_customer,
    SUM(COALESCE(c.qtd_perda_osa,0))::float8 AS loss_qty_sum,
    SUM(COALESCE(c.vl_perda_osa,0))::float8 AS loss_value_sum,
    SUM(COALESCE(c.qtd_problemas_osa,0))::float8 AS problem_sum,
    SUM(COALESCE(c.qtd_itens_ativos,0))::float8 AS active_sum,
    SUM(COALESCE(c.volume_unidades,0))::float8 AS volume_sum,
    SUM(COALESCE(c.faturamento,0))::float8 AS faturamento_sum,
    SUM(COALESCE(c.preco_medio,0))::float8 AS price_sum
  FROM cause_filtered c
  GROUP BY c.data,c.id_customer
), hist_factor AS (
  SELECT
    h.data,h.id_customer,m.nm_measure,
    COALESCE(MAX(cv.conversion_rate),
      CASE WHEN m.nm_measure='valor' THEN 1.0 END)::float8 AS conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM history_filtered) h
  JOIN measures m ON m.id_customer=h.id_customer
  LEFT JOIN gold.dim_conversao cv
    ON cv.id_customer=h.id_customer
   AND cv.id_item::text=h.id_item::text
   AND cv.nm_measure=m.nm_measure
  GROUP BY h.data,h.id_customer,m.nm_measure
), cause_factor AS (
  SELECT
    c.data,c.id_customer,m.nm_measure,
    COALESCE(MAX(cv.conversion_rate),
      CASE WHEN m.nm_measure='valor' THEN 1.0 END)::float8 AS conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM cause_filtered) c
  JOIN measures m ON m.id_customer=c.id_customer
  LEFT JOIN gold.dim_conversao cv
    ON cv.id_customer=c.id_customer
   AND cv.id_item::text=c.id_item::text
   AND cv.nm_measure=m.nm_measure
  GROUP BY c.data,c.id_customer,m.nm_measure
)
SELECT
  h.data,h.id_customer,hf.nm_measure,
  CASE
    WHEN h.faturamento_sum>0 THEN h.faturamento_sum
    WHEN hf.conversion_factor IS NOT NULL AND h.sales_price_count>0
      THEN (h.volume_sum*hf.conversion_factor)
         *((h.sales_price_sum/h.sales_price_count)*hf.conversion_factor)
    ELSE NULL
  END::float8 AS sellout_value,
  c.loss_value_sum::float8 AS loss_value,
  CASE
    WHEN c.faturamento_sum>0
      THEN 100.0*c.loss_value_sum/NULLIF(c.faturamento_sum,0)
    ELSE 100.0*c.loss_value_sum
      / NULLIF(c.volume_sum*c.price_sum,0)
  END::float8 AS loss_value_percent,
  (100.0*(1-h.problem_sum/NULLIF(h.active_sum,0)))::float8 AS osa_percent,
  (c.volume_sum*cf.conversion_factor)::float8 AS sales_qty,
  (c.loss_qty_sum*cf.conversion_factor)::float8 AS loss_qty,
  CASE
    WHEN hf.conversion_factor IS NULL THEN NULL
    ELSE 100.0*(h.loss_qty_sum*hf.conversion_factor)
      / NULLIF(h.volume_sum*hf.conversion_factor,0)
  END::float8 AS loss_qty_percent,
  {dims}
FROM hist_month h
JOIN hist_factor hf USING(data,id_customer)
LEFT JOIN cause_month c USING(data,id_customer)
LEFT JOIN cause_factor cf
  ON cf.data=h.data AND cf.id_customer=h.id_customer
 AND cf.nm_measure=hf.nm_measure
""".strip()


def weekly_overview_sql() -> str:
    """Weekly OSA timeline; the latest 13 filtered CD_WEEK values are returned."""
    weekly_overrides = {
        **DIMENSION_OVERRIDES,
        "tp_activity_level": "o.max_tp_activity_level",
    }
    weekly_predicates = _jinja_filter_predicates(
        "w", "o.max_tp_activity_level", weekly_overrides,
    )
    opportunity_overrides = {
        **DIMENSION_OVERRIDES,
        "tp_activity_level": "o.max_tp_activity_level",
    }
    opportunity_predicates = _jinja_filter_predicates(
        "o", "o.max_tp_activity_level", opportunity_overrides,
    )
    dims = _dimension_nulls()
    measure_filter = _measure_filter("m")
    return f"""
WITH weekly_filtered AS (
  SELECT
    w.id_time::date AS data,w.cd_week,w.id_customer,w.id_item,w.id_location,
    w.volume_unidade,w.faturamento,w.qtd_perda_osa,w.qtd_problemas_osa,
    w.qtd_item_ativo_osa,w.avg_sales_price,w.avg_price_cost
  FROM gold.fato_semanal w
  LEFT JOIN gold.dim_local l
    ON l.id_customer=w.id_customer AND l.id_location=w.id_location
  LEFT JOIN gold.dim_itens i
    ON i.id_customer=w.id_customer AND i.id_item=w.id_item
  LEFT JOIN gold.calculo_oportunidades o
    ON o.id_customer=w.id_customer
   AND o.id_location::text=w.id_location::text
   AND o.id_item::text=w.id_item::text
  WHERE 1=1
{weekly_predicates}
), ranked_weeks AS (
  SELECT id_customer,cd_week,MAX(data) AS data,
    DENSE_RANK() OVER (
      PARTITION BY id_customer ORDER BY cd_week DESC
    ) AS week_rank
  FROM weekly_filtered
  GROUP BY id_customer,cd_week
), scoped AS (
  SELECT w.*
  FROM weekly_filtered w
  JOIN ranked_weeks r USING(id_customer,cd_week)
  WHERE r.week_rank<=13
), opportunities_filtered AS (
  SELECT o.id_customer,o.id_item,o.id_location,o.demanda_media
  FROM gold.calculo_oportunidades o
  LEFT JOIN gold.dim_local l
    ON l.id_customer=o.id_customer AND l.id_location=o.id_location
  LEFT JOIN gold.dim_itens i
    ON i.id_customer=o.id_customer AND i.id_item=o.id_item
  WHERE COALESCE(o.qtd_item_ativo_osa_m0,0)>0
{opportunity_predicates}
), measures AS (
  SELECT DISTINCT id_customer,nm_measure
  FROM gold.nr_conversion_options m
  WHERE 1=1
{measure_filter}
), weekly AS (
  SELECT
    s.data,s.cd_week,s.id_customer,
    SUM(COALESCE(s.faturamento,0))::float8 AS faturamento_sum,
    SUM(COALESCE(s.volume_unidade,0))::float8 AS volume_sum,
    SUM(COALESCE(s.qtd_perda_osa,0))::float8 AS loss_qty_sum,
    SUM(COALESCE(s.qtd_problemas_osa,0))::float8 AS problem_sum,
    SUM(COALESCE(s.qtd_item_ativo_osa,0))::float8 AS active_sum,
    AVG(s.avg_sales_price)::float8 AS avg_sales_price,
    AVG(s.avg_price_cost)::float8 AS avg_price_cost
  FROM scoped s
  GROUP BY s.data,s.cd_week,s.id_customer
), factor AS (
  SELECT
    s.data,s.id_customer,m.nm_measure,
    COALESCE(MAX(cv.conversion_rate),
      CASE WHEN m.nm_measure='valor' THEN 1.0 END)::float8 AS conversion_factor
  FROM (SELECT DISTINCT data,id_customer,id_item FROM scoped) s
  JOIN measures m ON m.id_customer=s.id_customer
  LEFT JOIN gold.dim_conversao cv
    ON cv.id_customer=s.id_customer
   AND cv.id_item::text=s.id_item::text
   AND cv.nm_measure=m.nm_measure
  GROUP BY s.data,s.id_customer,m.nm_measure
), demand AS (
  SELECT id_customer,SUM(COALESCE(demanda_media,0))::float8 AS demand_sum
  FROM opportunities_filtered
  GROUP BY id_customer
)
SELECT
  w.data,w.cd_week,w.id_customer,f.nm_measure,
  CASE
    WHEN w.faturamento_sum>0 THEN w.faturamento_sum
    WHEN f.conversion_factor IS NOT NULL AND w.avg_sales_price IS NOT NULL
      THEN (w.volume_sum*f.conversion_factor)
         *(w.avg_sales_price*f.conversion_factor)
    ELSE NULL
  END::float8 AS sellout_value,
  (w.loss_qty_sum*w.avg_price_cost)::float8 AS loss_value,
  CASE
    WHEN w.faturamento_sum>0
      THEN 100.0*(w.loss_qty_sum*w.avg_price_cost)
        / NULLIF(w.faturamento_sum,0)
    ELSE 100.0*(w.loss_qty_sum*w.avg_price_cost)
      / NULLIF(w.volume_sum*w.avg_price_cost,0)
  END::float8 AS loss_value_percent,
  (100.0*(1-w.problem_sum/NULLIF(w.active_sum,0)))::float8 AS osa_percent,
  (w.volume_sum*f.conversion_factor)::float8 AS sales_qty,
  (w.loss_qty_sum*f.conversion_factor)::float8 AS loss_qty,
  (100.0*w.loss_qty_sum/NULLIF(d.demand_sum*30.0,0))::float8 AS loss_qty_percent,
  {dims}
FROM weekly w
JOIN factor f USING(data,id_customer)
LEFT JOIN demand d USING(id_customer)
ORDER BY w.data
""".strip()


def cause_period_sql() -> str:
    """Monthly cause rows expanded into the Power BI period selector contexts."""
    overrides = {
        **DIMENSION_OVERRIDES,
        "tp_activity_level": "o.max_tp_activity_level",
    }
    predicates = _jinja_filter_predicates(
        "c", "o.max_tp_activity_level", overrides,
    )
    measure_filter = _measure_filter("m")
    return f"""
WITH latest AS (
  SELECT id_customer,MAX(data)::date AS latest_data
  FROM gold.fato_mensal_causa_osa
  GROUP BY id_customer
), measures AS (
  SELECT DISTINCT id_customer,nm_measure
  FROM gold.nr_conversion_options m
  WHERE 1=1
{measure_filter}
), base AS (
  SELECT
    c.data,c.id_customer,c.id_item,c.id_location,
    c.motivo_osa,c.causa_osa,c.qtd_perda_osa,c.vl_perda_osa,
    c.qtd_problemas_osa,c.qtd_itens_ativos,c.volume_unidades,
    c.faturamento,c.preco_medio,
    l.rede,l.bandeira,l.uf,l.cidade,l.tipo_local,l.loja,l.regiao,
    i.item,i.descricao_marca,i.hierarquia_1,i.hierarquia_2,i.hierarquia_3,
    o.max_tp_activity_level::text AS tp_activity_level
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
{predicates}
), expanded AS (
  SELECT b.*,p.osa_period,p.osa_period_order
  FROM base b
  JOIN latest x USING(id_customer)
  CROSS JOIN LATERAL (
    SELECT 'MTD'::text AS osa_period,1::int AS osa_period_order
      WHERE DATE_TRUNC('month',b.data)=DATE_TRUNC('month',x.latest_data)
    UNION ALL
    SELECT 'Mês Anterior',2
      WHERE DATE_TRUNC('month',b.data)=DATE_TRUNC('month',x.latest_data-INTERVAL '1 month')
    UNION ALL
    SELECT 'U3M',3
      WHERE b.data>=DATE_TRUNC('month',x.latest_data)-INTERVAL '2 months'
        AND b.data<=x.latest_data
    UNION ALL
    SELECT 'YTD',5
      WHERE EXTRACT(YEAR FROM b.data)=EXTRACT(YEAR FROM x.latest_data)
  ) p
), converted AS (
  SELECT
    e.*,m.nm_measure,
    COALESCE(cv.conversion_rate,
      CASE WHEN m.nm_measure='valor' THEN 1.0 END)::float8 AS conversion_rate
  FROM expanded e
  JOIN measures m ON m.id_customer=e.id_customer
  LEFT JOIN gold.dim_conversao cv
    ON cv.id_customer=e.id_customer
   AND cv.id_item::text=e.id_item::text
   AND cv.nm_measure=m.nm_measure
)
SELECT * FROM converted
""".strip()


def period_options_sql() -> str:
    rows = ",".join(f"('{label}',{order})" for label,order in PERIODS)
    return f"""
SELECT c.id_customer,p.osa_period,p.osa_period_order
FROM (
  SELECT DISTINCT id_customer FROM gold.nr_filter_options
) c
CROSS JOIN (VALUES {rows}) AS p(osa_period,osa_period_order)
""".strip()


def _period_filter(period_dataset_id: int, excluded: list[int]) -> dict:
    return {
        "id": "NATIVE_FILTER-osa-certified-period",
        "controlValues": {
            "enableEmptyFilter": False,
            "defaultToFirstItem": False,
            "creatable": False,
            "multiSelect": False,
            "searchAllOptions": False,
            "inverseSelection": False,
            "sortAscending": True,
        },
        "name": "Período",
        "filterType": "filter_select",
        "targets": [{
            "datasetId": period_dataset_id,
            "column": {"name": "osa_period"},
        }],
        "defaultDataMask": {
            "extraFormData": {
                "filters": [{"col": "osa_period", "op": "IN", "val": ["Mês Anterior"]}],
            },
            "filterState": {"label": "Mês Anterior", "value": ["Mês Anterior"]},
            "ownState": {},
        },
        "cascadeParentIds": [],
        "scope": {"excluded": excluded, "rootPath": ["ROOT_ID"]},
        "type": "NATIVE_FILTER",
        "description": "MTD, Mês Anterior, U3M ou YTD. O padrão reproduz o estado observado no Power BI.",
    }


# Plugin values in percent format are 0..100.
TOP_VALUE_METRICS = [
    metric("Sell Out Venda", "SUM(sellout_value)"),
    metric("Perda R$ OSA", "SUM(loss_value)"),
    metric("% Perda", "AVG(loss_value_percent)"),
    metric("%OSA", "AVG(osa_percent)"),
]
TOP_QTY_METRICS = [
    metric("Venda qtd", "SUM(sales_qty)"),
    metric("Perda OSA qtd", "SUM(loss_qty)"),
    metric("% Perda", "AVG(loss_qty_percent)"),
    metric("%OSA", "AVG(osa_percent)"),
]

CAUSE_VALUE = metric("Perda R$ OSA", "SUM(vl_perda_osa)")
CAUSE_QTY = metric(
    "Perda OSA qtd",
    "SUM(qtd_perda_osa) * MAX(conversion_rate)",
)
TABLE_VALUE = formatted_metric(
    "Perda R$ OSA",
    "SUM(vl_perda_osa) * MAX(conversion_rate)",
    "$,.2f",
)
TABLE_QTY = formatted_metric(
    "Perda OSA qtd",
    "SUM(qtd_perda_osa) * MAX(conversion_rate)",
    ",.2f",
)
TABLE_PROBLEMS = formatted_metric(
    "Qtd Problema OSA",
    "SUM(qtd_problemas_osa) * MAX(conversion_rate)",
    ",.2f",
)
TABLE_OSA = formatted_metric(
    "% OSA",
    "1 - SUM(qtd_problemas_osa)/NULLIF(SUM(qtd_itens_ativos),0)",
    ".2%",
)


def _top_params(dataset, title: str, metrics: list[dict], *, weekly: bool, quantity: bool):
    params = custom_params(
        dataset,
        title,
        metrics,
        grain="P1D" if weekly else "P1M",
        styles="line|bar|line|line",
        formats=(
            "quantity|quantity|percent|percent"
            if quantity else
            "currency|currency|percent|percent"
        ),
        variant="panorama",
        row_limit=1000,
    )
    params.update({
        "summary_count": "4",
        "summary_labels": "U3M|U3M|U3M|U3M",
        "timeline_limit": "13" if weekly else "0",
    })
    return params


def _cause_params(dataset, title: str, metric_def: dict, groupby: str, fmt: str):
    return custom_params(
        dataset,
        title,
        [metric_def],
        groupby=[groupby],
        variant="verticalbars",
        formats=fmt,
        row_limit=20,
    )


def _matrix_params(dataset, rows: tuple[str, ...], metrics: list[dict]):
    params = comparison_pivot_params(dataset, rows, metrics)
    params["time_range"] = "No filter"
    params["row_limit"] = 10000
    return params


def main():
    app = create_app()
    with app.app_context():
        from superset import db
        from superset.connectors.sqla.models import SqlaTable
        from superset.models.core import Database
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice

        database = db.session.query(Database).filter(
            Database.database_name == "NeoRetail Gold - PostgreSQL Local"
        ).one()

        monthly = upsert_dataset(
            db.session,SqlaTable,database,"nr_osa_monthly_certified",
            sql=monthly_overview_sql(),
        )
        weekly = upsert_dataset(
            db.session,SqlaTable,database,"nr_osa_weekly_certified",
            sql=weekly_overview_sql(),
        )
        causes = upsert_dataset(
            db.session,SqlaTable,database,"nr_osa_causes_certified",
            sql=cause_period_sql(),
        )
        matrix_datasets = {
            key: upsert_dataset(
                db.session,SqlaTable,database,f"nr_osa_matrix_{key}_certified",
                sql=matrix_period_sql(group_column),
            )
            for key,(_,group_column) in MATRIX_SCOPES.items()
        }
        period_options = upsert_dataset(
            db.session,SqlaTable,database,"nr_osa_period_options",
            sql=period_options_sql(),
        )
        filter_options = upsert_dataset(
            db.session,SqlaTable,database,"nr_filter_options",
            table_name="nr_filter_options",
        )

        charts = {}
        def add(key, dataset, title, params, viz="neoretail-kpi-card"):
            charts[key] = upsert_chart(
                db.session,Slice,dataset,f"{PREFIX} {title}",params,viz,
            )

        add(
            "value_month",monthly,"Visão geral — Valor mensal",
            _top_params(monthly,"Visão geral — Valor mensal",TOP_VALUE_METRICS,
                        weekly=False,quantity=False),
        )
        add(
            "value_week",weekly,"Visão geral — Valor semanal",
            _top_params(weekly,"Visão geral — Valor semanal",TOP_VALUE_METRICS,
                        weekly=True,quantity=False),
        )
        add(
            "qty_month",monthly,"Visão geral — Quantidade mensal",
            _top_params(monthly,"Visão geral — Quantidade mensal",TOP_QTY_METRICS,
                        weekly=False,quantity=True),
        )
        add(
            "qty_week",weekly,"Visão geral — Quantidade semanal",
            _top_params(weekly,"Visão geral — Quantidade semanal",TOP_QTY_METRICS,
                        weekly=True,quantity=True),
        )

        for mode, metric_def, fmt in (
            ("value",CAUSE_VALUE,"currency"),
            ("qty",CAUSE_QTY,"quantity"),
        ):
            label = "Valor" if mode=="value" else "Quantidade"
            add(
                f"{mode}_motive",causes,f"Perda OSA por motivo — {label}",
                _cause_params(
                    causes,f"Perda OSA por motivo — {label}",
                    metric_def,"motivo_osa",fmt,
                ),
            )
            add(
                f"{mode}_cause",causes,f"Perda OSA por causa — {label}",
                _cause_params(
                    causes,f"Perda OSA por causa — {label}",
                    metric_def,"causa_osa",fmt,
                ),
            )

        for mode, loss_metric in (("value",MATRIX_VALUE),("qty",MATRIX_QTY)):
            label = "Valor" if mode=="value" else "Quantidade"
            for key,(title,group_column) in MATRIX_SCOPES.items():
                dataset = matrix_datasets[key]
                add(
                    f"{mode}_matrix_{key}",dataset,f"{title} — {label}",
                    _matrix_params(
                        dataset,(group_column,),
                        [loss_metric,MATRIX_PROBLEMS,MATRIX_OSA],
                    ),
                    "pivot_table_v2",
                )

        layout = Layout()
        parents = ["ROOT_ID","GRID_ID"]
        layout.period_tabs(
            "GRID_ID",parents,"Visão geral OSA",
            [
                ("Valor",[
                    ("mensal",charts["value_month"]),
                    ("semanal",charts["value_week"]),
                ]),
                ("Quantidade",[
                    ("mensal",charts["qty_month"]),
                    ("semanal",charts["qty_week"]),
                ]),
            ],
            height=58,
        )
        layout.tabs(
            "GRID_ID",parents,"Perdas por causa",
            [
                ("Valor",[
                    [charts["value_motive"]],
                    [charts["value_cause"]],
                ]),
                ("Quantidade",[
                    [charts["qty_motive"]],
                    [charts["qty_cause"]],
                ]),
            ],
            height=48,
        )
        layout.tabs(
            "GRID_ID",parents,"Análise por dimensão",
            [
                ("Valor",[[
                    charts["value_matrix_region"],
                    charts["value_matrix_retail"],
                    charts["value_matrix_item"],
                ]]),
                ("Quantidade",[[
                    charts["qty_matrix_region"],
                    charts["qty_matrix_retail"],
                    charts["qty_matrix_item"],
                ]]),
            ],
            height=52,
        )

        dashboard = db.session.query(Dashboard).filter(
            Dashboard.slug == DASHBOARD_SLUG
        ).one_or_none()
        if dashboard is None:
            dashboard = Dashboard(
                dashboard_title=DASHBOARD_TITLE,
                slug=DASHBOARD_SLUG,
                published=True,
            )
            db.session.add(dashboard)
        dashboard.dashboard_title = DASHBOARD_TITLE
        dashboard.published = True
        dashboard.position_json = json.dumps(layout.nodes,ensure_ascii=False)
        dashboard.css = (
            ".dashboard-content { background:#e7f0f5 !important; } "
            ".dashboard-component-chart-holder { border-radius:8px; background:#fff; } "
            ".dashboard-component-chart-holder > .header { display:none !important; }"
        )

        # Common slicers mirror the PBI location/activity/brand/category/item/
        # measure selectors. The period control applies only to cause/matrix
        # charts because the top timeline needs its full temporal window.
        dataset_ids = [
            monthly.id,weekly.id,causes.id,
            *[dataset.id for dataset in matrix_datasets.values()],
        ]
        native = overview_native_filters(dataset_ids,filter_options.id)
        top_ids = {
            charts["value_month"].id,charts["value_week"].id,
            charts["qty_month"].id,charts["qty_week"].id,
        }
        period_excluded = list(top_ids)
        native.append(_period_filter(period_options.id,period_excluded))

        dashboard.json_metadata = json.dumps({
            "timed_refresh_immune_slices": [],
            "expanded_slices": {},
            "refresh_frequency": 0,
            "color_scheme": "supersetColors",
            "native_filter_configuration": native,
            "filter_bar_orientation": "HORIZONTAL",
        },ensure_ascii=False)
        dashboard.slices = list(charts.values())
        db.session.commit()

        print(json.dumps({
            "dashboard_id": dashboard.id,
            "slug": dashboard.slug,
            "industry": {"id_customer":142,"label":"AMBEV"},
            "datasets": {
                "monthly":monthly.id,
                "weekly":weekly.id,
                "causes":causes.id,
                "matrices":{key:dataset.id for key,dataset in matrix_datasets.items()},
                "period_options":period_options.id,
            },
            "charts": {key:chart.id for key,chart in charts.items()},
        },ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
