# Certificação — Panorama OSA Indústria

## Escopo

Esta implementação cria uma página isolada para homologação:

- título: `NeoRetail V9 — OSA Indústria — Certificada`;
- slug: `neoretail-v9-osa-industria-certified`;
- tenant de validação: AMBEV (`id_customer = 142`);
- página antiga `neoretail-v9-osa-industria` preservada sem alteração.

A página reúne as duas visões existentes no Power BI, **Valor** e
**Quantidade**, com alternância **Mensal / Semanal**, perdas por motivo/causa,
seletor de período e as análises por Região, Varejo e Hierarquia de item.

## Contratos Power BI reproduzidos

### Mensal — Valor

- Sell Out: mesma lógica da medida histórica `Venda sell out`.
- Perda R$ OSA: `SUM(FATOS_MENSAL_CAUSA_OSA[VL_PERDA_OSA])`.
- % Perda: Perda R$ OSA dividida pelo faturamento; no fallback, volume × soma
  do preço médio da fato mensal OSA.
- % OSA: `1 - problemas / itens ativos` no histórico.

### Mensal — Quantidade

- Venda: volume da fato mensal OSA × fator da unidade selecionada.
- Perda OSA: quantidade perdida × fator.
- % Perda: `Perda OSA Historico / Venda histórica`.
- % OSA: mesma razão histórica da visão Valor.

### Semanal

A visão semanal usa `gold.fato_semanal` e conserva as fórmulas do modelo:

- Sell Out semanal com faturamento e fallback por volume/preço;
- perda em valor = quantidade perdida × média de custo;
- venda/perda em quantidade convertidas pela unidade;
- % OSA = `1 - problemas / ativos`;
- % perda de quantidade com a demanda ativa multiplicada por 30.

São exibidas as 13 semanas mais recentes do contexto filtrado.

## Período

Os visuais de causa e análise dimensional recebem o seletor desconectado
equivalente ao Power BI:

1. MTD
2. Mês Anterior
3. U3M
5. YTD

O estado padrão da página certificada é **Mês Anterior**, reproduzindo o estado
observado nos traces AMBEV. A opção ID 4 não foi inventada para OSA porque as
medidas OSA analisadas não possuem uma ramificação explícita para esse ID.

## VL_PERDA_OSA

A implementação anterior reconstruía perda em valor como quantidade × preço.
Isso não é equivalente ao modelo Power BI.

Para a origem particionada da AMBEV, `VL_VALUE_OSA_LOST_SALES` agora é
preservado na Silver/Gold como `vl_perda_osa`. O contrato legado também
aceita `VL_PERDA_OSA`.

A escrita PostgreSQL usada pelo serving é por nome de coluna e permite evolução
aditiva, portanto a nova coluna é adicionada à Gold sem substituir outros
tenants.

## Motivos OSA

A causa raiz diária é normalizada nos quatro grupos de negócio:

- Estoque virtual;
- Falta de Exposição;
- Falta de performance;
- Ruptura na loja.

A ordem das regras garante que **Ruptura parcial** permaneça em Falta de
Exposição, enquanto ruptura/pedido de abastecimento entra em Ruptura na loja.

## Matrizes / análises por dimensão

Os traces mais recentes usados na certificação mostram, no primeiro nível:

- Região;
- Rede;
- Hierarquia 1.

As medidas são calculadas **antes** da renderização:

- Valor: perda mensal em valor da fato OSA;
- Quantidade: perda histórica convertida;
- Qtd Problema OSA: histórico convertido;
- % OSA: razão histórica sobre o período.

Isso evita somar percentuais previamente calculados.

## Paridade visual com o Power BI

Os traces das páginas `Panorama 01 - osa0 indústria` e
`Panorama - osa indústria quantidade` foram usados também para validar o tipo
dos visuais, não apenas as consultas.

- a visão temporal principal é um `lineClusteredColumnComboChart`: Venda em
  coluna, % Perda e % OSA em linhas; Perda OSA continua disponível no resumo,
  mas não é desenhada como uma quarta série na timeline;
- Perda OSA por Motivo e por Causa são `clusteredColumnChart`, reproduzidas no
  plugin como barras/colunas verticais;
- Região, Varejo e Hierarquia de item são `pivotTable`, reproduzidas como
  `pivot_table_v2`;
- os slicers do Power BI são representados pelos filtros nativos governados do
  Superset;
- Valor e Quantidade existem como páginas separadas no Power BI. Na página
  certificada do Superset, um único seletor global Valor/Quantidade controla
  toda a tela, evitando combinações incoerentes entre timeline, causas e
  matrizes;
- Mensal/Semanal permanece como seletor interno da visão temporal.

Elementos puramente de moldura do PBIX (caixas de texto, imagens, formas e
HTML decorativo) não são reproduzidos quando não alteram a leitura analítica.
Bookmarks e botões são traduzidos em tabs e filtros do dashboard.

## RLS e filtros

Todos os datasets virtuais publicados expõem `id_customer`. O dashboard usa os
filtros governados já existentes para:

- Medida;
- Rede / Bandeira;
- UF / Cidade;
- Tipo de local / Loja;
- Nível de atividade;
- Marca;
- Hierarquias;
- Item.

O seletor de período é próprio da página OSA e não afeta as timelines
Mensal/Semanal.

## Execução local

Depois de trocar para `feat/osa-industry-certification`, o fluxo completo pode
ser executado com:

```powershell
.\run-osa-certified.ps1
```

O script:

1. executa os testes OSA;
2. recalcula a Silver 03B a partir do Bronze local;
3. executa o gate 03D;
4. republica a Gold/PostgreSQL com Step 06;
5. cria o novo dashboard;
6. habilita o embed;
7. executa o gate runtime.

Não usa `docker compose down -v` e não apaga volumes.

## Gate runtime

`superset/validate_osa_industry_certified.py`:

- falha se `gold.fato_mensal_causa_osa.vl_perda_osa` ainda não existir;
- executa todos os charts via ChartData para `id_customer=142`;
- reconcilia Mensal Valor/Quantidade com os fatos brutos;
- reconcilia Semanal Valor/Quantidade;
- reconcilia perdas MTD por motivo.

A implementação só deve substituir a página OSA antiga depois de esse gate
passar no ambiente local e da homologação visual com o Power BI.
