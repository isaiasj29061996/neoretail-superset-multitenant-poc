"""PBIP conversion-independent headlines; legacy builders stay frozen."""
from .filter_context import fact_filter_predicates, location_membership, CATALOG_COLUMNS, LOCAL_COLUMNS, PRODUCT_COLUMNS

DIMENSION_COLUMNS=tuple(CATALOG_COLUMNS)+tuple(LOCAL_COLUMNS)+tuple(PRODUCT_COLUMNS)+('tp_activity_level',)
NULL_DIMENSIONS=','.join('NULL::text AS '+c for c in DIMENSION_COLUMNS)

def has_dimensions():return ' or '.join("get_filters('"+c+"')" for c in DIMENSION_COLUMNS)

def giro_detail_sql(*, native=True):
    from .conversion_context import converted_item_membership
    where=fact_filter_predicates('h') if native else 'AND '+location_membership('h')
    where+=' AND '+converted_item_membership('h',mode='unidade')
    activity="CASE h.tp_activity_level WHEN 'F' THEN 'Fast Mover' WHEN 'S' THEN 'Slow Mover' WHEN 'U' THEN 'Ultra Slow Mover' WHEN 'N' THEN 'New Mover' ELSE NULL END"
    components='SUM(h.giro) FILTER(WHERE h.giro>0)::float8 AS giro_sum_positive,COUNT(h.giro) FILTER(WHERE h.giro>0)::bigint AS giro_count_positive'
    return f"""WITH filtered AS (SELECT h.* FROM gold.nr_pbip_overview_history h WHERE h.id_customer=290 {where})
 SELECT h.data,h.id_customer,'unidade'::text AS nm_measure,'all'::text AS semantic_scope,NULL::text AS activity_level,{components},{NULL_DIMENSIONS}
 FROM filtered h GROUP BY h.data,h.id_customer
 UNION ALL
 SELECT h.data,h.id_customer,'unidade'::text,'activity'::text,{activity},{components},{NULL_DIMENSIONS}
 FROM filtered h WHERE {activity} IS NOT NULL GROUP BY h.data,h.id_customer,{activity}"""

def giro_semantic_sql():
    return ("{% set ignored_conversion = get_filters('nm_measure', remove_filter=True) %}\n"
      +'{% if '+has_dimensions()+' %}\n'+giro_detail_sql()
      +'\n{% else %}\nSELECT * FROM gold.nr_pbip_giro_v3\n{% endif %}')

def headline_detail_sql(*, native=True):
    fact_where=fact_filter_predicates('f',product_alias='i',exclude_nonstore=True) if native else 'AND '+location_membership('f',exclude_nonstore=True)
    task_where=fact_filter_predicates('o',product_alias='i',activity_expression='max_tp_activity_level',exclude_nonstore=True) if native else 'AND '+location_membership('o',exclude_nonstore=True)
    return f"""WITH fact_filtered AS (
 SELECT f.* FROM gold.fato_ivd_tvd f
 LEFT JOIN gold.dim_itens i ON i.id_customer=f.id_customer AND CAST(i.id_item AS TEXT)=CAST(f.id_item AS TEXT)
 WHERE f.id_customer=290 {fact_where}
), daily AS (
 SELECT id_time::date AS data,id_customer,SUM(COALESCE(tvd_simplificado,0))::float8 AS tvd,SUM(COALESCE(ivd_simplificado,0))::float8 AS ivd
 FROM fact_filtered GROUP BY id_time::date,id_customer
), latest AS (SELECT id_customer,MAX(data) AS data FROM daily GROUP BY id_customer), tasks AS (
 SELECT o.id_customer,
 COUNT(o.id_item) FILTER(WHERE o.regra_critico='CRITICO' AND COALESCE(o.tvd,0)>0)::bigint AS itens_criticos_tvd,
 COUNT(o.id_item) FILTER(WHERE o.regra_critico='F' AND COALESCE(o.tvd,0)>0)::bigint AS itens_risco_tvd,
 COUNT(o.id_item) FILTER(WHERE o.regra_critico='CRITICO' AND COALESCE(o.ivd,0)>0)::bigint AS itens_criticos_ivd,
 COUNT(o.id_item) FILTER(WHERE o.regra_critico='F' AND COALESCE(o.ivd,0)>0)::bigint AS itens_risco_ivd
 FROM gold.calculo_oportunidades o
 LEFT JOIN gold.dim_itens i ON i.id_customer=o.id_customer AND i.id_item=o.id_item
 WHERE o.id_customer=290 {task_where} GROUP BY o.id_customer
)
 SELECT d.data,d.id_customer,d.tvd,d.ivd,
 CASE WHEN d.data=l.data THEN COALESCE(t.itens_criticos_tvd,0) ELSE 0 END AS itens_criticos_tvd,
 CASE WHEN d.data=l.data THEN COALESCE(t.itens_risco_tvd,0) ELSE 0 END AS itens_risco_tvd,
 CASE WHEN d.data=l.data THEN COALESCE(t.itens_criticos_ivd,0) ELSE 0 END AS itens_criticos_ivd,
 CASE WHEN d.data=l.data THEN COALESCE(t.itens_risco_ivd,0) ELSE 0 END AS itens_risco_ivd,
 {NULL_DIMENSIONS}
 FROM daily d JOIN latest l ON l.id_customer=d.id_customer LEFT JOIN tasks t ON t.id_customer=d.id_customer"""

def headline_semantic_sql(metric='tvd'):
    from .daily_context import daily_context_sql
    return daily_context_sql(metric)
