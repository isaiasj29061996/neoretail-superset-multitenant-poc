# Inicialização local com Assistente opcional

Execute os comandos na worktree `feat/osa-industry-certification`.

```powershell
.\start.ps1
.\start.ps1 -Rebuild
```

Sem `-Assistant`, somente `docker-compose.yml` é usado e Ollama não é iniciado.
O start prepara serviços; não executa ingestão ou refresh de tenants.

Com `-Assistant`, o start adiciona `docker-compose.assistant.yml` a todas as
suas operações Compose e habilita `ASSISTANT_ENABLED=true` apenas no processo
de inicialização. O valor original é restaurado ao terminar, inclusive em erro.
O `.env` existente não é editado. O embedded é criado uma única vez usando a
configuração final, depois do bootstrap opcional de Ollama. Compose recria o
embedded se sua configuração mudou. Não há remoção de serviços órfãos.

## Mock

O provider padrão do overlay e de `.env.example` continua sendo `mock`.
Para selecionar explicitamente sem editar `.env`:

```powershell
$env:LLM_PROVIDER = 'mock'
.\start.ps1 -Assistant
```

O provider mock é determinístico, não precisa de Ollama e usa as mesmas Tools
governadas. Perguntas analíticas ainda precisam de Analytics/serving disponíveis.

## Ollama

Configure `LLM_PROVIDER=ollama` no ambiente ou no `.env` para usar o provider real.
Variáveis do ambiente têm precedência no Compose. Exemplo para esta sessão:

```powershell
$env:LLM_PROVIDER = 'ollama'
$env:LLM_TIMEOUT_MS = '180000' # validado neste notebook em CPU
.\start.ps1 -Assistant
# Primeira instalação, somente após terminar o pipeline Spark:
.\start.ps1 -Assistant -PullModel
# Reconstrução das imagens da aplicação, quando necessária:
.\start.ps1 -Rebuild -Assistant
```

Modelo padrão: `llama3.1:8b`; URL interna padrão: `http://ollama:11434`.
`OLLAMA_MODEL` é resolvido pelo Compose, incluindo `.env`, e a correspondência
com os nomes retornados por `ollama list` é exata. Modelos com sufixos diferentes
não contam como instalados. O volume existente `ollama-data` é reutilizado.

Sem `-PullModel`, modelo ausente retorna `MODEL_NOT_FOUND` e o portal continua
disponível, com Assistente `degraded`. Com `-PullModel`, o fluxo existente
`ollama-model-init` roda apenas se o modelo estiver ausente, e a disponibilidade
é consultada novamente depois do download. `-PullModel` sem `-Assistant`, ou com
provider mock, falha antes de subir serviços.

O bootstrap espera health de Ollama com o timeout configurado. Falha de
disponibilidade é reportada como `OLLAMA_UNAVAILABLE`. O Assistente não é uma
dependência de Bronze, Silver, Gold, serving ou Superset.

## Ordem e recursos

Preflight → Compose/build opcional → metadata/Analytics/Redis → Superset init →
Superset/local-engine healthy → Ollama/modelo opcionais → embedded → health geral
→ health do Assistente → `docker stats --no-stream` e `docker system df`.

Antes de iniciar Ollama, o bootstrap procura processos Spark no local-engine.
Se encontrar Spark, falha com `SPARK_ACTIVE` antes de iniciar Ollama. Falha na
verificação também impede esse início. Isso é uma verificação pontual: não inicie
outro pipeline simultaneamente nem mantenha o modelo carregado durante uma carga
pesada. Inicie o Assistente somente após os gates Lactalis estarem aprovados.

## Health e tenant

`GET http://localhost:3000/api/assistant/health` deve retornar `status=ok`,
`enabled=true`, `available=true`, `provider=ollama` e o modelo configurado.
Modelo ausente ou Ollama inacessível retornam HTTP 503, `status=degraded` e
`errorCode=MODEL_NOT_FOUND` ou `OLLAMA_UNAVAILABLE`, respectivamente. O start lê
esse JSON dentro do embedded, incluindo respostas 503, e mostra o erro.

O tenant continua vindo da sessão NeoRetail. Não houve alterações em autorização,
SQL, fórmulas, catálogo ou semântica. O rebuild deve habilitar somente LACTALIS,
`id_customer=290`. O registro de clientes e a sessão local habilitam somente
LACTALIS. Nunca use o refresh multitenant padrão para essa carga. O rebuild
concluído e os comandos explícitos por cliente estão em
[reconstrução LACTALIS](lactalis_rebuild_report.md).

## Verificação

```powershell
python scripts/test_assistant_startup.py
# Com Node e dependências disponíveis, na pasta embedded-app:
npm run build
npm run test:assistant
```

Os testes de startup usam Docker simulado e verificam modos normal/rebuild,
overlay mock, autorização do pull, ausência de download automático, ordem,
degradação, bloqueio por Spark e preservação de `.env`/ambiente. O teste HTTP
Lactalis usa sessão 290 e resultados de Tool sintéticos: confirma parâmetros SQL
290 e recusa de overrides para 142/17066/609, sem carregar dados desses tenants.

`assistant/smoke.mjs`, `assistant/api-smoke.mjs` e `assistant/demo-regression.mjs`
dependem do portal/banco reconstruídos. Rode-os somente após habilitar usuário
Lactalis, validar a sessão 290 e reconstruir os marts. Esses smokes reais, inclusive
Ollama, não são substituídos pelos testes sintéticos.
