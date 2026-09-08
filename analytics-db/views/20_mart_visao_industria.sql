CREATE OR REPLACE VIEW gold.vw_mart_visao_industria AS
WITH opportunities AS (
    SELECT DISTINCT ON (id_customer, id_location, id_item)
        id_customer,
        id_location,
        id_item,
        regra_critico,
        tvd AS oportunidade_tvd,
        ivd AS oportunidade_ivd
    FROM gold.calculo_oportunidades
    ORDER BY id_customer, id_location, id_item, _silver_refreshed_at DESC NULLS LAST
)
SELECT
    f.id_customer,
    f.id_time,
    f.id_time::date AS data,
    f.id_item,
    f.id_location,
    f.tp_activity_level,
    f.tvd_simplificado,
    f.ivd_simplificado,
    l.id_retailer,
    l.rede,
    l.bandeira,
    l.uf,
    l.cidade,
    l.tipo_local,
    l.loja,
    i.item,
    i.descricao_marca,
    i.hierarquia_1,
    i.hierarquia_2,
    i.hierarquia_3,
    i.hierarquia_4,
    CONCAT_WS('|', f.id_customer::text, f.id_location, f.id_item) AS opportunity_key,
    o.regra_critico,
    o.oportunidade_tvd,
    o.oportunidade_ivd
FROM gold.fato_ivd_tvd f
LEFT JOIN gold.dim_local l
  ON l.id_customer = f.id_customer
 AND l.id_location = f.id_location
LEFT JOIN gold.dim_itens i
  ON i.id_customer = f.id_customer
 AND i.id_item = f.id_item
LEFT JOIN opportunities o
  ON o.id_customer = f.id_customer
 AND o.id_location = f.id_location
 AND o.id_item = f.id_item;

COMMENT ON VIEW gold.vw_mart_visao_industria IS
'Dataset compartilhado da V9: RLS por id_customer e filtros nativos por rede, local e item.';
