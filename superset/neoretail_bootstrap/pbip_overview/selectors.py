"""Opt-in selector contexts, independent of the frozen KPI SQL.

CNPJ is a cyclic filter graph, not a parent/child cascade. Each option request
uses the other selected dimension columns once, excluding its own selection.
No facts are joined; no product filter flows back into the conversion table.
"""
from copy import deepcopy
from .filter_context import CATALOG_COLUMNS, LOCAL_COLUMNS, PRODUCT_COLUMNS, native_predicates
from neoretail_bootstrap.overview.filters import _filter_definitions, _native_filters_for_targets

COLUMNS=tuple(c for c,_,_ in _filter_definitions())
GEO=tuple(CATALOG_COLUMNS)+tuple(LOCAL_COLUMNS)
PRODUCT=tuple(PRODUCT_COLUMNS)
ITEM_HIDDEN_FILTER={
    'measure':'Filtro Historico Com Dados',
    'dax':'VAR TemDados = CALCULATE(COUNTROWS(FATOS_PARTICULAR_HISTORICO), REMOVEFILTERS(AP_CONVERSAO), REMOVEFILTERS(DIM_CATALOGO_LOCAL[Rede]), REMOVEFILTERS(DIM_LOCAL[Rede])) RETURN IF(TemDados > 0, 1, 0)',
    'measure_returns':[0,1],
    'serialized_operator':'Not(ComparisonKind=0, Literal=null)',
    'status':'UNPROVEN_NULL_COMPARISON',
    'reason':'The serialized null comparison is not assumed to be DAX loose equality or ISBLANK. Both possible zero treatments are retained as an explicit residual; no EXISTS(history) invented.',
}

def context_dependencies(column):
    if column not in COLUMNS:raise ValueError('Unknown PBIP selector '+column)
    group=GEO if column in GEO else PRODUCT+('nm_measure',) if column in PRODUCT else ()
    return tuple(c for c in group if c!=column and c in COLUMNS)

def option_sql(column):
    if column not in COLUMNS:raise ValueError('Unknown PBIP selector '+column)
    # Consume unrelated filters too: a crafted product filter must not constrain
    # AP options or geographic dimensions via an outer WHERE on NULL columns.
    prelude='\n'.join("{% set ignored_"+c+" = get_filters('"+c+"', remove_filter=True) %}" for c in COLUMNS)
    output_columns=tuple(dict.fromkeys(COLUMNS+('regiao',)))
    def project(alias,expression=None):
        return ','.join((expression or alias+'.'+c)+' AS '+c if c==column else 'NULL::text AS '+c for c in output_columns)
    def search(alias,expression=None):
        # Own IN values do not restrict the option universe. Native asynchronous
        # search is different: keep its ILIKE predicate so options beyond the
        # initial 1,000-row page remain discoverable. where_in quotes the scalar.
        return "{% for f in ignored_"+column+" %}{% if f.get('op') in ['ILIKE', 'LIKE'] %} AND "+(expression or alias+'.'+column)+" {{ f.get('op') }} {{ [f.get('val')] | where_in }}{% endif %}{% endfor %}"
    if column in GEO:
        local_filters=native_predicates('pl',{c:v for c,v in LOCAL_COLUMNS.items() if c!=column})
        catalog_filters=native_predicates('pc',{c:v for c,v in CATALOG_COLUMNS.items() if c!=column})
        contexts=f"""WITH local_context AS (
 SELECT pl.* FROM gold.dim_local pl WHERE pl.id_customer=290 AND pl.rede IS NOT NULL
 {local_filters}
), catalog_context AS (
 SELECT pc.* FROM gold.dim_catalogo_local pc
 WHERE pc.id_customer=290 AND pc.rede <> 'GPA'
 AND EXISTS (SELECT 1 FROM gold.dim_local ac WHERE ac.id_customer=pc.id_customer AND ac.id_retailer=pc.id_retailer)
 {catalog_filters}
)
"""
        if column in CATALOG_COLUMNS:
            body='SELECT DISTINCT c.id_customer,'+project('c')+' FROM catalog_context c WHERE EXISTS (SELECT 1 FROM local_context l WHERE l.id_customer=c.id_customer AND l.cnpj IS NOT DISTINCT FROM c.cnpj)'
        else:
            body='SELECT DISTINCT l.id_customer,'+project('l')+' FROM local_context l WHERE EXISTS (SELECT 1 FROM catalog_context c WHERE c.id_customer=l.id_customer AND c.cnpj IS NOT DISTINCT FROM l.cnpj)'
        return prelude+'\n'+contexts+body+search('c' if column in CATALOG_COLUMNS else 'l')
    if column in PRODUCT:
        item_filters=native_predicates('i',{c:v for c,v in PRODUCT_COLUMNS.items() if c!=column})
        conversion_filters=native_predicates('conv',{'nm_measure':'nm_measure'})
        return prelude+f"""\nSELECT DISTINCT i.id_customer,{project('i')} FROM gold.dim_itens i
 WHERE i.id_customer=290 {item_filters}
 AND EXISTS (SELECT 1 FROM gold.dim_conversao conv
 WHERE conv.id_customer=i.id_customer AND CAST(conv.id_item AS TEXT)=CAST(i.id_item AS TEXT)
 AND conv.nm_measure <> 'valor' {conversion_filters})"""+search('i')
    if column=='nm_measure':
        return prelude+'\nSELECT DISTINCT c.id_customer,'+project('c')+" FROM gold.dim_conversao c WHERE c.id_customer=290 AND c.nm_measure <> 'valor'"+search('c')
    return prelude+'\nSELECT DISTINCT a.id_customer,'+project('a','a.nm_activity_level')+' FROM gold.dim_nivel_atividade a WHERE a.id_customer=290 AND a.nm_activity_level IS NOT NULL'+search('a','a.nm_activity_level')

def native_filters(dataset_ids, activity_labels=None):
    filters=deepcopy(_native_filters_for_targets(lambda c:[{'datasetId':dataset_ids[c],'column':{'name':c}}]))
    for f in filters:
        column=f['targets'][0]['column']['name']
        f['cascadeParentIds']=[]
        f['controlValues']['pbipContextParentIds']=['NATIVE_FILTER-neoretail-'+c for c in context_dependencies(column)]
        f['controlValues']['pbipSelectorContext']=True
        f['controlValues']['sortAscending']=True
        f['controlValues']['enableEmptyFilter']=column=='nm_measure'
        if column=='tp_activity_level':
            grouped={}
            for code,label in (activity_labels or {}).items():grouped.setdefault(label,[]).append(code)
            f['controlValues']['pbipOptionValueCodes']={label:sorted(codes) for label,codes in grouped.items()}
        f['description']=''
    return filters
