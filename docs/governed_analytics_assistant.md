# NeoRetail Analytics Assistant - POC governada

## Objetivo e fronteira

O assistente é uma camada opcional de consumo. Ele reutiliza a sessão do portal,
o `selectedCustomerId` autorizado e os marts existentes. O PostgreSQL calcula,
a governança autoriza e o provider de linguagem explica.

O LLM não recebe conexão de banco, não produz SQL, não troca tenant, não altera
métricas e não certifica regras de negócio. Perguntas fora do catálogo são
recusadas.

```text
sessão NeoRetail
  -> tenant confiável
  -> orquestrador
  -> catálogo + ferramentas allowlisted
  -> PostgreSQL em transação READ ONLY
  -> resultado + evidência
  -> provider mock ou Ollama
  -> resposta
```

## Isolamento operacional

- `ASSISTANT_ENABLED=false` por padrão;
- o portal não depende do Ollama para iniciar;
- `ollama` pertence ao profile Compose `assistant`;
- o modelo não é baixado durante o start normal;
- o painel só aparece quando a sessão retorna `assistantEnabled=true`;
- falha do assistente não afeta Superset, pipeline, dashboards ou Guest Token.

## Providers

`LLMProvider` define `health()` e `generate()`. A POC possui:

- `MockProvider`: determinístico, sem rede, adequado a CI e testes de segurança;
- `OllamaProvider`: usa `/api/tags` e `/api/chat`, modelo configurado por
  `OLLAMA_MODEL` e timeout por `LLM_TIMEOUT_MS`.

A aplicação fora do módulo de providers não depende da API do Ollama. Outro
provider pode implementar a mesma interface futuramente.

## Catálogo e ferramentas

O catálogo versionado está em `config/assistant_metrics.yaml`. Nesta branch ele
é alinhado às evidências herdadas das PRs #3 e #4, sem promover aprovação de
negócio ou certificação temporal. `RECONCILED` significa que a fórmula base foi
reconciliada tecnicamente; `CERTIFICADA` em TVD/IVD se restringe ao caminho
técnico fonte → mart → Superset documentado. Todas permanecem com aprovação de
negócio pendente e com `PARCIAL_CALENDARIO`.

| Métrica | Padrão sem filtro | Com filtros | Estado técnico | Evidência |
|---|---|---|---|---|
| Vendas (unidade) | `gold.nr_overview_quantity_default` | `gold.nr_overview_quantity_detail` | `RECONCILED` | `validate_overview_quantity.py` |
| % OSA | `gold.nr_overview_quantity_default` | `gold.nr_overview_quantity_detail` | `RECONCILED` | `validate_overview_quantity.py` |
| Estoque (quantidade) | `gold.nr_overview_quantity_default` | `gold.nr_overview_quantity_detail` | `RECONCILED` | `validate_overview_quantity.py` |
| TVD | `gold.nr_tvd_daily_summary` | `gold.nr_tvd_daily` | `CERTIFICADA` técnica | `validate_stock_headlines.py` |
| IVD | `gold.nr_ivd_daily_summary` | `gold.nr_ivd_daily` | `CERTIFICADA` técnica | `validate_stock_headlines.py` |

O campo `source` da evidência de cada resposta registra o mart realmente
consultado. `defaultSource`, `filteredSource`, `validator`, `contract`, versão da
fórmula e estados também são devolvidos, permitindo auditar o caminho numérico.

Ferramentas:

- `get_metric`;
- `get_metric_comparison`;
- `get_metric_timeseries`;
- `get_top_opportunities`;
- `get_osa_causes`;
- `get_stock_tasks`;
- `explain_metric`;
- `get_metric_governance`.

As consultas são constantes no backend. Tenant e filtros entram apenas como
parâmetros PostgreSQL. O limite de rankings é dez linhas. A conexão executa cada
consulta dentro de `BEGIN READ ONLY`, com `statement_timeout`.

`MTD`, `M-1` e `U3M` seguem o contrato implementado pela Visão Geral Quantidade:
último mês disponível, deslocamento exato de um mês e meses exatos M-1/M-2/M-3.
Para medidas aditivas, U3M divide a soma pelo divisor fixo três. Para % OSA, o
assistente soma problemas e ativos dos meses do período e só então recompõe a
razão; não calcula média de percentuais. Denominador zero preserva `BLANK`.

Essas regras comprovam consistência com o contrato implementado, mas não
substituem as flags DAX M0/M-1/U3M/LY ausentes. O estado continua
`PARCIAL_CALENDARIO`; Vendas e OSA também mantêm `PENDENTE_VARIANCE_DAX`.

O caminho filtrado de Vendas usa SQL fixo allowlisted para reproduzir
`SUM(volume_unidades) * MAX(fator)` na medida `unidade`. O usuário não fornece
SQL, nome de mart, fórmula nem tenant.

Para TVD/IVD filtrados, o mart resumo seleciona as datas de fechamento mensais
e o mart detalhado agrega somente essas datas. No snapshot AMBEV local, com o
filtro `uf=SP`, essa mudança reduziu TVD de aproximadamente 10,37 s para 258 ms
e IVD de 9,11 s para 193 ms, mantendo os mesmos valores. São medições locais e
não constituem SLA de produção.

## APIs

### `GET /api/assistant/health`

Não expõe secrets. Retorna `disabled`, `ok` ou `degraded`, provider, modelo e
disponibilidade.

### `POST /api/assistant/chat`

```json
{
  "message": "Como está o OSA este mês?",
  "context": {
    "dashboard": "overview",
    "filters": { "uf": "SP" }
  }
}
```

`tenantId`, `idCustomer` e `filters.id_customer` são proibidos no payload. O
backend usa exclusivamente o tenant da sessão e devolve HTTP 403 em tentativas
de override.

## Comportamento conversacional determinístico

O orchestrator distingue valor, comparação, variação, fonte, explicação da
fórmula, versão da fórmula e governança antes de chamar o provider. A métrica
ativa vem do texto explícito, do `context.metricId` mantido pela UI ou, como
fallback, do histórico recente. O LLM não decide qual métrica ou ferramenta será
usada.

Respostas de negócio não exibem códigos internos. `technicalStatus`,
`businessStatus`, `temporalStatus`, fonte, versão, validador e contrato continuam
no payload de evidências. Quando a pergunta trata diretamente de governança, o
MockProvider traduz os estados para linguagem amigável sem promover
certificação.

O bloco **Ver evidências** do embedded é recolhível e mostra período, tenant,
fonte, estados, atualização e versão da fórmula depois da resposta principal.

## Regression gate

O gate funcional usa o mesmo `createAssistantService`, orchestrator, Metric
Tools, conexão PostgreSQL `READ ONLY` e MockProvider usados em produção:

```powershell
docker run --rm --network neoretail-v9-multitenant_default `
  -v "${PWD}:/repo" `
  -w /repo/embedded-app `
  -e ANALYTICS_DB_HOST=analytics-db `
  -e ASSISTANT_METRIC_CATALOG=/repo/config/assistant_metrics.yaml `
  node:22-alpine npm run test:assistant:regression
```

O script valida semanticamente vinte perguntas canônicas, incluindo valores do
tenant 142, fontes, fórmula, versão, governança, respostas sem linhas e seis
tentativas de violação de política. O demo gate é o subconjunto obrigatório de
oito perguntas da apresentação. Ambos falham por conteúdo incorreto, e não
apenas por erro HTTP.

## Auditoria

Cada chamada registra JSON estruturado em stdout com `request_id`, usuário
pseudonimizado, tenant, pergunta redigida, intent, ferramenta, métrica, período,
filtros, mart, status, provider, modelo, latência, sucesso e código de erro.
JWTs, bearer tokens, passwords, connection strings e chaves são mascarados.

## Execução

Modo determinístico, sem Ollama:

```text
ASSISTANT_ENABLED=true
LLM_PROVIDER=mock
```

Ollama local:

```powershell
docker compose --profile assistant up -d ollama
.\bootstrap-ollama.ps1
.\bootstrap-ollama.ps1 -PullModel  # somente após autorizar o download
```

Depois use:

```text
ASSISTANT_ENABLED=true
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.1:8b
```

## Limitações desta primeira versão

- não há embeddings nem vector database;
- explicações usam catálogo estruturado;
- o frontend ainda não extrai automaticamente filtros internos do iframe;
- o histórico é curto e mantido apenas no navegador;
- não há Text-to-SQL, escrita, agente autônomo nem ações administrativas;
- aprovação de negócio continua pendente para todas as métricas;
- calendário permanece parcial enquanto as flags DAX originais não existirem;
- o assistente não expõe Distribuição, Ruptura, ISV, Cobertura, Preço Médio ou
  variações/setas como métricas consultáveis nesta versão, pois há pendências de
  dados, negócio ou contrato semântico;
- nenhum status é promovido automaticamente pelo LLM.
