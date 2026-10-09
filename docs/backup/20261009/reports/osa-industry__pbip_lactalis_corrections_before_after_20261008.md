> Cópia para GitHub: números de origem e identificadores numéricos omitidos. Original integral exige backup externo. Não usar esta cópia como fixture ou SQL executável.

# LACTALIS PBIP — correções semânticas e auditoria AFTER

Escopo: worktree `.worktrees/osa-industry`, branch `feat/osa-industry-certification`, tenant [DADO OMITIDO], página PBIP `b4da2[DADO OMITIDO]ee4[DADO OMITIDO]`. O relatório BEFORE e seus artefatos foram preservados. Esta etapa não constitui certificação numérica.

## [DADO OMITIDO]. Situação inicial e resultado completo

| Classificação | BEFORE | AFTER |
|---|---:|---:|
| SEMANTIC_MATCH completo | [DADO OMITIDO] | [DADO OMITIDO] |
| SEMANTIC_DIFFERENCE | [DADO OMITIDO] | [DADO OMITIDO] |
| UNMAPPED (ROI MTD) | [DADO OMITIDO] | [DADO OMITIDO] |
| NO_PBI_VALUE | [DADO OMITIDO] | [DADO OMITIDO] |

Foram corrigidas [DADO OMITIDO] ocorrências de causas nos pares, mas nenhum par mudou para MATCH completo: C0[DADO OMITIDO] continua relevante em todos os [DADO OMITIDO] pares. Reduzir causas internas não equivale a reduzir a contagem de pares com pelo menos uma diferença. Não foi forçado PASS.

## [DADO OMITIDO]. Causas e execução por grupos

| Grupo | Correção comprovada | Contratos por etapa | Transições de pares para MATCH completo |
|---|---|---|---:|
| Calendário | C0[DADO OMITIDO]; janela anual C0[DADO OMITIDO] | [DADO OMITIDO] passaram / [DADO OMITIDO] falharam | [DADO OMITIDO] |
| Contexto | Semijoin CNPJ, rede não nula, contratado no default de histórico/causas; C0[DADO OMITIDO] parcial | [DADO OMITIDO] passaram / [DADO OMITIDO] falharam | [DADO OMITIDO] |
| Giro/ROI/Markup | C0[DADO OMITIDO]: total all; barras continuam activity | [DADO OMITIDO] passaram / [DADO OMITIDO] falharam | [DADO OMITIDO] |
| Perda OSA | C0[DADO OMITIDO]: agregados de período; C0[DADO OMITIDO]: sem propagação extra de atividade | [DADO OMITIDO] passaram / [DADO OMITIDO] falhou | [DADO OMITIDO] |
| OSA ausentes | C0[DADO OMITIDO] no OSA; componentes NULL e ausência de causas não eliminam razão | [DADO OMITIDO] passaram / [DADO OMITIDO] falharam | [DADO OMITIDO] |

Os contratos de presença de fonte são verificações estruturais; os testes JS com linhas reais exercitam comportamento. Nenhum desses testes, isoladamente, prova toda a topologia de filtros da página. A reavaliação por grupo conserva C0[DADO OMITIDO] e, portanto, zero transições completas em todas as etapas.

## [DADO OMITIDO]. Arquivos alterados

 scripts/publish_lactalis_marts.py                  | [DADO OMITIDO] +++++++++++++++++++++-
 superset/bootstrap_overview.py                     | [DADO OMITIDO] ++++++--
 .../plugin-chart-neoretail-kpi/src/buildQuery.js   | [DADO OMITIDO] +++-
 .../src/transformProps.js                          | [DADO OMITIDO] ++++++++++++++---
 superset/validate_overview.py                      | [DADO OMITIDO] ++++++-
 [DADO OMITIDO] files changed, [DADO OMITIDO] insertions(+), [DADO OMITIDO] deletions(-)

Novos arquivos de produto: `analytics-db/marts/[DADO OMITIDO]_pbip_overview_calendar.sql`, `[DADO OMITIDO]_pbip_overview_context.sql`, pacote `superset/neoretail_bootstrap/pbip_overview/` (context, semantics, presentation e init), teste Python e duas fixtures PBIP/Gold em `local-engine/tests/`, teste frontend `tests/pbip-contract.mjs`. O diff stat acima não inclui arquivos untracked. Módulos compartilhados core/filters e overview/semantics/presentation foram restaurados a HEAD.

## [DADO OMITIDO]. DAX real utilizado como contrato

### Giro estoque
```dax
CALCULATE(  
			    AVERAGE(FATOS_PARTICULAR_HISTORICO[GIRO]), FATOS_PARTICULAR_HISTORICO[GIRO] > [DADO OMITIDO],
			    ALL(AP_CONVERSAO), AP_CONVERSAO[nm_measure] = "unidade")
```

### ROI
```dax
VAR vSellOut = [Venda sell out]
			VAR vVendaCusto = [Venda Custo]
			
			RETURN
			IF(
			    vSellOut = [DADO OMITIDO]
			        || vVendaCusto = [DADO OMITIDO],
			    [DADO OMITIDO],
			    CALCULATE(
			        DIVIDE(
			            vSellOut - vVendaCusto,
			            [Estoque Custo]
			        )
			    )
			)
```

### ROI Anual
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

### MARKUP MTD
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

### Qtd Perda OSA Mensal
```dax
VAR MedidaSelecionada = SELECTEDVALUE(AP_CONVERSAO[nm_measure])
			VAR Fator =
			    CALCULATE(
			        MAX(DIM_CONVERSAO[conversion_rate]),
			        DIM_CONVERSAO[nm_measure] = MedidaSelecionada
			    )
			RETURN 
			CALCULATE(
			    SUM(FATOS_MENSAL_CAUSA_OSA[QTD_PERDA_OSA]) * Fator
			)
			*
			CALCULATE(
			    AVERAGE(FATOS_MENSAL_CAUSA_OSA[PRECO_MEDIO])
			)
```

### Perda OSA Valor U3M
```dax
divide(calculate([Qtd Perda OSA Mensal], '[DADO OMITIDO]_0_CALENDARIO'[U3M] = True),[DADO OMITIDO])
```

### % OSA Historico
```dax
VAR Problemas =
			    SUM(FATOS_PARTICULAR_HISTORICO[QTD_PROBLEMAS_OSA])
			
			VAR Ativos =
			    SUM(FATOS_PARTICULAR_HISTORICO[QTD_ITEM_ATIVO_OSA])
			
			RETURN
			IF(
			    ISBLANK(Problemas) || ISBLANK(Ativos) || Ativos = [DADO OMITIDO],
			    BLANK(),
			    [DADO OMITIDO] - DIVIDE(Problemas, Ativos)   
			)
```

### % OSA U3M
```dax
calculate([% OSA Historico], '[DADO OMITIDO]_0_CALENDARIO'[U3M] = True)
```

O anexo JSON mantém a closure DAX de cada um dos [DADO OMITIDO] pares, tabelas, relações e filtros extraídos do ZIP. Não se derivou valor PBI do DAX.

## [DADO OMITIDO]. SQL e comportamento antigos

```sql
-- Charts Giro/ROI/Markup: semantic_scope = 'activity'
-- mensal: SUM(COALESCE(qtd_problemas_osa,[DADO OMITIDO]))
-- Perda OSA: SUM(qtd_mês * fator_mês * preço_médio_mês) / [DADO OMITIDO]
-- calendário do frontend: latest = última linha retornada pelo chart
```

As definições completas antigas constam no BEFORE, `superset_kpi_values_2[DADO OMITIDO].json` e Git HEAD.

## [DADO OMITIDO]. SQL e comportamento novos

```sql
-- Total Giro/ROI/Markup: semantic_scope = 'all'
-- Somente consulta agrupada de barras: semantic_scope = 'activity'
SUM(qtd_problemas_osa), SUM(qtd_item_ativo_osa)
-- Perda OSA retorna componentes mensais:
SUM(qtd_perda_osa), SUM(preco_medio), COUNT(preco_medio), MAX(conversion_rate)
-- frontend U3M: SUM(qtd) * MAX(fator) * SUM(preço) / SUM(contagem_preço) / [DADO OMITIDO]
-- calendário: DATA_AT = data de publicação/importação local - [DADO OMITIDO] dia
```

O SQL novo completo persistido e o SQL executado estão em `superset_kpi_values_after_2[DADO OMITIDO].json`; definições reais dos marts foram lidas por pg_get_viewdef.

## [DADO OMITIDO]. Testes criados

Seis contratos Python baseados em DAX/M/relacionamentos do ZIP. Fixture adicional contém componentes reais da Gold (julho–setembro), sem INSERT, e snapshot antigo real do Giro. Dois checks JS adicionais verificam calendário sem mês corrente e OSA BLANK; a perda é comparada com a fórmula independente aplicada aos componentes reais. Os [DADO OMITIDO] checks legados do frontend mantiveram os esperados.

## [DADO OMITIDO]. Falha antes das correções

A execução da implementação HEAD anterior contra o mesmo contrato real falha: `PBIP M0 has no Giro data; do not relabel August as October: [DADO OMITIDO] != null`. Registro: `pbip_frontend_before_contract.log`. Também foram observadas seis falhas estruturais antes da produção.

## [DADO OMITIDO]. Resultado dos testes depois

Última bateria Python: **[DADO OMITIDO] passed** ([DADO OMITIDO] contratos novos + regressões de semântica/arquitetura). Frontend: **[DADO OMITIDO] regressões + [DADO OMITIDO] checks adicionais = [DADO OMITIDO]**, e comparação independente da perda U3M aprovada. O valor calculado para teste em Gold não é um valor observado no Power BI. O build webpack terminou com duas warnings e exit [DADO OMITIDO].

## [DADO OMITIDO]. Calendário PBIP versus Superset

PBIP: DateTime.LocalNow na importação; DATA_AT=[DADO OMITIDO] dia no mesmo mês. Serving: publicação local [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO], âncora [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO], [DADO OMITIDO] datas até a véspera. MTD projetado usa M0, mês anterior M1, U3M meses completos anteriores; a janela anual usa datas em vez de últimas [DADO OMITIDO] linhas. Ausência de linha M0 produz NULL, não relabel do último mês. Bootstrap transmite âncora única a todos os oito charts e domínio temporal SQL. Flags fora do escopo da página (como YTD) não foram certificadas nem implementadas como novos KPIs.

## [DADO OMITIDO]. Filtros PBIP versus Superset

O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente.

## [DADO OMITIDO]. Ponte CNPJ: o que foi reproduzido e o que falta

O default da população foi implementado como conjunto de chaves: DIM_LOCAL com Rede não nula → EXISTS catálogo com CNPJ IS NOT DISTINCT FROM → rede catálogo diferente de GPA → EXISTS retailer na dimensão local previamente filtrada a contratados. EXISTS evita multiplicar fatos por várias linhas da ponte. A Gold não possui AUX_CONTRATADO_LOCAL; o estado contratado disponível é o já aplicado pela transformação Power Query às dimensões. Isso não certifica LOOKUPVALUE/status sob dados ambíguos nem a propagação bidirecional de toda seleção. TVD/IVD não usam o novo mart.

Invariante runtime: [DADO OMITIDO] linhas de histórico, zero locais ausentes/rede nula; nenhuma duplicação de chave customer/location/item/data detectada. Não confundir essa validação default com prova da ponte inteira.

## [DADO OMITIDO]. Giro

Recorte extra F/S/U/N removido do total; AVG de GIRO positivo continua soma/contagem. Barras mantêm o recorte próprio, por consulta separada. O gate de conversão continua C1[DADO OMITIDO], logo Giro não recebeu MATCH completo.

## [DADO OMITIDO]. ROI

Recorte extra removido do total e janela anual corrigida para calendário. Fórmula/components não foram substituídos por números. ROI MTD continua UNMAPPED: a medida existe, mas não é projetada no visual PBIP analisado. Não foi criado chart novo. C0[DADO OMITIDO]/C0[DADO OMITIDO]/C0[DADO OMITIDO] permanecem conforme período; tratamento de vazio anual ainda exige análise independente.

## [DADO OMITIDO]. Markup

Recorte extra removido do total; barras preservadas. C0[DADO OMITIDO] e fatores/fallback continuam, com C0[DADO OMITIDO] especificamente em U3M.

## [DADO OMITIDO]. Perda OSA U3M

C0[DADO OMITIDO] corrigida: os componentes do período são agregados antes do produto e da divisão por três. A perda não soma mais produtos mensais no perfil opt-in. C0[DADO OMITIDO] corrigida: atividade não filtra causas por ligação extra com oportunidades. Fator default usa dimensão completa; fator sob seleção de item/hierarquia continua C0[DADO OMITIDO]. C0[DADO OMITIDO] impede certificação completa.

## [DADO OMITIDO]. OSA U3M e BLANK

Fórmula central continua `[DADO OMITIDO] - SUM(problemas)/SUM(ativos)`; U3M não ganhou divisão por três. OSA preserva NULL para problemas/ativos ausentes e ativos zero. Razão usa histórico com contexto default, e LEFT JOIN permite mantê-la quando não há causa/perda. C0[DADO OMITIDO] do OSA foi resolvida; filtros completos C0[DADO OMITIDO] permanecem.

## [DADO OMITIDO]. Marts afetados

- `nr_pbip_calendar`: [DADO OMITIDO] linhas; MAX(data) [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO]; índices: ux_nr_pbip_calendar_customer_data
- `nr_pbip_overview_history`: [DADO OMITIDO] linhas; MAX(data) [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO]; índices: ix_nr_pbip_overview_history_customer_data, ix_nr_pbip_overview_history_customer_keys
- `nr_pbip_osa_industry_causes`: [DADO OMITIDO] linhas; MAX(data) [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO]; índices: ix_nr_pbip_osa_industry_causes_customer_data, ix_nr_pbip_osa_industry_causes_customer_keys
- `nr_pbip_overview_semantic_default`: [DADO OMITIDO] linhas; MAX(data) [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO]; índices: ux_nr_pbip_overview_semantic_default_key
- `nr_pbip_osa_semantic_default`: [DADO OMITIDO] linhas; MAX(data) [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO]; índices: ux_nr_pbip_osa_semantic_default_key

Os marts antigos e seus índices foram preservados. Só cinco novos marts de serving foram materializados; nenhum Bronze/Silver/Gold base foi reprocessado. Duas tentativas de SQL4[DADO OMITIDO] falharam antes do commit e tiveram rollback; a versão corrigida passou EXPLAIN/CREATE VIEW com rollback de teste e depois publicação em [DADO OMITIDO] segundos.

## [DADO OMITIDO]. DAG e helper

```text
Gold dimensões/fatos → nr_pbip_overview_history → nr_pbip_overview_semantic_default
Gold causas/dimensões → nr_pbip_osa_industry_causes ─┐
                        nr_pbip_overview_history ─┴→ nr_pbip_osa_semantic_default
Gold dim_customer + relógio local → nr_pbip_calendar
```

O helper lê pg_rewrite/pg_depend e ordena os marts solicitados, preserva índices por REFRESH, limita refresh-only a nr_pbip_* e exige Gold [DADO OMITIDO]. Execução sem SQL explícito recusa replay destrutivo em instalação existente. Ordem comprovada testando input invertido: nr_pbip_calendar, nr_pbip_osa_industry_causes, nr_pbip_overview_history, nr_pbip_osa_semantic_default, nr_pbip_overview_semantic_default. Para refresh posterior, solicite o conjunto completo afetado: a função não acrescenta ancestrais omitidos automaticamente. Nesta execução, os novos objetos foram criados em ordem de dependência; não houve replay dos marts legados.

## [DADO OMITIDO]. Datas após publicação

Gold diária continua MAX(id_time)=[DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] [DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO]; novos marts mensais terminam em [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] (competência). Calendário termina em [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO]. Datasets TVD/IVD legados continuam em [DADO OMITIDO]/[DADO OMITIDO]. Não se forçou último movimento a [DADO OMITIDO]/[DADO OMITIDO]; sua investigação fica separada.

## [DADO OMITIDO]. Bootstrap, validators, ChartData, Guest e RLS

Bootstrap atualizou apenas oito charts e seus datasets da página principal, IDs preservados. Validator corrigido para aplicar adhoc_filters persistidos, domínio temporal e scopes distintos do total/barras. Default: oito charts sem erro em [DADO OMITIDO]s; filtro atividade F: oito sem erro em [DADO OMITIDO]s. ChartData default/filtrado executado e default reproduzido por SELECT no PostgreSQL em modo read-only. Guest real emitido pelo Embedded: [DADO OMITIDO] probes nos quatro datasets, nenhuma fuga de tenant; override de contexto negado e assinatura adulterada rejeitada. Apenas a sessão LACTALIS foi acessada.

## [DADO OMITIDO]. Equivalência AFTER, por par

| KPI | Período | Antes | Causas corrigidas | Restante | Depois | Numérico |
|---|---|---|---|---|---|---|
| MARKUP | MTD | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| MARKUP | Mês anterior | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| MARKUP | Média U3M | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Venda qtd | MTD | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Venda qtd | Mês anterior | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Venda qtd | Média U3M | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO], C1[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO], C1[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Estoque qtd | MTD | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Estoque qtd | Mês anterior | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Estoque qtd | Média U3M | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO], C1[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO], C1[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Giro | MTD | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO], C1[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C1[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Giro | Mês anterior | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO], C1[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C1[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Giro | Média U3M | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO], C1[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C1[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Estoque custo | MTD | C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Estoque custo | Mês anterior | C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Estoque custo | Média U3M | C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| IVD - Excesso | MTD | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| IVD - Excesso | Mês anterior | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| IVD - Excesso | Média U3M | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Venda sell out | MTD | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Venda sell out | Mês anterior | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Venda sell out | Média U3M | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| OSA | MTD | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| OSA | Mês anterior | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| OSA | Média U3M | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Perda OSA | MTD | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Perda OSA | Mês anterior | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Perda OSA | Média U3M | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| ROI | Mês anterior | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| ROI | Média U3M | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| ROI | Anual [DADO OMITIDO]M | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Venda custo | MTD | C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Venda custo | Mês anterior | C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| Venda custo | Média U3M | C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| TVD - Pré-ruptura | MTD | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| TVD - Pré-ruptura | Mês anterior | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| TVD - Pré-ruptura | Média U3M | C0[DADO OMITIDO], C0[DADO OMITIDO], C0[DADO OMITIDO] | C0[DADO OMITIDO] | C0[DADO OMITIDO], C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | NO_PBI_VALUE |
| ROI | MTD | V0[DADO OMITIDO] | — | V0[DADO OMITIDO] | UNMAPPED | NO_PBI_VALUE |

## [DADO OMITIDO]. Justificativas das diferenças restantes

### C0[DADO OMITIDO]
O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente.

### C0[DADO OMITIDO]
Venda/Estoque/ROI/Markup ainda obtêm MAX(conversion_rate) a partir dos itens presentes no fato por mês. Perda OSA usa agora o MAX de toda a dimensão no default, mas ainda não restringe esse MAX pelas seleções nativas de item/hierarquia como o PBIP.

### C0[DADO OMITIDO]
Sell out U3M ainda soma IF/produtos já calculados por mês/região, em vez de avaliar IF e produto sobre os agregados dos três meses por região; afeta ROI/Markup U3M.

### C0[DADO OMITIDO]
TVD/IVD continuam com zeros introduzidos pelo serving legado. A correção de SUM/BLANK no OSA não certifica estes dois datasets.

### C1[DADO OMITIDO]
Giro ainda usa a expansão regional por conversão e exige uma seleção de medida no dataset compartilhado. PBIP remove AP_CONVERSAO e impõe unidade na própria medida; a eliminação de semantic_scope=activity não elimina este gate.

### C1[DADO OMITIDO]
Venda/Estoque quantidade U3M continuam somando resultados mensais com MAX de fator mensal, em vez do fator avaliado no contexto completo do período.

### MARKUP — MTD
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: Venda/Estoque/ROI/Markup ainda obtêm MAX(conversion_rate) a partir dos itens presentes no fato por mês. Perda OSA usa agora o MAX de toda a dimensão no default, mas ainda não restringe esse MAX pelas seleções nativas de item/hierarquia como o PBIP.

### MARKUP — Mês anterior
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: Venda/Estoque/ROI/Markup ainda obtêm MAX(conversion_rate) a partir dos itens presentes no fato por mês. Perda OSA usa agora o MAX de toda a dimensão no default, mas ainda não restringe esse MAX pelas seleções nativas de item/hierarquia como o PBIP.

### MARKUP — Média U3M
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: Venda/Estoque/ROI/Markup ainda obtêm MAX(conversion_rate) a partir dos itens presentes no fato por mês. Perda OSA usa agora o MAX de toda a dimensão no default, mas ainda não restringe esse MAX pelas seleções nativas de item/hierarquia como o PBIP. C0[DADO OMITIDO]: Sell out U3M ainda soma IF/produtos já calculados por mês/região, em vez de avaliar IF e produto sobre os agregados dos três meses por região; afeta ROI/Markup U3M.

### Venda qtd — MTD
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: Venda/Estoque/ROI/Markup ainda obtêm MAX(conversion_rate) a partir dos itens presentes no fato por mês. Perda OSA usa agora o MAX de toda a dimensão no default, mas ainda não restringe esse MAX pelas seleções nativas de item/hierarquia como o PBIP.

### Venda qtd — Mês anterior
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: Venda/Estoque/ROI/Markup ainda obtêm MAX(conversion_rate) a partir dos itens presentes no fato por mês. Perda OSA usa agora o MAX de toda a dimensão no default, mas ainda não restringe esse MAX pelas seleções nativas de item/hierarquia como o PBIP.

### Venda qtd — Média U3M
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: Venda/Estoque/ROI/Markup ainda obtêm MAX(conversion_rate) a partir dos itens presentes no fato por mês. Perda OSA usa agora o MAX de toda a dimensão no default, mas ainda não restringe esse MAX pelas seleções nativas de item/hierarquia como o PBIP. C1[DADO OMITIDO]: Venda/Estoque quantidade U3M continuam somando resultados mensais com MAX de fator mensal, em vez do fator avaliado no contexto completo do período.

### Estoque qtd — MTD
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: Venda/Estoque/ROI/Markup ainda obtêm MAX(conversion_rate) a partir dos itens presentes no fato por mês. Perda OSA usa agora o MAX de toda a dimensão no default, mas ainda não restringe esse MAX pelas seleções nativas de item/hierarquia como o PBIP.

### Estoque qtd — Mês anterior
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: Venda/Estoque/ROI/Markup ainda obtêm MAX(conversion_rate) a partir dos itens presentes no fato por mês. Perda OSA usa agora o MAX de toda a dimensão no default, mas ainda não restringe esse MAX pelas seleções nativas de item/hierarquia como o PBIP.

### Estoque qtd — Média U3M
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: Venda/Estoque/ROI/Markup ainda obtêm MAX(conversion_rate) a partir dos itens presentes no fato por mês. Perda OSA usa agora o MAX de toda a dimensão no default, mas ainda não restringe esse MAX pelas seleções nativas de item/hierarquia como o PBIP. C1[DADO OMITIDO]: Venda/Estoque quantidade U3M continuam somando resultados mensais com MAX de fator mensal, em vez do fator avaliado no contexto completo do período.

### Giro — MTD
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C1[DADO OMITIDO]: Giro ainda usa a expansão regional por conversão e exige uma seleção de medida no dataset compartilhado. PBIP remove AP_CONVERSAO e impõe unidade na própria medida; a eliminação de semantic_scope=activity não elimina este gate.

### Giro — Mês anterior
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C1[DADO OMITIDO]: Giro ainda usa a expansão regional por conversão e exige uma seleção de medida no dataset compartilhado. PBIP remove AP_CONVERSAO e impõe unidade na própria medida; a eliminação de semantic_scope=activity não elimina este gate.

### Giro — Média U3M
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C1[DADO OMITIDO]: Giro ainda usa a expansão regional por conversão e exige uma seleção de medida no dataset compartilhado. PBIP remove AP_CONVERSAO e impõe unidade na própria medida; a eliminação de semantic_scope=activity não elimina este gate.

### Estoque custo — MTD
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente.

### Estoque custo — Mês anterior
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente.

### Estoque custo — Média U3M
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente.

### IVD - Excesso — MTD
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: TVD/IVD continuam com zeros introduzidos pelo serving legado. A correção de SUM/BLANK no OSA não certifica estes dois datasets.

### IVD - Excesso — Mês anterior
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: TVD/IVD continuam com zeros introduzidos pelo serving legado. A correção de SUM/BLANK no OSA não certifica estes dois datasets.

### IVD - Excesso — Média U3M
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: TVD/IVD continuam com zeros introduzidos pelo serving legado. A correção de SUM/BLANK no OSA não certifica estes dois datasets.

### Venda sell out — MTD
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: Venda/Estoque/ROI/Markup ainda obtêm MAX(conversion_rate) a partir dos itens presentes no fato por mês. Perda OSA usa agora o MAX de toda a dimensão no default, mas ainda não restringe esse MAX pelas seleções nativas de item/hierarquia como o PBIP.

### Venda sell out — Mês anterior
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: Venda/Estoque/ROI/Markup ainda obtêm MAX(conversion_rate) a partir dos itens presentes no fato por mês. Perda OSA usa agora o MAX de toda a dimensão no default, mas ainda não restringe esse MAX pelas seleções nativas de item/hierarquia como o PBIP.

### Venda sell out — Média U3M
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: Venda/Estoque/ROI/Markup ainda obtêm MAX(conversion_rate) a partir dos itens presentes no fato por mês. Perda OSA usa agora o MAX de toda a dimensão no default, mas ainda não restringe esse MAX pelas seleções nativas de item/hierarquia como o PBIP. C0[DADO OMITIDO]: Sell out U3M ainda soma IF/produtos já calculados por mês/região, em vez de avaliar IF e produto sobre os agregados dos três meses por região; afeta ROI/Markup U3M.

### OSA — MTD
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente.

### OSA — Mês anterior
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente.

### OSA — Média U3M
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente.

### Perda OSA — MTD
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: Venda/Estoque/ROI/Markup ainda obtêm MAX(conversion_rate) a partir dos itens presentes no fato por mês. Perda OSA usa agora o MAX de toda a dimensão no default, mas ainda não restringe esse MAX pelas seleções nativas de item/hierarquia como o PBIP.

### Perda OSA — Mês anterior
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: Venda/Estoque/ROI/Markup ainda obtêm MAX(conversion_rate) a partir dos itens presentes no fato por mês. Perda OSA usa agora o MAX de toda a dimensão no default, mas ainda não restringe esse MAX pelas seleções nativas de item/hierarquia como o PBIP.

### Perda OSA — Média U3M
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: Venda/Estoque/ROI/Markup ainda obtêm MAX(conversion_rate) a partir dos itens presentes no fato por mês. Perda OSA usa agora o MAX de toda a dimensão no default, mas ainda não restringe esse MAX pelas seleções nativas de item/hierarquia como o PBIP.

### ROI — Mês anterior
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: Venda/Estoque/ROI/Markup ainda obtêm MAX(conversion_rate) a partir dos itens presentes no fato por mês. Perda OSA usa agora o MAX de toda a dimensão no default, mas ainda não restringe esse MAX pelas seleções nativas de item/hierarquia como o PBIP.

### ROI — Média U3M
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: Venda/Estoque/ROI/Markup ainda obtêm MAX(conversion_rate) a partir dos itens presentes no fato por mês. Perda OSA usa agora o MAX de toda a dimensão no default, mas ainda não restringe esse MAX pelas seleções nativas de item/hierarquia como o PBIP. C0[DADO OMITIDO]: Sell out U3M ainda soma IF/produtos já calculados por mês/região, em vez de avaliar IF e produto sobre os agregados dos três meses por região; afeta ROI/Markup U3M.

### ROI — Anual [DADO OMITIDO]M
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: Venda/Estoque/ROI/Markup ainda obtêm MAX(conversion_rate) a partir dos itens presentes no fato por mês. Perda OSA usa agora o MAX de toda a dimensão no default, mas ainda não restringe esse MAX pelas seleções nativas de item/hierarquia como o PBIP.

### Venda custo — MTD
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente.

### Venda custo — Mês anterior
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente.

### Venda custo — Média U3M
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente.

### TVD - Pré-ruptura — MTD
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: TVD/IVD continuam com zeros introduzidos pelo serving legado. A correção de SUM/BLANK no OSA não certifica estes dois datasets.

### TVD - Pré-ruptura — Mês anterior
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: TVD/IVD continuam com zeros introduzidos pelo serving legado. A correção de SUM/BLANK no OSA não certifica estes dois datasets.

### TVD - Pré-ruptura — Média U3M
C0[DADO OMITIDO]: O default de histórico/causas usa interseção CNPJ com EXISTS, Rede não nula e catálogo Gold contratado. Não foi reproduzida a propagação bidirecional de todas as seleções do catálogo: filtros nativos continuam incidindo nas colunas locais do histórico. TVD/IVD mantêm serving legado sem a nova interseção obrigatória. O filtro de página AP_CONVERSAO <> valor também não está implementado como uma restrição permanente para todas as interações. Portanto o contexto completo da página continua diferente. C0[DADO OMITIDO]: TVD/IVD continuam com zeros introduzidos pelo serving legado. A correção de SUM/BLANK no OSA não certifica estes dois datasets.

### ROI — MTD
V0[DADO OMITIDO]: ROI MTD não é projetado no visual principal.

Famílias de origem PBIP PARTICULAR3/LACTALIS versus Gold derivada de DAILY2[DADO OMITIDO] continuam sem prova upstream de igualdade de linhas. Bookmarks/estado interativo vivo não foram inventados. Estes limites impedem declarar equivalência completa além dos testes de cláusulas.

## [DADO OMITIDO]. git diff --stat
```text
 scripts/publish_lactalis_marts.py                  | [DADO OMITIDO] +++++++++++++++++++++-
 superset/bootstrap_overview.py                     | [DADO OMITIDO] ++++++--
 .../plugin-chart-neoretail-kpi/src/buildQuery.js   | [DADO OMITIDO] +++-
 .../src/transformProps.js                          | [DADO OMITIDO] ++++++++++++++---
 superset/validate_overview.py                      | [DADO OMITIDO] ++++++-
 [DADO OMITIDO] files changed, [DADO OMITIDO] insertions(+), [DADO OMITIDO] deletions(-)
```

## [DADO OMITIDO]. git status --short
```text
 M scripts/publish_lactalis_marts.py
 M superset/bootstrap_overview.py
 M superset/frontend-plugin/plugin-chart-neoretail-kpi/src/buildQuery.js
 M superset/frontend-plugin/plugin-chart-neoretail-kpi/src/transformProps.js
 M superset/validate_overview.py
?? analytics-db/marts/[DADO OMITIDO]_pbip_overview_calendar.sql
?? analytics-db/marts/[DADO OMITIDO]_pbip_overview_context.sql
?? local-engine/tests/fixtures/pbip_lactalis_overview_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_lactalis_real_contract_rows_2[DADO OMITIDO].json
?? local-engine/tests/test_pbip_lactalis_overview.py
?? superset/diagnose_lactalis_inventory.py
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-contract.mjs
?? superset/neoretail_bootstrap/pbip_overview/
?? superset/profile_lactalis_osa_filtered.py
```

Os dois scripts locais preexistentes permanecem untracked, sem staging. Nenhum arquivo foi adicionado ao índice. Artifacts de evidência ficam em generated, já ignorado pelo projeto.

## [DADO OMITIDO]. Nenhum commit/push

HEAD permanece `[DADO OMITIDO]d2f5[DADO OMITIDO]b5[DADO OMITIDO]ead1bae9af6d2ef7b7[DADO OMITIDO]f9a4[DADO OMITIDO]ae`; branch não mudou. Não houve commit, push, merge ou rebase; PR9 não foi alterada e permanece Draft.

## [DADO OMITIDO]. Volumes e dados preservados

Nenhum volume foi removido. Nenhum Bronze/Silver/Gold base foi escrito por esta tarefa. A nova imagem do Superset foi construída e somente esse serviço foi recriado; dados e outros serviços preservados. Nenhuma sessão Power BI foi lançada/restaurada/atualizada. Certificação numérica permanece NO_PBI_VALUE nos [DADO OMITIDO] pares.
