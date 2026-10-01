# Certificação — Panorama da Indústria — Comparativos

## Fonte de verdade auditada

O layout foi obtido do PBIP `NeoRetail Pocket RF.Report` e as fórmulas do TMDL
`NeoRetail Pocket RF.SemanticModel`. A seção original contém 15 matrizes,
controladas por cinco bookmarks:

| Aba | Medidas originais |
|---|---|
| Valor | Sell out venda Periodo; Sell out custo Periodo; Markup Periodo |
| Quantidade | Qtd venda Periodo; Qtd Perda OSA Periodo; Preço Médio Periodo |
| R$ Estoque | Estoque Custo Periodo; Estoque qtd; %ROI Periodo; GIRO Periodo |
| OSA | % OSA Periodo; % RUP Periodo; % ISV Periodo |
| Falta x Excesso | R$ TVD Periodo; R$ IVD Periodo |

Cada aba usa as mesmas três hierarquias:

- Região → UF → Cidade;
- Rede → Bandeira → Loja;
- Hierarquia 1 → Hierarquia 2 → Item.

Rastreabilidade dos objetos originais na página
`21f572604934cb3d24d6` (`Panorama 01 - panorama indústria`):

| Aba | Região | Varejo | Hierarquia |
|---|---|---|---|
| Valor | `4bc844f06e04820053b7` | `1308147b4d4d62983090` | `c1aa05ddbc9712087b21` |
| Quantidade | `16904611e55c9205baa6` | `8a66103b2b1879528bc6` | `11d5a959ee1d2c5e3983` |
| R$ Estoque | `32a8afd2642050701ce4` | `c015b8b1973bb6a710c8` | `19f30ce657a2460a5ab7` |
| OSA | `491344a02cbae5b76098` | `f66c9bfbd55126ac1202` | `c64ef22d5e976155441d` |
| Falta x Excesso | `da489a4925405958dde0` | `58bb5dd16aee20972007` | `d8b1aadcca91021ee47e` |

Bookmarks auditados: Valor `87fca45560880183bba0`, Quantidade
`11ae8a3b054893e40c80`, Estoque `4b11bd2122ca7d5badbc`, OSA
`219be7a8130c94872070` e Falta x Excesso `4f38a5f02e1a287ca344`.

Não existe Top N nesses objetos. O Superset usa limite técnico de 10.000 linhas
para não truncar Varejo, que possui 2.105 folhas no snapshot AMBEV. O período
padrão reproduz o estado do relatório: ano corrente.

## Semântica preservada

- Sell Out respeita o wrapper `Periodo`, que remove `AP_CONVERSAO`; se a soma
  de faturamento do grupo não é positiva, o resultado permanece BLANK.
- Quantidade, perda OSA e preço médio usam a medida selecionada e o fator de
  `dim_conversao`; `unidade` é o default, sem lista hardcoded.
- Giro mensal é a média de `GIRO > 0`.
- ROI é `(Sell Out - Custo) / Estoque Custo`, preservando o zero definido pelo
  DAX quando Sell Out ou Custo são zero.
- OSA é `1 - problemas / ativos`.
- Ruptura e ISV dividem por `STATUS_ITEM_GERAL`.
- TVD e IVD usam o último valor não BLANK dentro do contexto temporal.
- BLANK é preservado como `NULL`/`NaN` no caminho SQL/ChartData.

## Serving e Superset

Os comparativos históricos usam
`gold.nr_panorama_comparison_history_detail`. TVD/IVD usam
`gold.nr_panorama_comparison_gap_daily`, pré-agregado diariamente para as três
hierarquias. Os datasets Superset aplicam RLS, filtros nativos, período e a
agregação final exigida pelo visual.

Quando não há filtro dimensional, TVD/IVD usa o mart diário compacto. Quando há
filtro, o dataset volta ao mart físico detalhado `nr_panorama_opportunities`,
empurra o predicado antes da agregação e preserva o resultado correto. Essa
ramificação mantém a semântica dos filtros sem impor o custo detalhado ao caso
padrão.

Os 15 slices são `pivot_table_v2`. O dashboard continua com RLS por
`id_customer`; `nm_measure` usa `nr_conversion_options`.

## Análise detalhada: caminho de serving compacto

A análise detalhada usa `analytics-db/marts/44_panorama_detail_semantic.sql`.
O mart `gold.nr_panorama_detail_default` materializa uma única vez o snapshot
atual e o ROI móvel de 12 meses para Região, Rede, Categoria, Produto e Nível de
atividade. O cálculo usa `GROUPING SETS` para evitar cinco varreduras
independentes da história.

No Superset, o caminho sem filtro dimensional lê esse mart compacto. Quando há
um filtro de outra dimensão, o dataset volta para
`gold.nr_panorama_comparison_history_detail`, empurra o filtro para baixo e
recalcula as métricas no contexto filtrado. Assim o bootstrap não precisa
executar cinco consultas de 12 meses apenas para descobrir metadata, sem perder
a semântica dos filtros.

O gate `validate_panorama_details.py` reconcilia
fonte pré-joined → mart compacto → ChartData. A otimização precisa ser
reexecutada no ambiente local antes de atualizar os números de performance
documentados.

## Reconciliação executada

`superset/validate_panorama_comparisons.py` compara:

1. fatos Gold com joins dimensionais e fórmulas auditadas;
2. marts físicos de serving;
3. `ChartDataCommand` real com os parâmetros persistidos no Superset.

O gate foi aprovado para tenant 142, medida `unidade`, ano corrente:

| Escopo | Linhas históricas | Linhas TVD/IVD |
|---|---:|---:|
| Região | 543 | 541 |
| Varejo | 2.105 | 1.991 |
| Hierarquia de item | 802 | 775 |

Todas as chaves e medidas coincidiram nos três caminhos.

## Performance local do ChartData

Os 12 charts históricos ficaram entre 1,27 s e 2,81 s na rodada final. Antes do
mart diário, Falta x Excesso levou 4,71 s, 10,21 s e 21,02 s. Depois:

| Chart TVD/IVD | Antes | Depois |
|---|---:|---:|
| Região | 4,71 s | 0,40 s |
| Varejo | 10,21 s | 0,64 s |
| Hierarquia de item | 21,02 s | 0,37 s |

Os tempos são evidência local, não SLA de produção.

O probe com filtro nativo `rede=CENCOSUD` também reconciliou fonte e ChartData:
Valor/Região retornou 95 linhas em 0,05 s com cache aquecido; Falta x
Excesso/Região retornou 95 linhas em 3,67 s pelo fallback detalhado. O índice
`(id_customer, rede, data)` reduziu esse segundo caminho de 7,41 s para 3,67 s.
Esse caso filtrado continua sendo o principal candidato a novo orçamento e
benchmark com volume/concorrência de produção.

## Gates reproduzíveis

```powershell
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/validate_panorama_comparisons.py
docker run --rm -v "${PWD}:/repo" -w /repo neoretail-v9-multitenant-local-engine python -m pytest local-engine/tests/test_panorama_comparison_contracts.py -q
```

Status: **CERTIFICADO TECNICAMENTE** para o snapshot AMBEV/tenant 142. Isso não
substitui homologação visual e aceite de negócio em produção.
