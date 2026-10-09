# Panorama — Fase 2

## Branch e base

- Worktree: `.worktrees/superset-panorama-modules`.
- Branch: `refactor/superset-panorama-modules`.
- Base: `origin/feat/osa-industry-certification`, `07e09712a67da7327bd15e78f94ce55a1a96b4e0`, merge da Fase 1 (PR #13).
- A implementação e a validação inicial foram concluídas sem commit, stage, push ou merge. A preparação para publicação foi autorizada posteriormente, com a divisão em dois commits descrita abaixo.

## Dependências antes

O bootstrap Panorama concentrava SQL, métricas, charts, filtros, layout e persistência.

| Origem | Dependência | Contrato |
|---|---|---|
| Panorama | bootstrap_overview | HISTORY_SQL, M, overview_native_filters |
| Panorama | bootstrap_overview_quantity | Q, quantity_semantic_sql |
| Panorama | core | chart_params, filters, layout, metadata, metrics |
| Panorama | Superset/SQLAlchemy | aplicação, modelos e persistência |
| bootstrap_osa_industry_certified | bootstrap_panorama | WEEKLY_FILTER_COLUMNS |
| osa_certified_matrices | bootstrap_panorama | WEEKLY_FILTER_COLUMNS |

Os imports dos modelos ficavam dentro de `main()`. Não foi encontrado outro consumidor produtivo direto de símbolos Panorama. Cinco contratos de testes liam o monólito como texto.

## Estrutura depois

```text
superset/bootstrap_panorama.py      # entrypoint, integração e persistência
superset/neoretail_bootstrap/panorama/
  __init__.py
  sources.py       # contratos históricos/fonte semanal
  sales.py         # SQL e charts de vendas
  inventory.py     # SQL mensal/semanal, charts estoque/giro/ROI
  osa.py           # charts OSA
  gaps.py          # SQL/charts Falta x Excesso
  comparisons.py   # SQL/métricas/charts comparativos
  kpis.py          # SQL/controles/ordenação/charts KPI
  details.py       # SQL/métricas/charts análise detalhada
  filters.py       # dimensões e composição dos filtros nativos
  layout.py        # composição usando core.Layout
```

A proposta foi apresentada antes da implementação. KPI, análise detalhada e Falta x Excesso são responsabilidades já existentes. O SQL OSA integra o dataset certificado de inventário: permanece em Inventory para preservar esse contrato; os charts OSA têm proprietário próprio.

Os registradores recebem o callback `add` e os datasets existentes. `ensure_order_metrics` recebe a sessão e o modelo, sem abrir conexão. `panorama_native_filters` recebe a integração Overview por parâmetro. `build_layout` recebe os charts e opções já registrados. As instruções foram extraídas da composição original, preservando a ordem.

## Dependências residuais e compatibilidade

- O entrypoint continua integrando HISTORY_SQL/M/native filters de Overview e Q/quantity_semantic_sql de Overview Quantity. Nenhum módulo Panorama importa esses bootstraps.
- `DASHBOARD_TITLE`, `LATEST_SQL` e `P` permanecem no entrypoint. Os dois últimos são contratos legados preservados para compatibilidade.
- Os helpers genéricos de core anteriormente importados pelo entrypoint continuam disponíveis ali. Os módulos novos usam core diretamente.
- OSA Certificada e suas matrizes passam a importar `neoretail_bootstrap.panorama.filters.WEEKLY_FILTER_COLUMNS`. O valor do contrato não mudou.
- Imports entre módulos Panorama limitam-se a `filters`. Sales, Inventory, OSA, Comparisons e Layout não importam uns aos outros.
- Marts compartilhados continuam sendo contratos de dados. Esta fase não redefine seu SQL ou ownership no pipeline.
- Todos os 44 símbolos extraídos, inclusive privados, são reexportados explicitamente pelo entrypoint.

## Testes e cobertura

Os cinco contratos Panorama existentes só mudaram como localizam a fonte. Todas as assertions foram comparadas via AST com a base; nenhuma foi removida ou relaxada. O loader Jinja de inventário carrega a função em Inventory e o helper em core. No teste KPI, a busca do bloco de layout acompanha a indentação da nova função.

Cobertura semanal preservada: UF=RJ, UF IN/NOT IN, Item IN/NOT IN, os 13 filtros dimensionais, alias válido `w`, rejeição de `l.uf` e ramo mensal `f`. Nenhum teste foi pulado.

Os novos testes verificam limites de import, uso de core, ausência de helpers genéricos duplicados, consumidores canônicos, reexports explícitos e entrypoint como orquestrador. A permissão antiga para importar WEEKLY_FILTER_COLUMNS diretamente do bootstrap foi removida do guard da Fase 1.

`fixtures/panorama_phase2_baseline.json` foi gerado da fonte original da base: 44 hashes de AST normalizada e 23 hashes do SQL produzido. A normalização ignora campos opcionais vazios adicionados por versões novas do Python. O SQL é comparado byte a byte. Futuras mudanças funcionais certificadas exigirão atualização deliberada desta referência.

Execução em cópia isolada no container Local Engine, Python 3.11, com `python /tmp/run_phase2_tests.py ... -q`:

- test_bootstrap_architecture.py
- test_panorama_module_architecture.py
- test_panorama_comparison_contracts.py
- test_panorama_inventory_tabs_contracts.py
- test_panorama_kpi_dimension_contracts.py
- test_panorama_sales_contracts.py
- test_panorama_stock_contracts.py
- test_overview_metric_semantics.py
- test_osa_industry_certified_contracts.py
- test_local_contracts.py

Resultado: **179 passed, 2 failed**, sem novas falhas. Falhas preexistentes, mantidas sem alteração:

1. `test_value_and_quantity_dashboard_isolated_from_legacy_page`: expectativa textual `("Valor",[` não acompanha o espaço já existente no código OSA.
2. `test_v9_customer_registry_and_embedded_rls`: catálogo esperado não inclui `osa_certified`, já presente na configuração.

O runner corrige apenas a seleção preexistente de `/repo` no teste Overview dentro da cópia descartável, para usar esta worktree. Nenhum teste Overview foi modificado na branch.

## Metadados e idempotência real

Validação no Superset instalado, com aplicação/contexto únicos e `commit` substituído por `flush`. Foram executados o Panorama original da base, o Panorama modular e uma segunda execução modular na mesma transação. O `rollback` final restaurou o snapshot original completo.

Resultado: três execuções aprovadas, **36 charts** em todas. Snapshots de todos os datasets, colunas, métricas, charts, dashboards, associações, embedding e RLS foram comparados. IDs, UUIDs, SQL, parâmetros, nomes, slugs, publicação, layout, CSS, filtros nativos, domínios de embedding e regras RLS permaneceram idênticos.

Escopo de execução: `bootstrap_panorama.main()`. Demais entrypoints foram importados na imagem e seus contratos relevantes executados nos testes. Não foi executado `main()` dos outros dashboards. Guest Token e autenticação não foram exercitados de ponta a ponta; frontend, configurações e contratos RLS não mudaram.

Log persistente: `/tmp/panorama_phase2_metadata.log` no container Superset. Harness temporário: `/tmp/validate_panorama_phase2.py`. Artefatos de validação ficam fora da branch.

## Imagem real sem volumes

Build aprovado com `docker build --progress plain -t neoretail-superset-panorama-modules:phase2 .worktrees/superset-panorama-modules/superset`.

Probe com `docker run --rm --network none --read-only -e PYTHONPATH=/app/pythonpath --entrypoint /app/.venv/bin/python ...`: os 19 módulos/entrypoints importaram de `/app/pythonpath`, incluindo os seis bootstraps públicos, OSA Certificada, matrizes, core e os dez módulos Panorama. A identidade do reexport semanal foi confirmada. Sem volumes ou conexão ao banco nesse probe.

O COPY recursivo já introduzido na Fase 1 inclui automaticamente Panorama. Dockerfile e Compose ficaram intactos.

## Riscos e Fase 3

- Reexports mantêm compatibilidade; novos consumidores devem usar os módulos canônicos.
- A integração Overview/Quantity permanece no entrypoint. A próxima fase pode separar contratos dessas telas, com nova comparação de metadados.
- O entrypoint ainda provisiona datasets e persiste metadados. Separar catálogos de datasets seria escopo posterior, preservando suas identidades.
- A inspeção visual manual foi concluída e aprovada pelo usuário antes da autorização dos commits, conforme registrado abaixo.
- As duas falhas preexistentes merecem correção em escopo próprio.

## Escopo dos arquivos

Alterados: bootstrap Panorama, dois consumidores OSA, guard arquitetural da Fase 1 e cinco contratos Panorama. Criados: pacote Panorama (11 arquivos), helper de leitura dos contratos, teste arquitetural, fixture de paridade e este documento.

Nenhum arquivo temporário, cache ou generated foi transportado. `embedded-app/server.js`, frontend, Dockerfile, Compose, configurações de tenant e pipeline AMBEV não fazem parte do diff.

## Preparação para PR (revalidação em 2026-10-05)

Os dez arquivos de testes relacionados foram executados novamente: **179 passed, 2 failed**, somente as falhas preexistentes descritas acima. A validação real de metadados também foi repetida: base, versão modular e segunda execução modular preservaram os mesmos 36 charts, IDs, UUIDs, datasets, filtros, layouts, métricas e RLS. O rollback restaurou o snapshot inicial.

A tentativa de inspeção visual automatizada ficou bloqueada: o navegador integrado estava indisponível e o controle do Chrome retornou `Computer Use app approval timed out`. Os commits foram mantidos pendentes até a conclusão da inspeção manual.

Posteriormente, o usuário informou que realizou e aprovou a inspeção visual manual: Panorama abriu normalmente; foram verificados Vendas, Estoque Mensal, Estoque Semanal, OSA, Gaps, Comparisons, filtros nativos, troca Mensal/Semanal, UF=RJ e filtro por Item. Segundo o resultado informado pelo usuário, não houve quebra visual, erro SQL ou filtro desconectado. Essa aprovação autorizou os dois commits e o push da branch, sem abrir PR ou fazer merge.

A divisão autorizada é:

**Commit 1 — `refactor(superset): modularize panorama bootstrap` (14 arquivos)**

- `superset/bootstrap_panorama.py`
- `superset/bootstrap_osa_industry_certified.py`
- `superset/osa_certified_matrices.py`
- `superset/neoretail_bootstrap/panorama/__init__.py`
- `superset/neoretail_bootstrap/panorama/sources.py`
- `superset/neoretail_bootstrap/panorama/sales.py`
- `superset/neoretail_bootstrap/panorama/inventory.py`
- `superset/neoretail_bootstrap/panorama/osa.py`
- `superset/neoretail_bootstrap/panorama/gaps.py`
- `superset/neoretail_bootstrap/panorama/comparisons.py`
- `superset/neoretail_bootstrap/panorama/kpis.py`
- `superset/neoretail_bootstrap/panorama/details.py`
- `superset/neoretail_bootstrap/panorama/filters.py`
- `superset/neoretail_bootstrap/panorama/layout.py`

**Commit 2 — `test(superset): cover panorama module architecture` (10 arquivos)**

- `local-engine/tests/test_bootstrap_architecture.py`
- `local-engine/tests/test_panorama_module_architecture.py`
- `local-engine/tests/panorama_contract_sources.py`
- `local-engine/tests/fixtures/panorama_phase2_baseline.json`
- `local-engine/tests/test_panorama_comparison_contracts.py`
- `local-engine/tests/test_panorama_inventory_tabs_contracts.py`
- `local-engine/tests/test_panorama_kpi_dimension_contracts.py`
- `local-engine/tests/test_panorama_sales_contracts.py`
- `local-engine/tests/test_panorama_stock_contracts.py`
- `docs/superset_panorama_phase2.md`

Não há mudanças em server.js, frontend, Docker, tenant ou pipeline. A divisão não exige mudanças funcionais adicionais. Os arquivos serão adicionados ao stage por listas explícitas, separadamente para cada commit.

## Inventário completo dos símbolos extraídos

O inventário abaixo inclui funções, constantes e blocos da composição original.

| Module | Original symbols | Extracted main blocks |
|---|---|---|
| sources | `WEEKLY_SQL`, `OPPORTUNITIES_SQL`, `OPPORTUNITIES_LATEST_SQL`, `_WEEKLY_SELLOUT`, `WEEKLY_P`, `weekly_semantic_sql` | - |
| sales | `weekly_sales_semantic_sql`, `monthly_sales_semantic_sql`, `weekly_sales_card_semantic_sql` | `register_sales_charts` |
| inventory | `monthly_inventory_semantic_sql`, `weekly_inventory_card_semantic_sql` | `register_inventory_charts` |
| gaps | `GAP_TVD`, `GAP_IVD`, `monthly_gap_semantic_sql`, `weekly_gap_card_semantic_sql` | `register_gap_charts` |
| comparisons | `COMPARISON_SCOPES`, `_COMPARISON_SELLOUT`, `_COMPARISON_SALES_QTY`, `_COMPARISON_LOSS_QTY`, `_COMPARISON_PRICE`, `_COMPARISON_STOCK_QTY`, `COMPARISON_METRICS`, `COMPARISON_GAP_METRICS`, `_comparison_dimension_projection`, `comparison_history_sql`, `comparison_gap_sql` | `register_comparison_charts` |
| kpis | `KPI_DIMENSION_SCOPES`, `KPI_INDUSTRY_OPTIONS`, `KPI_DIMENSION_VALUE`, `_kpi_dimension_projection`, `_kpi_default_projection`, `kpi_dimension_sql`, `kpi_filter_options_sql`, `kpi_dimension_params`, `kpi_filter_bar_params` | `register_kpi_charts`, `ensure_order_metrics` |
| filters | `WEEKLY_FILTER_COLUMNS`, `KPI_ORDER_METRIC_NAME`, `KPI_MONTH_ORDER_METRIC_NAME`, `kpi_native_filters`, `sql_filter` | `panorama_native_filters` |
| details | `DETAIL_DIMENSIONS`, `detail_semantic_sql`, `DETAIL_METRICS`, `detail_table_params` | `register_detail_charts` |
| osa | - | `register_osa_charts` |
| layout | - | `build_layout` |

## Git status antes dos commits e lista exata dos arquivos

```text
 M local-engine/tests/test_bootstrap_architecture.py
 M local-engine/tests/test_panorama_comparison_contracts.py
 M local-engine/tests/test_panorama_inventory_tabs_contracts.py
 M local-engine/tests/test_panorama_kpi_dimension_contracts.py
 M local-engine/tests/test_panorama_sales_contracts.py
 M local-engine/tests/test_panorama_stock_contracts.py
 M superset/bootstrap_osa_industry_certified.py
 M superset/bootstrap_panorama.py
 M superset/osa_certified_matrices.py
?? docs/superset_panorama_phase2.md
?? local-engine/tests/fixtures/panorama_phase2_baseline.json
?? local-engine/tests/panorama_contract_sources.py
?? local-engine/tests/test_panorama_module_architecture.py
?? superset/neoretail_bootstrap/panorama/__init__.py
?? superset/neoretail_bootstrap/panorama/comparisons.py
?? superset/neoretail_bootstrap/panorama/details.py
?? superset/neoretail_bootstrap/panorama/filters.py
?? superset/neoretail_bootstrap/panorama/gaps.py
?? superset/neoretail_bootstrap/panorama/inventory.py
?? superset/neoretail_bootstrap/panorama/kpis.py
?? superset/neoretail_bootstrap/panorama/layout.py
?? superset/neoretail_bootstrap/panorama/osa.py
?? superset/neoretail_bootstrap/panorama/sales.py
?? superset/neoretail_bootstrap/panorama/sources.py
```

## Git diff --stat antes dos commits

```text
 local-engine/tests/test_bootstrap_architecture.py  |    1 -
 .../tests/test_panorama_comparison_contracts.py    |    4 +
 .../test_panorama_inventory_tabs_contracts.py      |    6 +-
 .../tests/test_panorama_kpi_dimension_contracts.py |    6 +-
 .../tests/test_panorama_sales_contracts.py         |   14 +-
 .../tests/test_panorama_stock_contracts.py         |    4 +-
 superset/bootstrap_osa_industry_certified.py       |    2 +-
 superset/bootstrap_panorama.py                     | 2015 +-------------------
 superset/osa_certified_matrices.py                 |    2 +-
 9 files changed, 118 insertions(+), 1936 deletions(-)
```

O snapshot acima foi capturado antes dos commits: o diff --stat inclui somente os nove arquivos então rastreados; os quinze arquivos novos apareciam como untracked e ainda não haviam sido adicionados ao stage.
