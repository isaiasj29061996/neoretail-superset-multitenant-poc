# Teste local de concorrência — NeoRetail / Superset

Este teste mede a concorrência do backend analítico quando vários usuários
abrem o mesmo dashboard. Ele executa as consultas persistidas dos charts por
`QueryContextFactory` e `ChartDataCommand` e monitora `superset`, `analytics-db`
e `redis` com `docker stats`.

> Este é um **backend/query concurrency benchmark**. Ele não atravessa HTTP,
> Gunicorn, Embedded API, Guest Token, navegador ou renderização React.

## Execução

Categoria realista, com o primeiro acesso frio e cache habilitado durante o
cenário:

```powershell
.\load-test-users.ps1 `
  -Users 1,5,10 `
  -Dashboard "neoretail-v9-visao-geral-industria" `
  -ColdCache
```

Capacidade bruta, sem leitura do cache de resultados:

```powershell
.\load-test-users.ps1 `
  -Users 1,5,10 `
  -Dashboard "neoretail-v9-visao-geral-industria" `
  -ColdCache `
  -ForceNoCache
```

Panorama:

```powershell
.\load-test-users.ps1 `
  -Users 1,5,10 `
  -Dashboard "neoretail-v9-panorama-industria" `
  -ColdCache
```

`-ColdCache` limpa Redis DB 1, 2, 3 e 4 antes de cada cenário. O cenário
`-Dashboard all` continua disponível como stress test, mas não representa uma
única página do produto.

## Telemetria no Windows

O monitor usa um processo PowerShell separado, iniciado com janela oculta. Esse
processo mantém um único `StreamWriter`, executa polling de `docker stats`,
libera o arquivo no encerramento e só então permite a leitura pelo processo
principal.

Essa arquitetura evita o erro `O fluxo não era legível` observado com
`Start-Job` e `Add-Content`. Falhas de telemetria geram aviso e não interrompem
os cenários seguintes. Cada cenário gera:

- resultado detalhado do benchmark em `.json`;
- amostras brutas de recursos em `-docker-stats.log`;
- máximos por container em `-resources.json`;
- uma tabela consolidada da bateria em `summary-*.json`.

## Semântica do cache

No Superset 6, `QueryContextFactory.create()` recebe `force` como argumento
próprio. Incluir `force` somente em `form_data` não altera
`QueryContext.force`.

O benchmark passa agora `force=LOAD_TEST_FORCE`. No
`QueryContextProcessor.get_df_payload()`, isso resulta em
`force_query = QueryContext.force`, fazendo `QueryCacheManager.get()` ignorar a
leitura do resultado armazenado. A bateria `-ForceNoCache` confirmou **0% de
cache hit** em 1, 5 e 10 usuários.

## Usuários, queries e workers

Usuários simultâneos e queries simultâneas são grandezas diferentes:

- Visão Geral: 8 charts por usuário;
- Panorama: 33 charts por usuário;
- 10 usuários da Visão Geral criam 80 tarefas de chart;
- 10 usuários do Panorama criam 330 tarefas de chart.

O executor limita quantas tarefas rodam ao mesmo tempo. O padrão foi ajustado
para **12 workers**. O processo interno usa um único pool de metadata SQLAlchemy
com `pool_size=5`, `max_overflow=10` e capacidade máxima de 15 conexões.
Doze workers deixam margem para operações auxiliares.

O valor anterior de 40 workers causou, em 10 usuários, um timeout de pool e
1,25% de erros. Esse resultado era metodologicamente misto: tentava reproduzir
os 2 workers × 20 threads do Gunicorn dentro de um único processo Python, que
possui apenas um pool de metadata. O limite 40 continua útil como stress test
explícito, mas não é o padrão do benchmark interno.

O deploy HTTP atual possui 2 workers Gunicorn × 20 threads. Este benchmark não
passa pelo Gunicorn e, portanto, não comprova que as 40 threads HTTP são
suficientes. Essa validação pertence ao teste E2E/HTTP.

## Resultados — Visão Geral, cache habilitado

Medição local de 18/09/2026, `id_customer = 142`, cache limpo antes de cada
cenário e até 12 charts em execução simultânea.

| Users | p50 chart | p95 chart | Page p95 | Throughput | CPU Superset | RAM Superset | CPU DB | RAM DB | CPU Redis | RAM Redis | Errors |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 5,24 s | 7,44 s | 7,45 s | 1,07 req/s | 190,68% | 1.041 MiB | 1.292,78% | 1.018 MiB | 4,02% | 7,63 MiB | 0% |
| 5 | 5,79 s | 10,40 s | 22,29 s | 1,79 req/s | 188,41% | 1.050 MiB | 1.349,53% | 1.065 MiB | 4,43% | 11,27 MiB | 0% |
| 10 | 6,30 s | 14,11 s | 50,98 s | 1,57 req/s | 128,58% | 1.054 MiB | 1.450,90% | 1.063 MiB | 17,72% | 8,10 MiB | 0% |

Degradação relativa do p95 de chart:

- 5 usuários / 1 usuário: **1,40×**;
- 10 usuários / 1 usuário: **1,90×**.

Crescimento da RAM do Superset:

- 5 usuários / 1 usuário: **1,008×**;
- 10 usuários / 1 usuário: **1,012×**.

## Resultados — Visão Geral, bypass de cache

| Users | p50 chart | p95 chart | Page p95 | Throughput | CPU Superset | RAM Superset | CPU DB | RAM DB | Cache hits | Errors |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 6,27 s | 7,44 s | 7,74 s | 1,03 req/s | 206,63% | 1.037 MiB | 1.015,21% | 2.759 MiB | 0% | 0% |
| 5 | 7,07 s | 15,32 s | 31,87 s | 1,25 req/s | 120,09% | 1.049 MiB | 1.494,87% | 2.792 MiB | 0% | 0% |
| 10 | 8,15 s | 17,21 s | 61,88 s | 1,29 req/s | 198,92% | 1.053 MiB | 1.440,38% | 2.805 MiB | 0% | 0% |

Degradação relativa do p95 de chart:

- 5 usuários / 1 usuário: **2,06×**;
- 10 usuários / 1 usuário: **2,31×**.

Crescimento da RAM do Superset:

- 5 usuários / 1 usuário: **1,011×**;
- 10 usuários / 1 usuário: **1,015×**.

## Resultados — Panorama, cache habilitado

| Users | p50 chart | p95 chart | Page p95 | Throughput | CPU Superset | RAM Superset | CPU DB | RAM DB | Errors |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2,37 s | 7,93 s | 10,36 s | 3,19 req/s | 193,83% | 1.047 MiB | 330,95% | 2.666 MiB | 0% |
| 5 | 2,13 s | 7,73 s | 44,35 s | 3,72 req/s | 132,85% | 1.059 MiB | 1.326,35% | 2.801 MiB | 0% |
| 10 | 1,98 s | 9,30 s | 77,34 s | 4,27 req/s | 130,07% | 1.074 MiB | 1.400,12% | 2.802 MiB | 0% |

O p95 de chart cresceu apenas **1,17×** entre 1 e 10 usuários, mas o page p95
cresceu por causa das 330 tarefas e da fila de 12 workers. A RAM do Superset
cresceu **1,026×**.

## Diagnóstico

O primeiro gargalo observado é o **PostgreSQL Analytics local e o fan-out de
charts**, não memória do Superset:

- Superset ficou entre aproximadamente 120% e 207% de CPU;
- PostgreSQL chegou a aproximadamente 1.495% de CPU, equivalente ao uso de
  cerca de 15 cores; `docker stats` permite valores acima de 100% em máquinas
  multicore;
- a RAM do Superset ficou entre 1,04 e 1,07 GiB, sem crescimento contínuo;
- Redis permaneceu pequeno e não aparece como gargalo;
- a Visão Geral sem cache piorou de forma clara, comprovando o benefício do
  result cache;
- os charts mensais de Vendas, Giro/ROI, OSA e Markup continuam entre os mais
  caros sob concorrência;
- no Panorama, a quantidade de charts domina o tempo total da página mesmo
  quando a latência individual permanece relativamente controlada.

Os resultados sustentam estabilidade técnica com 10 usuários — não houve erro
na configuração metodologicamente válida —, mas **não sustentam ainda uma UX
aceitável para dez aberturas frias simultâneas**. Page p95 de 50,98 s na Visão
Geral e 77,34 s no Panorama exige reduzir fan-out, custo SQL e/ou quantidade de
charts carregados inicialmente.

## Configuração de produção

Não há evidência para aumentar workers agora. O próximo teste deve manter como
baseline os 2 workers × 20 threads e exercitar o endpoint HTTP real. Nesse
teste, comparar de forma controlada alternativas como 2×10 e 4×10, respeitando:

- número máximo de conexões do metadata database por worker;
- orçamento de conexões do serving/DW;
- CPU disponível;
- timeout e tamanho das filas;
- cache compartilhado no Redis.

Se 20 threads por worker forem mantidas, o pool de metadata também precisa ser
dimensionado de forma coerente. O padrão observado de 5 + 10 conexões por
processo é menor que 20 threads, mas só deve ser alterado após o teste HTTP e a
definição do orçamento total de conexões.

## Próximo teste: E2E/HTTP

Criar uma suíte separada, sem misturar seus números com este benchmark, para
medir:

1. login NeoRetail;
2. catálogo;
3. emissão de Guest Token;
4. carregamento do Superset embedded via HTTP;
5. consultas dos charts;
6. tempo percebido pelo navegador.

Essa etapa poderá validar Gunicorn, rede, autenticação, Guest Token, embedded e
renderização. Os resultados locais também precisam ser repetidos contra o DW
produtivo antes de definir SLA ou sizing definitivo.
