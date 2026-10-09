> Cópia para GitHub: números de origem e identificadores numéricos omitidos. Original integral exige backup externo. Não usar esta cópia como fixture ou SQL executável.

# C1[DADO OMITIDO] — ROI / Markup — LACTALIS [DADO OMITIDO] — BEFORE / AFTER

C1[DADO OMITIDO] corrigida exclusivamente no guard condicional PBIP, compilada e ativa nos charts [DADO OMITIDO] e [DADO OMITIDO]. BLANK continua BLANK nos componentes. Classificação conservadora do estado salvo/contextos explícitos: **[DADO OMITIDO] MATCH / [DADO OMITIDO] DIFFERENCE / [DADO OMITIDO] UNMAPPED**; não foi forçado [DADO OMITIDO] MATCH. A diferença anual adicional abaixo ficou documentada, sem correção. Contrato completo: **[DADO OMITIDO] MATCH / [DADO OMITIDO] DIFFERENCE / [DADO OMITIDO] UNMAPPED**. **[DADO OMITIDO] NO_PBI_VALUE**; nenhum NUMERIC_MATCH.

## Referência primária: DAX literal e fechamento

Fonte atual do ZIP/PBIP: `generated\pbi_lactalis_reference_2[DADO OMITIDO]\NeoRetail Pocket RF.SemanticModel\definition\tables\_Metricas.tmdl`. SHA-[DADO OMITIDO] `c5[DADO OMITIDO]c0fa2[DADO OMITIDO]f7a0[DADO OMITIDO]f4[DADO OMITIDO]d3[DADO OMITIDO]c9bc0[DADO OMITIDO]c2a8[DADO OMITIDO]eb9[DADO OMITIDO]caa` verificado antes de editar; as [DADO OMITIDO] definições literais conferem com o TMDL atual. ROI MTD aparece apenas como definição de referência; permanece UNMAPPED, sem criar visual ou medida nova.

### Venda Custo

```dax
SUMX(
			    FATOS_PARTICULAR_HISTORICO,
			    FATOS_PARTICULAR_HISTORICO[VOLUME_UNIDADES]*
			    FATOS_PARTICULAR_HISTORICO[AVG_PRICE_COST])
```

### Venda Custo MTD

```dax
calculate([Venda Custo], all(AP_CONVERSAO[nm_measure]),'[DADO OMITIDO]_0_CALENDARIO'[M0] = True)
```

### Venda Custo Mes Ant

```dax
calculate([Venda Custo], all(AP_CONVERSAO[nm_measure]),'[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = True)
```

### Venda Custo U3M

```dax
divide(calculate([Venda Custo], all(AP_CONVERSAO[nm_measure]), '[DADO OMITIDO]_0_CALENDARIO'[U3M] = True),[DADO OMITIDO])
```

### Estoque Custo

```dax
SUMX(
			    FATOS_PARTICULAR_HISTORICO,
			    FATOS_PARTICULAR_HISTORICO[ESTOQUE_MEDIO]*
			    FATOS_PARTICULAR_HISTORICO[AVG_PRICE_COST])
```

### Estoque Custo MTD

```dax
calculate([Estoque Custo], '[DADO OMITIDO]_0_CALENDARIO'[M0] = True)
```

### Estoque Custo Mes Ant

```dax
calculate([Estoque Custo], '[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = True)
```

### Estoque Custo U3M

```dax
divide(calculate([Estoque Custo], '[DADO OMITIDO]_0_CALENDARIO'[U3M] = True),[DADO OMITIDO])
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

### Venda sell out MTD

```dax
calculate([Venda sell out], '[DADO OMITIDO]_0_CALENDARIO'[M0] = True)
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

### MARKUP Mes Ant

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

### Venda sell out Mes Ant

```dax
calculate([Venda sell out], '[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = True)
```

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

### ROI MTD

```dax
calculate([ROI],'[DADO OMITIDO]_0_CALENDARIO'[M0] = True)
```

### ROI Mes Ant

```dax
calculate([ROI],'[DADO OMITIDO]_0_CALENDARIO'[M-[DADO OMITIDO]] = True)
```

### ROI U3M

```dax
calculate([ROI],'[DADO OMITIDO]_0_CALENDARIO'[U3M] = True)
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

## Operadores e condições exatas

Markup MTD/Mes Ant/U3M e ROI base usam literalmente `vSellOut = [DADO OMITIDO] || vVendaCusto = [DADO OMITIDO]`. Os dois testes são igualdade ordinária `=`, combinados por OR `||`, seguidos de `IF(..., [DADO OMITIDO], CALCULATE(DIVIDE(...)))`. Não há `==`, SWITCH, comparação explícita com BLANK nem guard `[Estoque Custo] = [DADO OMITIDO]` nesses corpos. ROI Mes Ant/U3M avaliam ROI base no período; ROI anual itera ROI por AnoMes. A checagem de divisor do DIVIDE é diferente do guard IF.

A documentação primária Microsoft distingue `=` de `==`: a igualdade ordinária com zero considera BLANK igual a zero, enquanto a estrita distingue os dois. Isso prova o operador efetivamente encontrado no PBIP; não foi executado um motor DAX nem obtido valor vivo de Power BI. [Operadores DAX](https://learn.microsoft.com/en-us/dax/dax-operator-reference).

| Variável / condição | Operador | Comparado | BLANK (SQL NULL) | [DADO OMITIDO] | Positivo | Negativo |
|---|---|---|---|---|---|---|
| vSellOut | = | [DADO OMITIDO] | TRUE | TRUE | FALSE | FALSE |
| vVendaCusto | = | [DADO OMITIDO] | TRUE | TRUE | FALSE | FALSE |
| Contraste apenas: ambas | == | [DADO OMITIDO] | FALSE | TRUE | FALSE | FALSE |
| Estoque Custo | nenhum guard IF | — | DIVIDE retorna BLANK se guard acima falso | DIVIDE retorna BLANK se guard acima falso | DIVIDE | DIVIDE |

DAX BLANK e SQL NULL são representações correspondentes da ausência de valor da medida, não zeros armazenados. Linha existente com NULL difere de ausência de linha: os testes mantêm componentes `[null,...]`, contagem/timeline/hasData e a proveniência de atributos ausentes. Um contexto sem fatos produz componentes ausentes e IF verdadeiro, logo o resultado escalar é [DADO OMITIDO]; nenhum mês/fato é inserido na timeline. Uma resposta auxiliar C0[DADO OMITIDO] ausente não é uma prova de contexto vazio: permanece NULL; o SQL legítimo de agregação sem fatos retorna uma linha escalar nullable.

DIVIDE conserva o retorno BLANK para Estoque Custo BLANK/zero quando ambos Sell-out/Custo são nãozero; não transforma esse caso em IF=[DADO OMITIDO]. [DIVIDE](https://learn.microsoft.com/en-us/dax/divide-function-dax).

## BEFORE: caminho frontend e SQL

`numeric` já excluía null/undefined/string vazia antes de Number(...). C1[DADO OMITIDO] fornece NULL distinto de zero. `semanticValue` comparava numerator/denominator com `=== [DADO OMITIDO]`; null não ativava o IF, caindo no retorno null. `semanticAggregate` ignora componentes nulos e pode deixar posições undefined quando não há produto calculável. `?? [DADO OMITIDO]` usado para acumular valores existentes não deve ser trocado globalmente: a ausência completa de componente ainda precisa chegar ao guard. No buildQuery, os scopes/consultas C0[DADO OMITIDO] não mudaram.

SQL dos datasets [DADO OMITIDO] e [DADO OMITIDO] e dos demais seis consumidores ficou literalmente idêntico. Os charts ROI/Markup consomem SUM dos componentes nullable; a decisão IF/DIVIDE está no frontend, portanto não houve ajuste SQL. Replay de [DADO OMITIDO] cenários confirmou igualdade de todos os campos, com zero mudanças.

## AFTER: escopo da implementação

`daxEqualsZero(value)` testa `value == null || value === [DADO OMITIDO]` exclusivamente para medidas numéricas normalizadas. `semanticValue` recebe parâmetro opcional false; o flag `pbip_dax_zero_guard=true` é ativado somente em ROI/Markup da apresentação PBIP e nos charts [DADO OMITIDO]/[DADO OMITIDO] publicados. O guard é avaliado antes do divisor, retornando zero sem sobrescrever qualquer componente. Os perfis genéricos permanecem com seus contratos anteriores. O aggregate PBIP recebe o mesmo flag; current/previous sem fato avaliam o contexto BLANK sem criar linha. Stock cost ausente continua BLANK no DIVIDE. Nenhum operador foi substituído globalmente.

Fontes alteradas nesta etapa: `superset/frontend-plugin/plugin-chart-neoretail-kpi/src/transformProps.js` e `superset/neoretail_bootstrap/pbip_overview/presentation.py`. buildQuery, calendário, custos, Sell-out, OSA/Perda, TVD/IVD, conversão, AP→Produto, CNPJ, filtros e módulos F1[DADO OMITIDO]/F1[DADO OMITIDO]/C0[DADO OMITIDO]/C0[DADO OMITIDO]/C1[DADO OMITIDO] ficaram congelados. [Freeze verificável](pbip_c1[DADO OMITIDO]_freeze_2[DADO OMITIDO].json).

## Witness real Gold: mesmo input BEFORE / DAX CONTRACT / AFTER

| Item / loja / data | KPI | Componentes Sell/Custo/Estoque | BEFORE | DAX CONTRACT | AFTER |
|---|---|---|---|---|---|
| [DADO OMITIDO] - Queijo Roquefort Societe [DADO OMITIDO]G / B0[DADO OMITIDO] - CD ARACAJU / [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | markup | [null, null, [DADO OMITIDO]] | BLANK / NULL | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO] - Queijo Roquefort Societe [DADO OMITIDO]G / B0[DADO OMITIDO] - CD ARACAJU / [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | roi | [null, null, [DADO OMITIDO]] | BLANK / NULL | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO] - Queijo Roquefort Societe [DADO OMITIDO]G / L9[DADO OMITIDO] - CD GIGA JAGUARE / [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | markup | [null, null, [DADO OMITIDO]] | BLANK / NULL | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO] - Queijo Roquefort Societe [DADO OMITIDO]G / L9[DADO OMITIDO] - CD GIGA JAGUARE / [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | roi | [null, null, [DADO OMITIDO]] | BLANK / NULL | [DADO OMITIDO] | [DADO OMITIDO] |

Tenant [DADO OMITIDO], AP unidade e mesmos filtros Item/Loja. Exemplo Societe / B0[DADO OMITIDO]: Sell-out NULL, Venda Custo NULL, Estoque Custo zero calculável. BEFORE: `null === [DADO OMITIDO]` falso e ramo BLANK. Contrato DAX: `BLANK = [DADO OMITIDO]` verdadeiro e IF retorna [DADO OMITIDO]. AFTER: IF retorna [DADO OMITIDO]; timeline.components ainda `[null,null,[DADO OMITIDO]]`. Replay atual confirmou o input real; nenhuma linha foi fabricada na Gold. [Replay SQL](pbip_c1[DADO OMITIDO]_replay_2[DADO OMITIDO].json), [matriz completa BEFORE/CONTRACT/AFTER](pbip_c1[DADO OMITIDO]_frontend_contract_2[DADO OMITIDO].json). Esses resultados são contratos derivados, jamais NUMERIC_MATCH do Power BI.

## Casos controlados e ausência de linha

[DADO OMITIDO] combinações de perfis × Sell-out × Venda Custo × Estoque Custo com null/undefined/[DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] cobrem dois BLANK, BLANK+zero, BLANK+preenchido, positivos e negativos e todos preenchidos. Para cada combinação são verificados componentes preservados, MTD/previous/U3M e anual quando há valor numérico. O fator [DADO OMITIDO] é a convenção de apresentação percentual já certificada; DAX devolve razão decimal. U3M Markup divide Sell-out e custo por [DADO OMITIDO], que se cancela na razão; ROI U3M reavalia componentes no período e não divide ROI por [DADO OMITIDO]. Nenhum desses componentes/operadores C0[DADO OMITIDO]/C1[DADO OMITIDO] foi alterado.

| Sell-out | Venda Custo | Estoque Custo | Ramo | Markup (%) | ROI (%) |
|---|---|---|---|---|---|
| BLANK | BLANK | BLANK | IF | [DADO OMITIDO] | [DADO OMITIDO] |
| BLANK | [DADO OMITIDO] | [DADO OMITIDO] | IF | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO] | BLANK | [DADO OMITIDO] | IF | [DADO OMITIDO] | [DADO OMITIDO] |
| BLANK | [DADO OMITIDO] | BLANK | IF | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO] | [DADO OMITIDO] | BLANK | IF | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO] | [DADO OMITIDO] | BLANK / [DADO OMITIDO] | DIVIDE | [DADO OMITIDO] | BLANK |
| [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | DIVIDE | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | DIVIDE | [DADO OMITIDO] | [DADO OMITIDO] |
| Sem fatos | Sem fatos | Sem fatos | IF escalar | [DADO OMITIDO] | [DADO OMITIDO] |

Sem fatos: timeline vazia e hasData=false; componentes não materializados. SQL NULL numa linha mantém componente null. Resposta C0[DADO OMITIDO] faltante: average=null, sem fallback mensal. Os expected aprovados de testes antigos permanecem byte a byte iguais.

## Seis pares: C1[DADO OMITIDO] removida, sem forçar equivalência

| KPI | Período | Causas BEFORE | Causas AFTER (contrato completo) | Estado salvo / contexto explícito |
|---|---|---|---|---|
| MARKUP | MTD | C1[DADO OMITIDO], F1[DADO OMITIDO]D | F1[DADO OMITIDO]D | SEMANTIC_MATCH |
| MARKUP | Mês anterior | C1[DADO OMITIDO], F1[DADO OMITIDO]D | F1[DADO OMITIDO]D | SEMANTIC_MATCH |
| MARKUP | Média U3M | C1[DADO OMITIDO], F1[DADO OMITIDO]D | F1[DADO OMITIDO]D | SEMANTIC_MATCH |
| ROI | Mês anterior | C1[DADO OMITIDO], F1[DADO OMITIDO]D | F1[DADO OMITIDO]D | SEMANTIC_MATCH |
| ROI | Média U3M | C1[DADO OMITIDO], F1[DADO OMITIDO]D | F1[DADO OMITIDO]D | SEMANTIC_MATCH |
| ROI | Anual [DADO OMITIDO]M | C1[DADO OMITIDO], F1[DADO OMITIDO]D | F1[DADO OMITIDO]D, ANNUAL_ALL_BLANK_REDUCTION | SEMANTIC_DIFFERENCE |

Markup MTD usa M0; anterior usa M-[DADO OMITIDO]; U3M usa a consulta full-period C0[DADO OMITIDO]. ROI anterior/U3M usam ROI base no período. ROI anual usa os mesmos IF corrigidos em cada mês, mantendo DATESINPERIOD/VALUES/AnoMes/REMOVEFILTERS congelados. ROI MTD continua UNMAPPED.

## Divergência anual preexistente detectada, fora do guard C1[DADO OMITIDO]

Fixture controlada: contexto explícito AnoMes retendo Nov/[DADO OMITIDO]…Out/[DADO OMITIDO], uma linha em cada mês, Sell-out=[DADO OMITIDO], Venda Custo=[DADO OMITIDO], Estoque Custo=BLANK. IF é falso em cada mês; DIVIDE retorna BLANK. O filtro AnoMes exclui outros meses (inclusive a borda parcial anterior da janela diária); REMOVEFILTERS([DADO OMITIDO]_0_DIM_PERIODO) não remove esse filtro direto do calendário. SUMX sobre esses [DADO OMITIDO] retornos BLANK preserva BLANK, mas o frontend anual congelado usa `reduce((sum,row)=>sum+(row.values[[DADO OMITIDO]]??[DADO OMITIDO]),[DADO OMITIDO])` e retorna [DADO OMITIDO]. Witness controlado AFTER reproduz [DADO OMITIDO]; oracle independente SUM nullable retorna NULL. Isso não é valor vivo do PBI nem witness real Gold.

Se houver mês do calendário sem fatos, C1[DADO OMITIDO] faz ROI desse mês retornar [DADO OMITIDO], e o SUMX anual pode ser [DADO OMITIDO] corretamente. Assim, a divergência não é presumida para todo dashboard/default: é comprovada no contexto controlado restrito. Por prudência, ROI anual permanece DIFFERENCE para equivalência abrangendo contextos explícitos. Nenhuma redução anual, filtro ou calendário foi corrigido nesta etapa. [Fixture e contexto do calendário](pbip_c1[DADO OMITIDO]_annual_residual_2[DADO OMITIDO].json), [oracle](../local-engine/tests/test_pbip_c1[DADO OMITIDO]_operator_contract.py), [frontend e residual](pbip_c1[DADO OMITIDO]_frontend_contract_2[DADO OMITIDO].json). [SUMX Microsoft](https://learn.microsoft.com/en-us/dax/sumx-function-dax).

## Regressão completa e gates finais

| Gate | Resultado |
|---|---|
| Python completo | [DADO OMITIDO] passed; baseline [DADO OMITIDO] + [DADO OMITIDO] contratos/oracles C1[DADO OMITIDO] |
| Frontend anterior | [DADO OMITIDO]: [DADO OMITIDO] base/PBIP + [DADO OMITIDO] F1[DADO OMITIDO] + [DADO OMITIDO] F1[DADO OMITIDO]/C0[DADO OMITIDO] + [DADO OMITIDO] C0[DADO OMITIDO] + [DADO OMITIDO] C1[DADO OMITIDO] |
| Frontend C1[DADO OMITIDO] | [DADO OMITIDO] checks; total [DADO OMITIDO] |
| Opções | [DADO OMITIDO] comparações, [DADO OMITIDO] cenários, [DADO OMITIDO] probes Guest de opções |
| ChartData default / filtrado | [DADO OMITIDO] charts em cada; zero failures |
| Guest / RLS | [DADO OMITIDO] probes; [DADO OMITIDO] autorizado; overrides [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] negados; assinatura adulterada rejeitada |
| Replay SQL | [DADO OMITIDO] cenários datasets [DADO OMITIDO]/[DADO OMITIDO]; todos os campos inalterados |
| C0[DADO OMITIDO] witness congelado | full U3M [DADO OMITIDO]; monthly legado [DADO OMITIDO] |
| Assets publicados | flag C1[DADO OMITIDO] e markers F1[DADO OMITIDO]/C0[DADO OMITIDO] presentes em bundles compilados |
| Health | aprovado; [DADO OMITIDO] serviços saudáveis / init concluído; HTTP Embedded/Superset/Jupyter [DADO OMITIDO] |

Logs: [Python](pbip_c1[DADO OMITIDO]_python_full_final_2[DADO OMITIDO].log), [frontend base](pbip_c1[DADO OMITIDO]_frontend_base_2[DADO OMITIDO].log), [F1[DADO OMITIDO]](pbip_c1[DADO OMITIDO]_frontend_f1[DADO OMITIDO]_2[DADO OMITIDO].log), [F1[DADO OMITIDO]/C0[DADO OMITIDO]/C0[DADO OMITIDO]/C1[DADO OMITIDO]](pbip_c1[DADO OMITIDO]_frontend_existing_2[DADO OMITIDO].log), [opções](pbip_c1[DADO OMITIDO]_options_runtime_2[DADO OMITIDO].json), [Guest/RLS](pbip_c1[DADO OMITIDO]_guest_rls_2[DADO OMITIDO].json), [ChartData default](pbip_c1[DADO OMITIDO]_chartdata_default_2[DADO OMITIDO].log), [ChartData filtrado](pbip_c1[DADO OMITIDO]_chartdata_filtered_2[DADO OMITIDO].log), [assets](pbip_c1[DADO OMITIDO]_deployed_assets_2[DADO OMITIDO].json), [health](pbip_c1[DADO OMITIDO]_health_2[DADO OMITIDO].log). ChartData funcional pode usar cache; os tempos abaixo são replay sem cache.

## Performance: somente medição

Mesma construção de consultas ChartData; SQL compilado e SELECT Analytics readonly, sem cache de resultados/audit logger. Antes são medições congeladas da etapa C1[DADO OMITIDO], não uma repetição contemporânea. Depois não concorreu com os demais gates Gold. São tempos SQL, não renderização de navegador ou latência completa HTTP. Nenhuma otimização foi feita.

| Cenário | Dashboard BEFORE | Dashboard AFTER | ROI BEFORE | ROI AFTER | Markup BEFORE | Markup AFTER |
|---|---:|---:|---:|---:|---:|---:|
| default | [DADO OMITIDO]s | [DADO OMITIDO]s | [DADO OMITIDO]s | [DADO OMITIDO]s | [DADO OMITIDO]s | [DADO OMITIDO]s |
| filtered | [DADO OMITIDO]s | [DADO OMITIDO]s | [DADO OMITIDO]s | [DADO OMITIDO]s | [DADO OMITIDO]s | [DADO OMITIDO]s |

Uma execução separada compilou as mesmas consultas com e sem o flag C1[DADO OMITIDO] e exigiu igualdade literal do SQL. A medição final usa uma única compilação, como o baseline, e compara seus hashes contra essa prova separada. A primeira medição default [DADO OMITIDO]s incluía a segunda compilação de verificação e foi descartada como comparação de performance; seus logs ficaram preservados em pbip_c1[DADO OMITIDO]_sql_identity_default/filtered_2[DADO OMITIDO].log. Nenhum novo caminho/query SQL foi introduzido; diferenças de tempo observadas não provam regressão causada pelo frontend. A regressão anterior C1[DADO OMITIDO] continua separada e não foi otimizada. Tempos individuais por query:

- default / ROI: [DADO OMITIDO]s / [DADO OMITIDO] rows, [DADO OMITIDO]s / [DADO OMITIDO] rows, [DADO OMITIDO]s / [DADO OMITIDO] rows

- default / MARKUP: [DADO OMITIDO]s / [DADO OMITIDO] rows, [DADO OMITIDO]s / [DADO OMITIDO] rows, [DADO OMITIDO]s / [DADO OMITIDO] rows

- filtered / ROI: [DADO OMITIDO]s / [DADO OMITIDO] rows, [DADO OMITIDO]s / [DADO OMITIDO] rows, [DADO OMITIDO]s / [DADO OMITIDO] rows

- filtered / MARKUP: [DADO OMITIDO]s / [DADO OMITIDO] rows, [DADO OMITIDO]s / [DADO OMITIDO] rows, [DADO OMITIDO]s / [DADO OMITIDO] rows

Maior aumento observado em SELECT ROI/Markup (default): MARKUP, query [DADO OMITIDO] ([DADO OMITIDO]=timeline, [DADO OMITIDO]=barras, [DADO OMITIDO]=C0[DADO OMITIDO] full U3M), [DADO OMITIDO]s. SQL e caminho idênticos, sem evidência de causa C1[DADO OMITIDO]; comparações históricas isoladas não estabelecem regressão causal.

Maior aumento observado em SELECT ROI/Markup (filtered): ROI, query [DADO OMITIDO] ([DADO OMITIDO]=timeline, [DADO OMITIDO]=barras, [DADO OMITIDO]=C0[DADO OMITIDO] full U3M), [DADO OMITIDO]s. SQL e caminho idênticos, sem evidência de causa C1[DADO OMITIDO]; comparações históricas isoladas não estabelecem regressão causal.

[Replay default](pbip_c1[DADO OMITIDO]_sql_benchmark_after_default_2[DADO OMITIDO].log), [replay filtrado](pbip_c1[DADO OMITIDO]_sql_benchmark_after_filtered_2[DADO OMITIDO].log).

## Classificação final e limites

| Contrato | BEFORE MATCH / DIFFERENCE / UNMAPPED | AFTER MATCH / DIFFERENCE / UNMAPPED |
|---|---|---|
| Estado salvo / contextos explícitos | [DADO OMITIDO] / [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] / [DADO OMITIDO] |
| Contrato completo | [DADO OMITIDO] / [DADO OMITIDO] / [DADO OMITIDO] | [DADO OMITIDO] / [DADO OMITIDO] / [DADO OMITIDO] |

NO_PBI_VALUE=[DADO OMITIDO], sem estimativa de número atual do Power BI. Os proofs F1[DADO OMITIDO]D de cada linha foram preservados literalmente e verificados contra a classificação anterior. O sucesso condicional C1[DADO OMITIDO] não certifica bookmarks/interações completos. C1[DADO OMITIDO] foi removida dos seis pares; a redução anual all-BLANK é causa residual independente e não foi apagada por conveniência. [Classificação completa](pbi_superset_semantic_equivalence_c1[DADO OMITIDO]_after_2[DADO OMITIDO].json).

## Git e restrições

Branch `feat/osa-industry-certification`; HEAD `[DADO OMITIDO]d2f5[DADO OMITIDO]b5[DADO OMITIDO]ead1bae9af6d2ef7b7[DADO OMITIDO]f9a4[DADO OMITIDO]ae` iguais ao início. Nenhum commit, push, merge, rebase, troca de branch, main ou PR editada; PR permanece Draft. Nenhum mart republicado, dado inserido em Gold, pipeline Bronze/Silver/Gold executado ou volume Docker modificado. Apenas Superset foi recompilado/recriado, preservando os volumes. Nenhum arquivo apagado ou .gitignore alterado.

### git diff --stat antes

```text
 scripts/publish_lactalis_marts.py                  | [DADO OMITIDO] ++++++++++++-
 superset/Dockerfile                                |  [DADO OMITIDO] +
 superset/bootstrap_overview.py                     | [DADO OMITIDO] ++++++++++++++++------
 .../plugin-chart-neoretail-kpi/src/buildQuery.js   | [DADO OMITIDO] +++-
 .../src/transformProps.js                          | [DADO OMITIDO] +++++++++++--
 superset/validate_overview.py                      | [DADO OMITIDO] ++++++++-
 [DADO OMITIDO] files changed, [DADO OMITIDO] insertions(+), [DADO OMITIDO] deletions(-)
```

### git diff --stat depois

```text
 scripts/publish_lactalis_marts.py                  | [DADO OMITIDO] ++++++++++++-
 superset/Dockerfile                                |  [DADO OMITIDO] +
 superset/bootstrap_overview.py                     | [DADO OMITIDO] ++++++++++++++++------
 .../plugin-chart-neoretail-kpi/src/buildQuery.js   | [DADO OMITIDO] +++-
 .../src/transformProps.js                          | [DADO OMITIDO] ++++++++++++++++----
 superset/validate_overview.py                      | [DADO OMITIDO] ++++++++-
 [DADO OMITIDO] files changed, [DADO OMITIDO] insertions(+), [DADO OMITIDO] deletions(-)
```

O diff acima é acumulado de etapas anteriores e não inclui arquivos novos ainda untracked. O freeze por SHA separa esta etapa: só os dois fontes existentes indicados mudaram; foram acrescentados o contrato frontend C1[DADO OMITIDO], a fixture DAX e [DADO OMITIDO] testes Python.

### git status --short depois

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
?? superset/diagnose_lactalis_inventory.py
?? superset/frontend-extension/pbipSelectorDependencies.mjs
?? superset/frontend-extension/register-pbip-selectors.mjs
?? superset/frontend-extension/test-pbip-selectors.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-c0[DADO OMITIDO]-contract.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-c1[DADO OMITIDO]-contract.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-c1[DADO OMITIDO]-contract.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-contract.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-tvd-ivd-contract.mjs
?? superset/neoretail_bootstrap/pbip_overview/
?? superset/profile_lactalis_osa_filtered.py
```

Os scripts superset/diagnose_lactalis_inventory.py e superset/profile_lactalis_osa_filtered.py continuam visíveis e não foram versionados. Artefatos generated são locais. Sem commit/push.
