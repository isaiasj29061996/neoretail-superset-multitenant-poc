"""Preserve SUMX cost BLANKs in PBIP datasets without republishing marts."""
from .filter_context import fact_filter_predicates
from .conversion_context import converted_item_membership, overview_projection

COST_OPERANDS = {
    'sales_cost_sum': 'volume_unidades',
    'stock_cost_sum': 'estoque_medio',
}


def cost_sum_sql(operand):
    return f'SUM({operand} * avg_price_cost)'


def default_cost_blank_sql():
    # The frozen mart loses BLANK only when every row-product is BLANK. A sum
    # containing a numeric product (including real zero/cancellation) is kept.
    # Inspect raw operands only for zero-valued mart contexts; all other values
    # and every other metric remain verbatim. No source data is mutated.
    predicates = fact_filter_predicates('h') + ' AND ' + converted_item_membership('h')
    projection = overview_projection('b.sales_qty_sum')
    for name, operand in COST_OPERANDS.items():
        # CASE short-circuits the lookup for nonzero values. EXISTS stops on
        # the first numeric product, including a genuine zero product. This
        # avoids scanning all history just to certify non-BLANK aggregates.
        calculable = f"""EXISTS (
 SELECT 1 FROM gold.nr_pbip_overview_history h
 WHERE h.id_customer=b.id_customer AND h.data=b.data
 AND (b.semantic_scope='all' OR h.tp_activity_level IS NOT DISTINCT FROM b.tp_activity_level)
 AND h.{operand} IS NOT NULL AND h.avg_price_cost IS NOT NULL {predicates}
)"""
        projection = projection.replace(
            'b.' + name,
            f'CASE WHEN b.{name}=0 AND NOT {calculable} '
            f'THEN NULL ELSE b.{name} END AS {name}',
        )
    return f"""SELECT {projection} FROM gold.nr_pbip_overview_semantic_v3 b
WHERE b.nm_measure IN {{{{ conversion_filters[0].get('val') | where_in }}}}"""


def apply_cost_blank(query):
    for name, operand in COST_OPERANDS.items():
        old = f'SUM(COALESCE({operand},0)*COALESCE(avg_price_cost,0))'
        if query.count(old) != 1:
            raise ValueError(f'PBIP {name} expression boundary changed')
        query = query.replace(old, cost_sum_sql(operand))
    marker = 'SELECT * FROM gold.nr_pbip_overview_semantic_v3'
    if marker not in query:
        raise ValueError('PBIP default cost source boundary changed')
    default = default_cost_blank_sql()
    query = query.replace(marker + ' WHERE 1=0',
                          'SELECT * FROM (' + default + ') pbip_empty_cost WHERE 1=0')
    return query.replace(marker, default)
