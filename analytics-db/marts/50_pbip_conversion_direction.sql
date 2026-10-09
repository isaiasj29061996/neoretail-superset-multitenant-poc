-- Corrected direction proven by TOM: AP -> DIM_CONVERSAO -> DIM_ITENS -> facts.
-- Only PBIP serving objects; existing Gold base, previous marts and all indices are retained.
BEGIN;
CREATE INDEX IF NOT EXISTS ix_nr_pbip_history_customer_item ON gold.nr_pbip_overview_history(id_customer,id_item);
CREATE INDEX IF NOT EXISTS ix_nr_pbip_causes_customer_item ON gold.nr_pbip_osa_industry_causes(id_customer,id_item);
CREATE MATERIALIZED VIEW IF NOT EXISTS gold.nr_pbip_overview_semantic_v3 AS
(




WITH pbip_quantity_by_activity AS MATERIALIZED (
SELECT h.data,h.id_customer,h.tp_activity_level,f.nm_measure,SUM(h.volume_unidades*f.conversion_rate)::float8 AS quantity_sum FROM gold.nr_pbip_overview_history h JOIN (SELECT c.id_customer,c.nm_measure,MAX(CASE WHEN false THEN NULL ELSE c.conversion_rate END) AS conversion_rate
 FROM gold.dim_conversao c
 WHERE c.id_customer=290
 GROUP BY c.id_customer,c.nm_measure) f ON f.id_customer=h.id_customer WHERE h.id_customer=290  AND EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=h.id_customer AND CAST(ci.id_item AS TEXT)=CAST(h.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('hectolitro') AND pbip_conv.nm_measure <> 'valor') AND f.nm_measure IN ('hectolitro') GROUP BY h.data,h.id_customer,h.tp_activity_level,f.nm_measure)
SELECT b.data,b.id_customer,b.tp_activity_level,b.activity_level,b.nm_measure,b.semantic_scope,b.semantic_precomputed,b.sellout_sum,b.sales_cost_sum,(SELECT SUM(q.quantity_sum) FROM pbip_quantity_by_activity q WHERE q.data=b.data AND q.id_customer=b.id_customer AND q.nm_measure=b.nm_measure AND (b.semantic_scope='all' OR q.tp_activity_level IS NOT DISTINCT FROM b.tp_activity_level)) AS sales_qty_sum,b.stock_cost_sum,b.stock_qty_sum,b.giro_sum_positive,b.giro_count_positive,b.osa_problem_sum,b.osa_active_sum,b.rede,b.bandeira,b.uf,b.cidade,b.tipo_local,b.loja,b.regiao,b.item,b.descricao_marca,b.hierarquia_1,b.hierarquia_2,b.hierarquia_3 FROM (


WITH history_filtered AS (SELECT h.* FROM gold.nr_pbip_overview_history h WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=h.id_customer AND CAST(ci.id_item AS TEXT)=CAST(h.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('hectolitro') AND pbip_conv.nm_measure <> 'valor') AND 1=1

),
history_region AS (SELECT data,id_customer,tp_activity_level,CASE tp_activity_level WHEN 'F' THEN 'Fast Mover' WHEN 'S' THEN 'Slow Mover' WHEN 'U' THEN 'Ultra Slow Mover' WHEN 'N' THEN 'New Mover' ELSE NULL END activity_level,regiao,SUM(COALESCE(faturamento,0))::float8 faturamento_sum,SUM(volume_unidades)::float8 volume_sum,SUM(COALESCE(avg_sales_price,0))::float8 price_sum,COUNT(avg_sales_price)::bigint price_count,SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 sales_cost_sum,SUM(COALESCE(estoque_medio,0)*COALESCE(avg_price_cost,0))::float8 stock_cost_sum,SUM(estoque_unidades)::float8 stock_units_sum,SUM(CASE WHEN COALESCE(giro,0)>0 THEN giro ELSE 0 END)::float8 giro_sum_positive,COUNT(giro) FILTER (WHERE COALESCE(giro,0)>0)::bigint giro_count_positive,SUM(qtd_problemas_osa)::bigint osa_problem_sum,SUM(qtd_item_ativo_osa)::bigint osa_active_sum FROM history_filtered GROUP BY data,id_customer,tp_activity_level,regiao),
factor_region AS (SELECT h.data,h.id_customer,h.tp_activity_level,h.regiao,m.nm_measure,f.conversion_rate FROM (SELECT DISTINCT data,id_customer,tp_activity_level,regiao FROM history_filtered) h CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290) m LEFT JOIN (SELECT c.id_customer,c.nm_measure,MAX(CASE WHEN false THEN NULL ELSE c.conversion_rate END) AS conversion_rate
 FROM gold.dim_conversao c
 WHERE c.id_customer=290
 GROUP BY c.id_customer,c.nm_measure) f ON f.id_customer=h.id_customer AND f.nm_measure=m.nm_measure),
expanded AS (SELECT r.*,f.nm_measure,f.conversion_rate FROM history_region r JOIN factor_region f ON f.data=r.data AND f.id_customer=r.id_customer AND f.tp_activity_level IS NOT DISTINCT FROM r.tp_activity_level AND f.regiao IS NOT DISTINCT FROM r.regiao UNION ALL SELECT r.*,'valor'::text,NULL::float8 FROM history_region r),
region_scoped AS (SELECT e.*,'activity'::text semantic_scope FROM expanded e UNION ALL SELECT data,id_customer,NULL::text tp_activity_level,NULL::text activity_level,regiao,SUM(faturamento_sum)::float8,SUM(volume_sum)::float8,SUM(price_sum)::float8,SUM(price_count)::bigint,SUM(sales_cost_sum)::float8,SUM(stock_cost_sum)::float8,SUM(stock_units_sum)::float8,SUM(giro_sum_positive)::float8,SUM(giro_count_positive)::bigint,SUM(osa_problem_sum)::bigint,SUM(osa_active_sum)::bigint,nm_measure,MAX(conversion_rate)::float8,'all'::text FROM expanded GROUP BY data,id_customer,regiao,nm_measure)
SELECT data,id_customer,tp_activity_level,activity_level,nm_measure,semantic_scope,TRUE semantic_precomputed,SUM(CASE WHEN faturamento_sum>0 THEN faturamento_sum WHEN conversion_rate IS NOT NULL AND price_count>0 THEN (volume_sum*conversion_rate)*((price_sum/price_count)*conversion_rate) ELSE NULL END)::float8 sellout_sum,SUM(sales_cost_sum)::float8 sales_cost_sum,CASE WHEN nm_measure='valor' THEN SUM(faturamento_sum) ELSE SUM(volume_sum)*MAX(conversion_rate) END::float8 sales_qty_sum,SUM(stock_cost_sum)::float8 stock_cost_sum,CASE WHEN nm_measure='valor' THEN SUM(faturamento_sum) ELSE SUM(stock_units_sum)*MAX(conversion_rate) END::float8 stock_qty_sum,SUM(giro_sum_positive)::float8 giro_sum_positive,SUM(giro_count_positive)::bigint giro_count_positive,SUM(osa_problem_sum)::bigint osa_problem_sum,SUM(osa_active_sum)::bigint osa_active_sum,NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,NULL::text tipo_local,NULL::text loja,NULL::text regiao,NULL::text item,NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,NULL::text hierarquia_3 FROM region_scoped WHERE semantic_scope='all' OR activity_level IS NOT NULL GROUP BY data,id_customer,tp_activity_level,activity_level,nm_measure,semantic_scope

) b WHERE b.nm_measure IN ('hectolitro'))
UNION ALL
(




WITH pbip_quantity_by_activity AS MATERIALIZED (
SELECT h.data,h.id_customer,h.tp_activity_level,f.nm_measure,SUM(h.volume_unidades*f.conversion_rate)::float8 AS quantity_sum FROM gold.nr_pbip_overview_history h JOIN (SELECT c.id_customer,c.nm_measure,MAX(CASE WHEN false THEN NULL ELSE c.conversion_rate END) AS conversion_rate
 FROM gold.dim_conversao c
 WHERE c.id_customer=290
 GROUP BY c.id_customer,c.nm_measure) f ON f.id_customer=h.id_customer WHERE h.id_customer=290  AND EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=h.id_customer AND CAST(ci.id_item AS TEXT)=CAST(h.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('libra') AND pbip_conv.nm_measure <> 'valor') AND f.nm_measure IN ('libra') GROUP BY h.data,h.id_customer,h.tp_activity_level,f.nm_measure)
SELECT b.data,b.id_customer,b.tp_activity_level,b.activity_level,b.nm_measure,b.semantic_scope,b.semantic_precomputed,b.sellout_sum,b.sales_cost_sum,(SELECT SUM(q.quantity_sum) FROM pbip_quantity_by_activity q WHERE q.data=b.data AND q.id_customer=b.id_customer AND q.nm_measure=b.nm_measure AND (b.semantic_scope='all' OR q.tp_activity_level IS NOT DISTINCT FROM b.tp_activity_level)) AS sales_qty_sum,b.stock_cost_sum,b.stock_qty_sum,b.giro_sum_positive,b.giro_count_positive,b.osa_problem_sum,b.osa_active_sum,b.rede,b.bandeira,b.uf,b.cidade,b.tipo_local,b.loja,b.regiao,b.item,b.descricao_marca,b.hierarquia_1,b.hierarquia_2,b.hierarquia_3 FROM (


WITH history_filtered AS (SELECT h.* FROM gold.nr_pbip_overview_history h WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=h.id_customer AND CAST(ci.id_item AS TEXT)=CAST(h.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('libra') AND pbip_conv.nm_measure <> 'valor') AND 1=1

),
history_region AS (SELECT data,id_customer,tp_activity_level,CASE tp_activity_level WHEN 'F' THEN 'Fast Mover' WHEN 'S' THEN 'Slow Mover' WHEN 'U' THEN 'Ultra Slow Mover' WHEN 'N' THEN 'New Mover' ELSE NULL END activity_level,regiao,SUM(COALESCE(faturamento,0))::float8 faturamento_sum,SUM(volume_unidades)::float8 volume_sum,SUM(COALESCE(avg_sales_price,0))::float8 price_sum,COUNT(avg_sales_price)::bigint price_count,SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 sales_cost_sum,SUM(COALESCE(estoque_medio,0)*COALESCE(avg_price_cost,0))::float8 stock_cost_sum,SUM(estoque_unidades)::float8 stock_units_sum,SUM(CASE WHEN COALESCE(giro,0)>0 THEN giro ELSE 0 END)::float8 giro_sum_positive,COUNT(giro) FILTER (WHERE COALESCE(giro,0)>0)::bigint giro_count_positive,SUM(qtd_problemas_osa)::bigint osa_problem_sum,SUM(qtd_item_ativo_osa)::bigint osa_active_sum FROM history_filtered GROUP BY data,id_customer,tp_activity_level,regiao),
factor_region AS (SELECT h.data,h.id_customer,h.tp_activity_level,h.regiao,m.nm_measure,f.conversion_rate FROM (SELECT DISTINCT data,id_customer,tp_activity_level,regiao FROM history_filtered) h CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290) m LEFT JOIN (SELECT c.id_customer,c.nm_measure,MAX(CASE WHEN false THEN NULL ELSE c.conversion_rate END) AS conversion_rate
 FROM gold.dim_conversao c
 WHERE c.id_customer=290
 GROUP BY c.id_customer,c.nm_measure) f ON f.id_customer=h.id_customer AND f.nm_measure=m.nm_measure),
expanded AS (SELECT r.*,f.nm_measure,f.conversion_rate FROM history_region r JOIN factor_region f ON f.data=r.data AND f.id_customer=r.id_customer AND f.tp_activity_level IS NOT DISTINCT FROM r.tp_activity_level AND f.regiao IS NOT DISTINCT FROM r.regiao UNION ALL SELECT r.*,'valor'::text,NULL::float8 FROM history_region r),
region_scoped AS (SELECT e.*,'activity'::text semantic_scope FROM expanded e UNION ALL SELECT data,id_customer,NULL::text tp_activity_level,NULL::text activity_level,regiao,SUM(faturamento_sum)::float8,SUM(volume_sum)::float8,SUM(price_sum)::float8,SUM(price_count)::bigint,SUM(sales_cost_sum)::float8,SUM(stock_cost_sum)::float8,SUM(stock_units_sum)::float8,SUM(giro_sum_positive)::float8,SUM(giro_count_positive)::bigint,SUM(osa_problem_sum)::bigint,SUM(osa_active_sum)::bigint,nm_measure,MAX(conversion_rate)::float8,'all'::text FROM expanded GROUP BY data,id_customer,regiao,nm_measure)
SELECT data,id_customer,tp_activity_level,activity_level,nm_measure,semantic_scope,TRUE semantic_precomputed,SUM(CASE WHEN faturamento_sum>0 THEN faturamento_sum WHEN conversion_rate IS NOT NULL AND price_count>0 THEN (volume_sum*conversion_rate)*((price_sum/price_count)*conversion_rate) ELSE NULL END)::float8 sellout_sum,SUM(sales_cost_sum)::float8 sales_cost_sum,CASE WHEN nm_measure='valor' THEN SUM(faturamento_sum) ELSE SUM(volume_sum)*MAX(conversion_rate) END::float8 sales_qty_sum,SUM(stock_cost_sum)::float8 stock_cost_sum,CASE WHEN nm_measure='valor' THEN SUM(faturamento_sum) ELSE SUM(stock_units_sum)*MAX(conversion_rate) END::float8 stock_qty_sum,SUM(giro_sum_positive)::float8 giro_sum_positive,SUM(giro_count_positive)::bigint giro_count_positive,SUM(osa_problem_sum)::bigint osa_problem_sum,SUM(osa_active_sum)::bigint osa_active_sum,NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,NULL::text tipo_local,NULL::text loja,NULL::text regiao,NULL::text item,NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,NULL::text hierarquia_3 FROM region_scoped WHERE semantic_scope='all' OR activity_level IS NOT NULL GROUP BY data,id_customer,tp_activity_level,activity_level,nm_measure,semantic_scope

) b WHERE b.nm_measure IN ('libra'))
UNION ALL
(




WITH pbip_quantity_by_activity AS MATERIALIZED (
SELECT h.data,h.id_customer,h.tp_activity_level,f.nm_measure,SUM(h.volume_unidades*f.conversion_rate)::float8 AS quantity_sum FROM gold.nr_pbip_overview_history h JOIN (SELECT c.id_customer,c.nm_measure,MAX(CASE WHEN false THEN NULL ELSE c.conversion_rate END) AS conversion_rate
 FROM gold.dim_conversao c
 WHERE c.id_customer=290
 GROUP BY c.id_customer,c.nm_measure) f ON f.id_customer=h.id_customer WHERE h.id_customer=290  AND EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=h.id_customer AND CAST(ci.id_item AS TEXT)=CAST(h.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('litro') AND pbip_conv.nm_measure <> 'valor') AND f.nm_measure IN ('litro') GROUP BY h.data,h.id_customer,h.tp_activity_level,f.nm_measure)
SELECT b.data,b.id_customer,b.tp_activity_level,b.activity_level,b.nm_measure,b.semantic_scope,b.semantic_precomputed,b.sellout_sum,b.sales_cost_sum,(SELECT SUM(q.quantity_sum) FROM pbip_quantity_by_activity q WHERE q.data=b.data AND q.id_customer=b.id_customer AND q.nm_measure=b.nm_measure AND (b.semantic_scope='all' OR q.tp_activity_level IS NOT DISTINCT FROM b.tp_activity_level)) AS sales_qty_sum,b.stock_cost_sum,b.stock_qty_sum,b.giro_sum_positive,b.giro_count_positive,b.osa_problem_sum,b.osa_active_sum,b.rede,b.bandeira,b.uf,b.cidade,b.tipo_local,b.loja,b.regiao,b.item,b.descricao_marca,b.hierarquia_1,b.hierarquia_2,b.hierarquia_3 FROM (


WITH history_filtered AS (SELECT h.* FROM gold.nr_pbip_overview_history h WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=h.id_customer AND CAST(ci.id_item AS TEXT)=CAST(h.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('litro') AND pbip_conv.nm_measure <> 'valor') AND 1=1

),
history_region AS (SELECT data,id_customer,tp_activity_level,CASE tp_activity_level WHEN 'F' THEN 'Fast Mover' WHEN 'S' THEN 'Slow Mover' WHEN 'U' THEN 'Ultra Slow Mover' WHEN 'N' THEN 'New Mover' ELSE NULL END activity_level,regiao,SUM(COALESCE(faturamento,0))::float8 faturamento_sum,SUM(volume_unidades)::float8 volume_sum,SUM(COALESCE(avg_sales_price,0))::float8 price_sum,COUNT(avg_sales_price)::bigint price_count,SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 sales_cost_sum,SUM(COALESCE(estoque_medio,0)*COALESCE(avg_price_cost,0))::float8 stock_cost_sum,SUM(estoque_unidades)::float8 stock_units_sum,SUM(CASE WHEN COALESCE(giro,0)>0 THEN giro ELSE 0 END)::float8 giro_sum_positive,COUNT(giro) FILTER (WHERE COALESCE(giro,0)>0)::bigint giro_count_positive,SUM(qtd_problemas_osa)::bigint osa_problem_sum,SUM(qtd_item_ativo_osa)::bigint osa_active_sum FROM history_filtered GROUP BY data,id_customer,tp_activity_level,regiao),
factor_region AS (SELECT h.data,h.id_customer,h.tp_activity_level,h.regiao,m.nm_measure,f.conversion_rate FROM (SELECT DISTINCT data,id_customer,tp_activity_level,regiao FROM history_filtered) h CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290) m LEFT JOIN (SELECT c.id_customer,c.nm_measure,MAX(CASE WHEN false THEN NULL ELSE c.conversion_rate END) AS conversion_rate
 FROM gold.dim_conversao c
 WHERE c.id_customer=290
 GROUP BY c.id_customer,c.nm_measure) f ON f.id_customer=h.id_customer AND f.nm_measure=m.nm_measure),
expanded AS (SELECT r.*,f.nm_measure,f.conversion_rate FROM history_region r JOIN factor_region f ON f.data=r.data AND f.id_customer=r.id_customer AND f.tp_activity_level IS NOT DISTINCT FROM r.tp_activity_level AND f.regiao IS NOT DISTINCT FROM r.regiao UNION ALL SELECT r.*,'valor'::text,NULL::float8 FROM history_region r),
region_scoped AS (SELECT e.*,'activity'::text semantic_scope FROM expanded e UNION ALL SELECT data,id_customer,NULL::text tp_activity_level,NULL::text activity_level,regiao,SUM(faturamento_sum)::float8,SUM(volume_sum)::float8,SUM(price_sum)::float8,SUM(price_count)::bigint,SUM(sales_cost_sum)::float8,SUM(stock_cost_sum)::float8,SUM(stock_units_sum)::float8,SUM(giro_sum_positive)::float8,SUM(giro_count_positive)::bigint,SUM(osa_problem_sum)::bigint,SUM(osa_active_sum)::bigint,nm_measure,MAX(conversion_rate)::float8,'all'::text FROM expanded GROUP BY data,id_customer,regiao,nm_measure)
SELECT data,id_customer,tp_activity_level,activity_level,nm_measure,semantic_scope,TRUE semantic_precomputed,SUM(CASE WHEN faturamento_sum>0 THEN faturamento_sum WHEN conversion_rate IS NOT NULL AND price_count>0 THEN (volume_sum*conversion_rate)*((price_sum/price_count)*conversion_rate) ELSE NULL END)::float8 sellout_sum,SUM(sales_cost_sum)::float8 sales_cost_sum,CASE WHEN nm_measure='valor' THEN SUM(faturamento_sum) ELSE SUM(volume_sum)*MAX(conversion_rate) END::float8 sales_qty_sum,SUM(stock_cost_sum)::float8 stock_cost_sum,CASE WHEN nm_measure='valor' THEN SUM(faturamento_sum) ELSE SUM(stock_units_sum)*MAX(conversion_rate) END::float8 stock_qty_sum,SUM(giro_sum_positive)::float8 giro_sum_positive,SUM(giro_count_positive)::bigint giro_count_positive,SUM(osa_problem_sum)::bigint osa_problem_sum,SUM(osa_active_sum)::bigint osa_active_sum,NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,NULL::text tipo_local,NULL::text loja,NULL::text regiao,NULL::text item,NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,NULL::text hierarquia_3 FROM region_scoped WHERE semantic_scope='all' OR activity_level IS NOT NULL GROUP BY data,id_customer,tp_activity_level,activity_level,nm_measure,semantic_scope

) b WHERE b.nm_measure IN ('litro'))
UNION ALL
(




WITH pbip_quantity_by_activity AS MATERIALIZED (
SELECT h.data,h.id_customer,h.tp_activity_level,f.nm_measure,SUM(h.volume_unidades*f.conversion_rate)::float8 AS quantity_sum FROM gold.nr_pbip_overview_history h JOIN (SELECT c.id_customer,c.nm_measure,MAX(CASE WHEN false THEN NULL ELSE c.conversion_rate END) AS conversion_rate
 FROM gold.dim_conversao c
 WHERE c.id_customer=290
 GROUP BY c.id_customer,c.nm_measure) f ON f.id_customer=h.id_customer WHERE h.id_customer=290  AND EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=h.id_customer AND CAST(ci.id_item AS TEXT)=CAST(h.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('quilograma') AND pbip_conv.nm_measure <> 'valor') AND f.nm_measure IN ('quilograma') GROUP BY h.data,h.id_customer,h.tp_activity_level,f.nm_measure)
SELECT b.data,b.id_customer,b.tp_activity_level,b.activity_level,b.nm_measure,b.semantic_scope,b.semantic_precomputed,b.sellout_sum,b.sales_cost_sum,(SELECT SUM(q.quantity_sum) FROM pbip_quantity_by_activity q WHERE q.data=b.data AND q.id_customer=b.id_customer AND q.nm_measure=b.nm_measure AND (b.semantic_scope='all' OR q.tp_activity_level IS NOT DISTINCT FROM b.tp_activity_level)) AS sales_qty_sum,b.stock_cost_sum,b.stock_qty_sum,b.giro_sum_positive,b.giro_count_positive,b.osa_problem_sum,b.osa_active_sum,b.rede,b.bandeira,b.uf,b.cidade,b.tipo_local,b.loja,b.regiao,b.item,b.descricao_marca,b.hierarquia_1,b.hierarquia_2,b.hierarquia_3 FROM (


WITH history_filtered AS (SELECT h.* FROM gold.nr_pbip_overview_history h WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=h.id_customer AND CAST(ci.id_item AS TEXT)=CAST(h.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('quilograma') AND pbip_conv.nm_measure <> 'valor') AND 1=1

),
history_region AS (SELECT data,id_customer,tp_activity_level,CASE tp_activity_level WHEN 'F' THEN 'Fast Mover' WHEN 'S' THEN 'Slow Mover' WHEN 'U' THEN 'Ultra Slow Mover' WHEN 'N' THEN 'New Mover' ELSE NULL END activity_level,regiao,SUM(COALESCE(faturamento,0))::float8 faturamento_sum,SUM(volume_unidades)::float8 volume_sum,SUM(COALESCE(avg_sales_price,0))::float8 price_sum,COUNT(avg_sales_price)::bigint price_count,SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 sales_cost_sum,SUM(COALESCE(estoque_medio,0)*COALESCE(avg_price_cost,0))::float8 stock_cost_sum,SUM(estoque_unidades)::float8 stock_units_sum,SUM(CASE WHEN COALESCE(giro,0)>0 THEN giro ELSE 0 END)::float8 giro_sum_positive,COUNT(giro) FILTER (WHERE COALESCE(giro,0)>0)::bigint giro_count_positive,SUM(qtd_problemas_osa)::bigint osa_problem_sum,SUM(qtd_item_ativo_osa)::bigint osa_active_sum FROM history_filtered GROUP BY data,id_customer,tp_activity_level,regiao),
factor_region AS (SELECT h.data,h.id_customer,h.tp_activity_level,h.regiao,m.nm_measure,f.conversion_rate FROM (SELECT DISTINCT data,id_customer,tp_activity_level,regiao FROM history_filtered) h CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290) m LEFT JOIN (SELECT c.id_customer,c.nm_measure,MAX(CASE WHEN false THEN NULL ELSE c.conversion_rate END) AS conversion_rate
 FROM gold.dim_conversao c
 WHERE c.id_customer=290
 GROUP BY c.id_customer,c.nm_measure) f ON f.id_customer=h.id_customer AND f.nm_measure=m.nm_measure),
expanded AS (SELECT r.*,f.nm_measure,f.conversion_rate FROM history_region r JOIN factor_region f ON f.data=r.data AND f.id_customer=r.id_customer AND f.tp_activity_level IS NOT DISTINCT FROM r.tp_activity_level AND f.regiao IS NOT DISTINCT FROM r.regiao UNION ALL SELECT r.*,'valor'::text,NULL::float8 FROM history_region r),
region_scoped AS (SELECT e.*,'activity'::text semantic_scope FROM expanded e UNION ALL SELECT data,id_customer,NULL::text tp_activity_level,NULL::text activity_level,regiao,SUM(faturamento_sum)::float8,SUM(volume_sum)::float8,SUM(price_sum)::float8,SUM(price_count)::bigint,SUM(sales_cost_sum)::float8,SUM(stock_cost_sum)::float8,SUM(stock_units_sum)::float8,SUM(giro_sum_positive)::float8,SUM(giro_count_positive)::bigint,SUM(osa_problem_sum)::bigint,SUM(osa_active_sum)::bigint,nm_measure,MAX(conversion_rate)::float8,'all'::text FROM expanded GROUP BY data,id_customer,regiao,nm_measure)
SELECT data,id_customer,tp_activity_level,activity_level,nm_measure,semantic_scope,TRUE semantic_precomputed,SUM(CASE WHEN faturamento_sum>0 THEN faturamento_sum WHEN conversion_rate IS NOT NULL AND price_count>0 THEN (volume_sum*conversion_rate)*((price_sum/price_count)*conversion_rate) ELSE NULL END)::float8 sellout_sum,SUM(sales_cost_sum)::float8 sales_cost_sum,CASE WHEN nm_measure='valor' THEN SUM(faturamento_sum) ELSE SUM(volume_sum)*MAX(conversion_rate) END::float8 sales_qty_sum,SUM(stock_cost_sum)::float8 stock_cost_sum,CASE WHEN nm_measure='valor' THEN SUM(faturamento_sum) ELSE SUM(stock_units_sum)*MAX(conversion_rate) END::float8 stock_qty_sum,SUM(giro_sum_positive)::float8 giro_sum_positive,SUM(giro_count_positive)::bigint giro_count_positive,SUM(osa_problem_sum)::bigint osa_problem_sum,SUM(osa_active_sum)::bigint osa_active_sum,NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,NULL::text tipo_local,NULL::text loja,NULL::text regiao,NULL::text item,NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,NULL::text hierarquia_3 FROM region_scoped WHERE semantic_scope='all' OR activity_level IS NOT NULL GROUP BY data,id_customer,tp_activity_level,activity_level,nm_measure,semantic_scope

) b WHERE b.nm_measure IN ('quilograma'))
UNION ALL
(




WITH pbip_quantity_by_activity AS MATERIALIZED (
SELECT h.data,h.id_customer,h.tp_activity_level,f.nm_measure,SUM(h.volume_unidades*f.conversion_rate)::float8 AS quantity_sum FROM gold.nr_pbip_overview_history h JOIN (SELECT c.id_customer,c.nm_measure,MAX(CASE WHEN false THEN NULL ELSE c.conversion_rate END) AS conversion_rate
 FROM gold.dim_conversao c
 WHERE c.id_customer=290
 GROUP BY c.id_customer,c.nm_measure) f ON f.id_customer=h.id_customer WHERE h.id_customer=290  AND EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=h.id_customer AND CAST(ci.id_item AS TEXT)=CAST(h.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('tonelada') AND pbip_conv.nm_measure <> 'valor') AND f.nm_measure IN ('tonelada') GROUP BY h.data,h.id_customer,h.tp_activity_level,f.nm_measure)
SELECT b.data,b.id_customer,b.tp_activity_level,b.activity_level,b.nm_measure,b.semantic_scope,b.semantic_precomputed,b.sellout_sum,b.sales_cost_sum,(SELECT SUM(q.quantity_sum) FROM pbip_quantity_by_activity q WHERE q.data=b.data AND q.id_customer=b.id_customer AND q.nm_measure=b.nm_measure AND (b.semantic_scope='all' OR q.tp_activity_level IS NOT DISTINCT FROM b.tp_activity_level)) AS sales_qty_sum,b.stock_cost_sum,b.stock_qty_sum,b.giro_sum_positive,b.giro_count_positive,b.osa_problem_sum,b.osa_active_sum,b.rede,b.bandeira,b.uf,b.cidade,b.tipo_local,b.loja,b.regiao,b.item,b.descricao_marca,b.hierarquia_1,b.hierarquia_2,b.hierarquia_3 FROM (


WITH history_filtered AS (SELECT h.* FROM gold.nr_pbip_overview_history h WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=h.id_customer AND CAST(ci.id_item AS TEXT)=CAST(h.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('tonelada') AND pbip_conv.nm_measure <> 'valor') AND 1=1

),
history_region AS (SELECT data,id_customer,tp_activity_level,CASE tp_activity_level WHEN 'F' THEN 'Fast Mover' WHEN 'S' THEN 'Slow Mover' WHEN 'U' THEN 'Ultra Slow Mover' WHEN 'N' THEN 'New Mover' ELSE NULL END activity_level,regiao,SUM(COALESCE(faturamento,0))::float8 faturamento_sum,SUM(volume_unidades)::float8 volume_sum,SUM(COALESCE(avg_sales_price,0))::float8 price_sum,COUNT(avg_sales_price)::bigint price_count,SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 sales_cost_sum,SUM(COALESCE(estoque_medio,0)*COALESCE(avg_price_cost,0))::float8 stock_cost_sum,SUM(estoque_unidades)::float8 stock_units_sum,SUM(CASE WHEN COALESCE(giro,0)>0 THEN giro ELSE 0 END)::float8 giro_sum_positive,COUNT(giro) FILTER (WHERE COALESCE(giro,0)>0)::bigint giro_count_positive,SUM(qtd_problemas_osa)::bigint osa_problem_sum,SUM(qtd_item_ativo_osa)::bigint osa_active_sum FROM history_filtered GROUP BY data,id_customer,tp_activity_level,regiao),
factor_region AS (SELECT h.data,h.id_customer,h.tp_activity_level,h.regiao,m.nm_measure,f.conversion_rate FROM (SELECT DISTINCT data,id_customer,tp_activity_level,regiao FROM history_filtered) h CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290) m LEFT JOIN (SELECT c.id_customer,c.nm_measure,MAX(CASE WHEN false THEN NULL ELSE c.conversion_rate END) AS conversion_rate
 FROM gold.dim_conversao c
 WHERE c.id_customer=290
 GROUP BY c.id_customer,c.nm_measure) f ON f.id_customer=h.id_customer AND f.nm_measure=m.nm_measure),
expanded AS (SELECT r.*,f.nm_measure,f.conversion_rate FROM history_region r JOIN factor_region f ON f.data=r.data AND f.id_customer=r.id_customer AND f.tp_activity_level IS NOT DISTINCT FROM r.tp_activity_level AND f.regiao IS NOT DISTINCT FROM r.regiao UNION ALL SELECT r.*,'valor'::text,NULL::float8 FROM history_region r),
region_scoped AS (SELECT e.*,'activity'::text semantic_scope FROM expanded e UNION ALL SELECT data,id_customer,NULL::text tp_activity_level,NULL::text activity_level,regiao,SUM(faturamento_sum)::float8,SUM(volume_sum)::float8,SUM(price_sum)::float8,SUM(price_count)::bigint,SUM(sales_cost_sum)::float8,SUM(stock_cost_sum)::float8,SUM(stock_units_sum)::float8,SUM(giro_sum_positive)::float8,SUM(giro_count_positive)::bigint,SUM(osa_problem_sum)::bigint,SUM(osa_active_sum)::bigint,nm_measure,MAX(conversion_rate)::float8,'all'::text FROM expanded GROUP BY data,id_customer,regiao,nm_measure)
SELECT data,id_customer,tp_activity_level,activity_level,nm_measure,semantic_scope,TRUE semantic_precomputed,SUM(CASE WHEN faturamento_sum>0 THEN faturamento_sum WHEN conversion_rate IS NOT NULL AND price_count>0 THEN (volume_sum*conversion_rate)*((price_sum/price_count)*conversion_rate) ELSE NULL END)::float8 sellout_sum,SUM(sales_cost_sum)::float8 sales_cost_sum,CASE WHEN nm_measure='valor' THEN SUM(faturamento_sum) ELSE SUM(volume_sum)*MAX(conversion_rate) END::float8 sales_qty_sum,SUM(stock_cost_sum)::float8 stock_cost_sum,CASE WHEN nm_measure='valor' THEN SUM(faturamento_sum) ELSE SUM(stock_units_sum)*MAX(conversion_rate) END::float8 stock_qty_sum,SUM(giro_sum_positive)::float8 giro_sum_positive,SUM(giro_count_positive)::bigint giro_count_positive,SUM(osa_problem_sum)::bigint osa_problem_sum,SUM(osa_active_sum)::bigint osa_active_sum,NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,NULL::text tipo_local,NULL::text loja,NULL::text regiao,NULL::text item,NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,NULL::text hierarquia_3 FROM region_scoped WHERE semantic_scope='all' OR activity_level IS NOT NULL GROUP BY data,id_customer,tp_activity_level,activity_level,nm_measure,semantic_scope

) b WHERE b.nm_measure IN ('tonelada'))
UNION ALL
(




WITH pbip_quantity_by_activity AS MATERIALIZED (
SELECT h.data,h.id_customer,h.tp_activity_level,f.nm_measure,SUM(h.volume_unidades*f.conversion_rate)::float8 AS quantity_sum FROM gold.nr_pbip_overview_history h JOIN (SELECT c.id_customer,c.nm_measure,MAX(CASE WHEN false THEN NULL ELSE c.conversion_rate END) AS conversion_rate
 FROM gold.dim_conversao c
 WHERE c.id_customer=290
 GROUP BY c.id_customer,c.nm_measure) f ON f.id_customer=h.id_customer WHERE h.id_customer=290  AND EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=h.id_customer AND CAST(ci.id_item AS TEXT)=CAST(h.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('unidade') AND pbip_conv.nm_measure <> 'valor') AND f.nm_measure IN ('unidade') GROUP BY h.data,h.id_customer,h.tp_activity_level,f.nm_measure)
SELECT b.data,b.id_customer,b.tp_activity_level,b.activity_level,b.nm_measure,b.semantic_scope,b.semantic_precomputed,b.sellout_sum,b.sales_cost_sum,(SELECT SUM(q.quantity_sum) FROM pbip_quantity_by_activity q WHERE q.data=b.data AND q.id_customer=b.id_customer AND q.nm_measure=b.nm_measure AND (b.semantic_scope='all' OR q.tp_activity_level IS NOT DISTINCT FROM b.tp_activity_level)) AS sales_qty_sum,b.stock_cost_sum,b.stock_qty_sum,b.giro_sum_positive,b.giro_count_positive,b.osa_problem_sum,b.osa_active_sum,b.rede,b.bandeira,b.uf,b.cidade,b.tipo_local,b.loja,b.regiao,b.item,b.descricao_marca,b.hierarquia_1,b.hierarquia_2,b.hierarquia_3 FROM (


WITH history_filtered AS (SELECT h.* FROM gold.nr_pbip_overview_history h WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=h.id_customer AND CAST(ci.id_item AS TEXT)=CAST(h.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('unidade') AND pbip_conv.nm_measure <> 'valor') AND 1=1

),
history_region AS (SELECT data,id_customer,tp_activity_level,CASE tp_activity_level WHEN 'F' THEN 'Fast Mover' WHEN 'S' THEN 'Slow Mover' WHEN 'U' THEN 'Ultra Slow Mover' WHEN 'N' THEN 'New Mover' ELSE NULL END activity_level,regiao,SUM(COALESCE(faturamento,0))::float8 faturamento_sum,SUM(volume_unidades)::float8 volume_sum,SUM(COALESCE(avg_sales_price,0))::float8 price_sum,COUNT(avg_sales_price)::bigint price_count,SUM(COALESCE(volume_unidades,0)*COALESCE(avg_price_cost,0))::float8 sales_cost_sum,SUM(COALESCE(estoque_medio,0)*COALESCE(avg_price_cost,0))::float8 stock_cost_sum,SUM(estoque_unidades)::float8 stock_units_sum,SUM(CASE WHEN COALESCE(giro,0)>0 THEN giro ELSE 0 END)::float8 giro_sum_positive,COUNT(giro) FILTER (WHERE COALESCE(giro,0)>0)::bigint giro_count_positive,SUM(qtd_problemas_osa)::bigint osa_problem_sum,SUM(qtd_item_ativo_osa)::bigint osa_active_sum FROM history_filtered GROUP BY data,id_customer,tp_activity_level,regiao),
factor_region AS (SELECT h.data,h.id_customer,h.tp_activity_level,h.regiao,m.nm_measure,f.conversion_rate FROM (SELECT DISTINCT data,id_customer,tp_activity_level,regiao FROM history_filtered) h CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290) m LEFT JOIN (SELECT c.id_customer,c.nm_measure,MAX(CASE WHEN false THEN NULL ELSE c.conversion_rate END) AS conversion_rate
 FROM gold.dim_conversao c
 WHERE c.id_customer=290
 GROUP BY c.id_customer,c.nm_measure) f ON f.id_customer=h.id_customer AND f.nm_measure=m.nm_measure),
expanded AS (SELECT r.*,f.nm_measure,f.conversion_rate FROM history_region r JOIN factor_region f ON f.data=r.data AND f.id_customer=r.id_customer AND f.tp_activity_level IS NOT DISTINCT FROM r.tp_activity_level AND f.regiao IS NOT DISTINCT FROM r.regiao UNION ALL SELECT r.*,'valor'::text,NULL::float8 FROM history_region r),
region_scoped AS (SELECT e.*,'activity'::text semantic_scope FROM expanded e UNION ALL SELECT data,id_customer,NULL::text tp_activity_level,NULL::text activity_level,regiao,SUM(faturamento_sum)::float8,SUM(volume_sum)::float8,SUM(price_sum)::float8,SUM(price_count)::bigint,SUM(sales_cost_sum)::float8,SUM(stock_cost_sum)::float8,SUM(stock_units_sum)::float8,SUM(giro_sum_positive)::float8,SUM(giro_count_positive)::bigint,SUM(osa_problem_sum)::bigint,SUM(osa_active_sum)::bigint,nm_measure,MAX(conversion_rate)::float8,'all'::text FROM expanded GROUP BY data,id_customer,regiao,nm_measure)
SELECT data,id_customer,tp_activity_level,activity_level,nm_measure,semantic_scope,TRUE semantic_precomputed,SUM(CASE WHEN faturamento_sum>0 THEN faturamento_sum WHEN conversion_rate IS NOT NULL AND price_count>0 THEN (volume_sum*conversion_rate)*((price_sum/price_count)*conversion_rate) ELSE NULL END)::float8 sellout_sum,SUM(sales_cost_sum)::float8 sales_cost_sum,CASE WHEN nm_measure='valor' THEN SUM(faturamento_sum) ELSE SUM(volume_sum)*MAX(conversion_rate) END::float8 sales_qty_sum,SUM(stock_cost_sum)::float8 stock_cost_sum,CASE WHEN nm_measure='valor' THEN SUM(faturamento_sum) ELSE SUM(stock_units_sum)*MAX(conversion_rate) END::float8 stock_qty_sum,SUM(giro_sum_positive)::float8 giro_sum_positive,SUM(giro_count_positive)::bigint giro_count_positive,SUM(osa_problem_sum)::bigint osa_problem_sum,SUM(osa_active_sum)::bigint osa_active_sum,NULL::text rede,NULL::text bandeira,NULL::text uf,NULL::text cidade,NULL::text tipo_local,NULL::text loja,NULL::text regiao,NULL::text item,NULL::text descricao_marca,NULL::text hierarquia_1,NULL::text hierarquia_2,NULL::text hierarquia_3 FROM region_scoped WHERE semantic_scope='all' OR activity_level IS NOT NULL GROUP BY data,id_customer,tp_activity_level,activity_level,nm_measure,semantic_scope

) b WHERE b.nm_measure IN ('unidade'));
CREATE UNIQUE INDEX IF NOT EXISTS ux_nr_pbip_overview_semantic_v3_key ON gold.nr_pbip_overview_semantic_v3(id_customer,data,nm_measure,semantic_scope,tp_activity_level);
CREATE MATERIALIZED VIEW IF NOT EXISTS gold.nr_pbip_osa_semantic_v3 AS
(




SELECT * FROM (


WITH history_filtered AS (SELECT h.* FROM gold.nr_pbip_overview_history h WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=h.id_customer AND CAST(ci.id_item AS TEXT)=CAST(h.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('hectolitro') AND pbip_conv.nm_measure <> 'valor') AND 1=1

),ratio AS (SELECT data,id_customer,SUM(qtd_problemas_osa)::bigint osa_problem_sum,SUM(qtd_item_ativo_osa)::bigint osa_active_sum FROM history_filtered GROUP BY data,id_customer),cause_filtered AS (SELECT c.* FROM gold.nr_pbip_osa_industry_causes c WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=c.id_customer AND CAST(ci.id_item AS TEXT)=CAST(c.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('hectolitro') AND pbip_conv.nm_measure <> 'valor') AND 1=1

),loss_base AS (SELECT data,id_customer,SUM(qtd_perda_osa)::float8 loss_qty_sum,SUM(preco_medio)::float8 price_sum,COUNT(preco_medio)::bigint price_count FROM cause_filtered GROUP BY data,id_customer),loss_factor AS (SELECT h.data,h.id_customer,m.nm_measure,f.conversion_rate FROM (SELECT DISTINCT data,id_customer FROM cause_filtered) h CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290) m LEFT JOIN (SELECT c.id_customer,c.nm_measure,MAX(CASE WHEN false THEN NULL ELSE c.conversion_rate END) AS conversion_rate
 FROM gold.dim_conversao c
 WHERE c.id_customer=290
 GROUP BY c.id_customer,c.nm_measure) f ON f.id_customer=h.id_customer AND f.nm_measure=m.nm_measure),loss AS (SELECT b.data,b.id_customer,f.nm_measure,b.loss_qty_sum,b.price_sum,b.price_count,f.conversion_rate,CASE WHEN b.price_count>0 THEN b.loss_qty_sum*f.conversion_rate*(b.price_sum/b.price_count) ELSE NULL END::float8 osa_loss_sum FROM loss_base b JOIN loss_factor f USING(data,id_customer) UNION ALL SELECT data,id_customer,'valor'::text,loss_qty_sum,price_sum,price_count,NULL::float8,NULL::float8 FROM loss_base),tasks AS (SELECT o.id_customer,COUNT(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0,0)>0 AND a.nm_activity_level='Fast Mover')::bigint osa_critical_count,COUNT(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0,0)>0 AND o.max_tp_activity_level='S')::bigint osa_risk_count FROM gold.calculo_oportunidades o LEFT JOIN gold.dim_local l ON l.id_customer=o.id_customer AND l.id_location=o.id_location LEFT JOIN gold.dim_itens i ON i.id_customer=o.id_customer AND i.id_item=o.id_item LEFT JOIN gold.dim_nivel_atividade a ON a.id_customer=o.id_customer AND a.tp_activity_level=o.max_tp_activity_level WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=o.id_customer AND CAST(ci.id_item AS TEXT)=CAST(o.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('hectolitro') AND pbip_conv.nm_measure <> 'valor') AND 1=1
AND EXISTS (
 SELECT 1 FROM gold.dim_local pl
 WHERE pl.id_customer=o.id_customer AND pl.id_location=o.id_location
   AND pl.rede IS NOT NULL




 
   AND EXISTS (
     SELECT 1 FROM gold.dim_catalogo_local pc
     WHERE pc.id_customer=pl.id_customer AND pc.cnpj IS NOT DISTINCT FROM pl.cnpj
       AND pc.rede <> 'GPA'

 
       AND EXISTS (SELECT 1 FROM gold.dim_local ac
                   WHERE ac.id_customer=pc.id_customer AND ac.id_retailer=pc.id_retailer)
   )
)






GROUP BY o.id_customer),latest AS (SELECT id_customer,MAX(data) data FROM history_filtered GROUP BY id_customer) SELECT r.data,r.id_customer,m.nm_measure,r.osa_problem_sum,r.osa_active_sum,l.osa_loss_sum,l.loss_qty_sum,l.price_sum,l.price_count,l.conversion_rate,CASE WHEN r.data=d.data THEN COALESCE(t.osa_critical_count,0) ELSE 0 END osa_critical_count,CASE WHEN r.data=d.data THEN COALESCE(t.osa_risk_count,0) ELSE 0 END osa_risk_count FROM ratio r CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290 UNION SELECT 'valor') m LEFT JOIN loss l ON l.data=r.data AND l.id_customer=r.id_customer AND l.nm_measure=m.nm_measure JOIN latest d ON d.id_customer=r.id_customer LEFT JOIN tasks t ON t.id_customer=r.id_customer

) pbip_selected_context WHERE nm_measure IN ('hectolitro'))
UNION ALL
(




SELECT * FROM (


WITH history_filtered AS (SELECT h.* FROM gold.nr_pbip_overview_history h WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=h.id_customer AND CAST(ci.id_item AS TEXT)=CAST(h.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('libra') AND pbip_conv.nm_measure <> 'valor') AND 1=1

),ratio AS (SELECT data,id_customer,SUM(qtd_problemas_osa)::bigint osa_problem_sum,SUM(qtd_item_ativo_osa)::bigint osa_active_sum FROM history_filtered GROUP BY data,id_customer),cause_filtered AS (SELECT c.* FROM gold.nr_pbip_osa_industry_causes c WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=c.id_customer AND CAST(ci.id_item AS TEXT)=CAST(c.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('libra') AND pbip_conv.nm_measure <> 'valor') AND 1=1

),loss_base AS (SELECT data,id_customer,SUM(qtd_perda_osa)::float8 loss_qty_sum,SUM(preco_medio)::float8 price_sum,COUNT(preco_medio)::bigint price_count FROM cause_filtered GROUP BY data,id_customer),loss_factor AS (SELECT h.data,h.id_customer,m.nm_measure,f.conversion_rate FROM (SELECT DISTINCT data,id_customer FROM cause_filtered) h CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290) m LEFT JOIN (SELECT c.id_customer,c.nm_measure,MAX(CASE WHEN false THEN NULL ELSE c.conversion_rate END) AS conversion_rate
 FROM gold.dim_conversao c
 WHERE c.id_customer=290
 GROUP BY c.id_customer,c.nm_measure) f ON f.id_customer=h.id_customer AND f.nm_measure=m.nm_measure),loss AS (SELECT b.data,b.id_customer,f.nm_measure,b.loss_qty_sum,b.price_sum,b.price_count,f.conversion_rate,CASE WHEN b.price_count>0 THEN b.loss_qty_sum*f.conversion_rate*(b.price_sum/b.price_count) ELSE NULL END::float8 osa_loss_sum FROM loss_base b JOIN loss_factor f USING(data,id_customer) UNION ALL SELECT data,id_customer,'valor'::text,loss_qty_sum,price_sum,price_count,NULL::float8,NULL::float8 FROM loss_base),tasks AS (SELECT o.id_customer,COUNT(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0,0)>0 AND a.nm_activity_level='Fast Mover')::bigint osa_critical_count,COUNT(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0,0)>0 AND o.max_tp_activity_level='S')::bigint osa_risk_count FROM gold.calculo_oportunidades o LEFT JOIN gold.dim_local l ON l.id_customer=o.id_customer AND l.id_location=o.id_location LEFT JOIN gold.dim_itens i ON i.id_customer=o.id_customer AND i.id_item=o.id_item LEFT JOIN gold.dim_nivel_atividade a ON a.id_customer=o.id_customer AND a.tp_activity_level=o.max_tp_activity_level WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=o.id_customer AND CAST(ci.id_item AS TEXT)=CAST(o.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('libra') AND pbip_conv.nm_measure <> 'valor') AND 1=1
AND EXISTS (
 SELECT 1 FROM gold.dim_local pl
 WHERE pl.id_customer=o.id_customer AND pl.id_location=o.id_location
   AND pl.rede IS NOT NULL




 
   AND EXISTS (
     SELECT 1 FROM gold.dim_catalogo_local pc
     WHERE pc.id_customer=pl.id_customer AND pc.cnpj IS NOT DISTINCT FROM pl.cnpj
       AND pc.rede <> 'GPA'

 
       AND EXISTS (SELECT 1 FROM gold.dim_local ac
                   WHERE ac.id_customer=pc.id_customer AND ac.id_retailer=pc.id_retailer)
   )
)






GROUP BY o.id_customer),latest AS (SELECT id_customer,MAX(data) data FROM history_filtered GROUP BY id_customer) SELECT r.data,r.id_customer,m.nm_measure,r.osa_problem_sum,r.osa_active_sum,l.osa_loss_sum,l.loss_qty_sum,l.price_sum,l.price_count,l.conversion_rate,CASE WHEN r.data=d.data THEN COALESCE(t.osa_critical_count,0) ELSE 0 END osa_critical_count,CASE WHEN r.data=d.data THEN COALESCE(t.osa_risk_count,0) ELSE 0 END osa_risk_count FROM ratio r CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290 UNION SELECT 'valor') m LEFT JOIN loss l ON l.data=r.data AND l.id_customer=r.id_customer AND l.nm_measure=m.nm_measure JOIN latest d ON d.id_customer=r.id_customer LEFT JOIN tasks t ON t.id_customer=r.id_customer

) pbip_selected_context WHERE nm_measure IN ('libra'))
UNION ALL
(




SELECT * FROM (


WITH history_filtered AS (SELECT h.* FROM gold.nr_pbip_overview_history h WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=h.id_customer AND CAST(ci.id_item AS TEXT)=CAST(h.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('litro') AND pbip_conv.nm_measure <> 'valor') AND 1=1

),ratio AS (SELECT data,id_customer,SUM(qtd_problemas_osa)::bigint osa_problem_sum,SUM(qtd_item_ativo_osa)::bigint osa_active_sum FROM history_filtered GROUP BY data,id_customer),cause_filtered AS (SELECT c.* FROM gold.nr_pbip_osa_industry_causes c WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=c.id_customer AND CAST(ci.id_item AS TEXT)=CAST(c.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('litro') AND pbip_conv.nm_measure <> 'valor') AND 1=1

),loss_base AS (SELECT data,id_customer,SUM(qtd_perda_osa)::float8 loss_qty_sum,SUM(preco_medio)::float8 price_sum,COUNT(preco_medio)::bigint price_count FROM cause_filtered GROUP BY data,id_customer),loss_factor AS (SELECT h.data,h.id_customer,m.nm_measure,f.conversion_rate FROM (SELECT DISTINCT data,id_customer FROM cause_filtered) h CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290) m LEFT JOIN (SELECT c.id_customer,c.nm_measure,MAX(CASE WHEN false THEN NULL ELSE c.conversion_rate END) AS conversion_rate
 FROM gold.dim_conversao c
 WHERE c.id_customer=290
 GROUP BY c.id_customer,c.nm_measure) f ON f.id_customer=h.id_customer AND f.nm_measure=m.nm_measure),loss AS (SELECT b.data,b.id_customer,f.nm_measure,b.loss_qty_sum,b.price_sum,b.price_count,f.conversion_rate,CASE WHEN b.price_count>0 THEN b.loss_qty_sum*f.conversion_rate*(b.price_sum/b.price_count) ELSE NULL END::float8 osa_loss_sum FROM loss_base b JOIN loss_factor f USING(data,id_customer) UNION ALL SELECT data,id_customer,'valor'::text,loss_qty_sum,price_sum,price_count,NULL::float8,NULL::float8 FROM loss_base),tasks AS (SELECT o.id_customer,COUNT(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0,0)>0 AND a.nm_activity_level='Fast Mover')::bigint osa_critical_count,COUNT(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0,0)>0 AND o.max_tp_activity_level='S')::bigint osa_risk_count FROM gold.calculo_oportunidades o LEFT JOIN gold.dim_local l ON l.id_customer=o.id_customer AND l.id_location=o.id_location LEFT JOIN gold.dim_itens i ON i.id_customer=o.id_customer AND i.id_item=o.id_item LEFT JOIN gold.dim_nivel_atividade a ON a.id_customer=o.id_customer AND a.tp_activity_level=o.max_tp_activity_level WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=o.id_customer AND CAST(ci.id_item AS TEXT)=CAST(o.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('litro') AND pbip_conv.nm_measure <> 'valor') AND 1=1
AND EXISTS (
 SELECT 1 FROM gold.dim_local pl
 WHERE pl.id_customer=o.id_customer AND pl.id_location=o.id_location
   AND pl.rede IS NOT NULL




 
   AND EXISTS (
     SELECT 1 FROM gold.dim_catalogo_local pc
     WHERE pc.id_customer=pl.id_customer AND pc.cnpj IS NOT DISTINCT FROM pl.cnpj
       AND pc.rede <> 'GPA'

 
       AND EXISTS (SELECT 1 FROM gold.dim_local ac
                   WHERE ac.id_customer=pc.id_customer AND ac.id_retailer=pc.id_retailer)
   )
)






GROUP BY o.id_customer),latest AS (SELECT id_customer,MAX(data) data FROM history_filtered GROUP BY id_customer) SELECT r.data,r.id_customer,m.nm_measure,r.osa_problem_sum,r.osa_active_sum,l.osa_loss_sum,l.loss_qty_sum,l.price_sum,l.price_count,l.conversion_rate,CASE WHEN r.data=d.data THEN COALESCE(t.osa_critical_count,0) ELSE 0 END osa_critical_count,CASE WHEN r.data=d.data THEN COALESCE(t.osa_risk_count,0) ELSE 0 END osa_risk_count FROM ratio r CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290 UNION SELECT 'valor') m LEFT JOIN loss l ON l.data=r.data AND l.id_customer=r.id_customer AND l.nm_measure=m.nm_measure JOIN latest d ON d.id_customer=r.id_customer LEFT JOIN tasks t ON t.id_customer=r.id_customer

) pbip_selected_context WHERE nm_measure IN ('litro'))
UNION ALL
(




SELECT * FROM (


WITH history_filtered AS (SELECT h.* FROM gold.nr_pbip_overview_history h WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=h.id_customer AND CAST(ci.id_item AS TEXT)=CAST(h.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('quilograma') AND pbip_conv.nm_measure <> 'valor') AND 1=1

),ratio AS (SELECT data,id_customer,SUM(qtd_problemas_osa)::bigint osa_problem_sum,SUM(qtd_item_ativo_osa)::bigint osa_active_sum FROM history_filtered GROUP BY data,id_customer),cause_filtered AS (SELECT c.* FROM gold.nr_pbip_osa_industry_causes c WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=c.id_customer AND CAST(ci.id_item AS TEXT)=CAST(c.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('quilograma') AND pbip_conv.nm_measure <> 'valor') AND 1=1

),loss_base AS (SELECT data,id_customer,SUM(qtd_perda_osa)::float8 loss_qty_sum,SUM(preco_medio)::float8 price_sum,COUNT(preco_medio)::bigint price_count FROM cause_filtered GROUP BY data,id_customer),loss_factor AS (SELECT h.data,h.id_customer,m.nm_measure,f.conversion_rate FROM (SELECT DISTINCT data,id_customer FROM cause_filtered) h CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290) m LEFT JOIN (SELECT c.id_customer,c.nm_measure,MAX(CASE WHEN false THEN NULL ELSE c.conversion_rate END) AS conversion_rate
 FROM gold.dim_conversao c
 WHERE c.id_customer=290
 GROUP BY c.id_customer,c.nm_measure) f ON f.id_customer=h.id_customer AND f.nm_measure=m.nm_measure),loss AS (SELECT b.data,b.id_customer,f.nm_measure,b.loss_qty_sum,b.price_sum,b.price_count,f.conversion_rate,CASE WHEN b.price_count>0 THEN b.loss_qty_sum*f.conversion_rate*(b.price_sum/b.price_count) ELSE NULL END::float8 osa_loss_sum FROM loss_base b JOIN loss_factor f USING(data,id_customer) UNION ALL SELECT data,id_customer,'valor'::text,loss_qty_sum,price_sum,price_count,NULL::float8,NULL::float8 FROM loss_base),tasks AS (SELECT o.id_customer,COUNT(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0,0)>0 AND a.nm_activity_level='Fast Mover')::bigint osa_critical_count,COUNT(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0,0)>0 AND o.max_tp_activity_level='S')::bigint osa_risk_count FROM gold.calculo_oportunidades o LEFT JOIN gold.dim_local l ON l.id_customer=o.id_customer AND l.id_location=o.id_location LEFT JOIN gold.dim_itens i ON i.id_customer=o.id_customer AND i.id_item=o.id_item LEFT JOIN gold.dim_nivel_atividade a ON a.id_customer=o.id_customer AND a.tp_activity_level=o.max_tp_activity_level WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=o.id_customer AND CAST(ci.id_item AS TEXT)=CAST(o.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('quilograma') AND pbip_conv.nm_measure <> 'valor') AND 1=1
AND EXISTS (
 SELECT 1 FROM gold.dim_local pl
 WHERE pl.id_customer=o.id_customer AND pl.id_location=o.id_location
   AND pl.rede IS NOT NULL




 
   AND EXISTS (
     SELECT 1 FROM gold.dim_catalogo_local pc
     WHERE pc.id_customer=pl.id_customer AND pc.cnpj IS NOT DISTINCT FROM pl.cnpj
       AND pc.rede <> 'GPA'

 
       AND EXISTS (SELECT 1 FROM gold.dim_local ac
                   WHERE ac.id_customer=pc.id_customer AND ac.id_retailer=pc.id_retailer)
   )
)






GROUP BY o.id_customer),latest AS (SELECT id_customer,MAX(data) data FROM history_filtered GROUP BY id_customer) SELECT r.data,r.id_customer,m.nm_measure,r.osa_problem_sum,r.osa_active_sum,l.osa_loss_sum,l.loss_qty_sum,l.price_sum,l.price_count,l.conversion_rate,CASE WHEN r.data=d.data THEN COALESCE(t.osa_critical_count,0) ELSE 0 END osa_critical_count,CASE WHEN r.data=d.data THEN COALESCE(t.osa_risk_count,0) ELSE 0 END osa_risk_count FROM ratio r CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290 UNION SELECT 'valor') m LEFT JOIN loss l ON l.data=r.data AND l.id_customer=r.id_customer AND l.nm_measure=m.nm_measure JOIN latest d ON d.id_customer=r.id_customer LEFT JOIN tasks t ON t.id_customer=r.id_customer

) pbip_selected_context WHERE nm_measure IN ('quilograma'))
UNION ALL
(




SELECT * FROM (


WITH history_filtered AS (SELECT h.* FROM gold.nr_pbip_overview_history h WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=h.id_customer AND CAST(ci.id_item AS TEXT)=CAST(h.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('tonelada') AND pbip_conv.nm_measure <> 'valor') AND 1=1

),ratio AS (SELECT data,id_customer,SUM(qtd_problemas_osa)::bigint osa_problem_sum,SUM(qtd_item_ativo_osa)::bigint osa_active_sum FROM history_filtered GROUP BY data,id_customer),cause_filtered AS (SELECT c.* FROM gold.nr_pbip_osa_industry_causes c WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=c.id_customer AND CAST(ci.id_item AS TEXT)=CAST(c.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('tonelada') AND pbip_conv.nm_measure <> 'valor') AND 1=1

),loss_base AS (SELECT data,id_customer,SUM(qtd_perda_osa)::float8 loss_qty_sum,SUM(preco_medio)::float8 price_sum,COUNT(preco_medio)::bigint price_count FROM cause_filtered GROUP BY data,id_customer),loss_factor AS (SELECT h.data,h.id_customer,m.nm_measure,f.conversion_rate FROM (SELECT DISTINCT data,id_customer FROM cause_filtered) h CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290) m LEFT JOIN (SELECT c.id_customer,c.nm_measure,MAX(CASE WHEN false THEN NULL ELSE c.conversion_rate END) AS conversion_rate
 FROM gold.dim_conversao c
 WHERE c.id_customer=290
 GROUP BY c.id_customer,c.nm_measure) f ON f.id_customer=h.id_customer AND f.nm_measure=m.nm_measure),loss AS (SELECT b.data,b.id_customer,f.nm_measure,b.loss_qty_sum,b.price_sum,b.price_count,f.conversion_rate,CASE WHEN b.price_count>0 THEN b.loss_qty_sum*f.conversion_rate*(b.price_sum/b.price_count) ELSE NULL END::float8 osa_loss_sum FROM loss_base b JOIN loss_factor f USING(data,id_customer) UNION ALL SELECT data,id_customer,'valor'::text,loss_qty_sum,price_sum,price_count,NULL::float8,NULL::float8 FROM loss_base),tasks AS (SELECT o.id_customer,COUNT(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0,0)>0 AND a.nm_activity_level='Fast Mover')::bigint osa_critical_count,COUNT(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0,0)>0 AND o.max_tp_activity_level='S')::bigint osa_risk_count FROM gold.calculo_oportunidades o LEFT JOIN gold.dim_local l ON l.id_customer=o.id_customer AND l.id_location=o.id_location LEFT JOIN gold.dim_itens i ON i.id_customer=o.id_customer AND i.id_item=o.id_item LEFT JOIN gold.dim_nivel_atividade a ON a.id_customer=o.id_customer AND a.tp_activity_level=o.max_tp_activity_level WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=o.id_customer AND CAST(ci.id_item AS TEXT)=CAST(o.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('tonelada') AND pbip_conv.nm_measure <> 'valor') AND 1=1
AND EXISTS (
 SELECT 1 FROM gold.dim_local pl
 WHERE pl.id_customer=o.id_customer AND pl.id_location=o.id_location
   AND pl.rede IS NOT NULL




 
   AND EXISTS (
     SELECT 1 FROM gold.dim_catalogo_local pc
     WHERE pc.id_customer=pl.id_customer AND pc.cnpj IS NOT DISTINCT FROM pl.cnpj
       AND pc.rede <> 'GPA'

 
       AND EXISTS (SELECT 1 FROM gold.dim_local ac
                   WHERE ac.id_customer=pc.id_customer AND ac.id_retailer=pc.id_retailer)
   )
)






GROUP BY o.id_customer),latest AS (SELECT id_customer,MAX(data) data FROM history_filtered GROUP BY id_customer) SELECT r.data,r.id_customer,m.nm_measure,r.osa_problem_sum,r.osa_active_sum,l.osa_loss_sum,l.loss_qty_sum,l.price_sum,l.price_count,l.conversion_rate,CASE WHEN r.data=d.data THEN COALESCE(t.osa_critical_count,0) ELSE 0 END osa_critical_count,CASE WHEN r.data=d.data THEN COALESCE(t.osa_risk_count,0) ELSE 0 END osa_risk_count FROM ratio r CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290 UNION SELECT 'valor') m LEFT JOIN loss l ON l.data=r.data AND l.id_customer=r.id_customer AND l.nm_measure=m.nm_measure JOIN latest d ON d.id_customer=r.id_customer LEFT JOIN tasks t ON t.id_customer=r.id_customer

) pbip_selected_context WHERE nm_measure IN ('tonelada'))
UNION ALL
(




SELECT * FROM (


WITH history_filtered AS (SELECT h.* FROM gold.nr_pbip_overview_history h WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=h.id_customer AND CAST(ci.id_item AS TEXT)=CAST(h.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('unidade') AND pbip_conv.nm_measure <> 'valor') AND 1=1

),ratio AS (SELECT data,id_customer,SUM(qtd_problemas_osa)::bigint osa_problem_sum,SUM(qtd_item_ativo_osa)::bigint osa_active_sum FROM history_filtered GROUP BY data,id_customer),cause_filtered AS (SELECT c.* FROM gold.nr_pbip_osa_industry_causes c WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=c.id_customer AND CAST(ci.id_item AS TEXT)=CAST(c.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('unidade') AND pbip_conv.nm_measure <> 'valor') AND 1=1

),loss_base AS (SELECT data,id_customer,SUM(qtd_perda_osa)::float8 loss_qty_sum,SUM(preco_medio)::float8 price_sum,COUNT(preco_medio)::bigint price_count FROM cause_filtered GROUP BY data,id_customer),loss_factor AS (SELECT h.data,h.id_customer,m.nm_measure,f.conversion_rate FROM (SELECT DISTINCT data,id_customer FROM cause_filtered) h CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290) m LEFT JOIN (SELECT c.id_customer,c.nm_measure,MAX(CASE WHEN false THEN NULL ELSE c.conversion_rate END) AS conversion_rate
 FROM gold.dim_conversao c
 WHERE c.id_customer=290
 GROUP BY c.id_customer,c.nm_measure) f ON f.id_customer=h.id_customer AND f.nm_measure=m.nm_measure),loss AS (SELECT b.data,b.id_customer,f.nm_measure,b.loss_qty_sum,b.price_sum,b.price_count,f.conversion_rate,CASE WHEN b.price_count>0 THEN b.loss_qty_sum*f.conversion_rate*(b.price_sum/b.price_count) ELSE NULL END::float8 osa_loss_sum FROM loss_base b JOIN loss_factor f USING(data,id_customer) UNION ALL SELECT data,id_customer,'valor'::text,loss_qty_sum,price_sum,price_count,NULL::float8,NULL::float8 FROM loss_base),tasks AS (SELECT o.id_customer,COUNT(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0,0)>0 AND a.nm_activity_level='Fast Mover')::bigint osa_critical_count,COUNT(o.id_item) FILTER (WHERE COALESCE(o.qtd_problemas_osa_m0,0)>0 AND o.max_tp_activity_level='S')::bigint osa_risk_count FROM gold.calculo_oportunidades o LEFT JOIN gold.dim_local l ON l.id_customer=o.id_customer AND l.id_location=o.id_location LEFT JOIN gold.dim_itens i ON i.id_customer=o.id_customer AND i.id_item=o.id_item LEFT JOIN gold.dim_nivel_atividade a ON a.id_customer=o.id_customer AND a.tp_activity_level=o.max_tp_activity_level WHERE EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=o.id_customer AND CAST(ci.id_item AS TEXT)=CAST(o.id_item AS TEXT)  AND pbip_conv.nm_measure IN ('unidade') AND pbip_conv.nm_measure <> 'valor') AND 1=1
AND EXISTS (
 SELECT 1 FROM gold.dim_local pl
 WHERE pl.id_customer=o.id_customer AND pl.id_location=o.id_location
   AND pl.rede IS NOT NULL




 
   AND EXISTS (
     SELECT 1 FROM gold.dim_catalogo_local pc
     WHERE pc.id_customer=pl.id_customer AND pc.cnpj IS NOT DISTINCT FROM pl.cnpj
       AND pc.rede <> 'GPA'

 
       AND EXISTS (SELECT 1 FROM gold.dim_local ac
                   WHERE ac.id_customer=pc.id_customer AND ac.id_retailer=pc.id_retailer)
   )
)






GROUP BY o.id_customer),latest AS (SELECT id_customer,MAX(data) data FROM history_filtered GROUP BY id_customer) SELECT r.data,r.id_customer,m.nm_measure,r.osa_problem_sum,r.osa_active_sum,l.osa_loss_sum,l.loss_qty_sum,l.price_sum,l.price_count,l.conversion_rate,CASE WHEN r.data=d.data THEN COALESCE(t.osa_critical_count,0) ELSE 0 END osa_critical_count,CASE WHEN r.data=d.data THEN COALESCE(t.osa_risk_count,0) ELSE 0 END osa_risk_count FROM ratio r CROSS JOIN (SELECT DISTINCT nm_measure FROM gold.dim_conversao WHERE id_customer=290 UNION SELECT 'valor') m LEFT JOIN loss l ON l.data=r.data AND l.id_customer=r.id_customer AND l.nm_measure=m.nm_measure JOIN latest d ON d.id_customer=r.id_customer LEFT JOIN tasks t ON t.id_customer=r.id_customer

) pbip_selected_context WHERE nm_measure IN ('unidade'));
CREATE UNIQUE INDEX IF NOT EXISTS ux_nr_pbip_osa_semantic_v3_key ON gold.nr_pbip_osa_semantic_v3(id_customer,data,nm_measure);
CREATE MATERIALIZED VIEW IF NOT EXISTS gold.nr_pbip_giro_v3 AS
WITH filtered AS (SELECT h.* FROM gold.nr_pbip_overview_history h WHERE h.id_customer=290 AND EXISTS (
 SELECT 1 FROM gold.dim_local pl
 WHERE pl.id_customer=h.id_customer AND pl.id_location=h.id_location
   AND pl.rede IS NOT NULL 
   AND EXISTS (
     SELECT 1 FROM gold.dim_catalogo_local pc
     WHERE pc.id_customer=pl.id_customer AND pc.cnpj IS NOT DISTINCT FROM pl.cnpj
       AND pc.rede <> 'GPA' 
       AND EXISTS (SELECT 1 FROM gold.dim_local ac
                   WHERE ac.id_customer=pc.id_customer AND ac.id_retailer=pc.id_retailer)
   )
) AND EXISTS (SELECT 1 FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=h.id_customer AND CAST(ci.id_item AS TEXT)=CAST(h.id_item AS TEXT) AND pbip_conv.nm_measure='unidade'))
 SELECT h.data,h.id_customer,'unidade'::text AS nm_measure,'all'::text AS semantic_scope,NULL::text AS activity_level,SUM(h.giro) FILTER(WHERE h.giro>0)::float8 AS giro_sum_positive,COUNT(h.giro) FILTER(WHERE h.giro>0)::bigint AS giro_count_positive,NULL::text AS rede,NULL::text AS bandeira,NULL::text AS uf,NULL::text AS cidade,NULL::text AS tipo_local,NULL::text AS loja,NULL::text AS regiao,NULL::text AS item,NULL::text AS descricao_marca,NULL::text AS hierarquia_1,NULL::text AS hierarquia_2,NULL::text AS hierarquia_3,NULL::text AS tp_activity_level
 FROM filtered h GROUP BY h.data,h.id_customer
 UNION ALL
 SELECT h.data,h.id_customer,'unidade'::text,'activity'::text,CASE h.tp_activity_level WHEN 'F' THEN 'Fast Mover' WHEN 'S' THEN 'Slow Mover' WHEN 'U' THEN 'Ultra Slow Mover' WHEN 'N' THEN 'New Mover' ELSE NULL END,SUM(h.giro) FILTER(WHERE h.giro>0)::float8 AS giro_sum_positive,COUNT(h.giro) FILTER(WHERE h.giro>0)::bigint AS giro_count_positive,NULL::text AS rede,NULL::text AS bandeira,NULL::text AS uf,NULL::text AS cidade,NULL::text AS tipo_local,NULL::text AS loja,NULL::text AS regiao,NULL::text AS item,NULL::text AS descricao_marca,NULL::text AS hierarquia_1,NULL::text AS hierarquia_2,NULL::text AS hierarquia_3,NULL::text AS tp_activity_level
 FROM filtered h WHERE CASE h.tp_activity_level WHEN 'F' THEN 'Fast Mover' WHEN 'S' THEN 'Slow Mover' WHEN 'U' THEN 'Ultra Slow Mover' WHEN 'N' THEN 'New Mover' ELSE NULL END IS NOT NULL GROUP BY h.data,h.id_customer,CASE h.tp_activity_level WHEN 'F' THEN 'Fast Mover' WHEN 'S' THEN 'Slow Mover' WHEN 'U' THEN 'Ultra Slow Mover' WHEN 'N' THEN 'New Mover' ELSE NULL END;
CREATE UNIQUE INDEX IF NOT EXISTS ux_nr_pbip_giro_v3_key ON gold.nr_pbip_giro_v3(id_customer,data,semantic_scope,activity_level);
COMMIT;
