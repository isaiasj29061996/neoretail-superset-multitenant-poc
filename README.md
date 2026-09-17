# NeoRetail V9 — Superset multitenant

POC local da plataforma analítica NeoRetail com ingestão a partir do Azure Blob,
pipeline PySpark em camadas, PostgreSQL para serving, Apache Superset 6 com
visuais próprios e portal embedded com isolamento por indústria.

O projeto preserva a estrutura funcional da V8.1 e acrescenta o modelo
multitenant da V9. Toda dimensão e fato publicada na Gold carrega
`id_customer`, que também é a chave usada pelo RLS do Superset.

## O que está incluído

- descoberta e leitura de Parquets no Azure Blob;
- lake local em Raw cache, Bronze, Silver e Gold;
- normalização tolerante a schema drift e rastreabilidade da origem;
- quality gates para Silver, Gold e prontidão de métricas;
- PostgreSQL Analytics separado do banco de metadados do Superset;
- dashboards reproduzíveis de Visão Geral, Panorama, OSA da Indústria e
  Tarefas de Otimização de Estoque;
- plugin React `NeoRetail KPI Card` integrado ao frontend do Superset;
- portal embedded com Guest Token e RLS por `id_customer`;
- publicação de dashboards do Superset diretamente no catálogo do portal;
- oito marts físicos compartilhados e indexados no PostgreSQL;
- 58 gráficos publicados, todos consumindo datasets físicos;
- scripts de inicialização, atualização, saúde, validação e reset.

## Estado da POC

| Capacidade | Estado | Evidência principal |
|---|---|---|
| Pipeline com dados reais do Blob | validado na POC | descoberta, Raw cache, Bronze, Silver, Gold e quality gates |
| Multitenancy | validado para 3 indústrias | `id_customer` em todas as camadas, Guest Token e RLS |
| Dashboards | validado | 4 dashboards e 58 gráficos executados sem erro |
| Serving físico | validado | 8 materialized views e índices no PostgreSQL Analytics |
| Embedded | validado na POC | portal próprio, catálogo autorizado e 12 combinações de Guest Token |
| Publicação administrativa | validado na POC | botão `Publicar no NeoRetail`/`Atualizar no NeoRetail` |
| Performance TVD | validado localmente | consulta reduzida de 5,62 s para 1,72 s na primeira medição |
| Certificação das métricas | pendente | requer reconciliação formal com o Power BI e aceite do negócio |
| Escala para aproximadamente 22 tenants | pendente | requer testes de volume, concorrência, SLA e custo |
| Databricks, Delta e dbt | arquitetura alvo | ainda não implantados nesta POC |

Dashboard renderizado e teste técnico aprovado não significam que uma métrica
foi certificada pelo negócio. Os números de performance são do ambiente Docker
local e servem como evidência comparativa, não como previsão de produção.

## Arquitetura

```mermaid
flowchart LR
    A[Azure Blob<br/>fonte de verdade] --> B[PySpark local]
    B --> C[Raw cache]
    C --> D[Bronze]
    D --> E[Silver]
    E --> F[Gold]
    F --> G[(PostgreSQL Analytics)]
    G --> H[Datasets Superset]
    H --> I[Dashboards]
    J[Portal NeoRetail] --> K[Guest Token + RLS]
    K --> I
    L[(PostgreSQL Metadata)] --> H
    M[(Redis)] --> H
```

O Azure Blob continua sendo a fonte de verdade. O lake e o PostgreSQL locais
são materializações para desenvolvimento e validação. Na arquitetura alvo, o
Databricks substitui o PySpark e o serving local sem mudar o contrato
multitenant baseado em `id_customer`.

### Arquitetura alvo para produto

```mermaid
flowchart LR
    A[Azure Blob / ADLS] --> B[Databricks Jobs / Auto Loader]
    B --> C[Delta Bronze]
    C --> D[Delta Silver]
    D --> E[dbt]
    E --> F[Gold e marts Delta incrementais]
    F --> G[Databricks SQL Warehouse]
    G --> H[Apache Superset]
    H --> I[Backend NeoRetail]
    I --> J[Guest Token + RLS]
    J --> K[Portal embedded]
```

Esse desenho é uma proposta de industrialização. Databricks, dbt e Databricks
SQL não fazem parte do runtime atual. Migrar o banco sem corrigir grão, filtros,
agregações e consultas caras não garante dashboards rápidos.

### Isolamento por cliente

1. O usuário entra no portal NeoRetail.
2. O backend lê os clientes permitidos em `config/tenants.yaml`.
3. O usuário seleciona uma indústria autorizada.
4. O backend solicita ao Superset um Guest Token com uma cláusula como
   `id_customer = 142`.
5. O Superset aplica o RLS antes de calcular métricas e renderizar os gráficos.

Os filtros visíveis refinam a análise. Eles não substituem o RLS e não devem
ser usados como fronteira de segurança.

## Clientes iniciais

| `id_customer` | Cliente | Prefixo no Blob |
|---:|---|---|
| 142 | AMBEV | `FATO/CUSTOMER/DAILY/NM_CUSTOMER=AMBEV` |

O portal, o catálogo embedded e o RLS da POC estão configurados exclusivamente
para a AMBEV. A descoberta da origem diária particionada já foi validada, com
902 arquivos encontrados. A promoção desses dados aos contratos Silver/Gold e
aos sete marts ainda exige um adaptador explícito para esse layout de origem;
até essa etapa, os dashboards da AMBEV podem abrir sem dados. O pipeline atual
foi criado para as famílias legadas e não deve inferir fórmulas de negócio para
preencher os marts.

O cadastro corporativo fica em [`config/customers.yaml`](config/customers.yaml).
As permissões da POC embedded ficam em
[`config/tenants.yaml`](config/tenants.yaml). O pipeline valida o nome e o ID
contra `DIMENSAO_CUSTOMER` antes de publicar a Silver.

## Serviços locais

| Serviço | Finalidade | Acesso padrão |
|---|---|---|
| `superset-db` | Metadados, usuários, datasets, charts e dashboards | interno |
| `analytics-db` | Schemas `bronze`, `silver`, `gold` e `audit` | `localhost:5433` |
| `redis` | Cache e suporte ao Superset | interno |
| `superset-init` | Migrações, administrador e conexão Analytics | job one-shot |
| `superset` | Exploração e dashboards | <http://localhost:8088> |
| `local-engine` | PySpark, pipeline e Jupyter | <http://localhost:8888> |
| `embedded-app` | Portal multitenant demonstrativo | <http://localhost:3000> |
| `blob-profiler` | Perfil opcional das fontes no Blob | profile `blob` |

## Pré-requisitos

- Docker Desktop com Docker Compose v2;
- PowerShell 5.1 ou superior no Windows;
- pelo menos 8 GB de memória disponíveis para o Docker;
- acesso ao Azure Blob somente para executar o pipeline de dados;
- Git e Node.js apenas para desenvolvimento fora dos containers.

## Início rápido

No Windows:

```powershell
Copy-Item .env.example .env
.\start.ps1 -Rebuild
```

O parâmetro `-Rebuild` compila as imagens, inclusive o frontend customizado do
Superset. Nas execuções seguintes, quando o código das imagens não mudou:

```powershell
.\start.ps1
```

Em Linux ou macOS:

```bash
cp .env.example .env
./start.sh --build
```

O start funciona sem credencial do Blob. A ingestão permanece bloqueada até
que `AZURE_STORAGE_CONNECTION_STRING` seja preenchida no `.env`.

Credenciais locais padrão do Superset:

```text
usuário: admin
senha:   admin
```

Troque as credenciais e as chaves antes de usar o ambiente fora do localhost.

## Configuração

Copie [`.env.example`](.env.example) para `.env`. O arquivo `.env` não deve ser
versionado.

| Variável | Uso |
|---|---|
| `SUPERSET_SECRET_KEY` | assinatura interna do Superset |
| `GUEST_TOKEN_JWT_SECRET` | assinatura dos Guest Tokens |
| `SUPERSET_ADMIN_*` | usuário administrador local |
| `ANALYTICS_DB_*` | conexão com o PostgreSQL Analytics |
| `AZURE_STORAGE_CONNECTION_STRING` | acesso à fonte no Blob |
| `AZURE_STORAGE_CONTAINER` | container do Azure Storage |
| `NEORETAIL_CUSTOMER` | cliente padrão dos comandos locais |
| `LOCAL_LAKE_FORMAT` | `parquet` por padrão; `delta` é opcional |
| `SPARK_DRIVER_MEMORY` | memória do driver PySpark |
| `PUBLIC_SUPERSET_URL` | URL usada pelo portal embedded |
| `DEMO_USER_PASSWORD` | senha do usuário demonstrativo |

O valor padrão de `LOCAL_LAKE_FORMAT=parquet` evita baixar JARs do Maven.
O modo `delta` pode exigir acesso externo na primeira inicialização.

## Pipeline de dados

O comando principal executa uma etapa para um cliente por vez:

```powershell
.\run-local-pipeline.ps1 -Step 02A -Customer 142
```

O parâmetro `-Customer` aceita o ID ou o nome cadastrado. O resumo da execução
fica em `generated/local_pipeline_summary.json`.

| Etapa | Responsabilidade |
|---|---|
| `00` | prepara diretórios, schemas e configuração local |
| `01` | descobre e inventaria os arquivos do Blob |
| `02A` | carrega dimensões aprovadas na Bronze |
| `02B` | materializa fatos candidatos por família e varejista |
| `03A` | normaliza as dimensões na Silver |
| `03B` | consolida fatos com tratamento de schema drift |
| `03C` | estrutura oportunidades a partir do `ETL_CALC_V2` |
| `03D` | compara Bronze e Silver e grava o quality gate |
| `04` | verifica as famílias aprovadas para publicação |
| `05` | publica dimensões Gold no lake e no PostgreSQL |
| `06` | publica fatos Gold aprovados |
| `07` | registra a prontidão das métricas |
| `08` | executa o quality gate final da Gold |

Fluxo recomendado para o primeiro cliente:

```powershell
.\run-local-pipeline.ps1 -Step 02A -Customer 142
.\run-local-pipeline.ps1 -Step 02B -Customer 142
.\run-local-pipeline.ps1 -Step 03A -Customer 142
.\run-local-pipeline.ps1 -Step 03B -Customer 142
.\run-local-pipeline.ps1 -Step 03C -Customer 142
.\run-local-pipeline.ps1 -Step 03D -Customer 142
.\run-local-pipeline.ps1 -Step 04  -Customer 142
.\run-local-pipeline.ps1 -Step 05  -Customer 142
.\run-local-pipeline.ps1 -Step 06  -Customer 142
.\run-local-pipeline.ps1 -Step 07  -Customer 142
.\run-local-pipeline.ps1 -Step 08  -Customer 142
```

Para atualizar o tenant ativo:

```powershell
.\run-multitenant-refresh.ps1
```

`FATO_MERCADO` está fora do pipeline da POC. Mesmo que existam candidatos de
mercado antigos no lake local, as etapas Silver e de validação não os processam.

As etapas `04` e `06` retornam `blocked` enquanto
[`config/approved_facts.yaml`](config/approved_facts.yaml) não possuir fatos
aprovados. Esse resultado é uma proteção e não uma falha técnica.

### Particionamento e idempotência

- lake: `<camada>/<tabela>/id_customer=<ID>`;
- PostgreSQL: cada carga substitui somente as linhas do cliente processado;
- joins incluem `id_customer` junto à chave de item, local ou negócio;
- o cache não baixa novamente um Blob com o mesmo ETag;
- a Bronze preserva arquivo, varejista, família, status e horário de ingestão;
- a Gold recebe somente fatos registrados como aprovados.

## Superset e dashboards

O `superset-init` executa migrações, cria o administrador, sincroniza papéis e
cadastra a conexão `NeoRetail Gold - PostgreSQL Local`. Os dashboards são
criados por scripts idempotentes, que podem ser executados novamente para
atualizar charts e layouts existentes.

Se a Gold acabou de ser publicada ou atualizada, execute:

```powershell
.\create-superset-kpi-views.ps1
```

Esse comando aplica as views de `analytics-db/views` e recria os marts físicos
de `analytics-db/marts` no schema Gold. Os marts persistem os joins, recortes de
último período e janelas usados pelos dashboards e possuem índices iniciados por
`id_customer`, que também é a chave de RLS. Depois da carga, o comando executa
`ANALYZE` para o PostgreSQL escolher planos com estatísticas atualizadas.

Os scripts abaixo apontam o Superset para esses objetos físicos e escrevem
somente datasets, charts e layouts no banco de metadados do Superset.

```powershell
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/bootstrap_overview.py
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/bootstrap_panorama.py
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/bootstrap_osa_industry.py
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/bootstrap_stock_optimization.py
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/bootstrap_embedded.py
```

Os oito marts compartilhados são:

| Mart físico | Uso principal |
|---|---|
| `gold.nr_overview_history` | visão mensal, Panorama e OSA |
| `gold.nr_panorama_latest` | comparativos e rankings do último mês por indústria |
| `gold.nr_panorama_weekly` | evolutivos semanais |
| `gold.nr_panorama_opportunities` | TVD/IVD diário e marcadores de fechamento |
| `gold.nr_panorama_opportunities_latest` | falta/excesso no último movimento |
| `gold.nr_osa_industry_causes` | perdas OSA por motivo e causa |
| `gold.nr_stock_tasks` | rankings e incidências de pré-ruptura/excesso |
| `gold.nr_tvd_daily` | TVD diário e contagens aditivas de criticidade, com filtros e RLS |

O SQL versionado desses contratos está em
[`analytics-db/marts/30_neoretail_serving_marts.sql`](analytics-db/marts/30_neoretail_serving_marts.sql).
Na arquitetura futura, eles devem ser portados para modelos dbt incrementais
antes de o Superset trocar de fonte.

O refresh multitenant completo já chama `create-superset-kpi-views.ps1` depois
de atualizar os clientes configurados. Portanto, a camada física sempre é reconstruída
com o estado final da Gold:

```powershell
.\run-multitenant-refresh.ps1
```

| Dashboard | Slug | Conteúdo principal |
|---|---|---|
| NeoRetail V9 — Visão geral da indústria | `neoretail-v9-visao-geral-industria` | TVD, IVD, giro, vendas, estoque, ROI, markup e OSA |
| NeoRetail V9 — Panorama Indústria | `neoretail-v9-panorama-industria` | evolutivos, comparativos, rankings e análise detalhada |
| NeoRetail V9 — OSA Indústria | `neoretail-v9-osa-industria` | visão mensal, perdas por motivo/causa e rankings OSA |
| NeoRetail V9 — Tarefas de Otimização — Estoque | `neoretail-v9-tarefas-otimizacao-estoque` | tendências TVD/IVD, rankings e incidências de estoque |

### Performance medida

A primeira rodada substituiu SQLs virtuais reutilizados por marts físicos:

| Consulta mensal representativa | Tempo local |
|---|---:|
| SQL virtual | 1.646,7 ms |
| Mart físico | 433,6 ms |
| Redução | 73,7% |
| Ganho aproximado | 3,8x |

A segunda rodada investigou o card `TVD - Pré-ruptura` com
`EXPLAIN (ANALYZE, BUFFERS)`. A consulta antiga lia 6.205.243 linhas, fazia
`COUNT(DISTINCT CASE...)`, `GroupAggregate` e uma ordenação `external merge` de
aproximadamente 299 MiB.

O mart `gold.nr_tvd_daily` transfere esse cálculo para o refresh e entrega ao
Superset métricas somáveis. Ele preserva `id_customer` e todas as dimensões dos
filtros nativos.

Este benchmark histórico foi executado antes da mudança de escopo para a AMBEV
e usou o tenant 259. Ele comprova a otimização do mart, mas não mede o tenant 142.

| Consulta TVD | Antes | Depois |
|---|---:|---:|
| Sem filtro de indústria | 5.621 ms | 1.722 ms |
| Repetição | cerca de 5–6 s | 1.525 ms |
| RLS `id_customer = 259` | 4.288 ms | 1.746 ms |
| RLS 259, repetição | — | 1.558 ms |
| Arquivo temporário de ordenação | ~299 MiB | zero |

A reconciliação comparou 272 combinações de indústria e dia, sem divergência
nas contagens. O maior delta de TVD foi `1,58 x 10^-8`, causado pela ordem da
soma de valores de ponto flutuante. Também foi confirmado que uma oportunidade
não pertence a mais de uma combinação de filtros no mesmo dia.

Os oito marts ocupam aproximadamente 6,25 GiB no snapshot atual; somente
`nr_tvd_daily` ocupa cerca de 1,81 GiB com índices. Esse é o trade-off local:
mais custo e armazenamento no refresh para reduzir a latência interativa.

Exemplo de URL:

```text
http://localhost:8088/superset/dashboard/neoretail-v9-osa-industria/
```

O Panorama usa abas do Superset para as alternâncias Mensal/Semanal,
Valor/Quantidade e Estoque/Giro/OSA/Falta e Excesso. A tela OSA usa as abas
Valor/Perdas, equivalentes aos bookmarks do Power BI. O cliente inicial desses
dois dashboards é AMBEV (`id_customer = 142`).

### Filtros nativos

Os dashboards usam filtros horizontais sobre as dimensões disponíveis:

- indústria;
- rede e bandeira;
- UF e cidade;
- tipo de local e loja;
- nível de atividade;
- marca;
- hierarquias de item;
- item e período.

As dependências podem ser organizadas em cascata, por exemplo:
`rede → bandeira → UF → cidade → loja`.

## Plugin NeoRetail KPI Card

O plugin está em
[`superset/frontend-plugin/plugin-chart-neoretail-kpi`](superset/frontend-plugin/plugin-chart-neoretail-kpi)
e é registrado no `MainPreset` durante o build da imagem.

Ele suporta:

- área com MTD, mês anterior e média U3M;
- barras comparativas;
- cartões com vários indicadores;
- evolutivos combinando barras e linhas;
- rankings horizontais;
- colunas empilhadas;
- barras verticais por categoria;
- valores sobre barras e junto aos pontos das linhas;
- tarefas críticas e itens em risco;
- miniatura própria no seletor de gráficos.

Os filtros nativos e o RLS entram no `QueryObject` do Superset antes de os
resultados chegarem ao componente React. Handlebars e Jinja não são usados
como mecanismo de segurança.

Depois de alterar o frontend do plugin:

```powershell
docker compose build superset
docker compose up -d superset
```

Atualize o navegador com `Ctrl+Shift+R` para descartar o bundle anterior.

## Portal embedded

O portal em <http://localhost:3000> oferece uma experiência própria do
NeoRetail. Depois do login, a página **Minhas soluções** abre a seleção entre as
três indústrias autorizadas. O produto organiza os quatro dashboards em menus
de Visão geral, Panorama e Tarefas do dia, sem expor a navegação administrativa
do Superset.

A REST API do portal mantém a sessão, publica o catálogo autorizado e emite um
Guest Token específico para a combinação de dashboard e indústria. O token
aplica `id_customer` como RLS antes de qualquer consulta analítica.

Antes de testar o embedded:

1. use `demo.multitenant` / `neoretail-demo` ou defina `DEMO_USER_PASSWORD` no `.env`;
2. confirme que `PUBLIC_SUPERSET_URL` é acessível pelo navegador;
3. execute `superset/bootstrap_embedded.py` após os quatro bootstraps de dashboard;
4. recrie o serviço com `docker compose up -d --build embedded-app`;
5. teste pelo menos dois clientes e uma tentativa com cliente não autorizado.

O catálogo base em `config/tenants.yaml` define os menus, módulos, slugs e UUIDs
reproduzíveis da POC. Administradores também podem abrir um dashboard no
Superset e usar **Publicar no NeoRetail**, ao lado de **Editar dashboard**. A
ação publica o dashboard, habilita o recurso embedded, remove o filtro visível
de indústria e grava sua entrada dinâmica em
`generated/neoretail-published-dashboards.json`. O portal lê esse arquivo a cada
requisição, portanto a nova tela fica disponível sem editar YAML ou reiniciar o
produto.

## Validação

Validação estrutural, de sintaxe e build:

```powershell
.\validate.ps1
```

Smoke test do fluxo PySpark → PostgreSQL Analytics → Superset:

```powershell
.\test-local.ps1
```

Saúde dos containers e endpoints:

```powershell
.\health.ps1
.\status.ps1
```

Validação das consultas dos dashboards:

```powershell
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/validate_overview.py
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/validate_panorama.py
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/validate_osa_industry.py
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/validate_stock_optimization.py
```

Teste de regressão do plugin, quando Node.js estiver instalado no host:

```powershell
node superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/regression.mjs
```

## Operação diária

```powershell
# Estado e saúde
.\status.ps1

# Parar sem remover dados
.\stop.ps1

# Acompanhar logs
docker compose logs -f superset
docker compose logs -f local-engine

# Reconstruir depois de alterar Dockerfile ou frontend
.\start.ps1 -Rebuild
```

O reset remove os volumes de metadados, Analytics, Redis e lake local:

```powershell
.\reset.ps1 -Confirm
```

Use esse comando somente quando a perda do ambiente local for intencional.
O código, o `.env` e a pasta `generated` são preservados.

## Estrutura do repositório

```text
analytics-db/       inicialização e views do PostgreSQL Analytics
blob-profiler/      inventário e perfil opcional dos arquivos do Blob
config/             clientes, tenants, fontes e contratos analíticos
docs/               arquitetura, runbooks e troubleshooting
embedded-app/       backend e frontend do portal demonstrativo
local-engine/       pipeline PySpark, notebooks e testes
scripts/            validações auxiliares do projeto
superset/           imagem, configuração, plugin e bootstraps de dashboards
generated/          relatórios gerados localmente e não versionados
certs/              certificados corporativos locais e não versionados
```

## Adicionar uma indústria

1. confirme `id_customer` e `nm_customer` na dimensão corporativa;
2. cadastre o cliente em `config/customers.yaml`;
3. adicione as permissões da POC em `config/tenants.yaml`;
4. registre os caminhos comprovados em `config/source_catalog.yaml`;
5. execute descoberta, Bronze, Silver e os quality gates para o cliente;
6. aprove explicitamente os fatos antes da Gold;
7. valide o RLS com um usuário autorizado e outro não autorizado.

Não crie fórmulas de TVD, IVD, OSA, giro ou oportunidades por aproximação. Os
contratos de métricas em `config/metric_contracts.yaml` exigem definição de
negócio, expressão, fontes, grão, filtros, política de nulos, exemplos e
aprovação antes da publicação.

## Evolução para produto

O caminho recomendado mantém a separação de responsabilidades já validada:

```text
ingestão e schema drift
    → PySpark/Databricks

transformações analíticas estáveis
    → dbt entre Silver e Gold

serving interativo
    → marts físicos/incrementais preparados para BI

exploração e apresentação
    → Superset

identidade e autorização
    → backend NeoRetail + Guest Token + RLS
```

### Papel proposto do dbt

Os oito marts atuais funcionam como contratos de referência. A primeira etapa
do dbt deve portar esses SQLs para modelos governados e provar equivalência,
antes de criar novas regras.

Estrutura inicial sugerida:

```text
dbt/
  models/
    staging/       tipagem e padronização das fontes Silver
    intermediate/ joins e regras reutilizadas
    marts/         grão final consumido pelo Superset
  tests/
  macros/
  snapshots/
```

Materializações sugeridas:

| Camada | Estratégia inicial |
|---|---|
| `staging` | `view` |
| `intermediate` reutilizado | `table` ou `incremental` |
| marts de dashboard | `incremental` |
| dimensões pequenas e listas de filtros | `table` |
| lógica simples de uso único | `ephemeral` |

Cada modelo multitenant deve declarar grão, chave única, `id_customer`, regra
incremental, coluna temporal, fontes, joins, política de nulos e duplicidade,
métricas atendidas e orçamento de performance. Os testes mínimos incluem
`not_null`, `unique`, `relationships`, valores aceitos, reconciliação Silver ×
Gold e isolamento por indústria.

### Prioridades antes da produção

**P0 — bloqueiam a liberação:**

- reconciliar e aprovar as métricas prioritárias com o Power BI e o negócio;
- testar vazamento cruzado de tenant em CI, inclusive filtros e endpoints;
- integrar identidade corporativa e autorização oficial do NeoRetail;
- definir SLA, p95 de dashboards, volume e concorrência esperados;
- automatizar pipeline incremental e bloquear publicação quando gates falharem;
- validar a arquitetura com volume representativo dos aproximadamente 22 tenants.

**P1 — operação confiável:**

- separar DEV, HML e PROD;
- persistir e auditar o catálogo de dashboards, com aprovação e rollback;
- centralizar logs, métricas e alertas de pipeline, marts, queries e embedded;
- definir backup e recuperação do metadata database do Superset;
- medir warehouse frio/aquecido, cache, custo e concorrência;
- substituir a recriação integral dos marts por processamento incremental.

**P2 — evolução e acabamento:**

- criar dimensões enxutas para listas de filtros com muitos valores;
- revisar responsividade, alturas embedded, labels, loading e estados de erro;
- dividir o plugin visual quando surgirem comportamentos próprios de combo,
  ranking, mapa ou interação operacional;
- documentar linhagem e contratos dbt e publicar a documentação técnica.

### Escala para novos tenants

O pipeline aceita processamento parametrizado por cliente, mas a estratégia de
agrupar aproximadamente 22 tenants deve ser definida por medição. Clientes com
volumes diferentes podem exigir janelas e recursos diferentes. Antes de fixar
um tamanho de lote, registre por tenant:

- arquivos e linhas processadas;
- duração de cada etapa e do refresh de marts;
- volume armazenado e crescimento;
- tempo p50/p95/p99 dos gráficos;
- concorrência e cache hit;
- custo de compute/SQL Warehouse;
- impacto de falha e tempo de recuperação.

GitHub Actions ou GitLab CI pode validar código e disparar o processamento. No
ambiente local, o refresh exige runner self-hosted com Docker e acesso ao Azure.
Na arquitetura alvo, CI/CD deve autenticar por identidade federada/OIDC e
disparar Databricks Workflows; secrets permanentes não devem ficar no
repositório.

## Limites conhecidos da POC

- autenticação do portal ainda é demonstrativa;
- o catálogo dinâmico usa um JSON compartilhado local;
- os marts são recriados integralmente e podem segurar locks durante o refresh;
- métricas renderizadas ainda precisam de certificação formal do negócio;
- não há evidência suficiente de escala e concorrência para 22 tenants;
- não há implantação real de Databricks, Delta, dbt ou SQL Warehouse;
- resultados locais de performance não determinam o sizing produtivo;
- observabilidade, DR, rollback e ambientes separados ainda precisam ser
  implementados.

## Solução de problemas

- **PowerShell bloqueou scripts:** execute
  `Set-ExecutionPolicy -Scope Process Bypass`.
- **Pipeline informa credencial ausente:** preencha
  `AZURE_STORAGE_CONNECTION_STRING` no `.env`.
- **Porta 5433 ocupada:** altere `ANALYTICS_DB_PORT` no `.env`.
- **PySpark sem memória:** mantenha ao menos 8 GB no Docker e aumente
  `SPARK_DRIVER_MEMORY` gradualmente.
- **Superset não mostra a Gold:** execute o pipeline até a etapa 08, aplique as
  views e sincronize o schema `gold`.
- **Gráfico ainda usa o frontend anterior:** pressione `Ctrl+Shift+R`.
- **`superset-init` aparece `Exited (0)`:** comportamento correto; ele é um job
  de inicialização, não um serviço permanente.

Veja o guia completo em
[`docs/troubleshooting.md`](docs/troubleshooting.md).

## Documentação adicional

- [Arquitetura multitenant V9](docs/v9_multitenant_architecture.md)
- [Runbook V9](docs/v9_runbook.md)
- [Pipeline local](docs/local_pipeline.md)
- [Workflow Blob First](docs/blob_first_workflow.md)
- [Plugin NeoRetail KPI Card](docs/custom_kpi_plugin.md)
- [Paridade com Power Query](docs/power_query_parity.md)
- [Agendamento no GitLab](docs/gitlab_scheduling.md)
- [Relatório de validação](docs/validation_report.md)
- [Histórico da POC e plano de evolução para produto](docs/poc_history_and_productization.md)

## Segurança e versionamento

- nunca versione `.env`, SAS, senhas, tokens ou connection strings reais;
- mantenha certificados locais em `certs/`;
- use Guest Token com RLS para isolamento e filtros nativos para navegação;
- revise qualquer alteração em `analytics-db` antes de aplicá-la;
- os scripts `bootstrap_*.py` alteram somente metadados do Superset e consultam
  a camada Analytics em modo de leitura.
