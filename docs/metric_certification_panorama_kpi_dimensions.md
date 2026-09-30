# Panorama Indústria — Comparativo de KPIs por dimensão

## Escopo

Esta entrega adiciona três gráficos horizontais ao **Panorama Indústria**, entre
o Evolutivo de Estoque e as 15 matrizes comparativas existentes:

- Região: `regiao → uf → cidade`;
- Varejo: `rede → bandeira → loja`;
- Hierarquia de item: `hierarquia_1 → descricao_marca → item`.

Os três gráficos compartilham o seletor **Visualização por**, o filtro de ano,
o filtro de medida e os filtros dimensionais compatíveis. `id_customer` continua
protegido por RLS e também está presente em ambos os marts físicos novos.

Esta seção não usa `AP_KPI_MERCADO` nem `FATO_MERCADO`.

## Evidência PBIP e diferença de versão

O pacote PBIP disponível no repositório contém as medidas individuais que
fundamentam o contrato abaixo, mas é uma versão anterior: ele não contém a
tabela dinâmica `AP_KPI_INDUSTRIA` nem o binding dos três visuais mostrados nas
capturas mais recentes. A ordem do seletor foi fornecida como contrato da tela
atual. As fórmulas foram reconstruídas somente a partir das medidas DAX
individuais encontradas no modelo, sem substituir indicadores de mercado por
indicadores históricos.

## Contrato do seletor AP_KPI_INDUSTRIA

| Ordem | Opção | Medida/cálculo confirmado | Formato |
|---:|---|---|---|
| 1 | Venda R$ | `Sell out venda Periodo`: `SUM(faturamento)`; quando a soma não é positiva, fallback `(SUM(volume) × fator) × (AVERAGE(avg_sales_price) × fator)` | moeda |
| 2 | Estoque qtd | estoque da última `MES_ANO` no contexto × fator de conversão | quantidade |
| 3 | %OSA | `100 × (1 - SUM(qtd_problemas_osa) / SUM(qtd_item_ativo_osa))` | percentual |
| 4 | %Ruptura | `100 × SUM(rup) / SUM(status_item_geral)` | percentual |
| 5 | %Item sem Venda | `100 × SUM(est_virtual) / SUM(status_item_geral)` | percentual |
| 6 | Cobertura de estoque | `SUM(estoque_unidades) / SUM(demanda_media)` | número |
| 7 | Giro de estoque | `AVERAGE(giro)` onde `giro > 0`, em unidade | número |
| 8 | %ROI | zero quando sell-out ou custo de venda é zero; caso contrário `100 × (sell-out - custo de venda) / custo de estoque` | percentual |
| 9 | TVD - Pré-Ruptura | `SUM(tvd_simplificado)` na última data não vazia do contexto | moeda |
| 10 | IVD - Excesso de estoque | `SUM(ivd_simplificado)` na última data não vazia do contexto | moeda |

Divisores nulos ou iguais a zero continuam produzindo `BLANK`; o frontend não
converte `null` em zero. Ruptura permanece literal, inclusive acima de 100%, em
conformidade com o DAX existente.

## Serving e filtros

O caminho padrão usa:

- `gold.nr_panorama_kpi_dimension_history_default`, com 9.958 linhas;
- `gold.nr_panorama_kpi_dimension_gap_default`, com 3.720 linhas.

Os marts armazenam ano, tenant, escopo, nível de drill e caminho hierárquico.
Quando um filtro de rede, loja, localização, atividade ou produto está ativo, o
dataset troca para `gold.nr_panorama_comparison_history_detail` ou
`gold.nr_panorama_opportunities` e aplica o predicado antes da agregação. Para
`Estoque qtd`, medidas diferentes de `unidade` também usam o caminho detalhado
para preservar o fator real de `gold.dim_conversao`.

Essa separação mantém a abertura padrão rápida sem pré-agregar filtros que o
usuário ainda precisa aplicar.

## Reconciliação executada

O gate `superset/validate_panorama_kpi_dimensions.py` comparou, para o tenant
AMBEV (`id_customer = 142`) e ano 2026:

1. `gold.fato_historico` e `gold.fato_ivd_tvd`, com joins independentes às
   dimensões;
2. os dois marts compactos;
3. a resposta real do `ChartDataCommand` do Superset.

Foram reconciliadas as dez opções nas três dimensões, totalizando 30 caminhos
de ChartData. As quantidades no primeiro nível foram:

| Dimensão | Histórico | TVD/IVD |
|---|---:|---:|
| Região | 7 | 7 |
| Varejo | 36 | 34 |
| Hierarquia de item | 5 | 5 |

Um teste adicional aplicou `rede = CENCOSUD` ao gráfico de Região e confirmou
que o fallback filtrado corresponde à fonte bruta.

## Performance observada

Antes do mart compacto, a abertura padrão consumia:

- Região: 7,671 s;
- Varejo: 8,424 s;
- Hierarquia de item: 9,938 s.

Depois da materialização, a rodada completa das dez opções registrou:

- Região: 250–445 ms;
- Varejo: 219–321 ms;
- Hierarquia de item: 190–388 ms.

O fallback com filtro de rede levou 1,525 s. Esses números são evidência do
ambiente local e não representam SLA de produção.

## Estado

O contrato técnico está reconciliado para a versão de dados AMBEV avaliada. A
homologação de negócio das medidas continua sendo uma atividade separada. A
implementação preserva as 15 matrizes comparativas, a Análise detalhada e os
marts anteriores.

