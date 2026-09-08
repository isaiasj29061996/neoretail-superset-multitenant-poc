# Troubleshooting V8.1 Local

## 03B informa `dias_sem_venda` ausente

Alguns Parquets diarios usam `DIAS_SEM_VENDAS`, no plural, enquanto a consulta
M referencia `DIAS_SEM_VENDA`. A versao atual aceita ambas e publica somente
`dias_sem_venda` na Silver. Atualize o pacote, recrie o `local-engine` e execute
03B novamente.

## PowerShell bloqueou o script

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\start.ps1 -Rebuild
```

## Token do Jupyter

Use o valor de `JUPYTER_TOKEN` no `.env`. O padrao e
`neoretail-v81-local`. Depois de alterar:

```powershell
docker compose up -d --force-recreate local-engine
```

## Connection string do Blob ausente

O start continua funcionando, mas `run-local-pipeline.ps1` bloqueia. Preencha
`AZURE_STORAGE_CONNECTION_STRING` no `.env`.

## Erro TLS corporativo

Execute `export-company-ca.ps1`. Nao desative validacao SSL.

## PySpark ficou sem memoria

Comece com `SPARK_DRIVER_MEMORY=4g` e configure pelo menos 8 GB para o Docker
Desktop. Para conjuntos maiores, aumente gradualmente.

## Build informa que `openjdk-17-jre-headless` nao esta disponivel

Esse erro ocorreu quando a tag flutuante `python:3.11-slim` passou a apontar
para Debian Trixie, que substituiu o pacote Java 17 pelo Java 21. O pacote
V8.1 corrigido fixa `python:3.11-slim-bookworm`, mantendo o Java 17 esperado
pelo PySpark 3.5.

Se estiver corrigindo uma copia anterior manualmente, edite
`local-engine/Dockerfile` e troque a primeira linha por:

```dockerfile
FROM python:3.11-slim-bookworm
```

Depois execute novamente:

```powershell
.\start.ps1 -Rebuild
```

## Porta 5433 ocupada

Altere `ANALYTICS_DB_PORT` no `.env`, por exemplo:

```dotenv
ANALYTICS_DB_PORT=55433
```

Essa porta e apenas para acesso pelo Windows; os containers continuam usando
`analytics-db:5432`.

## Etapas 04 e 06 aparecem blocked

Correto enquanto `config/approved_facts.yaml` estiver vazio. Nao e falha.

## Superset nao mostra tabelas Gold

Execute o pipeline ate a etapa 08, abra a conexao
`NeoRetail Gold - PostgreSQL Local` e sincronize o schema `gold`.

## `'_GeneratorContextManager' object has no attribute 'begin'`

Esse erro era causado pelo bootstrap tratar diretamente o context manager do
Superset 6 como uma Engine SQLAlchemy. O pacote corrigido abre primeiro a
Engine e depois a transacao. Depois de atualizar `bootstrap_analytics.py`, rode:

```powershell
.\start.ps1 -Rebuild
```

## `DetachedInstanceError` durante `get_sqla_engine()`

Esse erro ocorre quando o metadata e confirmado antes de o Superset abrir a
conexao Analytics. O bootstrap corrigido usa `set_sqlalchemy_uri`, executa
`flush`, valida a Engine e somente depois executa `commit`. Como a pasta
`superset` e montada no container, depois de corrigir o arquivo basta rodar:

```powershell
.\start.ps1
```

## Um Parquet candidato possui zero linhas

O ingestor registra o arquivo como `empty_source` em
`audit.fact_candidate_inventory`, nao cria uma tabela Bronze vazia e continua
com os demais arquivos da familia. O resumo informa `empty` e `empty_files`.
Isso e evidencia da fonte e nao falha tecnica do pipeline.

## `superset-init` aparece Exited (0)

Correto. E um job; o healthcheck foi desativado para evitar o falso
`unhealthy` herdado da imagem base.
