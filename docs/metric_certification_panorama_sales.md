# Certificação semântica — Panorama / Evolutivo de vendas

## Escopo

Esta certificação cobre somente o primeiro bloco do dashboard `neoretail-v9-panorama-industria`: **Evolutivo de vendas**. Os blocos de estoque, comparativos, rankings, análise detalhada, OSA e Falta x Excesso não tiveram suas regras alteradas.

O visual possui os caminhos `Valor > Mensal`, `Valor > Semanal`, `Quantidade > Mensal` e `Quantidade > Semanal`. O tenant permanece definido por `id_customer` e protegido pelo RLS do Superset.

## Contratos implementados

| Caminho | Fonte | Componentes | Status |
|---|---|---|---|
| Valor mensal | `gold.fato_historico` / `gold.nr_overview_history` | sell out, custo e markup recomposto | `CERTIFICADA` |
| Valor semanal | `gold.fato_semanal` / `gold.nr_panorama_sales_weekly_default` | sell out com fallback original, custo e markup recomposto | `CERTIFICADA` |
| Quantidade mensal | contrato certificado `nr_overview_quantity_interactive` | venda convertida, perda OSA e preço médio | `CERTIFICADA` |
| Quantidade semanal | `gold.fato_semanal` / `gold.nr_panorama_sales_weekly_default` | venda convertida, perda OSA e preço médio | `CERTIFICADA` |

O semanal seleciona os 13 maiores valores reais de `CD_WEEK` no contexto filtrado e só depois os apresenta em ordem cronológica. Não deriva semanas do fato mensal.

## Semântica por métrica

O plugin passou a aceitar `metric_semantics` no formato `perfil:offset:quantidade`. Isso permite que um único gráfico preserve regras diferentes sem alterar os perfis usados por outros dashboards. O resumo lateral é um chart mensal próprio, reutilizado nas abas Mensal e Semanal; assim, trocar a granularidade da timeline não transforma MTD/U3M em agregações semanais.

- Valor: sell out U3M `/ 3`; custo U3M `/ 3`; markup calculado por `SUM(sell out) / SUM(custo)`.
- Quantidade: venda U3M `/ 3`; perda OSA U3M como soma; preço médio U3M por `SUM(price_numerator) / SUM(price_count)`.
- Markup igual a zero no evolutivo vira `BLANK`; o renderer omite o ponto e interrompe a linha.
- `null` continua distinto de zero.

## Conversão

O mensal reutiliza sem duplicação `quantity_semantic_sql()` e as métricas `Q` da Visão Geral Quantidade. O semanal usa `id_customer + id_item + nm_measure` e `MAX(conversion_rate)` no contexto, igual ao contrato já certificado. O filtro Medida permanece single select, com `unidade` como padrão e opções vindas de `gold.nr_conversion_options`.

## Evidência AMBEV — tenant 142

Validador: `superset/validate_panorama_sales.py`.

- Fonte → mart → resposta efetiva do Superset: reconciliados nos quatro caminhos.
- Valor mensal, U3M: sell out `100.324.242,3264`; custo `90.397.952,8058`; markup recomposto `110,9807%`.
- Quantidade mensal em `unidade`, U3M: venda `21.204.207,9406`; perda OSA `6.496.757,6314`; preço médio `10,228150`.
- Quantidade mensal em `quilograma`, U3M: venda `53.010.519,8516`; perda OSA `16.241.894,0786`; preço médio `25,570376`.
- Semanas retornadas: exatamente `2026-26` a `2026-38`, 13 períodos em ordem cronológica.
- Respostas do Superset: 27 meses nos caminhos mensais e 13 semanas nos caminhos semanais; os componentes de cada período coincidiram com o mart.
- Latência aquecida observada no gate final: timelines entre `25,97 ms` e `41,52 ms`; resumos entre `7,94 ms` e `38,48 ms`. A primeira execução fria observada chegou a `752,33 ms` no Valor mensal.

## Testes

- Python: suíte `local-engine/tests`, incluindo contratos deste bloco.
- Plugin: 72 checks de regressão aprovados.
- Build de produção do Superset/plugin aprovado; apenas os avisos preexistentes de tamanho de bundle foram emitidos.
- Bootstrap real do Panorama aprovado.
- Novo mart criado e analisado: 630 linhas no snapshot local, 105 semanas por medida para o tenant 142.
- `git diff --check` deve permanecer limpo antes do push.

## Limitações e status temporal

Os números reproduzem o contrato de deslocamento mensal já implementado. A ausência das flags originais de calendário M0/M-1/U3M/LY continua sendo uma limitação geral; por isso a interpretação temporal fora do snapshot reconciliado permanece `PARCIAL_CALENDARIO`. Nenhuma flag foi inventada.

O caminho principal e os componentes técnicos deste visual estão `CERTIFICADA` para o snapshot AMBEV validado. Mudanças futuras de regra DAX, granularidade do fato ou calendário exigem nova execução do validador.
