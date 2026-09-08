# NeoRetail V9 — Multi-tenant Superset Embedded

A V9 preserva a V8.1 e adiciona isolamento por `id_customer`, Gold compartilhada,
um único dashboard Superset e Guest Token com RLS emitido pelo backend.

## Clientes iniciais

| ID_CUSTOMER | Cliente | Prefixo no Blob |
|---:|---|---|
| 259 | 3 Corações | `PARTICULAR_3/3CORACOES` |
| 609 | Baston | `PARTICULAR_3/BASTON` |
| 16868 | Safira | `PARTICULAR_3/SAFIRA` |

O cadastro oficial fica em `config/customers.yaml`. O pipeline confirma o nome e
o ID contra `DIMENSAO_CUSTOMER` antes de publicar a Silver.

## Execução local por cliente

```powershell
.\run-local-pipeline.ps1 -Step 02A -Customer 259
.\run-local-pipeline.ps1 -Step 02B -Customer 259
.\run-local-pipeline.ps1 -Step 03A -Customer 259
.\run-local-pipeline.ps1 -Step 03B -Customer 259
.\run-local-pipeline.ps1 -Step 03C -Customer 259
.\run-local-pipeline.ps1 -Step 03D -Customer 259
.\run-local-pipeline.ps1 -Step 04 -Customer 259
.\run-local-pipeline.ps1 -Step 05 -Customer 259
.\run-local-pipeline.ps1 -Step 06 -Customer 259
.\run-local-pipeline.ps1 -Step 07 -Customer 259
.\run-local-pipeline.ps1 -Step 08 -Customer 259
```

Para atualizar os três clientes:

```powershell
.\run-multitenant-refresh.ps1
```

Os dados do lake são gravados em partições como
`gold/fato_ivd_tvd/id_customer=259`. No PostgreSQL, cada carga substitui somente
as linhas do cliente processado.

## Superset e Embedded

- Dataset compartilhado: `gold.vw_mart_visao_industria`.
- Segurança: Guest Token com cláusula `id_customer = <ID autorizado>`.
- Dashboard: um único UUID para todos os clientes.
- Filtros: controles nativos do Superset sobre rede, bandeira, UF, cidade, loja,
  marca, item, nível de atividade e período.
- Jinja: não é usado para segurança e não é necessário nos charts comuns.
- Visual próprio: `NeoRetail KPI Card`, plugin React sem Handlebars/Jinja.

Crie as views depois de publicar a Gold:

```powershell
.\create-superset-kpi-views.ps1
```

## Validação

```powershell
.\validate.ps1
docker compose exec -T local-engine pytest -q /workspace/local-engine/tests
```

Documentos principais:

- `docs/v9_multitenant_architecture.md`
- `docs/v9_runbook.md`
- `docs/gitlab_scheduling.md`
- `docs/custom_kpi_plugin.md`

Nenhum `.env`, SAS, senha ou connection string real deve ser versionado.
