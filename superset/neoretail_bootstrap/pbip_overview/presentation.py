"""Opt-in headlines; retain the legacy chart layout and grouped bar universe."""
from copy import deepcopy
from neoretail_bootstrap.overview.presentation import chart_specs as legacy_specs
from neoretail_bootstrap.core.metrics import metric
from neoretail_bootstrap.overview.filters import sql_filter

def chart_specs(*args):
    specs=[(dataset,title,deepcopy(params)) for dataset,title,params in legacy_specs(*args)]
    headline_scope = "semantic_scope = 'all'"
    for _,title,params in specs:
        if title in ('Giro','ROI','MARKUP'):
            params['pbip_headline_scope']=True
            params['adhoc_filters']=[sql_filter(headline_scope,'filter_headline_scope')]
        if title in ('ROI','MARKUP'):
            params['pbip_dax_zero_guard']=True
        if title=='ROI':
            params['pbip_roi_annual_blank']=True
        if title in ('Vendas','ROI','MARKUP'):
            params['pbip_sellout_u3m']=True
        if title=='OSA':
            params['pbip_loss_components']=True
            params['metrics']=params['metrics'][:2]+[
                metric('Perda quantidade','SUM(loss_qty_sum)'),
                metric('Perda preco soma','SUM(price_sum)'),
                metric('Perda preco contagem','SUM(price_count)'),
                metric('Perda fator','MAX(conversion_rate)'),
            ]
    for _,title,params in specs:
        if title in ('Vendas','ROI','MARKUP'):
            params['adhoc_filters'].append(sql_filter("row_scope = 'monthly'", 'pbip_monthly_scope'))
    return specs
