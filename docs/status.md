# Status da V8.1 Local

## Implementado

- Compose local com dois PostgreSQL, Redis, Superset, PySpark/Jupyter e Embedded.
- Azure Blob como fonte unica.
- Pipeline 00-08 executavel por PowerShell ou Jupyter, com Bronze 02A/02B e
  Silver 03A/03B/03C/03D.
- Seis fontes dimensionais/auxiliares com paths aprovados.
- Descoberta das nove familias de fatos da 3CORACOES por prefixo e regex.
- Ingestao reiniciavel de cada Parquet candidato em tabela Bronze isolada.
- Catalogo de candidatos em `audit.fact_candidate_inventory`.
- Consolidacao Silver por familia e varejista, com schema drift e linhagem.
- `silver.calculo_oportunidades` estruturada a partir de `ETL_CALC_V2`.
- Consultas M de dimensoes, fatos e oportunidades mapeadas a partir do TMDL.
- Validacoes em `audit.opportunity_readiness` e `audit.silver_quality_gate`.
- Publicacao Gold no PostgreSQL Analytics.
- Bootstrap automatico da conexao Superset.
- Guest Token e RLS derivados da sessao.
- Health checks de containers e endpoints HTTP.

## Bloqueado por evidencia

- Aprovacao das tabelas fato candidatas para Gold.
- Colunas calculadas e medidas DAX permanecem para a camada semantica/Gold.
- Definicoes de TVD, IVD, OSA, Giro, Oportunidades e Itens sem venda.
- Dashboard final com metricas reais.
- Teste de RLS com dados fato de dois tenants.
- Benchmark AMBEV e teste de carga de 1 a 100 usuarios.

## Estado esperado apos o start

O ambiente sobe saudavel mesmo sem connection string do Blob. O pipeline somente
executa depois de `AZURE_STORAGE_CONNECTION_STRING` ser preenchida.
