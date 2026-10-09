# Evidence snapshot before Git reconciliation

This canonical document records the rebuild validated at 307a129 on 2026-10-07. Counts are aggregate technical evidence, not database extracts. Raw logs/JSONL/JSON, tokens, passwords, caches and client rows are not published. The referenced generated/ artifacts remain only on the workstation.

# Reconstrução local LACTALIS — ID 290

Branch: `feat/osa-industry-certification`. Commit: `307a129dc13994019eeabedf92ee5341579e9706`.

Execução do zero, sem recuperação dos volumes apagados. Sem merge, push ou alteração de main.

## Origem e isolamento

Fatos: container Azure `neoretail`, prefixo `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/`: 172 arquivos, 2.262.892.218 bytes, 115.392.674 linhas. Versões/ETags: evidência: `generated/lactalis_source_versions_current.json` (evidencia local).

As dimensões com identidade foram filtradas por ID 290 e nome LACTALIS antes de persistir cache ou Bronze. `DIMENSAO_LOCAL` é compartilhada, sem ID de cliente: selecionada pelos varejistas contratados de LACTALIS. Leitura por ranges de Parquet remoto com ETag fixo; blocos compartilhados precisam ser lidos para selecionar linhas, mas a população não selecionada nunca é gravada localmente. Não foi inventado manufacturer_id.

Paths e schemas Azure: `generated/lactalis_source_preflight_current.json` (evidencia local) · seleção das dimensões: `generated/scoped_dimensions_290.json` (evidencia local)

## Lake: linhas e identidade

Dimensões Azure identificadas:

- `DIMENSAO/CATALOGO_PRODUTO_GVI.snappy.parquet`: 622,782 linhas na origem, 4,219,766 bytes.
- `DIMENSAO/DIMENSAO_LOCAL.snappy.parquet`: 42,235 linhas na origem, 1,907,942 bytes.
- `DIMENSAO/DIMENSAO_CUSTOMER.snappy.parquet`: 46 linhas na origem, 1,065 bytes.
- `DIMENSAO/DIMENSAO_CONVERSOES.snappy.parquet`: 1,589,018 linhas na origem, 4,341,049 bytes.
- `DIMENSAO/DIMENSAO_CATALOGO_PRODUTOS.snappy.parquet`: 2,999 linhas na origem, 137,404 bytes.
- `DIMENSAO/DIMENSAO_VAREJO_CONTRATADO.snappy.parquet`: 371 linhas na origem, 5,513 bytes.

As contagens abaixo são as linhas selecionadas/persistidas; dimensões remotas compartilhadas incluem outros clientes na origem.

### Bronze

Auditoria completa: `generated/lactalis_bronze_isolation.json` (evidencia local)

| Tabela | Linhas | ID |
|---|---:|---|
| candidate_customer_daily | 115,392,674 | [290] |
| dim_catalogo_produtos_raw | 1,327 | [290] |
| dim_conversao_raw | 120,629 | [290] |
| dim_customer_raw | 1 | [290] |
| dim_itens_raw | 29,195 | [290] |
| dim_local_raw | 6,061 | [] |
| dim_varejo_contratado_raw | 8 | [290] |

### Silver

Auditoria completa: `generated/lactalis_silver_isolation.json` (evidencia local)

| Tabela | Linhas | ID |
|---|---:|---|
| aux_contratado_local | 7 | [290] |
| aux_contratado_segmento | 0 | [] |
| calculo_oportunidades | 465,083 | [290] |
| dim_catalogo_local | 4,724 | [290] |
| dim_catalogo_produtos | 1,327 | [290] |
| dim_conversao | 120,629 | [290] |
| dim_customer | 1 | [290] |
| dim_itens | 29,195 | [290] |
| dim_local | 4,724 | [290] |
| dim_nivel_atividade | 6 | [290] |
| etl_calc_v2 | 465,083 | [290] |
| fato_diaria | 115,392,674 | [290] |
| fato_historico | 4,828,269 | [290] |
| fato_ivd_tvd | 115,392,674 | [290] |
| fato_mensal_causa_osa | 6,549,376 | [290] |
| fato_nivel_atividade | 465,083 | [290] |
| fato_preco | 4,828,269 | [290] |
| fato_semanal | 17,656,258 | [290] |

### Gold

Auditoria completa: `generated/lactalis_gold_isolation.json` (evidencia local)

| Tabela | Linhas | ID |
|---|---:|---|
| calculo_oportunidades | 465,083 | [290] |
| dim_catalogo_local | 4,724 | [290] |
| dim_catalogo_produtos | 1,327 | [290] |
| dim_conversao | 120,629 | [290] |
| dim_customer | 1 | [290] |
| dim_itens | 29,195 | [290] |
| dim_local | 4,724 | [290] |
| dim_nivel_atividade | 6 | [290] |
| fato_diaria | 115,392,674 | [290] |
| fato_historico | 4,828,269 | [290] |
| fato_ivd_tvd | 115,392,674 | [290] |
| fato_mensal_causa_osa | 6,549,376 | [290] |
| fato_nivel_atividade | 465,083 | [290] |
| fato_preco | 4,828,269 | [290] |
| fato_semanal | 17,656,258 | [290] |

## PostgreSQL e serving

O contrato desta branch é o schema `gold`. Não foram criados Gold AMBEV/PANDURATA. A Gold completa está no lake; a publicação SQL usa janelas existentes de serving: TVD 180 dias, semanal 730 dias, OSA/mensal 1095 dias; histórico mensal completo e exportação diária recente.

Isolamento SQL aprovado: **True**. Banco: **43,104,517,143 bytes**. Schemas: audit, bronze, gold, information_schema, pg_catalog, pg_toast, public, silver.

Objetos, contagens por tenant, tamanhos e índices: `generated/lactalis_sql_current.json` (evidencia local)

| Objeto | Linhas | Total bytes | Índices bytes |
|---|---:|---:|---:|
| audit.fact_candidate_inventory | 172 | 172,032 | 16,384 |
| audit.gold_quality_gate | 15 | 32,768 | 16,384 |
| audit.metric_readiness | 6 | 32,768 | 16,384 |
| audit.opportunity_readiness | 1 | 32,768 | 16,384 |
| audit.silver_quality_gate | 20 | 32,768 | 16,384 |
| gold.calculo_oportunidades | 465,083 | 96,165,888 | 23,298,048 |
| gold.dim_catalogo_local | 4,724 | 835,584 | 49,152 |
| gold.dim_catalogo_produtos | 1,327 | 434,176 | 32,768 |
| gold.dim_conversao | 120,629 | 18,505,728 | 6,258,688 |
| gold.dim_customer | 1 | 32,768 | 16,384 |
| gold.dim_itens | 29,195 | 17,784,832 | 9,248,768 |
| gold.dim_local | 4,724 | 3,137,536 | 1,851,392 |
| gold.dim_nivel_atividade | 6 | 32,768 | 16,384 |
| gold.fato_historico | 4,828,269 | 949,493,760 | 106,520,576 |
| gold.fato_ivd_tvd | 15,950,179 | 1,245,913,088 | 110,551,040 |
| gold.fato_mensal_causa_osa | 6,549,376 | 969,310,208 | 143,785,984 |
| gold.fato_semanal | 15,903,447 | 2,920,103,936 | 352,239,616 |
| gold.nr_conversion_options | 7 | 32,768 | 16,384 |
| gold.nr_export_daily | 5,199,515 | 2,437,316,608 | 192,184,320 |
| gold.nr_export_daily_retail_summary | 368 | 106,496 | 32,768 |
| gold.nr_export_daily_source | 5,199,515 | 751,673,344 | 36,052,992 |
| gold.nr_export_monthly | 4,828,269 | 1,929,510,912 | 176,824,320 |
| gold.nr_export_monthly_retail_summary | 172 | 57,344 | 16,384 |
| gold.nr_filter_options | 33,926 | 6,963,200 | 1,638,400 |
| gold.nr_ivd_daily | 10,099,428 | 3,461,799,936 | 303,636,480 |
| gold.nr_ivd_daily_summary | 180 | 40,960 | 16,384 |
| gold.nr_osa_causes_default | 4,235 | 811,008 | 303,104 |
| gold.nr_osa_causes_summary | 605 | 106,496 | 32,768 |
| gold.nr_osa_industry_causes | 6,549,376 | 2,182,807,552 | 238,698,496 |
| gold.nr_osa_matrix_default | 1,246 | 303,104 | 32,768 |
| gold.nr_osa_monthly_default | 210 | 73,728 | 32,768 |
| gold.nr_osa_monthly_retail | 1,050 | 344,064 | 73,728 |
| gold.nr_osa_semantic_default | 200 | 57,344 | 16,384 |
| gold.nr_osa_weekly_default | 91 | 40,960 | 16,384 |
| gold.nr_overview_default_summary | 152 | 90,112 | 16,384 |
| gold.nr_overview_distinct_summary | 30 | 24,576 | 16,384 |
| gold.nr_overview_history | 4,828,269 | 1,734,844,416 | 208,715,776 |
| gold.nr_overview_quantity_default | 200 | 90,112 | 16,384 |
| gold.nr_overview_quantity_detail | 4,828,269 | 1,532,608,512 | 176,390,144 |
| gold.nr_overview_semantic_default | 862 | 335,872 | 65,536 |
| gold.nr_overview_summary | 1,808,282 | 809,328,640 | 67,747,840 |
| gold.nr_panorama_comparison_gap_daily | 259,982 | 42,991,616 | 7,815,168 |
| gold.nr_panorama_comparison_history_detail | 4,828,269 | 1,549,377,536 | 180,043,776 |
| gold.nr_panorama_detail_default | 3,514 | 1,081,344 | 360,448 |
| gold.nr_panorama_gap_monthly_default | 7 | 32,768 | 16,384 |
| gold.nr_panorama_gap_periodic | 2,103,695 | 724,033,536 | 64,790,528 |
| gold.nr_panorama_gap_weekly_card_default | 20 | 32,768 | 16,384 |
| gold.nr_panorama_inventory_monthly_default | 170 | 57,344 | 16,384 |
| gold.nr_panorama_inventory_weekly_card_default | 248 | 106,496 | 32,768 |
| gold.nr_panorama_inventory_weekly_detail | 15,903,447 | 5,078,818,816 | 469,540,864 |
| gold.nr_panorama_kpi_dimension_gap_default | 1,675 | 294,912 | 32,768 |
| gold.nr_panorama_kpi_dimension_history_default | 5,391 | 1,679,360 | 57,344 |
| gold.nr_panorama_latest | 94,746 | 38,092,800 | 2,916,352 |
| gold.nr_panorama_opportunities | 15,950,179 | 5,936,873,472 | 700,375,040 |
| gold.nr_panorama_opportunities_latest | 5,991 | 2,293,760 | 155,648 |
| gold.nr_panorama_sales_monthly_default | 170 | 40,960 | 16,384 |
| gold.nr_panorama_sales_weekly_card_default | 248 | 73,728 | 32,768 |
| gold.nr_panorama_sales_weekly_default | 630 | 188,416 | 49,152 |
| gold.nr_panorama_weekly | 15,903,447 | 5,025,579,008 | 464,551,936 |
| gold.nr_panorama_weekly_summary | 105 | 40,960 | 16,384 |
| gold.nr_stock_tasks | 465,083 | 158,703,616 | 13,926,400 |
| gold.nr_tvd_daily | 10,099,428 | 3,461,799,936 | 303,636,480 |
| gold.nr_tvd_daily_summary | 180 | 40,960 | 16,384 |

Views: gold.vw_mart_visao_industria.

Maiores 30 objetos: campo `top30` da evidência SQL.

### Execução dos marts

Log completo: `generated/lactalis_marts_current.log` (evidencia local)

| SQL | Status | Segundos |
|---|---|---:|
| 20_mart_visao_industria.sql | passed | 0.03 |
| 30_neoretail_serving_marts.sql | passed | 1060.16 |
| 31_overview_performance.sql | passed | 400.25 |
| 32_export_serving.sql | passed | 151.6 |
| 33_interactive_performance.sql | passed | 60.35 |
| 34_native_filter_options.sql | passed | 0.5 |
| 35_stock_headline_performance.sql | passed | 14.98 |
| 36_panorama_weekly_summary.sql | passed | 11.98 |
| 37_interactive_p1_summary.sql | passed | 17.28 |
| 38_export_retail_summary.sql | passed | 17.07 |
| 39_overview_semantic_certification.sql | passed | 24.79 |
| 40_overview_quantity_semantic.sql | passed | 100.58 |
| 41_panorama_sales_semantic.sql | passed | 19.15 |
| 43_panorama_inventory_semantic.sql | passed | 472.11 |
| 44_panorama_detail_semantic.sql | passed | 100.45 |
| 45_osa_certified_semantic.sql | passed | 532.72 |
| 46_osa_monthly_retail.sql | passed | 11.42 |

## Pipeline e quality gates

| Etapa | Código de saída | Segundos |
|---|---:|---:|
| 02B: `generated/lactalis_02B_current.log` (evidencia local) | 0 | 735.1 |
| 03A: `generated/lactalis_03A_current.log` (evidencia local) | 0 | 44.3 |
| 03B: `generated/lactalis_03B_current.log` (evidencia local) | 0 | 845.67 |
| 03C: `generated/lactalis_03C_current.log` (evidencia local) | 0 | 25.33 |
| 03D: `generated/lactalis_03D_current.log` (evidencia local) | 0 | 38.43 |
| 04: `generated/lactalis_04_current.log` (evidencia local) | 0 | 20.63 |
| 05: `generated/lactalis_05_current.log` (evidencia local) | 0 | 30.1 |
| 06: `generated/lactalis_06_current.log` (evidencia local) | 0 | 708.37 |
| 07: `generated/lactalis_07_current.log` (evidencia local) | 0 | 18.84 |
| 08: `generated/lactalis_08_current.log` (evidencia local) | 0 | 23.35 |

Silver: 20 checks; Gold: 15 checks. Fórmulas Power Query preservadas; camada semântica mantém as definições DAX atuais. Silver: `generated/lactalis_03D_current.log` (evidencia local) · Gold: `generated/lactalis_07_current.log` (evidencia local).

## Superset: bootstrap e validação

| Script | Código de saída | Segundos |
|---|---:|---:|
| bootstrap_overview.py: `generated/lactalis_bootstrap_overview_current.log` (evidencia local) | 0 | 11.93 |
| bootstrap_overview_quantity.py: `generated/lactalis_bootstrap_overview_quantity_current.log` (evidencia local) | 0 | 6.82 |
| bootstrap_panorama.py: `generated/lactalis_bootstrap_panorama_current.log` (evidencia local) | 0 | 25.0 |
| bootstrap_stock_optimization.py: `generated/lactalis_bootstrap_stock_optimization_current.log` (evidencia local) | 0 | 8.0 |
| bootstrap_export.py: `generated/lactalis_bootstrap_export_current.log` (evidencia local) | 0 | 7.72 |
| bootstrap_osa_industry.py: `generated/lactalis_bootstrap_osa_industry_current.log` (evidencia local) | 0 | 7.65 |
| bootstrap_osa_industry_certified.py: `generated/lactalis_bootstrap_osa_industry_certified_current.log` (evidencia local) | 0 | 8.03 |
| bootstrap_embedded.py: `generated/lactalis_bootstrap_embedded_current.log` (evidencia local) | 0 | 7.96 |
| validate_overview.py: `generated/lactalis_validate_overview_current.log` (evidencia local) | 0 | 8.41 |
| validate_overview_quantity.py: `generated/lactalis_validate_overview_quantity_initial.log` (evidencia local) | 1 | 24.43 |
| validate_overview_quantity.py: `generated/lactalis_validate_overview_quantity_current.log` (evidencia local) | 0 | 32.72 |
| validate_panorama.py: `generated/lactalis_validate_panorama_current.log` (evidencia local) | 0 | 33.76 |
| validate_panorama_sales.py: `generated/lactalis_validate_panorama_sales_current.log` (evidencia local) | 0 | 26.51 |
| validate_panorama_stock.py: `generated/lactalis_validate_panorama_stock_current.log` (evidencia local) | 0 | 20.8 |
| validate_panorama_comparisons.py: `generated/lactalis_validate_panorama_comparisons_current.log` (evidencia local) | 0 | 120.42 |
| validate_panorama_details.py: `generated/lactalis_validate_panorama_details_current.log` (evidencia local) | 0 | 48.79 |
| validate_panorama_inventory_tabs.py: `generated/lactalis_validate_panorama_inventory_tabs_current.log` (evidencia local) | 0 | 20.8 |
| validate_panorama_inventory_filters.py: `generated/lactalis_validate_panorama_inventory_filters_initial.log` (evidencia local) | 1 | 313.06 |
| validate_panorama_inventory_filters.py: `generated/lactalis_validate_panorama_inventory_filters_current.log` (evidencia local) | 0 | 590.63 |
| validate_panorama_kpi_dimensions.py: `generated/lactalis_validate_panorama_kpi_dimensions_current.log` (evidencia local) | 0 | 63.42 |
| validate_osa_industry_certified.py: `generated/lactalis_validate_osa_industry_certified_initial.log` (evidencia local) | 1 | 41.8 |
| bootstrap_osa_industry_certified.py: `generated/lactalis_bootstrap_osa_industry_certified_current.log` (evidencia local) | 0 | 9.74 |
| bootstrap_embedded.py: `generated/lactalis_bootstrap_embedded_current.log` (evidencia local) | 0 | 7.9 |
| validate_osa_industry_certified.py: `generated/lactalis_validate_osa_industry_certified_current.log` (evidencia local) | 0 | 27.41 |
| validate_stock_optimization.py: `generated/lactalis_validate_stock_optimization_current.log` (evidencia local) | 0 | 9.81 |
| validate_export.py: `generated/lactalis_validate_export_current.log` (evidencia local) | 0 | 25.06 |
| validate_stock_headlines.py: `generated/lactalis_validate_stock_headlines_current.log` (evidencia local) | 0 | 21.99 |
| validate_osa_industry.py: `generated/lactalis_validate_osa_industry_initial.log` (evidencia local) | 1 | 8.42 |
| bootstrap_osa_industry.py: `generated/lactalis_bootstrap_osa_industry_current.log` (evidencia local) | 0 | 7.46 |
| bootstrap_osa_industry_certified.py: `generated/lactalis_bootstrap_osa_industry_certified_current.log` (evidencia local) | 0 | 7.18 |
| bootstrap_embedded.py: `generated/lactalis_bootstrap_embedded_current.log` (evidencia local) | 0 | 6.96 |
| bootstrap_osa_industry.py: `generated/lactalis_bootstrap_osa_industry_current.log` (evidencia local) | 0 | 6.76 |
| bootstrap_osa_industry_certified.py: `generated/lactalis_bootstrap_osa_industry_certified_current.log` (evidencia local) | 0 | 7.51 |
| bootstrap_embedded.py: `generated/lactalis_bootstrap_embedded_current.log` (evidencia local) | 0 | 8.1 |
| validate_osa_industry.py: `generated/lactalis_validate_osa_industry_current.log` (evidencia local) | 0 | 8.99 |
| validate_osa_industry.py: `generated/lactalis_validate_osa_industry_initial.log` (evidencia local) | 1 | 10.94 |
| validate_osa_industry.py: `generated/lactalis_validate_osa_industry_current.log` (evidencia local) | 0 | 9.76 |

## Embedded, RLS e Assistant

Sessão real: ID 290. Overrides negados: [142, 17066, 609].

- `neoretail-v9-visao-geral-industria`: RLS `id_customer = 290`, 16 probes; assinatura adulterada rejeitada: True.
- `neoretail-v9-visao-geral-quantidade`: RLS `id_customer = 290`, 4 probes; assinatura adulterada rejeitada: True.
- `neoretail-v9-panorama-industria`: RLS `id_customer = 290`, 88 probes; assinatura adulterada rejeitada: True.
- `neoretail-v9-osa-industria`: RLS `id_customer = 290`, 12 probes; assinatura adulterada rejeitada: True.
- `neoretail-v9-osa-industria-certified`: RLS `id_customer = 290`, 24 probes; assinatura adulterada rejeitada: True.
  Medida via Guest Token: hectolitro, libra, litro, quilograma, tonelada, unidade, valor.
- `neoretail-v9-tarefas-otimizacao-estoque`: RLS `id_customer = 290`, 12 probes; assinatura adulterada rejeitada: True.
- `neoretail-v9-exportacao-historico-dia`: RLS `id_customer = 290`, 8 probes; assinatura adulterada rejeitada: True.
- `neoretail-v9-exportacao-historico-mes`: RLS `id_customer = 290`, 8 probes; assinatura adulterada rejeitada: True.

- embedded: lactalis_http_embedded_current.log: `generated/lactalis_http_embedded_current.log` (evidencia local)
- guest: lactalis_http_guest_current.log: `generated/lactalis_http_guest_current.log` (evidencia local)
- assistant: lactalis_http_assistant_current.log: `generated/lactalis_http_assistant_current.log` (evidencia local)
- assistant_smoke: lactalis_http_assistant_smoke_current.log: `generated/lactalis_http_assistant_smoke_current.log` (evidencia local)

## Disco

| Etapa | C livre bytes | Lake KiB | Analytics volume KiB |
|---|---:|---:|---:|
| bronze_dimensions | 270,747,095,040 | 1858304 | 47312 |
| bronze_writing | 268,320,661,504 | 4214160 | 47312 |
| bronze | 267,974,098,944 | 4412080 | 47392 |
| silver | 265,253,961,728 | 6534172 | 47472 |
| gold | 252,948,492,288 | 8715620 | 7451056 |
| serving_writing | 252,188,897,280 | 8715620 | 9185836 |
| serving_writing_2 | 241,411,141,632 | 8715620 | 19115548 |
| serving_writing_3 | 228,684,779,520 | 8715620 | 23541100 |
| serving_writing_4 | 218,820,554,752 | 8715620 | 39056004 |
| serving_writing_5 | 205,378,228,224 | 8715620 | 51898988 |
| serving | 198,461,743,104 | 8715620 | 43166044 |
| serving_osa_fix | 187,082,215,424 | 8715620 | 43166404 |
| final | 186,892,128,256 | 8715620 | 43166404 |

Snapshots `lactalis_disk_*.txt` contêm docker system df -v. Os volumes incluem WAL e temporários; não equivalem ao tamanho lógico do banco.

## Ollama e pendências

Ollama foi autorizado somente após os gates de dados, Superset, Embedded/RLS e mock. Homologação de negócio/temporal depende dos responsáveis e não é substituída pelos testes técnicos.

Pre-flight antes do download:

```json
{
  "gates_passed": true,
  "validators": 15,
  "disk": {
    "Name": "C",
    "Used": 323632324608,
    "Free": 186983288832
  },
  "windows_memory_total_bytes": 34029125632,
  "windows_memory_available_bytes": 5620903936,
  "docker_memory": {
    "MemTotal": 16605908992,
    "MemAvailable": 15120949248
  },
  "spark_pids": [],
  "containers": [
    {
      "Service": "analytics-db",
      "State": "running",
      "Health": "healthy",
      "ExitCode": 0
    },
    {
      "Service": "embedded-app",
      "State": "running",
      "Health": "healthy",
      "ExitCode": 0
    },
    {
      "Service": "local-engine",
      "State": "running",
      "Health": "healthy",
      "ExitCode": 0
    },
    {
      "Service": "redis",
      "State": "running",
      "Health": "healthy",
      "ExitCode": 0
    },
    {
      "Service": "superset",
      "State": "running",
      "Health": "healthy",
      "ExitCode": 0
    },
    {
      "Service": "superset-db",
      "State": "running",
      "Health": "healthy",
      "ExitCode": 0
    },
    {
      "Service": "superset-init",
      "State": "exited",
      "Health": "",
      "ExitCode": 0
    }
  ],
  "model": "llama3.1:8b",
  "estimated_model_download_bytes": 4900000000,
  "estimate_source": "https://ollama.com/library/llama3.1:8b"
}
```

Pergunta real e comparação com a Tool SQL: `generated/lactalis_http_ollama_current.log` (evidencia local)

Ollama: teste aprovado **True**; provider `ollama`, modelo `llama3.1:8b`.

Pergunta: Como está o OSA este mês?

Resposta real: O valor do percentual de OSA (OSA) no período MTD é 83,44%.

Observação: A evidência disponível indica que a métrica está pendente em termos de governança.

Valor da Tool: **83.43631628432307**; igualdade exata com resultado HTTP; fonte `gold.nr_overview_quantity_default`. O código executa a Tool antes da geração; o modelo recebe somente o contexto estruturado autorizado e redige a resposta. Parâmetros SQL: [290].

Tempos reais em CPU: {'value': 13643, 'source': 67285, 'governance': 87989} ms (valor/fonte/governança).

Resposta de fonte: A fonte usada para calcular o % OSA (percentual de OSA) é a "gold.nr_overview_quantity_default".

Resposta de governança: O status técnico do OSA é RECONCILED.

O status de negócios do OSA é PENDING.

O status temporal do OSA é PARCIAL_CALENDARIO. Além disso, há uma variância pendente em relação ao DAX.

Startup Ollama: código 0, 476.18 s. Log: `generated/lactalis_start_ollama_current.log` (evidencia local).

A primeira geração real atingiu o timeout existente de 60 s em CPU. O runtime foi reconfigurado com LLM_TIMEOUT_MS=180000, sem novo download nem alteração de fórmulas. Falha inicial: `generated/lactalis_http_ollama_initial.log` (evidencia local) · startup com timeout ajustado: `generated/lactalis_start_ollama_timeout_current.log` (evidencia local).

Para iniciar novamente com a mesma configuração (o arquivo .env foi preservado):

```powershell
$env:LLM_PROVIDER = 'ollama'
$env:LLM_TIMEOUT_MS = '180000'
$env:NEORETAIL_CUSTOMER = '290'
$env:SPARK_MASTER = 'local[4]'
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
      "ExitCode": 0
    },
    {
      "Service": "embedded-app",
      "State": "running",
      "Health": "healthy",
      "ExitCode": 0
    },
    {
      "Service": "local-engine",
      "State": "running",
      "Health": "healthy",
      "ExitCode": 0
    },
    {
      "Service": "ollama",
      "State": "running",
      "Health": "healthy",
      "ExitCode": 0
    },
    {
      "Service": "redis",
      "State": "running",
      "Health": "healthy",
      "ExitCode": 0
    },
    {
      "Service": "superset",
      "State": "running",
      "Health": "healthy",
      "ExitCode": 0
    },
    {
      "Service": "superset-db",
      "State": "running",
      "Health": "healthy",
      "ExitCode": 0
    },
    {
      "Service": "superset-init",
      "State": "exited",
      "Health": "",
      "ExitCode": 0
    }
  ],
  "models": "NAME           ID              SIZE      MODIFIED       \nllama3.1:8b    46e0c10c039e    4.9 GB    10 minutes ago",
  "http": {
    "embedded": 200,
    "superset": 200,
    "jupyter": 200
  },
  "analytics_published_port": "0.0.0.0:5432",
  "assistant_probes": {
    "embedded": {
      "probe": "embedded",
      "exit_code": 0,
      "seconds": 2.41
    },
    "guest": {
      "probe": "guest",
      "exit_code": 0,
      "seconds": 116.54
    },
    "assistant": {
      "probe": "assistant",
      "exit_code": 0,
      "seconds": 1.74
    },
    "assistant_smoke": {
      "probe": "assistant_smoke",
      "exit_code": 0,
      "seconds": 1.11
    },
    "ollama": {
      "probe": "ollama",
      "exit_code": 0,
      "seconds": 170.19
    }
  },
  "git_branch": "feat/osa-industry-certification",
  "git_head": "307a129dc13994019eeabedf92ee5341579e9706"
}
```

URLs: [Embedded](http://localhost:3000), [Superset](http://localhost:8088), [Jupyter](http://localhost:8888). A porta publicada real de Analytics é **5432**; a mensagem fixa de startup ainda imprime 5433. Consumo dos containers: `generated/lactalis_stats_final.txt` (evidencia local) · Docker system df -v final: `generated/lactalis_disk_final.txt` (evidencia local) · Estado da worktree: `generated/lactalis_worktree_final.txt` (evidencia local).

Somente o modelo llama3.1:8b está instalado. O [catálogo oficial](https://ollama.com/library/llama3.1:8b) informa aproximadamente 4,9 GB; a instalação local confirmou esse tamanho. Sete serviços estão healthy e superset-init terminou com código zero. Embedded/Guest/RLS foram revalidados após a inicialização Ollama.

## Ocorrências e validações adicionais

O primeiro probe filtrado de Overview Quantidade usava a rede fixa AKKIATACADO, ausente na LACTALIS. O parâmetro NEORETAIL_VALIDATION_REDE permite executar a mesma exigência com CENCOSUD, presente no tenant. Fórmulas, tolerâncias e exigência de resultado não vazio foram mantidas. Falha original: `generated/lactalis_validate_overview_quantity_initial.log` (evidencia local) · resultado atual: `generated/lactalis_validate_overview_quantity_current.log` (evidencia local).

Nenhum ID diferente de 290 ou nome diferente de LACTALIS foi encontrado nas colunas de identidade dos dados carregados. Nomes históricos em código/documentação e em mensagens fixas de bootstrap não representam dados carregados de outro tenant.

O cenário por item escolhia globalmente hectolitro, inexistente para o iogurte selecionado: SOURCE e CHARTDATA retornaram ambos zero períodos. O gate exige cenário positivo; foi parametrizada a conversão de teste para quilograma, fornecida pela origem para esse mesmo item. As regras de métricas e comparações permaneceram iguais. O diagnóstico independente reconciliou os 30 períodos em quilograma. Nenhuma conversão foi criada. Diagnóstico: `generated/lactalis_inventory_conversion_diagnosis.json` (evidencia local) · falha original: `generated/lactalis_validate_panorama_inventory_filters_initial.log` (evidencia local).

OSA certificado: o teste de uma rede levou inicialmente 14.882 ms, acima do limite original de 3.000 ms. O novo mart nr_osa_monthly_retail (SQL 46) preserva as bases e fórmulas do SQL 45; apenas uma rede usa o cache. Múltiplas redes e outros filtros usam o detalhe. Resultado: 188,08 ms no caso filtrado, máximo 330,18 ms nos 14 charts padrão, zero violações. Quatro testes de roteamento e 11 contratos OSA passaram. Validator: `generated/lactalis_validate_osa_industry_certified_current.log` (evidencia local).

OSA antiga: referências a sellout_sum/osa_loss_sum eram incompatíveis com nr_overview_summary. Duas métricas foram vinculadas às bases existentes de faturamento/fallback, perda e preço médio. Sete consultas passaram; quatro fórmulas reconciliadas em 30 meses contra o fato histórico, incluindo a normalização de NULL já definida no SQL 31. Falha original: `generated/lactalis_validate_osa_industry_initial.log` (evidencia local) · reconciliação: `generated/lactalis_validate_osa_industry_current.log` (evidencia local).

O probe independente adicional inicialmente comparou NULL bruto com zero do mart, omitindo COALESCE já existente no SQL 31. O probe foi corrigido para reproduzir esse contrato de entrada sobre os fatos; métricas, mart e tolerância não foram alterados. A tabela de execução conserva todas as tentativas; logs *_current.log representam a última execução e *_initial.log a primeira falha preservada.

Assistant mock autenticado: OSA 83,43631628432307%, resposta 83,44%, igualdade exata com a Tool SQL de produção. Fonte gold.nr_overview_quantity_default; parâmetro SQL 290; overrides 142/17066/609 negados. Status preservados: RECONCILED, negócio pending, temporal PARCIAL_CALENDARIO e PENDENTE_VARIANCE_DAX.

Testes já executados: 10 de isolamento/Power Query, 60 contratos Panorama/OSA, 16 contratos locais, 31 Assistant e 7 startup. Nenhum modelo foi necessário para esses testes.


## Reproduction with explicit Lactalis scope

Copy .env.example to .env and configure Azure credentials locally. Never commit .env. Start base services with start.ps1, then use the reviewed scripts/run_lactalis_stage.py and scripts/run_lactalis_phase.py helpers only when a rebuild is intentionally required. Their pipeline calls explicitly use customer 290; dimension stage 02 uses -CustomerOnlyDimensions, and fact stage 02B uses the exact LACTALIS customer_daily family. Do not run ingestion just to verify this Git reconciliation. Legacy generic runners may still default to customer 142; always pass -Customer 290 when invoking run-local-pipeline.ps1 or run-osa-certified.ps1 directly. Current SQL producer order is the sorted analytics-db/marts scripts after view 20. Bootstrap and validators use scripts/run_lactalis_superset.py, with validation customer 290. Local evidence can be regenerated with scripts/report_lactalis_rebuild.py; update the canonical docs snapshot only after review.
