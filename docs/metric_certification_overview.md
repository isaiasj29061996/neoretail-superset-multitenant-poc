# Certificação semântica — Visão Geral

## Critério

Esta auditoria compara fórmula, contexto temporal, filtros fixos, granularidade, `BLANK`, conversão, contagem, dimensões e isolamento por `id_customer`. Os valores do snapshot local não são usados como referência numérica.

Status: `CERTIFICADA` (implementada e testada), `PARCIAL` (parte comprovada), `DIVERGENTE` (não reproduz o DAX) e `PENDENTE` (não implementada ou sem contrato).

## Resultado por visual

| Card | Métrica | Regra Power BI | Implementação Superset | Status | Teste / observação |
|---|---|---|---|---|---|
| TVD | base | soma `TVD_SIMPLIFICADO` na última data; exclui DEPÓSITO/CD/LOJA VIRTUAL nas duas dimensões | mart filtra ambas as dimensões; último ponto de cada Ano/Mês | CERTIFICADA | último ponto e contrato SQL testados |
| TVD | MTD | TVD em `M0` | maior mês com dado retornado | PARCIAL | falta definição da flag `M0` |
| TVD | mês anterior | TVD em `M-1` | mês anterior à âncora | PARCIAL | deslocamento testado; âncora pendente |
| TVD | U3M | `(M1 + M2 + M3) / 3` | soma três deslocamentos e divide sempre por 3 | PARCIAL | lacuna não muda denominador; âncora pendente |
| TVD | críticos | `COUNT(ID_ITEM)`, regra `CRITICO`, TVD > 0, locais excluídos | snapshot de oportunidades, uma flag por linha elegível | CERTIFICADA | 494.210 linhas = 494.210 chaves no tenant 142 |
| TVD | risco | `COUNT(ID_ITEM)`, regra `F`, TVD > 0 | snapshot de oportunidades | CERTIFICADA | referência: 2.743 no snapshot auditado |
| TVD | série | Ano > Mês, último dado | uma observação por Ano/Mês após filtros | CERTIFICADA | mês parcial e lacuna testados |
| IVD | base | soma `IVD_SIMPLIFICADO` na última data; mesmas exclusões | mart IVD específico e fechamento mensal | CERTIFICADA | contrato equivalente ao TVD |
| IVD | MTD / M-1 / U3M | períodos do TVD; denominador fixo 3 | mesma mecânica temporal | PARCIAL | falta contrato `M0…M-3` |
| IVD | críticos | `COUNT(ID_ITEM)`, regra `CRITICO`, IVD > 0 | snapshot de oportunidades | CERTIFICADA | sem `DISTINCT` |
| IVD | risco | `COUNT(ID_ITEM)`, regra `U`, IVD > 0 | corrigido de `F` para `U` | CERTIFICADA | referência: 17.598 no snapshot auditado |
| IVD | série | Ano > Mês | último ponto diário de cada mês | CERTIFICADA | teste compartilhado TVD/IVD |
| Giro | base | `AVERAGE(GIRO)` onde GIRO > 0 e unidade | `giro_sum_positive / giro_count_positive` | CERTIFICADA | componentes aditivos equivalentes |
| Giro | MTD / M-1 | medida recalculada no período | razão soma/contagem por mês | PARCIAL | fórmula testada; calendário pendente |
| Giro | U3M | média das linhas positivas no contexto U3M | soma dos numeradores / soma das contagens | PARCIAL | não usa média de médias; calendário pendente |
| Giro | barras | atividade, MTD x anterior | query agrupada usa o perfil ponderado | PARCIAL | depende da âncora M0 |
| OSA | percentual | `BLANK` se inválido; senão `1 - problemas/ativos` | perfil `one_minus_ratio` sobre componentes | CERTIFICADA | ativos=0 retorna `null` |
| OSA | MTD / M-1 / U3M | razão recalculada em cada contexto | soma problemas e ativos antes da divisão | PARCIAL | razão testada; calendário pendente |
| OSA | perda R$ | fato mensal de causa × conversão × preço médio | aproximação do fato histórico foi removida do card certificado | DIVERGENTE | requer mart próprio |
| OSA | críticos | `COUNT(ID_ITEM)` com problemas M0 e dimensão Fast Mover | aproximação por `MAX_TP_ACTIVITY_LEVEL`/distinct foi removida | DIVERGENTE | relação da dimensão não provada |
| OSA | risco | `COUNT(ID_ITEM)`, problemas M0 e `MAX_TP_ACTIVITY_LEVEL='S'` | aproximação distinta foi removida | DIVERGENTE | snapshot sem distinct pendente |
| Vendas | sell out | `SUMX` por Região; faturamento ou fallback com fator em volume e preço | fallback global sem seleção de conversão | DIVERGENTE | contrato de medida selecionada pendente |
| Vendas | custo | soma linha a linha `volume × custo` | `sales_cost_sum` | CERTIFICADA | componente aditivo equivalente |
| Vendas | quantidade | `Venda Historico` com ramo valor/unidade e conversão | soma direta de volume | DIVERGENTE | depende de AP_CONVERSAO |
| Vendas | períodos | MTD, M-1 e contexto U3M/3 | deslocamentos e denominador fixo | PARCIAL | custo correto; demais herdam divergências |
| Estoque | custo | soma `estoque_medio × avg_price_cost` | `stock_cost_sum` | CERTIFICADA | componente aditivo equivalente |
| Estoque | quantidade | última `MES_ANO`, soma estoque × conversão | soma direta sem conversão | DIVERGENTE | depende de AP_CONVERSAO |
| Estoque | períodos | MTD, M-1 e contexto U3M/3 | deslocamentos com denominador fixo | PARCIAL | custo correto; quantidade divergente |
| ROI | atual/anterior | zero se sell out ou custo=0; senão `(sellout-custo)/estoque` | ramificação incompleta e sell out divergente | DIVERGENTE | certificar sell out primeiro |
| ROI | U3M | ROI recalculado no contexto U3M | cálculo genérico por meses | DIVERGENTE | consulta semântica dedicada pendente |
| ROI | anual | soma dos ROI por AnoMês em 12 meses | ausente | PENDENTE | janela 12M própria |
| ROI | barras | atividade, atual x anterior | herda ROI divergente | DIVERGENTE | dependência da base |
| Markup | MTD / M-1 | sell out / custo com retorno 0 do DAX | ramificação incompleta e sell out divergente | DIVERGENTE | certificar sell out primeiro |
| Markup | U3M | sell out U3M / custo U3M | cálculo genérico | DIVERGENTE | razão sobre componentes pendente |
| Markup | barras | atividade, MTD x anterior | herda divergências | DIVERGENTE | dependência da base |

## Decisões implementadas

### TVD e IVD

A consulta permanece diária para que os filtros nativos sejam aplicados antes de `LASTNONBLANK`. O adaptador então mantém a última observação de cada Ano/Mês. Usar `P1M` diretamente somaria todos os snapshots diários.

O DAX fornecido certificou `REGRA_CRITICO`. Os alertas agora vêm de um snapshot independente de `calculo_oportunidades`, contam cada `ID_ITEM` não nulo e preservam dimensões, exclusões e RLS. IVD risco usa `U`.

### Giro e OSA

O plugin recebe componentes aditivos e um perfil semântico explícito. Giro agrega soma e contagem antes da divisão. OSA agrega problemas e ativos antes de `1 - problemas/ativos`. Isso substitui a antiga fórmula U3M universal.

Perda OSA e alertas OSA foram retirados do card certificado enquanto suas fontes e relações não forem implementadas de forma equivalente.

### Conversão e calendário

`dim_conversao` possui taxas por tenant, item e medida, mas a Visão Geral não publica contrato equivalente a `SELECTEDVALUE(AP_CONVERSAO[nm_measure])`. Métricas dependentes continuam divergentes; não se assume `unidade`.

O material usa `M0`, `M-1`, `M-2`, `M-3`, `U3M` e 12M, mas não define a âncora. A implementação usa o maior mês com dado. A certificação completa depende de `PENDENTE_CALENDARIO_M0`.

## Filtros, RLS e testes

Rede, Bandeira, UF, Cidade, Tipo local, Loja, Nível de atividade, Marca, H1, H2, H3 e Item permanecem publicados. Junções usam `id_customer + id_location` ou `id_customer + id_item`; `id_customer` permanece nos marts, índices, dataset e RLS.

Os testes controlados cobrem último ponto mensal, mês parcial, lacuna, denominador fixo 3, Giro ponderado, OSA por razão dos totais, OSA com denominador zero, exclusões de local, risco IVD `U`, preservação de filtros e contratos multitenant.

## Performance medida

No tenant 142, a consulta TVD detalhada de quatro meses caiu de **5.284 ms** para **3.421 ms**. O resumo sem filtro dimensional executou em **0,541 ms** no PostgreSQL local.

O refresh final de `30_neoretail_serving_marts.sql` levou **899,08 s**. A ordem de remoção dos resumos 33/35/36/37 foi corrigida e eles foram restaurados. Locks e duração continuam sendo risco operacional.

Após o build e o bootstrap, as oito consultas persistidas passaram sem erro. A execução sequencial sem cache aquecido levou **6,127 s** no total: TVD **0,336 s**, IVD **0,110 s**, Giro **1,353 s**, OSA **0,692 s**, Vendas **0,516 s**, Estoque **0,534 s**, ROI **1,235 s** e Markup **1,293 s**. No profiler com cache aquecido, o maior tempo foi TVD com **0,352 s**, seguido de IVD com **0,163 s**.

Depois da criação de `nr_overview_default_summary`, a primeira execução do novo dataset caiu para **1,530 s** no total, redução de **75,0%**. A consulta de Giro por mês e atividade caiu de **457,966 ms** para **0,303 ms** no PostgreSQL. Os 142 grupos compactos reconciliaram sem divergência; com filtro de Rede, o dataset retornou ao mart detalhado e manteve resultados.

## Arquivos alterados

- `analytics-db/marts/30_neoretail_serving_marts.sql`;
- `analytics-db/marts/31_overview_performance.sql`;
- `analytics-db/marts/37_interactive_p1_summary.sql`;
- `superset/Dockerfile`;
- `superset/bootstrap_overview.py`;
- `superset/validate_overview.py`;
- `superset/frontend-plugin/plugin-chart-neoretail-kpi/src/transformProps.js`;
- `superset/frontend-plugin/plugin-chart-neoretail-kpi/src/NeoRetailKpi.jsx`;
- `superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/regression.mjs`;
- `local-engine/tests/test_overview_metric_semantics.py`;
- este documento.

## Pendências que bloqueiam certificação total

1. definição das flags e janelas do calendário;
2. contrato do seletor AP_CONVERSAO no Superset;
3. mart de Perda OSA baseado no fato mensal de causas;
4. relação certificada de DIM_NIVEL_ATIVIDADE para OSA crítico;
5. `SUMX` regional de sell out com conversão;
6. consultas de ROI e Markup, incluindo ROI anual 12M.

Enquanto esses itens estiverem abertos, a resposta para “todos os componentes usam a mesma regra do Power BI?” é **não**. TVD, IVD, Giro, OSA percentual, Venda Custo e Estoque Custo têm contratos implementados; os demais estão classificados acima.
