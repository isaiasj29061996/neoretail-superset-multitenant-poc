> Cópia para GitHub: números de origem e identificadores numéricos omitidos. Original integral exige backup externo. Não usar esta cópia como fixture ou SQL executável.

# Atualização LACTALIS — TVD/IVD — [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO]

Carga concluída. Corte da origem e do serving: **[DADO OMITIDO][DADO OMITIDO][DADO OMITIDO]**. Tenant **[DADO OMITIDO] / LACTALIS**. Execução registrada de [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO]T0[DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO][DADO OMITIDO]:[DADO OMITIDO] até [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO]T0[DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO][DADO OMITIDO]:[DADO OMITIDO], America/Sao_Paulo.

Worktree .worktrees/osa-industry; branch feat/osa-industry-certification; HEAD [DADO OMITIDO]d2f5[DADO OMITIDO]b5[DADO OMITIDO]. Serviços necessários saudáveis. Cerca de [DADO OMITIDO] GiB livres no preflight; gate de [DADO OMITIDO] GiB antes de cada etapa. Volumes preservados, sem pruning.

Azure: [DADO OMITIDO] arquivos, **[DADO OMITIDO] registros**; [DADO OMITIDO] fatos com ETag alterado, nenhum arquivo adicionado/removido, seis dimensões alteradas no preflight. ETags ingeridos conferidos. Ao final, os fatos continuavam sem alterações adicionais, mas seis arquivos de dimensões compartilhadas tiveram novos ETags. A comparação integral do recorte LACTALIS das seis dimensões comprovou conteúdo idêntico ao raw ingerido e à Bronze, incluindo multiplicidade e NULL, com hashes iguais e zero linhas adicionadas/removidas. Isso evitou uma segunda carga desnecessária.

O pipeline não tem merge incremental desses fatos; a partição LACTALIS foi recalculada porque alterações atingem também arquivos históricos. Cache raw por ETag mantido; sem amostragem, MaxFiles=[DADO OMITIDO].

Fluxo: run-local-pipeline.ps1 -Customer [DADO OMITIDO]; [DADO OMITIDO]A com -CustomerOnlyDimensions e [DADO OMITIDO]B com -Family customer_daily. OUTPUT_DIR separado por etapa, preservando evidências anteriores.

| Etapa | Horário local | Duração | Status |
|---|---|---:|---|
| [DADO OMITIDO]A | [DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO]–[DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO] | [DADO OMITIDO]s | passou |
| [DADO OMITIDO]B | [DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO]–[DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO] | [DADO OMITIDO]s | passou |
| [DADO OMITIDO]A | [DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO]–[DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO] | [DADO OMITIDO]s | passou |
| [DADO OMITIDO]B | [DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO]–[DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO] | [DADO OMITIDO]s | passou |
| [DADO OMITIDO]C | [DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO]–[DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO] | [DADO OMITIDO]s | passou |
| [DADO OMITIDO]D | [DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO]–[DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO] | [DADO OMITIDO]s | passou |
| [DADO OMITIDO] | [DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO]–[DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO] | [DADO OMITIDO]s | passou |
| [DADO OMITIDO] | [DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO]–[DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO] | [DADO OMITIDO]s | passou |
| [DADO OMITIDO] | [DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO]–[DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO] | [DADO OMITIDO]s | passou |
| [DADO OMITIDO] | [DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO]–[DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO] | [DADO OMITIDO]s | passou |
| [DADO OMITIDO] | [DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO]–[DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO] | [DADO OMITIDO]s | passou |

Silver: **[DADO OMITIDO] checks** aprovados. Gold: **[DADO OMITIDO] checks** aprovados. **[DADO OMITIDO] marts existentes** atualizados em transação e ordem de dependências, com definições SQL e índices preservados.

| Camada/tabela TVD/IVD | Registros | Corte diário |
|---|---:|---|
| bronze / candidate_customer_daily | [DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] |
| silver / fato_ivd_tvd | [DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] |
| gold / fato_ivd_tvd | [DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] |
| PostgreSQL / fato_ivd_tvd | [DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] |
| PostgreSQL / nr_tvd_daily | [DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] |
| PostgreSQL / nr_ivd_daily | [DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] |
| PostgreSQL / nr_tvd_daily_summary | [DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] |
| PostgreSQL / nr_ivd_daily_summary | [DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] |
| PostgreSQL / nr_pbip_daily_headlines | [DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] |

A janela SQL de TVD/IVD permanece em [DADO OMITIDO] dias; o lake contém o histórico completo. Charts [DADO OMITIDO]/[DADO OMITIDO] consultam gold.fato_ivd_tvd, calculo_oportunidades, dimensões e nr_pbip_calendar. Marts diários e summaries relacionados também atualizados.

Antes da carga: Bronze/Silver/Gold até [DADO OMITIDO]/[DADO OMITIDO]; marts físicos tradicionais TVD/IVD até [DADO OMITIDO]/[DADO OMITIDO]; calendário PBIP até [DADO OMITIDO]/[DADO OMITIDO]. Consumo revalidado nos charts TVD/IVD da Visão Geral Indústria, default e filtrado. Dashboards e marts fora dessa comparação não foram certificados nesta rodada.

Calendário: data_at [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO], importação [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO]. Apenas datas/âncoras dos oito charts da visão geral sincronizadas pela regra do bootstrap existente. Fórmulas, DAX, SQL dos datasets, predicados de negócio, RLS, Guest Token e Embedded preservados.

## Indicadores preliminares do Superset

Valores em R$, extraídos via ChartData sem cache e transformador frontend vigente. Contexto default salvo + tenant [DADO OMITIDO], sem seleções adicionais de Rede/Bandeira/Produto/AP. MTD é a última data não BLANK do mês; mês anterior é setembro; U3M usa julho/agosto/setembro, divisor [DADO OMITIDO]. Precisão completa e linhas intermediárias nos JSONs de indicadores.

| Indicador | Antes | Depois |
|---|---:|---:|
| TVD MTD | [DADO OMITIDO] | [DADO OMITIDO] |
| TVD Mês anterior | [DADO OMITIDO] | [DADO OMITIDO] |
| TVD Média U3M | [DADO OMITIDO] | [DADO OMITIDO] |
| IVD MTD | [DADO OMITIDO] | [DADO OMITIDO] |
| IVD Mês anterior | [DADO OMITIDO] | [DADO OMITIDO] |
| IVD Média U3M | [DADO OMITIDO] | [DADO OMITIDO] |

| Contagens atuais | Críticos antes → depois | Em risco antes → depois |
|---|---:|---:|
| TVD | [DADO OMITIDO] → [DADO OMITIDO] | [DADO OMITIDO] → [DADO OMITIDO] |
| IVD | [DADO OMITIDO] → [DADO OMITIDO] | [DADO OMITIDO] → [DADO OMITIDO] |

Cache: extrações forçadas conferidas por replay SQL. Novas chaves após avanço das datas; repetição sem force retorna os mesmos dados atualizados. Sem flush global. Sessões de navegador já abertas devem recarregar o dashboard para receber os parâmetros atuais.

Testes: [DADO OMITIDO] testes Python TVD/IVD/visão geral/filtros; [DADO OMITIDO] checks PBIP frontend + [DADO OMITIDO] genéricos; [DADO OMITIDO] probes Guest/RLS; ChartData default/filtrado; replay SQL × API; gates Silver/Gold; auditorias de registros, datas e ETags. Contratos preservados. Referência anterior salva: [DADO OMITIDO] MATCH / [DADO OMITIDO] DIFFERENCE / [DADO OMITIDO] UNMAPPED; contrato completo: [DADO OMITIDO] / [DADO OMITIDO] / [DADO OMITIDO]; NO_PBI_VALUE=[DADO OMITIDO]. Nenhuma certificação numérica Power BI nesta etapa.

Pendência: confirmar refresh completo do Power BI (fatos e dimensões) até [DADO OMITIDO]/[DADO OMITIDO], calendário/data_at [DADO OMITIDO]/[DADO OMITIDO], página/bookmark e os mesmos filtros (ou fornecer a seleção desejada). As contagens retornadas também precisam dessa confirmação. Nenhuma investigação/correção de divergência numérica foi iniciada. Dashboards fora da comparação TVD/IVD permanecem sem revalidação.

Git status idêntico ao início: [DADO OMITIDO] modificados / [DADO OMITIDO] entradas não rastreadas. [Status completo](git_status_final.txt). Sem commit/push ou mudança de branch. [Evidência estruturada com timestamps](report.json).

Nota operacional: três tentativas do adaptador de logs falharam antes da ingestão; evidências preservadas. A revisão automática rejeitou uma alternativa que poderia mascarar falhas. O adaptador final separou stdout/stderr e abortou em todo exit code Docker não zero.
