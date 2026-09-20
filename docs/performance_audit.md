# Auditoria de performance interativa — AMBEV

Data da medição: **18/09/2026**
Tenant: **AMBEV (`id_customer = 142`)**
Ambiente: POC local com PostgreSQL Analytics, Superset 6 e Redis.

Este documento registra o primeiro lote incremental da auditoria solicitada no
handoff técnico. Os números locais servem para comparar desenhos de serving;
eles não constituem SLA nem sizing do DW produtivo.

## Diagnóstico

Os gargalos eram causados principalmente pela quantidade de linhas processadas:

- a Exportação multiplicava cada linha física por nove indicadores;
- TVD e IVD agregavam cerca de 14 milhões de linhas para devolver 180 dias;
- o Panorama semanal agregava cerca de 12,5 milhões de linhas;
- os dropdowns executavam `DISTINCT` em marts de 1–5 GB;
- distribuição/sortimento calculava dois `COUNT(DISTINCT ...)` na mart mensal;
- perdas OSA varria aproximadamente 5,2 milhões de linhas.

No `EXPLAIN (ANALYZE, BUFFERS)` anterior, tanto TVD quanto IVD fizeram `Seq
Scan`, leram **503.296 blocos** e levaram **3,78 s** e **3,60 s** diretamente no
PostgreSQL. Não houve spill: o custo dominante era I/O sobre o grão detalhado.

## Mudanças implementadas

### Exportação

O `CROSS JOIN` com nove indicadores foi removido. O filtro `Indicador` usa uma
dimensão de nove linhas e o dataset Jinja projeta somente o indicador escolhido.
O valor é validado por allowlist antes de ser inserido no SQL. O limite do chart
foi alinhado a `ROW_LIMIT`/`SQL_MAX_ROW`: **100.000 linhas**.

### Filtros nativos

`gold.nr_filter_options` reúne, por tenant, as combinações necessárias às
cascatas de localização, produto, atividade e unidade. Os dropdowns consultam
64.100 linhas em vez das marts analíticas. O valor selecionado continua sendo
aplicado ao dataset de cada chart pelo Superset.

### Caminho compacto com fallback detalhado

Foram adicionadas as seguintes marts:

| Arquivo | Mart | Grão compacto |
|---|---|---|
| `35_stock_headline_performance.sql` | `nr_tvd_daily_summary` | tenant × dia |
| `35_stock_headline_performance.sql` | `nr_ivd_daily_summary` | tenant × dia |
| `36_panorama_weekly_summary.sql` | `nr_panorama_weekly_summary` | tenant × semana |
| `37_interactive_p1_summary.sql` | `nr_overview_default_summary` | tenant × mês × nível de atividade |
| `37_interactive_p1_summary.sql` | `nr_overview_distinct_summary` | tenant × mês |
| `37_interactive_p1_summary.sql` | `nr_osa_causes_summary` | tenant × mês × motivo × causa |
| `38_export_retail_summary.sql` | `nr_export_daily_retail_summary` | tenant × dia × rede |
| `38_export_retail_summary.sql` | `nr_export_monthly_retail_summary` | tenant × mês × rede |

Cada dataset virtual usa a mart compacta no estado padrão. Quando recebe um
filtro dimensional, o Jinja seleciona a mart detalhada e o filtro é aplicado
normalmente. Isso mantém as combinações arbitrárias de rede, local e produto sem
duplicar as marts detalhadas.

## Resultado cold-cache

| Visual | Baseline | Depois | Redução aproximada |
|---|---:|---:|---:|
| Exportação mês — Produto | 25,31 s | 1,08 s | 95,7% |
| Exportação mês — Varejo | 10,40 s | 1,19 s | 88,6% |
| Exportação dia — Produto | 6,80 s | 2,55 s | 62,6% |
| Exportação dia — Varejo | 14,29 s | 0,39 s | 97,2% |
| TVD — Visão geral | 25,11 s* | 0,38 s | 98,5% |
| IVD — Visão geral | 44,73 s* | 0,14 s | 99,7% |
| Panorama vendas semanal | 4,80 s | 0,77 s | 84,1% |
| Panorama estoque semanal | 2,49 s | 0,15 s | 94,1% |
| Panorama Giro/ROI semanal | 2,26 s | 0,15 s | 93,2% |
| Panorama OSA semanal | 2,04 s | 0,13 s | 93,5% |
| Distribuição e sortimento | 5,48 s | 0,29 s | 94,6% |
| OSA — Perdas | 2,14 s | 0,61 s | 71,7% |
| Visão Geral — 8 charts sequenciais | 6,127 s | 1,530 s | 75,0% |

`*` TVD/IVD foram repetidos numa rodada fria antes da mudança e variaram acima
do baseline histórico de 4,49 s/4,58 s. O `EXPLAIN` isolado confirmou o mesmo
plano e o mesmo volume lido. Depois, o PostgreSQL executou as consultas compactas
em **0,30 ms** (TVD) e **0,22 ms** (IVD), lendo 5 e 2 blocos.

Os filtros nativos passaram de até **3,10 s** para **0,004–0,218 s**; a maior
parte ficou abaixo de 0,05 s.

## Reconciliação funcional

- os nove indicadores de Exportação retornaram 27 períodos, sem `CROSS JOIN`;
- o resumo de Varejo diário reconciliou todas as linhas e componentes com delta zero;
- TVD/IVD mantiveram as contagens exatamente; a maior diferença de soma foi
  `2,98e-08`, causada pela ordem da soma em `double precision`;
- os componentes semanais mantiveram contagens e tiveram delta máximo de
  `1,37e-06` nas somas em ponto flutuante;
- distribuição/sortimento usa cardinalidades exatas calculadas na mesma fonte;
- perdas OSA agrega o mesmo componente `qtd_perda_osa × preco_medio`;
- o resumo padrão da Visão Geral reconciliou 142 de 142 grupos mensais/de
  atividade sem divergência nos componentes usados pelos seis cards;
- os fallbacks detalhados foram exercitados com `rede = AKKIATACADO` e retornaram
  dados para TVD, IVD, semanal, distribuição e OSA.

Para a Visão Geral, o fallback também foi exercitado com `rede = ANGELONI`: os
seis cards escolheram `nr_overview_summary`, enquanto o estado sem filtro usou
`nr_overview_default_summary`. No `EXPLAIN (ANALYZE, BUFFERS)` da consulta de
Giro por mês/atividade, o tempo caiu de **457,966 ms** para **0,303 ms** e o
plano deixou de percorrer aproximadamente 1,88 milhão de linhas. O caminho
compacto ocupa **88 KiB / 142 linhas**, contra **781 MiB / ~1,89 milhão de
linhas** no mart detalhado.

Todos os novos objetos preservam `id_customer`. O RLS e o Guest Token continuam
sendo a fronteira de isolamento; a escolha entre mart compacta e detalhada não
usa o tenant informado pela interface.

## Custo de refresh local

| Lote | Tempo |
|---|---:|
| `34_native_filter_options.sql` | 1,81 s |
| `35_stock_headline_performance.sql` | 8,90 s |
| `36_panorama_weekly_summary.sql` | 28,74 s |
| `37_interactive_p1_summary.sql` | 35,45 s |
| `38_export_retail_summary.sql` | 13,39 s |

Na POC os objetos ainda são reconstruídos integralmente. No DW, esses contratos
devem virar tabelas incrementais/particionadas ou materializações equivalentes.

## Limitações e próximos passos

- Consultas com filtros dimensionais usam deliberadamente a mart detalhada e
  podem continuar mais lentas; precisam de benchmark por combinação frequente.
- `nr_panorama_opportunities` permanece grande e deve servir principalmente de
  fonte para marts menores.
- O teste de concorrência de backend/query para 1/5/10 usuários foi concluído;
  ainda faltam o teste E2E/HTTP, download CSV completo e benchmark conectado ao
  DW real. Resultados em [`load_testing.md`](load_testing.md).
- O próximo lote deve medir refresh incremental e as consultas filtradas mais
  frequentes antes de adicionar índices ou compute.

## Comandos de reprodução

```powershell
.\create-superset-kpi-views.ps1 -Only "34*"
.\create-superset-kpi-views.ps1 -Only "35*"
.\create-superset-kpi-views.ps1 -Only "36*"
.\create-superset-kpi-views.ps1 -Only "37*"
.\create-superset-kpi-views.ps1 -Only "38*"

docker compose exec -T superset `
  /app/.venv/bin/python /app/pythonpath/validate_export.py
docker compose exec -T superset `
  /app/.venv/bin/python /app/pythonpath/validate_stock_headlines.py
docker compose exec -T superset `
  /app/.venv/bin/python /app/pythonpath/validate_interactive_paths.py

.\profile-performance.ps1 -ColdCache
.\profile-performance.ps1 -ColdCache `
  -Dashboard neoretail-v9-panorama-industria `
  -Chart semanal
```
