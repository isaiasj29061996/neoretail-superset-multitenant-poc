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

O catálogo versionado está em `config/assistant_metrics.yaml`. A baseline da
`main` ainda registra as métricas como `discovery`/`pending`; o assistente expõe
esses estados e não os promove.

Métricas iniciais:

- Vendas;
- % OSA;
- TVD;
- IVD;
- Estoque.

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

`MTD`, `M-1` e `U3M` seguem o comportamento temporal atual do plugin: último
período disponível, período imediatamente anterior e média dos três períodos
anteriores. O status continua `PARCIAL_CALENDARIO`; essas convenções não
substituem as flags DAX originais.

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
- métricas continuam com os status da baseline, sem certificação automática.
