"""Main-page PBIP filters as intersections of dimension key sets.

Catalog Rede/Bandeira are not local attributes. The active CNPJ many-to-many
relationship intersects catalog and local CNPJ sets in both directions. EXISTS
implements that intersection without multiplying facts for duplicate keys.
Gold DIM_LOCAL already contains the AUX_CONTRATADO_LOCAL inner-join population;
the existing AUX retailer key set is verified separately before publication.
"""

CATALOG_COLUMNS={'rede':'rede','bandeira':'bandeira'}
LOCAL_COLUMNS={c:c for c in ('uf','cidade','tipo_local','loja','regiao')}
PRODUCT_COLUMNS={c:c for c in ('item','descricao_marca','hierarquia_1','hierarquia_2','hierarquia_3')}

def native_predicates(alias, columns):
    lines=[]
    for column,expression in columns.items():
        value=f'{alias}.{expression}'
        lines += [f"{{% for filter in get_filters('{column}', remove_filter=True) %}}",
          "{% set values = filter.get('val', []) %}",
          "{% set nonnull = values | reject('none') | list %}",
          "{% if filter.get('op') == 'IN' %}",
          f" AND ({{% if nonnull %}}{value} IN {{{{ nonnull | where_in }}}}{{% else %}}FALSE{{% endif %}}{{% if none in values %}} OR {value} IS NULL{{% endif %}})",
          "{% elif filter.get('op') == 'NOT IN' %}",
          f" AND ({{% if nonnull %}}{value} NOT IN {{{{ nonnull | where_in }}}}{{% else %}}TRUE{{% endif %}}{{% if none not in values %}} OR {value} IS NULL{{% endif %}}){{% if none in values %}} AND {value} IS NOT NULL{{% endif %}}",
          "{% endif %}","{% endfor %}"]
    return '\n'.join(lines)

def location_membership(alias, *, local_predicates='', catalog_predicates='', exclude_nonstore=False):
    local_extra=f'AND ({local_predicates})' if local_predicates else ''
    catalog_extra=f'AND ({catalog_predicates})' if catalog_predicates else ''
    if exclude_nonstore:
        local_extra += " AND (pl.tipo_local IS NULL OR pl.tipo_local NOT IN ('DEPÓSITO','CD','LOJA VIRTUAL'))"
        catalog_extra += " AND (pc.tipo_local IS NULL OR pc.tipo_local NOT IN ('DEPÓSITO','CD','LOJA VIRTUAL'))"
    return f"""EXISTS (
 SELECT 1 FROM gold.dim_local pl
 WHERE pl.id_customer={alias}.id_customer AND pl.id_location={alias}.id_location
   AND pl.rede IS NOT NULL {local_extra}
   AND EXISTS (
     SELECT 1 FROM gold.dim_catalogo_local pc
     WHERE pc.id_customer=pl.id_customer AND pc.cnpj IS NOT DISTINCT FROM pl.cnpj
       AND pc.rede <> 'GPA' {catalog_extra}
       AND EXISTS (SELECT 1 FROM gold.dim_local ac
                   WHERE ac.id_customer=pc.id_customer AND ac.id_retailer=pc.id_retailer)
   )
)"""

def fact_filter_predicates(alias, *, exclude_activity=False, activity_expression=None, exclude_nonstore=False, product_alias=None):
    # Local and catalog selections are independent before their key intersection.
    membership=location_membership(alias,exclude_nonstore=exclude_nonstore)
    membership=membership.replace('AND pl.rede IS NOT NULL', 'AND pl.rede IS NOT NULL\n'+native_predicates('pl',LOCAL_COLUMNS))
    membership=membership.replace("AND pc.rede <> 'GPA'", "AND pc.rede <> 'GPA'\n"+native_predicates('pc',CATALOG_COLUMNS))
    result='AND '+membership+'\n'+native_predicates(product_alias or alias,PRODUCT_COLUMNS)
    if not exclude_activity:
        result+='\n'+native_predicates(alias,{'tp_activity_level':activity_expression or 'tp_activity_level'})
    return result

def selector_options_sql():
    """Catalog/local selector tuples are dimension key sets, never fact joins.

    DISTINCT is intentional here: selector options are sets; KPI facts never
    traverse this many-to-many join and therefore cannot be multiplied by it.
    Native cascade direction remains a separately reported UI limitation.
    """
    columns=tuple(CATALOG_COLUMNS)+tuple(LOCAL_COLUMNS)+tuple(PRODUCT_COLUMNS)+('tp_activity_level',)
    def projection(values):
        return ','.join(values.get(c,'NULL::text')+' AS '+c for c in columns)
    local={**{c:'pc.'+c for c in CATALOG_COLUMNS},**{c:'pl.'+c for c in LOCAL_COLUMNS}}
    product={c:'i.'+c for c in PRODUCT_COLUMNS}
    return ('SELECT DISTINCT pl.id_customer,'+projection(local)+" FROM gold.dim_local pl JOIN gold.dim_catalogo_local pc ON pc.id_customer=pl.id_customer AND pc.cnpj IS NOT DISTINCT FROM pl.cnpj WHERE pl.id_customer=290 AND pl.rede IS NOT NULL AND pc.rede <> 'GPA' AND EXISTS (SELECT 1 FROM gold.dim_local ac WHERE ac.id_customer=pc.id_customer AND ac.id_retailer=pc.id_retailer)"
       +' UNION ALL SELECT DISTINCT i.id_customer,'+projection(product)+' FROM gold.dim_itens i WHERE i.id_customer=290'
       +' UNION ALL SELECT DISTINCT a.id_customer,'+projection({'tp_activity_level':'a.tp_activity_level'})+' FROM gold.dim_nivel_atividade a WHERE a.id_customer=290 AND a.nm_activity_level IS NOT NULL')
