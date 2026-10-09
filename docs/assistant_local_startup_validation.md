# Validação da integração de startup — 2026-10-07

Branch: feat/osa-industry-certification. Worktree: .worktrees/osa-industry.
Base: 307a129dc13994019eeabedf92ee5341579e9706. Alterações locais anteriores preservadas.

Este documento registra a etapa inicial de testes sintéticos. As pendências de
runtime nas tabelas abaixo são históricas: depois dessa etapa, o rebuild LACTALIS,
Embedded/RLS, mock e Ollama reais foram concluídos e aprovados. O registro final
está em [reconstrução LACTALIS](lactalis_rebuild_report.md), com o timeout de CPU
validado de 180 segundos. As homologações de negócio/calendário continuam pendentes.

## Arquivos desta entrega

- start.ps1: flags Assistant/PullModel, seleção explícita base/overlay, habilitação
  temporária, provider resolvido pelo Compose, bootstrap posterior ao local-engine,
  embedded na configuração final, health e auditoria de recursos. Removido
  --remove-orphans para preservar a infraestrutura opcional entre modos.
- bootstrap-ollama.ps1: health aguardado, modelo resolvido do Compose, comparação
  exata, consulta depois do pull, retorno estruturado para o start e bloqueio Spark.
- scripts/test_assistant_startup.py: testes dos scripts reais com Docker simulado.
- embedded-app/assistant/tests/lactalis-session.test.js: smoke HTTP com sessão
  Lactalis 290, Tool sintética e bloqueios de outros tenants.
- README.md e docs/assistant_local_startup.md: modos e limites documentados.
- Este relatório.

## Resultado

| Item | Resultado |
|---|---|
| Sem Assistant, com/sem Rebuild | Testado; base somente; sem iniciar Ollama |
| Assistant mock | Testado; overlay e enabled=true; sem iniciar Ollama |
| Assistant Ollama | Sequência e falhas testadas com CLI simulado |
| PullModel sem Assistant ou com mock | Reprovado antes de subir serviços, conforme contrato |
| Modelo ausente sem autorização | MODEL_NOT_FOUND; sem pull; portal pode continuar |
| Modelo já presente | Sem pull repetido |
| Modelo ausente com autorização | model-init; nova consulta confirma presença |
| Spark ativo | SPARK_ACTIVE; Ollama não iniciado |
| Sintaxe PowerShell | Aprovada pelo parser |
| Compose base/overlay | config --quiet aprovado |
| Testes startup | 7/7 aprovados |
| Testes existentes + novo smoke HTTP | 31/31 aprovados |
| Sessão Lactalis 290 no smoke | SQL com id_customer = $1 e parâmetro 290 |
| Overrides 142, 17066, 609 | HTTP 403 TENANT_OVERRIDE_FORBIDDEN; nenhuma Tool chamada |
| Prompt para todos os clientes | policy_refusal; nenhuma consulta adicional |
| Health mock no smoke | ok, enabled=true, available=true, mock, deterministic |
| Modelo configurado padrão | llama3.1:8b; provider padrão mantido mock |
| Health Ollama real | Não executado; não instalado/iniciado |
| Health Assistente no portal real | Pendente: portal/dados ainda não reconstruídos |
| Smokes DB api-smoke/demo-regression/smoke | Pendentes: requerem Analytics e usuário Lactalis reais |
| Smoke Ollama real | Pendente após dados/validators; nenhum modelo baixado |

O smoke HTTP usa sessão Express e a implementação real de routes/orquestrador/
Tools/provider mock, com resultados de consulta sintéticos. Não certifica dados,
RLS do banco ou login da aplicação completa. SQL e fórmulas de produção não foram
alterados. Nenhum tenant foi ingerido.

## Recursos

docker stats --no-stream: nenhum container em execução no fim, portanto nenhuma
medição de RAM do Assistente real. docker system df: uma imagem Node de teste,
237,9 MB; containers 0 B; volumes 0 B; build cache 0 B. Dependências npm e bundle
foram gerados na worktree para os testes, sem alterar package.json/lockfile.

Main, merges, push, PR/Draft e volumes não foram alterados. .env não foi editado.
A reconstrução Lactalis do Azure até serving/BI continua pendente e deve preceder
a ativação real de Ollama.
