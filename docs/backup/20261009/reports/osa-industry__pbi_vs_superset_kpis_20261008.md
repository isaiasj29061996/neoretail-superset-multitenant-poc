> Cópia para GitHub: números de origem e identificadores numéricos omitidos. Original integral exige backup externo. Não usar esta cópia como fixture ou SQL executável.

# Fotografia dos KPIs — LACTALIS — [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO]

Nenhuma correção, refresh, commit ou push foi executado nesta auditoria. Apenas evidências locais ignoradas pelo Git foram criadas. Valores PBI não foram estimados.

## Referência e limites

ZIP: `C:\Users\ijusto\Downloads\NeoRetail Pocket RF.Report.zip`, [DADO OMITIDO] bytes, modificado em [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] às [DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO] (horário local). Projeto completo confirmado (.pbip, .Report, .SemanticModel). Extração em `generated/pbi_lactalis_reference_2[DADO OMITIDO]/`.
Power BI Desktop e msmdsrv não detectados nas consultas realizadas antes e depois do reinício. Porta local: indisponível. Não foi aberto, fechado, reiniciado ou atualizado nenhum modelo. Cache do modelo no ZIP não foi executado nem tratado como resultados DAX.
Tenant: LACTALIS confirmado pelo parâmetro `_nomeCliente` do PBIP; [DADO OMITIDO] confirmado no catálogo Superset e nas consultas PostgreSQL. O ID numérico dentro do modelo importado não pôde ser confirmado em sessão viva.
Página: **Visão geral [DADO OMITIDO] - visão indústria** (`b4da2[DADO OMITIDO]ee4[DADO OMITIDO]`). Inventário: [DADO OMITIDO] páginas, [DADO OMITIDO] tabelas, [DADO OMITIDO] medidas e [DADO OMITIDO] bookmarks. Definições completas de páginas, visuais, medidas, Power Query, relacionamentos, calendário, conversões e parâmetros estão no JSON de inventário.
ROI tem mês anterior, U3M e anual no cartão PBI; ROI MTD não está projetado nesse cartão. São [DADO OMITIDO] pares KPI/período presentes, mais ROI MTD do Superset registrado separadamente.

## Contexto comprovado

PBI salvo: AP_CONVERSAO[nm_measure] exclui `valor`; DIM_LOCAL[Rede] exclui nulo; DIM_CATALOGO_LOCAL[Status Contratado] = `Contratado`. Slicer de conversão salva `unidade`. Slicers presentes: hierarquia [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO], marca, UF, item, nível de atividade, tipo local/loja e rede/bandeira. Ausência de seleção explícita nos demais slicers não comprova ausência de filtro na sessão.
Filtros completos de relatório/página/visual, objetos dos slicers, interações DataFilter/NoFilter e [DADO OMITIDO] bookmarks estão no inventário. Bookmark ativo e seleções transitórias: UNKNOWN. Região, local e produto da sessão viva: UNKNOWN. Períodos seguem DAX M0/M-[DADO OMITIDO]/U3M e o calendário do modelo; âncora numérica do calendário importado indisponível.
Superset consultado: dashboard salvo `neoretail-v9-visao-geral-industria`, filtro explícito id_customer=[DADO OMITIDO], conversão padrão `unidade`, filtros SQL persistidos em cada chart. Seleções transitórias de um navegador não foram comprovadas. O contexto PBI de contratado/rede não nula não foi presumido equivalente ao contexto Superset.

## Datas

Power BI: último movimento UNKNOWN. Azure: [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] no snapshot de fonte coletado anteriormente em `refresh_2[DADO OMITIDO]_azure.json`; não é uma nova consulta Azure desta auditoria. Gold PostgreSQL: [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO], confirmado agora. TVD/IVD serving: [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO]. Competências mensais são datas de início do mês, não o dia do último movimento.

## Comparação

N/D significa valor PBI não comprovado. Diferença numérica e tolerância de arredondamento só podem ser aplicadas quando os dois valores brutos existem. Percentuais Superset abaixo estão em pontos percentuais; DAX percentual costuma usar fração, cuja unidade deve ser confirmada pela expressão e formato.

| KPI | Período | Power BI | Superset bruto | Diferença | PBI measure | Superset source | Data PBI | Data Superset da consulta | Status |
|---|---|---:|---:|---:|---|---|---|---|---|
| MARKUP | MTD | N/D | [DADO OMITIDO] | N/D | MARKUP MTD | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| MARKUP | Mês anterior | N/D | [DADO OMITIDO] | N/D | MARKUP Mes Ant | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| MARKUP | Média U3M | N/D | [DADO OMITIDO] | N/D | MARKUP U3M | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Venda qtd | MTD | N/D | [DADO OMITIDO] | N/D | Venda MTD | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Venda qtd | Mês anterior | N/D | [DADO OMITIDO] | N/D | Venda Mes Ant | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Venda qtd | Média U3M | N/D | [DADO OMITIDO] | N/D | Venda U3M | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Estoque qtd | MTD | N/D | [DADO OMITIDO] | N/D | Estoque MTD | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Estoque qtd | Mês anterior | N/D | [DADO OMITIDO] | N/D | Estoque Mes Ant | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Estoque qtd | Média U3M | N/D | [DADO OMITIDO] | N/D | Estoque U3M | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Giro | MTD | N/D | [DADO OMITIDO] | N/D | Giro MTD | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Giro | Mês anterior | N/D | [DADO OMITIDO] | N/D | Giro Mes Ant | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Giro | Média U3M | N/D | [DADO OMITIDO] | N/D | Giro U3M | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Estoque custo | MTD | N/D | [DADO OMITIDO] | N/D | Estoque Custo MTD | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Estoque custo | Mês anterior | N/D | [DADO OMITIDO] | N/D | Estoque Custo Mes Ant | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Estoque custo | Média U3M | N/D | [DADO OMITIDO] | N/D | Estoque Custo U3M | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| IVD - Excesso | MTD | N/D | [DADO OMITIDO] | N/D | IVD MTD | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_ivd_daily_summary | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| IVD - Excesso | Mês anterior | N/D | [DADO OMITIDO] | N/D | IVD Mes Ant | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_ivd_daily_summary | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| IVD - Excesso | Média U3M | N/D | [DADO OMITIDO] | N/D | IVD U3M | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_ivd_daily_summary | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Venda sell out | MTD | N/D | [DADO OMITIDO] | N/D | Venda sell out MTD | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Venda sell out | Mês anterior | N/D | [DADO OMITIDO] | N/D | Venda sell out Mes Ant | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Venda sell out | Média U3M | N/D | [DADO OMITIDO] | N/D | Venda sell out U3M | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| OSA | MTD | N/D | [DADO OMITIDO] | N/D | % OSA MTD | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_osa_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| OSA | Mês anterior | N/D | [DADO OMITIDO] | N/D | % OSA Mes Ant | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_osa_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| OSA | Média U3M | N/D | [DADO OMITIDO] | N/D | % OSA U3M | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_osa_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Perda OSA | MTD | N/D | [DADO OMITIDO] | N/D | Perda OSA Valor MTD | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_osa_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Perda OSA | Mês anterior | N/D | [DADO OMITIDO] | N/D | Perda OSA Valor Mes Ant | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_osa_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Perda OSA | Média U3M | N/D | [DADO OMITIDO] | N/D | Perda OSA Valor U3M | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_osa_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| ROI | Mês anterior | N/D | [DADO OMITIDO] | N/D | ROI Mes Ant | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| ROI | Média U3M | N/D | [DADO OMITIDO] | N/D | ROI U3M | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| ROI | Anual [DADO OMITIDO]M | N/D | [DADO OMITIDO] | N/D | ROI Anual | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Venda custo | MTD | N/D | [DADO OMITIDO] | N/D | Venda Custo MTD | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Venda custo | Mês anterior | N/D | [DADO OMITIDO] | N/D | Venda Custo Mes Ant | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| Venda custo | Média U3M | N/D | [DADO OMITIDO] | N/D | Venda Custo U3M | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_overview_semantic_default | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| TVD - Pré-ruptura | MTD | N/D | [DADO OMITIDO] | N/D | TVD MTD | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_tvd_daily_summary | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| TVD - Pré-ruptura | Mês anterior | N/D | [DADO OMITIDO] | N/D | TVD Mes Ant | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_tvd_daily_summary | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |
| TVD - Pré-ruptura | Média U3M | N/D | [DADO OMITIDO] | N/D | TVD U3M | chart [DADO OMITIDO] / dataset [DADO OMITIDO] / gold.nr_tvd_daily_summary | UNKNOWN | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (âncora [DADO OMITIDO][DADO OMITIDO]) | NO_PBI_VALUE |

## Mapping e valores por camada

O mapping liga a medida do cartão ao cartão homólogo no Superset; não certifica igualdade semântica ou de filtros. SQL virtual integral, SQL executado, componentes ChartData, SELECT direto reproduzido e definição física dos marts estão em `superset_kpi_values_2[DADO OMITIDO].json`. Cada fonte SQL executada é o mart indicado; o dataset aplica os filtros e agrega esses componentes; o frontend calcula os indicadores acima. Os indicadores não foram capturados visualmente no navegador.

| Chart | Dataset | Mart executado | Dependências diretas verificadas | MAX(data) mart | Última data retornada no contexto do chart |
|---|---|---|---|---|---|
| [DADO OMITIDO] TVD - Pré-ruptura | [DADO OMITIDO] nr_tvd_daily_interactive | gold.nr_tvd_daily_summary | nr_tvd_daily | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] |
| [DADO OMITIDO] IVD - Excesso | [DADO OMITIDO] nr_ivd_daily_interactive | gold.nr_ivd_daily_summary | nr_ivd_daily | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] |
| [DADO OMITIDO] Giro | [DADO OMITIDO] nr_overview_interactive | gold.nr_overview_semantic_default | dim_conversao, nr_overview_history | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] |
| [DADO OMITIDO] OSA | [DADO OMITIDO] nr_osa_interactive | gold.nr_osa_semantic_default | calculo_oportunidades, dim_conversao, dim_nivel_atividade, fato_mensal_causa_osa, nr_overview_default_summary, nr_overview_history | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] |
| [DADO OMITIDO] Vendas | [DADO OMITIDO] nr_overview_interactive | gold.nr_overview_semantic_default | dim_conversao, nr_overview_history | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] |
| [DADO OMITIDO] Estoque | [DADO OMITIDO] nr_overview_interactive | gold.nr_overview_semantic_default | dim_conversao, nr_overview_history | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] |
| [DADO OMITIDO] ROI | [DADO OMITIDO] nr_overview_interactive | gold.nr_overview_semantic_default | dim_conversao, nr_overview_history | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] |
| [DADO OMITIDO] MARKUP | [DADO OMITIDO] nr_overview_interactive | gold.nr_overview_semantic_default | dim_conversao, nr_overview_history | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] |

Gold final sob dependências intermediárias: TVD/IVD usam o contrato de `fato_ivd_tvd`; histórico usa `fato_historico`; OSA possui dependências diretas verificadas `fato_mensal_causa_osa`, `calculo_oportunidades` e dimensões, além de history/summary. A cadeia intermediária completa não foi certificada em runtime; não foi inventada equivalência para conversões ou filtros.

## Medidas e expressões DAX

### MARKUP — MTD

Medida: `MARKUP MTD` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `[DADO OMITIDO];[DADO OMITIDO];[DADO OMITIDO]`; definições dinâmicas completas no inventário.

```dax
VAR vSellOut = [Venda sell out MTD]
			VAR vVendaCusto = [Venda Custo MTD]
			
			RETURN
			IF(
			    vSellOut = [DADO OMITIDO]
			        || vVendaCusto = [DADO OMITIDO],
			    [DADO OMITIDO],
			    CALCULATE(
			        DIVIDE(
			            vSellOut,
			            vVendaCusto
			        )
			    )
			)
```

### MARKUP — Mês anterior

Medida: `MARKUP Mes Ant` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `[DADO OMITIDO];[DADO OMITIDO];[DADO OMITIDO]`; definições dinâmicas completas no inventário.

```dax
VAR vSellOut = [Venda sell out Mes Ant]
			VAR vVendaCusto = [Venda Custo Mes Ant]
			
			RETURN
			IF(
			    vSellOut = [DADO OMITIDO]
			        || vVendaCusto = [DADO OMITIDO],
			    [DADO OMITIDO],
			    CALCULATE(
			        DIVIDE(
			            vSellOut,
			            vVendaCusto
			        )
			    )
			)
```

### MARKUP — Média U3M

Medida: `MARKUP U3M` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `[DADO OMITIDO];[DADO OMITIDO];[DADO OMITIDO]`; definições dinâmicas completas no inventário.

```dax
VAR vSellOut = [Venda sell out U3M]
			VAR vVendaCusto = [Venda Custo U3M]
			
			RETURN
			IF(
			    vSellOut = [DADO OMITIDO]
			        || vVendaCusto = [DADO OMITIDO],
			    [DADO OMITIDO],
			    CALCULATE(
			        DIVIDE(
			            vSellOut,
			            vVendaCusto
			        )
			    )
			)
```

### Venda qtd — MTD

Medida: `Venda MTD` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
calculate([Venda Historico], '[DADO OMITIDO]_0_CALENDARIO'[M0] = True)
```

### Venda qtd — Mês anterior

Medida: `Venda Mes Ant` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
calculate([Venda Historico], '[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = True)
```

### Venda qtd — Média U3M

Medida: `Venda U3M` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
divide(calculate([Venda Historico], '[DADO OMITIDO]_0_CALENDARIO'[U3M] = True),[DADO OMITIDO])
```

### Estoque qtd — MTD

Medida: `Estoque MTD` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
calculate([Estoque qtd], '[DADO OMITIDO]_0_CALENDARIO'[M0] = True)
```

### Estoque qtd — Mês anterior

Medida: `Estoque Mes Ant` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
calculate([Estoque qtd], '[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = True)
```

### Estoque qtd — Média U3M

Medida: `Estoque U3M` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
divide(calculate([Estoque qtd], '[DADO OMITIDO]_0_CALENDARIO'[U3M] = True),[DADO OMITIDO])
```

### Giro — MTD

Medida: `Giro MTD` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `[DADO OMITIDO]`; definições dinâmicas completas no inventário.

```dax
calculate([Giro estoque], '[DADO OMITIDO]_0_CALENDARIO'[M0] = True)
```

### Giro — Mês anterior

Medida: `Giro Mes Ant` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `[DADO OMITIDO]`; definições dinâmicas completas no inventário.

```dax
calculate([Giro estoque], '[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = True)
```

### Giro — Média U3M

Medida: `Giro U3M` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `[DADO OMITIDO]`; definições dinâmicas completas no inventário.

```dax
calculate([Giro estoque], '[DADO OMITIDO]_0_CALENDARIO'[U3M] = True)
```

### Estoque custo — MTD

Medida: `Estoque Custo MTD` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
calculate([Estoque Custo], '[DADO OMITIDO]_0_CALENDARIO'[M0] = True)
```

### Estoque custo — Mês anterior

Medida: `Estoque Custo Mes Ant` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
calculate([Estoque Custo], '[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = True)
```

### Estoque custo — Média U3M

Medida: `Estoque Custo U3M` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
divide(calculate([Estoque Custo], '[DADO OMITIDO]_0_CALENDARIO'[U3M] = True),[DADO OMITIDO])
```

### IVD - Excesso — MTD

Medida: `IVD MTD` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
CALCULATE(
			   [IVD],
			    '[DADO OMITIDO]_0_CALENDARIO'[M0] = TRUE())
```

### IVD - Excesso — Mês anterior

Medida: `IVD Mes Ant` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
CALCULATE(
			   [IVD],
			    '[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = TRUE())
```

### IVD - Excesso — Média U3M

Medida: `IVD U3M` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
VAR M1 =
			    CALCULATE(
			        [IVD],
			        '[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = TRUE()
			    )
			
			VAR M2 =
			    CALCULATE(
			        [IVD],
			        '[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = TRUE()
			    )
			
			VAR M3 =
			    CALCULATE(
			        [IVD],
			        '[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = TRUE()
			    )
			
			RETURN
			DIVIDE(M1 + M2 + M3, [DADO OMITIDO])
```

### Venda sell out — MTD

Medida: `Venda sell out MTD` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
calculate([Venda sell out], '[DADO OMITIDO]_0_CALENDARIO'[M0] = True)
```

### Venda sell out — Mês anterior

Medida: `Venda sell out Mes Ant` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
calculate([Venda sell out], '[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = True)
```

### Venda sell out — Média U3M

Medida: `Venda sell out U3M` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
DIVIDE(calculate([Venda sell out], '[DADO OMITIDO]_0_CALENDARIO'[U3M] = True),[DADO OMITIDO])
```

### OSA — MTD

Medida: `% OSA MTD` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `[DADO OMITIDO];[DADO OMITIDO];[DADO OMITIDO]`; definições dinâmicas completas no inventário.

```dax
calculate([% OSA Historico], '[DADO OMITIDO]_0_CALENDARIO'[M0] = True)
```

### OSA — Mês anterior

Medida: `% OSA Mes Ant` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `[DADO OMITIDO];[DADO OMITIDO];[DADO OMITIDO]`; definições dinâmicas completas no inventário.

```dax
calculate([% OSA Historico], '[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = True)
```

### OSA — Média U3M

Medida: `% OSA U3M` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `[DADO OMITIDO];[DADO OMITIDO];[DADO OMITIDO]`; definições dinâmicas completas no inventário.

```dax
calculate([% OSA Historico], '[DADO OMITIDO]_0_CALENDARIO'[U3M] = True)
```

### Perda OSA — MTD

Medida: `Perda OSA Valor MTD` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
calculate([Qtd Perda OSA Mensal], '[DADO OMITIDO]_0_CALENDARIO'[M0] = True)
```

### Perda OSA — Mês anterior

Medida: `Perda OSA Valor Mes Ant` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
calculate([Qtd Perda OSA Mensal], '[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = True)
```

### Perda OSA — Média U3M

Medida: `Perda OSA Valor U3M` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
divide(calculate([Qtd Perda OSA Mensal], '[DADO OMITIDO]_0_CALENDARIO'[U3M] = True),[DADO OMITIDO])
```

### ROI — Mês anterior

Medida: `ROI Mes Ant` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `#,[DADO OMITIDO];-#,[DADO OMITIDO];#,[DADO OMITIDO]`; definições dinâmicas completas no inventário.

```dax
calculate([ROI],'[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = True)
```

### ROI — Média U3M

Medida: `ROI U3M` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `[DADO OMITIDO];[DADO OMITIDO];[DADO OMITIDO]`; definições dinâmicas completas no inventário.

```dax
calculate([ROI],'[DADO OMITIDO]_0_CALENDARIO'[U3M] = True)
```

### ROI — Anual [DADO OMITIDO]M

Medida: `ROI Anual` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `[DADO OMITIDO];[DADO OMITIDO];[DADO OMITIDO]`; definições dinâmicas completas no inventário.

```dax
CALCULATE(
			    SUMX(
			        VALUES('[DADO OMITIDO]_0_CALENDARIO'[AnoMes]),
			        [ROI]
			    ),
			    DATESINPERIOD(
			        '[DADO OMITIDO]_0_CALENDARIO'[DATA],
			        MAX('[DADO OMITIDO]_0_CALENDARIO'[DATA]),
			        [DADO OMITIDO],
			        MONTH
			    ),
			    REMOVEFILTERS('[DADO OMITIDO]_0_DIM_PERIODO')
			)
```

### Venda custo — MTD

Medida: `Venda Custo MTD` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
calculate([Venda Custo], all(AP_CONVERSAO[nm_measure]),'[DADO OMITIDO]_0_CALENDARIO'[M0] = True)
```

### Venda custo — Mês anterior

Medida: `Venda Custo Mes Ant` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
calculate([Venda Custo], all(AP_CONVERSAO[nm_measure]),'[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = True)
```

### Venda custo — Média U3M

Medida: `Venda Custo U3M` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
divide(calculate([Venda Custo], all(AP_CONVERSAO[nm_measure]), '[DADO OMITIDO]_0_CALENDARIO'[U3M] = True),[DADO OMITIDO])
```

### TVD - Pré-ruptura — MTD

Medida: `TVD MTD` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
CALCULATE(
			   [TVD],
			    '[DADO OMITIDO]_0_CALENDARIO'[M0] = TRUE())
```

### TVD - Pré-ruptura — Mês anterior

Medida: `TVD Mes Ant` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
CALCULATE(
			   [TVD],
			    '[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = TRUE())
```

### TVD - Pré-ruptura — Média U3M

Medida: `TVD U3M` na tabela `_Metricas`. Bruto: N/D. Exibido: N/D. Formato estático: `None`; definições dinâmicas completas no inventário.

```dax
VAR M1 =
			    CALCULATE(
			        [TVD],
			        '[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = TRUE()
			    )
			
			VAR M2 =
			    CALCULATE(
			        [TVD],
			        '[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = TRUE()
			    )
			
			VAR M3 =
			    CALCULATE(
			        [TVD],
			        '[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = TRUE()
			    )
			
			RETURN
			DIVIDE(M1 + M2 + M3, [DADO OMITIDO])
```

## Resultado objetivo

**BATEM:** nenhum confirmado. **NÃO BATEM:** nenhum confirmado. **NÃO COMPARÁVEIS AINDA:** os [DADO OMITIDO] pares da tabela, todos NO_PBI_VALUE; filtros/âncora da sessão viva também não confirmados. Esses status não afirmam divergência numérica. ROI MTD não possui valor projetado no cartão PBI.

Nenhuma investigação de causa foi realizada. Para obter MATCH/DIFFERENT/ROUNDING_ONLY são necessários os valores PBI comprovados no contexto correspondente.

## Git final esperado e conferido

Branch `feat/osa-industry-certification`, HEAD `[DADO OMITIDO]d2f5`.

```text
?? superset/diagnose_lactalis_inventory.py
?? superset/profile_lactalis_osa_filtered.py
```

Verificacao interna Superset: os componentes ChartData e o SELECT direto do dataset bateram nos oito cartoes (tolerancia numerica [DADO OMITIDO] relativa / [DADO OMITIDO] absoluta; NaN do transporte tratado como SQL NULL). Isso nao constitui MATCH contra Power BI.

ROI MTD adicional do Superset: [DADO OMITIDO] pontos percentuais, ancora [DADO OMITIDO][DADO OMITIDO]; sem projecao equivalente no cartao PBI analisado.
