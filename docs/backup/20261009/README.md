# Backup pré-formatação — 09/10/2026

Repositório privado: https://github.com/isaiasj29061996/neoretail-superset-multitenant-poc

Código de cada worktree é preservado em branch própria `backup/*-pre-format-20261009`, sem trocar branches de trabalho, reset, clean, alteração de negócio ou force push. Cada branch é um snapshot WIP, não uma nova certificação funcional.

Relatórios PBIP, Performance Wave 1/Wave 2, atualização TVD/IVD e causa raiz estão em `reports/`, com dados numéricos privados omitidos. `reports-manifest.json` lista os originais e hashes. Os relatórios integrais, fixtures reais, PBIP/PBIX e dados continuam exigindo backup externo privado.

Estado certificado histórico: 36 MATCH, 0 DIFFERENCE, 1 UNMAPPED; 37 NO_PBI_VALUE. Performance: Wave 1 ~24s; Wave 2 ~22–24s, sem atingir 15s com baixo risco. Investigação nova comprovou origens diferentes e risco IVD com predicado distinto do DAX. Essas conclusões não reclassificam retroativamente o baseline.

**Não formatar até concluir e validar backup externo.** GitHub não contém bancos, volumes, segredos nem evidências numéricas completas. Dois fixtures reais deliberadamente ausentes: `local-engine/tests/fixtures/pbip_filters_conversion_real_rows_20261008.json` e `local-engine/tests/fixtures/pbip_lactalis_real_contract_rows_20261008.json`. Alguns testes dependem da restauração desses arquivos privados; não há claim de recuperação integral somente pelo GitHub.

Leia `RESTORE.md`, `EXTERNAL-BACKUP.md` e o inventário de branches antes de restaurar.
