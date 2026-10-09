"""LACTALIS main-page context; existence filters do not multiply fact rows.

DIM_LOCAL CNPJ <-> DIM_CATALOGO_LOCAL CNPJ is a key-set intersection.
The page's catalog predicate is evaluated before filtering fact location keys.
Only the overview datasets opt into these dedicated serving objects.
"""

def location_membership(alias: str) -> str:
    return f"""EXISTS (
 SELECT 1 FROM gold.dim_local pl
 WHERE pl.id_customer={alias}.id_customer AND pl.id_location={alias}.id_location
   AND pl.rede IS NOT NULL
   AND EXISTS (
     SELECT 1 FROM gold.dim_catalogo_local pc
     WHERE pc.id_customer=pl.id_customer AND pc.cnpj IS NOT DISTINCT FROM pl.cnpj
       AND pc.rede <> 'GPA'
       AND EXISTS (SELECT 1 FROM gold.dim_local ac
                   WHERE ac.id_customer=pc.id_customer AND ac.id_retailer=pc.id_retailer)
   )
)"""

def adapt_sources(query: str) -> str:
    for old,new in (
        ('nr_overview_history','nr_pbip_overview_history'),
        ('nr_overview_semantic_default','nr_pbip_overview_semantic_default'),
        ('nr_osa_semantic_default','nr_pbip_osa_semantic_default'),
        ('nr_osa_industry_causes','nr_pbip_osa_industry_causes'),
    ):
        query=query.replace('gold.'+old,'gold.'+new)
    return query
