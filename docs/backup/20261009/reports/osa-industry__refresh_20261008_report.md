> Cópia para GitHub: números de origem e identificadores numéricos omitidos. Original integral exige backup externo. Não usar esta cópia como fixture ou SQL executável.

# Atualizacao LACTALIS ? [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] ? interrompida nos marts

Estado registrado em [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO]T1[DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO][DADO OMITIDO]:[DADO OMITIDO]. Inicio da carga: [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO]T1[DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO][DADO OMITIDO]:[DADO OMITIDO] (UTC; America/Sao_Paulo = UTC-[DADO OMITIDO]).

**Atualizacao incompleta nos dashboards.** Bronze/Silver/Gold aprovados ate [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO]; os principais marts diarios continuam em [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO]. Nao houve fatos de [DADO OMITIDO]/[DADO OMITIDO] no snapshot Azure auditado.

## Contexto e origem

Worktree .worktrees/osa-industry; branch feat/osa-industry-certification; HEAD [DADO OMITIDO]d2f5[DADO OMITIDO]b5[DADO OMITIDO]ead1bae9af6d2ef7b7[DADO OMITIDO]f9a4[DADO OMITIDO]ae. Tenant unico [DADO OMITIDO]/LACTALIS.

Antes: MAX diario [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO], [DADO OMITIDO] arquivos, [DADO OMITIDO] linhas. Azure: MAX(id_time)=[DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO], [DADO OMITIDO] arquivos, [DADO OMITIDO] linhas. Novos: [DADO OMITIDO]; modificados: [DADO OMITIDO]; removidos: [DADO OMITIDO]. Seis dimensoes mudaram ETag.

Full refresh somente do cliente [DADO OMITIDO]: nao existe watermark/merge incremental de facts; [DADO OMITIDO]B le todos os arquivos selecionados e substitui a particao do cliente. [DADO OMITIDO]B refaz agregacoes e snapshots historicos. Alteracoes em arquivos de [DADO OMITIDO], [DADO OMITIDO] e [DADO OMITIDO] tambem exigem recalc. Downloads reutilizaram [DADO OMITIDO] arquivos; [DADO OMITIDO] foram baixados novamente, [DADO OMITIDO] bytes. Todos os ETags ingeridos correspondem ao snapshot auditado.

## Etapas e duracoes

| Etapa | Exit code | Segundos |
|---|---:|---:|
| [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO]B | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO]A | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO]B | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO]C | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO]D | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| publish_lactalis_marts.py | [DADO OMITIDO] | [DADO OMITIDO] |

Silver: [DADO OMITIDO] checks aprovados. Gold: [DADO OMITIDO] checks aprovados. Auditorias completas Bronze/Silver/Gold: somente ID [DADO OMITIDO] e nomes LACTALIS, zero identidades nulas. DIM_LOCAL_RAW e compartilhada e foi filtrada pelos [DADO OMITIDO] varejistas contratados.

## Datas por camada

| Camada | MAX diario | Situacao |
|---|---|---|
| Azure | [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] | snapshot de metadados auditado |
| Bronze | [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] | aprovado; id_time |
| Silver | [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] | aprovado; fato_diaria.data/fato_ivd_tvd.id_time |
| Gold lake | [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] | aprovado; fato_diaria.data/fato_ivd_tvd.id_time |
| Gold SQL | [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] | fato_ivd_tvd.id_time e nr_export_daily_source.data |
| Marts de serving diarios | [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] | nr_export_daily, nr_tvd_daily, nr_stock_tasks etc NAO atualizados |
| Superset | nao revalidado | marts principais ainda antigos; nao certificar dashboards atualizados |

Buckets mensais terminam em [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] e semanais em [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO], por definicao do periodo. Isso nao representa por si so watermark diario nem prova freshness: os marts nao foram refreshed. View vw_mart_visao_industria atualizada pelo SQL2[DADO OMITIDO] ja consulta Gold de [DADO OMITIDO]/[DADO OMITIDO]; nao confundir com os demais marts ainda antigos.

## Contagens atuais por camada

### bronze

| Tabela | Linhas | IDs | Nomes |
|---|---:|---|---|
| candidate_customer_daily | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| dim_catalogo_produtos_raw | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| dim_conversao_raw | [DADO OMITIDO] | [[DADO OMITIDO]] | [] |
| dim_customer_raw | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| dim_itens_raw | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| dim_local_raw | [DADO OMITIDO] | [] | [] |
| dim_varejo_contratado_raw | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |

### silver

| Tabela | Linhas | IDs | Nomes |
|---|---:|---|---|
| aux_contratado_local | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| aux_contratado_segmento | [DADO OMITIDO] | [] | [] |
| calculo_oportunidades | [DADO OMITIDO] | [[DADO OMITIDO]] | [] |
| dim_catalogo_local | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| dim_catalogo_produtos | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| dim_conversao | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| dim_customer | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| dim_itens | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| dim_local | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| dim_nivel_atividade | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| etl_calc_v2 | [DADO OMITIDO] | [[DADO OMITIDO]] | [] |
| fato_diaria | [DADO OMITIDO] | [[DADO OMITIDO]] | [] |
| fato_historico | [DADO OMITIDO] | [[DADO OMITIDO]] | [] |
| fato_ivd_tvd | [DADO OMITIDO] | [[DADO OMITIDO]] | [] |
| fato_mensal_causa_osa | [DADO OMITIDO] | [[DADO OMITIDO]] | [] |
| fato_nivel_atividade | [DADO OMITIDO] | [[DADO OMITIDO]] | [] |
| fato_preco | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| fato_semanal | [DADO OMITIDO] | [[DADO OMITIDO]] | [] |

### gold

| Tabela | Linhas | IDs | Nomes |
|---|---:|---|---|
| calculo_oportunidades | [DADO OMITIDO] | [[DADO OMITIDO]] | [] |
| dim_catalogo_local | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| dim_catalogo_produtos | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| dim_conversao | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| dim_customer | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| dim_itens | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| dim_local | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| dim_nivel_atividade | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| fato_diaria | [DADO OMITIDO] | [[DADO OMITIDO]] | [] |
| fato_historico | [DADO OMITIDO] | [[DADO OMITIDO]] | [] |
| fato_ivd_tvd | [DADO OMITIDO] | [[DADO OMITIDO]] | [] |
| fato_mensal_causa_osa | [DADO OMITIDO] | [[DADO OMITIDO]] | [] |
| fato_nivel_atividade | [DADO OMITIDO] | [[DADO OMITIDO]] | [] |
| fato_preco | [DADO OMITIDO] | [[DADO OMITIDO]] | ['LACTALIS'] |
| fato_semanal | [DADO OMITIDO] | [[DADO OMITIDO]] | [] |

## Bloqueio e estado BI

SQL2[DADO OMITIDO] executado com sucesso. SQL3[DADO OMITIDO] falhou: nao pode remover gold.nr_overview_quantity_default porque gold.nr_panorama_sales_weekly_card_default depende dele. SQL3[DADO OMITIDO] tem BEGIN; a conexao foi fechada e a transacao abortada foi revertida. Os [DADO OMITIDO] materialized views continuam presentes e populated=true. Nenhum script SQL posterior foi executado.

Bootstrap Superset e validators Overview, Quantity, Panorama/Sales/Stock/comparacoes/detalhes/inventory/KPI, OSA/certificado, Stock e Export: NAO executados nesta atualizacao, pois dependem dos marts atualizados. Guest Token/RLS atualizado: NAO executado. Nao reaproveitar provas de ontem como validacao desta carga.

Plano revisavel, nao executado: refresh_2[DADO OMITIDO]_proposed_mart_refresh.sql. Propoe REFRESH dos [DADO OMITIDO] marts em ordem de dependencia, dentro de transacao, preservando definicoes e indices. O codigo versionado nao foi alterado.

## Recursos, volumes e Git

Disco C antes: [DADO OMITIDO] bytes livres ([DADO OMITIDO] GiB); depois: [DADO OMITIDO] bytes ([DADO OMITIDO] GiB).

Lake KiB antes/depois: [DADO OMITIDO]/[DADO OMITIDO]. Analytics KiB antes/depois: [DADO OMITIDO]/[DADO OMITIDO].

| Servico | Estado | Health |
|---|---|---|
| analytics-db | running | healthy |
| embedded-app | running | healthy |
| local-engine | running | healthy |
| ollama | exited | unhealthy |
| redis | running | healthy |
| superset | running | healthy |
| superset-db | running | healthy |
| superset-init | exited |  |

HTTP Embedded/Superset/Jupyter: {'embedded': [DADO OMITIDO], 'superset': [DADO OMITIDO], 'jupyter': [DADO OMITIDO]}. Ollama foi parado intencionalmente para Spark; modelo e ollama-data preservados, sem redownload. Todos os IDs de containers e mounts permanecem iguais. **Nenhum volume removido. Nenhum outro tenant ingerido.** .env preservado; codigo versionado inalterado; sem commit/push/merge/mudanca de branch/main/PR/Draft; WIP preservada.

Git status:

```
?? superset/diagnose_lactalis_inventory.py
?? superset/profile_lactalis_osa_filtered.py
```

## Arquivos novos/modificados na fonte

Lista completa dos [DADO OMITIDO] caminhos modificados (nenhum novo ou removido):

- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/armazmateus.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/cencosud.snappy.parquet`
- `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/vl_year=[DADO OMITIDO]/vl_month=[DADO OMITIDO]/novoatacado.snappy.parquet`

ETags, linhas e datas de cada um dos [DADO OMITIDO] arquivos: refresh_2[DADO OMITIDO]_azure.json. Datas/contagens de cada relacao SQL: refresh_2[DADO OMITIDO]_sql_before.json e refresh_2[DADO OMITIDO]_sql_after.json (reltuples sao ESTIMATIVAS, nao counts exatos). Contagens exatas do lake foram obtidas nos metadados Parquet e confirmadas pelos gates. Relatorio integral estruturado: refresh_2[DADO OMITIDO]_report.json. Todos esses arquivos sao evidencia local ignorada pelo Git.

**A carga ate Gold foi atualizada ate a ultima data disponivel no snapshot da fonte: [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO]. A atualizacao dos dashboards ainda NAO foi concluida.**
