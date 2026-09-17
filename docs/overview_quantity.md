# Visão geral — Quantidade

## Referência Power BI

Página usada como referência no PBIX `NeoRetail Pocket RF(3).pbix`:

- `Visão geral - visão indústria quantidade`
- grade 4 x 2 de cards;
- filtros no topo;
- comparação `Ano atual` x `Ano anterior` com `MTD`, `Mês anterior` e `Média U3M`;
- cards de OSA, Ruptura e Item sem venda com `Tarefas do dia`;
- `Distribuição e sortimento` com Quantidade de lojas e Quantidade de itens.

### Medidas referenciadas pelos visuais

| Card | Medidas encontradas no report definition |
| --- | --- |
| Vendas | `Venda MTD`, `Venda Mes Ant`, `Venda U3M`, `Venda MTD LY`, `Venda Mes Ant LY`, `Venda U3M LY`, `Var Venda Qtd MA-U3M`, `Var Venda MA-U3M LY` |
| Perda de vendas OSA | `Perda OSA MTD`, `Perda OSA Mes Ant`, `Perda OSA U3M`, equivalentes `LY`, `Var Perda OSA MA-U3M`, `Var Perda OSA MA U3M LY` |
| Preço médio | `Preço Médio MTD`, `Preço Médio Mes Ant`, `Preço Médio U3M` e equivalentes `LY` |
| Distribuição e sortimento | `Qtd Lojas MTD`, `Qtd Lojas Mes Ant`, `Qtd Lojas U3M`, `Var Qtd loja MA-U3M`, `Qtd itens MTD`, `Qtd itens Mes Ant`, `Qtd itens U3M`, `Var Qtd item MA-U3M` |
| % OSA | `% OSA MTD`, `% OSA Mes Ant`, `% OSA U3M` e equivalentes `LY`; `Var OSA % MTD-MA`, `Var OSA % MA-U3M` e equivalentes `LY`; `Itens OSA Criticos`, `Itens OSA Risco` |
| Ruptura | `Ruptura MTD`, `Ruptura Mes Ant`, `Ruptura U3M` e equivalentes `LY`; `Var Rup MTD-MA`, `Var Rup MA-U3M` e equivalentes `LY`; `Itens Rup Criticos`, `Itens Rup Risco` |
| Item sem venda | `ISV MTD`, `ISV Mes Ant`, `ISV U3M` e equivalentes `LY`; `Var ISV MTD-MA`, `Var ISV MA-U3M` e equivalentes `LY`; `Itens ISV Criticos`, `Itens ISV Risco` |
| Cobertura de estoque | `Cobertura de estoque MTD`, `Cobertura de estoque Mes Ant`, `Cobertura de estoque U3M` e equivalentes `LY`; `Var Cobertura Estoque MTD-MA`, `Var Cobertura Estoque MA-U3M` e equivalentes `LY` |

A inspeção do report definition permite recuperar com segurança os nomes das medidas usadas pelos visuais. As expressões DAX das medidas não foram recuperadas de forma confiável nesse fluxo de extração; por isso a implementação não inventa fórmulas DAX. Ela reutiliza as fórmulas já validadas na camada Superset/Gold do projeto e mantém a política `no_unproven_business_formula`.

## Implementação Superset

Dashboard:

- título: `NeoRetail V9 — Visão geral quantidade`
- slug: `neoretail-v9-visao-geral-quantidade`
- dataset: `gold.nr_overview_history`
- bootstrap: `superset/bootstrap_overview_quantity.py`
- menu embedded: `Visão geral > Visão quantidade`

Métricas usadas na paridade atual:

- Vendas: `SUM(volume_unidades)`
- Perda de vendas OSA: `SUM(qtd_perda_osa)`
- Preço médio: `SUM(faturamento) / SUM(volume_unidades)`
- Quantidade de lojas: `COUNT(DISTINCT id_location)`
- Quantidade de itens: `COUNT(DISTINCT id_item)`
- OSA: fórmula já usada no dashboard de Visão geral
- Ruptura: fórmula já usada no Panorama
- Item sem venda: fórmula já usada no Panorama
- Cobertura de estoque: fórmula já usada no Panorama

O componente `NeoRetailKpiRouter.jsx` adiciona a variante de apresentação `quantitycompare`, que mostra Ano atual e Ano anterior no mesmo card. O Ano anterior é calculado por deslocamento mensal sobre a série retornada pelo Superset:

- MTD LY: mês atual - 12 meses;
- Mês anterior LY: mês atual - 13 meses;
- Média U3M LY: média dos meses -13, -14 e -15.

## Publicação local

Após atualizar a branch:

```powershell
.\start.ps1 -Rebuild

docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/bootstrap_overview_quantity.py
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/bootstrap_embedded.py
```

O `bootstrap_embedded.py` lê `config/tenants.yaml`; como `overview_quantity` usa `section: overview`, o portal o coloca automaticamente no dropdown de `Visão geral`, abaixo de `Indústria`.
