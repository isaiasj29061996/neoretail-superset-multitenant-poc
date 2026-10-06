# OSA Certificada — extração conservadora

## Base e escopo

- Base: `origin/feat/osa-industry-certification`, `09d7c06e9e32062c0312331954fb8e3de43cf37e` (merge da modularização Overview).
- Branch: `refactor/superset-osa-certified-modules`.
- Worktree: `.worktrees/superset-osa-certified-modules`.
- Preparação em dois commits, sem abrir PR ou fazer merge. Nenhuma outra worktree recebeu alterações de arquivos.
- Fora do escopo: frontend, Dockerfile, Compose, tenants, pipeline, embedding, RLS e `embedded-app/server.js`.

## Estrutura e ownership

```text
superset/bootstrap_osa_industry_certified.py       # runtime e persistência
superset/osa_certified_matrices.py                # fachada explícita
superset/neoretail_bootstrap/osa_certified/
  __init__.py
  semantics.py
  matrices.py
  filters.py
  presentation.py
```

| Módulo | Contratos |
|---|---|
| semantics | PERIODS; monthly_overview_sql; weekly_overview_sql; cause_period_sql; period_options_sql; TOP_VALUE_METRICS; TOP_QTY_METRICS; CAUSE_VALUE; CAUSE_QTY |
| filters | DIMENSION_OVERRIDES; _dimension_nulls; _measure_filter; _period_filter; composição native_filters com exclusão dos quatro timelines |
| matrices | Conteúdo integral do auxiliar original: MATRIX_SCOPES; DIMENSION_OVERRIDES; _measure_filter; _period_rows; matrix_period_sql; TABLE_VALUE; TABLE_QTY; TABLE_PROBLEMS; TABLE_OSA |
| presentation | _top_params; _cause_params; _matrix_params; chart_specs; position_json; CSS |
| entrypoint | DASHBOARD_TITLE; DASHBOARD_SLUG; PREFIX; main; aplicação/contexto, banco, upserts, associação, serialização de position_json/json_metadata, commit e relatório de IDs |

Os SQLs foram movidos como blocos completos. Os helpers homônimos de matrizes continuam independentes. Os novos módulos não inicializam Superset nem persistem metadados.

Reexports explícitos mantêm os símbolos anteriores do bootstrap, inclusive funções privadas e aliases MATRIX_*, além dos imports core/Overview/Panorama anteriormente expostos. A fachada de matrizes mantém seus nove símbolos próprios e seus imports legados. Nenhum import estrela foi introduzido.

As dependências seguem core.*, overview.filters e panorama.filters. WEEKLY_FILTER_COLUMNS mantém 14 colunas; o gerador genérico continua com 13 dimensões. Não foram consolidados os dois contratos. `l.uf` permanece nos trechos que possuem JOIN com `dim_local l`.

## Baseline e regressão

`fixtures/osa_certified_modules_baseline.json` foi capturado antes da movimentação, executando os contratos originais e extraindo os símbolos de HEAD. Contém os sete SQLs completos (mensal, semanal, causas, opções de período e três matrizes), hashes AST normalizados, os 14 specs completos, métricas/formatos, layout, filtros/targets/exclusões e CSS.

Os novos testes comparam bytes de SQL e os 28 símbolos originais. Também renderizam os seis caminhos dimensionais com 13 dimensões × IN/NOT IN, incluindo UF=RJ e Item, além de medida default/IN/NOT IN. Protegem escalas, fontes temporais e `IS NOT DISTINCT FROM`.

Os guards Panorama e Overview foram ampliados para inspecionar os novos donos, conservando as verificações antigas. O leitor dos contratos OSA agora inclui as fontes canônicas; nenhuma assertion foi removida ou alterada. A identidade das assertions dos três testes modificados e do validador geral foi verificada por AST.

Regressão numa cópia isolada no container Local Engine, com `-q -p no:cacheprovider`:

- test_bootstrap_architecture.py;
- test_osa_certified_module_architecture.py;
- test_overview_module_architecture.py;
- test_overview_metric_semantics.py;
- test_panorama_module_architecture.py;
- test_panorama_comparison_contracts.py;
- test_panorama_inventory_tabs_contracts.py;
- test_panorama_kpi_dimension_contracts.py;
- test_panorama_sales_contracts.py;
- test_panorama_stock_contracts.py;
- test_osa_industry_certified_contracts.py;
- test_local_contracts.py.

Resultado: **489 passed, 2 failed**. São as duas falhas anteriores: literal textual das abas Valor/Quantidade e catálogo local esperado sem osa_certified. Nenhuma nova falha. O runner aponta ROOT para a cópia descartável apenas no teste Overview que prefere `/repo` de outra worktree.

`scripts/validate_project.py` continua parando nessa mesma assertion preexistente do catálogo de tenants. Sua lista de fontes foi ampliada para o novo pacote; os contratos não foram relaxados.

## Metadados e idempotência

Harness real Superset: execução original, execução modular e segunda execução modular, em uma transação com commit substituído por flush e rollback ao final. Snapshot inclui datasets/colunas/métricas/SQL, charts/parâmetros/descrições/IDs/UUIDs, dashboards/slugs/layout/CSS/native filters/relações, embedding e regras RLS com roles/tabelas.

Resultado: **exit code 0**. Snapshots original/modular/idempotente idênticos; rollback restaurou o snapshot inicial completo. OSA Certificada mantém 14 charts, sete datasets virtuais e a fonte física de filtros. Contagens dos demais dashboards também permaneceram intactas: Overview 8, Quantity 8, Panorama 36, OSA original 7, Stock 10 e Export 4+4.

Log fora da branch: `/tmp/osa_modules_metadata.log` no container Superset existente. A validação não publicou o bootstrap candidato no ambiente principal.

## SQL, períodos e Guest Token

O novo `superset/validate_osa_certified_modules.py` faz EXPLAIN em transação analítica somente leitura e executa fixtures temporais no PostgreSQL. Foram aprovados **174 casos de planejamento SQL** e **4 cenários temporais** (fragmentos de causas e matrizes × duas âncoras). Os casos incluem os quatro períodos, virada de ano, ausência de dezembro, datas máximas distintas e linhas posteriores à âncora dentro do mês, preservando a semântica existente.

A validação Guest usa a imagem candidata, sem volumes, uma cópia dos metadados em PostgreSQL temporário e cache NullCache. Roles, UUIDs de embedding e configurações RLS são herdados da cópia; não são modificados no principal. Os dados analíticos existentes são compartilhados somente para leitura, sem criar outro tenant.

São usados JWTs Guest reais assinados e verificados pelas APIs instaladas, autorização do dashboard e ChartDataCommand/QueryContext. Não existe filtro administrativo id_customer na query: a cláusula deve vir do JWT e aparecer no SQL executado. Compara cliente 142 com cliente inexistente -1 em seis datasets candidatos. SQL candidato é aplicado apenas na transação de metadados da cópia e revertido ao final. Tokens/segredos não são registrados.

Resultado: **exit code 0**, 174 verificações SQL, quatro cenários temporais e **12 verificações Guest RLS aprovadas**. Os seis datasets retornaram somente id_customer=142 para o token autorizado e nenhuma linha para -1. Cada QueryContext foi conferido contra o SQL candidato em sua própria sessão. A checagem final, por consulta nova ao banco, confirmou a restauração do SQL original na cópia de metadados. Os containers temporários e arquivos de dump/credenciais foram removidos após registrar o log fora da branch.

Limites: não é teste do navegador/SDK, não cria dados sintéticos para dois tenants existentes e não altera o catálogo. O probe de colunas verifica isolamento dos seis datasets; specs e metadados dos 14 charts são protegidos separadamente.

## Packaging

Build real com o Dockerfile inalterado: `neoretail-superset-osa-modules:review`. Digest de configuração: `cd4039b392580f3108215c1115629fb66e2a519c75906b7455a7ea5ed88d7adf`.

Container `--network none --read-only`, sem volumes, PYTHONPATH=/app/pythonpath: sete imports aprovados (entrypoint, fachada, pacote e quatro módulos). Todos carregaram de /app/pythonpath; identidade dos reexports de matrizes confirmada. O COPY recursivo existente inclui o pacote.

O validador adicional não foi adicionado ao packaging dos entrypoints; foi copiado explicitamente para o container temporário de testes, sem bind mount. Nenhuma mudança Docker/Compose.

## Riscos e resíduos

- Reexports são temporários, mas a remoção exige nova revisão de consumidores externos.
- Os períodos mantêm âncoras distintas: causas usam fonte de causas; matrizes usam histórico.
- Timelines mantêm escala 0–100; matriz %OSA mantém razão com formato percentual.
- Preservados JOINs, aliases, conversões, IS NOT DISTINCT FROM, seleção de medidas, targets e exclusão do período nos quatro timelines.
- As duas falhas preexistentes permanecem.
- Inspeção visual manual concluída e aprovada pelo responsável: 14 charts, Valor/Quantidade, Mensal/Semanal, causas/motivos, matrizes de região/varejo/item, filtros, período e layout. Nenhum erro visual ou SQL, chart ausente ou filtro desconectado foi observado. A aprovação manual complementa as validações automatizadas descritas acima.
- Nenhum cache, dump, token, screenshot ou artefato temporário está no diff. Os artefatos de testes ficam fora da worktree.

## Inventario de arquivos e Git antes da revisao

Criados (9):

- `docs/superset_osa_certified_modularization.md`
- `local-engine/tests/fixtures/osa_certified_modules_baseline.json`
- `local-engine/tests/test_osa_certified_module_architecture.py`
- `superset/neoretail_bootstrap/osa_certified/__init__.py`
- `superset/neoretail_bootstrap/osa_certified/filters.py`
- `superset/neoretail_bootstrap/osa_certified/matrices.py`
- `superset/neoretail_bootstrap/osa_certified/presentation.py`
- `superset/neoretail_bootstrap/osa_certified/semantics.py`
- `superset/validate_osa_certified_modules.py`

Alterados (6):

- `local-engine/tests/test_osa_industry_certified_contracts.py`
- `local-engine/tests/test_overview_module_architecture.py`
- `local-engine/tests/test_panorama_module_architecture.py`
- `scripts/validate_project.py`
- `superset/bootstrap_osa_industry_certified.py`
- `superset/osa_certified_matrices.py`

`git diff --stat` (arquivos rastreados; os nove novos estao listados acima):

```text
 .../tests/test_osa_industry_certified_contracts.py |   5 +
 .../tests/test_overview_module_architecture.py     |   2 +-
 .../tests/test_panorama_module_architecture.py     |   2 +-
 scripts/validate_project.py                        |   4 +
 superset/bootstrap_osa_industry_certified.py       | 635 +--------------------
 superset/osa_certified_matrices.py                 | 180 +-----
 6 files changed, 27 insertions(+), 801 deletions(-)
```

`git status --short --branch`:

```text
## refactor/superset-osa-certified-modules...origin/feat/osa-industry-certification
 M local-engine/tests/test_osa_industry_certified_contracts.py
 M local-engine/tests/test_overview_module_architecture.py
 M local-engine/tests/test_panorama_module_architecture.py
 M scripts/validate_project.py
 M superset/bootstrap_osa_industry_certified.py
 M superset/osa_certified_matrices.py
?? docs/superset_osa_certified_modularization.md
?? local-engine/tests/fixtures/osa_certified_modules_baseline.json
?? local-engine/tests/test_osa_certified_module_architecture.py
?? superset/neoretail_bootstrap/osa_certified/__init__.py
?? superset/neoretail_bootstrap/osa_certified/filters.py
?? superset/neoretail_bootstrap/osa_certified/matrices.py
?? superset/neoretail_bootstrap/osa_certified/presentation.py
?? superset/neoretail_bootstrap/osa_certified/semantics.py
?? superset/validate_osa_certified_modules.py
```
