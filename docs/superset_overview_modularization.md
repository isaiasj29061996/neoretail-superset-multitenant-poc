# Overview — modularização dos contratos

## Base e escopo

- Base: `origin/feat/osa-industry-certification`, `71184f2225c41c594fd4bfb2fc4be2ee79a9036b` (merge PR #14).
- Branch: `refactor/superset-overview-modules`.
- Worktree: `.worktrees/superset-overview-modules`.
- A worktree original e suas alterações anteriores são preservadas. Preparação em dois commits, sem abrir PR ou fazer merge.
- Nenhuma mudança em fórmulas, SQL funcional, marts, frontend, Docker, pipeline ou tenants.

## Auditoria antes da alteração

O entrypoint original foi lido integralmente antes da implementação. Possuía 482 linhas, 10 funções e 9 constantes, incluindo criação da aplicação, consultas de datas, persistência, oito charts, filtros e apresentação. O mapa de extração foi apresentado antes de modificar o código.

| Consumidor | Imports originais de bootstrap_overview | Localização depois |
|---|---|---|
| Overview Quantity | overview_native_filters, position_json | overview.filters, overview.presentation |
| Panorama | HISTORY_SQL, M, overview_native_filters | overview.semantics, overview.filters |
| OSA original | HISTORY_SQL, M, OVERVIEW_M, native_filters | overview.semantics, overview.filters |
| OSA Certificada | overview_native_filters | overview.filters |
| Stock Optimization | headline_semantic_sql | overview.semantics |

Consumidores de fonte encontrados: `test_overview_metric_semantics.py` e `scripts/validate_project.py`. O contrato local de Quantity lê seu próprio entrypoint, cujo corpo permanece intacto. Os validadores SQL Overview/Quantity/Stock leem metadados e não exigem mudança de localização de símbolos.

## Estrutura depois

```text
superset/bootstrap_overview.py                 # aplicação, datasets e persistência
superset/neoretail_bootstrap/overview/
  __init__.py                                 # pacote, sem imports eager
  semantics.py                                # contratos semânticos certificados
  filters.py                                  # contratos específicos de filtros
  presentation.py                             # specs e layout do Overview
```

O entrypoint preserva sua execução por `main()`. `main()` mantém o mesmo provisionamento, consultas de datas, ordem de upserts, lookup do dashboard, CSS, metadados, associações e commit. A única extração em seu corpo é o bloco de specs dos charts, chamado agora por `chart_specs`.

## Inventário completo

| Proprietário | Símbolos originais movidos |
|---|---|
| semantics | HISTORY_SQL, M, OVERVIEW_M, ROI_COMPONENTS, MARKUP_COMPONENTS, TVD_DAILY, IVD_DAILY, headline_semantic_sql, overview_semantic_sql, osa_semantic_sql |
| filters | HEADLINE_FILTER_COLUMNS, sql_filter, _filter_definitions, _native_filters_for_targets, native_filters, overview_native_filters |
| presentation | position_json |

Os **17 símbolos** preservam suas árvores sintáticas. `chart_specs(tvd_daily, ivd_daily, summary, osa_summary, tvd_max_date, ivd_max_date)` contém as mesmas instruções originais de `tvd_recent`, `ivd_recent` e `specs`, acrescentando apenas o retorno da lista. O bloco foi comparado via AST e os parâmetros produzidos foram comparados com a fonte original para datas presentes e ausentes.

`DASHBOARD_TITLE` e `main` continuam definidos no entrypoint. Nenhuma regra legada foi removida.

## Reexports e dependências

O entrypoint reexporta explicitamente todos os 17 símbolos movidos, inclusive os privados, e continua expondo os helpers que importava de core: `chart_params`, `_jinja_filter_predicates`, `upsert_dataset`, `upsert_chart` (alias de `upsert_overview_chart`) e `metric`.

Não restam consumidores produtivos no repositório importando contratos de `bootstrap_overview`. Testes de compatibilidade verificam os reexports; consumidores externos desconhecidos continuam protegidos pela interface preservada. Não se infere autorização para remover um símbolo pela ausência de uso interno.

Dependências do novo pacote:

- semantics → core.metrics, core.filters e overview.filters (allowlist dimensional);
- presentation → core.chart_params, overview.semantics, overview.filters e json;
- filters → nenhum bootstrap, framework ou outro dashboard.

Nenhum módulo do pacote importa Superset/SQLAlchemy ou abre conexão. A persistência permanece no entrypoint. `sql_filter` preserva o default específico `filter_recent_period`; sua consolidação com builders de outros dashboards não integra esta fase.

Dependências residuais preservadas: Panorama → bootstrap_overview_quantity para Q/quantity_semantic_sql; OSA Certificada/matrizes → panorama.filters para WEEKLY_FILTER_COLUMNS; validador Export → bootstrap_export para seus contratos públicos. Nenhuma delas foi ampliada.

## Testes

O teste existente de semântica Overview lê agora o entrypoint junto aos três módulos canônicos. `scripts/validate_project.py` inclui essas fontes no inventário que já inspeciona. Todas as assertions desses arquivos foram comparadas com a base via AST e permanecem iguais. O guard da Fase 1 deixou de permitir imports de contratos pelo bootstrap Overview.

O novo teste arquitetural verifica ownership, dependências, ausência de duplicação de helpers core, reexports, consumers canônicos e papel do entrypoint. A referência `fixtures/overview_modules_baseline.json` foi gerada do Overview original da base, não da implementação nova, e cobre:

- 17 árvores sintáticas normalizadas entre versões Python;
- 4 templates SQL comparados byte a byte (Overview, OSA, TVD e IVD);
- 5 composições de filtros, incluindo defaults, cascatas, targets e IDs;
- serialização exata de position_json com IDs, UUIDs e títulos;
- specs completos dos oito charts com datas presentes/ausentes;
- bloco de composição original dos charts.

Os testes Jinja adicionais exercitam as 13 dimensões com IN/NOT IN para Overview e OSA, alias h no histórico, caminho compacto e proteção de cardinalidade da seleção de medida. A cobertura Panorama anterior, inclusive UF=RJ, Item, IN/NOT IN e proteção semanal contra l.uf, não foi alterada.

Regressão em cópia isolada no container Local Engine, com `-q -p no:cacheprovider`:

- test_bootstrap_architecture.py
- test_overview_module_architecture.py
- test_overview_metric_semantics.py
- test_panorama_module_architecture.py
- test_panorama_comparison_contracts.py
- test_panorama_inventory_tabs_contracts.py
- test_panorama_kpi_dimension_contracts.py
- test_panorama_sales_contracts.py
- test_panorama_stock_contracts.py
- test_osa_industry_certified_contracts.py
- test_local_contracts.py

Resultado: **273 passed, 2 failed**. As únicas falhas são as duas preexistentes: expectativa textual sem espaço em `("Valor",[` no contrato OSA e catálogo esperado sem `osa_certified` no contrato local. Nenhuma assertion foi relaxada, nenhum teste pulado e nenhum problema de negócio foi corrigido nesta fase.

O runner seleciona HOST_ROOT somente na cópia descartável do teste Overview para evitar sua preferência preexistente pelo `/repo` montado de outra worktree. Artefatos de validação ficam fora da branch.

## Metadados, idempotência e queries

A comparação real usa a aplicação Superset instalada e uma única transação, substituindo commit por flush. Executa a base, a versão modular e a versão modular pela segunda vez; o rollback final restaura o snapshot inicial.

Entrypoints incluídos: Overview, Overview Quantity, Panorama, OSA original, OSA Certificada e Stock Optimization. São comparados todos os datasets, colunas, métricas, charts, IDs/UUIDs, SQL armazenado, parâmetros, descrições, dashboards, slugs, layout/CSS, native filters, associações, embedding e RLS (cláusulas, roles e tabelas).

Contagens protegidas: Overview 8, Quantity 8, Panorama 36, OSA original 7, OSA Certificada 14, Stock 10.

Resultado da execução real: **aprovado, exit code 0**. Os seis bootstraps foram executados três vezes (base, modular, modular novamente); snapshots completos permaneceram idênticos. As seis contagens de charts foram preservadas, RLS não mudou e o rollback restaurou o snapshot inicial completo. Logs persistentes: `/tmp/overview_modules_metadata.log` no container Superset. Validadores de queries existentes Overview/Quantity/Stock também são executados sem alterar seus arquivos; log `/tmp/overview_modules_queries.log`.

Os três validadores de queries concluíram com exit code 0. Overview consultou seus oito charts sem erro. Quantity reconciliou fonte/mart, componentes, tasks, períodos conforme os limites de calendário já documentados, sete opções de medida e fallback detalhado com filtro. Stock Optimization executou seus dez charts sem erro.

Esses validadores consultam os metadados publicados no ambiente existente; não aplicam o bootstrap candidato. A prova da equivalência dos metadados candidatos é feita separadamente na transação com rollback descrita acima. A reconciliação não amplia a certificação dos limites de calendário ou dados já existentes.

## Imagem sem bind mount

Build aprovado com o Dockerfile existente:

```text
docker build --progress plain -t neoretail-superset-overview-modules:review .worktrees/superset-overview-modules/superset
```

Probe com container `--rm --network none --read-only`, sem volumes, `PYTHONPATH=/app/pythonpath`: **15 imports aprovados**, incluindo os nove bootstraps, matrizes OSA, core e o pacote Overview com seus três módulos. Os contratos são carregados de `/app/pythonpath`; reexports e o alias de upsert Overview preservam a identidade dos objetos canônicos. Não há conexão ao banco nesse probe.

Nenhuma alteração no Dockerfile/Compose. O COPY recursivo já existente inclui o novo pacote.

## Riscos e resíduos

- Reexports continuam necessários para compatibilidade; sua remoção exige uma etapa explícita posterior.
- O entrypoint ainda é responsável por persistência, CSS e composição de metadados; isso é intencional neste escopo.
- Defaults e targets dos filtros não foram reinterpretados, mesmo quando seus parâmetros podem parecer simplificáveis.
- A inspeção visual manual foi concluída e aprovada pelo responsável: Overview com oito charts, filtros nativos e em cascata, filtro dimensional, atualização de cards/gráficos, Quantity, Panorama, OSA original, OSA Certificada e Stock Optimization. Não foram observados erros SQL, charts ausentes, filtros desconectados ou quebras visuais. Não houve teste ponta a ponta de Guest Token; embedding e RLS são protegidos pela comparação de metadados e pelos contratos existentes.
- As duas falhas preexistentes permanecem documentadas.
- O guard mais restrito impede reintroduzir imports de contratos pelo entrypoint Overview.

## Arquivos

Criados: os quatro arquivos do pacote Overview, `overview_contract_sources.py`, `test_overview_module_architecture.py`, `fixtures/overview_modules_baseline.json` e este documento.

Alterados: o bootstrap Overview, os cinco consumidores da tabela inicial, `test_overview_metric_semantics.py`, `test_bootstrap_architecture.py` e `scripts/validate_project.py`.

Nenhum cache, arquivo temporário, screenshot ou artefato generated foi transportado. `embedded-app/server.js` não pertence ao diff.

A conferência final comparou HEAD, status completo e hashes de todos os arquivos locais modificados/não rastreados da worktree original com o snapshot anterior à criação desta worktree: nenhum mudou. Na conferência anterior aos commits, o stage da nova worktree estava vazio.

## Git diff --stat e status antes dos commits

```text
 local-engine/tests/test_bootstrap_architecture.py  |   4 -
 .../tests/test_overview_metric_semantics.py        |   4 +
 scripts/validate_project.py                        |   3 +
 superset/bootstrap_osa_industry.py                 |   3 +-
 superset/bootstrap_osa_industry_certified.py       |   2 +-
 superset/bootstrap_overview.py                     | 393 ++-------------------
 superset/bootstrap_overview_quantity.py            |   3 +-
 superset/bootstrap_panorama.py                     |   3 +-
 superset/bootstrap_stock_optimization.py           |   2 +-
 9 files changed, 42 insertions(+), 375 deletions(-)
```

O diff --stat inclui os nove arquivos rastreados. Os oito arquivos novos continuam untracked e aparecem na lista completa abaixo; nenhum arquivo foi adicionado ao stage.

```text
## refactor/superset-overview-modules...origin/feat/osa-industry-certification
 M local-engine/tests/test_bootstrap_architecture.py
 M local-engine/tests/test_overview_metric_semantics.py
 M scripts/validate_project.py
 M superset/bootstrap_osa_industry.py
 M superset/bootstrap_osa_industry_certified.py
 M superset/bootstrap_overview.py
 M superset/bootstrap_overview_quantity.py
 M superset/bootstrap_panorama.py
 M superset/bootstrap_stock_optimization.py
?? docs/superset_overview_modularization.md
?? local-engine/tests/fixtures/overview_modules_baseline.json
?? local-engine/tests/overview_contract_sources.py
?? local-engine/tests/test_overview_module_architecture.py
?? superset/neoretail_bootstrap/overview/__init__.py
?? superset/neoretail_bootstrap/overview/filters.py
?? superset/neoretail_bootstrap/overview/presentation.py
?? superset/neoretail_bootstrap/overview/semantics.py
```
