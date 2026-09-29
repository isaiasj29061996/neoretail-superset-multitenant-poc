# Certificação — Panorama da Indústria — Evolutivo de estoque / Estoque

## Escopo

Esta certificação cobre somente **Panorama da Indústria > Evolutivo de estoque > Estoque**.
Não altera Giro x ROI, OSA, Falta x Excesso, rankings ou análise detalhada.

A referência funcional é o visual Power BI fornecido e o DAX/TMDL do modelo.

## Contrato Power BI

O card possui duas saídas:

1. **Estoque Preço Custo**
2. **Estoque Quantidade**

### Estoque Preço Custo

Mensal:

```DAX
SUMX(
    FATOS_PARTICULAR_HISTORICO,
    FATOS_PARTICULAR_HISTORICO[ESTOQUE_MEDIO]
        * FATOS_PARTICULAR_HISTORICO[AVG_PRICE_COST]
)
```

Semanal:

```DAX
SUMX(
    FATOS_PARTICULAR_SEMANAL,
    FATOS_PARTICULAR_SEMANAL[ESTOQUE_MEDIO]
        * FATOS_PARTICULAR_SEMANAL[AVG_PRICE_COST]
)
```

O valor de custo não é convertido pela seleção de unidade.

### Estoque Quantidade

Mensal:

```text
SUM(ESTOQUE_UNIDADES no mês de contexto) * FatorSelecionado
```

Semanal:

```text
SUM(ESTOQUE_UNIDADES na semana de contexto) * FatorSelecionado
```

O fator segue o contrato do modelo: `MAX(DIM_CONVERSAO[conversion_rate])`
para o `nm_measure` selecionado no contexto filtrado.

### Resumo lateral

Para as duas métricas:

- MTD = valor no contexto atual.
- U3M = soma dos três meses anteriores dividida por 3.

O plugin usa:

```text
direct_average:0:1|direct_average:1:1
```

Portanto a ausência de um dos meses não altera silenciosamente o denominador
do contrato: o cálculo continua sendo dividido por 3.

## Implementação Superset

Foram criados dois datasets virtuais dedicados:

- `nr_panorama_stock_monthly_interactive`
- `nr_panorama_stock_weekly_card_interactive`

O mensal entrega custo e quantidade convertida por mês.

O semanal é um único slice visual. A query `row_scope=timeline` entrega o
TOP 13 semanal e a query `row_scope=summary` entrega o histórico mensal usado
para MTD/U3M. Assim o card continua único e o resumo não passa a usar agregação
semanal.

Os charts finais são:

- `[Panorama] Evolutivo de estoque — Estoque mensal`
- `[Panorama] Evolutivo de estoque — Estoque semanal`

Ambos usam os rótulos:

- `Estoque Preço Custo`
- `Estoque Quantidade`

com `summary_count=2` e `timeline_limit=13`.

## Conversão e filtros

`Estoque Quantidade` respeita `nm_measure`; `Estoque Preço Custo` preserva
o valor monetário original. Os filtros dimensionais são empurrados para a base
antes das agregações, e `id_customer` continua fazendo parte do dataset final
para manter o isolamento por tenant.

## Status

- Fórmula de Estoque Preço Custo mensal: **CERTIFICADA NO CÓDIGO**
- Fórmula de Estoque Preço Custo semanal: **CERTIFICADA NO CÓDIGO**
- Conversão de Estoque Quantidade mensal: **CERTIFICADA NO CÓDIGO**
- Conversão de Estoque Quantidade semanal: **CERTIFICADA NO CÓDIGO**
- MTD/U3M das duas métricas: **CERTIFICADO NO CONTRATO DO PLUGIN**
- Card único mensal/semanal: **IMPLEMENTADO**
- Reconciliação com o PostgreSQL/Superset local: **PENDENTE DE EXECUÇÃO NO AMBIENTE DOCKER**
