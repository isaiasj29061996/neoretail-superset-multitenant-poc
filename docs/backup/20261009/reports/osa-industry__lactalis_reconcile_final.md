> Cópia para GitHub: números de origem e identificadores numéricos omitidos. Original integral exige backup externo. Não usar esta cópia como fixture ou SQL executável.

# Reconciliacao segura LACTALIS ? relatorio final

Fechamento: [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (America/Sao_Paulo). Operacoes Git e testes iniciados em [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO].

Push normal concluido. Local/remoto: `[DADO OMITIDO]d2f5[DADO OMITIDO]b5[DADO OMITIDO]ead1bae9af6d2ef7b7[DADO OMITIDO]f9a4[DADO OMITIDO]ae`. PR #[DADO OMITIDO] OPEN, DRAFT, sem merge.

## [DADO OMITIDO]. Estado inicial e [DADO OMITIDO] commits remotos

Local: `[DADO OMITIDO]a1[DADO OMITIDO]dc1[DADO OMITIDO]eeabedf9[DADO OMITIDO]ee5[DADO OMITIDO]`. Remoto inicial/pre-push: `[DADO OMITIDO]d2[DADO OMITIDO]b9c7[DADO OMITIDO]dcf9[DADO OMITIDO]f8be`. Divergencia inicial: [DADO OMITIDO] atras, [DADO OMITIDO] a frente.

- `[DADO OMITIDO]bd8[DADO OMITIDO]da8a7[DADO OMITIDO]cda2ae7ef4[DADO OMITIDO]ddc3[DADO OMITIDO] test(panorama): cover weekly filtered inventory aliases`
- `[DADO OMITIDO]d8[DADO OMITIDO]a0c3d4[DADO OMITIDO]de0[DADO OMITIDO]afbbb3[DADO OMITIDO]adde6[DADO OMITIDO]c3 Merge pull request #[DADO OMITIDO] from isaiasj2[DADO OMITIDO]/fix/panorama-weekly-filter-contract`
- `d9[DADO OMITIDO]eca1[DADO OMITIDO]b5[DADO OMITIDO]f5[DADO OMITIDO]c5b4[DADO OMITIDO]fbce8[DADO OMITIDO]fe7 refactor(superset): extract shared bootstrap core`
- `a5f2a5[DADO OMITIDO]b8[DADO OMITIDO]b5[DADO OMITIDO]d2[DADO OMITIDO]a1[DADO OMITIDO]c0 fix(superset): package bootstrap modules in image`
- `[DADO OMITIDO]a6[DADO OMITIDO]da7[DADO OMITIDO]bd1[DADO OMITIDO]f9[DADO OMITIDO]ce5[DADO OMITIDO]a1a9[DADO OMITIDO]b4e0 Merge pull request #[DADO OMITIDO] from isaiasj2[DADO OMITIDO]/refactor/superset-bootstrap-core`
- `a3[DADO OMITIDO]cae6ac9[DADO OMITIDO]c0[DADO OMITIDO]a8df7[DADO OMITIDO]c2c4[DADO OMITIDO]a8[DADO OMITIDO]d3[DADO OMITIDO] refactor(superset): modularize panorama bootstrap`
- `[DADO OMITIDO]ab0[DADO OMITIDO]f9e2b4edf4c6[DADO OMITIDO]cf7b4[DADO OMITIDO]ee5 test(superset): cover panorama module architecture`
- `[DADO OMITIDO]f2[DADO OMITIDO]c4[DADO OMITIDO]c5[DADO OMITIDO]fd4bfb2fc4be2ee7[DADO OMITIDO]a9[DADO OMITIDO]b Merge pull request #[DADO OMITIDO] from isaiasj2[DADO OMITIDO]/refactor/superset-panorama-modules`
- `c0[DADO OMITIDO]ce8[DADO OMITIDO]f1[DADO OMITIDO]ecdcec9[DADO OMITIDO]d2[DADO OMITIDO]ee0be1[DADO OMITIDO] refactor(superset): modularize overview bootstrap`
- `a1[DADO OMITIDO]f4[DADO OMITIDO]ad8b4d0[DADO OMITIDO]bd2[DADO OMITIDO]a8fb4[DADO OMITIDO]bb6[DADO OMITIDO]b8 test(superset): cover overview module architecture`
- `[DADO OMITIDO]d7c0[DADO OMITIDO]e3[DADO OMITIDO]c0[DADO OMITIDO]fb8e3de4[DADO OMITIDO]cf3[DADO OMITIDO]e Merge pull request #[DADO OMITIDO] from isaiasj2[DADO OMITIDO]/refactor/superset-overview-modules`
- `[DADO OMITIDO]fea7ae6[DADO OMITIDO]d0[DADO OMITIDO]c2[DADO OMITIDO]f5[DADO OMITIDO]bf2a0c3bd0e2[DADO OMITIDO] refactor(superset): modularize certified osa bootstrap`
- `d3[DADO OMITIDO]af4[DADO OMITIDO]b9b3[DADO OMITIDO]b0[DADO OMITIDO]ddc3[DADO OMITIDO]b3ac2f test(superset): cover certified osa module architecture`
- `[DADO OMITIDO]d2[DADO OMITIDO]b9c7[DADO OMITIDO]dcf9[DADO OMITIDO]f8be Merge pull request #[DADO OMITIDO] from isaiasj2[DADO OMITIDO]/refactor/superset-osa-certified-modules`

## [DADO OMITIDO]. Inventario e classificacao das alteracoes locais

Inventario integral, hashes, worktrees e status inicial preservados em `lactalis_reconcile_initial.json`; patch original em `lactalis_reconcile_initial.patch`. Os cinco grupos revisaram [DADO OMITIDO] caminhos; na reconciliacao final, [DADO OMITIDO] arquivos diferem do remoto inicial devido a portabilidade modular.

A: pipeline/registries e isolamento [DADO OMITIDO]. B: startup opcional/Ollama e teste de sessao. C: serving OSA, testes e validadores de tenant/RLS/Panorama/Stock. D: README e relatorios. E: caches, capturas e diagnosticos locais excluidos. F: nao houve codigo de origem incerta incorporado; alteracoes da worktree raiz permaneceram intocadas.

Status inicial dos caminhos rastreados:

```
M	README.md
M	bootstrap-ollama.ps1
M	config/customers.yaml
M	config/tenants.yaml
M	embedded-app/smoke.mjs
M	local-engine/neoretail_local/candidates.py
M	local-engine/neoretail_local/partitioned_daily.py
M	local-engine/neoretail_local/pipeline.py
M	local-engine/tests/test_local_contracts.py
M	local-engine/tests/test_osa_industry_certified_contracts.py
M	local-engine/tests/test_panorama_inventory_tabs_contracts.py
M	local-engine/tests/test_power_query_runtime.py
M	run-local-pipeline.ps1
M	run-osa-certified.ps1
M	scripts/validate_project.py
M	start.ps1
M	superset/bootstrap_osa_industry.py
M	superset/bootstrap_osa_industry_certified.py
M	superset/bootstrap_overview_quantity.py
M	superset/osa_certified_matrices.py
M	superset/validate_export.py
M	superset/validate_interactive_paths.py
M	superset/validate_osa_industry.py
M	superset/validate_osa_industry_certified.py
M	superset/validate_overview.py
M	superset/validate_overview_quantity.py
M	superset/validate_panorama.py
M	superset/validate_panorama_comparisons.py
M	superset/validate_panorama_details.py
M	superset/validate_panorama_inventory_filters.py
M	superset/validate_panorama_inventory_tabs.py
M	superset/validate_panorama_kpi_dimensions.py
M	superset/validate_panorama_sales.py
M	superset/validate_panorama_stock.py
M	superset/validate_stock_headlines.py
M	superset/validate_stock_optimization.py
```

Status inicial da worktree raiz (preservada):

```
 M embedded-app/server.js
 M local-engine/tests/test_panorama_comparison_contracts.py
 M local-engine/tests/test_panorama_inventory_tabs_contracts.py
 M local-engine/tests/test_panorama_sales_contracts.py
 M superset/bootstrap_export.py
 M superset/bootstrap_osa_industry.py
 M superset/bootstrap_osa_industry_certified.py
 M superset/bootstrap_overview.py
 M superset/bootstrap_overview_quantity.py
 M superset/bootstrap_panorama.py
 M superset/bootstrap_stock_optimization.py
 M superset/osa_certified_matrices.py
?? docs/superset_bootstrap_phase1.md
?? local-engine/tests/test_bootstrap_architecture.py
?? superset/neoretail_bootstrap/
```

## [DADO OMITIDO]. Branch de seguranca, commits, SHAs e arquivos

Branch local preservada: `wip/lactalis-rebuild-safe-[DADO OMITIDO]`, HEAD `daec7[DADO OMITIDO]cf9caf1c3[DADO OMITIDO]acb8[DADO OMITIDO]d7[DADO OMITIDO]a4[DADO OMITIDO]f1[DADO OMITIDO]e`.

### feat(lactalis): isolate local pipeline for customer [DADO OMITIDO]

A: pipeline LACTALIS

WIP: `[DADO OMITIDO]b7[DADO OMITIDO]f1edc1[DADO OMITIDO]d6[DADO OMITIDO]fd0[DADO OMITIDO]cc9b4[DADO OMITIDO]d3ba8b5[DADO OMITIDO]c` ? aplicado: `cf7[DADO OMITIDO]f8[DADO OMITIDO]c4[DADO OMITIDO]d4[DADO OMITIDO]d6ee3[DADO OMITIDO]a8d3[DADO OMITIDO]c4de9d9[DADO OMITIDO]d0[DADO OMITIDO]`.

Arquivos do commit WIP:

- `.env.example`
- `config/customers.yaml`
- `config/tenants.yaml`
- `local-engine/neoretail_local/candidates.py`
- `local-engine/neoretail_local/partitioned_daily.py`
- `local-engine/neoretail_local/pipeline.py`
- `local-engine/neoretail_local/scoped_dimensions.py`
- `local-engine/tests/test_local_contracts.py`
- `local-engine/tests/test_power_query_runtime.py`
- `local-engine/tests/test_scoped_dimensions.py`
- `run-local-pipeline.ps1`

### perf(osa): preserve certified metrics with compact serving

C: OSA/serving e contratos

WIP: `a1[DADO OMITIDO]f8[DADO OMITIDO]d1b4[DADO OMITIDO]b8ae1[DADO OMITIDO]d5[DADO OMITIDO]cf4[DADO OMITIDO]c8c4[DADO OMITIDO]a` ? aplicado: `[DADO OMITIDO]db1[DADO OMITIDO]eb6[DADO OMITIDO]b5d7[DADO OMITIDO]f0[DADO OMITIDO]a9[DADO OMITIDO]ee6ef4ba6`.

Arquivos do commit WIP:

- `analytics-db/marts/[DADO OMITIDO]_osa_certified_semantic.sql`
- `analytics-db/marts/[DADO OMITIDO]_osa_monthly_retail.sql`
- `local-engine/tests/test_osa_industry_certified_contracts.py`
- `local-engine/tests/test_panorama_inventory_tabs_contracts.py`
- `run-osa-certified.ps1`
- `scripts/validate_project.py`
- `superset/bootstrap_osa_industry.py`
- `superset/bootstrap_osa_industry_certified.py`
- `superset/bootstrap_overview_quantity.py`
- `superset/osa_certified_matrices.py`
- `superset/test_osa_retail_routing.py`

Arquivos finais apos reconciliacao (fachadas/contratos ja cobertos pelo remoto podem nao produzir diff):

- `analytics-db/marts/[DADO OMITIDO]_osa_certified_semantic.sql`
- `analytics-db/marts/[DADO OMITIDO]_osa_monthly_retail.sql`
- `local-engine/tests/test_osa_certified_module_architecture.py`
- `local-engine/tests/test_osa_industry_certified_contracts.py`
- `run-osa-certified.ps1`
- `scripts/validate_project.py`
- `superset/bootstrap_osa_industry.py`
- `superset/bootstrap_osa_industry_certified.py`
- `superset/bootstrap_overview_quantity.py`
- `superset/neoretail_bootstrap/osa_certified/filters.py`
- `superset/neoretail_bootstrap/osa_certified/matrices.py`
- `superset/neoretail_bootstrap/osa_certified/presentation.py`
- `superset/neoretail_bootstrap/osa_certified/semantics.py`
- `superset/test_osa_retail_routing.py`

### feat(assistant): add optional local Ollama startup

B: Assistant/startup

WIP: `[DADO OMITIDO]b8[DADO OMITIDO]d2[DADO OMITIDO]ef1[DADO OMITIDO]bf3[DADO OMITIDO]d2[DADO OMITIDO]b1[DADO OMITIDO]bb9[DADO OMITIDO]a7[DADO OMITIDO]d` ? aplicado: `[DADO OMITIDO]afd1c1b9[DADO OMITIDO]dfca3[DADO OMITIDO]bfe7[DADO OMITIDO]b7b7e8[DADO OMITIDO]`.

Arquivos do commit WIP:

- `.gitattributes`
- `bootstrap-ollama.ps1`
- `embedded-app/assistant/tests/lactalis-session.test.js`
- `scripts/test_assistant_startup.py`
- `start.ps1`

### test(certification): validate Lactalis tenants and reproducible gates

C: validators/RLS e evidencias

WIP: `[DADO OMITIDO]db6afe5[DADO OMITIDO]c0[DADO OMITIDO]c0[DADO OMITIDO]dbaf6[DADO OMITIDO]f5f7f2f` ? aplicado: `[DADO OMITIDO]c3bfba7[DADO OMITIDO]a0f5[DADO OMITIDO]ca1f2c8fb8[DADO OMITIDO]fe7[DADO OMITIDO]`.

Arquivos do commit WIP:

- `embedded-app/smoke.mjs`
- `scripts/audit_lactalis_lake.py`
- `scripts/audit_lactalis_sql.py`
- `scripts/lactalis_assistant_runtime.mjs`
- `scripts/lactalis_disk_snapshot.py`
- `scripts/lactalis_ollama_preflight.py`
- `scripts/lactalis_runtime_final.py`
- `scripts/lactalis_source_preflight.py`
- `scripts/publish_lactalis_marts.py`
- `scripts/report_lactalis_rebuild.py`
- `scripts/run_lactalis_bi.py`
- `scripts/run_lactalis_http.py`
- `scripts/run_lactalis_phase.py`
- `scripts/run_lactalis_stage.py`
- `scripts/run_lactalis_superset.py`
- `superset/validate_export.py`
- `superset/validate_interactive_paths.py`
- `superset/validate_lactalis_guest.py`
- `superset/validate_osa_industry.py`
- `superset/validate_osa_industry_certified.py`
- `superset/validate_overview.py`
- `superset/validate_overview_quantity.py`
- `superset/validate_panorama.py`
- `superset/validate_panorama_comparisons.py`
- `superset/validate_panorama_details.py`
- `superset/validate_panorama_inventory_filters.py`
- `superset/validate_panorama_inventory_tabs.py`
- `superset/validate_panorama_kpi_dimensions.py`
- `superset/validate_panorama_sales.py`
- `superset/validate_panorama_stock.py`
- `superset/validate_stock_headlines.py`
- `superset/validate_stock_optimization.py`

### docs: record Lactalis rebuild and startup validation

D: documentacao

WIP: `daec7[DADO OMITIDO]cf9caf1c3[DADO OMITIDO]acb8[DADO OMITIDO]d7[DADO OMITIDO]a4[DADO OMITIDO]f1[DADO OMITIDO]e` ? aplicado: `[DADO OMITIDO]d2f5[DADO OMITIDO]b5[DADO OMITIDO]ead1bae9af6d2ef7b7[DADO OMITIDO]f9a4[DADO OMITIDO]ae`.

Arquivos do commit WIP:

- `README.md`
- `docs/assistant_local_startup.md`
- `docs/assistant_local_startup_validation.md`
- `docs/lactalis_rebuild_report.md`

## [DADO OMITIDO]. Arquivos fora do Git e stash

Preservados localmente; nenhum publicado:

```
?? .chrome-headless/
?? .chrome-selenium/
?? .tmp_osa_visual.py
?? osa-dashboard.png
?? osa-page-text.txt
?? osa-quantidade.png
?? osa-valor-mensal.png
?? osa-valor-semanal.png
?? superset/diagnose_lactalis_inventory.py
?? superset/profile_lactalis_osa_filtered.py
```

Caches Chrome contem dados de navegador; capturas/textos de dashboard e scripts temporarios nao entram no commit. diagnose_lactalis_inventory.py inclui amostra de produto real e foi excluido; profile_lactalis_osa_filtered.py e diagnostico pontual. .env, generated/, node_modules, bundle, lake, dumps, Parquets e modelos continuam fora do push.

Nenhum stash novo: os leftovers nao colidiram com caminhos remotos nem impediram checkout. Stash anterior preservado:

```
stash@{[DADO OMITIDO]} On main: wip-panorama-stock-filters
```

## [DADO OMITIDO]. Conflitos e resolucao semantica

- `local-engine/tests/test_panorama_inventory_tabs_contracts.py`: Mantido o import e o leitor modular read_panorama do remoto. Os contratos adicionais de aliases semanais ja estavam incluidos no remoto; nenhum teste remoto foi removido.
- `superset/bootstrap_osa_industry_certified.py`: Mantida a fachada e chart_specs/position_json/native_filters modulares. Roteamento compacto e helper de filtros portados para semantics.py/filters.py; row_limit=[DADO OMITIDO] para presentation.py. SqlMetric e conversion_options ficaram no bootstrap; native_filters aceita conversion_options mantendo compatibilidade do chamado anterior.
- `superset/osa_certified_matrices.py`: Mantida a fachada de reexports do remoto; wrapper de rota compacta/detail portado para neoretail_bootstrap/osa_certified/matrices.py.

- Baseline remoto de arquitetura mantido sem regenerar o fixture. Os testes comparam AST das formulas detalhadas e SQL renderizado contra o baseline original; verificam explicitamente row_limit=[DADO OMITIDO], roteamento compacto e dataset de conversoes.
- Validator estatico atualizado de AMBEV/[DADO OMITIDO] para LACTALIS/[DADO OMITIDO] e com import dos auxiliares de teste presentes nos commits remotos.
- entrypoint.sh e init.sh tinham apenas diferenca de final de linha: indice normalizado, conteudo semantico preservado e *.sh text eol=lf versionado.

Aplicacao foi individual, na ordem dos cinco grupos. Nunca usado --ours/--theirs automatico, merge, rebase ou reset para descartar trabalho.

## [DADO OMITIDO]. Testes e resultados

| Verificacao | Resultado |
|---|---|
| pytest contratos/arquitetura Panorama, Stock, OSA, pipeline e RLS estaticos | [DADO OMITIDO] passed |
| validator estatico de projeto | exit [DADO OMITIDO]; clientes, particoes, Gold e RLS aprovados |
| startup Windows com Docker simulado | [DADO OMITIDO]/[DADO OMITIDO] OK |
| Assistant com fonte reconciliada, container descartavel sem rede | [DADO OMITIDO]/[DADO OMITIDO] passed |
| roteamento OSA via fachada real Superset | [DADO OMITIDO]/[DADO OMITIDO] passed |
| Embedded real, sessao [DADO OMITIDO] | exit [DADO OMITIDO] |
| Guest Tokens reais, RLS, assinatura adulterada, overrides e dashboards | exit [DADO OMITIDO] |
| OSA certificado real / ChartData / fontes / performance | exit [DADO OMITIDO] |
| health HTTP Embedded, Superset, Jupyter, Assistant | todos HTTP [DADO OMITIDO]; Assistant Ollama ok, enabled e available |

O teste PySpark Power Query runtime foi excluido nesta reconciliacao para manter o gate rapido. Nao foram ingeridas novamente as [DADO OMITIDO] milhoes de linhas; evidencias completas do rebuild anterior permanecem em docs/lactalis_rebuild_report.md. Panorama e Stock foram cobertos pela suite estatica e pelos probes Guest/ChartData em todos os dashboards; nao se repetiu a bateria longa de todos os validators.

Ocorrencias iniciais e correcoes (sem ocultar falhas):

- Primeira suite apos portabilidade apontou [DADO OMITIDO] testes de baseline que exigiam SQL completo/AST sem wrappers e literal antigo; reconciliados para comparar formulas detalhadas inalteradas e comportamentos novos explicitamente. Uma segunda rodada apontou helper filter_checks adicional na AST de matrix; excluido apenas esse helper da comparacao da formula detalhada. Rodada final: [DADO OMITIDO]/[DADO OMITIDO].
- Validator estatico tentou gravar pycache no bind read-only; reexecutado com pycache_prefix em /tmp. Em seguida identificou import ausente dos auxiliares remotos; import corrigido e validator aprovado.
- Startup sem elevacao encontrou restricao de permissao para criar diretorios temporarios no sandbox Windows; reexecutado no contexto autorizado e [DADO OMITIDO]/[DADO OMITIDO] aprovado.
- Comparacao inicial de mounts considerava ordem da lista do Docker; comparar por Destination confirmou mesmos mounts e IDs. Nenhum container foi recriado.

## [DADO OMITIDO]. HEAD, push, remoto final e PR

HEAD apos os cinco cherry-picks: `[DADO OMITIDO]d2f5[DADO OMITIDO]b5[DADO OMITIDO]ead1bae9af6d2ef7b7[DADO OMITIDO]f9a4[DADO OMITIDO]ae`. Fetch obrigatorio pre-push confirmou `[DADO OMITIDO]d2[DADO OMITIDO]b9c7[DADO OMITIDO]dcf9[DADO OMITIDO]f8be` e divergencia `[DADO OMITIDO] [DADO OMITIDO]`. Push normal, exit [DADO OMITIDO]: `[DADO OMITIDO]..[DADO OMITIDO]d2f5`. ls-remote e novo fetch confirmaram `[DADO OMITIDO]d2f5[DADO OMITIDO]b5[DADO OMITIDO]ead1bae9af6d2ef7b7[DADO OMITIDO]f9a4[DADO OMITIDO]ae`, divergencia final `[DADO OMITIDO] [DADO OMITIDO]`.

[PR #[DADO OMITIDO]](https://github.com/isaiasj2[DADO OMITIDO]/neoretail-superset-multitenant-poc/pull/[DADO OMITIDO]): OPEN, DRAFT, merged=false, head=[DADO OMITIDO]d2f5[DADO OMITIDO]b5[DADO OMITIDO]ead1bae9af6d2ef7b7[DADO OMITIDO]f9a4[DADO OMITIDO]ae. Nao houve alteracao de estado da PR nem da main.

## [DADO OMITIDO]. Status final e preservacao dos dados/volumes

Somente os arquivos E nao rastreados da secao [DADO OMITIDO] permanecem no status. Indice sem staged changes; nenhum diff rastreado nem operacao Git incompleta. WIP e stash anterior preservados.

Nenhuma ingestao, refresh, republicacao SQL, bootstrap de metadata, remocao/recriacao de containers/volumes, merge ou alteracao de main durante a reconciliacao. Dados LACTALIS e volumes persistentes preservados. Smokes fizeram leituras de dados; logs/caches e sessoes de teste podem registrar atividade normal.

Sete servicos healthy e superset-init exited [DADO OMITIDO]. Todos os oito IDs de containers e mounts sao os mesmos do snapshot inicial (comparacao por Destination). Volumes Analytics, lake, metadata, Redis e Ollama nao foram apagados ou recriados. HTTP Embedded/Superset/Jupyter/Assistant=[DADO OMITIDO]; Assistant provider ollama, modelo llama3.[DADO OMITIDO]:[DADO OMITIDO]b, status ok.

Evidencia: `lactalis_reconcile_runtime_before.json` / `lactalis_reconcile_runtime_after.json`. Auditoria de segredos nos arquivos destinados ao push aprovada; credenciais reais de .env nao aparecem nos fontes candidatos.

O JSON acompanhante inclui o inventario integral e os arquivos de cada commit. Este relatorio e local (generated/), sem novo commit ou push adicional.
