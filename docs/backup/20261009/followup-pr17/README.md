# PR #17 — conciliação individual dos 81 itens locais

**Não liberar a formatação: backup privado externo ainda não realizado nem validado.**

Em 09/10/2026, `git status --porcelain=v1 -z --untracked-files=all` identificou exatamente **81 arquivos** na worktree OSA. **79** coincidem byte a byte no conteúdo canônico Git (blob hash) com `origin/backup/osa-industry-pre-format-20261009`, commit `48d7d7b66f302cdf440495118d45171805c4ff98`. **2** são fixtures reais, deliberadamente ausentes do GitHub. **Nenhum código seguro desses 81 está faltando no remoto.**

A lista do VS Code permanece porque a worktree está em `feat/osa-industry-certification`, HEAD `569d2f536b5968ead1bae9af6d2ef7b76f9a45ae`; os snapshots foram feitos em outra branch, usando índices temporários. Não é evidência de perda nem motivo para reset/clean/checkout destrutivo. Não se deve criar commits duplicados desses 79. Este commit acrescenta apenas a prova de conciliação, preservando os commits anteriores e sem alterar fontes/índices/branches de trabalho.

PR #17 consultada: aberta, draft=true, merged=false, head=backup/osa-industry-pre-format-20261009, base=main. Seu novo commit de auditoria deve ser confirmado novamente pela API após o push. Não houve merge nem pedido de merge.

## Todas as worktrees

| Worktree | Itens locais | Já no GitHub | Branch de preservação |
|---|---:|---:|---|
| NeoRetail_V8_1_LOCAL_POSTGRES | 21 | 21 | `backup/root-pre-format-20261009` |
| governed-assistant | 1 | 1 | `backup/governed-assistant-pre-format-20261009` |
| governed-assistant-ambev | 1 | 1 | `backup/governed-assistant-ambev-pre-format-20261009` |
| integration-pr3 | 1 | 1 | `backup/integration-pr3-pre-format-20261009` |
| multitenant-fasttrack | 58 | 58 | `backup/multitenant-fasttrack-pre-format-20261009` |
| multitenant-tenant-context | 18 | 18 | `backup/multitenant-tenant-context-pre-format-20261009` |
| osa-industry | 81 | 79 | `backup/osa-industry-pre-format-20261009` |
| overview-quantity | 0 | 0 | `backup/overview-quantity-pre-format-20261009` |
| panorama-sales-evolution | 0 | 0 | `backup/panorama-sales-evolution-pre-format-20261009` |
| panorama-stock | 0 | 0 | `backup/panorama-stock-pre-format-20261009` |
| superset-bootstrap-core | 0 | 0 | `backup/superset-bootstrap-core-pre-format-20261009` |
| superset-osa-certified-modules | 0 | 0 | `backup/superset-osa-certified-modules-pre-format-20261009` |
| superset-overview-modules | 0 | 0 | `backup/superset-overview-modules-pre-format-20261009` |
| superset-panorama-modules | 0 | 0 | `backup/superset-panorama-modules-pre-format-20261009` |

Total: 181 itens locais examinados nas 14 worktrees; 179 já no GitHub, dois privados. As 17 branches de backup existentes cobrem também três linhas históricas sem worktree. Foram conferidos blobs individuais, não apenas existência de nomes de arquivo. Nos dois init.sh de assistants, a normalização LF/CRLF explica status local sem conteúdo Git diferente.

## Destino individual dos 81 itens OSA

| # | Git status | Arquivo | Destino | Prova / justificativa |
|---:|---|---|---|---|
| 1 | ` M` | `scripts/publish_lactalis_marts.py` | GitHub: blob idêntico | `fd85f261c1ea1ca63e81cdd524bbfd346109c16f` |
| 2 | ` M` | `superset/Dockerfile` | GitHub: blob idêntico | `34a4b8f423ebc0071b06562f01e6b7dedabe2fd6` |
| 3 | ` M` | `superset/bootstrap_analytics.py` | GitHub: blob idêntico | `72076be220c40466da79620c1fc05090a62e00ff` |
| 4 | ` M` | `superset/bootstrap_overview.py` | GitHub: blob idêntico | `a6e91c312f21c15a4939bf6ba1bdafbe61313384` |
| 5 | ` M` | `superset/frontend-plugin/plugin-chart-neoretail-kpi/src/buildQuery.js` | GitHub: blob idêntico | `234db9f5e0611922a21121912ca5e90e8482f392` |
| 6 | ` M` | `superset/frontend-plugin/plugin-chart-neoretail-kpi/src/transformProps.js` | GitHub: blob idêntico | `7bc9a07fa7e1c3fc249086eac6d92b898d2c547d` |
| 7 | ` M` | `superset/validate_overview.py` | GitHub: blob idêntico | `3064fcd781c70ef2a00f2c6429b2e834e55a291b` |
| 8 | `??` | `analytics-db/marts/47_pbip_overview_calendar.sql` | GitHub: blob idêntico | `e75ca6ee7f808a4fb8c7efcef71748624042b686` |
| 9 | `??` | `analytics-db/marts/48_pbip_overview_context.sql` | GitHub: blob idêntico | `a083c7bb97d3e97726206170d5c8003b88be783c` |
| 10 | `??` | `analytics-db/marts/49_pbip_filters_conversion.sql` | GitHub: blob idêntico | `d68d2d2705e82e8baf0944b09bfb403720043c96` |
| 11 | `??` | `analytics-db/marts/50_pbip_conversion_direction.sql` | GitHub: blob idêntico | `13910f79e9528531a8ab3a5b86da122c4ef30e56` |
| 12 | `??` | `analytics-db/marts/51_pbip_performance_indexes.sql` | GitHub: blob idêntico | `c4b13e8e008694ca4913fd9d1ede732f309d02b2` |
| 13 | `??` | `docs/backup/20261009/EXTERNAL-BACKUP.md` | GitHub: blob idêntico | `487b2d37b680cd99ce74493767300075cef17fe2` |
| 14 | `??` | `docs/backup/20261009/README.md` | GitHub: blob idêntico | `18eed568a81a81a7e8d37715e3bdc08fa04039ef` |
| 15 | `??` | `docs/backup/20261009/REMOTE-VERIFICATION.md` | GitHub: blob idêntico | `666450b683f1dd42d58253ced4d15cfe5e8e746f` |
| 16 | `??` | `docs/backup/20261009/RESTORE.md` | GitHub: blob idêntico | `f78a01d03c16758b6185b5edcb26ae91d096cee4` |
| 17 | `??` | `docs/backup/20261009/branches.json` | GitHub: blob idêntico | `c88487927742e76400befff820fd6236f0e8bb12` |
| 18 | `??` | `docs/backup/20261009/remote-verification.json` | GitHub: blob idêntico | `80e74169a32eb621952761b9e8b980df9d3d06d0` |
| 19 | `??` | `docs/backup/20261009/reports-manifest.json` | GitHub: blob idêntico | `cfcba73f9bce03fc4653db48e9cd4156cccdbe02` |
| 20 | `??` | `docs/backup/20261009/reports/NeoRetail_V8_1_LOCAL_POSTGRES__lactalis_only_rebuild_audit_2026-10-07.md` | GitHub: blob idêntico | `7ce01f1f3968af097b58b5532b3834237f06cd4c` |
| 21 | `??` | `docs/backup/20261009/reports/osa-industry__lactalis_push_audit_blocked.md` | GitHub: blob idêntico | `b98764db147bd199e8b8ec400b3d429c5e0ce10c` |
| 22 | `??` | `docs/backup/20261009/reports/osa-industry__lactalis_rebuild_report.md` | GitHub: blob idêntico | `67012b78c00cc44d60932b868aa1845038836b91` |
| 23 | `??` | `docs/backup/20261009/reports/osa-industry__lactalis_reconcile_final.md` | GitHub: blob idêntico | `12300988d41c9f6997e36d22afcc28d7e6e3437e` |
| 24 | `??` | `docs/backup/20261009/reports/osa-industry__pbi_superset_semantic_equivalence_20261008.md` | GitHub: blob idêntico | `f52b0dd431a1732c46fc199eb08cf1c8c4d73afc` |
| 25 | `??` | `docs/backup/20261009/reports/osa-industry__pbi_vs_superset_kpis_20261008.md` | GitHub: blob idêntico | `6382f017ed92156a699f93befc1d0068c458e606` |
| 26 | `??` | `docs/backup/20261009/reports/osa-industry__pbip_c05_sellout_u3m_before_after_20261008.md` | GitHub: blob idêntico | `15aba8c457d63c35ae602c7bc18c821be2b7e1ff` |
| 27 | `??` | `docs/backup/20261009/reports/osa-industry__pbip_c14_cost_blank_before_after_20261008.md` | GitHub: blob idêntico | `cd48a3bd417a8bf1b61ff80268b5e4f5541c0bb5` |
| 28 | `??` | `docs/backup/20261009/reports/osa-industry__pbip_c16_roi_markup_before_after_20261008.md` | GitHub: blob idêntico | `a28a2fea32a6974b88b9f6815969da4c7678fad9` |
| 29 | `??` | `docs/backup/20261009/reports/osa-industry__pbip_f13_final_20261008.md` | GitHub: blob idêntico | `13f8383b5f063060db914679ca12abd2f1d62661` |
| 30 | `??` | `docs/backup/20261009/reports/osa-industry__pbip_f13_selectors_before_after_20261008.md` | GitHub: blob idêntico | `a6d3153db144b74b9f0a770dc8e108ffc0fcd2ea` |
| 31 | `??` | `docs/backup/20261009/reports/osa-industry__pbip_f15_c08_tvd_ivd_before_after_20261008.md` | GitHub: blob idêntico | `137bef5a8740d61e6aa732f350dc42a4a2af47a7` |
| 32 | `??` | `docs/backup/20261009/reports/osa-industry__pbip_filters_conversion_before_after_20261008.md` | GitHub: blob idêntico | `f05521520f3b0bdb53a02fe023de52eeee9f340e` |
| 33 | `??` | `docs/backup/20261009/reports/osa-industry__pbip_lactalis_corrections_before_after_20261008.md` | GitHub: blob idêntico | `40b9efb21efa306a7d1e37d12573ec3885b12082` |
| 34 | `??` | `docs/backup/20261009/reports/osa-industry__pbip_performance_optimization_20261008.md` | GitHub: blob idêntico | `80b2cd65ee6b02df2be8637376aa33b3e1261086` |
| 35 | `??` | `docs/backup/20261009/reports/osa-industry__pbip_performance_wave2_20261008.md` | GitHub: blob idêntico | `da5860b7ba22c276a22d9ca659adb9714cf94d41` |
| 36 | `??` | `docs/backup/20261009/reports/osa-industry__pbip_roi_annual_blank_final_20261008.md` | GitHub: blob idêntico | `5a11f3e02cb4fc583aeb866e7dbde610901c1d09` |
| 37 | `??` | `docs/backup/20261009/reports/osa-industry__refresh_20261008_report.md` | GitHub: blob idêntico | `e43289d678c796f224c8082ad3e4441fe13adbf4` |
| 38 | `??` | `docs/backup/20261009/reports/osa-industry__tvd_giro_rootcause_20261009_084854__report.md` | GitHub: blob idêntico | `35fd80270068423cf469a62b0af79b6e3d0db651` |
| 39 | `??` | `docs/backup/20261009/reports/osa-industry__tvd_ivd_refresh_20261009_070824__report.md` | GitHub: blob idêntico | `dffbc375d6f66ad60fdcd0712010d410abdfb022` |
| 40 | `??` | `docs/backup/20261009/worktrees-audit.json` | GitHub: blob idêntico | `8e705481138bf00273d3414dd594603279e5f4ac` |
| 41 | `??` | `local-engine/tests/fixtures/pbip_c16_dax_20261008.json` | GitHub: blob idêntico | `c913de3746ffc751b60b8835aff57d77209e93b7` |
| 42 | `??` | `local-engine/tests/fixtures/pbip_f13_final_evidence_20261008.json` | GitHub: blob idêntico | `029eb7e4c9cf68764a496b69e6c9881879f284d0` |
| 43 | `??` | `local-engine/tests/fixtures/pbip_f13_selectors_pbip_20261008.json` | GitHub: blob idêntico | `1a87b7133401efb3100b3bfe36c0aeb7b996c002` |
| 44 | `??` | `local-engine/tests/fixtures/pbip_f15_c08_dax_20261008.json` | GitHub: blob idêntico | `ad6c4f80fe4807ac8c3fd25738e9a835e51f678c` |
| 45 | `??` | `local-engine/tests/fixtures/pbip_filters_conversion_real_rows_20261008.json` | EXTERNO PRIVADO: não publicar | Fixture extraÃ­do de registros reais de localizaÃ§Ã£o/conversÃ£o, incluindo CNPJ; nÃ£o publicar. Backup externo privado obrigatÃ³rio. |
| 46 | `??` | `local-engine/tests/fixtures/pbip_lactalis_overview_20261008.json` | GitHub: blob idêntico | `5fca7598befae3e06743bf195d271fcf63a91122` |
| 47 | `??` | `local-engine/tests/fixtures/pbip_lactalis_real_contract_rows_20261008.json` | EXTERNO PRIVADO: não publicar | Fixture extraÃ­do de agregaÃ§Ãµes e resultados reais da Lactalis; nÃ£o publicar. Backup externo privado obrigatÃ³rio. |
| 48 | `??` | `local-engine/tests/test_analytics_performance.py` | GitHub: blob idêntico | `8990830734aa81344f1e923064078641a5109835` |
| 49 | `??` | `local-engine/tests/test_pbip_c05_sellout_u3m.py` | GitHub: blob idêntico | `469d172054e2d0b983c71456df5257df101c8c9a` |
| 50 | `??` | `local-engine/tests/test_pbip_c14_cost_blank.py` | GitHub: blob idêntico | `37bc6d9cf350905997e41656333916a6cf5dd2f2` |
| 51 | `??` | `local-engine/tests/test_pbip_c16_operator_contract.py` | GitHub: blob idêntico | `c52d01c9a2c4fde47d2d6584e82d6dd63567d24c` |
| 52 | `??` | `local-engine/tests/test_pbip_f13_final_evidence.py` | GitHub: blob idêntico | `bda9e16164838a65abbea6ce3f61ff5f190a44cc` |
| 53 | `??` | `local-engine/tests/test_pbip_f13_selectors.py` | GitHub: blob idêntico | `f843fc84d1ec2a85a5e97bfcec8c3584155a98cc` |
| 54 | `??` | `local-engine/tests/test_pbip_f15_c08_daily_context.py` | GitHub: blob idêntico | `c74765dc517bd956a11b3c70ab5c5604e0174d1e` |
| 55 | `??` | `local-engine/tests/test_pbip_filter_conversion_contract.py` | GitHub: blob idêntico | `fb5b1cc502320d3cb0d33745bba9ed07a1ce35c3` |
| 56 | `??` | `local-engine/tests/test_pbip_lactalis_overview.py` | GitHub: blob idêntico | `42ca71cc9e3d093cee801542e9edc419c861e22e` |
| 57 | `??` | `local-engine/tests/test_pbip_roi_annual_blank.py` | GitHub: blob idêntico | `3f0b2878fb09ac1d747fde7d00070c76206f90ce` |
| 58 | `??` | `superset/diagnose_lactalis_inventory.py` | GitHub: blob idêntico | `ae3d22bde1e171c707588605b8c8968e124cca4d` |
| 59 | `??` | `superset/frontend-extension/pbipSelectorDependencies.mjs` | GitHub: blob idêntico | `71656fad0f93045f45d46f224a8963888c3b7994` |
| 60 | `??` | `superset/frontend-extension/register-pbip-selectors.mjs` | GitHub: blob idêntico | `b3f3f98aca214cd084cd55d020f489f8cbd0cc49` |
| 61 | `??` | `superset/frontend-extension/test-pbip-selectors.mjs` | GitHub: blob idêntico | `37f7d8243c72f6ad4438792bb7494bf3e002e6b3` |
| 62 | `??` | `superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-c05-contract.mjs` | GitHub: blob idêntico | `3b83a77974ed222250ba71c0725521c9753f8c9d` |
| 63 | `??` | `superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-c14-contract.mjs` | GitHub: blob idêntico | `7dff5a4864883f5c52b07d7aa19e1ff015235c81` |
| 64 | `??` | `superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-c16-contract.mjs` | GitHub: blob idêntico | `cb585fc2a9f93ff1402670c6092f28d777418793` |
| 65 | `??` | `superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-contract.mjs` | GitHub: blob idêntico | `7c45134b49e7cdfbde025eb702a663752196b7a9` |
| 66 | `??` | `superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-roi-annual-blank-contract.mjs` | GitHub: blob idêntico | `4c3c0dcda243066058d49d0d50daeffba9e84ed4` |
| 67 | `??` | `superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-tvd-ivd-contract.mjs` | GitHub: blob idêntico | `7c1447668fc98fc56569142ba8e73ec55dc153d8` |
| 68 | `??` | `superset/neoretail_bootstrap/core/analytics_performance.py` | GitHub: blob idêntico | `375018fe5308f2d10e8112b930416563a469854d` |
| 69 | `??` | `superset/neoretail_bootstrap/pbip_overview/__init__.py` | GitHub: blob idêntico | `eeb53ee0d36078fea067a5c1a4588cf9402445e5` |
| 70 | `??` | `superset/neoretail_bootstrap/pbip_overview/context.py` | GitHub: blob idêntico | `ce5f683a67486ff7347398e087287995556c7093` |
| 71 | `??` | `superset/neoretail_bootstrap/pbip_overview/conversion_context.py` | GitHub: blob idêntico | `63dd968deda1ec0773471545669f4c4db71d54af` |
| 72 | `??` | `superset/neoretail_bootstrap/pbip_overview/cost_blank.py` | GitHub: blob idêntico | `2ddec4264a41bc65eb56620f95bfe087af74312f` |
| 73 | `??` | `superset/neoretail_bootstrap/pbip_overview/daily_context.py` | GitHub: blob idêntico | `0928ea9636f0f9eb620db3e8a879cb63d78508d7` |
| 74 | `??` | `superset/neoretail_bootstrap/pbip_overview/filter_context.py` | GitHub: blob idêntico | `e29ddad995ec89fb261b19209fcb55ca8f426e7d` |
| 75 | `??` | `superset/neoretail_bootstrap/pbip_overview/headlines.py` | GitHub: blob idêntico | `39ded39c0b728e896ff18b52a009dd194f3a48aa` |
| 76 | `??` | `superset/neoretail_bootstrap/pbip_overview/metadata.py` | GitHub: blob idêntico | `8a8bf6d0a4974f1bb0afaab830fffe8d32102bcd` |
| 77 | `??` | `superset/neoretail_bootstrap/pbip_overview/presentation.py` | GitHub: blob idêntico | `b8e33cd2b360b1aceef05df9887096e6dec464cd` |
| 78 | `??` | `superset/neoretail_bootstrap/pbip_overview/selectors.py` | GitHub: blob idêntico | `a19f7737926fde6d20a81a1fc0bad3e464b52c1f` |
| 79 | `??` | `superset/neoretail_bootstrap/pbip_overview/sellout_u3m.py` | GitHub: blob idêntico | `cefa042f0f1c60739e19e482b2daf89526da02aa` |
| 80 | `??` | `superset/neoretail_bootstrap/pbip_overview/semantics.py` | GitHub: blob idêntico | `e8b20bba867acf04337d58f6cf470baa4dfa9836` |
| 81 | `??` | `superset/profile_lactalis_osa_filtered.py` | GitHub: blob idêntico | `265b9e7e643de911410478195bbfee6d9ea104f0` |

## Exclusões privadas — não são trabalho descartado

1. `local-engine/tests/fixtures/pbip_filters_conversion_real_rows_20261008.json`: registros reais de localização/conversão e CNPJ. Copiar integralmente para armazenamento privado externo; restaurar no mesmo caminho para os testes que dependem dele.
2. `local-engine/tests/fixtures/pbip_lactalis_real_contract_rows_20261008.json`: agregações/resultados reais da Lactalis. Mesmo procedimento privado. Ambos continuam no disco original. Seus hashes locais estão no manifesto, sem publicar seu conteúdo.

Os testes continuam versionados. A recuperação completa desses testes depende dos fixtures externos; não afirmar recuperação integral apenas pelo clone.

## Ignorados e evidências

Inventário adicional: 2718 arquivos ignorados fora de diretórios reproduzíveis/cache explicitamente excluídos. Categorias: quatro configurações privadas, 41 artefatos de dados/fontes, 2663 evidências originais ou ferramentas históricas e dez artefatos locais para revisão externa. `ignored-summary.json` explica o escopo; inventário completo privado permanece no generated desta rodada. Node_modules, caches de browser/pytest/Python e dependências reproduzíveis não são fonte de código exclusivo.

Os 20 relatórios originais mantêm SHA256 do manifesto anterior. As cópias sanitizadas estão no GitHub; originais, JSON numéricos, Parquet, SQL/evidências completos, ferramentas históricas e PBIP/PBIX/cache ABF devem acompanhar o backup externo de todos os generated. Não sobrescrevemos evidências antigas.

## Bloqueios de formatação

- Não foi informado/verificado destino fora deste computador; só C: foi detectado.
- Docker Engine indisponível. Volumes, PostgreSQL Analytics e metadata Superset NÃO tiveram backup/restauração de teste nesta rodada.
- `.env`, chaves, fixtures reais, evidências integrais, PBIP/PBIX e anexos privados NÃO são recuperáveis pelo GitHub.
- Bundle privado da rodada anterior permanece no mesmo disco: não é proteção contra a formatação e antecede este novo commit de auditoria.

Seguir `../EXTERNAL-BACKUP.md` e `../RESTORE.md`. Só liberar quando os itens privados estiverem em OUTRO dispositivo/cofre, hashes conferidos e recuperação de bancos/artefatos testada. O commit de auditoria não muda esse bloqueio.

## Validação requerida após este commit

Novo clone HTTPS independente, sem objetos compartilhados; fetch das 17 branches; comparação de commits/árvores/blobs e integridade `git fsck --full --strict`; checkout OSA limpo; presença dos 79 arquivos e desta auditoria; dois fixtures ausentes por regra de privacidade; PR #17 draft=true, merged=false e head_sha igual ao commit enviado. Relatório final local registra os resultados efetivos, sem presumir sucesso apenas pelo push.
