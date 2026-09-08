# Workflow Blob First local

1. Preencher o SAS somente no `.env`.
2. Executar `discover-blob.ps1`.
3. Revisar o inventario geral e o escopo `facts_3coracoes` produzido pela etapa 01.
4. Executar o notebook 02A para as dimensoes aprovadas.
5. Executar o notebook 02B ou `ingest-fact-candidates.ps1` por familia.
6. Materializar candidatos Bronze sem unir V1/V2.
7. Executar 03A para normalizar dimensoes.
8. Executar 03B para consolidar os fatos por familia e varejista.
9. Executar 03C para estruturar `calculo_oportunidades` via `ETL_CALC_V2`.
10. Executar 03D e conferir `audit.silver_quality_gate`.
11. Revisar schemas, grao, tenant, chaves e a paridade com o Power Query.
12. Manter apenas paths comprovados em `source_catalog.yaml`.
13. Registrar fatos aprovados em `approved_facts.yaml`.
14. Executar as etapas Gold do pipeline local.
15. Conferir `audit.gold_quality_gate`.
16. Criar datasets Superset somente sobre `gold.*`.
17. Validar Guest Token e RLS com dois tenants.

O cache local e uma materializacao tecnica controlada por ETag. O Azure Blob
continua sendo a fonte de verdade.
