# Relatorio de validacao da V8.1 Local

## Validacoes disponiveis no pacote

- Python do profiler e engine local compila.
- YAML do Compose e contratos carrega.
- Backend e frontend passam no parser Node.
- Shell do bootstrap passa em validacao sintatica.
- Compose contem `analytics-db` e `local-engine`.
- Compose nao contem Databricks, PBIX ou converter.
- PostgreSQL Metadata e Analytics estao separados.
- Nove notebooks locais 00-08 estao presentes.
- Superset usa somente o driver PostgreSQL local.
- Nenhum segredo real integra o pacote.
- Imagem do engine local fixada em Debian Bookworm, onde OpenJDK 17 esta
  disponivel para o PySpark 3.5.
- Nove familias de nomes da 3CORACOES possuem testes de classificacao.
- ETL_CALC V1 e V2 geram tabelas Bronze distintas.
- O ingestor de candidatos nao contem SAS nem promove dados para Gold.

## Correcao apos o primeiro build no Windows

O primeiro build identificou que `python:3.11-slim` passou a resolver para
Debian Trixie e deixou de oferecer `openjdk-17-jre-headless`. O Dockerfile foi
fixado em `python:3.11-slim-bookworm` para tornar o build reproduzivel sem
alterar a versao Java prevista pela arquitetura.

O primeiro bootstrap completo tambem identificou a mudanca de contrato do
`Database.get_sqla_engine()` no Superset 6. O script agora entra no context
manager para obter a Engine e somente depois abre a transacao SQLAlchemy.
O metadata permanece em `flush` durante a verificacao, evitando que a instancia
`Database` seja desanexada antes da leitura da URI criptografada.

## Evidencias dependentes do computador do usuario

- Build Docker do PySpark e Superset.
- Leitura real do Azure Blob.
- Carga das dimensoes Bronze/Silver/Gold.
- Escrita JDBC no PostgreSQL Analytics.
- Descoberta e aprovacao de fatos.
- Valores de KPI e dashboards.

Esses itens nao devem ser declarados concluidos sem executar
`start.ps1 -Rebuild`, `test-local.ps1` e `run-local-pipeline.ps1`.
