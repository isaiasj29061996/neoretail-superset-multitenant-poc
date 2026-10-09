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

O DAX é assimétrico e essa assimetria precisa ser preservada literalmente:

- **Estoque Preço Custo MTD** = custo em M0.
- **Estoque Preço Custo U3M** = custo no contexto U3M dividido por 3. Como a medida base de custo soma as linhas, isso equivale à média dos três meses.
- **Estoque Quantidade MTD** = `[Estoque qtd]` no contexto MTD.
- **Estoque Quantidade U3M** = `CALCULATE([Estoque qtd], U3M=TRUE) / 3`.

A última regra não é uma média comum. A medida `[Estoque qtd]` calcula
`MaxDataMes` dentro do contexto recebido e mantém somente esse mês. Logo, no
contexto U3M ela retorna o estoque do mês máximo do U3M e só depois o BN divide
esse valor por 3.

O plugin já possui o perfil `stock_bundle`, que reproduz exatamente essa regra:
o índice 0 agrega os três meses e divide por 3; o índice 1 usa o último mês do
U3M e divide por 3.

## Implementação Superset

Foram criados dois datasets virtuais dedicados:

- `nr_panorama_inventory_monthly_interactive`
- `nr_panorama_inventory_weekly_card_interactive`

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

## Arquitetura de serving

A implementação final usa marts físicos dedicados para o bloco de inventário. O caminho sem filtros é `gold.nr_panorama_inventory_monthly_default` / `gold.nr_panorama_inventory_weekly_card_default`. Com filtros dimensionais, o mensal usa `gold.fato_historico` com suas dimensões; o card semanal usa `gold.nr_panorama_inventory_weekly_detail` para a timeline e `gold.nr_panorama_comparison_history_detail` para o resumo mensal. Esta última fonte já contém as dimensões e `status_item_geral`, denominador certificado de Ruptura/ISV. Os filtros são aplicados antes das agregações, preservando as mesmas fórmulas e `id_customer`.

O gate `superset/validate_panorama_inventory_filters.py` reconcilia Estoque, Giro x ROI e OSA com as fatos de origem, incluindo resumos mensais dos cards semanais, filtros de UF/item (IN e NOT IN) e conversão em unidade e uma medida alternativa. Também verifica RLS guest nos oito charts de estoque com uma regra de tenant conflitante e confirma sua presença no SQL executado. O BLANK de Giro na última semana é normalizado de NaN para nulo somente no validador.

## Status

- Fórmula de Estoque Preço Custo mensal: **CERTIFICADA NO CÓDIGO**
- Fórmula de Estoque Preço Custo semanal: **CERTIFICADA NO CÓDIGO**
- Conversão de Estoque Quantidade mensal: **CERTIFICADA NO CÓDIGO**
- Conversão de Estoque Quantidade semanal: **CERTIFICADA NO CÓDIGO**
- MTD/U3M: **CERTIFICADO NO CONTRATO DO PLUGIN**, incluindo a assimetria literal de `Estoque qtd`
- Card único mensal/semanal: **IMPLEMENTADO**
- Reconciliação com o PostgreSQL/Superset local: **VALIDADA EM TRANSAÇÃO DE TESTE** em 05/10/2026 para o tenant 142, unidade e hectolitro; 36 cenários com filtros de UF/item e oito checks de RLS guest aprovados.
- Aplicação persistente e inspeção visual: **PENDENTES**. O ambiente Docker encontrado aponta para outra worktree; os arquivos atuais foram copiados para diretórios temporários e o bootstrap incremental de estoque foi validado com rollback, reutilizando os metadados dos demais datasets. Nenhum rebuild integral foi certificado nesta auditoria.
