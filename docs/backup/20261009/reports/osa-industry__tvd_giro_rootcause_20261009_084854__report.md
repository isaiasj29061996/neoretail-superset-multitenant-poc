> Cópia para GitHub: números de origem e identificadores numéricos omitidos. Original integral exige backup externo. Não usar esta cópia como fixture ou SQL executável.

# TVD, Giro, IVD e tarefas — causa raiz LACTALIS [DADO OMITIDO]

Investigação em [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO]. Nenhuma implementação alterada. Pipeline existente até [DADO OMITIDO]/[DADO OMITIDO]; consultas de corte [DADO OMITIDO]/[DADO OMITIDO] somente leitura. Evidências novas nesta pasta; fontes Azure lidas sem ingestão/publicação. Os valores do print são arredondados; os valores abaixo das fontes Azure não são apresentados como exportações do modelo importado no Power BI.

## Conclusões comprovadas

[DADO OMITIDO]. **As fontes não são numericamente equivalentes.** O PBIP lê `PARTICULAR_3/LACTALIS/PARTICULAR_FATO_IVD_TVD_*`, `PARTICULAR_FATO_HISTORICO_*` e `ETL_CALC_V2*`. O local deriva esses contratos a partir de `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS/`. A reconstrução mantém nomes, mas não os mesmos valores/NULLs/populações.
[DADO OMITIDO]. **[DADO OMITIDO]/[DADO OMITIDO] × [DADO OMITIDO]/[DADO OMITIDO] explica parte do MTD, não os meses anteriores nem Giro.** TVD local no corte correto é [DADO OMITIDO]; IVD [DADO OMITIDO]. As duas referências permanecem diferentes do PBI.
[DADO OMITIDO]. **Tarefas zeradas têm causa na origem local:** `REGRA_CRITICO := tp_activity_level`, sem nenhuma linha `CRITICO` ou `F`. Não é apenas formatação do componente.
[DADO OMITIDO]. **Nova diferença semântica comprovada nas tarefas IVD:** DAX `Aviso IVD Risco` exige `Nivel de atividade IVD = "Ultra Slow Mover"`, isto é, regra `U`; SQL local exige regra `F`. Não foi corrigida. O baseline histórico [DADO OMITIDO] MATCH / [DADO OMITIDO] DIFFERENCE / [DADO OMITIDO] UNMAPPED foi preservado sem reclassificação; ele não elimina este novo achado fora da evidência anterior.

## Filtros e período

Página PBIP `b4da2[DADO OMITIDO]ee4[DADO OMITIDO]`, a mesma URL do print: Visão geral [DADO OMITIDO] — visão indústria / Valor. Tenant/fabricante LACTALIS, [DADO OMITIDO]. Unidade `unidade`; rede, bandeira, UF/cidade, tipo/loja, atividade, marca, hierarquias e item em Todos no print. Defaults atuais do Superset confirmam `unidade` e demais seletores sem restrição.

Filtros ocultos PBIP: AP_CONVERSAO diferente de `valor`, DIM_LOCAL.Rede não BLANK, catálogo Status Contratado = Contratado; catálogo/locais e AUX são implementados localmente por EXISTS, excluindo GPA. Medidas TVD/IVD excluem DEPÓSITO, CD, LOJA VIRTUAL em ambas as dimensões. Giro não herda essa exclusão específica. Barras de Giro têm filtros de atividade adicionais; o cartão Giro não tem filtro próprio. Definições completas: `pbip_target_page.json`, `runtime_readonly.json`, helpers de origem e SQL exportado.

Superset tem âncora [DADO OMITIDO]/[DADO OMITIDO] e calendário até [DADO OMITIDO]/[DADO OMITIDO], M0 outubro, M-[DADO OMITIDO] setembro, U3M julho/agosto/setembro. PBI informa último movimento [DADO OMITIDO]/[DADO OMITIDO] e M-[DADO OMITIDO] setembro. O corte foi inserido **antes** do LASTNONBLANK no SQL de evidência; filtrar apenas a saída seria incorreto. O print não comprova todos os filtros persistidos/bookmarks do Service nem a versão importada das dimensões; esses permanecem pendentes.

## Reprodução local e impacto de datas

| Indicador | Local [DADO OMITIDO]/[DADO OMITIDO] | Local corte [DADO OMITIDO]/[DADO OMITIDO] | Print PBI |
|---|---:|---:|---:|
| TVD MTD | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] mi |
| TVD mês anterior | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] mi |
| TVD U3M | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] mi |
| IVD MTD | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] mi |
| IVD mês anterior | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] mi |
| IVD U3M | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] mi |
| Giro MTD | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| Giro mês anterior | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| Giro U3M ponderado | ~[DADO OMITIDO] | ~[DADO OMITIDO] | [DADO OMITIDO] |

Giro [DADO OMITIDO]/[DADO OMITIDO] foi reconstruído em memória do Bronze existente, aplicando a mesma média por item/loja/mês da implementação, depois média de positivos. A reprodução [DADO OMITIDO]/[DADO OMITIDO] concorda com o mart ([DADO OMITIDO] grupos positivos). Nenhuma camada foi regravada.

Fato diário: [DADO OMITIDO] linhas em [DADO OMITIDO]/[DADO OMITIDO]; [DADO OMITIDO] em [DADO OMITIDO]/[DADO OMITIDO]; [DADO OMITIDO] em [DADO OMITIDO]/[DADO OMITIDO]. É cobertura desigual observada, não prova de falha de ingestão: a fonte PBIP também tem exatamente essas quantidades nas duas últimas datas. LASTNONBLANK escolhe o último dia global com soma não BLANK; não recompõe último movimento por loja. Não propomos mudar essa regra DAX.

## Confronto direto com a fonte indicada pelo PBIP

Recortes Azure com ETags verificados, mesmas chaves locais de localização/item para os filtros; sem executar Power BI Desktop. Arquivos e versões em `pbip_source_inventory.json` e `source_slices_manifest.json`.

| Indicador | Fonte PBIP atual sob contexto local | Local no mesmo corte |
|---|---:|---:|
| TVD [DADO OMITIDO]/[DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| TVD setembro | [DADO OMITIDO] | [DADO OMITIDO] |
| TVD U3M | [DADO OMITIDO] | [DADO OMITIDO] |
| IVD [DADO OMITIDO]/[DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| IVD setembro | [DADO OMITIDO] | [DADO OMITIDO] |
| IVD U3M | [DADO OMITIDO] | [DADO OMITIDO] |
| Giro outubro | [DADO OMITIDO] | [DADO OMITIDO] |
| Giro setembro | [DADO OMITIDO] | [DADO OMITIDO] |
| Giro U3M ponderado | [DADO OMITIDO] | ~[DADO OMITIDO] |

TVD setembro/U3M e IVD MTD/setembro da fonte são compatíveis com o arredondamento do print. **TVD MTD [DADO OMITIDO] não prova o print [DADO OMITIDO] mi; Giro [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] não prova [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO]; IVD U3M [DADO OMITIDO] mi não prova [DADO OMITIDO] mi.** Diferenças residuais exigem o snapshot/ETags e contexto efetivamente importados no PBI, não uma correção presumida. Há arquivos de histórico atualizados em horários distintos em [DADO OMITIDO] e [DADO OMITIDO]/[DADO OMITIDO] (inclusive NovoAtacado em [DADO OMITIDO]/[DADO OMITIDO] [DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO] UTC).

## Registros, NULLs e joins

Nas cinco datas [DADO OMITIDO]/[DADO OMITIDO], [DADO OMITIDO]/[DADO OMITIDO], [DADO OMITIDO]/[DADO OMITIDO], [DADO OMITIDO]/[DADO OMITIDO] e [DADO OMITIDO]/[DADO OMITIDO], o FULL OUTER equivalente por data+item+loja encontrou **zero chaves exclusivas em cada lado e zero multiplicação**. Quantidades respectivas: [DADO OMITIDO], [DADO OMITIDO], [DADO OMITIDO], [DADO OMITIDO], [DADO OMITIDO]. Portanto a grande diferença diária já está no conteúdo das mesmas linhas, antes dos joins/visuais.

Exemplo [DADO OMITIDO]/[DADO OMITIDO]: TVD NULL local **[DADO OMITIDO]/[DADO OMITIDO]**, contra **[DADO OMITIDO]/[DADO OMITIDO]** na fonte PBIP. Em [DADO OMITIDO]/[DADO OMITIDO]: **[DADO OMITIDO]/[DADO OMITIDO]**, contra **[DADO OMITIDO]/[DADO OMITIDO]**. `vl_tvd` mapeado diretamente para `tvd_simplificado` não equivale numericamente à coluna pronta `TVD_SIMPLIFICADO`. Não substituir NULL por zero: alteraria o contrato BLANK/LASTNONBLANK.

DIM_ITENS local tem [DADO OMITIDO] linhas e [DADO OMITIDO] chaves distintas, nenhuma NULL; LEFT JOIN por tenant+item não multiplica. Filtros de catálogo/conversão usam EXISTS, evitando multiplicação por relações muitos-para-muitos. A unidade seleciona o conjunto de itens na busca de data; `ALL(AP_CONVERSAO)` limpa esse filtro no valor TVD/IVD, sem multiplicar por fator. Giro força unidade e usa positivos; U3M divide soma dos numeradores pela soma das contagens, não média simples das três médias.

Histórico julho–outubro: local **[DADO OMITIDO]** linhas, fonte PBIP **[DADO OMITIDO]**; interseção **[DADO OMITIDO]**, local-only **[DADO OMITIDO]**, PBIP-only **[DADO OMITIDO]**, sem multiplicação nesse confronto. Além da população diferente, a implementação cria `GIRO = AVG(vl_average_monthly_stock_turnover)` por item/loja/mês. O PBIP lê `GIRO` pronto e aplica AVERAGE dos positivos. Nem fator fixo ×[DADO OMITIDO], nem simples troca de escala está justificada. Evidência completa: `source_comparison.json`.

## Por que IVD setembro parece próximo

Com mesmos filtros, a fonte PBIP resulta em [DADO OMITIDO] e a local em [DADO OMITIDO]: diferença **[DADO OMITIDO] (~[DADO OMITIDO])**. Em [DADO OMITIDO]/[DADO OMITIDO], fonte PBIP [DADO OMITIDO] versus local [DADO OMITIDO]: diferença **[DADO OMITIDO] (~[DADO OMITIDO])**. A proximidade de setembro é agregada e não comprova igualdade de linhas: das [DADO OMITIDO] chaves de setembro, somente [DADO OMITIDO] valores IVD passam no teste aproximado `numpy.isclose` usado no diagnóstico. Não é contagem de igualdade exata. Somar divergências pode compensá-las. Usar [DADO OMITIDO]/[DADO OMITIDO] adiciona outro efeito: queda local de [DADO OMITIDO] em relação a [DADO OMITIDO]/[DADO OMITIDO].

## Tarefas

Local: [DADO OMITIDO] linhas; regras I=[DADO OMITIDO], N=[DADO OMITIDO], U=[DADO OMITIDO], W=[DADO OMITIDO]; nenhuma F/CRITICO; todos os ALERTA_TVD/IVD NULL. A derivação usa o último registro diário por item/loja e copia atividade para regra. PBIP lê ETL_CALC_V2 pronto: **[DADO OMITIDO] chaves únicas**, [DADO OMITIDO] após o contexto de localização/item utilizado.

Fonte PBIP filtrada: TVD crítico **[DADO OMITIDO]**, risco F **[DADO OMITIDO]**; IVD crítico **[DADO OMITIDO]**, risco U **[DADO OMITIDO]**. Os três primeiros reproduzem os prints. IVD risco difere em **[DADO OMITIDO]** de [DADO OMITIDO] e exige snapshot/contexto PBI para fechar. Aplicar F ao IVD nessa mesma fonte daria [DADO OMITIDO], demonstrando que apenas restaurar as regras da fonte não corrigiria o predicado local de risco IVD.

## Rastro da implementação e proposta mínima — não executada

- TVD/IVD: `partitioned_daily.py` → Gold `fato_ivd_tvd` → dataset SQL `daily_context_sql` → charts **[DADO OMITIDO]/[DADO OMITIDO]** → `transformProps.js` perfil direct_average; marts diários/headlines são auxiliares, não substituem o SQL dinâmico inspecionado.
- Giro: `_periodic` → Gold histórico → `nr_pbip_overview_history` → `nr_pbip_giro_v3` → dataset **[DADO OMITIDO]** → chart **[DADO OMITIDO]**, perfil weighted_average. SQL detalhado é usado quando existem filtros dimensionais.
- Tarefas: oportunidades derivadas → Gold `calculo_oportunidades` → CTE tasks nos datasets → critical/risk do componente.

Menor correção candidata para investigação posterior: fazer a entrada LACTALIS desses contratos consumir os artefatos prontos que o PBIP consome, com tenant [DADO OMITIDO] explícito, mesmas chaves/NULLs e versão/corte acordados; validar em staging isolado antes de publicar. Alternativa: especificar e reproduzir exatamente o ETL legado, mas sua regra não está descrita no DAX/PQ e não pode ser inventada. Separadamente, corrigir risco IVD para a condição Ultra Slow Mover comprovada. **Nada disso foi implementado ou autorizado por este relatório.** Não alterar o DAX para encaixar valores locais.

Pendências mínimas: exportação PBI sem arredondamento dos nove cartões e tarefas; contexto efetivo/exportação de filtros e bookmarks; snapshot/ETags importados das três famílias e dimensões; amostra data+item+loja com TVD_SIMPLIFICADO/IVD_SIMPLIFICADO/GIRO/REGRA_CRITICO. A fórmula interna que produz os artefatos prontos não está no PBIP; este apenas os importa.

## Preservação e evidências

[DADO OMITIDO] testes relevantes aprovados ([DADO OMITIDO] warning), em `semantic_tests.log`. Hashes das fontes mantidos, git status idêntico ao início ([DADO OMITIDO] modificados e [DADO OMITIDO] entradas não rastreadas preexistentes), parâmetros/SQL/dashboard iguais entre leituras desta investigação. Baseline histórico [DADO OMITIDO] MATCH / [DADO OMITIDO] DIFFERENCE / [DADO OMITIDO] UNMAPPED preservado; não confundir com aprovação da nova divergência de tarefas. Nenhum pipeline, refresh de mart, alteração de fórmula/RLS/Guest/Embedded, exclusão de volume, commit ou push.

SQL executado está nos arquivos `.sql` desta pasta: `tvd_2[DADO OMITIDO][DADO OMITIDO][DADO OMITIDO].sql`, `ivd_2[DADO OMITIDO][DADO OMITIDO][DADO OMITIDO].sql`, versões [DADO OMITIDO]/[DADO OMITIDO], `daily_raw_vs_filtered.sql`, `task_population.sql`, `giro_current.sql` e exports de chaves. Resultados em `sql_results.json`. Comparação Parquet reproduzível em `compare_sources.py`, recortes em `source_slices/`, reconstrução de Giro em `giro_cutoff_reconstruction.py/json`. `preservation.json`, `git_before.txt`, `git_after.txt` documentam preservação. Evidências anteriores não foram sobrescritas.
