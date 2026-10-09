> Cópia para GitHub: números de origem e identificadores numéricos omitidos. Original integral exige backup externo. Não usar esta cópia como fixture ou SQL executável.

# LACTALIS — filtros e conversões PBIP → Superset

Escopo: página Visão geral [DADO OMITIDO] – visão indústria. ZIP/PBIP é contrato; TOM desserializado offline, sem Power BI Desktop. Código/Gold numérica não provam o valor atual do Power BI.

## [DADO OMITIDO]. Diferenças de filtro antes

C0[DADO OMITIDO] nos [DADO OMITIDO] pares: atributos locais usados como catálogo, ponte CNPJ/catálogo não reproduzidos nos detalhes, seletores e contexto oculto incompletos. TVD/IVD também exigem separar a seleção de data do ALL(AP). O inventário completo por par está na matriz JSON, com níveis report/page/visual, slicers, bookmark, interações e DAX.

## [DADO OMITIDO]. Diferenças de conversão antes

C0[DADO OMITIDO]: fatores derivados de coortes de fatos/contexto mensal em vez da dimensão. C1[DADO OMITIDO]: Giro dependendo da seleção externa. C1[DADO OMITIDO]: quantidades com fator mensal em vez do contexto dimensional. Foi corrigida uma interpretação incorreta desta própria etapa: a direção não é item→conversão, mas conversão→item; produto não reduz MAX dimensional e Giro exige chave unidade.

## [DADO OMITIDO]. Matriz KPI × filtro

Detalhe completo: [pbip_kpi_filter_matrix_after_2[DADO OMITIDO].json](pbip_kpi_filter_matrix_after_2[DADO OMITIDO].json). Todas as linhas preservam fontes e filtros efetivos, inclusive filtros ocultos e interações.

| KPI/período | Filtro PBIP e SQL implementado | Diferença restante |
|---|---|---|
| MARKUP / MTD | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| MARKUP / Mês anterior | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| MARKUP / Média U3M | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Venda qtd / MTD | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Venda qtd / Mês anterior | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Venda qtd / Média U3M | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Estoque qtd / MTD | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Estoque qtd / Mês anterior | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Estoque qtd / Média U3M | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Giro / MTD | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Giro / Mês anterior | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Giro / Média U3M | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Estoque custo / MTD | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Estoque custo / Mês anterior | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Estoque custo / Média U3M | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| IVD - Excesso / MTD | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO], F1[DADO OMITIDO] |
| IVD - Excesso / Mês anterior | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO], F1[DADO OMITIDO] |
| IVD - Excesso / Média U3M | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO], F1[DADO OMITIDO] |
| Venda sell out / MTD | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Venda sell out / Mês anterior | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Venda sell out / Média U3M | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| OSA / MTD | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| OSA / Mês anterior | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| OSA / Média U3M | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Perda OSA / MTD | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Perda OSA / Mês anterior | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Perda OSA / Média U3M | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| ROI / Mês anterior | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| ROI / Média U3M | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| ROI / Anual [DADO OMITIDO]M | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Venda custo / MTD | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Venda custo / Mês anterior | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| Venda custo / Média U3M | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO] |
| TVD - Pré-ruptura / MTD | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO], F1[DADO OMITIDO] |
| TVD - Pré-ruptura / Mês anterior | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO], F1[DADO OMITIDO] |
| TVD - Pré-ruptura / Média U3M | Contrato específico preservado na matriz; CNPJ por conjuntos de chaves, contratado e Rede não nula | F1[DADO OMITIDO], F1[DADO OMITIDO] |

## [DADO OMITIDO]. Matriz KPI × conversão

Detalhe completo: [pbip_kpi_conversion_matrix_after_2[DADO OMITIDO].json](pbip_kpi_conversion_matrix_after_2[DADO OMITIDO].json).

| KPI/período | DAX: ordem/contexto | Superset |
|---|---|---|
| MARKUP / MTD | sell-out/custo; guardas DAX; componentes avaliados no mesmo período | componentes com conversão contextual corrigida; C1[DADO OMITIDO] e U3M C0[DADO OMITIDO] mantidos |
| MARKUP / Mês anterior | sell-out/custo; guardas DAX; componentes avaliados no mesmo período | componentes com conversão contextual corrigida; C1[DADO OMITIDO] e U3M C0[DADO OMITIDO] mantidos |
| MARKUP / Média U3M | sell-out/custo; guardas DAX; componentes avaliados no mesmo período | componentes com conversão contextual corrigida; C1[DADO OMITIDO] e U3M C0[DADO OMITIDO] mantidos |
| Venda qtd / MTD | SUMX(histórico, volume*Fator); MAX dimensional; U3M reavalia/[DADO OMITIDO] | SUM por linha volume*MAX dimensional; chave dos itens AP; U3M aditivo com fator constante no contexto |
| Venda qtd / Mês anterior | SUMX(histórico, volume*Fator); MAX dimensional; U3M reavalia/[DADO OMITIDO] | SUM por linha volume*MAX dimensional; chave dos itens AP; U3M aditivo com fator constante no contexto |
| Venda qtd / Média U3M | SUMX(histórico, volume*Fator); MAX dimensional; U3M reavalia/[DADO OMITIDO] | SUM por linha volume*MAX dimensional; chave dos itens AP; U3M aditivo com fator constante no contexto |
| Estoque qtd / MTD | MAX(MES_ANO) no período; SUM(estoque do mês)*Fator; U3M último mês/[DADO OMITIDO] | stock_bundle já usa último mês/[DADO OMITIDO]; fator dimensional global; AP restringe chaves |
| Estoque qtd / Mês anterior | MAX(MES_ANO) no período; SUM(estoque do mês)*Fator; U3M último mês/[DADO OMITIDO] | stock_bundle já usa último mês/[DADO OMITIDO]; fator dimensional global; AP restringe chaves |
| Estoque qtd / Média U3M | MAX(MES_ANO) no período; SUM(estoque do mês)*Fator; U3M último mês/[DADO OMITIDO] | stock_bundle já usa último mês/[DADO OMITIDO]; fator dimensional global; AP restringe chaves |
| Giro / MTD | AVERAGE(GIRO>[DADO OMITIDO]); ALL(AP), força nm_measure=unidade; chave dos itens unitários, sem multiplicar por taxa | EXISTS DIM_CONVERSAO/DIM_ITENS unidade; SUM positivo/COUNT positivo; seleção externa ignorada |
| Giro / Mês anterior | AVERAGE(GIRO>[DADO OMITIDO]); ALL(AP), força nm_measure=unidade; chave dos itens unitários, sem multiplicar por taxa | EXISTS DIM_CONVERSAO/DIM_ITENS unidade; SUM positivo/COUNT positivo; seleção externa ignorada |
| Giro / Média U3M | AVERAGE(GIRO>[DADO OMITIDO]); ALL(AP), força nm_measure=unidade; chave dos itens unitários, sem multiplicar por taxa | EXISTS DIM_CONVERSAO/DIM_ITENS unidade; SUM positivo/COUNT positivo; seleção externa ignorada |
| Estoque custo / MTD | SUMX(estoque_médio*custo); sem fator aritmético, mas AP restringe os itens | sem multiplicação pela taxa; chaves AP aplicadas; BLANK de operandos residual C1[DADO OMITIDO] |
| Estoque custo / Mês anterior | SUMX(estoque_médio*custo); sem fator aritmético, mas AP restringe os itens | sem multiplicação pela taxa; chaves AP aplicadas; BLANK de operandos residual C1[DADO OMITIDO] |
| Estoque custo / Média U3M | SUMX(estoque_médio*custo); sem fator aritmético, mas AP restringe os itens | sem multiplicação pela taxa; chaves AP aplicadas; BLANK de operandos residual C1[DADO OMITIDO] |
| IVD - Excesso / MTD | sem fator; SUM simplificado na última data não BLANK; ALL(AP) na expressão principal | AP removido da soma; contexto da data continua residual F1[DADO OMITIDO] |
| IVD - Excesso / Mês anterior | sem fator; SUM simplificado na última data não BLANK; ALL(AP) na expressão principal | AP removido da soma; contexto da data continua residual F1[DADO OMITIDO] |
| IVD - Excesso / Média U3M | sem fator; SUM simplificado na última data não BLANK; ALL(AP) na expressão principal | AP removido da soma; contexto da data continua residual F1[DADO OMITIDO] |
| Venda sell out / MTD | SUMX(VALUES(Região), receita>[DADO OMITIDO] ? receita : (SUM(volume)*Fator)*(AVERAGE(preço)*Fator)) | ramo por Região e fator global; U3M mensal ainda residual C0[DADO OMITIDO] |
| Venda sell out / Mês anterior | SUMX(VALUES(Região), receita>[DADO OMITIDO] ? receita : (SUM(volume)*Fator)*(AVERAGE(preço)*Fator)) | ramo por Região e fator global; U3M mensal ainda residual C0[DADO OMITIDO] |
| Venda sell out / Média U3M | SUMX(VALUES(Região), receita>[DADO OMITIDO] ? receita : (SUM(volume)*Fator)*(AVERAGE(preço)*Fator)) | ramo por Região e fator global; U3M mensal ainda residual C0[DADO OMITIDO] |
| OSA / MTD | razão de SUM(problemas)/SUM(ativos), com BLANK congelado; AP restringe itens pela relação | mesma razão congelada; EXISTS das chaves da medida selecionada antes da agregação |
| OSA / Mês anterior | razão de SUM(problemas)/SUM(ativos), com BLANK congelado; AP restringe itens pela relação | mesma razão congelada; EXISTS das chaves da medida selecionada antes da agregação |
| OSA / Média U3M | razão de SUM(problemas)/SUM(ativos), com BLANK congelado; AP restringe itens pela relação | mesma razão congelada; EXISTS das chaves da medida selecionada antes da agregação |
| Perda OSA / MTD | SUM(qtd_perda)*MAX(taxa)*AVERAGE(preço); U3M contexto completo/[DADO OMITIDO]; atividade não propaga à causa | mesmos componentes congelados; taxa global da dimensão; AP restringe chaves; sem fator inventado |
| Perda OSA / Mês anterior | SUM(qtd_perda)*MAX(taxa)*AVERAGE(preço); U3M contexto completo/[DADO OMITIDO]; atividade não propaga à causa | mesmos componentes congelados; taxa global da dimensão; AP restringe chaves; sem fator inventado |
| Perda OSA / Média U3M | SUM(qtd_perda)*MAX(taxa)*AVERAGE(preço); U3M contexto completo/[DADO OMITIDO]; atividade não propaga à causa | mesmos componentes congelados; taxa global da dimensão; AP restringe chaves; sem fator inventado |
| ROI / Mês anterior | (sell-out-custo)/estoque_custo; guardas DAX; annual SUMX por YearMonth em janela [DADO OMITIDO]M | componentes com conversão contextual corrigida; C1[DADO OMITIDO] e U3M C0[DADO OMITIDO] mantidos |
| ROI / Média U3M | (sell-out-custo)/estoque_custo; guardas DAX; annual SUMX por YearMonth em janela [DADO OMITIDO]M | componentes com conversão contextual corrigida; C1[DADO OMITIDO] e U3M C0[DADO OMITIDO] mantidos |
| ROI / Anual [DADO OMITIDO]M | (sell-out-custo)/estoque_custo; guardas DAX; annual SUMX por YearMonth em janela [DADO OMITIDO]M | componentes com conversão contextual corrigida; C1[DADO OMITIDO] e U3M C0[DADO OMITIDO] mantidos |
| Venda custo / MTD | SUMX(volume*custo); sem fator aritmético, mas AP restringe os itens | sem multiplicação pela taxa; chaves AP aplicadas; BLANK de operandos residual C1[DADO OMITIDO] |
| Venda custo / Mês anterior | SUMX(volume*custo); sem fator aritmético, mas AP restringe os itens | sem multiplicação pela taxa; chaves AP aplicadas; BLANK de operandos residual C1[DADO OMITIDO] |
| Venda custo / Média U3M | SUMX(volume*custo); sem fator aritmético, mas AP restringe os itens | sem multiplicação pela taxa; chaves AP aplicadas; BLANK de operandos residual C1[DADO OMITIDO] |
| TVD - Pré-ruptura / MTD | sem fator; SUM simplificado na última data não BLANK; ALL(AP) na expressão principal | AP removido da soma; contexto da data continua residual F1[DADO OMITIDO] |
| TVD - Pré-ruptura / Mês anterior | sem fator; SUM simplificado na última data não BLANK; ALL(AP) na expressão principal | AP removido da soma; contexto da data continua residual F1[DADO OMITIDO] |
| TVD - Pré-ruptura / Média U3M | sem fator; SUM simplificado na última data não BLANK; ALL(AP) na expressão principal | AP removido da soma; contexto da data continua residual F1[DADO OMITIDO] |

## [DADO OMITIDO]. Ponte CNPJ

TOM confirma DIM_LOCAL.CNPJ ↔ DIM_CATALOGO_LOCAL.CNPJ: Many/Many, BothDirections, ativa. Local e catálogo são filtrados separadamente e intersectam CNPJ; fatos recebem chaves de localização válidas. EXISTS preserva duplicatas da dimensão sem multiplicar fatos. CNPJ BLANK usa IS NOT DISTINCT FROM, coerente com membro BLANK do modelo. Fixtures reais incluem duplicidades; o caso Local [DADO OMITIDO] tem Bandeira MIX ATACADO e o mesmo CNPJ no catálogo MATEUS SUPERMERCADOS: antigo filtro local falha, novo conjunto passa.

## [DADO OMITIDO]. Locais contratados

DIM_LOCAL no Power Query usa inner join AUX_CONTRATADO_LOCAL por retailer. AUX restringe cliente LACTALIS e exclui GPA/GPA2/MLUIZA. Catálogo global exclui Rede GPA; Status Contratado faz LOOKUPVALUE AUX. Os retailers AUX atuais são iguais aos da Gold DIM_LOCAL, verificados em leitura apenas. Teste inclui contratado e candidato não contratado avaliados no tenant [DADO OMITIDO]; o candidato é linha da dimensão global existente, não uma fato fabricada. Nenhuma linha foi inserida em produção.

## [DADO OMITIDO]. Rede não nula

Filtro oculto de página DIM_LOCAL[Rede] NOT null; aplica aos [DADO OMITIDO] pares KPI/período analisados nesta página. O predicado existe somente no pacote PBIP opt-in; outras páginas e contratos legados não foram alterados. Gold atual não possui Rede NULL, mas o teste isolado prova a exclusão.

## [DADO OMITIDO]. AP_CONVERSAO

DISTINCT nm_measure da dimensão, acrescido de literal valor. Slicer salvo unidade; bookmark LimpaFiltrosVGPN restaura unidade e tem strictSingleSelect. Bookmark ativo não é conhecido e não foi usado para inventar estado. Relação AP→DIM_CONVERSAO ativa Many/One. Sem seleção única: fator BLANK, chaves seguem conjunto de modos permitido na página; não se inventa fator [DADO OMITIDO].

## [DADO OMITIDO]. DIM_CONVERSAO

MAX(conversion_rate) é calculado na dimensão por tenant/nm, sem restrição inversa por produto, região ou fatos do mês. Microsoft TOM confirma DIM_ITENS→DIM_CONVERSAO no texto from/to, Many/Many, OneDirection; operacionalmente to filtra from, portanto DIM_CONVERSAO→DIM_ITENS. Esta direção foi provada no modelo inteiro desserializado, não suposta. Filtro AP restringe itens e então histórico/causas/daily. [Definição oficial da direção](https://learn.microsoft.com/en-us/dotnet/api/microsoft.analysisservices.tabular.crossfilteringbehavior?view=analysisservices-dotnet). Artefato: pbip_tom_relationships_2[DADO OMITIDO].json. Testemunho real: restringir o fator ao produto [DADO OMITIDO] daria [DADO OMITIDO]; MAX dimensional quilograma é [DADO OMITIDO] na Gold usada pelo teste. Isto prova uma diferença de SQL/contexto, não o KPI atual do Power BI.

## [DADO OMITIDO]. Opção valor

Excluída pelo filtro oculto/locked da página e pelo slicer AP nesta página. Outras páginas ainda podem usar valor, conforme seu próprio filtro. Em Venda Historico, valor é modo especial de faturamento com ALL(AP), não unidade com taxa [DADO OMITIDO]. DIM_CONVERSAO não contém taxa física valor. Medida nativa opt-in consulta a dimensão e exclui valor; a opção compartilhada legada permanece intacta.

## [DADO OMITIDO]. Ordem de aplicação

TVD/IVD não multiplicam taxa. Giro AVERAGE positivo força chaves unidade. OSA não multiplica taxa, mas AP restringe chaves. Perda OSA preserva SUM(qtd)*MAX(taxa)*AVERAGE(preço), U3M/[DADO OMITIDO] no contexto completo. Venda qtd usa SUMX(volume*Fator), implementado por linha. Estoque qtd usa SUM do último mês*Fator; stock_bundle já implementa U3M último mês/[DADO OMITIDO], portanto a suspeita de soma dos três meses foi descartada. Sell-out conserva receita/fallback por Região, com fator duas vezes no fallback; não se assume linearidade U3M. Venda/Estoque custo não multiplicam taxa, mas recebem filtro de chaves AP. ROI/Markup consomem esses componentes; C0[DADO OMITIDO]/C1[DADO OMITIDO] não são escondidos.

## [DADO OMITIDO]. Testes novos

[DADO OMITIDO] contratos executáveis: cinco de ponte/contratado/Rede; fator dimensional e ausência de propagação inversa; prova real de fator antigo diferente; valor; ausência de fator; quatro aliases de fato com correlação testada; seletor catálogo executado no caso real; SUMX por linha; Giro unidade; conjunto de chaves sem multiplicação; item sem modo; fórmulas OSA/perda congeladas e atividade não propagando à causa; exclusão de não lojas nos dois lados. Fixtures têm apenas linhas existentes, SQLite efêmero. Testemunhos BEFORE: pbip_filter_before_failure_2[DADO OMITIDO].json e pbip_conversion_direction_before_failure_2[DADO OMITIDO].json. Três testes inicialmente derivados da direção errada foram corrigidos com evidência TOM, sem alterar qualquer expected numérico de KPI para produzir PASS.

## [DADO OMITIDO]. Regressões

........................................................................ [ [DADO OMITIDO]]

........................................................................ [ [DADO OMITIDO]]

........................................................................ [ [DADO OMITIDO]]

........................................................................ [ [DADO OMITIDO]]

........................................................................ [ [DADO OMITIDO]]

..                                                                       [[DADO OMITIDO]]

[DADO OMITIDO] passed in [DADO OMITIDO]s

[DADO OMITIDO] regression checks passed (Superset dependency doubles).

{"pbip_contract":"passed","checks":[DADO OMITIDO],"loss_u3m":[DADO OMITIDO],"dax_period_formula":[DADO OMITIDO]}

ChartData default/filtrado e Guest RLS estão nos artefatos de runtime. A primeira tentativa de suíte completa no mount /workspace calculou ROOT errado e produziu FileNotFound; corrigido para /repo, sem alterar testes. A primeira tentativa frontend leu UTF-[DADO OMITIDO] como ANSI; corrigida a leitura, sem editar o bundle. O bootstrap inicial da etapa [DADO OMITIDO] precedeu o commit dos marts e falhou sem commit de metadata; repetido após publicação. Três tentativas de publicação da etapa [DADO OMITIDO] foram canceladas antes de commit e revertidas: agregado de quantidade repetido, alias das causas não correlacionado e plano dos seis modos com índice inadequado. A investigação de uma consulta somente leitura também atingiu timeout; isso não é PASS. Dois índices por customer/item nos marts de contexto eliminaram a varredura repetida por item. A publicação final foi atômica e concluída. CTE MATERIALIZED e remoção provada de guarda default já materializado corrigem o plano sem alterar fórmulas; o guarda não é removido dos detalhes filtrados ou de oportunidades raw. Esses erros operacionais não foram contabilizados como gates aprovados.

Gates finais: [DADO OMITIDO] testes Python (incluem os [DADO OMITIDO] anteriores e [DADO OMITIDO] novos contratos); [DADO OMITIDO] checks frontend; oito gráficos default e oito filtrados sem erro; Guest RLS com [DADO OMITIDO] probes de datasets e testes de seletores, override de tenant e assinatura. ChartData default: [DADO OMITIDO]s; filtrado: [DADO OMITIDO]s. Replay SQL somente leitura executado nos oito gráficos. Logs são evidência de regressão operacional, não prova de equivalência semântica completa.

## [DADO OMITIDO]. Arquivos alterados

Nesta etapa: filter_context.py, conversion_context.py, headlines.py, metadata.py, roteamento de semantics.py, bootstrap_overview.py e reconhecimento de fontes em validate_overview.py; migrations [DADO OMITIDO]/[DADO OMITIDO]; testes/fixture de filtros/conversão. Scripts SQL [DADO OMITIDO]/[DADO OMITIDO], context.py, presentation.py, frontend buildQuery/transformProps e os dois scripts locais foram preservados byte a byte desde o snapshot inicial desta etapa. Alterações já existentes nessas versões seguem no status; não foram reabertas.

## [DADO OMITIDO]. Marts afetados

Etapa [DADO OMITIDO] publicou nr_pbip_overview_semantic_v2, nr_pbip_giro_default e nr_pbip_daily_headlines. Os dois primeiros foram superados após a prova da direção. Etapa [DADO OMITIDO] publicou nr_pbip_overview_semantic_v3, nr_pbip_osa_semantic_v3 e nr_pbip_giro_v3; somente esses três são o caminho de conversão corrigido. TVD/IVD continuam nr_pbip_daily_headlines, com F1[DADO OMITIDO] explicitamente residual. Os novos objetos têm índices próprios. Também foram criados ix_nr_pbip_history_customer_item e ix_nr_pbip_causes_customer_item nos dois marts PBIP de contexto, sem alterar índices das tabelas Gold base. Nenhum mart/índice anterior foi apagado. O bootstrap usa uma amostra do mart correspondente apenas para introspecção de colunas e persiste o SQL interativo completo; não executa todo o contexto sem seleção para descobrir metadata. O detalhe de quantidade e os demais componentes compartilham history_filtered MATERIALIZED, mantendo o mesmo filtro e a mesma conversão por linha. As dependências são Gold e marts PBIP de contexto já existentes; sem reconstruir Bronze/Silver/Gold. SQL foi planejado em transação rollback antes de publicação. Artefatos intermediários são preservados e não certificados.

## [DADO OMITIDO]. Equivalência BEFORE/AFTER

| Etapa | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE | UNMAPPED | NO_PBI_VALUE |
|---|---:|---:|---:|---:|
| Antes | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| Após filtros | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| Após conversões | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |

[DADO OMITIDO] ocorrências de causas de conversão foram corrigidas: C0[DADO OMITIDO]=[DADO OMITIDO], C1[DADO OMITIDO]=[DADO OMITIDO], C1[DADO OMITIDO]=[DADO OMITIDO]. A parte SQL de C0[DADO OMITIDO] foi corrigida nos [DADO OMITIDO] pares, mas não é contada como eliminação completa da causa enquanto F1[DADO OMITIDO] permanecer. As [DADO OMITIDO] ocorrências corrigidas na etapa anterior foram preservadas. F1[DADO OMITIDO] impede equivalência integral mesmo nos pares cuja álgebra e filtro SQL foram corrigidos. Após filtros é classificação por cláusulas, sem alegar snapshot numérico intermediário. Nenhum NUMERIC_MATCH atribuído. ROI MTD permanece UNMAPPED; nenhum cartão criado.

## [DADO OMITIDO]. Divergências restantes

- **F1[DADO OMITIDO]**: Seletores: origem Rede/Bandeira foi corrigida para o catálogo em nr_pbip_filter_options. Permanece o DAG nativo propagando apenas pais para filhos, sem contexto bidirecional completo CNPJ entre os seletores; opções de produto ainda não recebem AP automaticamente. O filtro oculto de Item compara a medida Filtro Historico Com Dados com null; não foi convertido por suposição em COUNTROWS>[DADO OMITIDO]. Equivalência integral dos seletores/interações não certificada.
- **F1[DADO OMITIDO]**: TVD/IVD: a expressão LASTNONBLANK é argumento de filtro de CALCULATE, avaliada antes da remoção de AP_CONVERSAO na expressão principal. O SQL atual remove nm_measure da consulta inteira, incluindo a seleção de datas; falta separar o universo da data do universo da soma. Análise da ordem DAX, não inferência de valor atual; fonte: [Contexto e argumentos de CALCULATE](https://www.sqlbi.com/articles/context-transition-and-filters-in-calculate/).
- **C0[DADO OMITIDO]**: Sell-out U3M reavalia por Região no contexto completo U3M e divide por [DADO OMITIDO]; o frontend agrega resultados mensais. Receita positiva/fallback e média de preço tornam a operação não linear. Também afeta Markup/ROI U3M.
- **C0[DADO OMITIDO]**: TVD/IVD: SUM(COALESCE(...,[DADO OMITIDO])) e tratamento de datas totalmente nulas podem substituir BLANK por zero e alterar LASTNONBLANK. Fora do núcleo OSA congelado.
- **C1[DADO OMITIDO]**: Venda Custo/Estoque Custo: o SQL isolado ainda usa SUM(COALESCE(a,[DADO OMITIDO])*COALESCE(b,[DADO OMITIDO])); DAX SUMX(a*b) preserva BLANK quando todos os produtos são BLANK. Também afeta ROI/Markup que consomem esses componentes. Não alterado nesta etapa limitada a filtros/conversão.
- **C1[DADO OMITIDO]**: ROI/Markup: DAX usa comparações vSellOut=[DADO OMITIDO] e vVendaCusto=[DADO OMITIDO]; igualdade não estrita considera BLANK igual a [DADO OMITIDO]. O frontend usa ===[DADO OMITIDO] e depois retorna null para operandos null; quando ambos são BLANK retorna null, onde o DAX retorna [DADO OMITIDO]. Fórmula fora do escopo desta etapa; mantida e reportada, sem reabrir OSA. Fonte: [Operadores DAX e igualdade com BLANK](https://learn.microsoft.com/en-us/dax/dax-operator-reference).

## [DADO OMITIDO]. Justificativa individual

| KPI/período | Classificação | Causas exatas |
|---|---|---|
| MARKUP / MTD | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO], C1[DADO OMITIDO], C1[DADO OMITIDO] |
| MARKUP / Mês anterior | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO], C1[DADO OMITIDO], C1[DADO OMITIDO] |
| MARKUP / Média U3M | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO], C1[DADO OMITIDO], C1[DADO OMITIDO], C0[DADO OMITIDO] |
| Venda qtd / MTD | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO] |
| Venda qtd / Mês anterior | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO] |
| Venda qtd / Média U3M | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO] |
| Estoque qtd / MTD | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO] |
| Estoque qtd / Mês anterior | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO] |
| Estoque qtd / Média U3M | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO] |
| Giro / MTD | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO] |
| Giro / Mês anterior | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO] |
| Giro / Média U3M | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO] |
| Estoque custo / MTD | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO], C1[DADO OMITIDO] |
| Estoque custo / Mês anterior | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO], C1[DADO OMITIDO] |
| Estoque custo / Média U3M | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO], C1[DADO OMITIDO] |
| IVD - Excesso / MTD | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO], F1[DADO OMITIDO], C0[DADO OMITIDO] |
| IVD - Excesso / Mês anterior | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO], F1[DADO OMITIDO], C0[DADO OMITIDO] |
| IVD - Excesso / Média U3M | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO], F1[DADO OMITIDO], C0[DADO OMITIDO] |
| Venda sell out / MTD | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO] |
| Venda sell out / Mês anterior | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO] |
| Venda sell out / Média U3M | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO], C0[DADO OMITIDO] |
| OSA / MTD | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO] |
| OSA / Mês anterior | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO] |
| OSA / Média U3M | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO] |
| Perda OSA / MTD | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO] |
| Perda OSA / Mês anterior | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO] |
| Perda OSA / Média U3M | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO] |
| ROI / Mês anterior | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO], C1[DADO OMITIDO], C1[DADO OMITIDO] |
| ROI / Média U3M | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO], C1[DADO OMITIDO], C1[DADO OMITIDO], C0[DADO OMITIDO] |
| ROI / Anual [DADO OMITIDO]M | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO], C1[DADO OMITIDO], C1[DADO OMITIDO] |
| Venda custo / MTD | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO], C1[DADO OMITIDO] |
| Venda custo / Mês anterior | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO], C1[DADO OMITIDO] |
| Venda custo / Média U3M | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO], C1[DADO OMITIDO] |
| TVD - Pré-ruptura / MTD | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO], F1[DADO OMITIDO], C0[DADO OMITIDO] |
| TVD - Pré-ruptura / Mês anterior | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO], F1[DADO OMITIDO], C0[DADO OMITIDO] |
| TVD - Pré-ruptura / Média U3M | SEMANTIC_DIFFERENCE | F1[DADO OMITIDO], F1[DADO OMITIDO], C0[DADO OMITIDO] |
| ROI / MTD | UNMAPPED | ROI MTD sem visual correspondente no PBIP desta página |

Cada causa está explicada por extenso em remaining_justification no JSON, com SQL persistido, DAX closure e matriz de filtros. O filtro oculto do seletor Item permanece não certificado; sua comparação serializada com null não foi traduzida pelo nome da medida. Fonte PBIP PARTICULAR/LACTALIS versus Gold DAILY [DADO OMITIDO] é limitação de linhagem separada: não prova identidade de valores.

## [DADO OMITIDO]. git diff --stat

```text
 scripts/publish_lactalis_marts.py                  | [DADO OMITIDO] +++++++++++++++++++++-
 superset/bootstrap_overview.py                     | [DADO OMITIDO] ++++++++++++++++-----
 .../plugin-chart-neoretail-kpi/src/buildQuery.js   | [DADO OMITIDO] +++-
 .../src/transformProps.js                          | [DADO OMITIDO] ++++++++++++++---
 superset/validate_overview.py                      | [DADO OMITIDO] +++++++++++-
 [DADO OMITIDO] files changed, [DADO OMITIDO] insertions(+), [DADO OMITIDO] deletions(-)
```

git diff --stat não inclui arquivos untracked; a seção [DADO OMITIDO] e o status abaixo incluem as adições.

## [DADO OMITIDO]. git status --short

```text
 M scripts/publish_lactalis_marts.py
 M superset/bootstrap_overview.py
 M superset/frontend-plugin/plugin-chart-neoretail-kpi/src/buildQuery.js
 M superset/frontend-plugin/plugin-chart-neoretail-kpi/src/transformProps.js
 M superset/validate_overview.py
?? analytics-db/marts/[DADO OMITIDO]_pbip_overview_calendar.sql
?? analytics-db/marts/[DADO OMITIDO]_pbip_overview_context.sql
?? analytics-db/marts/[DADO OMITIDO]_pbip_filters_conversion.sql
?? analytics-db/marts/[DADO OMITIDO]_pbip_conversion_direction.sql
?? local-engine/tests/fixtures/pbip_filters_conversion_real_rows_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_lactalis_overview_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_lactalis_real_contract_rows_2[DADO OMITIDO].json
?? local-engine/tests/test_pbip_filter_conversion_contract.py
?? local-engine/tests/test_pbip_lactalis_overview.py
?? superset/diagnose_lactalis_inventory.py
?? superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/pbip-contract.mjs
?? superset/neoretail_bootstrap/pbip_overview/
?? superset/profile_lactalis_osa_filtered.py
```

## [DADO OMITIDO]. Sem commit/push

Branch feat/osa-industry-certification; HEAD [DADO OMITIDO]d2f5[DADO OMITIDO]b5[DADO OMITIDO]ead1bae9af6d2ef7b7[DADO OMITIDO]f9a4[DADO OMITIDO]ae. Nenhum commit, push, merge, rebase ou troca de branch. Main não alterada. Dois scripts untracked preservados. Nenhum volume Docker apagado e nenhum pipeline base reprocessado.

Relatório não declara certificação completa: [DADO OMITIDO] pares continuam SEMANTIC_DIFFERENCE pelas causas enumeradas, e [DADO OMITIDO] continuam NO_PBI_VALUE.
