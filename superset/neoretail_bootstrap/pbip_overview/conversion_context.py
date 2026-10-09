"""AP -> conversion -> items -> facts; item filters do not flow backwards.

Direction is verified by deserializing the actual PBIP with Microsoft TOM.
The MAX rate remains a dimension scalar, independent of selected product keys.
"""
from .filter_context import PRODUCT_COLUMNS, native_predicates

def dimension_factors_sql():
    return f"""SELECT c.id_customer,c.nm_measure,MAX(c.conversion_rate) AS conversion_rate
 FROM gold.dim_conversao c
 WHERE c.id_customer=290
 GROUP BY c.id_customer,c.nm_measure"""

def filtered_dimension_factors_sql():
    return dimension_factors_sql().replace('MAX(c.conversion_rate)',
        'MAX(CASE WHEN {{ pbip_factor_blank | lower }} THEN NULL ELSE c.conversion_rate END)')

def converted_item_membership(alias, *, mode=None):
    if mode is None:
        predicate="{% if selected %} AND pbip_conv.nm_measure IN {{ selected | where_in }}{% endif %} AND pbip_conv.nm_measure <> 'valor'"
    else:
        predicate="AND pbip_conv.nm_measure='"+mode.replace("'","''")+"'"
    return f"""EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer={alias}.id_customer AND CAST(ci.id_item AS TEXT)=CAST({alias}.id_item AS TEXT) {predicate})"""

def overview_factor_region_sql():
    return "factor_region AS (SELECT h.data,h.id_customer,h.tp_activity_level,h.regiao,m.nm_measure,f.conversion_rate FROM (SELECT DISTINCT data,id_customer,tp_activity_level,regiao FROM history_filtered) h CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290) m LEFT JOIN ("+filtered_dimension_factors_sql()+") f ON f.id_customer=h.id_customer AND f.nm_measure=m.nm_measure),\n"

def loss_factor_sql():
    return "loss_factor AS (SELECT h.data,h.id_customer,m.nm_measure,f.conversion_rate FROM (SELECT DISTINCT data,id_customer FROM cause_filtered) h CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290) m LEFT JOIN ("+filtered_dimension_factors_sql()+") f ON f.id_customer=h.id_customer AND f.nm_measure=m.nm_measure),"

def apply_conversion_context(query, *, osa=False):
    """Replace only conversion input/routing; retain frozen metric expressions."""
    import re
    prelude="""{% set incoming_measure = get_filters('nm_measure', remove_filter=True) %}
{% set selected = incoming_measure[0].get('val', []) if incoming_measure|length == 1 else [] %}
{% set pbip_factor_blank = selected|length != 1 or selected[0] == 'valor' %}
{% set conversion_filters = [{'val': ['unidade'] if pbip_factor_blank else selected}] %}
"""
    query=query.replace("{% set conversion_filters = get_filters('nm_measure') %}\n",'')
    detail=re.search(r'\{% set has_detail_filter = (.*?) %\}',query)
    if not detail:raise ValueError('PBIP detail routing declaration changed')
    prelude+='{% set has_detail_filter = pbip_factor_blank or '+detail.group(1)+' %}\n'
    query=query.replace(detail.group(0),'')
    # Only the input universe changes. Frozen OSA/loss formulas remain verbatim.
    for table,alias in [('nr_pbip_overview_history','h'),('nr_pbip_osa_industry_causes','c'),('calculo_oportunidades','o')]:
        marker='FROM gold.'+table+' '+alias
        # Tasks have dimension joins between FROM and WHERE, handled separately.
        if alias!='o':
            query=query.replace(marker+' WHERE 1=1',marker+' WHERE '+converted_item_membership(alias)+' AND 1=1')
    if osa:
        query=query.replace('WHERE 1=1\nAND EXISTS (','WHERE '+converted_item_membership('o')+' AND 1=1\nAND EXISTS (')
        query=query.replace('gold.nr_pbip_osa_semantic_default','gold.nr_pbip_osa_semantic_v3')
    if osa:
        query,n=re.subn(r'loss_factor AS \(.*?\),loss AS \(',loss_factor_sql()+'loss AS (',query,count=1,flags=re.S)
    else:
        query,n=re.subn(r'factor_region AS \(.*?\),\nexpanded AS \(',overview_factor_region_sql()+'expanded AS (',query,count=1,flags=re.S)
        # Preserve missing input operands during conversion, not synthetic zero.
        query=query.replace('SUM(COALESCE(volume_unidades,0))','SUM(volume_unidades)')
        query=query.replace('SUM(COALESCE(estoque_unidades,0))','SUM(estoque_unidades)')
        query=query.replace('gold.nr_pbip_overview_semantic_default','gold.nr_pbip_overview_semantic_v3')
        query=query.replace('ELSE 0 END)::float8 sellout_sum','ELSE NULL END)::float8 sellout_sum')
    if n!=1:raise ValueError('PBIP conversion CTE boundary changed')
    if osa:
        return prelude+"SELECT * FROM (\n"+query+"\n) pbip_selected_context WHERE nm_measure IN {{ conversion_filters[0].get('val') | where_in }}"
    # Both aggregates consume the identical effective filter key set. Repeating
    # the bridge in a second fact scan caused a pathological nested-loop plan.
    match=re.search(r'WITH history_filtered AS \(.*?\),\n',query,flags=re.S)
    if not match:raise ValueError('PBIP shared history context boundary changed')
    history_context=match.group(0).replace('WITH history_filtered AS (','WITH history_filtered AS MATERIALIZED (',1)
    query=query.replace(match.group(0),'WITH ',1)
    quantity=quantity_by_activity_sql(filtered_dimension_factors_sql(),source='history_filtered',
        measure_predicate="AND f.nm_measure IN {{ conversion_filters[0].get('val') | where_in }}")
    override="{% if has_detail_filter %}"+quantity_projection()+"{% else %}b.sales_qty_sum{% endif %} AS sales_qty_sum"
    # The scalar lookup must not inline and rescan millions of rows per output.
    return prelude+"{% if has_detail_filter %}\n"+history_context+"pbip_quantity_by_activity AS MATERIALIZED (\n"+quantity+")\n{% endif %}\nSELECT "+overview_projection(override)+" FROM (\n"+query+"\n) b WHERE b.nm_measure IN {{ conversion_filters[0].get('val') | where_in }}"

def quantity_by_activity_sql(factors_sql, *, native=False, measure_predicate='', source='gold.nr_pbip_overview_history'):
    from .filter_context import fact_filter_predicates
    predicates=fact_filter_predicates('h') if native else ''
    if native:
        predicates+=' AND '+converted_item_membership('h')
    # Venda Historico is SUMX(VOLUME_UNIDADES * Fator), not SUM(volume)*Fator.
    return "SELECT h.data,h.id_customer,h.tp_activity_level,f.nm_measure,SUM(h.volume_unidades*f.conversion_rate)::float8 AS quantity_sum FROM "+source+" h JOIN ("+factors_sql+") f ON f.id_customer=h.id_customer WHERE h.id_customer=290 "+predicates+' '+measure_predicate+' GROUP BY h.data,h.id_customer,h.tp_activity_level,f.nm_measure'

def quantity_projection():
    return "(SELECT SUM(q.quantity_sum) FROM pbip_quantity_by_activity q WHERE q.data=b.data AND q.id_customer=b.id_customer AND q.nm_measure=b.nm_measure AND (b.semantic_scope='all' OR q.tp_activity_level IS NOT DISTINCT FROM b.tp_activity_level))"

def overview_projection(quantity):
    columns=('data','id_customer','tp_activity_level','activity_level','nm_measure','semantic_scope','semantic_precomputed','sellout_sum','sales_cost_sum','sales_qty_sum','stock_cost_sum','stock_qty_sum','giro_sum_positive','giro_count_positive','osa_problem_sum','osa_active_sum','rede','bandeira','uf','cidade','tipo_local','loja','regiao','item','descricao_marca','hierarquia_1','hierarquia_2','hierarquia_3')
    return ','.join(quantity if c=='sales_qty_sum' else 'b.'+c for c in columns)

def converted_default_sql(base):
    quantity=quantity_by_activity_sql(dimension_factors_sql())
    projection="CASE WHEN b.nm_measure='valor' THEN b.sales_qty_sum ELSE "+quantity_projection()+" END AS sales_qty_sum"
    return 'WITH pbip_quantity_by_activity AS ('+quantity+') SELECT '+overview_projection(projection)+' FROM ('+base+') b'
