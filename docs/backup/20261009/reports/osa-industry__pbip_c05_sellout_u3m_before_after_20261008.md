> Cópia para GitHub: números de origem e identificadores numéricos omitidos. Original integral exige backup externo. Não usar esta cópia como fixture ou SQL executável.

# C0[DADO OMITIDO] — Sell-out U3M, Markup U3M e ROI U3M — LACTALIS [DADO OMITIDO]

Escopo concluído exclusivamente no caminho PBIP. Fonte principal: ZIP extraído, modelo `NeoRetail Pocket RF.SemanticModel/definition/tables/_Metricas.tmdl`. Nenhum valor atual observado no Power BI: **[DADO OMITIDO] NO_PBI_VALUE**. O expected abaixo é derivado do contrato DAX sobre Gold real.

## DAX exato e medidas auxiliares

### MARKUP U3M

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

### Venda sell out U3M

```dax
DIVIDE(calculate([Venda sell out], '[DADO OMITIDO]_0_CALENDARIO'[U3M] = True),[DADO OMITIDO])
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

### Venda Custo U3M

```dax
divide(calculate([Venda Custo], all(AP_CONVERSAO[nm_measure]), '[DADO OMITIDO]_0_CALENDARIO'[U3M] = True),[DADO OMITIDO])
```

### Venda Custo

```dax
SUMX(
			    FATOS_PARTICULAR_HISTORICO,
			    FATOS_PARTICULAR_HISTORICO[VOLUME_UNIDADES]*
			    FATOS_PARTICULAR_HISTORICO[AVG_PRICE_COST])
```

### ROI U3M

```dax
calculate([ROI],'[DADO OMITIDO]_0_CALENDARIO'[U3M] = True)
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

### Estoque Custo

```dax
SUMX(
			    FATOS_PARTICULAR_HISTORICO,
			    FATOS_PARTICULAR_HISTORICO[ESTOQUE_MEDIO]*
			    FATOS_PARTICULAR_HISTORICO[AVG_PRICE_COST])
```

## Região, filtros e ordem de avaliação

`VALUES(DIM_LOCAL[Região])` vem de DIM_LOCAL, não de uma região calculada globalmente na fato. A relação DIM_LOCAL → FATOS_PARTICULAR_HISTORICO é OneDirection, Many-to-One; produto/fato não reduz DIM_LOCAL no sentido inverso. Filtros locais, catálogo e a ponte CNPJ já certificada determinam as regiões e fatos elegíveis. BLANK Região participa; o GROUP BY SQL mantém NULL como grupo. Regiões sem fatos produzem BLANK e não contribuem ao SUMX. A agregação por regiões com fatos é equivalente nesse domínio, sem criar uma região global.

A consulta aplica os filtros dimensionais e calendário U3M antes de agrupar por Região. Calcula SUM(FATURAMENTO), SUM(VOLUME_UNIDADES) e AVG(AVG_SALES_PRICE) no contexto inteiro. Em cada Região usa exatamente `receita > [DADO OMITIDO]`; zero, negativa e BLANK seguem o fallback `(volume * fator) * (preço * fator)`. O fator é MAX dimensional conforme AP, sem redução por Produto, aplicado duas vezes. Seleção inexistente/valor mantém o fator BLANK; não foi introduzido COALESCE/default novo.

A soma regional completa só é dividida por [DADO OMITIDO] no indicador Sell-out U3M. Markup usa essa média em relação a Venda Custo U3M; os /[DADO OMITIDO] cancelam na razão. ROI U3M aplica CALCULATE([ROI], U3M=True), sem /[DADO OMITIDO] no ROI: reutiliza Sell-out total U3M, custo total e estoque custo total. Custo/estoque reutilizam os componentes mensais aditivos já aprovados; C1[DADO OMITIDO]/C1[DADO OMITIDO] continuam registradas e não foram corrigidas.

## Witness BEFORE / EXPECTED SEMANTIC / AFTER

Filtros nativos exatos: Item `[DADO OMITIDO] - Iogurte Liquido Morang Btv Cx8Gf1[DADO OMITIDO]G`, Loja `B6[DADO OMITIDO] - B6[DADO OMITIDO] - MORADA DO SOL`, AP `unidade`. U3M: julho, agosto e setembro de [DADO OMITIDO], segundo os flags importados do calendário congelado. Fator: [DADO OMITIDO].

| Mês | Região | Receita | Volume | Soma de preços | Preços não BLANK |
|---|---|---:|---:|---:|---:|
| [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | Centro-Oeste | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | Centro-Oeste | None | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | Centro-Oeste | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |



| Caminho | Sell-out U3M |
|---|---:|
| BEFORE: calcular cada mês, somar, /[DADO OMITIDO] | [DADO OMITIDO] |
| EXPECTED SEMANTIC: calcular U3M completo, /[DADO OMITIDO] | [DADO OMITIDO] |
| AFTER: SQL publicado, /[DADO OMITIDO] | [DADO OMITIDO] |

Diferença AFTER − BEFORE: [DADO OMITIDO].

A receita de julho é negativa e aciona fallback; agosto tem volume zero; setembro aciona receita positiva. No contexto completo, receita total positiva muda o ramo aplicado. Este witness real tem uma Região (Centro-Oeste); não foi encontrado witness nativo adequado com a mistura preferencial entre múltiplas Regiões. Testes controlados cobrem múltiplas Regiões e mistura receita/fallback; esses fixtures não são valores observados do Power BI.

A busca inicial por ID interno foi descartada como prova de filtro nativo: o seletor Item reúne IDs de mesma descrição. A prova final usa os valores exatos Item + Loja acima e confirma tanto o caminho SQL mensal BEFORE quanto o SQL U3M AFTER.

Artefatos: [Gold BEFORE](pbip_c0[DADO OMITIDO]_real_before_2[DADO OMITIDO].json), [SQL publicado AFTER](pbip_c0[DADO OMITIDO]_real_after_2[DADO OMITIDO].json), [DAX fonte](pbip_c0[DADO OMITIDO]_dax_2[DADO OMITIDO].json).

## Implementação e publicação

Dataset virtual novo **[DADO OMITIDO] — nr_pbip_sellout_u3m_interactive**, usado somente por charts **[DADO OMITIDO] Vendas, [DADO OMITIDO] ROI, [DADO OMITIDO] MARKUP**. Combina o SQL mensal verbatim com uma linha auxiliar `row_scope=pbip_c0[DADO OMITIDO]_u3m`. O filtro de escopo é aplicado por query; get_filters do Superset lê form_data compartilhado, portanto não serve para escolher esse escopo auxiliar entre queries de uma mesma requisição. O frontend consome a última query auxiliar apenas com flag opt-in. Ausência desse resultado mantém BLANK, sem retornar ao cálculo mensal antigo.

O dataset [DADO OMITIDO] e chart [DADO OMITIDO] Estoque permanecem exatamente iguais. Dataset [DADO OMITIDO] TVD, [DADO OMITIDO] IVD, [DADO OMITIDO] OSA e [DADO OMITIDO] Giro, metadados do dashboard e definições dos [DADO OMITIDO] marts PBIP permaneceram iguais. Nenhum mart novo ou republicado; nenhum reprocessamento Bronze/Silver/Gold. Apenas metadados desses três charts/dataset e imagem/assets Superset foram atualizados.

Arquivos existentes alterados nesta etapa:

- `superset\bootstrap_overview.py`
- `superset\validate_overview.py`
- `superset\neoretail_bootstrap\pbip_overview\presentation.py`
- `superset\neoretail_bootstrap\pbip_overview\semantics.py`
- `superset\frontend-plugin\plugin-chart-neoretail-kpi\src\buildQuery.js`
- `superset\frontend-plugin\plugin-chart-neoretail-kpi\src\transformProps.js`

Arquivos novos de implementação/teste: `superset/neoretail_bootstrap/pbip_overview/sellout_u3m.py`, `local-engine/tests/test_pbip_c0[DADO OMITIDO]_sellout_u3m.py`, `superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-c0[DADO OMITIDO]-contract.mjs`.

## Gates e regressão

- **[DADO OMITIDO] Python = [DADO OMITIDO] existentes + [DADO OMITIDO] C0[DADO OMITIDO]**. Receita positiva/zero/BLANK/negativa, uma/múltiplas Regiões, NULL Região, mistura de ramos, preço/volume variáveis, fator ao quadrado, MAX independente do Produto, U3M e BLANK. Expected values antigos preservados.
- **[DADO OMITIDO] frontend = [DADO OMITIDO] baseline + [DADO OMITIDO] F1[DADO OMITIDO] + [DADO OMITIDO] F1[DADO OMITIDO]/C0[DADO OMITIDO] + [DADO OMITIDO] C0[DADO OMITIDO]**. Sell-out, Markup e ROI U3M; MTD/anterior; caminho legado; ausência de query auxiliar; C1[DADO OMITIDO] residual.
- **[DADO OMITIDO] comparações de opções**, [DADO OMITIDO] probes RLS de opções, cinco seleções de atividade e busca Loja assíncrona.
- **ChartData default e filtrado: [DADO OMITIDO] charts, zero falhas**. Conversão filtrada quilograma, Bandeira MATEUS SUPERMERCADOS.
- Guest Token/RLS [DADO OMITIDO], overrides e assinatura adulterada: detalhes no artefato de gate abaixo.
- Assets servidos contêm os três markers F1[DADO OMITIDO] e os dois markers C0[DADO OMITIDO].
- Replay SQL: todos os [DADO OMITIDO] campos mensais iguais em [DADO OMITIDO] linhas default, [DADO OMITIDO] filtradas e [DADO OMITIDO] witness; garante MTD e mês anterior preservados.

[Python](pbip_c0[DADO OMITIDO]_python_full_2[DADO OMITIDO].log), [frontend baseline](pbip_c0[DADO OMITIDO]_frontend_base_2[DADO OMITIDO].log), [frontend F1[DADO OMITIDO]](pbip_c0[DADO OMITIDO]_frontend_f1[DADO OMITIDO]_2[DADO OMITIDO].log), [frontend F1[DADO OMITIDO]/C0[DADO OMITIDO]](pbip_c0[DADO OMITIDO]_frontend_new_2[DADO OMITIDO].log), [opções](pbip_c0[DADO OMITIDO]_options_runtime_2[DADO OMITIDO].json), [Guest/RLS](pbip_c0[DADO OMITIDO]_guest_rls_2[DADO OMITIDO].json), [replay SQL](pbip_c0[DADO OMITIDO]_replay_2[DADO OMITIDO].json), [freeze](pbip_c0[DADO OMITIDO]_freeze_2[DADO OMITIDO].json), [assets](pbip_c0[DADO OMITIDO]_deployed_assets_2[DADO OMITIDO].json).

## Performance

Tempos em segundos por chart, incluindo suas queries, e execução sequencial dos oito charts. Não são tempos de renderização de navegador. Baseline anterior é a medição F1[DADO OMITIDO]/C0[DADO OMITIDO] congelada; variação nos charts TVD/IVD não é atribuída a C0[DADO OMITIDO]. Há custo novo real nas consultas auxiliares que reavaliam U3M sobre Gold; sem otimização F1[DADO OMITIDO]/C0[DADO OMITIDO] nesta etapa.

| Contexto/chart | Antes C0[DADO OMITIDO] | Depois C0[DADO OMITIDO] |
|---|---:|---:|
| Default / Vendas | [DADO OMITIDO] | [DADO OMITIDO] |
| Default / MARKUP | [DADO OMITIDO] | [DADO OMITIDO] |
| Default / ROI | [DADO OMITIDO] | [DADO OMITIDO] |
| Default / dashboard | [DADO OMITIDO] | [DADO OMITIDO] |
| Bandeira + kg / Vendas | [DADO OMITIDO] | [DADO OMITIDO] |
| Bandeira + kg / MARKUP | [DADO OMITIDO] | [DADO OMITIDO] |
| Bandeira + kg / ROI | [DADO OMITIDO] | [DADO OMITIDO] |
| Bandeira + kg / dashboard | [DADO OMITIDO] | [DADO OMITIDO] |

## Replay dos três KPIs no frontend real

Mesmo witness Gold e params publicados dos charts, sem valores PBI. Custo U3M total congelado: [DADO OMITIDO]; estoque custo U3M total congelado: [DADO OMITIDO]. Os valores abaixo comprovam apenas a remoção C0[DADO OMITIDO], mantendo os componentes aprovados e causas residuais C1[DADO OMITIDO]/C1[DADO OMITIDO].

| Chart | BEFORE | AFTER | Expected com custo/estoque congelados |
|---|---:|---:|---:|
| [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |

Charts [DADO OMITIDO]/[DADO OMITIDO] em percentuais, chart [DADO OMITIDO] em valor monetário. Todos também confirmam MTD/anterior iguais. [Log do replay frontend Gold](pbip_c0[DADO OMITIDO]_frontend_gold_2[DADO OMITIDO].log).

## Performance por query — replay isolado do snapshot BEFORE

O replay BEFORE usa dataset [DADO OMITIDO] e params congelados, sem editar metadados. AFTER usa dataset [DADO OMITIDO]. Execuções sequenciais, force=True, sem as outras validações rodando; o total desta seção é somente dos três charts, não do dashboard. Há regressão nova C0[DADO OMITIDO] tanto na query auxiliar quanto no caminho mensal envolvido por UNION ALL; o SQL mensal e valores permaneceram iguais, mas seu envelope de execução mudou. Sem atribuir essa diferença a F1[DADO OMITIDO]/C0[DADO OMITIDO] e sem otimizar F1[DADO OMITIDO]/C0[DADO OMITIDO].

| Contexto | Chart | Total BEFORE | Total AFTER | Mensal AFTER | Auxiliar U3M AFTER |
|---|---|---:|---:|---:|---:|
| default | Vendas | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| default | ROI | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| default | MARKUP | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| filtered | Vendas | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| filtered | ROI | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| filtered | MARKUP | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |

O primeiro instrumento AFTER reporta o total dos três charts sob o campo legado total_seconds_sequential; não o confundir com o dashboard de oito charts da seção anterior. [Perf BEFORE default](pbip_c0[DADO OMITIDO]_performance_before_default_2[DADO OMITIDO].log), [BEFORE filtrado](pbip_c0[DADO OMITIDO]_performance_before_filtered_2[DADO OMITIDO].log), [AFTER default](pbip_c0[DADO OMITIDO]_performance_after_default_2[DADO OMITIDO].log), [AFTER filtrado](pbip_c0[DADO OMITIDO]_performance_after_filtered_2[DADO OMITIDO].log).

Guest/RLS: [DADO OMITIDO] probes em seis datasets, inclusive original [DADO OMITIDO] e novo [DADO OMITIDO]; seis MAX(datas), seleções AP e catálogo UF→Bandeira; overrides [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] negados, assinatura adulterada rejeitada. Health final dos serviços: [log](pbip_c0[DADO OMITIDO]_health_2[DADO OMITIDO].log).

## Reclassificação — somente C0[DADO OMITIDO]

| Escopo | MATCH antes/depois | DIFFERENCE antes/depois | UNMAPPED |
|---|---:|---:|---:|
| Estado salvo/contexto explícito | [DADO OMITIDO] → [DADO OMITIDO] | [DADO OMITIDO] → [DADO OMITIDO] | [DADO OMITIDO] |
| Contrato completo | [DADO OMITIDO] → [DADO OMITIDO] | [DADO OMITIDO] → [DADO OMITIDO] | [DADO OMITIDO] |

**NO_PBI_VALUE: [DADO OMITIDO] → [DADO OMITIDO]. Nenhum NUMERIC_MATCH.**

| Par U3M | Causas antes | Causas depois | Estado salvo | Contrato completo |
|---|---|---|---|---|
| MARKUP | C1[DADO OMITIDO], C1[DADO OMITIDO], C0[DADO OMITIDO], F1[DADO OMITIDO]D | C1[DADO OMITIDO], C1[DADO OMITIDO], F1[DADO OMITIDO]D | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| Venda sell out | C0[DADO OMITIDO], F1[DADO OMITIDO]D | F1[DADO OMITIDO]D | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| ROI | C1[DADO OMITIDO], C1[DADO OMITIDO], C0[DADO OMITIDO], F1[DADO OMITIDO]D | C1[DADO OMITIDO], C1[DADO OMITIDO], F1[DADO OMITIDO]D | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |

F1[DADO OMITIDO]D continua individualizada com os caminhos e provas por KPI. F1[DADO OMITIDO]A elegibilidade Item continua UNPROVEN, F1[DADO OMITIDO]B navegação pendente, F1[DADO OMITIDO]C ação de bookmark UNMAPPED; nenhuma dessas causas foi recertificada nesta etapa. Markup/ROI continuam DIFFERENCE devido a C1[DADO OMITIDO]/C1[DADO OMITIDO]. [Classificação completa das [DADO OMITIDO] linhas](pbi_superset_semantic_equivalence_c0[DADO OMITIDO]_after_2[DADO OMITIDO].json).

## Git e preservação

Branch: `feat/osa-industry-certification`. HEAD: `[DADO OMITIDO]d2f5[DADO OMITIDO]b5[DADO OMITIDO]ead1bae9af6d2ef7b7[DADO OMITIDO]f9a4[DADO OMITIDO]ae`; iguais ao snapshot inicial. Sem commit, push, merge, rebase, troca de branch ou alteração de main/PR. Nenhum volume Docker removido ou recriado. O diff abaixo é cumulativo da worktree, incluindo as etapas anteriores e não apenas C0[DADO OMITIDO].

```text
 scripts/publish_lactalis_marts.py                  | [DADO OMITIDO] ++++++++++++-
 superset/Dockerfile                                |  [DADO OMITIDO] +
 superset/bootstrap_overview.py                     | [DADO OMITIDO] ++++++++++++++++------
 .../plugin-chart-neoretail-kpi/src/buildQuery.js   | [DADO OMITIDO] +++-
 .../src/transformProps.js                          | [DADO OMITIDO] +++++++++++--
 superset/validate_overview.py                      | [DADO OMITIDO] ++++++++-
 [DADO OMITIDO] files changed, [DADO OMITIDO] insertions(+), [DADO OMITIDO] deletions(-)
```

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
?? local-engine/tests/fixtures/pbip_f1[DADO OMITIDO]_final_evidence_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_f1[DADO OMITIDO]_selectors_pbip_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_f1[DADO OMITIDO]_c0[DADO OMITIDO]_dax_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_filters_conversion_real_rows_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_lactalis_overview_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_lactalis_real_contract_rows_2[DADO OMITIDO].json
?? local-engine/tests/test_pbip_c0[DADO OMITIDO]_sellout_u3m.py
?? local-engine/tests/test_pbip_f1[DADO OMITIDO]_final_evidence.py
?? local-engine/tests/test_pbip_f1[DADO OMITIDO]_selectors.py
?? local-engine/tests/test_pbip_f1[DADO OMITIDO]_c0[DADO OMITIDO]_daily_context.py
?? local-engine/tests/test_pbip_filter_conversion_contract.py
?? local-engine/tests/test_pbip_lactalis_overview.py
?? superset/diagnose_lactalis_inventory.py
?? superset/frontend-extension/pbipSelectorDependencies.mjs
?? superset/frontend-extension/register-pbip-selectors.mjs
?? superset/frontend-extension/test-pbip-selectors.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-c0[DADO OMITIDO]-contract.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-contract.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-tvd-ivd-contract.mjs
?? superset/neoretail_bootstrap/pbip_overview/
?? superset/profile_lactalis_osa_filtered.py
```
