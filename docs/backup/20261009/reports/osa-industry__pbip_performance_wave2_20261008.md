> Cópia para GitHub: números de origem e identificadores numéricos omitidos. Original integral exige backup externo. Não usar esta cópia como fixture ou SQL executável.

# Performance wave [DADO OMITIDO] — encerrada

**performance estrutural mínima segura encontrada = [DADO OMITIDO]s**, no lote API paralelo sem cache. Não atingiu <[DADO OMITIDO]s. Nenhuma mudança mantida; speedup atribuível à implementação: **[DADO OMITIDO]×**. Medida HTTP, sem incluir renderização no navegador.

| Top [DADO OMITIDO] no baseline default | Tempo / parcela dos [DADO OMITIDO]s | Gargalo do EXPLAIN ANALYZE | Menor risco avaliado |
|---|---:|---|---|
| IVD | [DADO OMITIDO]s / [DADO OMITIDO] | Dois contextos distintos varrem o fato diário de [DADO OMITIDO] milhões de linhas | Reuso de CTE já sem ganho estável na wave [DADO OMITIDO]; não repetir nem fundir contextos |
| TVD | [DADO OMITIDO]s / [DADO OMITIDO] | Scans e joins do fato diário para calendário/AP e valores | Índice de data já rejeitado na wave [DADO OMITIDO]; cobertura ampla/preagregação exigiria ampliar escopo |
| Markup U3M | [DADO OMITIDO]s / [DADO OMITIDO] | Materialização de [DADO OMITIDO] linhas mensais com verificações C1[DADO OMITIDO]; agregado precisa de scope all e U3M | Antecipar exatamente esses predicados em frozen_monthly |

No filtrado, maiores custos anteriores: IVD [DADO OMITIDO]s ([DADO OMITIDO]), OSA [DADO OMITIDO]s ([DADO OMITIDO]), TVD [DADO OMITIDO]s ([DADO OMITIDO]).

**Único experimento novo:** antecipação dos predicados existentes, em consultas read-only, sem publicação. Default: Markup [DADO OMITIDO]→[DADO OMITIDO]s; ROI [DADO OMITIDO]→[DADO OMITIDO]s; Venda [DADO OMITIDO]→[DADO OMITIDO]s. Filtrado: Markup [DADO OMITIDO]→[DADO OMITIDO]s; ROI **[DADO OMITIDO]→[DADO OMITIDO]s**; Venda [DADO OMITIDO]→[DADO OMITIDO]s. Seis result sets equivalentes, incluindo tipos, linhas e NULL, contra a referência congelada (float: tolerância [DADO OMITIDO] relativa/[DADO OMITIDO] absoluta). **Descartado por regressão filtrada.** Nenhum índice/mart/materialização foi adicionado nesta rodada. Parada: próximo trabalho nos fatos diários exige maior intervenção; não perseguir [DADO OMITIDO]s.

| Performance | Baseline wave [DADO OMITIDO] | Final wave [DADO OMITIDO], SQL preservado |
|---|---:|---:|
| SQL default, soma sequencial | [DADO OMITIDO]s | [DADO OMITIDO]s |
| SQL filtrado, soma sequencial | [DADO OMITIDO]s | [DADO OMITIDO]s |
| API default, [DADO OMITIDO] requests paralelos force=true | [DADO OMITIDO]s | [DADO OMITIDO]s |
| API filtrada, [DADO OMITIDO] requests paralelos force=true | [DADO OMITIDO]s | [DADO OMITIDO]s |

Diferenças de tempo sem mudança mantida são variação de execução; não representam otimização comprovada.

**Gates essenciais:** [DADO OMITIDO] testes Python; [DADO OMITIDO] checks PBIP frontend + [DADO OMITIDO] genéricos; ChartData [DADO OMITIDO] default + [DADO OMITIDO] filtrados ([DADO OMITIDO] resultados comparados); [DADO OMITIDO] probes Guest/RLS; [DADO OMITIDO] pares replay SQL com testemunhas C1[DADO OMITIDO]; [DADO OMITIDO] queries diretas com tipos/valores/NULL/linhas preservados. Todos passaram. Fontes semânticas, datasets SQL, parâmetros dos charts, metadados, [DADO OMITIDO] definições de marts e índices conferidos sem alteração.

**Semântica congelada:** [DADO OMITIDO] MATCH / [DADO OMITIDO] DIFFERENCE / [DADO OMITIDO] UNMAPPED. Contrato completo continua [DADO OMITIDO] / [DADO OMITIDO] / [DADO OMITIDO]. **NO_PBI_VALUE = [DADO OMITIDO]**; nenhum valor Power BI inventado.

**Git:** status idêntico ao início ([DADO OMITIDO] modificados, [DADO OMITIDO] entradas não rastreadas); branch feat/osa-industry-certification, HEAD [DADO OMITIDO]d2f5[DADO OMITIDO]b5[DADO OMITIDO]. [Status completo](pbip_performance_wave2_git_status_2[DADO OMITIDO].txt). Sem commit/push, troca de branch, reprocessamento Bronze/Silver/Gold ou alteração de volumes.

**Limitação dos artefatos:** o instrumento inicial sobrescreveu seis JSONs auxiliares da wave [DADO OMITIDO]. Candidatos foram preservados em nomes wave2; SQL/referência e tempos/resumos históricos foram reconstruídos das fontes intactas, com nota explícita. Os seis planos completos históricos estão indisponíveis. Código e dados não foram afetados.

[Evidência final dos gates e medidas](pbip_performance_wave2_freeze_2[DADO OMITIDO].json).
