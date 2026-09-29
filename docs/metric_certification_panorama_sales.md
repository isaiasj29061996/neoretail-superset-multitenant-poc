# Certificação semântica — Panorama / Evolutivo de vendas

## Escopo

Esta certificação cobre somente o primeiro bloco do dashboard `neoretail-v9-panorama-industria`: **Evolutivo de vendas**. Os blocos de estoque, comparativos, rankings, análise detalhada, OSA e Falta x Excesso não tiveram suas regras alteradas.

O visual possui os caminhos `Valor > Mensal`, `Valor > Semanal`, `Quantidade > Mensal` e `Quantidade > Semanal`. O tenant permanece definido por `id_customer` e protegido pelo RLS do Superset.

## Contratos implementados

| Caminho | Fonte | Componentes | Status |
|---|---|---|---|
| Valor mensal | `gold.fato_historico` / `gold.nr_panorama_sales_monthly_default` | sell out, custo e markup recomposto | `CERTIFICADA` |
| Valor semanal | `gold.fato_semanal` / `gold.nr_panorama_sales_weekly_default` | sell out com fallback original, custo e markup recomposto | `CERTIFICADA` |
| Quantidade mensal | contrato certificado `nr_overview_quantity_interactive` | venda convertida, perda OSA e preço médio | `CERTIFICADA` |
| Quantidade semanal | `gold.fato_semanal` / `gold.nr_panorama_sales_weekly_default` | venda convertida, perda OSA e preço médio | `CERTIFICADA` |

O semanal seleciona os 13 maiores valores reais de `CD_WEEK` no contexto filtrado e só depois os apresenta em ordem cronológica. Não deriva semanas do fato mensal.

## Semântica por métrica

O plugin passou a aceitar `metric_semantics` no formato `perfil:offset:quantidade`. Isso permite que um único gráfico preserve regras diferentes sem alterar os perfis usados por outros dashboards. O bloco agora usa um único slice Superset por combinação `Valor/Quantidade × Mensal/Semanal`. Nos caminhos semanais, esse mesmo slice executa duas queries contra o mesmo dataset: a primeira devolve o TOP 13 semanal da timeline e a segunda devolve o histórico mensal usado exclusivamente pelos indicadores MTD/U3M. Assim, o card é realmente único sem trocar a semântica mensal do resumo por uma agregação semanal.

- Valor: sell out U3M `/ 3`; custo U3M `/ 3`; markup calculado por `SUM(sell out) / SUM(custo)`.
- Quantidade: venda U3M `/ 3`; perda OSA U3M como soma; preço médio U3M por `SUM(price_numerator) / SUM(price_count)`.
- Markup igual a zero no evolutivo vira `BLANK`; o renderer omite o ponto e interrompe a linha.
- `null` continua distinto de zero.

## Falha de runtime encontrada e correção

A primeira validação visual da PR encontrou quatro sintomas reais: `metric_semantics` e `timeline_limit` não chegavam ao renderer, Quantidade expunha o quarto componente técnico, Markup não era derivado e os resumos U3M ficavam vazios.

A causa raiz foi a ausência de `metric_semantics` e `timeline_limit` no `controlPanel.js`. O Superset não os incluía no `formData` transformado, embora estivessem persistidos em `chart.params`. A correção registra os dois controles, preserva valores snake_case de `rawFormData` quando o controle transformado está vazio e dá precedência a valores camelCase explícitos. O mesmo gate cobre `summary_count`, `card_variant`, `metric_labels`, `metric_formats` e `chart_styles`.

Também foram corrigidos dois comportamentos adjacentes comprovados durante a regressão:

- `summary_count=0` agora permanece zero em vez de cair no total de indicadores;
- configurações persistidas deixam de ser concatenadas aos defaults (`bar|bar|line` não vira seis estilos).

O gate `runtime-panorama-sales.mjs` recebe os `chart.params` e as respostas reais extraídas do Superset, simula a conversão snake_case → camelCase e executa o mesmo `transformProps.js` usado pelo renderer. O resultado final foi de 62 checks aprovados: exatamente três séries nos oito charts, Preço Médio derivado, Markup derivado, U3M preenchido e limite 13 entregue ao renderer.

## Composição visual integrada

A implementação final deixou de usar dois slices lado a lado. Cada combinação do **Evolutivo de vendas** é agora um único chart `panorama`, com `summary_count=3`, renderizando os indicadores MTD/U3M na lateral esquerda e a timeline à direita dentro do mesmo componente.

- `Valor > Mensal` e `Quantidade > Mensal` usam uma única query mensal; o próprio renderer calcula MTD/U3M e desenha a timeline.
- `Valor > Semanal` e `Quantidade > Semanal` continuam sendo um único slice, mas executam duas queries no mesmo dataset: `row_scope=timeline` para o TOP 13 semanal e `row_scope=summary` para o histórico mensal do resumo.
- `buildQuery.js` adiciona a segunda query somente quando `summary_query_scope` está configurado.
- `transformProps.js` usa a query semanal apenas para o gráfico e a query mensal apenas para os indicadores, preservando o contrato DAX.
- Os antigos charts `Resumo Valor ...` e `Resumo Quantidade ...` não fazem mais parte do dashboard.
- Nenhuma fórmula de Sell Out, Custo, Markup, Quantidade, Perda OSA, Preço Médio, U3M ou TOP 13 foi alterada por essa mudança.


## Conversão

O mensal reutiliza sem duplicação `quantity_semantic_sql()` e as métricas `Q` da Visão Geral Quantidade. O semanal usa `id_customer + id_item + nm_measure` e `MAX(conversion_rate)` no contexto, igual ao contrato já certificado. O filtro Medida permanece single select, com `unidade` como padrão e opções vindas de `gold.nr_conversion_options`.

O fallback de Venda Sell Out foi corrigido para reproduzir literalmente o DAX, após a agregação:

```text
(SUM(volume) * fator)
*
(AVERAGE(avg_sales_price) * fator)
```

Ele não usa mais `SUM(volume * avg_sales_price)`. Um probe SQL controlado retornou `2.200` para a fórmula DAX e `280` para a antiga soma de produtos, comprovando que os caminhos são matematicamente diferentes.

## Evidência AMBEV — tenant 142

Validador: `superset/validate_panorama_sales.py`.

- Fonte → mart → resposta efetiva do Superset: reconciliados nos quatro caminhos.
- Valor mensal, U3M: sell out `100.324.242,3264`; custo `90.397.952,8058`; markup recomposto `110,9807%`.
- Quantidade mensal em `unidade`, U3M: venda `21.204.207,9406`; perda OSA `6.496.757,6314`; preço médio `10,228150`.
- Quantidade mensal em `quilograma`, U3M: venda `53.010.519,8516`; perda OSA `16.241.894,0786`; preço médio `25,570376`.
- Semanas retornadas: exatamente `2026-26` a `2026-38`, 13 períodos em ordem cronológica.
- Respostas do Superset: 27 meses nos caminhos mensais e 13 semanas nos caminhos semanais; os componentes de cada período coincidiram com o mart.
- Latência aquecida observada após a correção: timelines entre `31,96 ms` e `71,15 ms`; resumos entre `28,51 ms` e `49,07 ms`. Uma rodada posterior, com cache diferente, ficou entre `144,35 ms` e `186,88 ms` nas timelines. A primeira execução fria histórica chegou a `752,33 ms` no Valor mensal.

## Testes

- Python: 52 testes aprovados na suíte completa `local-engine/tests`.
- Plugin: 81 checks de regressão aprovados.
- Runtime real: 62 checks aprovados com `chart.params` e respostas efetivas dos oito charts.
- Build de produção do Superset/plugin aprovado; apenas os avisos preexistentes de tamanho de bundle foram emitidos.
- Bootstrap real do Panorama aprovado.
- Marts recriados e analisados: 162 linhas mensais e 630 linhas semanais no snapshot local; o tenant 142 mantém 105 semanas por medida antes do TOP 13.
- `git diff --check` deve permanecer limpo antes do push.

## Limitações e status temporal

Os números reproduzem o contrato de deslocamento mensal já implementado. A ausência das flags originais de calendário M0/M-1/U3M/LY continua sendo uma limitação geral; por isso a interpretação temporal fora do snapshot reconciliado permanece `PARCIAL_CALENDARIO`. Nenhuma flag foi inventada.

Após a correção da falha visual e a passagem do gate fonte → mart → Superset → `transformProps`, o caminho principal e os componentes técnicos deste visual voltam a ficar `CERTIFICADA` para o snapshot AMBEV validado. Mudanças futuras de regra DAX, granularidade do fato ou calendário exigem nova execução do validador.
