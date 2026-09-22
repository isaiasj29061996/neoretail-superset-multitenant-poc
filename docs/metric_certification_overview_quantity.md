# Certificação semântica — Visão geral quantidade

## Critério

`CERTIFICADA` significa que a fórmula base foi reproduzida, seus componentes foram reconciliados entre consulta independente, mart e resultado do Superset, e RLS/filtros foram preservados. `PARCIAL` indica que a fórmula base está correta, mas falta um artefato original necessário para afirmar equivalência temporal completa. `PENDENTE` indica ausência de dados ou de definição de negócio.

A certificação usa o tenant AMBEV (`id_customer = 142`) e o snapshot mensal mais recente, `01/09/2026`.

## Resultado

| Card | Fórmula base | Períodos/LY | Tarefas | Status |
|---|---|---|---|---|
| Vendas | reconciliada com seletor real e ramo `valor` | U3M implementado; flags de calendário ausentes | n/a | PARCIAL_CALENDARIO; PENDENTE_VARIANCE_DAX |
| Perda de vendas OSA | reconciliada; U3M é soma, sem `/3` | flags de calendário ausentes | n/a | PARCIAL_CALENDARIO; PENDENTE_VARIANCE_DAX |
| Preço médio | média apenas de linhas com faturamento e fator aplicado | definição DAX específica de LY não localizada | n/a | PARCIAL_LY; PENDENTE_VARIANCE_DAX |
| Distribuição e sortimento | regra `positivacao=1` e distintos CNPJ/EAN implementada | U3M distinto implementado | n/a | PENDENTE_DADOS; PENDENTE_VARIANCE_DAX |
| % OSA | razão dos totais e `BLANK` no divisor zero | flags de calendário ausentes | crítico/risco certificados | PARCIAL_CALENDARIO; PENDENTE_VARIANCE_DAX |
| Ruptura | razão `rup/status_item_geral` reconciliada | flags de calendário ausentes | crítico/risco certificados | PARCIAL_CALENDARIO; PENDENTE_NEGOCIO; PENDENTE_VARIANCE_DAX |
| Item sem venda | razão `est_virtual/status_item_geral` reconciliada | flags de calendário ausentes | crítico/risco certificados | PARCIAL_CALENDARIO; PENDENTE_VARIANCE_DAX |
| Cobertura de estoque | razão estoque/demanda reconciliada | flags de calendário ausentes | n/a | PARCIAL_CALENDARIO; PENDENTE_VARIANCE_DAX |

Nenhum card recebe `CERTIFICADA` de ponta a ponta. As fórmulas base, exceto Distribuição, estão tecnicamente reconciliadas, mas faltam as flags originais de calendário e as medidas DAX de variação. Distribuição continua bloqueada pela ausência de `positivacao`, e Ruptura depende de decisão de negócio sobre o resultado literal acima de 100%.

## Reconciliação do mês atual

Consulta independente direta em `gold.fato_historico`, mart `gold.nr_overview_quantity_default` e consulta persistida do Superset concordaram nos componentes abaixo para `nm_measure = 'unidade'`:

| Métrica | Resultado |
|---|---:|
| Venda quantidade | 9.786.865,3950 |
| Perda OSA quantidade | 848.852,1723 |
| Preço médio | 8,7478637726 |
| % OSA | 74,1269094532% |
| Ruptura | 307,7138885378% |
| Item sem venda | 49,1520283078% |
| Cobertura de estoque | 58,1892885948 |
| Lojas positivadas | 0 |
| Itens positivados | 0 |

As diferenças numéricas entre a consulta independente e o mart ficaram restritas à ordem de soma em ponto flutuante.

Ruptura acima de 100% é o resultado literal de `SUM(rup)/SUM(status_item_geral)` neste snapshot. A implementação não limita o valor artificialmente. A fórmula está tecnicamente reconciliada, mas o resultado precisa de aceite do responsável de negócio ou confirmação de que o denominador fornecido é o correto.

## Tarefas do dia

As seis contagens vêm de `gold.calculo_oportunidades`, sem `DISTINCT`, e foram publicadas somente no último mês:

| Tarefa | Críticos | Risco |
|---|---:|---:|
| OSA | 3.866 | 3.279 |
| Ruptura | 610 | 910 |
| Item sem venda | 188 | 267 |

`superset/validate_overview_quantity.py` compara todos os componentes retornados pelos oito charts com o mart e falha em qualquer divergência.

## Pendência de distribuição

No tenant 142, as 2.977.167 linhas de `gold.fato_historico` têm `positivacao` nula. As colunas factuais `cnpj` e `ean` também estão nulas, embora as dimensões possuam identificadores parcialmente utilizáveis:

- `dim_local`: 5.252 CNPJs não nulos em 5.605 locais; 4.299 distintos;
- `dim_itens`: 58.488 itens com `cd_ean`; 1.971 EANs distintos;
- cobertura do join na fato: 1.947.713 linhas com CNPJ de dimensão e 2.971.507 com EAN de dimensão.

A ausência de `positivacao` impede aplicar o filtro DAX. O card foi mantido, retorna zero de forma rastreável e mostra `PENDENTE_DADOS`; IDs de local/item não foram usados como substitutos. Para certificar, a carga precisa publicar `positivacao` com semântica aprovada.

## Calendário, LY e variações

A busca nos arquivos versionados não encontrou as flags originais de calendário M0, M-1, U3M e LY, nem as expressões DAX das variações e da versão LY de Preço médio. A implementação usa deslocamentos mensais sobre o maior mês disponível, mas mantém esses períodos como `PARCIAL`.

As setas foram desativadas nos oito cards (`quantitycompareplain`) e permanecem `PENDENTE_VARIANCE_DAX`. Elas só devem voltar após incorporar as fórmulas originais e casos esperados.

O validador também reconcilia, para cada card aplicável, os seis valores finais produzidos pelo contrato atual de deslocamento mensal: MTD, M-1, U3M, MTD LY, M-1 LY e U3M LY. Essa evidência comprova a implementação atual; não substitui as flags DAX originais e mantém `PARCIAL_CALENDARIO`. Preço médio LY permanece `BLANK`, pois sua definição DAX original não foi localizada.

Valores reconciliados para `unidade` no snapshot mais recente:

| Card | MTD | M-1 | U3M | MTD LY | M-1 LY | U3M LY |
|---|---:|---:|---:|---:|---:|---:|
| Vendas | 9.786.865,3950 | 17.572.147,1240 | 21.204.207,9406 | 29.894.183,1000 | 26.812.610,8900 | 21.541.545,7633 |
| Perda OSA | 848.852,1723 | 1.737.802,7551 | 6.496.757,6314 | 1.400.194,3511 | 805.374,3435 | 3.553.383,4278 |
| Preço médio | 8,747864 | 10,174136 | 10,228150 | BLANK | BLANK | BLANK |
| Lojas positivadas | 0 | 0 | 0 | 0 | 0 | 0 |
| Itens positivados | 0 | 0 | 0 | 0 | 0 | 0 |
| % OSA | 74,126909% | 75,423182% | 72,687374% | 87,332602% | 90,207200% | 82,828654% |
| Ruptura | 307,713889% | 613,859964% | 576,527200% | 1.749,584404% | 1.110,317460% | 667,301175% |
| Item sem venda | 49,152028% | 130,404478% | 258,592530% | 1.163,511032% | 529,111327% | 692,597546% |
| Cobertura | 58,189289 | 43,016086 | 54,503127 | 39,573097 | 49,329109 | 52,733332 |

## Filtro Medida

O filtro `nm_measure` usa exclusivamente o dataset físico `gold.nr_conversion_options`. Os demais filtros continuam em `gold.nr_filter_options`. O Superset confirmou seleção única, default visual `unidade` e as sete opções reais: `hectolitro`, `libra`, `litro`, `quilograma`, `tonelada`, `unidade` e `valor`.

Cada opção foi executada pelo motor do Superset nos cards Vendas, Perda OSA e Preço médio e reconciliada com `nr_overview_quantity_default`. O ramo `valor` preserva Vendas como faturamento e mantém Perda OSA e Preço médio como `BLANK`, conforme o contrato atual.

## Semântica de BLANK

O plugin preserva `null`/`undefined` até a renderização, que apresenta `—`. Denominador zero ou ausente retorna `BLANK` para % OSA, Cobertura e demais razões. Ausência de mês e períodos LY inexistentes também permanecem `BLANK`; um zero numérico real continua sendo formatado como zero. Os testes cobrem separadamente esses casos.

## Filtros, RLS e performance

- RLS continua em `id_customer`.
- O caminho filtrado foi executado com `Rede=AKKIATACADO`, tenant 142 e medida `unidade`; retornou seis meses e usou `nr_overview_quantity_detail`.
- O caminho padrão dos oito charts usou `nr_overview_quantity_default` e retornou 27 meses por chart.
- Tempos pelo motor real do Superset após as correções: 0,1564 s a 0,3297 s por chart; soma sequencial de 1,5169 s; zero erros.
- O mart detalhado ocupa aproximadamente 1.034 MiB no snapshot local. Esse custo deve ser considerado no refresh; o caminho interativo padrão consulta somente 189 linhas compactas.
- O build de produção do Superset concluiu com sucesso.
- A suíte Python completa (45 testes), a validação estrutural e 67 verificações JavaScript passaram.

## Evidências versionadas

- `analytics-db/marts/40_overview_quantity_semantic.sql`;
- `superset/bootstrap_overview_quantity.py`;
- `superset/validate_overview_quantity.py`;
- `superset/frontend-plugin/plugin-chart-neoretail-kpi/src/transformProps.js`;
- `superset/frontend-plugin/plugin-chart-neoretail-kpi/src/NeoRetailKpiRouter.jsx`;
- `generated/performance_overview_quantity.json` (artefato local de execução).

## Decisão

A página está pronta para revisão técnica com fórmulas base reconciliadas e desempenho adequado no caminho padrão. A conclusão funcional permanece condicionada a quatro evidências externas: `positivacao` preenchida, calendário DAX original, aceite do percentual de Ruptura acima de 100% e medidas DAX originais de variação. Não se deve promover a página como semanticamente certificada de ponta a ponta antes dessas quatro resoluções.
