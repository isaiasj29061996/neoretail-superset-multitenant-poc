"""Overview semantics: existing certified contracts."""
from __future__ import annotations

from neoretail_bootstrap.core.metrics import metric
from neoretail_bootstrap.core.filters import _jinja_filter_predicates
from .filters import HEADLINE_FILTER_COLUMNS


HISTORY_SQL = """
SELECT
  f.mes_ano AS data,
  f.id_customer,
  f.id_item,
  f.id_location,
  f.volume_unidades,
  f.faturamento,
  f.estoque_unidades,
  f.expectativa_vendas,
  f.qtd_perda_osa,
  f.rup,
  f.est_virtual,
  f.giro,
  f.qtd_problemas_osa,
  f.qtd_item_ativo_osa,
  f.avg_sales_price,
  f.avg_price_cost,
  f.estoque_medio,
  f.demanda_media,
  f.tp_activity_level,
  CASE f.tp_activity_level
    WHEN 'F' THEN 'Fast Mover'
    WHEN 'S' THEN 'Slow Mover'
    WHEN 'US' THEN 'Ultra Slow Mover'
    WHEN 'N' THEN 'New Mover'
    ELSE COALESCE(f.tp_activity_level, 'Outros')
  END AS activity_level,
  l.rede, l.bandeira, l.uf, l.cidade, l.tipo_local, l.loja, l.regiao,
  i.item, i.descricao_marca, i.hierarquia_1, i.hierarquia_2, i.hierarquia_3,
  CONCAT_WS('|', f.id_customer::text, f.id_location, f.id_item) AS opportunity_key,
  o.qtd_problemas_osa_m0,
  o.max_tp_activity_level
FROM gold.fato_historico f
LEFT JOIN gold.dim_local l
  ON l.id_customer = f.id_customer AND l.id_location = f.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer = f.id_customer AND i.id_item = f.id_item
LEFT JOIN (
  SELECT DISTINCT ON (id_customer, id_location, id_item)
    id_customer, id_location, id_item, qtd_problemas_osa_m0, max_tp_activity_level
  FROM gold.calculo_oportunidades
  ORDER BY id_customer, id_location, id_item, _silver_refreshed_at DESC NULLS LAST
) o ON o.id_customer = f.id_customer AND o.id_location = f.id_location AND o.id_item = f.id_item
""".strip()


M = {
    "tvd": metric("TVD", "SUM(tvd_simplificado)"),
    "ivd": metric("IVD", "SUM(ivd_simplificado)"),
    "tvd_critical": metric("Itens críticos TVD", "COUNT(DISTINCT CASE WHEN regra_critico = 'CRITICO' AND COALESCE(oportunidade_tvd,0) > 0 THEN opportunity_key END)"),
    "tvd_risk": metric("Itens risco TVD", "COUNT(DISTINCT CASE WHEN regra_critico = 'F' AND COALESCE(oportunidade_tvd,0) > 0 THEN opportunity_key END)"),
    "ivd_critical": metric("Itens críticos IVD", "COUNT(DISTINCT CASE WHEN regra_critico = 'CRITICO' AND COALESCE(oportunidade_ivd,0) > 0 THEN opportunity_key END)"),
    "ivd_risk": metric("Itens risco IVD", "COUNT(DISTINCT CASE WHEN regra_critico = 'F' AND COALESCE(oportunidade_ivd,0) > 0 THEN opportunity_key END)"),
    "sellout": metric("Venda sell out", "CASE WHEN SUM(faturamento) > 0 THEN SUM(faturamento) ELSE SUM(volume_unidades * avg_sales_price) END"),
    "cost": metric("Venda custo", "SUM(volume_unidades * avg_price_cost)"),
    "sales_qty": metric("Venda qtd", "SUM(volume_unidades)"),
    "stock_cost": metric("Estoque custo", "SUM(estoque_medio * avg_price_cost)"),
    "stock_qty": metric("Estoque qtd", "SUM(estoque_unidades)"),
    "giro": metric("Giro", "AVG(giro) FILTER (WHERE giro > 0)"),
    "osa": metric("OSA", "100.0 * (1 - SUM(qtd_problemas_osa) / NULLIF(SUM(qtd_item_ativo_osa), 0))"),
    "osa_loss": metric("Perda OSA", "SUM(qtd_perda_osa) * AVG(avg_sales_price)"),
    "osa_critical": metric("Itens críticos OSA", "COUNT(DISTINCT CASE WHEN qtd_problemas_osa_m0 > 0 AND max_tp_activity_level = 'F' THEN opportunity_key END)"),
    "osa_risk": metric("Itens risco OSA", "COUNT(DISTINCT CASE WHEN qtd_problemas_osa_m0 > 0 AND max_tp_activity_level = 'S' THEN opportunity_key END)"),
    "roi": metric("ROI", "100.0 * ((CASE WHEN SUM(faturamento) > 0 THEN SUM(faturamento) ELSE SUM(volume_unidades * avg_sales_price) END) - SUM(volume_unidades * avg_price_cost)) / NULLIF(SUM(estoque_medio * avg_price_cost), 0)"),
    "markup": metric("Markup", "100.0 * (CASE WHEN SUM(faturamento) > 0 THEN SUM(faturamento) ELSE SUM(volume_unidades * avg_sales_price) END) / NULLIF(SUM(volume_unidades * avg_price_cost), 0)"),
}


OVERVIEW_M = {
    "sellout": metric("Venda sell out", "SUM(sellout_sum)"),
    "cost": metric("Venda custo", "SUM(sales_cost_sum)"),
    "sales_qty": metric("Venda qtd", "SUM(sales_qty_sum)"),
    "stock_cost": metric("Estoque custo", "SUM(stock_cost_sum)"),
    "stock_qty": metric("Estoque qtd", "SUM(stock_qty_sum)"),
    "giro": metric("Giro", "SUM(giro_sum_positive) / NULLIF(SUM(giro_count_positive), 0)"),
    "osa": metric("OSA", "100.0 * (1 - SUM(osa_problem_sum) / NULLIF(SUM(osa_active_sum), 0))"),
    "osa_loss": metric("Perda OSA", "SUM(osa_loss_sum)"),
    "osa_critical": metric("Itens críticos OSA", "SUM(osa_critical_count)"),
    "osa_risk": metric("Itens risco OSA", "SUM(osa_risk_count)"),
    # Additive components retained separately so U3M ratios can be
    # recalculated over the whole three-month context instead of averaging
    # already aggregated monthly values in React.
    "giro_sum": metric("Giro soma positiva", "SUM(giro_sum_positive)"),
    "giro_count": metric("Giro contagem positiva", "SUM(giro_count_positive)"),
    "osa_problem": metric("OSA problemas", "SUM(osa_problem_sum)"),
    "osa_active": metric("OSA ativos", "SUM(osa_active_sum)"),
}


ROI_COMPONENTS = [
    OVERVIEW_M["sellout"], OVERVIEW_M["cost"], OVERVIEW_M["stock_cost"],
]


MARKUP_COMPONENTS = [OVERVIEW_M["sellout"], OVERVIEW_M["cost"]]


TVD_DAILY = {
    "tvd": metric("TVD", "SUM(tvd)"),
    "critical": metric("Itens críticos TVD", "SUM(itens_criticos_tvd)"),
    "risk": metric("Itens risco TVD", "SUM(itens_risco_tvd)"),
}


IVD_DAILY = {
    "ivd": metric("IVD", "SUM(ivd)"),
    "critical": metric("Itens críticos IVD", "SUM(itens_criticos_ivd)"),
    "risk": metric("Itens risco IVD", "SUM(itens_risco_ivd)"),
}


def headline_semantic_sql(detail_table: str, summary_table: str) -> str:
    """Use daily totals by default and retain detail for dimensional filters."""
    checks = " or ".join(
        f"get_filters('{column}')" for column in HEADLINE_FILTER_COLUMNS
    )
    return (
        f"{{% set has_dimension_filter = {checks} %}}\n"
        "{% if has_dimension_filter %}\n"
        f"SELECT * FROM gold.{detail_table}\n"
        "{% else %}\n"
        f"SELECT * FROM gold.{summary_table}\n"
        "{% endif %}"
    )


def overview_semantic_sql() -> str:
    """Certified conversion/SUMX path with a compact unfiltered branch."""
    checks = " or ".join(
        f"get_filters('{column}')" for column in HEADLINE_FILTER_COLUMNS
        if column not in ("unidade_medida", "deposito", "hierarquia_4")
    )
    predicates = _jinja_filter_predicates("h")
    return (
        "{% set conversion_filters = get_filters('nm_measure') %}\n"
        f"{{% set has_detail_filter = {checks} %}}\n"
        "{% if conversion_filters|length != 1 or conversion_filters[0].get('val')|length != 1 %}\n"
        "SELECT * FROM gold.nr_overview_semantic_default WHERE 1=0\n"
        "{% elif has_detail_filter %}\n"
        "WITH history_filtered AS (SELECT h.* FROM gold.nr_overview_history h WHERE 1=1\n" + predicates + "\n),\n"
        "history_region AS (SELECT data,id_customer,tp_activity_level,CASE tp_activity_level WHEN 'F' THEN 'Fast Mover' WHEN 'S' THEN 'Slow Mover' WHEN 'U' THEN 'Ultra Slow Mover' WHEN 'N' THEN 'New Mover' ELSE NULL END activity_level,regiao,"
        "SUM(COALESCE(faturamento,0))::float8 faturamento_sum,SUM(COALESCE(volume_unidades,0))::float8 volume_sum,SUM(COALESCE(avg_sales_price,0))::float8 price_sum,COUNT(avg_sales_price)::bigint price_count,"
        "SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 sales_cost_sum,SUM(COALESCE(estoque_medio,0)*COALESCE(avg_price_cost,0))::float8 stock_cost_sum,SUM(COALESCE(estoque_unidades,0))::float8 stock_units_sum,"
        "SUM(CASE WHEN COALESCE(giro,0)>0 THEN giro ELSE 0 END)::float8 giro_sum_positive,COUNT(giro) FILTER (WHERE COALESCE(giro,0)>0)::bigint giro_count_positive,SUM(COALESCE(qtd_problemas_osa,0))::bigint osa_problem_sum,SUM(COALESCE(qtd_item_ativo_osa,0))::bigint osa_active_sum "
        "FROM history_filtered GROUP BY data,id_customer,tp_activity_level,regiao),\n"
        "factor_region AS (SELECT h.data,h.id_customer,h.tp_activity_level,h.regiao,c.nm_measure,MAX(c.conversion_rate)::float8 conversion_rate FROM (SELECT DISTINCT data,id_customer,tp_activity_level,regiao,id_item FROM history_filtered) h JOIN gold.dim_conversao c ON c.id_customer=h.id_customer AND c.id_item::text=h.id_item GROUP BY h.data,h.id_customer,h.tp_activity_level,h.regiao,c.nm_measure),\n"
        "expanded AS (SELECT r.*,f.nm_measure,f.conversion_rate FROM history_region r JOIN factor_region f ON f.data=r.data AND f.id_customer=r.id_customer AND f.tp_activity_level IS NOT DISTINCT FROM r.tp_activity_level AND f.regiao IS NOT DISTINCT FROM r.regiao UNION ALL SELECT r.*,'valor'::text,NULL::float8 FROM history_region r),\n"
        "region_scoped AS (SELECT e.*,'activity'::text semantic_scope FROM expanded e UNION ALL SELECT data,id_customer,NULL::text tp_activity_level,NULL::text activity_level,regiao,SUM(faturamento_sum)::float8,SUM(volume_sum)::float8,SUM(price_sum)::float8,SUM(price_count)::bigint,SUM(sales_cost_sum)::float8,SUM(stock_cost_sum)::float8,SUM(stock_units_sum)::float8,SUM(giro_sum_positive)::float8,SUM(giro_count_positive)::bigint,SUM(osa_problem_sum)::bigint,SUM(osa_active_sum)::bigint,nm_measure,MAX(conversion_rate)::float8,'all'::text FROM expanded GROUP BY data,id_customer,regiao,nm_measure)\n"
        "SELECT data,id_customer,tp_activity_level,activity_level,nm_measure,semantic_scope,TRUE semantic_precomputed,"
        "SUM(CASE WHEN faturamento_sum>0 THEN faturamento_sum WHEN conversion_rate IS NOT NULL AND price_count>0 THEN (volume_sum*conversion_rate)*((price_sum/price_count)*conversion_rate) ELSE 0 END)::float8 sellout_sum,"
        "SUM(sales_cost_sum)::float8 sales_cost_sum,CASE WHEN nm_measure='valor' THEN SUM(faturamento_sum) ELSE SUM(volume_sum)*MAX(conversion_rate) END::float8 sales_qty_sum,"
        "SUM(stock_cost_sum)::float8 stock_cost_sum,CASE WHEN nm_measure='valor' THEN SUM(faturamento_sum) ELSE SUM(stock_units_sum)*MAX(conversion_rate) END::float8 stock_qty_sum,"
        "SUM(giro_sum_positive)::float8 giro_sum_positive,SUM(giro_count_positive)::bigint giro_count_positive,SUM(osa_problem_sum)::bigint osa_problem_sum,SUM(osa_active_sum)::bigint osa_active_sum,"
        "NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,NULL::text tipo_local,NULL::text loja,NULL::text regiao,NULL::text item,NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,NULL::text hierarquia_3 "
        "FROM region_scoped WHERE semantic_scope='all' OR activity_level IS NOT NULL GROUP BY data,id_customer,tp_activity_level,activity_level,nm_measure,semantic_scope\n"
        "{% else %}\nSELECT * FROM gold.nr_overview_semantic_default\n{% endif %}"
    )


def osa_semantic_sql() -> str:
    """OSA loss source and row-count alerts, with identical filter context."""
    checks = " or ".join(
        f"get_filters('{column}')" for column in HEADLINE_FILTER_COLUMNS
        if column not in ("unidade_medida", "deposito", "hierarquia_4")
    )
    history_filters = _jinja_filter_predicates("h")
    cause_filters = _jinja_filter_predicates("c", "o.max_tp_activity_level")
    task_filters = _jinja_filter_predicates("o", "max_tp_activity_level", {
        "rede": "l.rede", "bandeira": "l.bandeira", "uf": "l.uf", "cidade": "l.cidade",
        "tipo_local": "l.tipo_local", "loja": "l.loja", "regiao": "l.regiao",
        "descricao_marca": "i.descricao_marca", "hierarquia_1": "i.hierarquia_1",
        "hierarquia_2": "i.hierarquia_2", "hierarquia_3": "i.hierarquia_3", "item": "i.item",
    })
    return (
        "{% set conversion_filters = get_filters('nm_measure') %}\n"
        f"{{% set has_detail_filter = {checks} %}}\n"
        "{% if conversion_filters|length != 1 or conversion_filters[0].get('val')|length != 1 %}\n"
        "SELECT * FROM gold.nr_osa_semantic_default WHERE 1=0\n"
        "{% elif has_detail_filter %}\n"
        "WITH history_filtered AS (SELECT h.* FROM gold.nr_overview_history h WHERE 1=1\n" + history_filters + "\n),"
        "ratio AS (SELECT data,id_customer,SUM(COALESCE(qtd_problemas_osa,0))::bigint osa_problem_sum,SUM(COALESCE(qtd_item_ativo_osa,0))::bigint osa_active_sum FROM history_filtered GROUP BY data,id_customer),"
        "cause_filtered AS (SELECT c.*,o.max_tp_activity_level FROM gold.nr_osa_industry_causes c LEFT JOIN gold.calculo_oportunidades o ON o.id_customer=c.id_customer AND o.id_location=c.id_location AND o.id_item=c.id_item WHERE 1=1\n" + cause_filters + "\n),"
        "loss_base AS (SELECT data,id_customer,SUM(COALESCE(qtd_perda_osa,0))::float8 loss_qty_sum,SUM(COALESCE(preco_medio,0))::float8 price_sum,COUNT(preco_medio)::bigint price_count FROM cause_filtered GROUP BY data,id_customer),"
        "loss_factor AS (SELECT f.data,f.id_customer,c.nm_measure,MAX(c.conversion_rate)::float8 conversion_rate FROM (SELECT DISTINCT data,id_customer,id_item FROM cause_filtered) f JOIN gold.dim_conversao c ON c.id_customer=f.id_customer AND c.id_item::text=f.id_item GROUP BY f.data,f.id_customer,c.nm_measure),"
        "loss AS (SELECT b.data,b.id_customer,f.nm_measure,CASE WHEN b.price_count>0 THEN b.loss_qty_sum*f.conversion_rate*(b.price_sum/b.price_count) ELSE NULL END::float8 osa_loss_sum FROM loss_base b JOIN loss_factor f USING(data,id_customer) UNION ALL SELECT data,id_customer,'valor'::text,NULL::float8 FROM loss_base),"
        "tasks AS (SELECT o.id_customer,COUNT(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0,0)>0 AND a.nm_activity_level='Fast Mover')::bigint osa_critical_count,COUNT(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0,0)>0 AND o.max_tp_activity_level='S')::bigint osa_risk_count FROM gold.calculo_oportunidades o LEFT JOIN gold.dim_local l ON l.id_customer=o.id_customer AND l.id_location=o.id_location LEFT JOIN gold.dim_itens i ON i.id_customer=o.id_customer AND i.id_item=o.id_item LEFT JOIN gold.dim_nivel_atividade a ON a.id_customer=o.id_customer AND a.tp_activity_level=o.max_tp_activity_level WHERE 1=1\n" + task_filters + "\nGROUP BY o.id_customer),"
        "latest AS (SELECT id_customer,MAX(data) data FROM history_filtered GROUP BY id_customer) "
        "SELECT r.data,r.id_customer,l.nm_measure,r.osa_problem_sum,r.osa_active_sum,l.osa_loss_sum,CASE WHEN r.data=d.data THEN COALESCE(t.osa_critical_count,0) ELSE 0 END osa_critical_count,CASE WHEN r.data=d.data THEN COALESCE(t.osa_risk_count,0) ELSE 0 END osa_risk_count FROM ratio r JOIN loss l USING(data,id_customer) JOIN latest d USING(id_customer) LEFT JOIN tasks t USING(id_customer)\n"
        "{% else %}\nSELECT * FROM gold.nr_osa_semantic_default\n{% endif %}"
    )
