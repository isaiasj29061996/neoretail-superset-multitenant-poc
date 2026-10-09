> Cópia para GitHub: números de origem e identificadores numéricos omitidos. Original integral exige backup externo. Não usar esta cópia como fixture ou SQL executável.

# LACTALIS — F1[DADO OMITIDO]: seletores BEFORE/AFTER

**F1[DADO OMITIDO] foi corrigida parcialmente e permanece residual nos [DADO OMITIDO] pares. Não há certificação integral nem NUMERIC_MATCH.**

Worktree .worktrees/osa-industry; branch feat/osa-industry-certification; tenant [DADO OMITIDO]. Nenhuma causa F1[DADO OMITIDO]/C0[DADO OMITIDO]/C0[DADO OMITIDO]/C1[DADO OMITIDO]/C1[DADO OMITIDO] foi reaberta. Calendário, OSA, perda U3M, atividade, conversão, ponte SQL dos KPIs e marts publicados foram preservados.

## [DADO OMITIDO]. Freeze e estado inicial

Snapshot antes de qualquer edição: pbip_f1[DADO OMITIDO]_stage_before_2[DADO OMITIDO].json. Todos os hashes existentes conferem, exceto bootstrap_overview.py, alterado somente para os datasets/configurações de seletores e seus rótulos. Os oito charts têm os mesmos parâmetros, IDs e SQL; as [DADO OMITIDO] definições dos marts PBIP também são iguais. Dois scripts locais untracked e todos os testes anteriores intactos.

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

```text
 scripts/publish_lactalis_marts.py                  | [DADO OMITIDO] +++++++++++++++++++++-
 superset/bootstrap_overview.py                     | [DADO OMITIDO] ++++++++++++++++-----
 .../plugin-chart-neoretail-kpi/src/buildQuery.js   | [DADO OMITIDO] +++-
 .../src/transformProps.js                          | [DADO OMITIDO] ++++++++++++++---
 superset/validate_overview.py                      | [DADO OMITIDO] +++++++++++-
 [DADO OMITIDO] files changed, [DADO OMITIDO] insertions(+), [DADO OMITIDO] deletions(-)
```

## [DADO OMITIDO]. Grafo real PBIP e DAG condensada

A ponte BothDirections forma um ciclo. Portanto o grafo completo não é uma DAG; a DAG de componentes agrupa Local e Catálogo no mesmo componente. As dependências abaixo vêm das relações TOM ativas e dos campos do PBIP, não da posição visual.

```mermaid
flowchart LR
  AP[AP_CONVERSAO] --> CONV[DIM_CONVERSAO]
  CONV --> ITEM[DIM_ITENS: Marca / Hierarquias / Item]
  LOC[DIM_LOCAL: UF / Cidade / Tipo / Loja] <-->|CNPJ Many/Many BothDirections| CAT[DIM_CATALOGO_LOCAL: Rede / Bandeira]
  LOC --> FACT[Fatos]
  ITEM --> FACT
  ACT[DIM_NIVEL_ATIVIDADE] --> FACT
  CAL[Calendário congelado] --> FACT
```

Não existem arestas ordinárias Produto→AP, Produto→MAX taxa, fato→Local/Produto ou Local→Produto. O filtro de medida do seletor Item é uma condição adicional separada e ainda não certificada.

## [DADO OMITIDO]. DAG Superset antes

```mermaid
flowchart LR
  Rede --> Bandeira
  UF --> Cidade
  Tipo --> Loja
  Marca --> H1 --> H2 --> H3 --> Item
```

AP e atividade eram independentes; AP não limitava opções de produto. O catálogo/local já usava tuplas CNPJ no dataset [DADO OMITIDO], mas o frontend só enviava pais da DAG, perdendo o sentido inverso e combinações entre controles.

## [DADO OMITIDO]. Contexto Superset depois

```mermaid
flowchart LR
  GEO[Outros campos Local/Catálogo selecionados] --> GO[Opções do campo geográfico solicitado]
  AP[AP selecionado] --> PO[Opções Produto / Marca / Hierarquias]
  PROD[Outros campos Produto selecionados] --> PO
  APDIM[Dimensão conversão] --> AO[Opções AP independentes de produto]
  ACTDIM[Dimensão atividade] --> ACO[Opções atividade]
```

pbipContextParentIds fornece data masks diretos ao hook; cascadeParentIds fica vazio no opt-in. Isso evita representar o ciclo como uma cascata destrutiva. O caminho legado usa os cascadeParentIds originais. Cada consulta exclui sua seleção própria, intersecta os demais campos permitidos e preserva ILIKE de busca. Não há consultas por opção nem joins a fatos.

## [DADO OMITIDO]. Inventário por seletor

O PBIP tem oito visuais slicer; o Superset expõe [DADO OMITIDO] controles planos. Região é atributo/modelo relevante, mas não um slicer visível nesta página: não foi inventado um controle Região. Projeções active=false são níveis da hierarquia, não visuais separados.

| Visual PBIP | Origem e campos | Seleção | SyncGroup | Filtro próprio |
|---|---|---|---|---|
| [DADO OMITIDO]c7[DADO OMITIDO]a5b6[DADO OMITIDO]bcecb | DIM_ITENS[Hierarquia [DADO OMITIDO]], DIM_ITENS[Hierarquia [DADO OMITIDO]], DIM_ITENS[Hierarquia [DADO OMITIDO]] | multi | NM_HIERARCHY_LEVEL_1 | nenhum declarado |
| [DADO OMITIDO]f4ef5a9[DADO OMITIDO]c0[DADO OMITIDO] | DIM_ITENS[Descrição marca] | multi | NM_BRAND | nenhum declarado |
| [DADO OMITIDO]d5e7efab0[DADO OMITIDO]d2[DADO OMITIDO]a5[DADO OMITIDO] | DIM_LOCAL[UF], DIM_LOCAL[Cidade] | multi | UF | nenhum declarado |
| [DADO OMITIDO]f6c2[DADO OMITIDO]dd4[DADO OMITIDO]c3[DADO OMITIDO]b5[DADO OMITIDO]bd | DIM_ITENS[Item] | multi | Item | Item medida != null |
| [DADO OMITIDO]ffb4dd6[DADO OMITIDO]bb6[DADO OMITIDO]ac | DIM_NIVEL_ATIVIDADE[NM_ACTIVITY_LEVEL] | multi | nm_activity_level1 | NM_ACTIVITY_LEVEL NOT null |
| ad3[DADO OMITIDO]f9b0[DADO OMITIDO]ebe5 | AP_CONVERSAO[nm_measure] | strict single | nm_measure | NOT valor; hidden no visual |
| e2b3d1e3e2[DADO OMITIDO]eca2[DADO OMITIDO]a | DIM_LOCAL[TIPO_LOCAL], DIM_LOCAL[Loja] | multi | TIPO_LOCAL | nenhum declarado |
| feab3[DADO OMITIDO]d9[DADO OMITIDO]fae8[DADO OMITIDO]c3[DADO OMITIDO] | DIM_CATALOGO_LOCAL[Rede], DIM_CATALOGO_LOCAL[Bandeira] | multi | Rede | nenhum declarado |

| Controle Superset | Dataset virtual | Contextos enviados à consulta de opções |
|---|---|---|
| nm_measure | nr_pbip_options_nm_measure (ID [DADO OMITIDO]) | independente |
| rede | nr_pbip_options_rede (ID [DADO OMITIDO]) | bandeira, uf, cidade, tipo_local, loja |
| bandeira | nr_pbip_options_bandeira (ID [DADO OMITIDO]) | rede, uf, cidade, tipo_local, loja |
| uf | nr_pbip_options_uf (ID [DADO OMITIDO]) | rede, bandeira, cidade, tipo_local, loja |
| cidade | nr_pbip_options_cidade (ID [DADO OMITIDO]) | rede, bandeira, uf, tipo_local, loja |
| tipo_local | nr_pbip_options_tipo_local (ID [DADO OMITIDO]) | rede, bandeira, uf, cidade, loja |
| loja | nr_pbip_options_loja (ID [DADO OMITIDO]) | rede, bandeira, uf, cidade, tipo_local |
| tp_activity_level | nr_pbip_options_tp_activity_level (ID [DADO OMITIDO]) | independente |
| descricao_marca | nr_pbip_options_descricao_marca (ID [DADO OMITIDO]) | item, hierarquia_1, hierarquia_2, hierarquia_3, nm_measure |
| hierarquia_1 | nr_pbip_options_hierarquia_1 (ID [DADO OMITIDO]) | item, descricao_marca, hierarquia_2, hierarquia_3, nm_measure |
| hierarquia_2 | nr_pbip_options_hierarquia_2 (ID [DADO OMITIDO]) | item, descricao_marca, hierarquia_1, hierarquia_3, nm_measure |
| hierarquia_3 | nr_pbip_options_hierarquia_3 (ID [DADO OMITIDO]) | item, descricao_marca, hierarquia_1, hierarquia_2, nm_measure |
| item | nr_pbip_options_item (ID [DADO OMITIDO]) | descricao_marca, hierarquia_1, hierarquia_2, hierarquia_3, nm_measure |

Inventário literal completo: [pbip_f1[DADO OMITIDO]_selector_inventory_2[DADO OMITIDO].json](pbip_f1[DADO OMITIDO]_selector_inventory_2[DADO OMITIDO].json), com filtros report/page/visual, objetos, single/multi-select, sync, bookmark e interações. sortDefinition ausente nos oito visuais: ordenação/collation não certificada. A seleção AP salva e o bookmark LimpaFiltrosVGPN usam unidade. Bookmark ativo não identificado; não foi inventado estado corrente.

## [DADO OMITIDO]. CNPJ, contratado e Rede null

DIM_LOCAL[CNPJ] ↔ DIM_CATALOGO_LOCAL[CNPJ], ativa Many/Many BothDirections, comprovada no TOM. Cada lado recebe somente seus filtros, depois EXISTS intersecta CNPJs com IS NOT DISTINCT FROM. DISTINCT retorna opções como conjunto; duplicidade não multiplica opções ou fatos. Nenhum KPI passou a usar estes datasets como fato.

DIM_LOCAL permanece o universo Power Query contratado por retailer/AUX, previamente verificado; catálogo usa o conjunto de retailer contratado da DIM_LOCAL. Gold atual não foi redefinida por presença em fatos. Rede não nula e catálogo != GPA permanecem guardas opt-in desta página, não globais. Testes incluem local contratado, candidato global não contratado avaliado no mesmo tenant em memória, Rede NULL e duplicidade; nenhuma linha de produção fabricada.

Caso real: Local [DADO OMITIDO], Bandeira local MIX ATACADO, CNPJ [DADO OMITIDO]; catálogo MATEUS SUPERMERCADOS. A seleção de Bandeira não compara pl.bandeira: chega via conjunto CNPJ. O teste de runtime usa a Loja real desse local e testa também o sentido inverso.

## [DADO OMITIDO]. AP_CONVERSAO e Produto

AP→DIM_CONVERSAO→DIM_ITENS comprovado: opções de Marca/Hierarquia/Item recebem os itens da unidade selecionada. No sentido inverso, produto não restringe as opções AP nem altera MAX dimensional. MAX e SQL de conversão congelados. Sem seleção, opções seguem o conjunto de modos permitido na página; a UI exige AP single-select com unidade salva. valor continua excluído somente neste opt-in.

Atividade oferece DISTINCT NM_ACTIVITY_LEVEL, como no PBIP. A opção Não Informado agrupa os códigos I e W e envia ambos em TP_ACTIVITY_LEVEL; a seleção Fast Mover envia F. A máscara mantém o nome como estado UI, expandindo apenas os valores enviados ao KPI. Seis códigos geram cinco opções, sem duplicar nomes. Isso preserva o recorte congelado e a origem nominal do slicer PBIP.

## [DADO OMITIDO]. Condição oculta Item — evidência e limite

DAX completo extraído:

```text
measure 'Filtro Historico Com Dados' =
			
			VAR TemDados =
			    CALCULATE(
			        COUNTROWS(FATOS_PARTICULAR_HISTORICO),
			        REMOVEFILTERS(AP_CONVERSAO), REMOVEFILTERS(DIM_CATALOGO_LOCAL[Rede]), REMOVEFILTERS(DIM_LOCAL[Rede])
			    )
			RETURN
			IF(TemDados > [DADO OMITIDO], [DADO OMITIDO], [DADO OMITIDO])
		formatString: [DADO OMITIDO]
		displayFolder: _Universo de Dados
		lineageTag: [DADO OMITIDO]ff9[DADO OMITIDO]-b7bf-[DADO OMITIDO]f0[DADO OMITIDO]f3[DADO OMITIDO]d1b7[DADO OMITIDO]a
```

Filtro literal: Not(ComparisonKind=[DADO OMITIDO], Measure Filtro Historico Com Dados, Literal null). A medida retorna [DADO OMITIDO] para ausência de linhas e [DADO OMITIDO] para presença; nunca retorna BLANK. Logo não se pode substituir a condição pelo nome da medida. Se o comparador for IS NOT BLANK, [DADO OMITIDO] e [DADO OMITIDO] passam; se tratar [DADO OMITIDO] como BLANK, [DADO OMITIDO] não passa. Não foi provado qual tradução o motor usa nessa expressão serializada. Nenhum EXISTS(histórico), COUNTROWS>[DADO OMITIDO] ou calendário novo foi inserido. Teste usa a condição literal e a medida completa do PBIP; mantém essa parte F1[DADO OMITIDO] residual.

A [referência Microsoft de expressões](https://github.com/microsoft/skills-for-fabric/blob/main/skills/powerbi-report-authoring/references/conditional-formatting.md) identifica ComparisonKind=[DADO OMITIDO] e Not como negação, mas isso não basta para certificar a coerção null/zero deste filtro de medida em runtime.

## [DADO OMITIDO]. Testemunho BEFORE

{
  "witness": "Select UF MA, then request Bandeira options",
  "real_location": "[DADO OMITIDO]",
  "local_band": "MIX ATACADO",
  "catalog_band": "MATEUS SUPERMERCADOS",
  "old_native_cascade_parent_ids": [
    "NATIVE_FILTER-neoretail-rede"
  ],
  "selection_not_sent_before": {
    "uf": [
      "MA"
    ]
  },
  "pbip_contract_options_on_fixture": [
    "MATEUS SUPERMERCADOS",
    "MIX ATACADO"
  ],
  "old_options": [
    "ARCO-ÍRIS",
    "CD",
    "MATEUS SUPERMERCADOS",
    "MIX ATACADO",
    "SAVEGNAGO"
  ],
  "missing": [],
  "extra": [
    "ARCO-ÍRIS",
    "CD",
    "SAVEGNAGO"
  ],
  "old_behavior_matches": false,
  "production_writes": false,
  "activity_before_witness": {
    "source": "existing Gold DIM_NIVEL_ATIVIDADE rows from runtime snapshot",
    "old_option_column": "tp_activity_level",
    "old_code_count": [DADO OMITIDO],
    "pbip_option_column": "NM_ACTIVITY_LEVEL",
    "expected_name_count": [DADO OMITIDO],
    "real_shared_name_codes": [
      "W",
      "I"
    ],
    "old_behavior_matches": false
  }
}

Este witness executa o builder anterior e suas opções sobre as linhas reais da fixture, em SQLite efêmero. Ao selecionar UF MA, o frontend antigo não enviava UF a Bandeira: três opções extras (ARCO-ÍRIS, CD, SAVEGNAGO). Falha comprovada de opção/contexto; não é valor de KPI do Power BI.

## [DADO OMITIDO]. Testes AFTER e regressão

........................................................................ [ [DADO OMITIDO]]
........................................................................ [ [DADO OMITIDO]]
........................................................................ [ [DADO OMITIDO]]
........................................................................ [ [DADO OMITIDO]]
........................................................................ [ [DADO OMITIDO]]
........................................................................ [ [DADO OMITIDO]]
........................................................................ [ [DADO OMITIDO]]
.......................................................                  [[DADO OMITIDO]]
[DADO OMITIDO] passed in [DADO OMITIDO]s ([DADO OMITIDO]:[DADO OMITIDO]:[DADO OMITIDO])

[DADO OMITIDO] regression checks passed (Superset dependency doubles).
{"pbip_contract":"passed","checks":[DADO OMITIDO],"loss_u3m":[DADO OMITIDO],"dax_period_formula":[DADO OMITIDO]}

{"pbip_selector_frontend":"passed","checks":[DADO OMITIDO]}

[DADO OMITIDO] novos contratos Python: sentidos CNPJ, caso real, duplicidades, Rede NULL+contrato, AP→Produto, não inversão do fator, combinações, ausência, single-select, própria seleção excluída, busca assíncrona, condição Item literal e rótulos atividade sem mudar o código. Nenhum expected existente alterado. A tentativa inicial Docker antes/depois não executou testes porque o engine estava desligado; Docker Desktop localizado/iniciado e containers existentes retomados, sem limpar volumes. A suíte final completa usa /repo.

## [DADO OMITIDO]. Universo de opções e missing/extra

**As contagens expected abaixo são o contrato PBIP aplicado às dimensões Gold atuais. Não são contagens observadas no cache/import do ZIP ou numa sessão Power BI.** Essa distinção também vale para zero missing/extra: certifica os conjuntos relacionais modelados, excluindo o filtro Item não provado.

| Cenário | Seletor | Expected PBIP sobre Gold | Superset | Missing | Extra | segundos |
|---|---|---:|---:|---:|---:|---:|
| default | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| default | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| default | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| default | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| default | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| default | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| default | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| default | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| default | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| default | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| default | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| default | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| default | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede_band | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede_band | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede_band | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede_band | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede_band | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede_band | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede_band | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede_band | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede_band | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede_band | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede_band | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede_band | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| rede_band | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| band_local | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| band_local | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| band_local | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| band_local | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| band_local | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| band_local | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| band_local | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| band_local | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| band_local | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| band_local | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| band_local | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| band_local | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| band_local | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| local_reverse | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| local_reverse | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| local_reverse | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| local_reverse | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| local_reverse | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| local_reverse | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| local_reverse | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| local_reverse | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| local_reverse | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| local_reverse | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| local_reverse | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| local_reverse | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| local_reverse | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| unit_to_kg | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| unit_to_kg | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| unit_to_kg | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| unit_to_kg | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| unit_to_kg | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| unit_to_kg | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| unit_to_kg | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| unit_to_kg | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| unit_to_kg | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| unit_to_kg | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| unit_to_kg | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| unit_to_kg | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| unit_to_kg | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| item_does_not_filter_measure | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| item_does_not_filter_measure | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| item_does_not_filter_measure | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| item_does_not_filter_measure | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| item_does_not_filter_measure | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| item_does_not_filter_measure | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| item_does_not_filter_measure | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| item_does_not_filter_measure | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| item_does_not_filter_measure | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| item_does_not_filter_measure | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| item_does_not_filter_measure | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| item_does_not_filter_measure | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| item_does_not_filter_measure | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| no_selection | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| no_selection | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| no_selection | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| no_selection | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| no_selection | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| no_selection | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| no_selection | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| no_selection | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| no_selection | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| no_selection | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| no_selection | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| no_selection | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| no_selection | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |

SQL executado, exemplos reais, máscaras selecionadas e dados de prova (incluindo cinco seleções de atividade propagadas aos códigos do KPI): [pbip_f1[DADO OMITIDO]_options_runtime_2[DADO OMITIDO].json](pbip_f1[DADO OMITIDO]_options_runtime_2[DADO OMITIDO].json). Foram [DADO OMITIDO] comparações em oito contextos, [DADO OMITIDO] conflitos de tenant e busca comprovada de uma Loja além das primeiras [DADO OMITIDO] opções.

## [DADO OMITIDO]. Sequências de interação

default(unidade) → Rede real → Rede+Bandeira MATEUS; cadeia inversa Loja real → Bandeira/Catálogo; Bandeira+Loja → unidade→quilograma→Produto; Produto selecionado→AP permanece sem inversão; ausência de seleção. Cada passo gera opções novas via máscaras dos contextos permitidos e ChartData nativo com Guest JWT real. A camada JS também prova que consultar dependências não muta outras máscaras.

Não houve teste de clique/screenshot: a ferramenta retornou browsers=[] e Browser is not available: iab. Isso é limite da evidência UI e não foi contado como PASS visual. Não se declara igualdade completa de hierarquia, Select All, bookmark ou sincronização entre páginas.

## [DADO OMITIDO]. ChartData, Guest/RLS e performance

Default oito charts: [DADO OMITIDO]s, zero falhas. Filtrado Bandeira MATEUS SUPERMERCADOS / quilograma: [DADO OMITIDO]s, zero falhas. Baseline anterior: [DADO OMITIDO]s default e [DADO OMITIDO]s filtrado; tempos locais não são benchmark isolado. Consultas KPI e charts são idênticos por snapshot.

Guest: tenant [DADO OMITIDO], overrides [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO] bloqueados; assinatura adulterada rejeitada; [DADO OMITIDO] probes dos cinco datasets KPI e seletores nativos aprovados. Adicionalmente, cada um dos [DADO OMITIDO] datasets F1[DADO OMITIDO] recusou opções para tenants [DADO OMITIDO] e [DADO OMITIDO] ([DADO OMITIDO] probes). Credenciais/JWT não incluídos no relatório.

| Cadeia de opções | [DADO OMITIDO] requests: segundos totais sequenciais |
|---|---:|
| default | [DADO OMITIDO] |
| rede | [DADO OMITIDO] |
| rede_band | [DADO OMITIDO] |
| band_local | [DADO OMITIDO] |
| local_reverse | [DADO OMITIDO] |
| unit_to_kg | [DADO OMITIDO] |
| item_does_not_filter_measure | [DADO OMITIDO] |
| no_selection | [DADO OMITIDO] |

Uma consulta por controle solicitado, não uma consulta por opção/item. Usados índices já existentes; zero novos índices/marts físicos. A busca ILIKE é preservada, diferente da seleção própria IN. O filtro nativo limita o lote inicial a [DADO OMITIDO]; a busca permite localizar opções além desse lote, demonstrada no artefato. Não se declara Select All equivalente ao PBIP.

## [DADO OMITIDO]. Classificação before/after

| Etapa | MATCH | DIFFERENCE | UNMAPPED | NO_PBI_VALUE |
|---|---:|---:|---:|---:|
| Antes F1[DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |
| Após F1[DADO OMITIDO] parcial | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] |

F1[DADO OMITIDO] não é removida: conjuntos dimensionais/contexto foram corrigidos e testados, mas o critério integral ainda exige as condições e a experiência restantes abaixo. ROI MTD continua UNMAPPED, nenhum cartão criado. Nenhuma inferência numérica ou NUMERIC_MATCH.

## [DADO OMITIDO]. Pendências F1[DADO OMITIDO] e causas por KPI

- Item: a condição literal Not(ComparisonKind=[DADO OMITIDO], Measure Filtro Historico Com Dados, Literal null) não foi traduzida em EXISTS ou COUNTROWS>[DADO OMITIDO]. A medida retorna [DADO OMITIDO]/[DADO OMITIDO]; falta evidência de execução do comparador serializado distinguindo [DADO OMITIDO] de BLANK. A opção Item está certificada somente para os filtros dimensionais/AP, não para essa condição oculta.
- Estado da experiência: os oito seletores PBIP incluem quatro hierarquias; o Superset mantém [DADO OMITIDO] controles planos. O contrato de conjuntos foi testado, mas a navegação de hierarquia, select-all e restauração exata do bookmark LimpaFiltrosVGPN não foram certificados. O AP single-select requerido tem unidade salva; Clear All nativo não é declarado equivalente ao bookmark que restaura unidade.
- SyncGroup: grupos de sincronização foram inventariados. Não foi implementada sincronização entre dashboards legados, fora do escopo opt-in. Não se alega equivalência de um estado herdado de outra página.
- Ordenação: sortDefinition não consta nos oito visuais extraídos; Superset usa ordenação ascendente. Igualdade de collation/ordem e posicionamento de BLANK não foi demonstrada.
- Observação UI: não havia navegador conectado em cua.getState e criar aba iab retornou Browser is not available. As sequências foram verificadas pelo hook de dependências + Native Filter ChartData/Guest reais; não são testes de clique nem screenshots da UI.

| KPI / período | Status | Causas preservadas |
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
| ROI / MTD | UNMAPPED | ROI MTD sem visual mapeado |

Justificativas individuais da etapa anterior foram mantidas no JSON, com f1[DADO OMITIDO]_after detalhando apenas o avanço desta etapa. F1[DADO OMITIDO]/C0[DADO OMITIDO]/C0[DADO OMITIDO]/C1[DADO OMITIDO]/C1[DADO OMITIDO] não foram removidas nem corrigidas.

## [DADO OMITIDO]. Arquivos, publicação e fontes

Novos: pbip_overview/selectors.py; frontend-extension/pbipSelectorDependencies.mjs, register-pbip-selectors.mjs e test-pbip-selectors.mjs; test_pbip_f1[DADO OMITIDO]_selectors.py e fixture PBIP literal. Alterados nesta etapa: bootstrap_overview.py e Dockerfile. A extensão altera dois pontos da build upstream apenas mediante pbipSelectorContext=true: dependências de opções, rótulos e expansão de nomes de atividade em conjuntos de códigos. Dashboards legados continuam no caminho original.

Foram criados [DADO OMITIDO] datasets virtuais nr_pbip_options_<campo>. nr_pbip_filter_options e nr_pbip_conversion_options anteriores foram preservados. Nenhum mart PBIP republicado ou atualizado; nenhum reprocessamento Bronze/Silver/Gold; nenhum índice novo. Somente o serviço Superset foi reiniciado para aplicar os builds da extensão. A prova dos assets implantados está em pbip_f1[DADO OMITIDO]_deployed_assets_2[DADO OMITIDO].json. Um build inicial testou dependências, outro incluiu rótulos e o último corrigiu a duplicidade real I/W no universo e na máscara; versões intermediárias não são certificadas como finais.

A integração foi baseada no [hook nativo Superset [DADO OMITIDO]](https://raw.githubusercontent.com/apache/superset/[DADO OMITIDO]/superset-frontend/src/dashboard/components/nativeFilters/FilterBar/FilterControls/state.ts), no [gerador de formulário](https://raw.githubusercontent.com/apache/superset/[DADO OMITIDO]/superset-frontend/src/dashboard/components/nativeFilters/utils.ts) e na [busca do seletor](https://raw.githubusercontent.com/apache/superset/[DADO OMITIDO]/superset-frontend/src/filters/components/Select/buildQuery.ts). Modelo PBIP, condição literal e linhas Gold são as fontes locais de contrato e prova.

## [DADO OMITIDO]. Git final

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
?? local-engine/tests/fixtures/pbip_f1[DADO OMITIDO]_selectors_pbip_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_filters_conversion_real_rows_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_lactalis_overview_2[DADO OMITIDO].json
?? local-engine/tests/fixtures/pbip_lactalis_real_contract_rows_2[DADO OMITIDO].json
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

diff --stat não inclui untracked. O snapshot inicial distingue alterações anteriores destas adições F1[DADO OMITIDO]. Branch feat/osa-industry-certification; HEAD [DADO OMITIDO]d2f5[DADO OMITIDO]b5[DADO OMITIDO]ead1bae9af6d2ef7b7[DADO OMITIDO]f9a4[DADO OMITIDO]ae. Nenhum commit, push, merge, rebase ou troca de branch; main não alterada. PR #[DADO OMITIDO] não foi modificada por esta tarefa. Nenhuma operação sobre volumes Docker.
