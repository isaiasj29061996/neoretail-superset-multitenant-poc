> Cópia para GitHub: números de origem e identificadores numéricos omitidos. Original integral exige backup externo. Não usar esta cópia como fixture ou SQL executável.

# ROI / Anual [DADO OMITIDO]M — agregado BLANK final — LACTALIS [DADO OMITIDO] — [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO]

**SEMÂNTICA DO ESTADO SALVO CONGELÁVEL**: **[DADO OMITIDO] SEMANTIC_MATCH / [DADO OMITIDO] SEMANTIC_DIFFERENCE / [DADO OMITIDO] UNMAPPED** após corrigir somente o agregado anual. Contrato completo: **[DADO OMITIDO] MATCH / [DADO OMITIDO] DIFFERENCE / [DADO OMITIDO] UNMAPPED**, com cada proof F1[DADO OMITIDO]D preservado. **[DADO OMITIDO] NO_PBI_VALUE**, sem NUMERIC_MATCH. Nenhum dado/mart, filtro, conversão, calendário ou fórmula mensal alterado. Sem otimização, commit ou push.

## Contrato DAX literal e cadeia de dependências

PBIP extraído atual: `generated\pbi_lactalis_reference_2[DADO OMITIDO]\NeoRetail Pocket RF.SemanticModel\definition\tables\_Metricas.tmdl`; SHA-[DADO OMITIDO] `c5[DADO OMITIDO]c0fa2[DADO OMITIDO]f7a0[DADO OMITIDO]f4[DADO OMITIDO]d3[DADO OMITIDO]c9bc0[DADO OMITIDO]c2a8[DADO OMITIDO]eb9[DADO OMITIDO]caa` conferido antes de editar. Fechamento completo ROI Anual: Estoque Custo, ROI, ROI Anual, Venda Custo, Venda sell out. As [DADO OMITIDO] definições do snapshot DAX também conferem literalmente com o TMDL, preservando referências dos períodos já certificados.

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

### Venda sell out

```dax
SUMX(
			
			    VALUES(DIM_LOCAL[Região]), 
			    VAR MedidaSelecionada = SELECTEDVALUE(AP_CONVERSAO[nm_measure])
			    VAR Fator =
			        CALCULATE(
			            MAX(DIM_CONVERSAO[conversion_rate]),
			            DIM_CONVERSAO[nm_measure] = MedidaSelecionada
			        )
			    VAR FaturamentoLocal = CALCULATE(SUM(FATOS_PARTICULAR_HISTORICO[FATURAMENTO]))
			    VAR VolumeLocal = CALCULATE(SUM(FATOS_PARTICULAR_HISTORICO[VOLUME_UNIDADES]))
			    VAR PrecoMedioLocal = CALCULATE(AVERAGE(FATOS_PARTICULAR_HISTORICO[AVG_SALES_PRICE]))
			    RETURN
			        IF(
			            FaturamentoLocal > [DADO OMITIDO],
			            FaturamentoLocal,
			            (VolumeLocal * Fator) * (PrecoMedioLocal * Fator)
			        )
			)
```

### Venda Custo

```dax
SUMX(
			    FATOS_PARTICULAR_HISTORICO,
			    FATOS_PARTICULAR_HISTORICO[VOLUME_UNIDADES]*
			    FATOS_PARTICULAR_HISTORICO[AVG_PRICE_COST])
```

### Estoque Custo

```dax
SUMX(
			    FATOS_PARTICULAR_HISTORICO,
			    FATOS_PARTICULAR_HISTORICO[ESTOQUE_MEDIO]*
			    FATOS_PARTICULAR_HISTORICO[AVG_PRICE_COST])
```

ROI Anual aplica CALCULATE(SUMX(VALUES(calendário[AnoMes]),[ROI]),DATESINPERIOD(calendário[DATA],MAX(calendário[DATA]),[DADO OMITIDO],MONTH),REMOVEFILTERS([DADO OMITIDO]_0_DIM_PERIODO)). Cada membro AnoMes reavalia ROI base com transição de contexto. ROI usa IF(vSellOut=[DADO OMITIDO] || vVendaCusto=[DADO OMITIDO],CALCULATE(DIVIDE(vSellOut-vVendaCusto,[Estoque Custo]))). Venda Custo e Estoque Custo somam produtos nullable por fato; Sell-out conserva a iteração regional e fatores existentes. Nenhuma medida DAX foi editada.

## Janela congelada e membros do iterador

Calendar importado: [DADO OMITIDO] dias, [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO]…[DADO OMITIDO][DADO OMITIDO][DADO OMITIDO]; âncora MAX(Data)=[DADO OMITIDO][DADO OMITIDO][DADO OMITIDO], independente de MAX(fato). DATESINPERIOD([DADO OMITIDO],MONTH) retém [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO]…[DADO OMITIDO][DADO OMITIDO][DADO OMITIDO]: [DADO OMITIDO] meses de duração podem tocar **[DADO OMITIDO] AnoMes**. O default contém Out/[DADO OMITIDO] parcial, Nov/[DADO OMITIDO]…Set/[DADO OMITIDO] e Out/[DADO OMITIDO] parcial. Esta etapa não alterou annualBoundary, filtros de data, SQL, materialized calendar, DATA_AT nem sua publicação.

A relação do PBIP é FATOS_PARTICULAR_HISTORICO.MES_ANO → [DADO OMITIDO]_0_CALENDARIO.Data. A prova somente leitura contou [DADO OMITIDO] linhas na history, **zero datas fora do início do mês**. Na borda inicial Out/[DADO OMITIDO], o dia [DADO OMITIDO] está fora da janela: esse membro do calendário existe, mas sem fatos elegíveis; ROI C1[DADO OMITIDO] retorna [DADO OMITIDO]. Logo, não seria correto afirmar que [DADO OMITIDO] retornos de fatos BLANK implicam agregado BLANK no default de [DADO OMITIDO] membros. O witness da divergência exige o contexto explícito AnoMes Nov/[DADO OMITIDO]…Out/[DADO OMITIDO], que exclui a borda anterior. REMOVEFILTERS([DADO OMITIDO]_0_DIM_PERIODO) não remove o filtro direto de AnoMes.

[Calendário/membros e granularidade Gold, somente leitura](pbip_roi_annual_calendar_proof_2[DADO OMITIDO].json). [DATESINPERIOD Microsoft](https://learn.microsoft.com/en-us/dax/datesinperiod-function-dax). Nenhum número observado no Power BI foi obtido; contrato e witnesses derivam do PBIP, não de uma sessão Desktop.

## Diferença comprovada BEFORE e camada responsável

SQL/datasets entregam corretamente NULL, zero e componentes numéricos após C1[DADO OMITIDO]. C1[DADO OMITIDO] já faz o IF DAX ordinário comparar BLANK com zero, sem destruir componentes. O problema restante era exclusivamente o **agregado anual no frontend**: `annualCalendarRows.reduce((sum,row)=>sum+(row.values[[DADO OMITIDO]]??[DADO OMITIDO]),[DADO OMITIDO])`. Todos os intermediários BLANK e nenhum membro numérico eram transformados em resultado [DADO OMITIDO]. O iterador SUMX ignora BLANK; sem retorno numérico produz BLANK. [SUMX Microsoft](https://learn.microsoft.com/en-us/dax/sumx-function-dax). Expected derived DAX CONTRACT não significa valor vivo de Power BI.

## Witness reproduzível BEFORE / CONTRACT / AFTER

Fixture controlada, sem inserção na Gold: contexto explícito dos [DADO OMITIDO] AnoMes abaixo; em cada mês Sell-out=[DADO OMITIDO], Venda Custo=[DADO OMITIDO], Estoque Custo=NULL. IF zero é falso; DIVIDE([DADO OMITIDO],BLANK) retorna BLANK. A fixture mantém esses mesmos inputs, membros e intermediários no BEFORE e AFTER.

| AnoMes retido | Sell-out | Venda Custo | Estoque Custo | ROI intermediário |
|---|---:|---:|---|---|
| [DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | BLANK | BLANK |
| [DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | BLANK | BLANK |
| [DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | BLANK | BLANK |
| [DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | BLANK | BLANK |
| [DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | BLANK | BLANK |
| [DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | BLANK | BLANK |
| [DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | BLANK | BLANK |
| [DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | BLANK | BLANK |
| [DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | BLANK | BLANK |
| [DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | BLANK | BLANK |
| [DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | BLANK | BLANK |
| [DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | BLANK | BLANK |

Agregado final do mesmo contexto:

| Agregado | DAX CONTRACT | SUPERSET BEFORE | SUPERSET AFTER |
|---|---|---|---|
| [DADO OMITIDO] intermediários BLANK | BLANK | [DADO OMITIDO] | BLANK |

[Witness BEFORE](pbip_roi_annual_witness_before_2[DADO OMITIDO].json), [witness AFTER e tabela completa](pbip_roi_annual_witness_after_2[DADO OMITIDO].json). Não foi apresentado um witness real com [DADO OMITIDO] meses todos BLANK: a borda default mensal já retorna [DADO OMITIDO] por ausência de fato. A fixture retém explicitamente os [DADO OMITIDO] membros necessários à divergência e foi executada no consumidor frontend real com doubles apenas de dependência Superset.

## BLANK, ausência de linha e zero

| Caso | Membros VALUES | Fatos / retornos | DAX CONTRACT / AFTER |
|---|---:|---|---|
| Todos [DADO OMITIDO] BLANK | [DADO OMITIDO] | [DADO OMITIDO] linhas existentes, [DADO OMITIDO] retornos BLANK | BLANK |
| Iterador vazio | [DADO OMITIDO] | nenhum membro | BLANK |
| Sem fatos, calendário presente | [DADO OMITIDO] | nenhum fato; ROI C1[DADO OMITIDO] avalia [DADO OMITIDO] por membro | [DADO OMITIDO] |
| BLANK + valor | [DADO OMITIDO] | números e BLANK | soma dos números |
| BLANK + zero | [DADO OMITIDO] | pelo menos um zero numérico | [DADO OMITIDO] |
| Todos zero | [DADO OMITIDO] | [DADO OMITIDO] zeros numéricos | [DADO OMITIDO] |
| Um valor e demais BLANK | [DADO OMITIDO] | um número, demais BLANK | esse número |
| Positivos / negativos / mistura | [DADO OMITIDO] | números assinados; BLANK ignorado | soma assinada |
| Default, [DADO OMITIDO] fatos BLANK e borda parcial sem fato | [DADO OMITIDO] | [DADO OMITIDO] BLANK + um ROI C1[DADO OMITIDO]=[DADO OMITIDO] | [DADO OMITIDO] |

Iterador vazio e todos os retornos BLANK coincidem em resultado BLANK, mas permanecem distintos na proveniência/contagem. Nenhum fato não equivale a VALUES vazio: o calendário pode continuar produzindo membros e ROI C1[DADO OMITIDO]=[DADO OMITIDO]. Timeline e hasData mantêm ausência real de linha; o agregado não cria fatos ou pontos de gráfico. Zero numérico continua contado, inclusive resultado de cancelamento entre valores positivos/negativos.

## Implementação mínima e limite do contexto

`pbipAnnualRoiSum` recebe os intermediários e os membros efetivos do iterador. Conta/soma somente valores não nulos e retorna null quando nenhum existe. Para membro do calendário sem fato, reutiliza o ROI C1[DADO OMITIDO] atual no contexto sem componentes, que retorna [DADO OMITIDO]; não coalesce o BLANK de uma linha existente. Apenas o agregado anual ROI opt-in usa esse helper. Perfis genéricos e caminhos ROI anterior/U3M/Markup permanecem com o código e contratos anteriores.

`pbip_roi_annual_blank=true` foi publicado somente no chart ROI [DADO OMITIDO] e na apresentação PBIP durável. O helper consome a janela anual já existente. No default enumera os AnoMes tocados por essa janela; `pbip_roi_annual_members` permite fornecer o conjunto explícito efetivamente retido, com unicidade VALUES e interseção da mesma janela. Esse campo descreve contexto conhecido do iterador; **não cria/modifica um filtro nativo ou SQL**. O witness antes/depois fornece o mesmo conjunto conhecido. Não foi implementada nem certificada a propagação automática desse conjunto através de bookmarks/hierarquias/interações: isso continua no F1[DADO OMITIDO]D, separadamente, mantendo contrato completo [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO].

Não houve alteração de IF/DIVIDE ROI, Markup, Venda Custo, Estoque Custo, Sell-out, C1[DADO OMITIDO], calendário, conversão, AP→Produto, CNPJ, filtros ou buildQuery. [Freeze por SHA](pbip_roi_annual_freeze_2[DADO OMITIDO].json). Nenhum BLANK foi convertido globalmente em zero.

## Casos controlados e não regressão

| Caso | BEFORE | DAX CONTRACT | AFTER |
|---|---|---|---|
| all1[DADO OMITIDO]_blank | [DADO OMITIDO] | BLANK / NULL | BLANK / NULL |
| [DADO OMITIDO]_existing_all_blank | [DADO OMITIDO] | BLANK / NULL | BLANK / NULL |
| blank_and_values | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| blank_and_zero | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| all_zero | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| one_value_other_blank | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| positive_values | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| negative_values | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| positive_negative_blank | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| no_calendar_members | [DADO OMITIDO] | BLANK / NULL | BLANK / NULL |
| no_facts_calendar_members_exist | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |

Foram acrescentados **[DADO OMITIDO] checks frontend**: todos os cenários obrigatórios, membros vazios, fatos ausentes com calendário existente, borda parcial, unicidade/interseção de membros e ausência de âncora. Em nove matrizes são comparados integralmente os intermediários e os componentes BEFORE/AFTER, ROI current/previous/U3M/lastYear e o objeto Markup completo. Negativos são permitidos: Sell-out [DADO OMITIDO], Venda Custo [DADO OMITIDO], Estoque Custo [DADO OMITIDO] gera ROI [DADO OMITIDO], sem violar os guards existentes. Oracle relacional independente usa SQLite em memória e SUM nullable sobre calendário LEFT JOIN intermediários; foram acrescentados [DADO OMITIDO] casos mais o contrato DAX literal. Nenhuma linha em produção.

Os **[DADO OMITIDO] pares MATCH anteriores foram preservados integralmente na classificação JSON**, com prova de igualdade das linhas anteriores e freeze de fontes. Só ROI / Anual [DADO OMITIDO]M mudou de status e ganhou o flag. ROI MTD continua UNMAPPED e não recebeu visual/medida nova.

## Regressão completa e runtime

| Gate | Resultado |
|---|---|
| Python completo | [DADO OMITIDO] passed = [DADO OMITIDO] anteriores + [DADO OMITIDO] novos |
| Frontend anterior | [DADO OMITIDO] = [DADO OMITIDO] base/PBIP + [DADO OMITIDO] F1[DADO OMITIDO] + [DADO OMITIDO] F1[DADO OMITIDO]/C0[DADO OMITIDO] + [DADO OMITIDO] C0[DADO OMITIDO] + [DADO OMITIDO] C1[DADO OMITIDO] + [DADO OMITIDO] C1[DADO OMITIDO] |
| Frontend anual novo | [DADO OMITIDO]; total [DADO OMITIDO] |
| Opções | [DADO OMITIDO] comparações / [DADO OMITIDO] cenários / [DADO OMITIDO] probes Guest |
| ChartData default / filtrado | [DADO OMITIDO] charts por cenário, zero failures |
| Guest/RLS tenant [DADO OMITIDO] | [DADO OMITIDO] probes; overrides [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] negados; assinatura adulterada rejeitada |
| Replay SQL | [DADO OMITIDO] cenários datasets [DADO OMITIDO]/[DADO OMITIDO]; todos os campos idênticos |
| C0[DADO OMITIDO] congelado | full U3M [DADO OMITIDO], contra monthly legado [DADO OMITIDO] |
| Assets | flags anuais, C1[DADO OMITIDO], C0[DADO OMITIDO] e F1[DADO OMITIDO] encontrados nos bundles compilados |
| Health | aprovado; [DADO OMITIDO] serviços e [DADO OMITIDO] endpoints HTTP [DADO OMITIDO] |

Nenhum expected existente foi editado. [Python](pbip_roi_annual_python_full_2[DADO OMITIDO].log), [frontend base](pbip_roi_annual_frontend_base_2[DADO OMITIDO].log), [F1[DADO OMITIDO]](pbip_roi_annual_frontend_f1[DADO OMITIDO]_2[DADO OMITIDO].log), [F1[DADO OMITIDO]/C0[DADO OMITIDO]/C0[DADO OMITIDO]/C1[DADO OMITIDO]](pbip_roi_annual_frontend_existing_2[DADO OMITIDO].log), [C1[DADO OMITIDO]](pbip_roi_annual_frontend_c1[DADO OMITIDO]_2[DADO OMITIDO].json), [contrato anual](pbip_roi_annual_frontend_contract_2[DADO OMITIDO].json), [opções](pbip_roi_annual_options_runtime_2[DADO OMITIDO].json), [Guest/RLS](pbip_roi_annual_guest_rls_2[DADO OMITIDO].json), [replay](pbip_roi_annual_replay_2[DADO OMITIDO].json), [ChartData default](pbip_roi_annual_chartdata_default_2[DADO OMITIDO].log), [ChartData filtrado](pbip_roi_annual_chartdata_filtered_2[DADO OMITIDO].log), [assets](pbip_roi_annual_deployed_assets_2[DADO OMITIDO].json), [health](pbip_roi_annual_health_2[DADO OMITIDO].log).

## Performance: somente medição, protocolo congelado

Baseline histórico C1[DADO OMITIDO] e AFTER usam uma única compilação das mesmas consultas ChartData e SELECT Analytics readonly, sem cache de resultados/audit logger. Hashes compilados são comparados à prova anterior de igualdade SQL; não há segunda compilação dentro do tempo medido. AFTER não concorreu com outros gates Gold. ChartData funcional pode usar cache e não serve como benchmark. Os tempos não medem navegador/renderização nem todo o endpoint HTTP.

| Cenário | Dashboard BEFORE | Dashboard AFTER | ROI BEFORE | ROI AFTER | Markup BEFORE | Markup AFTER |
|---|---:|---:|---:|---:|---:|---:|
| default | [DADO OMITIDO]s | [DADO OMITIDO]s | [DADO OMITIDO]s | [DADO OMITIDO]s | [DADO OMITIDO]s | [DADO OMITIDO]s |
| filtered | [DADO OMITIDO]s | [DADO OMITIDO]s | [DADO OMITIDO]s | [DADO OMITIDO]s | [DADO OMITIDO]s | [DADO OMITIDO]s |

SQL e queries são idênticos, sem custo SQL introduzido pela correção. O custo frontend adicional é uma enumeração curta dos membros existentes e uma soma final; não há nova consulta. As medições históricas isoladas não provam causalidade de variação temporal. Nenhuma otimização ou refactor foi realizado. Tempos individuais ROI por query (timeline / barras / auxiliar C0[DADO OMITIDO]):

- default: [DADO OMITIDO]s / [DADO OMITIDO] rows, [DADO OMITIDO]s / [DADO OMITIDO] rows, [DADO OMITIDO]s / [DADO OMITIDO] rows

- filtered: [DADO OMITIDO]s / [DADO OMITIDO] rows, [DADO OMITIDO]s / [DADO OMITIDO] rows, [DADO OMITIDO]s / [DADO OMITIDO] rows

[Replay default](pbip_roi_annual_sql_benchmark_after_default_2[DADO OMITIDO].log), [replay filtrado](pbip_roi_annual_sql_benchmark_after_filtered_2[DADO OMITIDO].log).

## Classificação final e estado congelável

| Contrato | BEFORE MATCH / DIFFERENCE / UNMAPPED | AFTER MATCH / DIFFERENCE / UNMAPPED |
|---|---|---|
| Estado salvo / contexto explícito conhecido | [DADO OMITIDO] / [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] / [DADO OMITIDO] |
| Contrato completo com interação não certificada | [DADO OMITIDO] / [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] / [DADO OMITIDO] |

Resultado [DADO OMITIDO]/[DADO OMITIDO] decorre do DAX e dos casos executados, não de editar expected/status para esconder divergência. Causa ANNUAL_ALL_BLANK_REDUCTION removida somente do par ROI Anual. F1[DADO OMITIDO]D continua individualmente em cada linha mapeada; não foi apagado ou tratado como certificado por sucesso da soma. NO_PBI_VALUE=[DADO OMITIDO]; nenhuma estimativa ou valor vivo de Power BI. Não foi detectada nem corrigida outra fórmula fora do escopo.

**SEMÂNTICA DO ESTADO SALVO CONGELÁVEL**, para próxima etapa de otimização autorizada separadamente: [manifesto de fontes/charts/SQL/assets/marts](pbip_roi_annual_frozen_semantics_2[DADO OMITIDO].json), [classificação de todos os [DADO OMITIDO] pares](pbi_superset_semantic_equivalence_roi_annual_final_2[DADO OMITIDO].json). O contexto explícito dos membros faz parte desse contrato; propagação por UI completa permanece F1[DADO OMITIDO]D.

## Git e restrições

Branch `feat/osa-industry-certification` e HEAD `[DADO OMITIDO]d2f5[DADO OMITIDO]b5[DADO OMITIDO]ead1bae9af6d2ef7b7[DADO OMITIDO]f9a4[DADO OMITIDO]ae` iguais ao início. PR não foi editada e continua Draft conforme baseline. Nenhum commit/push/merge/rebase/troca de branch/main, nenhuma publicação de marts ou pipeline Bronze/Silver/Gold, nenhum volume alterado. Só Superset foi recompilado/recriado, mantendo os volumes. Nenhum arquivo apagado, .gitignore ou exclude alterado.

### git diff --stat BEFORE

```text
 scripts/publish_lactalis_marts.py                  | [DADO OMITIDO] ++++++++++++-
 superset/Dockerfile                                |  [DADO OMITIDO] +
 superset/bootstrap_overview.py                     | [DADO OMITIDO] ++++++++++++++++------
 .../plugin-chart-neoretail-kpi/src/buildQuery.js   | [DADO OMITIDO] +++-
 .../src/transformProps.js                          | [DADO OMITIDO] ++++++++++++++++----
 superset/validate_overview.py                      | [DADO OMITIDO] ++++++++-
 [DADO OMITIDO] files changed, [DADO OMITIDO] insertions(+), [DADO OMITIDO] deletions(-)
```

### git diff --stat AFTER

```text
 scripts/publish_lactalis_marts.py                  |  [DADO OMITIDO] ++++++++++-
 superset/Dockerfile                                |   [DADO OMITIDO] +
 superset/bootstrap_overview.py                     |  [DADO OMITIDO] ++++++++++++-----
 .../plugin-chart-neoretail-kpi/src/buildQuery.js   |  [DADO OMITIDO] ++-
 .../src/transformProps.js                          | [DADO OMITIDO] ++++++++++++++++++---
 superset/validate_overview.py                      |  [DADO OMITIDO] ++++++-
 [DADO OMITIDO] files changed, [DADO OMITIDO] insertions(+), [DADO OMITIDO] deletions(-)
```

Diff acumulado inclui etapas anteriores e não mostra fontes novos untracked. O snapshot SHA comprova apenas dois arquivos existentes alterados nesta etapa: transformProps.js e apresentação PBIP. Tests/expected antigos e todo SQL permanecem idênticos. Acrescentados somente contrato frontend anual e [DADO OMITIDO] testes Python/oracle, além dos artefatos generated locais.

### git status --short AFTER

```text
 M scripts/publish_lactalis_marts.py
 M superset/Dockerfile
 M superset/bootstrap_overview.py
 M superset/frontend-plugin/plugin-chart-neoretail-kpi/src/buildQuery.js
 M superset/frontend-plugin/plugin-chart-neoretail-kpi/src/transformProps.js
 M superset/validate_overview.py
?? analytics-db/marts/[DADO OMITIDO]_pbip_overview_calendar.sql
?? analytics-db/marts/[DADO OMITIDO]_pbip_overview_context.sql
?? analytics-db/marts/[DADO OMITIDO]_pbip_filters_conversion.sql
?? analytics-db/marts/[DADO OMITIDO]_pbip_conversion_direction.sql
?? local-engine/tests/fixtures/pbip_c1[DADO OMITIDO]_dax_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_f1[DADO OMITIDO]_final_evidence_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_f1[DADO OMITIDO]_selectors_pbip_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_f1[DADO OMITIDO]_c0[DADO OMITIDO]_dax_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_filters_conversion_real_rows_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_lactalis_overview_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_lactalis_real_contract_rows_2[DADO OMITIDO].json
?? local-engine/tests/test_pbip_c0[DADO OMITIDO]_sellout_u3m.py
?? local-engine/tests/test_pbip_c1[DADO OMITIDO]_cost_blank.py
?? local-engine/tests/test_pbip_c1[DADO OMITIDO]_operator_contract.py
?? local-engine/tests/test_pbip_f1[DADO OMITIDO]_final_evidence.py
?? local-engine/tests/test_pbip_f1[DADO OMITIDO]_selectors.py
?? local-engine/tests/test_pbip_f1[DADO OMITIDO]_c0[DADO OMITIDO]_daily_context.py
?? local-engine/tests/test_pbip_filter_conversion_contract.py
?? local-engine/tests/test_pbip_lactalis_overview.py
?? local-engine/tests/test_pbip_roi_annual_blank.py
?? superset/diagnose_lactalis_inventory.py
?? superset/frontend-extension/pbipSelectorDependencies.mjs
?? superset/frontend-extension/register-pbip-selectors.mjs
?? superset/frontend-extension/test-pbip-selectors.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-c0[DADO OMITIDO]-contract.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-c1[DADO OMITIDO]-contract.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-c1[DADO OMITIDO]-contract.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-contract.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-roi-annual-blank-contract.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-tvd-ivd-contract.mjs
?? superset/neoretail_bootstrap/pbip_overview/
?? superset/profile_lactalis_osa_filtered.py
```

Os dois scripts superset/diagnose_lactalis_inventory.py e superset/profile_lactalis_osa_filtered.py permanecem visíveis, sem versionamento. Sem commit/push.
