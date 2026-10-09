# Panorama Indústria — Comparativo de KPIs por dimensão

## Escopo

Esta entrega adiciona três gráficos horizontais ao **Panorama Indústria**, entre
o Evolutivo de Estoque e as 15 matrizes comparativas existentes:

- Região: o visual abre em `UF → Cidade` como na captura do Power BI; o mart físico preserva `regiao → uf → cidade`, sem afetar as matrizes.
- Varejo: `rede → bandeira → loja`;
- Hierarquia de item: `hierarquia_1 → descricao_marca → item`.

Os três gráficos compartilham o seletor **Visualização por**, o filtro **Ano**,
o filtro **Mês** (em cascata com Ano), o filtro de medida e os filtros
dimensionais compatíveis. O filtro Mês apresenta opções como
`2026-01 · janeiro`; sem selecionar nenhum mês, considera todos os meses
do ano escolhido. Os controles são filtros nativos do Superset: aparecem na
barra de filtros, não fisicamente dentro do cartão como no Power BI.

`id_customer` continua protegido por RLS, está presente nos dois marts
físicos novos e agora também no dataset de opções dos seletores. Isso impede
que um filtro sem a coluna de tenant quebre a consulta sob o Guest Token.

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
Quando um filtro de rede, loja, localização, atividade, produto **ou mês**
está ativo, o dataset usa o detalhe
`gold.nr_panorama_comparison_history_detail` ou
`gold.nr_panorama_opportunities` e aplica o predicado **antes** de calcular
somas, taxas, fotografia de estoque e LASTNONBLANK. O mart padrão é anual
e não pode responder à seleção parcial de meses sem introduzir erro.
Para `Estoque qtd`, medidas diferentes de `unidade` também seguem esse
caminho detalhado, preservando `gold.dim_conversao`.

Essa separação mantém a abertura padrão rápida sem pré-agregar filtros que o
usuário ainda precisa aplicar.

## Reconciliação executada

O gate `superset/validate_panorama_kpi_dimensions.py` comparou, para o tenant
AMBEV (`id_customer = 142`) e ano 2026:

1. `gold.fato_historico` e `gold.fato_ivd_tvd`, com joins independentes às
   dimensões;
2. os dois marts compactos;
3. a resposta real do `ChartDataCommand` do Superset.

Na versão anterior à inclusão do filtro Mês e à mudança de apresentação
UF/Cidade, foram reconciliadas as dez opções nas três dimensões, totalizando
30 caminhos de ChartData. As contagens antigas no primeiro nível foram:

| Dimensão | Histórico | TVD/IVD |
|---|---:|---:|
| Região | 7 | 7 |
| Varejo | 36 | 34 |
| Hierarquia de item | 5 | 5 |

Um teste adicional da versão anterior aplicou `rede = CENCOSUD` ao gráfico
de Região e confirmou que o fallback filtrado correspondia à fonte bruta.
O gate atualizado também compara as saídas por **UF** e verifica mês selecionado
para Venda R$, OSA, estoque e TVD, além de consultar as opções de filtros
com `id_customer` explícito.

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

## Controles locais iguais à organização da referência Power BI

A versão atual inclui um **novo chart de controles** no topo da seção
`Comparativo de KPIs por dimensão`: `Ano / Mês` fica à esquerda e
`Visualização por` fica à direita, acima das três barras. As opções do
controle são consultadas pelo dataset governado
`nr_panorama_kpi_filter_options`, respeitando RLS por `id_customer`.

O frontend `KpiFilterBar.jsx` usa o mesmo estado Redux `dataMask` dos três
filtros nativos que já alimentam as consultas. Selecionar um KPI ou período
dentro da seção atualiza **simultaneamente** os três gráficos, sem criar
cálculos paralelos no navegador. Os filtros têm escopo restrito aos três charts
de KPI, e o chart de opções não recebe os próprios filtros que criaria, para
evitar que opções desapareçam ao escolher outro ano.

**Diferença ainda intencional:** o seletor visual de Ano permite um ano por
vez, com múltiplos meses dentro dele (e "Todos os meses"). O PBIX permite
combinar vários anos, mas não foi habilitado aqui porque o mart anual e a
métrica atual de chart usam `MAX(kpi_value)` ao agrupar; combinar anos sem
uma agregação matemática específica geraria valores incorretos. Essa evolução
exige uma certificação separada.

O novo toolbar é frontend do Superset, compilado na imagem `superset`;
portanto não basta apenas executar o bootstrap Python. Para usar a alteração
na worktree local:

```powershell
git pull --ff-only origin feat/panorama-stock-certification
docker run --rm -v "${PWD}:/repo" -w /repo neoretail-v9-multitenant-local-engine python -m pytest local-engine/tests/test_panorama_kpi_dimension_contracts.py -q
docker compose build superset
docker compose up -d --no-deps superset
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/bootstrap_panorama.py
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/validate_panorama_kpi_dimensions.py
```

Se `superset-init` ou outros serviços não estiverem ativos, subir o ambiente
normalmente antes dos comandos de bootstrap. **Não executar**
`docker compose down -v`, porque isso apagaria os volumes locais.

A validação frontend completa deve incluir: abrir os dois menus locais,
alterar de Venda R$ para %OSA e Estoque qtd; escolher janeiro e fevereiro;
confirmar atualização nos três gráficos; retornar a Todos os meses e verificar
a restauração do caminho anual rápido. A consulta de opções deve funcionar
também com Guest Token sob RLS (não confundir admin local com embed).

## Estado após a inclusão do ano/mês e UF/Cidade

As 30 reconciliações e os números de performance acima pertencem à rodada
**anterior** a estas alterações. Para considerar a nova versão certificada,
é obrigatório executar novamente, no Docker local:

```powershell
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/bootstrap_panorama.py
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/validate_panorama_kpi_dimensions.py
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/validate_panorama_comparisons.py
```

O filtro Mês usa o caminho detalhado; seu tempo ainda não foi medido. A
barra nativa de filtros deve estar expandida no Superset. O Embedded SDK já
a configura com `visible: true, expanded: true`. O controle hierárquico dentro da seção agora foi implementado no frontend,
com um ano de cada vez e múltiplos meses. É necessário compilar a imagem
Superset e homologar o resultado visual no ambiente local; o PBI original
continua sendo a referência de aparência.

Comparação de **valores absolutos** com as capturas depende do mesmo
`id_customer`, do mesmo conjunto de arquivos (a POC pode estar com apenas
35% da origem), da mesma seleção de meses, unidade e demais filtros. Mesmo
que o conteúdo da captura represente outra indústria, o teste de contrato
com fonte bruta do tenant 142 permanece válido.

**Status:** controles locais implementados e testes estáticos atualizados no GitHub; pendentes build frontend, validação runtime após o pull e homologação visual. As 15 matrizes,
a Análise detalhada e os marts anteriores foram preservados.

