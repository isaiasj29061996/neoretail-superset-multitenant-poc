"""PBIP-only full-U3M SUMX(Regiao); monthly SQL remains verbatim."""
from .filter_context import fact_filter_predicates
from .conversion_context import converted_item_membership, filtered_dimension_factors_sql

SCOPE='pbip_c05_u3m'

def full_u3m_sql(monthly_sql):
    predicates=fact_filter_predicates('h')+' AND '+converted_item_membership('h')
    sums=('sales_cost_sum','sales_qty_sum','stock_cost_sum','stock_qty_sum','giro_sum_positive','giro_count_positive','osa_problem_sum','osa_active_sum')
    dims=('rede','bandeira','uf','cidade','tipo_local','loja','regiao','item','descricao_marca','hierarquia_1','hierarquia_2','hierarquia_3')
    # Existing cost/stock components are reused unchanged, retaining C14/C16.
    components=','.join('SUM(b.'+c+') AS '+c for c in sums)
    return """{% set incoming_measure = get_filters('nm_measure', remove_filter=True) %}
{% set selected = incoming_measure[0].get('val', []) if incoming_measure|length == 1 else [] %}
{% set pbip_factor_blank = selected|length != 1 or selected[0] == 'valor' %}
{% set conversion_filters = [{'val': ['unidade'] if pbip_factor_blank else selected}] %}
"""+f"""WITH frozen_monthly AS MATERIALIZED (
{monthly_sql}
), retained_components AS (
 SELECT {components} FROM frozen_monthly b
 WHERE b.semantic_scope='all' AND EXISTS(SELECT 1 FROM gold.nr_pbip_calendar cal
 WHERE cal.id_customer=b.id_customer AND cal.u3m AND date_trunc('month',cal.data)::date=b.data)
), region_context AS (
 SELECT h.regiao,SUM(h.faturamento) AS revenue,SUM(h.volume_unidades) AS volume,
        AVG(h.avg_sales_price) AS price
 FROM gold.nr_pbip_overview_history h WHERE h.id_customer=290 {predicates}
 AND EXISTS(SELECT 1 FROM gold.nr_pbip_calendar cal WHERE cal.id_customer=h.id_customer
 AND cal.u3m AND date_trunc('month',cal.data)::date=h.data)
 GROUP BY h.regiao
), factor AS (
 SELECT conversion_rate FROM ({filtered_dimension_factors_sql()}) f
 WHERE nm_measure IN {{{{ conversion_filters[0].get('val') | where_in }}}}
), sellout AS (
 SELECT SUM(CASE WHEN r.revenue>0 THEN r.revenue
 ELSE (r.volume*f.conversion_rate)*(r.price*f.conversion_rate) END)::float8 AS sellout_sum
 FROM region_context r CROSS JOIN factor f
), anchor AS (SELECT MAX(data_at) AS data FROM gold.nr_pbip_calendar WHERE id_customer=290)
 SELECT a.data,290 AS id_customer,NULL::text AS tp_activity_level,NULL::text AS activity_level,
 {{{{ conversion_filters[0].get('val') | where_in }}}}[1] AS nm_measure,
 'all'::text AS semantic_scope,TRUE AS semantic_precomputed,s.sellout_sum,
 {','.join('c.'+c for c in sums)},
 {','.join('NULL::text AS '+c for c in dims)},'{SCOPE}'::text AS row_scope
 FROM anchor a CROSS JOIN sellout s CROSS JOIN retained_components c""".replace("{{ conversion_filters[0].get('val') | where_in }}[1]", "(SELECT nm_measure FROM gold.dim_conversao WHERE id_customer=290 AND nm_measure IN {{ conversion_filters[0].get('val') | where_in }} LIMIT 1)")

def wrap_monthly_sql(monthly_sql):
    # A per-query outer scope is intentional. Superset get_filters reads shared
    # request form data; dispatching the auxiliary query through it can select
    # the timeline scope. Literal scopes let PostgreSQL prune the unused branch.
    return "SELECT monthly.*, 'monthly'::text AS row_scope FROM (\n"+monthly_sql+"\n) monthly UNION ALL (\n"+full_u3m_sql(monthly_sql)+"\n)"
