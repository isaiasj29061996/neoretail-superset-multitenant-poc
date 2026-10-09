# Certificação — Panorama da Indústria — Giro x ROI, OSA e Falta x Excesso

## Fonte de verdade

A definição dos visuais vem do projeto Power BI Report (`NeoRetail Pocket RF.Report`) e as fórmulas vêm do TMDL do modelo. O objetivo desta implementação é equivalência semântica: mesmos dados + mesmos filtros + mesma fórmula devem produzir o mesmo resultado. Prints antigos não são usados como critério de igualdade absoluta.

## Giro x ROI

O visual do Power BI combina:

- **Estoque Preço Custo** — coluna;
- **% ROI** — linha;
- **Giro** — linha.

Mensal:
- Giro = média de `GIRO` somente onde `GIRO > 0`, ignorando a seleção de conversão e fixando unidade.
- ROI = `(Venda Sell Out - Venda Custo) / Estoque Custo`; se Sell Out ou Venda Custo forem zero, a medida-base retorna zero.
- O wrapper do gráfico transforma ROI igual a zero em BLANK.
- O resumo mostra Estoque Custo MTD/U3M, ROI MTD/**Anual** e Giro MTD/U3M.
- ROI Anual é a soma das medidas mensais de ROI no período móvel de 12 meses.

Semanal:
- ROI usa Sell Out Semanal, Venda Custo Semanal e Estoque Custo Semanal.
- Giro usa `AVERAGE(GIRO)` sem o filtro `GIRO > 0`.
- A última `CD_WEEK` global do tenant é BLANK para Giro, exatamente como no TMDL.
- O card continua usando o histórico mensal para os números de resumo.

No plugin, as três saídas são derivadas dos componentes:

```text
direct_average:0:1 | roi:1:3 | weighted_average:4:2
```

O chart usa `summary_labels=U3M|Anual|U3M`, `metric_summary_modes=u3m|annual12|u3m` e `timeline_zero_blank_indices=1`.

## OSA

O visual possui três linhas:

- `% OSA = 1 - SUM(QTD_PROBLEMAS_OSA) / SUM(QTD_ITEM_ATIVO_OSA)`
- `% Ruptura = SUM(RUP) / SUM(STATUS_ITEM_GERAL)`
- `% ISV = SUM(EST_VIRTUAL) / SUM(STATUS_ITEM_GERAL)`

As mesmas fórmulas são usadas no mensal e semanal, mudando apenas a fato de origem.

A configuração por saída é:

```text
one_minus_ratio:0:2 | ratio_percent:2:2 | ratio_percent:4:2
```

Isso evita o erro anterior em que Ruptura e ISV podiam reutilizar o denominador de OSA.

## Falta x Excesso

A aba reproduz o seletor Power BI **TVD x IVD**:

- `TVD - Risco`
- `IVD - Excesso`

As medidas-base usam `LASTNONBLANK` e removem a influência de `AP_CONVERSAO`.

Para preservar esse comportamento, os marts certificados identificam separadamente a última data com valor de TVD e de IVD em cada mês/semana. O U3M do card é:

```text
(M-1 + M-2 + M-3) / 3
```

para as duas métricas.

## Serving marts

A certificação não deixa as regras apenas no SQL virtual do Superset. Foram criados:

- `gold.nr_panorama_inventory_weekly_detail`
- `gold.nr_panorama_inventory_monthly_default`
- `gold.nr_panorama_inventory_weekly_card_default`
- `gold.nr_panorama_gap_monthly_default`
- `gold.nr_panorama_gap_weekly_card_default`

O caminho sem filtros usa diretamente os marts materializados. Quando existem filtros dimensionais, os datasets virtuais empurram os filtros para uma base física detalhada e recompõem exatamente os mesmos componentes antes da agregação.

## Single-card Mensal/Semanal

Cada combinação é um único slice Superset.

Mensal:
- uma query;
- resumo MTD/U3M (ou Anual para ROI) e timeline no mesmo componente.

Semanal:
- `row_scope=timeline` → exatamente 13 períodos semanais;
- `row_scope=summary` → histórico mensal para o resumo;
- as duas queries pertencem ao mesmo chart.

## Charts certificados no código

- `[Panorama] Evolutivo de estoque — Giro x ROI mensal`
- `[Panorama] Evolutivo de estoque — Giro x ROI semanal`
- `[Panorama] Evolutivo de estoque — OSA mensal`
- `[Panorama] Evolutivo de estoque — OSA semanal`
- `[Panorama] Evolutivo de estoque — Falta x Excesso mensal`
- `[Panorama] Evolutivo de estoque — Falta x Excesso semanal`

## Gates

- `local-engine/tests/test_panorama_inventory_tabs_contracts.py`: trava fórmulas, labels, estilos, marts e configuração do plugin.
- `superset/validate_panorama_inventory_tabs.py`: reconcilia fonte → mart, valida TOP 13, chart.params e executa as queries reais dos seis charts.
- `superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/runtime-panorama-inventory.mjs`: valida as props finais do renderer e recompõe ROI, Giro, OSA, Ruptura e ISV.


## Status

A implementação e os gates estão versionados na branch eat/panorama-stock-certification.

O gate de runtime foi executado no Docker local para o tenant 142. Fonte, mart e ChartData concordaram nos seis charts. As séries semanais possuem exatamente 13 períodos; a série mensal de Falta x Excesso possui sete meses porque esse é todo o histórico disponível no snapshot. 	imeline_limit=13 é limite máximo visual, não uma exigência para fabricar meses ausentes.

Evidências: 24 testes Python, 81 checks JS de regressão e 68 checks sobre ChartData real aprovados. Ruptura do último mês permaneceu em 307,7138885%, literalmente conforme o DAX e sem limite artificial em 100%.
