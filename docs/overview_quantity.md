# Visão geral — Quantidade

A página `NeoRetail V9 — Visão geral quantidade` usa o slug `neoretail-v9-visao-geral-quantidade` e contém oito cards. A implementação publicada é criada por `superset/bootstrap_overview_quantity.py` sobre o dataset virtual `gold.nr_overview_quantity_interactive`.

## Serving

O caminho padrão consulta `gold.nr_overview_quantity_default`, no grão `id_customer + mês + nm_measure`. O mart armazena componentes aditivos para que percentuais e médias sejam recalculados no contexto MTD/U3M/LY. Quando um filtro de Rede, Bandeira, UF, Cidade, Tipo de local, Loja, Região, atividade, Marca, hierarquia ou Item está ativo, o dataset troca para `gold.nr_overview_quantity_detail`, empurra o filtro para a base e refaz as agregações.

O filtro `Medida` é de seleção única e inicia em `unidade`. Vendas usa faturamento quando a medida é `valor`; nas demais opções usa volume multiplicado por `MAX(conversion_rate)`. Junções de conversão e dimensões incluem `id_customer`.

## Contratos dos cards

| Card | Regra publicada |
|---|---|
| Vendas | `valor → SUM(faturamento)`; demais medidas → `SUM(volume) × MAX(fator)`; U3M divide a soma por 3 |
| Perda de vendas OSA | `SUM(qtd_perda_osa) × MAX(fator)`; U3M mantém a soma |
| Preço médio | `AVG(avg_sales_price)` somente onde `faturamento > 0`, multiplicada pelo fator; U3M recalcula soma/contagem |
| Distribuição e sortimento | `DISTINCTCOUNT(CNPJ/EAN)` onde `positivacao = 1`; U3M usa cardinalidade distinta no intervalo, sem somar meses |
| % OSA | `1 - SUM(problemas)/SUM(ativos)`; divisor zero retorna vazio |
| Ruptura | `SUM(rup)/SUM(status_item_geral)` |
| Item sem venda | `SUM(est_virtual)/SUM(status_item_geral)` |
| Cobertura de estoque | `SUM(estoque_unidades)/SUM(demanda_media)` |

As tarefas usam `COUNT(id_item)`, sem `DISTINCT`, sobre `calculo_oportunidades`. OSA crítico usa a relação com `Fast Mover`; OSA risco usa `S`. Ruptura e Item sem venda usam `F` para crítico e `S` para risco.

As setas de variação estão ocultas nesta página porque as medidas DAX de variância não foram encontradas. Exibir uma comparação genérica como se fosse a fórmula original criaria uma regra de negócio sem evidência.

## Publicação e validação

```powershell
# marts
Get-Content -Raw analytics-db/marts/40_overview_quantity_semantic.sql |
  docker compose exec -T analytics-db psql -U analytics -d analytics -v ON_ERROR_STOP=1

# objetos Superset
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/bootstrap_overview_quantity.py

# reconciliação e desempenho
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/validate_overview_quantity.py
docker compose exec -T superset env PROFILE_DASHBOARD_SLUG=neoretail-v9-visao-geral-quantidade \
  /app/.venv/bin/python /app/pythonpath/profile_dashboard_performance.py
```

A classificação de cada métrica, as evidências numéricas e as pendências estão em `docs/metric_certification_overview_quantity.md`.
