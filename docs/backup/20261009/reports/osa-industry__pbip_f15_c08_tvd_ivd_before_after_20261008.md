> Cópia para GitHub: números de origem e identificadores numéricos omitidos. Original integral exige backup externo. Não usar esta cópia como fixture ou SQL executável.

# LACTALIS — TVD/IVD F1[DADO OMITIDO]/C0[DADO OMITIDO] BEFORE/AFTER

**F1[DADO OMITIDO] e C0[DADO OMITIDO] corrigidas nos seis pares TVD/IVD. Estado salvo/contexto explícito: [DADO OMITIDO] MATCH, [DADO OMITIDO] DIFFERENCE, [DADO OMITIDO] UNMAPPED. Contrato completo: [DADO OMITIDO] MATCH, [DADO OMITIDO] DIFFERENCE, [DADO OMITIDO] UNMAPPED. NO_PBI_VALUE = [DADO OMITIDO].**

A diferença do contrato completo continua sendo F1[DADO OMITIDO]D; suas provas e classificações não foram alteradas. Nenhum NUMERIC_MATCH. Números e datas de replay abaixo pertencem exclusivamente ao Gold/SQL local, não a uma sessão Power BI.

## Escopo, snapshot e isolamento

Snapshot inicial: pbip_f1[DADO OMITIDO]_c0[DADO OMITIDO]_stage_before_2[DADO OMITIDO].json, contendo git status/diffstat/HEAD/branch antes das edições. Apenas bootstrap_overview.py e pbip_overview/headlines.py mudaram entre [DADO OMITIDO] arquivos existentes. Novos: daily_context.py, test_pbip_f1[DADO OMITIDO]_c0[DADO OMITIDO]_daily_context.py, fixture DAX literal e teste frontend pbip-tvd-ivd-contract.mjs. Todos os testes/expected anteriores preservados.

Calendário, OSA/Perda OSA, conversões, atividade, filtros, CNPJ, AP→Produto, seletores F1[DADO OMITIDO] e frontend de produção intactos. Onze definições de marts inalteradas; metadados de dashboard, IDs e params dos oito charts idênticos. Somente SQL dos datasets [DADO OMITIDO] e [DADO OMITIDO] foi publicado em uma transação de metadata. Nenhum mart novo, refresh ou reprocessamento de Bronze/Silver/Gold.

### Git inicial

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
?? local-engine/tests/fixtures/pbip_filters_conversion_real_rows_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_lactalis_overview_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_lactalis_real_contract_rows_2[DADO OMITIDO].json
?? local-engine/tests/test_pbip_f1[DADO OMITIDO]_final_evidence.py
?? local-engine/tests/test_pbip_f1[DADO OMITIDO]_selectors.py
?? local-engine/tests/test_pbip_filter_conversion_contract.py
?? local-engine/tests/test_pbip_lactalis_overview.py
?? superset/diagnose_lactalis_inventory.py
?? superset/frontend-extension/pbipSelectorDependencies.mjs
?? superset/frontend-extension/register-pbip-selectors.mjs
?? superset/frontend-extension/test-pbip-selectors.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-contract.mjs
?? superset/neoretail_bootstrap/pbip_overview/
?? superset/profile_lactalis_osa_filtered.py
```

```text
 scripts/publish_lactalis_marts.py                  | [DADO OMITIDO] ++++++++++++++-
 superset/Dockerfile                                |  [DADO OMITIDO] +
 superset/bootstrap_overview.py                     | [DADO OMITIDO] ++++++++++++++++------
 .../plugin-chart-neoretail-kpi/src/buildQuery.js   | [DADO OMITIDO] ++-
 .../src/transformProps.js                          | [DADO OMITIDO] ++++++++++--
 superset/validate_overview.py                      | [DADO OMITIDO] +++++++-
 [DADO OMITIDO] files changed, [DADO OMITIDO] insertions(+), [DADO OMITIDO] deletions(-)
```

## DAX exato: medidas e auxiliares

Oito definições rechecadas literalmente contra generated/pbi_lactalis_reference_2[DADO OMITIDO]/NeoRetail Pocket RF.SemanticModel/definition/tables/_Metricas.tmdl; fixture registra fonte, visuais e períodos. Cartões: TVD dac3d0[DADO OMITIDO]b0[DADO OMITIDO]bc5[DADO OMITIDO]d9[DADO OMITIDO]a9[DADO OMITIDO] e IVD [DADO OMITIDO]b0[DADO OMITIDO]a6b8d7[DADO OMITIDO]c7d0[DADO OMITIDO]. Colunas: FATOS_PARTICULAR_TVD_IVD[TVD_SIMPLIFICADO/IVD_SIMPLIFICADO], data [DADO OMITIDO]_0_CALENDARIO[Data]. Nenhuma medida usa COALESCE nem fator de conversão.

### IVD MTD

```dax
CALCULATE(
			   [IVD],
			    '[DADO OMITIDO]_0_CALENDARIO'[M0] = TRUE())
```

### IVD

```dax
CALCULATE(
			    SUM(FATOS_PARTICULAR_TVD_IVD[IVD_SIMPLIFICADO]),
			
			    LASTNONBLANK(
			        '[DADO OMITIDO]_0_CALENDARIO'[Data],
			        CALCULATE(
			            SUM(FATOS_PARTICULAR_TVD_IVD[IVD_SIMPLIFICADO])
			        )
			    ),
			
			    ALL(AP_CONVERSAO),
			
			    FILTER(
			        DIM_LOCAL,
			        NOT DIM_LOCAL[TIPO_LOCAL]
			            IN {"DEPÓSITO", "CD", "LOJA VIRTUAL"}
			    ),
			
			    FILTER(
			        DIM_CATALOGO_LOCAL,
			        NOT DIM_CATALOGO_LOCAL[Tipo local]
			            IN {"DEPÓSITO", "CD", "LOJA VIRTUAL"}
			    )
			)
```

### IVD Mes Ant

```dax
CALCULATE(
			   [IVD],
			    '[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = TRUE())
```

### IVD U3M

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

### TVD MTD

```dax
CALCULATE(
			   [TVD],
			    '[DADO OMITIDO]_0_CALENDARIO'[M0] = TRUE())
```

### TVD

```dax
CALCULATE(
			    SUM(FATOS_PARTICULAR_TVD_IVD[TVD_SIMPLIFICADO]),
			
			    LASTNONBLANK(
			        '[DADO OMITIDO]_0_CALENDARIO'[Data],
			        CALCULATE(
			            SUM(FATOS_PARTICULAR_TVD_IVD[TVD_SIMPLIFICADO])
			        )
			    ),
			
			    ALL(AP_CONVERSAO),
			
			    FILTER(
			        DIM_LOCAL,
			        NOT DIM_LOCAL[TIPO_LOCAL]
			            IN {"DEPÓSITO", "CD", "LOJA VIRTUAL"}
			    ),
			
			    FILTER(
			        DIM_CATALOGO_LOCAL,
			        NOT DIM_CATALOGO_LOCAL[Tipo local]
			            IN {"DEPÓSITO", "CD", "LOJA VIRTUAL"}
			    )
			)
```

### TVD Mes Ant

```dax
CALCULATE(
			   [TVD],
			    '[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = TRUE())
```

### TVD U3M

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

## Ordem CALCULATE: date_context e value_context

A) LASTNONBLANK é um argumento de filtro avaliado no contexto de entrada da medida, já com o período do CALCULATE externo. Sua expressão é CALCULATE(SUM(coluna simplificada)), que aplica a transição para a data candidata. AP, página e dimensões permanecem nesse universo.

B) Os filtros irmãos FILTER(DIM_LOCAL, NOT tipo IN ...) e FILTER(DIM_CATALOGO_LOCAL, NOT tipo IN ...) também são avaliados independentemente no contexto de entrada. A exclusão não-store desses argumentos não é antecipada para LASTNONBLANK.

C) ALL(AP_CONVERSAO) modifica o contexto da expressão principal SUM, depois que os argumentos de filtro foram avaliados. A data escolhida e filtros de dimensões permanecem; AP é removido nessa soma. Essa separação segue a [ordem de avaliação dos argumentos CALCULATE](https://www.sqlbi.com/articles/order-of-evaluation-in-calculate-parameters/). LASTNONBLANK escolhe a última data cuja expressão não é BLANK, conforme a [documentação Microsoft](https://learn.microsoft.com/en-us/dax/lastnonblank-function-dax).

```mermaid
flowchart TD
 IN[Período + página + dimensões + AP] --> DC[date_context SUM nullable por data]
 DC --> CH[Última data não BLANK por mês e KPI]
 IN --> VF[Filtros irmãos Local/Catálogo avaliados]
 CH --> VC[value_context data escolhida]
 VF --> VC
 AP[ALL AP: remove somente da soma principal] --> VC
 VC --> SUM[SUM nullable sem fator de conversão]
 SUM --> U3M[M-[DADO OMITIDO] + M-[DADO OMITIDO] + M-[DADO OMITIDO] / [DADO OMITIDO]]
```

No SQL, remove_filter=True consome o filtro externo Superset, mas captura sua seleção em incoming_measure/selected e a aplica explicitamente em date_context. Não significa remover AP desse universo. value_context não recebe a condição AP. Produto ainda filtra pelo campo original; não altera MAX taxa e não entra nenhum conversion_rate.

## U3M

DAX real usa M1/M2/M3, cada qual CALCULATE([TVD/IVD], M-i=TRUE), depois DIVIDE(M1+M2+M3,[DADO OMITIDO]). Portanto são três escolhas de data por mês; não uma última data sobre toda U3M e não a soma diária. O dataset entrega uma linha por mês na data selecionada de cada KPI, mantendo semantic_period=month_last_nonblank e direct_average já existentes. Meses sem valor não alteram o denominador. Todos BLANK → BLANK; pelo menos um valor zero → zero onde a soma for zero. O frontend de produção não mudou.

## BLANK/zero — casos controlados

| Valores na data candidata | DAX SUM | SQL antigo SUM(COALESCE) | SQL corrigido SUM | Candidata LASTNONBLANK |
|---|---|---|---|---|
| BLANK, BLANK | BLANK | [DADO OMITIDO] | NULL | não |
| BLANK, [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | sim |
| [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | sim |
| BLANK, positivo | positivo | positivo | positivo | sim |
| nenhuma linha | BLANK | NULL | NULL | não |
| uma linha NULL | BLANK | [DADO OMITIDO] | NULL | não |

Cada caso foi executado contra SQL gerado de produção em SQLite efêmero. Casts PostgreSQL são removidos somente no adaptador de teste; agregações/FILTER/CTEs relacionais continuam executadas. O teste de filtro irmão não-store comprova que uma data pode ser escolhida primeiro e a soma final ser BLANK após a exclusão: não retroceder indevidamente para outra data. TVD e IVD escolhem datas independentemente.

## Witness BEFORE controlado e AFTER

Dados controlados, sem inserir em Gold: A(unidade) em [DADO OMITIDO]/[DADO OMITIDO] vale [DADO OMITIDO]; B(quilograma) em [DADO OMITIDO]/[DADO OMITIDO] vale [DADO OMITIDO] e em [DADO OMITIDO]/[DADO OMITIDO] vale [DADO OMITIDO]. SQL antigo global escolhe [DADO OMITIDO]/[DADO OMITIDO] para todos. Novo com unidade escolhe [DADO OMITIDO]/[DADO OMITIDO] e soma [DADO OMITIDO] (A+B, ALL AP). Novo com quilograma escolhe [DADO OMITIDO]/[DADO OMITIDO] e soma [DADO OMITIDO]. O fator artificial [DADO OMITIDO] na dimensão de teste não entra no resultado. Litro possui dado em [DADO OMITIDO]/[DADO OMITIDO]; sem seleção usa o universo de modos permitido pela página. Cases incluem datas iguais, modo sem dado no último dia global, Produto/Rede/Bandeira, domínio do calendário e U3M com mês BLANK.

## Witnesses reais BEFORE/AFTER — replay Gold

BEFORE é reexecução do SQL persistido capturado no snapshot, contra o mesmo Gold existente. Não é reimplantação do pipeline antigo nem valor fabricado de Power BI. AFTER executa o novo SQL completo.

### F1[DADO OMITIDO]: Item/Local com dados e ausência de chave litro

Item [DADO OMITIDO] — [DADO OMITIDO] - Iog Mor C/ Confete Bob Esponja Cp [DADO OMITIDO]G; Local [DADO OMITIDO] — B6[DADO OMITIDO] - B6[DADO OMITIDO] ITUMBIARA. Contexto explícito Item+Loja igual nos três modos. Este replay não certifica se a UI PBIP permitiria uma seleção persistida cuja opção fica indisponível; esse comportamento continua em F1[DADO OMITIDO].

| KPI | AP | Última data SQL antigo | Última data SQL novo | Linhas mensais novas |
|---|---|---|---|---:|
| tvd | unidade | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO] |
| tvd | quilograma | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO] |
| tvd | litro | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | BLANK | [DADO OMITIDO] |
| ivd | unidade | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO] |
| ivd | quilograma | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | [DADO OMITIDO] |
| ivd | litro | [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | BLANK | [DADO OMITIDO] |

Artefato com SQL renderizado, filtros e linhas completas: pbip_f1[DADO OMITIDO]_c0[DADO OMITIDO]_real_f1[DADO OMITIDO]_replay_2[DADO OMITIDO].json. O antigo ignora AP ao escolher data; o novo elimina a candidata quando litro não possui chave no contexto deste Item.

### C0[DADO OMITIDO]: linhas simplificadas BLANK

Item [DADO OMITIDO] — [DADO OMITIDO] - Iogurte Liquido Morang Btv Cx8Gf1[DADO OMITIDO]G; Local [DADO OMITIDO] — [DADO OMITIDO] - SAVEGNAGO LOJA [DADO OMITIDO]. Linha real de [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] [DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO] contém TVD/IVD NULL. No recorte completo Item+Loja, SQL antigo produz [DADO OMITIDO] dias zero para cada KPI/modo testado; SQL novo não encontra última data não BLANK e retorna ausência.

Seis probes unidade/quilograma/litro × TVD/IVD passaram. Fonte: pbip_f1[DADO OMITIDO]_c0[DADO OMITIDO]_real_replay_2[DADO OMITIDO].json. É prova SQL/Gold de C0[DADO OMITIDO], não NUMERIC_MATCH/DIFERENCE Power BI.

## SQL alterado e publicação

daily_context.py gera dois universos separados. selected_dates calcula MAX(data) FILTER(WHERE tvd_date_sum IS NOT NULL) ou ivd_date_sum, agrupado por mês. value_context une somente a data escolhida, mantém filtros dimensionais e aplica exclusões não-store. SUM nullable em ambos os contextos. Os contadores de tarefas preservam expressões/escopo existentes; não são reinterpretados como os seis KPIs desta etapa.

headlines.headline_semantic_sql(metric) delega a esse módulo; bootstrap passa tvd/ivd explicitamente. headline_detail_sql antigo foi preservado para compatibility/replay, mas não é mais usado pela entrada persistida dos dois datasets. nr_pbip_daily_headlines físico fica intacto: usado apenas como schema probe no bootstrap; suas agregações antigas não servem mais os valores TVD/IVD.

### SQL TVD publicado (IVD muda o seletor *_date_sum)

```sql
{% set incoming_measure = get_filters('nm_measure', remove_filter=True) %}
{% set selected = incoming_measure[[DADO OMITIDO]].get('val', []) if incoming_measure|length == [DADO OMITIDO] else [] %}
WITH date_context AS MATERIALIZED (
 SELECT f.id_time::date AS data, f.id_customer,
        SUM(f.tvd_simplificado)::float8 AS tvd_date_sum,
        SUM(f.ivd_simplificado)::float8 AS ivd_date_sum
 FROM gold.fato_ivd_tvd f
 LEFT JOIN gold.dim_itens i ON i.id_customer=f.id_customer AND CAST(i.id_item AS text)=CAST(f.id_item AS text)
 WHERE f.id_customer=[DADO OMITIDO] AND EXISTS (
 SELECT [DADO OMITIDO] FROM gold.dim_local pl
 WHERE pl.id_customer=f.id_customer AND pl.id_location=f.id_location
   AND pl.rede IS NOT NULL
{% for filter in get_filters('uf', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pl.uf IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pl.uf IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pl.uf NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pl.uf IS NULL{% endif %}){% if none in values %} AND pl.uf IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('cidade', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pl.cidade IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pl.cidade IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pl.cidade NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pl.cidade IS NULL{% endif %}){% if none in values %} AND pl.cidade IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('tipo_local', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pl.tipo_local IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pl.tipo_local IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pl.tipo_local NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pl.tipo_local IS NULL{% endif %}){% if none in values %} AND pl.tipo_local IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('loja', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pl.loja IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pl.loja IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pl.loja NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pl.loja IS NULL{% endif %}){% if none in values %} AND pl.loja IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('regiao', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pl.regiao IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pl.regiao IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pl.regiao NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pl.regiao IS NULL{% endif %}){% if none in values %} AND pl.regiao IS NOT NULL{% endif %}
{% endif %}
{% endfor %} 
   AND EXISTS (
     SELECT [DADO OMITIDO] FROM gold.dim_catalogo_local pc
     WHERE pc.id_customer=pl.id_customer AND pc.cnpj IS NOT DISTINCT FROM pl.cnpj
       AND pc.rede <> 'GPA'
{% for filter in get_filters('rede', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pc.rede IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pc.rede IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pc.rede NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pc.rede IS NULL{% endif %}){% if none in values %} AND pc.rede IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('bandeira', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pc.bandeira IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pc.bandeira IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pc.bandeira NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pc.bandeira IS NULL{% endif %}){% if none in values %} AND pc.bandeira IS NOT NULL{% endif %}
{% endif %}
{% endfor %} 
       AND EXISTS (SELECT [DADO OMITIDO] FROM gold.dim_local ac
                   WHERE ac.id_customer=pc.id_customer AND ac.id_retailer=pc.id_retailer)
   )
)
{% for filter in get_filters('item', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}i.item IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR i.item IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}i.item NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR i.item IS NULL{% endif %}){% if none in values %} AND i.item IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('descricao_marca', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}i.descricao_marca IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR i.descricao_marca IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}i.descricao_marca NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR i.descricao_marca IS NULL{% endif %}){% if none in values %} AND i.descricao_marca IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('hierarquia_1', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}i.hierarquia_1 IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR i.hierarquia_1 IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}i.hierarquia_1 NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR i.hierarquia_1 IS NULL{% endif %}){% if none in values %} AND i.hierarquia_1 IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('hierarquia_2', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}i.hierarquia_2 IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR i.hierarquia_2 IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}i.hierarquia_2 NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR i.hierarquia_2 IS NULL{% endif %}){% if none in values %} AND i.hierarquia_2 IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('hierarquia_3', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}i.hierarquia_3 IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR i.hierarquia_3 IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}i.hierarquia_3 NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR i.hierarquia_3 IS NULL{% endif %}){% if none in values %} AND i.hierarquia_3 IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('tp_activity_level', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}f.tp_activity_level IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR f.tp_activity_level IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}f.tp_activity_level NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR f.tp_activity_level IS NULL{% endif %}){% if none in values %} AND f.tp_activity_level IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
 AND EXISTS (SELECT [DADO OMITIDO] FROM gold.dim_itens ci
 JOIN gold.dim_conversao pbip_conv ON pbip_conv.id_customer=ci.id_customer AND CAST(pbip_conv.id_item AS TEXT)=CAST(ci.id_item AS TEXT)
 WHERE ci.id_customer=f.id_customer AND CAST(ci.id_item AS TEXT)=CAST(f.id_item AS TEXT) {% if selected %} AND pbip_conv.nm_measure IN {{ selected | where_in }}{% endif %} AND pbip_conv.nm_measure <> 'valor')
 AND EXISTS (SELECT [DADO OMITIDO] FROM gold.nr_pbip_calendar cal WHERE cal.id_customer=f.id_customer AND cal.data=f.id_time::date)
 GROUP BY f.id_time::date,f.id_customer
), selected_dates AS (
 SELECT id_customer,date_trunc('month',data)::date AS month,
        MAX(data) FILTER (WHERE tvd_date_sum IS NOT NULL) AS data
 FROM date_context GROUP BY id_customer,date_trunc('month',data)::date
), value_context AS (
 SELECT f.id_time::date AS data,f.id_customer,
        SUM(f.tvd_simplificado)::float8 AS tvd,
        SUM(f.ivd_simplificado)::float8 AS ivd
 FROM gold.fato_ivd_tvd f
 JOIN selected_dates chosen ON chosen.id_customer=f.id_customer AND chosen.data=f.id_time::date
 LEFT JOIN gold.dim_itens i ON i.id_customer=f.id_customer AND CAST(i.id_item AS text)=CAST(f.id_item AS text)
 WHERE f.id_customer=[DADO OMITIDO] AND EXISTS (
 SELECT [DADO OMITIDO] FROM gold.dim_local pl
 WHERE pl.id_customer=f.id_customer AND pl.id_location=f.id_location
   AND pl.rede IS NOT NULL
{% for filter in get_filters('uf', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pl.uf IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pl.uf IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pl.uf NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pl.uf IS NULL{% endif %}){% if none in values %} AND pl.uf IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('cidade', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pl.cidade IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pl.cidade IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pl.cidade NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pl.cidade IS NULL{% endif %}){% if none in values %} AND pl.cidade IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('tipo_local', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pl.tipo_local IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pl.tipo_local IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pl.tipo_local NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pl.tipo_local IS NULL{% endif %}){% if none in values %} AND pl.tipo_local IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('loja', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pl.loja IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pl.loja IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pl.loja NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pl.loja IS NULL{% endif %}){% if none in values %} AND pl.loja IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('regiao', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pl.regiao IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pl.regiao IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pl.regiao NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pl.regiao IS NULL{% endif %}){% if none in values %} AND pl.regiao IS NOT NULL{% endif %}
{% endif %}
{% endfor %}  AND (pl.tipo_local IS NULL OR pl.tipo_local NOT IN ('DEPÓSITO','CD','LOJA VIRTUAL'))
   AND EXISTS (
     SELECT [DADO OMITIDO] FROM gold.dim_catalogo_local pc
     WHERE pc.id_customer=pl.id_customer AND pc.cnpj IS NOT DISTINCT FROM pl.cnpj
       AND pc.rede <> 'GPA'
{% for filter in get_filters('rede', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pc.rede IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pc.rede IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pc.rede NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pc.rede IS NULL{% endif %}){% if none in values %} AND pc.rede IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('bandeira', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pc.bandeira IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pc.bandeira IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pc.bandeira NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pc.bandeira IS NULL{% endif %}){% if none in values %} AND pc.bandeira IS NOT NULL{% endif %}
{% endif %}
{% endfor %}  AND (pc.tipo_local IS NULL OR pc.tipo_local NOT IN ('DEPÓSITO','CD','LOJA VIRTUAL'))
       AND EXISTS (SELECT [DADO OMITIDO] FROM gold.dim_local ac
                   WHERE ac.id_customer=pc.id_customer AND ac.id_retailer=pc.id_retailer)
   )
)
{% for filter in get_filters('item', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}i.item IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR i.item IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}i.item NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR i.item IS NULL{% endif %}){% if none in values %} AND i.item IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('descricao_marca', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}i.descricao_marca IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR i.descricao_marca IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}i.descricao_marca NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR i.descricao_marca IS NULL{% endif %}){% if none in values %} AND i.descricao_marca IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('hierarquia_1', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}i.hierarquia_1 IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR i.hierarquia_1 IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}i.hierarquia_1 NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR i.hierarquia_1 IS NULL{% endif %}){% if none in values %} AND i.hierarquia_1 IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('hierarquia_2', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}i.hierarquia_2 IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR i.hierarquia_2 IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}i.hierarquia_2 NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR i.hierarquia_2 IS NULL{% endif %}){% if none in values %} AND i.hierarquia_2 IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('hierarquia_3', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}i.hierarquia_3 IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR i.hierarquia_3 IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}i.hierarquia_3 NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR i.hierarquia_3 IS NULL{% endif %}){% if none in values %} AND i.hierarquia_3 IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('tp_activity_level', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}f.tp_activity_level IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR f.tp_activity_level IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}f.tp_activity_level NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR f.tp_activity_level IS NULL{% endif %}){% if none in values %} AND f.tp_activity_level IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
 GROUP BY f.id_time::date,f.id_customer
), latest AS (
 SELECT id_customer,MAX(data) AS data FROM selected_dates WHERE data IS NOT NULL GROUP BY id_customer
), tasks AS (
 SELECT o.id_customer,
 COUNT(o.id_item) FILTER(WHERE o.regra_critico='CRITICO' AND COALESCE(o.tvd,[DADO OMITIDO])>[DADO OMITIDO])::bigint AS itens_criticos_tvd,
 COUNT(o.id_item) FILTER(WHERE o.regra_critico='F' AND COALESCE(o.tvd,[DADO OMITIDO])>[DADO OMITIDO])::bigint AS itens_risco_tvd,
 COUNT(o.id_item) FILTER(WHERE o.regra_critico='CRITICO' AND COALESCE(o.ivd,[DADO OMITIDO])>[DADO OMITIDO])::bigint AS itens_criticos_ivd,
 COUNT(o.id_item) FILTER(WHERE o.regra_critico='F' AND COALESCE(o.ivd,[DADO OMITIDO])>[DADO OMITIDO])::bigint AS itens_risco_ivd
 FROM gold.calculo_oportunidades o
 LEFT JOIN gold.dim_itens i ON i.id_customer=o.id_customer AND i.id_item=o.id_item
 WHERE o.id_customer=[DADO OMITIDO] AND EXISTS (
 SELECT [DADO OMITIDO] FROM gold.dim_local pl
 WHERE pl.id_customer=o.id_customer AND pl.id_location=o.id_location
   AND pl.rede IS NOT NULL
{% for filter in get_filters('uf', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pl.uf IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pl.uf IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pl.uf NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pl.uf IS NULL{% endif %}){% if none in values %} AND pl.uf IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('cidade', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pl.cidade IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pl.cidade IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pl.cidade NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pl.cidade IS NULL{% endif %}){% if none in values %} AND pl.cidade IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('tipo_local', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pl.tipo_local IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pl.tipo_local IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pl.tipo_local NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pl.tipo_local IS NULL{% endif %}){% if none in values %} AND pl.tipo_local IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('loja', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pl.loja IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pl.loja IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pl.loja NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pl.loja IS NULL{% endif %}){% if none in values %} AND pl.loja IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('regiao', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pl.regiao IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pl.regiao IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pl.regiao NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pl.regiao IS NULL{% endif %}){% if none in values %} AND pl.regiao IS NOT NULL{% endif %}
{% endif %}
{% endfor %}  AND (pl.tipo_local IS NULL OR pl.tipo_local NOT IN ('DEPÓSITO','CD','LOJA VIRTUAL'))
   AND EXISTS (
     SELECT [DADO OMITIDO] FROM gold.dim_catalogo_local pc
     WHERE pc.id_customer=pl.id_customer AND pc.cnpj IS NOT DISTINCT FROM pl.cnpj
       AND pc.rede <> 'GPA'
{% for filter in get_filters('rede', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pc.rede IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pc.rede IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pc.rede NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pc.rede IS NULL{% endif %}){% if none in values %} AND pc.rede IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('bandeira', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}pc.bandeira IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR pc.bandeira IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}pc.bandeira NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR pc.bandeira IS NULL{% endif %}){% if none in values %} AND pc.bandeira IS NOT NULL{% endif %}
{% endif %}
{% endfor %}  AND (pc.tipo_local IS NULL OR pc.tipo_local NOT IN ('DEPÓSITO','CD','LOJA VIRTUAL'))
       AND EXISTS (SELECT [DADO OMITIDO] FROM gold.dim_local ac
                   WHERE ac.id_customer=pc.id_customer AND ac.id_retailer=pc.id_retailer)
   )
)
{% for filter in get_filters('item', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}i.item IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR i.item IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}i.item NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR i.item IS NULL{% endif %}){% if none in values %} AND i.item IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('descricao_marca', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}i.descricao_marca IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR i.descricao_marca IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}i.descricao_marca NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR i.descricao_marca IS NULL{% endif %}){% if none in values %} AND i.descricao_marca IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('hierarquia_1', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}i.hierarquia_1 IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR i.hierarquia_1 IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}i.hierarquia_1 NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR i.hierarquia_1 IS NULL{% endif %}){% if none in values %} AND i.hierarquia_1 IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('hierarquia_2', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}i.hierarquia_2 IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR i.hierarquia_2 IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}i.hierarquia_2 NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR i.hierarquia_2 IS NULL{% endif %}){% if none in values %} AND i.hierarquia_2 IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('hierarquia_3', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}i.hierarquia_3 IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR i.hierarquia_3 IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}i.hierarquia_3 NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR i.hierarquia_3 IS NULL{% endif %}){% if none in values %} AND i.hierarquia_3 IS NOT NULL{% endif %}
{% endif %}
{% endfor %}
{% for filter in get_filters('tp_activity_level', remove_filter=True) %}
{% set values = filter.get('val', []) %}
{% set nonnull = values | reject('none') | list %}
{% if filter.get('op') == 'IN' %}
 AND ({% if nonnull %}o.max_tp_activity_level IN {{ nonnull | where_in }}{% else %}FALSE{% endif %}{% if none in values %} OR o.max_tp_activity_level IS NULL{% endif %})
{% elif filter.get('op') == 'NOT IN' %}
 AND ({% if nonnull %}o.max_tp_activity_level NOT IN {{ nonnull | where_in }}{% else %}TRUE{% endif %}{% if none not in values %} OR o.max_tp_activity_level IS NULL{% endif %}){% if none in values %} AND o.max_tp_activity_level IS NOT NULL{% endif %}
{% endif %}
{% endfor %} GROUP BY o.id_customer
)
 SELECT d.data,d.id_customer,v.tvd,v.ivd,
 CASE WHEN d.data=l.data THEN COALESCE(t.itens_criticos_tvd,[DADO OMITIDO]) ELSE [DADO OMITIDO] END AS itens_criticos_tvd,
 CASE WHEN d.data=l.data THEN COALESCE(t.itens_risco_tvd,[DADO OMITIDO]) ELSE [DADO OMITIDO] END AS itens_risco_tvd,
 CASE WHEN d.data=l.data THEN COALESCE(t.itens_criticos_ivd,[DADO OMITIDO]) ELSE [DADO OMITIDO] END AS itens_criticos_ivd,
 CASE WHEN d.data=l.data THEN COALESCE(t.itens_risco_ivd,[DADO OMITIDO]) ELSE [DADO OMITIDO] END AS itens_risco_ivd,
 NULL::text AS rede,NULL::text AS bandeira,NULL::text AS uf,NULL::text AS cidade,NULL::text AS tipo_local,NULL::text AS loja,NULL::text AS regiao,NULL::text AS item,NULL::text AS descricao_marca,NULL::text AS hierarquia_1,NULL::text AS hierarquia_2,NULL::text AS hierarquia_3,NULL::text AS tp_activity_level
 FROM selected_dates d LEFT JOIN value_context v ON v.id_customer=d.id_customer AND v.data=d.data
 LEFT JOIN latest l ON l.id_customer=d.id_customer LEFT JOIN tasks t ON t.id_customer=d.id_customer
 WHERE d.data IS NOT NULL
```

Os dois SQLs completos e BEFORE estão em pbip_f1[DADO OMITIDO]_c0[DADO OMITIDO]_dataset_publication_2[DADO OMITIDO].json. Publicação restrita: nr_tvd_daily_interactive id=[DADO OMITIDO] e nr_ivd_daily_interactive id=[DADO OMITIDO]. Nenhum chart criado ou ROI MTD adicionado.

## Testes e gates finais

| Gate | Resultado |
|---|---|
| Python completo | [DADO OMITIDO] PASS = [DADO OMITIDO] preservados + [DADO OMITIDO] novos |
| Frontend completo | [DADO OMITIDO] PASS = [DADO OMITIDO] + [DADO OMITIDO] F1[DADO OMITIDO] + [DADO OMITIDO] TVD/IVD |
| Opções F1[DADO OMITIDO] | [DADO OMITIDO] PASS; zero missing/extra/duplicatas |
| Isolamento opções | [DADO OMITIDO] overrides tenant recusados |
| Atividades → códigos KPI | cinco probes preservados |
| CNPJ Local [DADO OMITIDO] | preservado |
| ChartData default/filtrado | oito charts em cada; zero falhas |
| Guest/RLS [DADO OMITIDO] | [DADO OMITIDO] probes KPI; overrides [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO]; assinatura adulterada rejeitada |
| Replay real | seis probes F1[DADO OMITIDO] + seis C0[DADO OMITIDO] PASS |
| Snapshot | seis demais charts e seus datasets, params/IDs dos oito charts, F1[DADO OMITIDO] e onze marts intactos |

Logs prefixados pbip_f1[DADO OMITIDO]_c0[DADO OMITIDO]_* preservados. Novos testes verificam SQL executável e DAX literal, não alteram expected values antigos. Sem execução da sessão Power BI viva; NO_PBI_VALUE permanece [DADO OMITIDO].

## Performance e limitação material

Medição isolada default: [DADO OMITIDO]s; inicial após correção: [DADO OMITIDO]s; baseline anterior: [DADO OMITIDO]s. Filtrado: [DADO OMITIDO]s; baseline anterior: [DADO OMITIDO]s. Medidas locais, sem garantir estabilidade entre execuções.

**O default ficou substancialmente mais lento.** O antigo usava totals de nr_pbip_daily_headlines, que perdiam AP/BLANK. O novo consulta fato_ivd_tvd para date_context e novamente para value_context nas datas escolhidas. Estas são as queries causadoras do custo; SQL completo está no artefato de publicação. Não foi sacrificada equivalência nem realizada otimização ampla/mart adicional.

| Execução | Chart | Dataset | segundos | Linhas |
|---|---|---:|---:|---|
| default_initial | TVD - Pré-ruptura | [DADO OMITIDO] | [DADO OMITIDO] | [[DADO OMITIDO]] |
| default_initial | IVD - Excesso | [DADO OMITIDO] | [DADO OMITIDO] | [[DADO OMITIDO]] |
| default_isolated | TVD - Pré-ruptura | [DADO OMITIDO] | [DADO OMITIDO] | [[DADO OMITIDO]] |
| default_isolated | IVD - Excesso | [DADO OMITIDO] | [DADO OMITIDO] | [[DADO OMITIDO]] |
| filtered | TVD - Pré-ruptura | [DADO OMITIDO] | [DADO OMITIDO] | [[DADO OMITIDO]] |
| filtered | IVD - Excesso | [DADO OMITIDO] | [DADO OMITIDO] | [[DADO OMITIDO]] |

## Classificação dos seis pares

| KPI | Período | Causas antes | Causas depois | Estado salvo antes → depois | Completo depois |
|---|---|---|---|---|---|
| IVD - Excesso | MTD | F1[DADO OMITIDO],C0[DADO OMITIDO],F1[DADO OMITIDO]D | F1[DADO OMITIDO]D | DIFFERENCE → MATCH | DIFFERENCE |
| IVD - Excesso | Mês anterior | F1[DADO OMITIDO],C0[DADO OMITIDO],F1[DADO OMITIDO]D | F1[DADO OMITIDO]D | DIFFERENCE → MATCH | DIFFERENCE |
| IVD - Excesso | Média U3M | F1[DADO OMITIDO],C0[DADO OMITIDO],F1[DADO OMITIDO]D | F1[DADO OMITIDO]D | DIFFERENCE → MATCH | DIFFERENCE |
| TVD - Pré-ruptura | MTD | F1[DADO OMITIDO],C0[DADO OMITIDO],F1[DADO OMITIDO]D | F1[DADO OMITIDO]D | DIFFERENCE → MATCH | DIFFERENCE |
| TVD - Pré-ruptura | Mês anterior | F1[DADO OMITIDO],C0[DADO OMITIDO],F1[DADO OMITIDO]D | F1[DADO OMITIDO]D | DIFFERENCE → MATCH | DIFFERENCE |
| TVD - Pré-ruptura | Média U3M | F1[DADO OMITIDO],C0[DADO OMITIDO],F1[DADO OMITIDO]D | F1[DADO OMITIDO]D | DIFFERENCE → MATCH | DIFFERENCE |

| Escopo | Etapa | MATCH | DIFFERENCE | UNMAPPED | NO_PBI_VALUE |
|---|---|---:|---:|---:|---:|
| Salvo/contexto explícito | antes | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| Salvo/contexto explícito | depois | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| Contrato completo | antes | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| Contrato completo | depois | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |

As outras [DADO OMITIDO] linhas foram preservadas integralmente. Para as seis afetadas, F1[DADO OMITIDO]A/B/C/D permanecem exatamente como no JSON anterior; F1[DADO OMITIDO]D não apaga MATCH do contexto salvo. C0[DADO OMITIDO]/C1[DADO OMITIDO]/C1[DADO OMITIDO] não foram corrigidas ou removidas. ROI MTD continua UNMAPPED. JSON completo: pbi_superset_semantic_equivalence_f1[DADO OMITIDO]_c0[DADO OMITIDO]_after_2[DADO OMITIDO].json.

## Git final

```text
 scripts/publish_lactalis_marts.py                  | [DADO OMITIDO] ++++++++++++++-
 superset/Dockerfile                                |  [DADO OMITIDO] +
 superset/bootstrap_overview.py                     | [DADO OMITIDO] ++++++++++++++++------
 .../plugin-chart-neoretail-kpi/src/buildQuery.js   | [DADO OMITIDO] ++-
 .../src/transformProps.js                          | [DADO OMITIDO] ++++++++++--
 superset/validate_overview.py                      | [DADO OMITIDO] +++++++-
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
?? local-engine/tests/test_pbip_f1[DADO OMITIDO]_final_evidence.py
?? local-engine/tests/test_pbip_f1[DADO OMITIDO]_selectors.py
?? local-engine/tests/test_pbip_f1[DADO OMITIDO]_c0[DADO OMITIDO]_daily_context.py
?? local-engine/tests/test_pbip_filter_conversion_contract.py
?? local-engine/tests/test_pbip_lactalis_overview.py
?? superset/diagnose_lactalis_inventory.py
?? superset/frontend-extension/pbipSelectorDependencies.mjs
?? superset/frontend-extension/register-pbip-selectors.mjs
?? superset/frontend-extension/test-pbip-selectors.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-contract.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-tvd-ivd-contract.mjs
?? superset/neoretail_bootstrap/pbip_overview/
?? superset/profile_lactalis_osa_filtered.py
```

Diffstat tracked não inclui o pacote/testes untracked; snapshot inicial distingue trabalho anterior desta etapa. Os scripts diagnose_lactalis_inventory.py e profile_lactalis_osa_filtered.py continuam untracked.

Branch feat/osa-industry-certification; HEAD [DADO OMITIDO]d2f5[DADO OMITIDO]b5[DADO OMITIDO]ead1bae9af6d2ef7b7[DADO OMITIDO]f9a4[DADO OMITIDO]ae. Nenhum commit, push, merge, rebase, troca de branch, alteração da main ou da PR. PR não modificada. Nenhuma limpeza, remoção de arquivo ou operação sobre volumes Docker.
