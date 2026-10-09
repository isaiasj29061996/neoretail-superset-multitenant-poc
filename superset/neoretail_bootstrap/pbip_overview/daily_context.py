"""TVD/IVD: evaluate LASTNONBLANK before CALCULATE's AP removal.

Date candidates preserve incoming AP and page dimensions. The final SUM clears
AP and applies the sibling non-store table filters. One date is selected per
month and per headline: PBIP U3M calls the measure in M-1, M-2 and M-3.
"""
from .filter_context import fact_filter_predicates
from .conversion_context import converted_item_membership


def daily_context_sql(metric='tvd'):
    if metric not in ('tvd', 'ivd'):
        raise ValueError('Only TVD/IVD may use this PBIP context')
    # Captured masks are reused by the independent contexts, not removed from
    # the date universe. get_filters(remove_filter=True) only consumes the outer
    # Superset filter; the captured selection is applied explicitly below.
    from .headlines import NULL_DIMENSIONS
    date_where = fact_filter_predicates('f', product_alias='i')
    value_where = fact_filter_predicates('f', product_alias='i', exclude_nonstore=True)
    task_where = fact_filter_predicates('o', product_alias='i', activity_expression='max_tp_activity_level', exclude_nonstore=True)
    return """{% set incoming_measure = get_filters('nm_measure', remove_filter=True) %}
{% set selected = incoming_measure[0].get('val', []) if incoming_measure|length == 1 else [] %}
""" + f"""WITH date_context AS MATERIALIZED (
 SELECT f.id_time::date AS data, f.id_customer,
        SUM(f.tvd_simplificado)::float8 AS tvd_date_sum,
        SUM(f.ivd_simplificado)::float8 AS ivd_date_sum
 FROM gold.fato_ivd_tvd f
 LEFT JOIN gold.dim_itens i ON i.id_customer=f.id_customer AND CAST(i.id_item AS text)=CAST(f.id_item AS text)
 WHERE f.id_customer=290 {date_where}
 AND {converted_item_membership('f')}
 AND EXISTS (SELECT 1 FROM gold.nr_pbip_calendar cal WHERE cal.id_customer=f.id_customer AND cal.data=f.id_time::date)
 GROUP BY f.id_time::date,f.id_customer
), selected_dates AS (
 SELECT id_customer,date_trunc('month',data)::date AS month,
        MAX(data) FILTER (WHERE {metric}_date_sum IS NOT NULL) AS data
 FROM date_context GROUP BY id_customer,date_trunc('month',data)::date
), value_context AS (
 SELECT f.id_time::date AS data,f.id_customer,
        SUM(f.tvd_simplificado)::float8 AS tvd,
        SUM(f.ivd_simplificado)::float8 AS ivd
 FROM gold.fato_ivd_tvd f
 JOIN selected_dates chosen ON chosen.id_customer=f.id_customer AND chosen.data=f.id_time::date
 LEFT JOIN gold.dim_itens i ON i.id_customer=f.id_customer AND CAST(i.id_item AS text)=CAST(f.id_item AS text)
 WHERE f.id_customer=290 {value_where}
 GROUP BY f.id_time::date,f.id_customer
), latest AS (
 SELECT id_customer,MAX(data) AS data FROM selected_dates WHERE data IS NOT NULL GROUP BY id_customer
), tasks AS (
 SELECT o.id_customer,
 COUNT(o.id_item) FILTER(WHERE o.regra_critico='CRITICO' AND COALESCE(o.tvd,0)>0)::bigint AS itens_criticos_tvd,
 COUNT(o.id_item) FILTER(WHERE o.regra_critico='F' AND COALESCE(o.tvd,0)>0)::bigint AS itens_risco_tvd,
 COUNT(o.id_item) FILTER(WHERE o.regra_critico='CRITICO' AND COALESCE(o.ivd,0)>0)::bigint AS itens_criticos_ivd,
 COUNT(o.id_item) FILTER(WHERE o.regra_critico='F' AND COALESCE(o.ivd,0)>0)::bigint AS itens_risco_ivd
 FROM gold.calculo_oportunidades o
 LEFT JOIN gold.dim_itens i ON i.id_customer=o.id_customer AND i.id_item=o.id_item
 WHERE o.id_customer=290 {task_where} GROUP BY o.id_customer
)
 SELECT d.data,d.id_customer,v.tvd,v.ivd,
 CASE WHEN d.data=l.data THEN COALESCE(t.itens_criticos_tvd,0) ELSE 0 END AS itens_criticos_tvd,
 CASE WHEN d.data=l.data THEN COALESCE(t.itens_risco_tvd,0) ELSE 0 END AS itens_risco_tvd,
 CASE WHEN d.data=l.data THEN COALESCE(t.itens_criticos_ivd,0) ELSE 0 END AS itens_criticos_ivd,
 CASE WHEN d.data=l.data THEN COALESCE(t.itens_risco_ivd,0) ELSE 0 END AS itens_risco_ivd,
 {NULL_DIMENSIONS}
 FROM selected_dates d LEFT JOIN value_context v ON v.id_customer=d.id_customer AND v.data=d.data
 LEFT JOIN latest l ON l.id_customer=d.id_customer LEFT JOIN tasks t ON t.id_customer=d.id_customer
 WHERE d.data IS NOT NULL"""
