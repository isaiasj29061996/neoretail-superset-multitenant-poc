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

## Filtros, RLS e performance

- RLS continua em `id_customer`.
- O caminho filtrado foi executado com `Rede=AKKIATACADO`, tenant 142 e medida `unidade`; retornou seis meses e usou `nr_overview_quantity_detail`.
- O caminho padrão dos oito charts usou `nr_overview_quantity_default` e retornou 27 meses por chart.
- Tempos pelo motor real do Superset: 0,129 s a 0,358 s por chart; soma sequencial aproximada de 1,344 s; zero erros.
- O mart detalhado ocupa aproximadamente 1.034 MiB no snapshot local. Esse custo deve ser considerado no refresh; o caminho interativo padrão consulta somente 189 linhas compactas.
- O build de produção do Superset concluiu com sucesso.
- 21 testes Python (contratos + runtime Power Query) e 56 verificações JavaScript passaram.

## Evidências versionadas

- `analytics-db/marts/40_overview_quantity_semantic.sql`;
- `superset/bootstrap_overview_quantity.py`;
- `superset/validate_overview_quantity.py`;
- `superset/frontend-plugin/plugin-chart-neoretail-kpi/src/transformProps.js`;
- `superset/frontend-plugin/plugin-chart-neoretail-kpi/src/NeoRetailKpiRouter.jsx`;
- `generated/performance_overview_quantity.json` (artefato local de execução).

## Decisão

A página está pronta para revisão técnica com fórmulas base reconciliadas e desempenho adequado no caminho padrão. A conclusão funcional permanece condicionada a quatro evidências externas: `positivacao` preenchida, calendário DAX original, aceite do percentual de Ruptura acima de 100% e medidas DAX originais de variação. Não se deve promover a página como semanticamente certificada de ponta a ponta antes dessas quatro resoluções.
