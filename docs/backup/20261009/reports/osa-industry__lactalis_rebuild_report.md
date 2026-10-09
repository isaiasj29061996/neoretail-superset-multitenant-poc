> Cópia para GitHub: números de origem e identificadores numéricos omitidos. Original integral exige backup externo. Não usar esta cópia como fixture ou SQL executável.

# Reconstrução local LACTALIS — ID [DADO OMITIDO]

Branch: `feat/osa-industry-certification`. Commit: `[DADO OMITIDO]a1[DADO OMITIDO]dc1[DADO OMITIDO]eeabedf9[DADO OMITIDO]ee5[DADO OMITIDO]`.

Execução do zero, sem recuperação dos volumes apagados. Sem merge, push ou alteração de main.

## Origem e isolamento

Fatos: container Azure `neoretail`, prefixo `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/`: [DADO OMITIDO] arquivos, [DADO OMITIDO] bytes, [DADO OMITIDO] linhas. Versões/ETags: [evidência](lactalis_source_versions_current.json).

As dimensões com identidade foram filtradas por ID [DADO OMITIDO] e nome LACTALIS antes de persistir cache ou Bronze. `DIMENSAO_LOCAL` é compartilhada, sem ID de cliente: selecionada pelos varejistas contratados de LACTALIS. Leitura por ranges de Parquet remoto com ETag fixo; blocos compartilhados precisam ser lidos para selecionar linhas, mas a população não selecionada nunca é gravada localmente. Não foi inventado manufacturer_id.

[Paths e schemas Azure](lactalis_source_preflight_current.json) · [seleção das dimensões](scoped_dimensions_2[DADO OMITIDO].json)

## Lake: linhas e identidade

Dimensões Azure identificadas:

- `DIMENSAO/CATALOGO_PRODUTO_GVI.snappy.parquet`: [DADO OMITIDO] linhas na origem, [DADO OMITIDO] bytes.
- `DIMENSAO/DIMENSAO_LOCAL.snappy.parquet`: [DADO OMITIDO] linhas na origem, [DADO OMITIDO] bytes.
- `DIMENSAO/DIMENSAO_CUSTOMER.snappy.parquet`: [DADO OMITIDO] linhas na origem, [DADO OMITIDO] bytes.
- `DIMENSAO/DIMENSAO_CONVERSOES.snappy.parquet`: [DADO OMITIDO] linhas na origem, [DADO OMITIDO] bytes.
- `DIMENSAO/DIMENSAO_CATALOGO_PRODUTOS.snappy.parquet`: [DADO OMITIDO] linhas na origem, [DADO OMITIDO] bytes.
- `DIMENSAO/DIMENSAO_VAREJO_CONTRATADO.snappy.parquet`: [DADO OMITIDO] linhas na origem, [DADO OMITIDO] bytes.

As contagens abaixo são as linhas selecionadas/persistidas; dimensões remotas compartilhadas incluem outros clientes na origem.

### Bronze

[Auditoria completa](lactalis_bronze_isolation.json)

| Tabela | Linhas | ID |
|---|---:|---|
| candidate_customer_daily | [DADO OMITIDO] | [[DADO OMITIDO]] |
| dim_catalogo_produtos_raw | [DADO OMITIDO] | [[DADO OMITIDO]] |
| dim_conversao_raw | [DADO OMITIDO] | [[DADO OMITIDO]] |
| dim_customer_raw | [DADO OMITIDO] | [[DADO OMITIDO]] |
| dim_itens_raw | [DADO OMITIDO] | [[DADO OMITIDO]] |
| dim_local_raw | [DADO OMITIDO] | [] |
| dim_varejo_contratado_raw | [DADO OMITIDO] | [[DADO OMITIDO]] |

### Silver

[Auditoria completa](lactalis_silver_isolation.json)

| Tabela | Linhas | ID |
|---|---:|---|
| aux_contratado_local | [DADO OMITIDO] | [[DADO OMITIDO]] |
| aux_contratado_segmento | [DADO OMITIDO] | [] |
| calculo_oportunidades | [DADO OMITIDO] | [[DADO OMITIDO]] |
| dim_catalogo_local | [DADO OMITIDO] | [[DADO OMITIDO]] |
| dim_catalogo_produtos | [DADO OMITIDO] | [[DADO OMITIDO]] |
| dim_conversao | [DADO OMITIDO] | [[DADO OMITIDO]] |
| dim_customer | [DADO OMITIDO] | [[DADO OMITIDO]] |
| dim_itens | [DADO OMITIDO] | [[DADO OMITIDO]] |
| dim_local | [DADO OMITIDO] | [[DADO OMITIDO]] |
| dim_nivel_atividade | [DADO OMITIDO] | [[DADO OMITIDO]] |
| etl_calc_v2 | [DADO OMITIDO] | [[DADO OMITIDO]] |
| fato_diaria | [DADO OMITIDO] | [[DADO OMITIDO]] |
| fato_historico | [DADO OMITIDO] | [[DADO OMITIDO]] |
| fato_ivd_tvd | [DADO OMITIDO] | [[DADO OMITIDO]] |
| fato_mensal_causa_osa | [DADO OMITIDO] | [[DADO OMITIDO]] |
| fato_nivel_atividade | [DADO OMITIDO] | [[DADO OMITIDO]] |
| fato_preco | [DADO OMITIDO] | [[DADO OMITIDO]] |
| fato_semanal | [DADO OMITIDO] | [[DADO OMITIDO]] |

### Gold

[Auditoria completa](lactalis_gold_isolation.json)

| Tabela | Linhas | ID |
|---|---:|---|
| calculo_oportunidades | [DADO OMITIDO] | [[DADO OMITIDO]] |
| dim_catalogo_local | [DADO OMITIDO] | [[DADO OMITIDO]] |
| dim_catalogo_produtos | [DADO OMITIDO] | [[DADO OMITIDO]] |
| dim_conversao | [DADO OMITIDO] | [[DADO OMITIDO]] |
| dim_customer | [DADO OMITIDO] | [[DADO OMITIDO]] |
| dim_itens | [DADO OMITIDO] | [[DADO OMITIDO]] |
| dim_local | [DADO OMITIDO] | [[DADO OMITIDO]] |
| dim_nivel_atividade | [DADO OMITIDO] | [[DADO OMITIDO]] |
| fato_diaria | [DADO OMITIDO] | [[DADO OMITIDO]] |
| fato_historico | [DADO OMITIDO] | [[DADO OMITIDO]] |
| fato_ivd_tvd | [DADO OMITIDO] | [[DADO OMITIDO]] |
| fato_mensal_causa_osa | [DADO OMITIDO] | [[DADO OMITIDO]] |
| fato_nivel_atividade | [DADO OMITIDO] | [[DADO OMITIDO]] |
| fato_preco | [DADO OMITIDO] | [[DADO OMITIDO]] |
| fato_semanal | [DADO OMITIDO] | [[DADO OMITIDO]] |

## PostgreSQL e serving

O contrato desta branch é o schema `gold`. Não foram criados Gold AMBEV/PANDURATA. A Gold completa está no lake; a publicação SQL usa janelas existentes de serving: TVD [DADO OMITIDO] dias, semanal [DADO OMITIDO] dias, OSA/mensal [DADO OMITIDO] dias; histórico mensal completo e exportação diária recente.

Isolamento SQL aprovado: **True**. Banco: **[DADO OMITIDO] bytes**. Schemas: audit, bronze, gold, information_schema, pg_catalog, pg_toast, public, silver.

[Objetos, contagens por tenant, tamanhos e índices](lactalis_sql_current.json)

| Objeto | Linhas | Total bytes | Índices bytes |
|---|---:|---:|---:|
| audit.fact_candidate_inventory | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| audit.gold_quality_gate | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| audit.metric_readiness | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| audit.opportunity_readiness | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| audit.silver_quality_gate | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.calculo_oportunidades | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.dim_catalogo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.dim_catalogo_produtos | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.dim_conversao | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.dim_customer | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.dim_itens | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.dim_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.dim_nivel_atividade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.fato_historico | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.fato_ivd_tvd | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.fato_mensal_causa_osa | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.fato_semanal | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_conversion_options | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_export_daily | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_export_daily_retail_summary | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_export_daily_source | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_export_monthly | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_export_monthly_retail_summary | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_filter_options | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_ivd_daily | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_ivd_daily_summary | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_osa_causes_default | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_osa_causes_summary | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_osa_industry_causes | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_osa_matrix_default | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_osa_monthly_default | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_osa_monthly_retail | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_osa_semantic_default | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_osa_weekly_default | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_overview_default_summary | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_overview_distinct_summary | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_overview_history | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_overview_quantity_default | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_overview_quantity_detail | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_overview_semantic_default | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_overview_summary | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_panorama_comparison_gap_daily | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_panorama_comparison_history_detail | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_panorama_detail_default | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_panorama_gap_monthly_default | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_panorama_gap_periodic | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_panorama_gap_weekly_card_default | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_panorama_inventory_monthly_default | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_panorama_inventory_weekly_card_default | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_panorama_inventory_weekly_detail | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_panorama_kpi_dimension_gap_default | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_panorama_kpi_dimension_history_default | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_panorama_latest | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_panorama_opportunities | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_panorama_opportunities_latest | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_panorama_sales_monthly_default | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_panorama_sales_weekly_card_default | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_panorama_sales_weekly_default | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_panorama_weekly | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_panorama_weekly_summary | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_stock_tasks | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_tvd_daily | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold.nr_tvd_daily_summary | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |

Views: gold.vw_mart_visao_industria.

Maiores [DADO OMITIDO] objetos: campo `top3[DADO OMITIDO]` da evidência SQL.

### Execução dos marts

[Log completo](lactalis_marts_current.log)

| SQL | Status | Segundos |
|---|---|---:|
| [DADO OMITIDO]_mart_visao_industria.sql | passed | [DADO OMITIDO] |
| [DADO OMITIDO]_neoretail_serving_marts.sql | passed | [DADO OMITIDO] |
| [DADO OMITIDO]_overview_performance.sql | passed | [DADO OMITIDO] |
| [DADO OMITIDO]_export_serving.sql | passed | [DADO OMITIDO] |
| [DADO OMITIDO]_interactive_performance.sql | passed | [DADO OMITIDO] |
| [DADO OMITIDO]_native_filter_options.sql | passed | [DADO OMITIDO] |
| [DADO OMITIDO]_stock_headline_performance.sql | passed | [DADO OMITIDO] |
| [DADO OMITIDO]_panorama_weekly_summary.sql | passed | [DADO OMITIDO] |
| [DADO OMITIDO]_interactive_p1_summary.sql | passed | [DADO OMITIDO] |
| [DADO OMITIDO]_export_retail_summary.sql | passed | [DADO OMITIDO] |
| [DADO OMITIDO]_overview_semantic_certification.sql | passed | [DADO OMITIDO] |
| [DADO OMITIDO]_overview_quantity_semantic.sql | passed | [DADO OMITIDO] |
| [DADO OMITIDO]_panorama_sales_semantic.sql | passed | [DADO OMITIDO] |
| [DADO OMITIDO]_panorama_inventory_semantic.sql | passed | [DADO OMITIDO] |
| [DADO OMITIDO]_panorama_detail_semantic.sql | passed | [DADO OMITIDO] |
| [DADO OMITIDO]_osa_certified_semantic.sql | passed | [DADO OMITIDO] |
| [DADO OMITIDO]_osa_monthly_retail.sql | passed | [DADO OMITIDO] |

## Pipeline e quality gates

| Etapa | Código de saída | Segundos |
|---|---:|---:|
| [[DADO OMITIDO]B](lactalis_0[DADO OMITIDO]B_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [[DADO OMITIDO]A](lactalis_0[DADO OMITIDO]A_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [[DADO OMITIDO]B](lactalis_0[DADO OMITIDO]B_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [[DADO OMITIDO]C](lactalis_0[DADO OMITIDO]C_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [[DADO OMITIDO]D](lactalis_0[DADO OMITIDO]D_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [[DADO OMITIDO]](lactalis_0[DADO OMITIDO]_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [[DADO OMITIDO]](lactalis_0[DADO OMITIDO]_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [[DADO OMITIDO]](lactalis_0[DADO OMITIDO]_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [[DADO OMITIDO]](lactalis_0[DADO OMITIDO]_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [[DADO OMITIDO]](lactalis_0[DADO OMITIDO]_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |

Silver: [DADO OMITIDO] checks; Gold: [DADO OMITIDO] checks. Fórmulas Power Query preservadas; camada semântica mantém as definições DAX atuais. [Silver](lactalis_0[DADO OMITIDO]D_current.log) · [Gold](lactalis_0[DADO OMITIDO]_current.log).

## Superset: bootstrap e validação

| Script | Código de saída | Segundos |
|---|---:|---:|
| [bootstrap_overview.py](lactalis_bootstrap_overview_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [bootstrap_overview_quantity.py](lactalis_bootstrap_overview_quantity_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [bootstrap_panorama.py](lactalis_bootstrap_panorama_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [bootstrap_stock_optimization.py](lactalis_bootstrap_stock_optimization_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [bootstrap_export.py](lactalis_bootstrap_export_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [bootstrap_osa_industry.py](lactalis_bootstrap_osa_industry_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [bootstrap_osa_industry_certified.py](lactalis_bootstrap_osa_industry_certified_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [bootstrap_embedded.py](lactalis_bootstrap_embedded_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_overview.py](lactalis_validate_overview_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_overview_quantity.py](lactalis_validate_overview_quantity_initial.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_overview_quantity.py](lactalis_validate_overview_quantity_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_panorama.py](lactalis_validate_panorama_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_panorama_sales.py](lactalis_validate_panorama_sales_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_panorama_stock.py](lactalis_validate_panorama_stock_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_panorama_comparisons.py](lactalis_validate_panorama_comparisons_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_panorama_details.py](lactalis_validate_panorama_details_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_panorama_inventory_tabs.py](lactalis_validate_panorama_inventory_tabs_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_panorama_inventory_filters.py](lactalis_validate_panorama_inventory_filters_initial.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_panorama_inventory_filters.py](lactalis_validate_panorama_inventory_filters_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_panorama_kpi_dimensions.py](lactalis_validate_panorama_kpi_dimensions_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_osa_industry_certified.py](lactalis_validate_osa_industry_certified_initial.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [bootstrap_osa_industry_certified.py](lactalis_bootstrap_osa_industry_certified_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [bootstrap_embedded.py](lactalis_bootstrap_embedded_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_osa_industry_certified.py](lactalis_validate_osa_industry_certified_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_stock_optimization.py](lactalis_validate_stock_optimization_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_export.py](lactalis_validate_export_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_stock_headlines.py](lactalis_validate_stock_headlines_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_osa_industry.py](lactalis_validate_osa_industry_initial.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [bootstrap_osa_industry.py](lactalis_bootstrap_osa_industry_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [bootstrap_osa_industry_certified.py](lactalis_bootstrap_osa_industry_certified_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [bootstrap_embedded.py](lactalis_bootstrap_embedded_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [bootstrap_osa_industry.py](lactalis_bootstrap_osa_industry_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [bootstrap_osa_industry_certified.py](lactalis_bootstrap_osa_industry_certified_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [bootstrap_embedded.py](lactalis_bootstrap_embedded_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_osa_industry.py](lactalis_validate_osa_industry_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_osa_industry.py](lactalis_validate_osa_industry_initial.log) | [DADO OMITIDO] | [DADO OMITIDO] |
| [validate_osa_industry.py](lactalis_validate_osa_industry_current.log) | [DADO OMITIDO] | [DADO OMITIDO] |

## Embedded, RLS e Assistant

Sessão real: ID [DADO OMITIDO]. Overrides negados: [[DADO OMITIDO], [DADO OMITIDO], [DADO OMITIDO]].

- `neoretail-v9-visao-geral-industria`: RLS `id_customer = [DADO OMITIDO]`, [DADO OMITIDO] probes; assinatura adulterada rejeitada: True.
- `neoretail-v9-visao-geral-quantidade`: RLS `id_customer = [DADO OMITIDO]`, [DADO OMITIDO] probes; assinatura adulterada rejeitada: True.
- `neoretail-v9-panorama-industria`: RLS `id_customer = [DADO OMITIDO]`, [DADO OMITIDO] probes; assinatura adulterada rejeitada: True.
- `neoretail-v9-osa-industria`: RLS `id_customer = [DADO OMITIDO]`, [DADO OMITIDO] probes; assinatura adulterada rejeitada: True.
- `neoretail-v9-osa-industria-certified`: RLS `id_customer = [DADO OMITIDO]`, [DADO OMITIDO] probes; assinatura adulterada rejeitada: True.
  Medida via Guest Token: hectolitro, libra, litro, quilograma, tonelada, unidade, valor.
- `neoretail-v9-tarefas-otimizacao-estoque`: RLS `id_customer = [DADO OMITIDO]`, [DADO OMITIDO] probes; assinatura adulterada rejeitada: True.
- `neoretail-v9-exportacao-historico-dia`: RLS `id_customer = [DADO OMITIDO]`, [DADO OMITIDO] probes; assinatura adulterada rejeitada: True.
- `neoretail-v9-exportacao-historico-mes`: RLS `id_customer = [DADO OMITIDO]`, [DADO OMITIDO] probes; assinatura adulterada rejeitada: True.

- embedded: [lactalis_http_embedded_current.log](lactalis_http_embedded_current.log)
- guest: [lactalis_http_guest_current.log](lactalis_http_guest_current.log)
- assistant: [lactalis_http_assistant_current.log](lactalis_http_assistant_current.log)
- assistant_smoke: [lactalis_http_assistant_smoke_current.log](lactalis_http_assistant_smoke_current.log)

## Disco

| Etapa | C livre bytes | Lake KiB | Analytics volume KiB |
|---|---:|---:|---:|
| bronze_dimensions | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| bronze_writing | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| bronze | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| silver | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| gold | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| serving_writing | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| serving_writing_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| serving_writing_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| serving_writing_4 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| serving_writing_5 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| serving | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| serving_osa_fix | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| final | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |

Snapshots `lactalis_disk_*.txt` contêm docker system df -v. Os volumes incluem WAL e temporários; não equivalem ao tamanho lógico do banco.

## Ollama e pendências

Ollama foi autorizado somente após os gates de dados, Superset, Embedded/RLS e mock. Homologação de negócio/temporal depende dos responsáveis e não é substituída pelos testes técnicos.

Pre-flight antes do download:

```json
{
  "gates_passed": true,
  "validators": [DADO OMITIDO],
  "disk": {
    "Name": "C",
    "Used": [DADO OMITIDO],
    "Free": [DADO OMITIDO]
  },
  "windows_memory_total_bytes": [DADO OMITIDO],
  "windows_memory_available_bytes": [DADO OMITIDO],
  "docker_memory": {
    "MemTotal": [DADO OMITIDO],
    "MemAvailable": [DADO OMITIDO]
  },
  "spark_pids": [],
  "containers": [
    {
      "Service": "analytics-db",
      "State": "running",
      "Health": "healthy",
      "ExitCode": [DADO OMITIDO]
    },
    {
      "Service": "embedded-app",
      "State": "running",
      "Health": "healthy",
      "ExitCode": [DADO OMITIDO]
    },
    {
      "Service": "local-engine",
      "State": "running",
      "Health": "healthy",
      "ExitCode": [DADO OMITIDO]
    },
    {
      "Service": "redis",
      "State": "running",
      "Health": "healthy",
      "ExitCode": [DADO OMITIDO]
    },
    {
      "Service": "superset",
      "State": "running",
      "Health": "healthy",
      "ExitCode": [DADO OMITIDO]
    },
    {
      "Service": "superset-db",
      "State": "running",
      "Health": "healthy",
      "ExitCode": [DADO OMITIDO]
    },
    {
      "Service": "superset-init",
      "State": "exited",
      "Health": "",
      "ExitCode": [DADO OMITIDO]
    }
  ],
  "model": "llama3.[DADO OMITIDO]:[DADO OMITIDO]b",
  "estimated_model_download_bytes": [DADO OMITIDO],
  "estimate_source": "https://ollama.com/library/llama3.[DADO OMITIDO]:[DADO OMITIDO]b"
}
```

[Pergunta real e comparação com a Tool SQL](lactalis_http_ollama_current.log)

Ollama: teste aprovado **True**; provider `ollama`, modelo `llama3.[DADO OMITIDO]:[DADO OMITIDO]b`.

Pergunta: Como está o OSA este mês?

Resposta real: O valor do percentual de OSA (OSA) no período MTD é [DADO OMITIDO]. 

Observação: A evidência disponível indica que a métrica está pendente em termos de governança.

Valor da Tool: **[DADO OMITIDO]**; igualdade exata com resultado HTTP; fonte `gold.nr_overview_quantity_default`. O código executa a Tool antes da geração; o modelo recebe somente o contexto estruturado autorizado e redige a resposta. Parâmetros SQL: [[DADO OMITIDO]].

Tempos reais em CPU: {'value': [DADO OMITIDO], 'source': [DADO OMITIDO], 'governance': [DADO OMITIDO]} ms (valor/fonte/governança).

Resposta de fonte: A fonte usada para calcular o % OSA (percentual de OSA) é a "gold.nr_overview_quantity_default".

Resposta de governança: O status técnico do OSA é RECONCILED. 

O status de negócios do OSA é PENDING.

O status temporal do OSA é PARCIAL_CALENDARIO. Além disso, há uma variância pendente em relação ao DAX.

Startup Ollama: código [DADO OMITIDO], [DADO OMITIDO] s. [Log](lactalis_start_ollama_current.log).

A primeira geração real atingiu o timeout existente de [DADO OMITIDO] s em CPU. O runtime foi reconfigurado com LLM_TIMEOUT_MS=[DADO OMITIDO], sem novo download nem alteração de fórmulas. [Falha inicial](lactalis_http_ollama_initial.log) · [startup com timeout ajustado](lactalis_start_ollama_timeout_current.log).

Para iniciar novamente com a mesma configuração (o arquivo .env foi preservado):

```powershell
$env:LLM_PROVIDER = 'ollama'
$env:LLM_TIMEOUT_MS = '[DADO OMITIDO]'
$env:NEORETAIL_CUSTOMER = '[DADO OMITIDO]'
$env:SPARK_MASTER = 'local[[DADO OMITIDO]]'
.\start.ps1 -Assistant
```

Estado final:

```json
{
  "containers": [
    {
      "Service": "analytics-db",
      "State": "running",
      "Health": "healthy",
      "ExitCode": [DADO OMITIDO]
    },
    {
      "Service": "embedded-app",
      "State": "running",
      "Health": "healthy",
      "ExitCode": [DADO OMITIDO]
    },
    {
      "Service": "local-engine",
      "State": "running",
      "Health": "healthy",
      "ExitCode": [DADO OMITIDO]
    },
    {
      "Service": "ollama",
      "State": "running",
      "Health": "healthy",
      "ExitCode": [DADO OMITIDO]
    },
    {
      "Service": "redis",
      "State": "running",
      "Health": "healthy",
      "ExitCode": [DADO OMITIDO]
    },
    {
      "Service": "superset",
      "State": "running",
      "Health": "healthy",
      "ExitCode": [DADO OMITIDO]
    },
    {
      "Service": "superset-db",
      "State": "running",
      "Health": "healthy",
      "ExitCode": [DADO OMITIDO]
    },
    {
      "Service": "superset-init",
      "State": "exited",
      "Health": "",
      "ExitCode": [DADO OMITIDO]
    }
  ],
  "models": "NAME           ID              SIZE      MODIFIED       \nllama3.[DADO OMITIDO]:[DADO OMITIDO]b    [DADO OMITIDO]c1[DADO OMITIDO]c0[DADO OMITIDO]e    [DADO OMITIDO] GB    [DADO OMITIDO] minutes ago",
  "http": {
    "embedded": [DADO OMITIDO],
    "superset": [DADO OMITIDO],
    "jupyter": [DADO OMITIDO]
  },
  "analytics_published_port": "[DADO OMITIDO]:[DADO OMITIDO]",
  "assistant_probes": {
    "embedded": {
      "probe": "embedded",
      "exit_code": [DADO OMITIDO],
      "seconds": [DADO OMITIDO]
    },
    "guest": {
      "probe": "guest",
      "exit_code": [DADO OMITIDO],
      "seconds": [DADO OMITIDO]
    },
    "assistant": {
      "probe": "assistant",
      "exit_code": [DADO OMITIDO],
      "seconds": [DADO OMITIDO]
    },
    "assistant_smoke": {
      "probe": "assistant_smoke",
      "exit_code": [DADO OMITIDO],
      "seconds": [DADO OMITIDO]
    },
    "ollama": {
      "probe": "ollama",
      "exit_code": [DADO OMITIDO],
      "seconds": [DADO OMITIDO]
    }
  },
  "git_branch": "feat/osa-industry-certification",
  "git_head": "[DADO OMITIDO]a1[DADO OMITIDO]dc1[DADO OMITIDO]eeabedf9[DADO OMITIDO]ee5[DADO OMITIDO]"
}
```

URLs: [Embedded](http://localhost:[DADO OMITIDO]), [Superset](http://localhost:[DADO OMITIDO]), [Jupyter](http://localhost:[DADO OMITIDO]). A porta publicada real de Analytics é **[DADO OMITIDO]**; a mensagem fixa de startup ainda imprime [DADO OMITIDO]. [Consumo dos containers](lactalis_stats_final.txt) · [Docker system df -v final](lactalis_disk_final.txt) · [Estado da worktree](lactalis_worktree_final.txt).

Somente o modelo llama3.[DADO OMITIDO]:[DADO OMITIDO]b está instalado. O [catálogo oficial](https://ollama.com/library/llama3.[DADO OMITIDO]:[DADO OMITIDO]b) informa aproximadamente [DADO OMITIDO] GB; a instalação local confirmou esse tamanho. Sete serviços estão healthy e superset-init terminou com código zero. Embedded/Guest/RLS foram revalidados após a inicialização Ollama.

## Ocorrências e validações adicionais

O primeiro probe filtrado de Overview Quantidade usava a rede fixa AKKIATACADO, ausente na LACTALIS. O parâmetro NEORETAIL_VALIDATION_REDE permite executar a mesma exigência com CENCOSUD, presente no tenant. Fórmulas, tolerâncias e exigência de resultado não vazio foram mantidas. [Falha original](lactalis_validate_overview_quantity_initial.log) · [resultado atual](lactalis_validate_overview_quantity_current.log).

Nenhum ID diferente de [DADO OMITIDO] ou nome diferente de LACTALIS foi encontrado nas colunas de identidade dos dados carregados. Nomes históricos em código/documentação e em mensagens fixas de bootstrap não representam dados carregados de outro tenant.

O cenário por item escolhia globalmente hectolitro, inexistente para o iogurte selecionado: SOURCE e CHARTDATA retornaram ambos zero períodos. O gate exige cenário positivo; foi parametrizada a conversão de teste para quilograma, fornecida pela origem para esse mesmo item. As regras de métricas e comparações permaneceram iguais. O diagnóstico independente reconciliou os [DADO OMITIDO] períodos em quilograma. Nenhuma conversão foi criada. [Diagnóstico](lactalis_inventory_conversion_diagnosis.json) · [falha original](lactalis_validate_panorama_inventory_filters_initial.log).

OSA certificado: o teste de uma rede levou inicialmente [DADO OMITIDO] ms, acima do limite original de [DADO OMITIDO] ms. O novo mart nr_osa_monthly_retail (SQL [DADO OMITIDO]) preserva as bases e fórmulas do SQL [DADO OMITIDO]; apenas uma rede usa o cache. Múltiplas redes e outros filtros usam o detalhe. Resultado: [DADO OMITIDO] ms no caso filtrado, máximo [DADO OMITIDO] ms nos [DADO OMITIDO] charts padrão, zero violações. Quatro testes de roteamento e [DADO OMITIDO] contratos OSA passaram. [Validator](lactalis_validate_osa_industry_certified_current.log).

OSA antiga: referências a sellout_sum/osa_loss_sum eram incompatíveis com nr_overview_summary. Duas métricas foram vinculadas às bases existentes de faturamento/fallback, perda e preço médio. Sete consultas passaram; quatro fórmulas reconciliadas em [DADO OMITIDO] meses contra o fato histórico, incluindo a normalização de NULL já definida no SQL [DADO OMITIDO]. [Falha original](lactalis_validate_osa_industry_initial.log) · [reconciliação](lactalis_validate_osa_industry_current.log).

O probe independente adicional inicialmente comparou NULL bruto com zero do mart, omitindo COALESCE já existente no SQL [DADO OMITIDO]. O probe foi corrigido para reproduzir esse contrato de entrada sobre os fatos; métricas, mart e tolerância não foram alterados. A tabela de execução conserva todas as tentativas; logs *_current.log representam a última execução e *_initial.log a primeira falha preservada.

Assistant mock autenticado: OSA [DADO OMITIDO], resposta [DADO OMITIDO], igualdade exata com a Tool SQL de produção. Fonte gold.nr_overview_quantity_default; parâmetro SQL [DADO OMITIDO]; overrides [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] negados. Status preservados: RECONCILED, negócio pending, temporal PARCIAL_CALENDARIO e PENDENTE_VARIANCE_DAX.

Testes já executados: [DADO OMITIDO] de isolamento/Power Query, [DADO OMITIDO] contratos Panorama/OSA, [DADO OMITIDO] contratos locais, [DADO OMITIDO] Assistant e [DADO OMITIDO] startup. Nenhum modelo foi necessário para esses testes.
