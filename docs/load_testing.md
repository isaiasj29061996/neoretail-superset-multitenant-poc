# Teste local de concorrência — NeoRetail / Superset

Este teste mede o comportamento do backend analítico quando vários usuários abrem o mesmo dashboard ao mesmo tempo.

Ele executa as consultas persistidas dos charts pelo motor do Superset e mede, em paralelo, CPU/RAM dos containers `superset`, `analytics-db` e `redis`.

> O teste é de **concorrência de backend/query**. Ele não mede tempo de pintura do navegador, JavaScript do Embedded SDK ou FPS.

## Cenário padrão

A primeira bateria recomendada usa a Visão Geral da Indústria com 1, 5 e 10 usuários simultâneos.

~~~powershell
.\load-test-users.ps1 -Users 1,5,10 -Dashboard "neoretail-v9-visao-geral-industria" -ColdCache
~~~

Os resultados ficam em `generated/load-tests/`.

## Métricas

O JSON reporta tempo total, p50/p95/máximo da latência de chart, p50/p95/máximo da conclusão por usuário, taxa de erro, throughput e distribuição por chart.

O wrapper PowerShell mostra também os picos de CPU/RAM do Superset, PostgreSQL Analytics e Redis.

## Cache

`-ColdCache` limpa Redis DB 1, 2, 3 e 4 antes de cada cenário. Para um teste mais agressivo, use também `-ForceNoCache` para solicitar bypass do result cache do Superset.

## Outros cenários

~~~powershell
.\load-test-users.ps1 -Users 1,5,10 -Dashboard "neoretail-v9-panorama-industria" -ColdCache
~~~

~~~powershell
.\load-test-users.ps1 -Users 5 -Dashboard "all" -ColdCache
~~~

O cenário `all` é um stress test e não representa uma única página sendo aberta no navegador.

## Interpretação

O objetivo é verificar se, ao passar de 1 para 5 e 10 usuários, o p95 cresce de forma controlada, a taxa de erro permanece em zero, CPU/RAM ficam estáveis e nenhum chart específico domina a latência.

Não dimensione produção apenas pelo resultado local. O benchmark definitivo deve ser repetido contra o DW e a infraestrutura de produção.