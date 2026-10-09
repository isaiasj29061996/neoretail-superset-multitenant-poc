> Cópia para GitHub: números de origem e identificadores numéricos omitidos. Original integral exige backup externo. Não usar esta cópia como fixture ou SQL executável.

# C1[DADO OMITIDO] — Venda Custo e Estoque Custo: BLANK / NULL / zero — LACTALIS [DADO OMITIDO]

Corrigida exclusivamente C1[DADO OMITIDO] na camada semântica PBIP. Referência principal: ZIP extraído atual, sem depender de Power BI Desktop. Nenhum número observado no Power BI; **[DADO OMITIDO] NO_PBI_VALUE**, sem NUMERIC_MATCH.

## Contrato DAX exato

Fonte: `generated\pbi_lactalis_reference_2[DADO OMITIDO]\NeoRetail Pocket RF.SemanticModel\definition\tables\_Metricas.tmdl`; SHA-[DADO OMITIDO] `c5[DADO OMITIDO]c0fa2[DADO OMITIDO]f7a0[DADO OMITIDO]f4[DADO OMITIDO]d3[DADO OMITIDO]c9bc0[DADO OMITIDO]c2a8[DADO OMITIDO]eb9[DADO OMITIDO]caa`. Inclui as oito medidas de custo, Markup/ROI e todo o fechamento de medidas auxiliares usado por esses consumidores.

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

## SUMX, operandos e períodos

`Venda Custo` itera FATOS_PARTICULAR_HISTORICO e multiplica VOLUME_UNIDADES × AVG_PRICE_COST por linha. `Estoque Custo` itera a mesma tabela e multiplica ESTOQUE_MEDIO × AVG_PRICE_COST por linha. Não há conversion_rate aritmético. Item/Produto e a direção AP → conversão → chaves dos itens continuam congelados, assim como a ponte CNPJ e os filtros de página.

Os wrappers Venda Custo MTD/Mes Ant/U3M usam ALL(AP_CONVERSAO[nm_measure]); Estoque Custo usa diretamente o contexto AP da medida. Este estágio não reimplementa a propagação de AP já certificada: altera apenas os produtos/ausência de valor dos mesmos conjuntos de linhas. MTD usa M0, mês anterior M-[DADO OMITIDO]; ambos os custos U3M reavaliam o SUMX no período completo e dividem por [DADO OMITIDO]. Como o produto por linha é aditivo, SUM dos custos mensais nullable seguido de /[DADO OMITIDO] preserva esse operador e BLANK quando não há qualquer produto numérico. Não há escolha de último mês para Estoque Custo U3M; a regra de último mês é de Estoque Qtd, que ficou intacta.

Um operando BLANK faz o produto BLANK; SUMX ignora esses produtos. Sem produto numérico, o resultado contratual é BLANK, inclusive contexto sem linhas. Isso difere de um produto numérico igual a zero. A documentação Microsoft confirma a multiplicação com BLANK e o comportamento iterador de SUMX: [BLANK e operadores DAX](https://support.microsoft.com/en-us/excel/data-types-in-data-models), [SUMX](https://learn.microsoft.com/en-us/dax/sumx-function-dax). Os expected abaixo são derivados desse contrato; não são resultados observados de uma consulta ao modelo Power BI.

## Tabela controlada BLANK / NULL / zero

| Caso | Linhas | Produtos calculáveis | SQL antigo | Contrato DAX | AFTER (ambos os custos) |
|---|---:|---:|---:|---:|---:|
| valid | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| a_blank | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | BLANK / NULL | BLANK / NULL |
| b_blank | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | BLANK / NULL | BLANK / NULL |
| both_blank | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | BLANK / NULL | BLANK / NULL |
| mixed | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| all_blank | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | BLANK / NULL | BLANK / NULL |
| empty | [DADO OMITIDO] | [DADO OMITIDO] | BLANK / NULL | BLANK / NULL | BLANK / NULL |
| zero | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| zero_plus_blank | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| zero_times_blank | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | BLANK / NULL | BLANK / NULL |
| negative | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |

Nenhuma linha: COUNT(*)=[DADO OMITIDO], SUMX BLANK. Linha existente com operando BLANK: COUNT(*)>[DADO OMITIDO], COUNT(produto)=[DADO OMITIDO], SUMX BLANK. Zero real: COUNT(produto)>[DADO OMITIDO], SUMX=[DADO OMITIDO]. Zero × BLANK ainda é BLANK. Misturas ignoram produtos BLANK e mantêm os produtos numéricos, inclusive zero e negativos. Fixtures controladas usam SELECT VALUES/SQLite efêmero; nenhuma linha foi inserida na Gold. [Artefato controlado BEFORE/CONTRACT/AFTER](pbip_c1[DADO OMITIDO]_controlled_before_after_2[DADO OMITIDO].json).

## Witnesses reais BEFORE / DAX CONTRACT / AFTER

Gold elegível (LACTALIS, ponte CNPJ/filtros de página/AP unidade): {"rows": [DADO OMITIDO], "volume_blank": [DADO OMITIDO], "stock_blank": [DADO OMITIDO], "price_blank": [DADO OMITIDO], "negative_volume": [DADO OMITIDO], "negative_stock": [DADO OMITIDO]}. Inclui valores negativos reais, sem fabricar dados.

| Item + Loja / mês | Componente | BEFORE | DAX CONTRACT | AFTER |
|---|---|---:|---:|---:|
| [DADO OMITIDO] - Queijo Roquefort Societe [DADO OMITIDO]G / B0[DADO OMITIDO] - CD ARACAJU / [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | sales_cost_sum | [DADO OMITIDO] | BLANK / NULL | BLANK / NULL |
| [DADO OMITIDO] - Queijo Roquefort Societe [DADO OMITIDO]G / B0[DADO OMITIDO] - CD ARACAJU / [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | stock_cost_sum | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO] - Queijo Roquefort Societe [DADO OMITIDO]G / L9[DADO OMITIDO] - CD GIGA JAGUARE / [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | sales_cost_sum | [DADO OMITIDO] | BLANK / NULL | BLANK / NULL |
| [DADO OMITIDO] - Queijo Roquefort Societe [DADO OMITIDO]G / L9[DADO OMITIDO] - CD GIGA JAGUARE / [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | stock_cost_sum | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| [DADO OMITIDO] - Le Blue Azul Fração [DADO OMITIDO]G Président Imp / [DADO OMITIDO] - SAVEGNAGO CROSSDOCK [DADO OMITIDO] / [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | sales_cost_sum | [DADO OMITIDO] | BLANK / NULL | BLANK / NULL |
| [DADO OMITIDO] - Le Blue Azul Fração [DADO OMITIDO]G Président Imp / [DADO OMITIDO] - SAVEGNAGO CROSSDOCK [DADO OMITIDO] / [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | stock_cost_sum | [DADO OMITIDO] | BLANK / NULL | BLANK / NULL |
| [DADO OMITIDO] - Le Blue Azul Fração [DADO OMITIDO]G Président Imp / [DADO OMITIDO] - SAVEGNAGO CROSSDOCK [DADO OMITIDO] / [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | sales_cost_sum | [DADO OMITIDO] | BLANK / NULL | BLANK / NULL |
| [DADO OMITIDO] - Le Blue Azul Fração [DADO OMITIDO]G Président Imp / [DADO OMITIDO] - SAVEGNAGO CROSSDOCK [DADO OMITIDO] / [DADO OMITIDO][DADO OMITIDO][DADO OMITIDO] | stock_cost_sum | [DADO OMITIDO] | BLANK / NULL | BLANK / NULL |

Filtros nativos exatos Item + Loja + unidade, não IDs internos que mudem a cardinalidade do seletor. Roquefort comprova Venda Custo [DADO OMITIDO]→BLANK com Estoque Custo zero real preservado. Le Blue comprova ambos [DADO OMITIDO]→BLANK. [Prova BEFORE](pbip_c1[DADO OMITIDO]_before_2[DADO OMITIDO].json), [BEFORE Estoque](pbip_c1[DADO OMITIDO]_stock_before_2[DADO OMITIDO].json), [AFTER e replay de todos os campos](pbip_c1[DADO OMITIDO]_replay_2[DADO OMITIDO].json).

## SQL antes e depois

```sql
-- BEFORE, caminho filtrado
SUM(COALESCE(volume_unidades,[DADO OMITIDO])*COALESCE(avg_price_cost,[DADO OMITIDO])) AS sales_cost_sum,
SUM(COALESCE(estoque_medio,[DADO OMITIDO])*COALESCE(avg_price_cost,[DADO OMITIDO])) AS stock_cost_sum
-- AFTER, caminho filtrado
SUM(volume_unidades * avg_price_cost) AS sales_cost_sum,
SUM(estoque_medio * avg_price_cost) AS stock_cost_sum
```

No default, o mart já perdeu a distinção NULL/[DADO OMITIDO]. Portanto só retirar COALESCE no caminho filtrado seria insuficiente. A projeção default consulta os operandos originais quando o agregado é zero: se não existe produto calculável no mesmo contexto (data, tenant, all/atividade, chaves AP e filtros), devolve NULL; se existe, preserva o zero. Agregados não zero e NULL existente continuam iguais. A consulta usa EXISTS com parada no primeiro produto calculável; não agrega nem reprocessa a Gold.

```sql
CASE WHEN b.sales_cost_sum=[DADO OMITIDO] AND NOT EXISTS (
  SELECT [DADO OMITIDO] FROM gold.nr_pbip_overview_history h
  WHERE h.id_customer=b.id_customer AND h.data=b.data
    AND (b.semantic_scope='all' OR h.tp_activity_level IS NOT DISTINCT FROM b.tp_activity_level)
    AND h.volume_unidades IS NOT NULL AND h.avg_price_cost IS NOT NULL
    -- mesmos predicados dimensionais/CNPJ/AP já certificados
) THEN NULL ELSE b.sales_cost_sum END AS sales_cost_sum
-- análogo para estoque_medio / stock_cost_sum
```

SQL completo real: [datasets BEFORE](pbip_c1[DADO OMITIDO]_runtime_before_2[DADO OMITIDO].json) e [SQL publicado AFTER](pbip_c1[DADO OMITIDO]_publication_2[DADO OMITIDO].json). Datasets **[DADO OMITIDO] e [DADO OMITIDO]** atualizados in-place. Nenhum chart mudou de dataset ou params; nenhum mart criado/republicado; nenhum processamento Bronze/Silver/Gold.

## Impacto em Markup, ROI e C0[DADO OMITIDO]

Markup MTD/anterior/U3M e ROI anterior/U3M/[DADO OMITIDO]M recebem os componentes nullable, mas seus operadores próprios e guardas C1[DADO OMITIDO] não mudaram. C1[DADO OMITIDO] permanece SEMANTIC_DIFFERENCE: por exemplo, guarda zero estrita em JavaScript não interpreta BLANK como a comparação DAX `= [DADO OMITIDO]`. Corrigir o custo pode tornar visível essa diferença; ela não foi mascarada nem corrigida.

C0[DADO OMITIDO] permanece congelada: o frontend consome Sell-out completo U3M antes de /[DADO OMITIDO]; Markup e ROI seguem suas ordens aprovadas. Replay adicional do witness Gold C0[DADO OMITIDO] confirma **[DADO OMITIDO]** depois de C1[DADO OMITIDO], igual ao valor semântico aprovado, sem usar valor observado PBI. [Replay C0[DADO OMITIDO]](pbip_c1[DADO OMITIDO]_c0[DADO OMITIDO]_frozen_replay_2[DADO OMITIDO].json). ROI [DADO OMITIDO]M e o calendário mantiveram seus caminhos anteriores; só o componente custo sofreu o delta C1[DADO OMITIDO].

## Testes e gates

- **[DADO OMITIDO] Python = [DADO OMITIDO] anteriores + [DADO OMITIDO] C1[DADO OMITIDO]**, na implementação final. Produtos preenchidos, BLANK parcial/todos, vazio, zero, zero+BLANK, negativo, ambas as medidas, caminho default/filtrado, MTD/anterior/U3M, AP/Produto e nenhum fator de conversão aritmético.
- **[DADO OMITIDO] frontend = [DADO OMITIDO] anteriores + [DADO OMITIDO] C1[DADO OMITIDO]**: baseline [DADO OMITIDO], F1[DADO OMITIDO] [DADO OMITIDO], F1[DADO OMITIDO]/C0[DADO OMITIDO] [DADO OMITIDO], C0[DADO OMITIDO] [DADO OMITIDO] e C1[DADO OMITIDO] [DADO OMITIDO]. Consumo nullable por custos, Markup e ROI, zero distinto de BLANK, C1[DADO OMITIDO] preservada.
- **[DADO OMITIDO] comparações de opções** em [DADO OMITIDO] cenários, [DADO OMITIDO] probes RLS de opções, seleção das cinco atividades e busca Loja.
- **[DADO OMITIDO] probes Guest/RLS** em seis datasets, incluindo [DADO OMITIDO]/[DADO OMITIDO]; overrides [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] negados; assinatura adulterada rejeitada.
- Replay SQL default, filtrado e quatro witnesses reais nos datasets [DADO OMITIDO]/[DADO OMITIDO]: apenas custos [DADO OMITIDO]→NULL; todos os outros campos e cardinalidades iguais.
- Health check final, ChartData default e filtrado: evidências abaixo.

[Python final](pbip_c1[DADO OMITIDO]_python_full_final_2[DADO OMITIDO].log), [frontend baseline](pbip_c1[DADO OMITIDO]_frontend_base_2[DADO OMITIDO].log), [frontend F1[DADO OMITIDO]](pbip_c1[DADO OMITIDO]_frontend_f1[DADO OMITIDO]_2[DADO OMITIDO].log), [frontend F1[DADO OMITIDO]/C0[DADO OMITIDO]/C1[DADO OMITIDO]](pbip_c1[DADO OMITIDO]_frontend_new_2[DADO OMITIDO].log), [opções](pbip_c1[DADO OMITIDO]_options_runtime_2[DADO OMITIDO].json), [Guest/RLS](pbip_c1[DADO OMITIDO]_guest_rls_2[DADO OMITIDO].json), [freeze](pbip_c1[DADO OMITIDO]_freeze_2[DADO OMITIDO].json), [health](pbip_c1[DADO OMITIDO]_health_2[DADO OMITIDO].log).

## ChartData e performance

Tempos em segundos por chart, incluindo queries, e dashboard sequencial de oito charts; não são latências de renderização do navegador. Antes C1[DADO OMITIDO] usa o SQL publicado congelado na etapa C0[DADO OMITIDO]. F1[DADO OMITIDO]/C0[DADO OMITIDO]/C0[DADO OMITIDO] não foram otimizadas. A tabela usa replay direto do SQL compilado pela mesma API de queries ChartData (force=True no contexto), sequencialmente e sem outras validações concorrentes na Gold. Mede compilação + SQL, sem cache de resultados e sem o logger de auditoria, não a serialização/DataFrame do endpoint. BEFORE usa o SQL congelado apenas em memória no processo do benchmark, com autoflush=False, transação de metadados READ ONLY e rollback; o atributo SQL é restaurado antes de executar qualquer SELECT na Analytics. Nenhum SQL anterior é republicado. AFTER usa o SQL final C1[DADO OMITIDO]. Cada query confirma o estágio de seu SQL. São registros locais de uma execução, não benchmark estatístico.

| Contexto / chart | BEFORE C1[DADO OMITIDO] | AFTER C1[DADO OMITIDO] final |
|---|---:|---:|
| default / Vendas | [DADO OMITIDO] | [DADO OMITIDO] |
| default / Estoque | [DADO OMITIDO] | [DADO OMITIDO] |
| default / MARKUP | [DADO OMITIDO] | [DADO OMITIDO] |
| default / ROI | [DADO OMITIDO] | [DADO OMITIDO] |
| default / dashboard | [DADO OMITIDO] | [DADO OMITIDO] |
| filtered / Vendas | [DADO OMITIDO] | [DADO OMITIDO] |
| filtered / Estoque | [DADO OMITIDO] | [DADO OMITIDO] |
| filtered / MARKUP | [DADO OMITIDO] | [DADO OMITIDO] |
| filtered / ROI | [DADO OMITIDO] | [DADO OMITIDO] |
| filtered / dashboard | [DADO OMITIDO] | [DADO OMITIDO] |

A primeira implementação C1[DADO OMITIDO] usava uma agregação de validade e registrou [DADO OMITIDO]s no dashboard default (gate sem force). Os gates sem force reutilizaram cache em charts congelados, portanto não são usados para inferir o delta final; a tabela final usa replay SQL sem cache. A tentativa de benchmark via comando completo ChartData foi descartada: o logger tentou INSERT em logs e encontrou a proteção READ ONLY. Seus números não foram usados para a comparação final. A agregação de validade foi substituída dentro do escopo C1[DADO OMITIDO] por CASE + EXISTS, preservando a mesma semântica. O resultado final está na tabela acima; [medição inicial](pbip_c1[DADO OMITIDO]_chartdata_initial_default_2[DADO OMITIDO].log) mantida como evidência. Nenhuma otimização geral/F1[DADO OMITIDO]/C0[DADO OMITIDO]/C0[DADO OMITIDO] foi feita.

### Custos medidos separadamente

Cada query abaixo mede somente um componente custo e retorna seus valores MTD/anterior/U3M; SQL BEFORE e AFTER executados sequencialmente, sem gates concorrentes na Gold. Usa dataset [DADO OMITIDO] e SUMX equivalente, sem Sell-out ou renderização frontend.

| Contexto / medida | BEFORE | AFTER |
|---|---:|---:|
| default / Venda Custo | [DADO OMITIDO] | [DADO OMITIDO] |
| default / Estoque Custo | [DADO OMITIDO] | [DADO OMITIDO] |
| filtered / Venda Custo | [DADO OMITIDO] | [DADO OMITIDO] |
| filtered / Estoque Custo | [DADO OMITIDO] | [DADO OMITIDO] |

### Custo adicional C1[DADO OMITIDO] por query

Nos três charts consumidores, a última query é a auxiliar U3M de C0[DADO OMITIDO]. Seu frozen_monthly materializado passa a verificar custos zero/BLANK também nas linhas de atividade. O módulo C0[DADO OMITIDO] não mudou, mas esta consulta consome os custos corrigidos. A medição mostra o custo nas consultas mensais e na auxiliar U3M do envelope do dataset [DADO OMITIDO]; a tabela separa cada query. O SQL de custo nullable/EXISTS é o delta C1[DADO OMITIDO], enquanto o módulo C0[DADO OMITIDO] permanece igual. Não atribuir esses aumentos à regressão histórica F1[DADO OMITIDO]/C0[DADO OMITIDO]/C0[DADO OMITIDO].

| Contexto / chart / query | SQL BEFORE | SQL AFTER |
|---|---:|---:|
| default / Vendas / timeline mensal | [DADO OMITIDO] | [DADO OMITIDO] |
| default / Vendas / auxiliar U3M | [DADO OMITIDO] | [DADO OMITIDO] |
| default / ROI / timeline mensal | [DADO OMITIDO] | [DADO OMITIDO] |
| default / ROI / barras atividade | [DADO OMITIDO] | [DADO OMITIDO] |
| default / ROI / auxiliar U3M | [DADO OMITIDO] | [DADO OMITIDO] |
| default / MARKUP / timeline mensal | [DADO OMITIDO] | [DADO OMITIDO] |
| default / MARKUP / barras atividade | [DADO OMITIDO] | [DADO OMITIDO] |
| default / MARKUP / auxiliar U3M | [DADO OMITIDO] | [DADO OMITIDO] |
| filtered / Vendas / timeline mensal | [DADO OMITIDO] | [DADO OMITIDO] |
| filtered / Vendas / auxiliar U3M | [DADO OMITIDO] | [DADO OMITIDO] |
| filtered / ROI / timeline mensal | [DADO OMITIDO] | [DADO OMITIDO] |
| filtered / ROI / barras atividade | [DADO OMITIDO] | [DADO OMITIDO] |
| filtered / ROI / auxiliar U3M | [DADO OMITIDO] | [DADO OMITIDO] |
| filtered / MARKUP / timeline mensal | [DADO OMITIDO] | [DADO OMITIDO] |
| filtered / MARKUP / barras atividade | [DADO OMITIDO] | [DADO OMITIDO] |
| filtered / MARKUP / auxiliar U3M | [DADO OMITIDO] | [DADO OMITIDO] |

[SQL e tempos dos custos](pbip_c1[DADO OMITIDO]_cost_performance_2[DADO OMITIDO].json), [Replay SQL ChartData BEFORE default](pbip_c1[DADO OMITIDO]_sql_benchmark_before_default_2[DADO OMITIDO].log), [BEFORE filtrado](pbip_c1[DADO OMITIDO]_sql_benchmark_before_filtered_2[DADO OMITIDO].log), [AFTER default](pbip_c1[DADO OMITIDO]_sql_benchmark_after_default_2[DADO OMITIDO].log), [AFTER filtrado](pbip_c1[DADO OMITIDO]_sql_benchmark_after_filtered_2[DADO OMITIDO].log).

## Reclassificação — somente C1[DADO OMITIDO]

| Escopo | MATCH antes/depois | DIFFERENCE antes/depois | UNMAPPED |
|---|---:|---:|---:|
| Estado salvo / contexto explícito | [DADO OMITIDO] → [DADO OMITIDO] | [DADO OMITIDO] → [DADO OMITIDO] | [DADO OMITIDO] |
| Contrato completo | [DADO OMITIDO] → [DADO OMITIDO] | [DADO OMITIDO] → [DADO OMITIDO] | [DADO OMITIDO] |

**NO_PBI_VALUE: [DADO OMITIDO] → [DADO OMITIDO]; nenhum NUMERIC_MATCH.**

| KPI / período | Causas BEFORE | Causas AFTER | Estado salvo AFTER | Contrato completo AFTER |
|---|---|---|---|---|
| MARKUP / MTD | C1[DADO OMITIDO], C1[DADO OMITIDO], F1[DADO OMITIDO]D | C1[DADO OMITIDO], F1[DADO OMITIDO]D | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| MARKUP / Mês anterior | C1[DADO OMITIDO], C1[DADO OMITIDO], F1[DADO OMITIDO]D | C1[DADO OMITIDO], F1[DADO OMITIDO]D | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| MARKUP / Média U3M | C1[DADO OMITIDO], C1[DADO OMITIDO], F1[DADO OMITIDO]D | C1[DADO OMITIDO], F1[DADO OMITIDO]D | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| Estoque custo / MTD | C1[DADO OMITIDO], F1[DADO OMITIDO]D | F1[DADO OMITIDO]D | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| Estoque custo / Mês anterior | C1[DADO OMITIDO], F1[DADO OMITIDO]D | F1[DADO OMITIDO]D | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| Estoque custo / Média U3M | C1[DADO OMITIDO], F1[DADO OMITIDO]D | F1[DADO OMITIDO]D | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| ROI / Mês anterior | C1[DADO OMITIDO], C1[DADO OMITIDO], F1[DADO OMITIDO]D | C1[DADO OMITIDO], F1[DADO OMITIDO]D | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| ROI / Média U3M | C1[DADO OMITIDO], C1[DADO OMITIDO], F1[DADO OMITIDO]D | C1[DADO OMITIDO], F1[DADO OMITIDO]D | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| ROI / Anual [DADO OMITIDO]M | C1[DADO OMITIDO], C1[DADO OMITIDO], F1[DADO OMITIDO]D | C1[DADO OMITIDO], F1[DADO OMITIDO]D | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| Venda custo / MTD | C1[DADO OMITIDO], F1[DADO OMITIDO]D | F1[DADO OMITIDO]D | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| Venda custo / Mês anterior | C1[DADO OMITIDO], F1[DADO OMITIDO]D | F1[DADO OMITIDO]D | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| Venda custo / Média U3M | C1[DADO OMITIDO], F1[DADO OMITIDO]D | F1[DADO OMITIDO]D | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |

Os seis pares de Venda/Estoque Custo tornam-se MATCH no estado salvo porque C1[DADO OMITIDO] era sua única causa nesse contexto. Os seis consumidores Markup/ROI mantêm DIFFERENCE por C1[DADO OMITIDO]. F1[DADO OMITIDO]D permanece individualizada para cada KPI, com prova de caminho e contexto de sincronização externo; F1[DADO OMITIDO]A/B/C e demais resíduos de interação não foram recertificados. ROI MTD continua UNMAPPED nesta página. [Matriz completa de [DADO OMITIDO] pares](pbi_superset_semantic_equivalence_c1[DADO OMITIDO]_after_2[DADO OMITIDO].json).

## Arquivos, preservação e Git

Único arquivo existente alterado nesta etapa: `superset/neoretail_bootstrap/pbip_overview/semantics.py` (integração do helper). Novos: `superset/neoretail_bootstrap/pbip_overview/cost_blank.py`, `local-engine/tests/test_pbip_c1[DADO OMITIDO]_cost_blank.py`, `superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-c1[DADO OMITIDO]-contract.mjs`. Artefatos de prova/report em generated. Código frontend de produção e assets servidos não mudaram, portanto não houve rebuild/deploy de frontend nesta etapa.

Hashes comprovam que F1[DADO OMITIDO]/F1[DADO OMITIDO]/C0[DADO OMITIDO]/C0[DADO OMITIDO], calendário, OSA/Perda OSA, conversões, filtros/CNPJ, scripts SQL/marts e todos os testes/expected antigos ficaram iguais. Os oito charts mantiveram params/IDs e metadados do dashboard; os onze marts PBIP mantiveram suas definições. Não foram executados INSERT/UPDATE/DELETE/REFRESH/DDL na Analytics/Gold; somente SELECTs de prova. Escrita restrita a metadados Superset dos dois SQLs.

Branch `feat/osa-industry-certification`, HEAD `[DADO OMITIDO]d2f5[DADO OMITIDO]b5[DADO OMITIDO]ead1bae9af6d2ef7b7[DADO OMITIDO]f9a4[DADO OMITIDO]ae`, iguais ao snapshot inicial. Sem commit, push, merge, rebase, troca de branch, alteração da main ou da PR Draft. Nenhum volume Docker removido ou recriado. Diff/status abaixo são cumulativos da worktree e incluem trabalho anterior, não apenas C1[DADO OMITIDO].

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
?? local-engine/tests/test_pbip_c1[DADO OMITIDO]_cost_blank.py
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
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-contract.mjs
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-tvd-ivd-contract.mjs
?? superset/neoretail_bootstrap/pbip_overview/
?? superset/profile_lactalis_osa_filtered.py
```
