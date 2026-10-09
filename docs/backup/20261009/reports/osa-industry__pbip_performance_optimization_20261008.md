> Cópia para GitHub: números de origem e identificadores numéricos omitidos. Original integral exige backup externo. Não usar esta cópia como fixture ou SQL executável.

# Performance PBIP LACTALIS — [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO]

Otimização concluída com redução material e resultados preservados. Somente JIT da conexão Analytics e um índice parcial foram mantidos. Não houve alteração do SQL semântico, fórmulas, frontend, filtros, calendário ou marts. A meta de <[DADO OMITIDO] s sem cache não foi atingida na API HTTP medida; renderização de navegador não foi medida.

## [DADO OMITIDO]. Baseline

Worktree `C:\Users\ijusto\Downloads\NeoRetail_V8_1_LOCAL_POSTGRES_POWERQUERY_COMPLETO\NeoRetail_V8_1_LOCAL_POSTGRES\.worktrees\osa-industry`. Branch `feat/osa-industry-certification`. HEAD `[DADO OMITIDO]d2f5[DADO OMITIDO]b5[DADO OMITIDO]ead1bae9af6d2ef7b7[DADO OMITIDO]f9a4[DADO OMITIDO]ae`. Snapshots [host BEFORE](pbip_performance_host_before_2[DADO OMITIDO].json), [runtime BEFORE](pbip_performance_runtime_before_2[DADO OMITIDO].json), [runtime AFTER](pbip_performance_runtime_after_2[DADO OMITIDO].json). Baseline histórico SQL sequencial: default [DADO OMITIDO] s, filtrado [DADO OMITIDO] s. Nova rodada controlada BEFORE: [DADO OMITIDO] s e [DADO OMITIDO] s; usar esta rodada para o delta principal, com variação local de carga/buffers explicitada.

Snapshot contém oito charts, seis datasets ([DADO OMITIDO]), SQLs integrais, parâmetros, onze definições de marts PBIP, catálogo de relações/índices e tamanhos. Histórico PBIP: [DADO OMITIDO] linhas; causas OSA: [DADO OMITIDO]; calendário: [DADO OMITIDO]; semantic_v3: [DADO OMITIDO]. Fato diário TVD/IVD: [DADO OMITIDO] linhas visitadas por scan completo no plano. Nenhum refresh ou reprocessamento foi executado.

## [DADO OMITIDO]. Perfil por chart

Default, SQL direto sequencial sem cache de resultado:

| Chart | Dataset | BEFORE s | AFTER s | Speedup | Linhas retornadas por query | Visitas a tuplas nos scans EXPLAIN |
|---|---|---|---|---|---|---|
| TVD - Pré-ruptura | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x | [DADO OMITIDO] | [DADO OMITIDO] |
| IVD - Excesso | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x | [DADO OMITIDO] | [DADO OMITIDO] |
| Giro | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x | [DADO OMITIDO] | [DADO OMITIDO] |
| OSA | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x | [DADO OMITIDO] | [DADO OMITIDO] |
| Vendas | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x | [DADO OMITIDO] | [DADO OMITIDO] |
| Estoque | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x | [DADO OMITIDO] | [DADO OMITIDO] |
| ROI | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x | [DADO OMITIDO] | [DADO OMITIDO] |
| MARKUP | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x | [DADO OMITIDO] | [DADO OMITIDO] |

Bandeira MATEUS SUPERMERCADOS + quilograma:

| Chart | Dataset | BEFORE s | AFTER s | Speedup | Linhas retornadas por query | Visitas a tuplas nos scans EXPLAIN |
|---|---|---|---|---|---|---|
| TVD - Pré-ruptura | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x | [DADO OMITIDO] | [DADO OMITIDO] |
| IVD - Excesso | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x | [DADO OMITIDO] | [DADO OMITIDO] |
| Giro | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x | [DADO OMITIDO] | [DADO OMITIDO] |
| OSA | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x | [DADO OMITIDO] | [DADO OMITIDO] |
| Vendas | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x | [DADO OMITIDO] | [DADO OMITIDO] |
| Estoque | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x | [DADO OMITIDO] | [DADO OMITIDO] |
| ROI | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x | [DADO OMITIDO] | [DADO OMITIDO] |
| MARKUP | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x | [DADO OMITIDO] | [DADO OMITIDO] |

Visitas a tuplas = soma de (Actual Rows + Rows Removed by Filter) × Actual Loops nos nós de scan ativos. Inclui dimensões e releituras de CTE; não é cardinalidade distinta nem bytes físicos de disco. Valores detalhados estão em [perfis completos](pbip_performance_profiles_2[DADO OMITIDO].json).

## [DADO OMITIDO]. TOP [DADO OMITIDO] queries mais lentas

### default

| Chart / query (base [DADO OMITIDO]) | Dataset | BEFORE s | % SQL total | AFTER s | Speedup |
|---|---|---|---|---|---|
| IVD - Excesso / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |
| TVD - Pré-ruptura / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |
| ROI / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |
| Vendas / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |
| MARKUP / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |
| MARKUP / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |
| ROI / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |
| MARKUP / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |
| ROI / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |
| Vendas / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |

### filtered

| Chart / query (base [DADO OMITIDO]) | Dataset | BEFORE s | % SQL total | AFTER s | Speedup |
|---|---|---|---|---|---|
| OSA / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |
| IVD - Excesso / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |
| Vendas / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |
| TVD - Pré-ruptura / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |
| ROI / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |
| MARKUP / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |
| ROI / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |
| ROI / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |
| MARKUP / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |
| Vendas / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO]x |

## [DADO OMITIDO]. EXPLAIN BEFORE

Todos os [DADO OMITIDO] SQLs efetivos default/filtrado foram executados com `EXPLAIN (ANALYZE, BUFFERS, VERBOSE, SETTINGS, FORMAT JSON)` em conexão de leitura. Planejamento, execução, buffers, sorts, hashes, batches/spill, scans, joins, CTEs e subplans constam dos JSONs por query. EXPLAIN ANALYZE instrumenta milhões de tuplas e pode custar mais que o SQL; seu tempo não substitui o replay medido.

### default

| Chart / query | Planning ms | Execution ms | JIT ms | Hit / Read blocks | Temp read / written |
|---|---|---|---|---|---|
| TVD - Pré-ruptura / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| IVD - Excesso / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| Giro / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| Giro / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| OSA / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| Vendas / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| Vendas / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| Estoque / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| ROI / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| ROI / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| ROI / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| MARKUP / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| MARKUP / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| MARKUP / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |

### filtered

| Chart / query | Planning ms | Execution ms | JIT ms | Hit / Read blocks | Temp read / written |
|---|---|---|---|---|---|
| TVD - Pré-ruptura / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| IVD - Excesso / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| Giro / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| Giro / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| OSA / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| Vendas / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| Vendas / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| Estoque / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| ROI / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| ROI / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| ROI / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| MARKUP / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| MARKUP / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |
| MARKUP / [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] |

## [DADO OMITIDO]. Gargalos e atribuição das regressões

F1[DADO OMITIDO]/C0[DADO OMITIDO]: o relatório anterior registrou default [DADO OMITIDO] → [DADO OMITIDO] s ao trocar totais diários pelo LASTNONBLANK correto. Os planos atuais comprovam scans completos de fato_ivd_tvd para date_context e value_context e tarefas executadas cinco vezes. AP da seleção da data e ALL(AP) do valor continuam separados. [Relatório anterior](pbip_f1[DADO OMITIDO]_c0[DADO OMITIDO]_tvd_ivd_before_after_2[DADO OMITIDO].md).

C0[DADO OMITIDO]: novas queries auxiliares fazem SUMX por Região em U3M e retêm componentes de frozen_monthly MATERIALIZED. O plano Vendas default / q1 registrou JIT [DADO OMITIDO] ms, componentes mensais e cálculo regional separados. Há três recalculações do mesmo contexto base U3M nos charts Vendas/ROI/Markup, com projeções de métricas distintas; não se tratam de SQLs finais idênticos. [Relatório C0[DADO OMITIDO]](pbip_c0[DADO OMITIDO]_sellout_u3m_before_after_2[DADO OMITIDO].md).

C1[DADO OMITIDO]: relatório anterior [DADO OMITIDO] → [DADO OMITIDO] s no default após preservar BLANK. Plano ROI atividade mostrou [DADO OMITIDO] EXISTS ativos; o índice anterior customer/data descartava em média [DADO OMITIDO] linhas por lookup, com [DADO OMITIDO] Shared Read blocks. A seleção de produto calculável e a bridge CNPJ/AP foram preservadas. JIT do envelope mensal também custa segundos mesmo quando o branch U3M é podado. [Relatório C1[DADO OMITIDO]](pbip_c1[DADO OMITIDO]_cost_blank_before_after_2[DADO OMITIDO].md).

C1[DADO OMITIDO] e ROI anual: somente frontend; SQLs e definições dos marts antes/depois dessas etapas e desta otimização são iguais. Não há nova construção SQL atribuível a C1[DADO OMITIDO]. Não atribuir variância de tempo dessas etapas a uma regressão SQL inexistente.

## [DADO OMITIDO]. Alterações mantidas

`superset/neoretail_bootstrap/core/analytics_performance.py` mescla `-c jit=off` nas opções da conexão, preservando as demais configurações e sendo idempotente. `bootstrap_analytics.py` aplica essa configuração em próximos bootstraps. Metadado da conexão Analytics foi atualizado isoladamente; `SHOW jit` confirmou off. Somente Superset foi reiniciado para renovar conexões. Nenhuma regra estrutural nova usa id_customer=[DADO OMITIDO].

A experiência isolada de JIT, antes do índice, reduziu SQL default [DADO OMITIDO] → [DADO OMITIDO] s e filtrado [DADO OMITIDO] → [DADO OMITIDO] s, com [DADO OMITIDO] result sets equivalentes. [Experimento](pbip_performance_jit_experiment_2[DADO OMITIDO].log). O valor final depois do índice consta abaixo.

## [DADO OMITIDO]. Índice criado e candidato rejeitado

Mantido `ix_pbip_history_sales_cost_present`, em `(id_customer,data,tp_activity_level) INCLUDE(id_location,id_item) WHERE volume_unidades IS NOT NULL AND avg_price_cost IS NOT NULL`. Atende a prova EXISTS de produto calculável de Venda Custo, inclusive zero e cancelamento; não é uma aproximação do SUMX. O predicado é independente do tenant. DDL idempotente em `analytics-db/marts/[DADO OMITIDO]_pbip_performance_indexes.sql`.

Após JIT, ROI atividade [DADO OMITIDO] → [DADO OMITIDO] s no experimento do índice; MARKUP atividade [DADO OMITIDO] → [DADO OMITIDO] s. ROI filtrado não degradou materialmente: [DADO OMITIDO] → [DADO OMITIDO] s. Plano passou a Index Only Scan, [DADO OMITIDO] loops, aproximadamente [DADO OMITIDO] ms/lookup, zero Heap Fetches e zero Shared Read blocks no plano warm observado. [Planos/medidas intermediárias](pbip_performance_sales_index_experiment_2[DADO OMITIDO].log).

O candidato `ix_pbip_daily_customer_date` foi criado em [DADO OMITIDO] s e rejeitado: TVD ainda executava após [DADO OMITIDO] s, com espera de I/O e Index Scan no value_context escolhido por data. Capturado EXPLAIN sem ANALYZE completo; o replay em execução foi cancelado. Somente esse índice recém-criado foi removido; não há tempo final nem equivalência concluída desse candidato. DDL foi retirado do arquivo novo para não reaplicá-lo. [Prova da rejeição](pbip_performance_rejected_daily_index_2[DADO OMITIDO].json). Nenhum índice preexistente foi removido.

## [DADO OMITIDO]. Marts e CTEs

Nenhum mart/preagregação novo. Os onze marts e suas definições/contagens permanecem iguais. `tasks AS MATERIALIZED` foi testado apenas em sessão de leitura: quatro resultados equivalentes, default TVD [DADO OMITIDO] s / IVD [DADO OMITIDO] s, filtrado [DADO OMITIDO] / [DADO OMITIDO] s. Ganho pequeno frente à variância do replay após JIT; não publicado. Date/value context, SUMX Região, CNPJ, conversão e frozen_monthly não foram fundidos. [Experiência de CTE](pbip_performance_tasks_candidate_2[DADO OMITIDO].log).

## [DADO OMITIDO]. EXPLAIN AFTER

Os mesmos [DADO OMITIDO] SQLs receberam novo EXPLAIN completo. JIT está off; a mudança de plano de C1[DADO OMITIDO] é documentada por query, incluindo os sorts/spills que ainda existem. [Perfis BEFORE/AFTER e contadores](pbip_performance_profiles_2[DADO OMITIDO].json).

| Chart / query / cenário | Planning ms | Execution ms | Scans ativos | Temp written blocks |
|---|---|---|---|---|
| TVD - Pré-ruptura / [DADO OMITIDO] / default | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO], CTE Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| IVD - Excesso / [DADO OMITIDO] / default | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO], CTE Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| Giro / [DADO OMITIDO] / default | [DADO OMITIDO] | [DADO OMITIDO] | Seq Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| Giro / [DADO OMITIDO] / default | [DADO OMITIDO] | [DADO OMITIDO] | Seq Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| OSA / [DADO OMITIDO] / default | [DADO OMITIDO] | [DADO OMITIDO] | Seq Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| Vendas / [DADO OMITIDO] / default | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| Vendas / [DADO OMITIDO] / default | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO], Index Scan:[DADO OMITIDO], CTE Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| Estoque / [DADO OMITIDO] / default | [DADO OMITIDO] | [DADO OMITIDO] | Seq Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| ROI / [DADO OMITIDO] / default | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| ROI / [DADO OMITIDO] / default | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| ROI / [DADO OMITIDO] / default | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO], Index Scan:[DADO OMITIDO], CTE Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| MARKUP / [DADO OMITIDO] / default | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| MARKUP / [DADO OMITIDO] / default | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| MARKUP / [DADO OMITIDO] / default | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO], Index Scan:[DADO OMITIDO], CTE Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| TVD - Pré-ruptura / [DADO OMITIDO] / filtered | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO], CTE Scan:[DADO OMITIDO], Index Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| IVD - Excesso / [DADO OMITIDO] / filtered | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO], CTE Scan:[DADO OMITIDO], Index Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| Giro / [DADO OMITIDO] / filtered | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO], CTE Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| Giro / [DADO OMITIDO] / filtered | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO], CTE Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| OSA / [DADO OMITIDO] / filtered | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO], CTE Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| Vendas / [DADO OMITIDO] / filtered | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO], CTE Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| Vendas / [DADO OMITIDO] / filtered | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO], CTE Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| Estoque / [DADO OMITIDO] / filtered | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO], CTE Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| ROI / [DADO OMITIDO] / filtered | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO], CTE Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| ROI / [DADO OMITIDO] / filtered | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO], CTE Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| ROI / [DADO OMITIDO] / filtered | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO], CTE Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| MARKUP / [DADO OMITIDO] / filtered | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO], CTE Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| MARKUP / [DADO OMITIDO] / filtered | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO], CTE Scan:[DADO OMITIDO] | [DADO OMITIDO] |
| MARKUP / [DADO OMITIDO] / filtered | [DADO OMITIDO] | [DADO OMITIDO] | Subquery Scan:[DADO OMITIDO], Seq Scan:[DADO OMITIDO], Index Scan:[DADO OMITIDO], Index Only Scan:[DADO OMITIDO], CTE Scan:[DADO OMITIDO] | [DADO OMITIDO] |

## [DADO OMITIDO]. Tempos por query e cenários de filtro

Todas as [DADO OMITIDO] queries finais dos sete cenários foram executadas e repetidas imediatamente, sem Redis/resultado materializado de ChartData. As [DADO OMITIDO] default/filtrado foram comparadas também aos resultados BEFORE. Para os cinco filtros adicionais não há baseline físico anterior aos índices; não inventar speedup desses cenários.

| Cenário | SQL BEFORE s | SQL AFTER primeira s | SQL AFTER warm s | Queries |
|---|---|---|---|---|
| default | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| filtered | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede | não medido | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede_bandeira | não medido | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| produto | não medido | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| ap_conversao | não medido | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| combined | não medido | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |

Máscaras exatas em [cenários](pbip_performance_scenarios_2[DADO OMITIDO].json). Rede=ARMAZMATEUS; Rede+Bandeira=MATEUS SUPERMERCADOS; Produto=Societe [DADO OMITIDO]G; AP_CONVERSAO=quilograma, explicitamente aplicado ao contexto Jinja inclusive nos headlines; combinação real=Item Iogurte Liquido Morang Btv + Loja B6[DADO OMITIDO]. Default/filtrado preservam o mesmo protocolo do instrumento congelado, inclusive sua regra de injeção de nm_measure conforme colunas do dataset. Duas tentativas iniciais usaram Rede=MATEUS (inexistente), foram preservadas como `invalid_mask_attempt` e excluídas das medições finais.

## [DADO OMITIDO]. Dashboard default BEFORE/AFTER

SQL sequencial: **[DADO OMITIDO] → [DADO OMITIDO] s**, **[DADO OMITIDO]x**, redução **[DADO OMITIDO]**. Histórico anterior: [DADO OMITIDO] s. Não comparar diretamente esse total SQL com latência HTTP paralela ou browser.

## [DADO OMITIDO]. Dashboard filtrado BEFORE/AFTER

SQL sequencial: **[DADO OMITIDO] → [DADO OMITIDO] s**, **[DADO OMITIDO]x**, redução **[DADO OMITIDO]**. Histórico anterior: [DADO OMITIDO] s. Não comparar diretamente esse total SQL com latência HTTP paralela ou browser.

## [DADO OMITIDO]. Primeira execução, warm e limites de cold

Primeira execução significa primeira naquele instrumento; não é cold absoluto. PostgreSQL/OS já podiam conter páginas do workload, e CREATE INDEX aquece páginas. Não houve restart do Analytics, limpeza de buffers ou invalidação destrutiva. Before/after guardam primeira e repetição imediata separadas; EXPLAIN vem depois. Nenhum replay SQL usou Redis. Uma tentativa inicial do instrumento foi interrompida por comparação exata de floats; foi retomada nos charts [DADO OMITIDO]–[DADO OMITIDO] usando a tolerância contratual. Artefatos por query válidos compõem o baseline, não o total com repetições/EXPLAINs.

## [DADO OMITIDO]. API, cache, frontend e concorrência

HTTP real em `/api/v1/chart/data`, oito charts/[DADO OMITIDO] queries, autenticação admin local, primeiro sequencial force=True, depois oito requests paralelas force=True, depois duas repetições sequenciais force=False. Timer do grupo exclui login/CSRF; não inclui portal, opções, guest-token nem renderização de navegador. Force=True ignora cache; campo is_cached ausente nessa resposta não é convertido artificialmente em false. Repetições possuem is_cached=true em todas as [DADO OMITIDO] queries.

| Cenário | Execução API | Wall s | Cache |
|---|---|---|---|
| default | sequential_force | [DADO OMITIDO] | force=True, bypass |
| default | parallel_force | [DADO OMITIDO] | force=True, bypass |
| default | cache_repeat_1 | [DADO OMITIDO] | [DADO OMITIDO]/[DADO OMITIDO] hits |
| default | cache_repeat_2 | [DADO OMITIDO] | [DADO OMITIDO]/[DADO OMITIDO] hits |
| filtered | sequential_force | [DADO OMITIDO] | force=True, bypass |
| filtered | parallel_force | [DADO OMITIDO] | force=True, bypass |
| filtered | cache_repeat_1 | [DADO OMITIDO] | [DADO OMITIDO]/[DADO OMITIDO] hits |
| filtered | cache_repeat_2 | [DADO OMITIDO] | [DADO OMITIDO]/[DADO OMITIDO] hits |

[Resultados HTTP](pbip_performance_api_2[DADO OMITIDO].json), [[DADO OMITIDO] comparações de resultados HTTP contra SQL baseline](pbip_performance_api_equivalence_2[DADO OMITIDO].json). Normalização de serialização Decimal/inteiros usa os OIDs PostgreSQL; datas epoch são comparadas à data original. Os [DADO OMITIDO] replays diretos preservam tipos PostgreSQL, NULLs, quantidade, chaves e ordem. Tolerância float contratual: rel_tol=[DADO OMITIDO], abs_tol=[DADO OMITIDO].

Microbenchmark Node de buildQuery/transformProps, [DADO OMITIDO] chamadas/chart, linhas Gold reais e doubles das dependências Superset: máximo das médias por chart: buildQuery [DADO OMITIDO] ms; transformProps [DADO OMITIDO] ms. [Medição](pbip_performance_frontend_timings_2[DADO OMITIDO].log). Não é tempo de renderização de browser. Frontend ficou intacto.

O harness serializa consultas dentro de cada chart; na API paralela foram oito requisições concorrentes. Superset mantém [DADO OMITIDO] workers gthread / [DADO OMITIDO] threads na configuração local padrão. A concorrência foi medida, sem mudar essa configuração. Vendas/ROI/Markup repetem o mesmo contexto base mensal/atividade/U3M, mas com projeções de métricas diferentes; nenhum compartilhamento/cache de contexto novo foi introduzido. buildQuery gera [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] queries para TVD/IVD/Giro/OSA/Vendas/Estoque/ROI/Markup. Não se observou chamada por linha no harness; tráfego real de browser/N+[DADO OMITIDO] de opções não foi capturado. O teste de opções executa [DADO OMITIDO] seletores em [DADO OMITIDO] estados, separadamente das [DADO OMITIDO] queries de KPI; não é uma contagem de chamadas de um navegador.

## [DADO OMITIDO]. Tamanho dos objetos

Índice mantido: **[DADO OMITIDO] bytes ([DADO OMITIDO] MiB)**, **[DADO OMITIDO] entradas**, criação **[DADO OMITIDO] s**. Dependência única: gold.nr_pbip_overview_history; cinco colunas de chave/cobertura e predicado nullable descritos no DDL. Não há materialização nova. Tamanho do candidato rejeitado não foi capturado antes da remoção; não estimado.

Refresh futuro: o índice é mantido/reconstruído pelo REFRESH MATERIALIZED VIEW da relação existente. Não foi executado refresh nesta etapa nem medido seu custo adicional. Se a relação for recriada em uma migração futura, reaplicar o DDL idempotente [DADO OMITIDO] após a criação; o publicador já descobre os SQLs numerados. Configuração JIT é reaplicada pelo bootstrap Analytics, preservando outras opções. Não mudou estratégia de publicação, dependencies ou pipeline Gold.

## [DADO OMITIDO]. Regressão completa

| Gate | Resultado | Evidência |
|---|---|---|
| Python completo | [DADO OMITIDO] passed ([DADO OMITIDO] anteriores [DADO OMITIDO] configuração) | [log](pbip_performance_python_tests_2[DADO OMITIDO].log) |
| Frontend PBIP | [DADO OMITIDO] checks, sem reduzir baseline | cinco bundles executados novamente |
| Frontend genérico | [DADO OMITIDO] checks adicionais; total [DADO OMITIDO] | bundle base |
| F1[DADO OMITIDO]/F1[DADO OMITIDO]-C0[DADO OMITIDO]/C0[DADO OMITIDO]/C1[DADO OMITIDO]/C1[DADO OMITIDO]/ROI anual | PASS, expected anteriores intactos | [freeze](pbip_performance_freeze_2[DADO OMITIDO].json) |
| Opções | [DADO OMITIDO] comparações /[DADO OMITIDO] cenários; [DADO OMITIDO] negativas guest | [JSON](pbip_performance_options_runtime_2[DADO OMITIDO].json) |
| ChartData default e filtrado | [DADO OMITIDO] charts por cenário; failures=[DADO OMITIDO] | [default](pbip_performance_chartdata_default_2[DADO OMITIDO].log) / [filtrado](pbip_performance_chartdata_filtered_2[DADO OMITIDO].log) |
| Replay direto BEFORE/AFTER | [DADO OMITIDO] sets + tipos/nulls/chaves/ordem equivalentes | [perfis](pbip_performance_profiles_2[DADO OMITIDO].json) |
| Replay SQL/Gold testemunhos | [DADO OMITIDO] contextos/dataset; nenhum campo mudou | [JSON](pbip_performance_replay_2[DADO OMITIDO].json) |
| C0[DADO OMITIDO] testemunho U3M | [DADO OMITIDO] preservado | [JSON](pbip_performance_c0[DADO OMITIDO]_frozen_replay_2[DADO OMITIDO].json) |
| Guest/RLS/override | PASS | [JSON](pbip_performance_guest_rls_2[DADO OMITIDO].json) |
| Health | [DADO OMITIDO] serviços/oneshot e HTTPs aprovados | [log](pbip_performance_health_2[DADO OMITIDO].log) |

Gates rodaram com carga de testes concorrente; os tempos de validate_overview (incluindo seus replays) não são o benchmark isolado da seção [DADO OMITIDO]/[DADO OMITIDO]. Não reutilizar esses tempos como regressão final. Item hidden NULL continua fora da certificação de opções, exatamente como no baseline F1[DADO OMITIDO]A; nenhum expected foi editado para mascarar isso.

## [DADO OMITIDO]. Estado salvo: [DADO OMITIDO] MATCH preservados

Reclassificação executada novamente contando cada um dos [DADO OMITIDO] registros: **[DADO OMITIDO] SEMANTIC_MATCH /[DADO OMITIDO] SEMANTIC_DIFFERENCE /[DADO OMITIDO] UNMAPPED**. Todas as linhas e provas são idênticas ao baseline anual. ROI MTD segue UNMAPPED, sem visual criado. Contextos explícitos conhecidos preservados; nenhuma extensão de certificação UI. [Classificação](pbi_superset_semantic_equivalence_performance_2[DADO OMITIDO].json).

## [DADO OMITIDO]. Contrato completo preservado

**[DADO OMITIDO] MATCH /[DADO OMITIDO] DIFFERENCE /[DADO OMITIDO] UNMAPPED**. F1[DADO OMITIDO]D está preservado em cada registro mapeado, com os mesmos limites de interação UI/bookmarks/hierarquias. Sucesso dos replays não remove F1[DADO OMITIDO]D.

## [DADO OMITIDO]. Valores Power BI

**[DADO OMITIDO] NO_PBI_VALUE**, todos pbi_value=null. Nenhum NUMERIC_MATCH/ROUNDING_ONLY foi criado. Valores de SQL/Gold/HTTP são provas internas BEFORE/AFTER, não observações do Power BI nem estimativas DAX.

## [DADO OMITIDO]. Guest/RLS e tenant isolation

Sessão embedded somente tenant [DADO OMITIDO]. Overrides [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] negados; [DADO OMITIDO] probes em seis datasets retornam dados para tenant autorizado e zero para outros; assinatura adulterada rejeitada. Datas máximas e opções AP/catálogo permaneceram iguais. Índice e conexão não têm hardcode de customer; tenant continua chave do índice. SQLs PBIP anteriores, inclusive seus limites de atendimento no deployment LACTALIS, não foram reescritos nem ampliados a tenants sem dados.

## [DADO OMITIDO]. Git diff --stat

```text
 scripts/publish_lactalis_marts.py                  |  [DADO OMITIDO] ++++++++++-
 superset/Dockerfile                                |   [DADO OMITIDO] +
 superset/bootstrap_analytics.py                    |   [DADO OMITIDO] +
 superset/bootstrap_overview.py                     |  [DADO OMITIDO] ++++++++++++-----
 .../plugin-chart-neoretail-kpi/src/buildQuery.js   |  [DADO OMITIDO] ++-
 .../src/transformProps.js                          | [DADO OMITIDO] ++++++++++++++++++---
 superset/validate_overview.py                      |  [DADO OMITIDO] ++++++-
 [DADO OMITIDO] files changed, [DADO OMITIDO] insertions(+), [DADO OMITIDO] deletions(-)
```

Diffstat é acumulado da worktree e não inclui arquivos untracked. Escopo novo desta etapa: bootstrap_analytics.py (duas linhas), helper analytics_performance.py, sete testes de configuração, DDL [DADO OMITIDO]. Os demais arquivos modificados/untracked já estavam no snapshot inicial.

## [DADO OMITIDO]. Git status --short

```text
 M scripts/publish_lactalis_marts.py
 M superset/Dockerfile
 M superset/bootstrap_analytics.py
 M superset/bootstrap_overview.py
 M superset/frontend-plugin/plugin-chart-neoretail-kpi/src/buildQuery.js
 M superset/frontend-plugin/plugin-chart-neoretail-kpi/src/transformProps.js
 M superset/validate_overview.py
?? analytics-db/marts/[DADO OMITIDO]_pbip_overview_calendar.sql
?? analytics-db/marts/[DADO OMITIDO]_pbip_overview_context.sql
?? analytics-db/marts/[DADO OMITIDO]_pbip_filters_conversion.sql
?? analytics-db/marts/[DADO OMITIDO]_pbip_conversion_direction.sql
?? analytics-db/marts/[DADO OMITIDO]_pbip_performance_indexes.sql
?? local-engine/tests/fixtures/pbip_c1[DADO OMITIDO]_dax_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_f1[DADO OMITIDO]_final_evidence_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_f1[DADO OMITIDO]_selectors_pbip_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_f1[DADO OMITIDO]_c0[DADO OMITIDO]_dax_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_filters_conversion_real_rows_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_lactalis_overview_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_lactalis_real_contract_rows_2[DADO OMITIDO].json
?? local-engine/tests/test_analytics_performance.py
?? local-engine/tests/test_pbip_c0[DADO OMITIDO]_sellout_u3m.py
?? local-engine/tests/test_pbip_c1[DADO OMITIDO]_cost_blank.py
?? local-engine/tests/test_pbip_c1[DADO OMITIDO]_operator_contract.py
?? local-engine/tests/test_pbip_f1[DADO OMITIDO]_final_evidence.py
?? local-engine/tests/test_pbip_f1[DADO OMITIDO]_selectors.py
?? local-engine/tests/test_pbip_f1[DADO OMITIDO]_c0[DADO OMITIDO]_daily_context.py
?? local-engine/tests/test_pbip_filter_conversion_contract.py
?? local-engine/tests/test_pbip_lactalis_overview.py
?? local-engine/tests/test_pbip_roi_annual_blank.py
?? superset/diagnose_lactalis_inventory.py
?? superset/frontend-extension/pbipSelectorDependencies.mjs
?? superset/frontend-extension/register-pbip-selectors.mjs
?? superset/frontend-extension/test-pbip-selectors.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-c0[DADO OMITIDO]-contract.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-c1[DADO OMITIDO]-contract.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-c1[DADO OMITIDO]-contract.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-contract.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-roi-annual-blank-contract.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-tvd-ivd-contract.mjs
?? superset/neoretail_bootstrap/core/analytics_performance.py
?? superset/neoretail_bootstrap/pbip_overview/
?? superset/profile_lactalis_osa_filtered.py
```

## [DADO OMITIDO]. Sem commit/push e operações preservadas

HEAD e branch continuam `[DADO OMITIDO]d2f5[DADO OMITIDO]b5[DADO OMITIDO]ead1bae9af6d2ef7b7[DADO OMITIDO]f9a4[DADO OMITIDO]ae` / `feat/osa-industry-certification`. Sem commit, push, merge, troca de branch, alteração da main, reset/clean ou edição de .gitignore/exclude. Nenhum arquivo apagado. Nenhuma alteração/reprocessamento de Bronze/Silver/Gold, refresh de mart, mart removido, volume apagado, down -v ou prune. Apenas o índice candidato criado nesta etapa foi removido após regressão comprovada; o índice mantido acrescenta acesso físico sem editar linhas. PR não foi alterada.

## [DADO OMITIDO]. Gargalos restantes e limites

O custo sem cache permanece nos scans e joins do contexto diário TVD/IVD sobre [DADO OMITIDO] milhões de registros, avaliação de data/valor em contextos independentes e cálculo regional de U3M repetido em três charts. O índice parcial remove a leitura ampla para provar BLANK, mas não substitui esses scans nem elimina bridge/AP. HTTP paralelo medido ainda fica acima de [DADO OMITIDO] s; não foi demonstrado <[DADO OMITIDO] s nem E2E de navegador. Cache é uma segunda camada comprovada e está separado do ganho SQL. O caminho futuro de maior impacto exigiria avaliar compartilhamento/preagregação com granularidade de filtros e contextos separados; não foi publicado um mart especulativo nesta etapa.

Critério cumprido: ganho SQL material (aproximadamente [DADO OMITIDO] default /[DADO OMITIDO] filtrado), sem nenhuma diferença nos contratos congelados ou nos resultados internos comparados. Não declarar performance universal a partir dos sete cenários locais.
