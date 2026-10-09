> Cópia para GitHub: números de origem e identificadores numéricos omitidos. Original integral exige backup externo. Não usar esta cópia como fixture ou SQL executável.

# LACTALIS — conclusão residual F1[DADO OMITIDO], [DADO OMITIDO]/[DADO OMITIDO]/[DADO OMITIDO]

**Contrato completo: [DADO OMITIDO] SEMANTIC_MATCH, [DADO OMITIDO] SEMANTIC_DIFFERENCE, [DADO OMITIDO] UNMAPPED. Estado salvo e contexto explícito da página, sem transição externa/bookmark: [DADO OMITIDO] SEMANTIC_MATCH, [DADO OMITIDO] SEMANTIC_DIFFERENCE, [DADO OMITIDO] UNMAPPED. NO_PBI_VALUE = [DADO OMITIDO] em ambos.**

Os números têm escopos diferentes. Os [DADO OMITIDO] MATCH são condicionados ao estado/contexto explícito, não uma certificação da experiência inteira. F1[DADO OMITIDO] genérica foi removida das causas individuais. O contrato completo mantém F1[DADO OMITIDO]D somente com um caminho por KPI/período documentado no JSON: grupo UF externo → UF desta página → DIM_LOCAL → fato efetivamente lido pelo DAX. Não foi provada diferença numérica atual. A/B/C pendentes não foram promovidas automaticamente a DIFFERENCE.

Nenhum código de produção, dataset, mart ou dado foi alterado nesta etapa. Foram adicionados somente dois arquivos de teste/evidência e artefatos em generated. A ausência de comparador executável e navegação UI impede implementar equivalentes presumidos.

## [DADO OMITIDO]. F1[DADO OMITIDO]A — filtro oculto de Item

Filtro local do visual Item [DADO OMITIDO]f6c2[DADO OMITIDO]dd4[DADO OMITIDO]c3[DADO OMITIDO]b5[DADO OMITIDO]bd. A medida está em _Metricas. Relações Item→Histórico, calendário→Histórico, Local→Histórico e atividade→Histórico permanecem; CALCULATE remove AP e os dois campos Rede, não todas as dimensões. Bandeira, demais campos Local, Produto, atividade e calendário podem continuar filtrando as linhas. Remover Rede não elimina automaticamente o universo contratado nem os demais campos da ponte CNPJ. Não é filtro global da página/KPI. Sem Item selecionado, não há predicado desta medida acrescentado aos cards.

## [DADO OMITIDO]. F1[DADO OMITIDO]B — hierarquias/dependências

Quatro seletores hierárquicos PBIP contra controles planos Superset. Os conjuntos e os filtros explícitos foram provados; navegação, seleção de tuplas mistas e select-all ainda não. Posição/ordenação visual não é dependência nem prova de alteração de KPI.

| Visual PBIP | Origem/campos, pai→filho | Seleção | Superset atual |
|---|---|---|---|
| [DADO OMITIDO]c7[DADO OMITIDO]a5b6[DADO OMITIDO]bcecb | DIM_ITENS.Hierarquia [DADO OMITIDO] → DIM_ITENS.Hierarquia [DADO OMITIDO] → DIM_ITENS.Hierarquia [DADO OMITIDO] | multi; select-all configurado | campos separados; dependências relacionais opt-in |
| [DADO OMITIDO]f4ef5a9[DADO OMITIDO]c0[DADO OMITIDO] | DIM_ITENS.Descrição marca | multi; select-all configurado | campos separados; dependências relacionais opt-in |
| [DADO OMITIDO]d5e7efab0[DADO OMITIDO]d2[DADO OMITIDO]a5[DADO OMITIDO] | DIM_LOCAL.UF → DIM_LOCAL.Cidade | multi; select-all configurado | campos separados; dependências relacionais opt-in |
| [DADO OMITIDO]f6c2[DADO OMITIDO]dd4[DADO OMITIDO]c3[DADO OMITIDO]b5[DADO OMITIDO]bd | DIM_ITENS.Item | multi; select-all configurado | campos separados; dependências relacionais opt-in |
| [DADO OMITIDO]ffb4dd6[DADO OMITIDO]bb6[DADO OMITIDO]ac | DIM_NIVEL_ATIVIDADE.NM_ACTIVITY_LEVEL | multi; select-all configurado | campos separados; dependências relacionais opt-in |
| ad3[DADO OMITIDO]f9b0[DADO OMITIDO]ebe5 | AP_CONVERSAO.nm_measure | single obrigatório; unidade salva | campos separados; dependências relacionais opt-in |
| e2b3d1e3e2[DADO OMITIDO]eca2[DADO OMITIDO]a | DIM_LOCAL.TIPO_LOCAL → DIM_LOCAL.Loja | multi; select-all configurado | campos separados; dependências relacionais opt-in |
| feab3[DADO OMITIDO]d9[DADO OMITIDO]fae8[DADO OMITIDO]c3[DADO OMITIDO] | DIM_CATALOGO_LOCAL.Rede → DIM_CATALOGO_LOCAL.Bandeira | multi; select-all configurado | campos separados; dependências relacionais opt-in |

Região: atributo DIM_LOCAL[Região], usado em medidas; nenhum seletor Região visível nesta página. Não foi criada uma dependência fictícia. Catálogo Rede/Bandeira se reduz mutuamente por linhas e pela ponte CNPJ; Local devolve contexto ao catálogo. AP→Produto sim; Produto→AP não; Produto→MAX(conversion_rate) não. Atividade não recebe contexto ordinário do fato/Produto.

## [DADO OMITIDO]. F1[DADO OMITIDO]C — bookmarks/estado restaurado

Único bookmark relevante: LimpaFiltrosVGPN. Restaura oito seletores e AP unidade. A aplicação é limitada a targetVisualNames; estados de cards presentes no payload não se tornam aplicáveis só por estarem serializados. suppressDisplay=true impede tratar visibilidade salva como mudança aplicada; suppressActiveSection=true impede atribuir navegação automática. Ação correspondente não mapeada no Superset. Não se declara que Clear All restaura unidade ou que o bookmark estava ativo.

## [DADO OMITIDO]. F1[DADO OMITIDO]D — sincronização/interações

Separar: dependências de opções dentro da página estão implementadas; sincronização PBIP entre páginas não está mapeada em máscaras do Superset. Mudar UF em um membro externo altera o contexto recebido pela página PBIP. Cada uma das [DADO OMITIDO] linhas possui relação ativa Local→seu fato e closure sem remoção desse contexto; daí a diferença de capacidade contextual individual, inclusive Giro, que ignora AP mas não UF. Isso não implica diferença de valor em toda seleção.

## [DADO OMITIDO]. DAX completo do filtro Item

```dax
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

## [DADO OMITIDO]. Filtro serializado

```json
{
  "filters": [
    {
      "name": "[DADO OMITIDO]b1[DADO OMITIDO]db6[DADO OMITIDO]d8[DADO OMITIDO]a6ad9[DADO OMITIDO]",
      "field": {
        "Measure": {
          "Expression": {
            "SourceRef": {
              "Entity": "_Metricas"
            }
          },
          "Property": "Filtro Historico Com Dados"
        }
      },
      "type": "Advanced",
      "filter": {
        "Version": [DADO OMITIDO],
        "From": [
          {
            "Name": "_",
            "Entity": "_Metricas",
            "Type": [DADO OMITIDO]
          }
        ],
        "Where": [
          {
            "Condition": {
              "Not": {
                "Expression": {
                  "Comparison": {
                    "ComparisonKind": [DADO OMITIDO],
                    "Left": {
                      "Measure": {
                        "Expression": {
                          "SourceRef": {
                            "Source": "_"
                          }
                        },
                        "Property": "Filtro Historico Com Dados"
                      }
                    },
                    "Right": {
                      "Literal": {
                        "Value": "null"
                      }
                    }
                  }
                }
              }
            }
          }
        ]
      },
      "howCreated": "User"
    }
  ]
}
```

Operador literal: Not(ComparisonKind=[DADO OMITIDO], Left=Measure, Right=Literal("null")). Não foi traduzido em EXISTS, COUNTROWS>[DADO OMITIDO] ou SUM>[DADO OMITIDO].

## [DADO OMITIDO]. BLANK/null e casos controlados

Os resultados abaixo são dedução da expressão IF/COUNTROWS para linhas controladas, não execução do engine DAX nem valores atuais do Power BI. COUNTROWS não lê o payload numérico; IF retorna [DADO OMITIDO] ou [DADO OMITIDO], nunca BLANK. Falta provar a coerção do comparador serializado: identidade estrita de BLANK incluiria [DADO OMITIDO]; comparação frouxa pode tratar [DADO OMITIDO] como BLANK e excluí-lo. Não escolher uma delas sem evidência.

| Caso | Linhas após contexto retido | Resultado IF | Candidato antes do filtro oculto | Inclusão/exclusão pelo comparador |
|---|---|---:|---|---|
| history | [None] | [DADO OMITIDO] | True | UNPROVEN |
| no_history | [] | [DADO OMITIDO] | True | UNPROVEN |
| only_blank | [None, None] | [DADO OMITIDO] | True | UNPROVEN |
| zero | [[DADO OMITIDO]] | [DADO OMITIDO] | True | UNPROVEN |
| conversion_filtered | [[DADO OMITIDO]] | [DADO OMITIDO] | False | UNPROVEN |
| invalid_conversion_key | [[DADO OMITIDO]] | [DADO OMITIDO] | False | UNPROVEN |
| outside_local_or_calendar_context | [] | [DADO OMITIDO] | True | UNPROVEN |

Nos casos conversão excluída/chave inválida, a medida hipotética pode contar histórico após REMOVEFILTERS(AP), mas isso não insere o Item no universo do seletor: a candidatura AP→Produto é etapa distinta. Fora do contexto Local/calendário: zero linhas na avaliação controlada → [DADO OMITIDO]; possuir catálogo não garante histórico no contexto. F1[DADO OMITIDO]A residual é elegibilidade de opções, não um filtro KPI global.

## [DADO OMITIDO]. Grafo PBIP

```mermaid
flowchart LR
 AP[AP_CONVERSAO] --> CONV[DIM_CONVERSAO] --> ITEM[DIM_ITENS]
 CAT[Catálogo Rede/Bandeira] <-->|CNPJ BothDirections| LOC[Local UF/Cidade/Tipo/Loja]
 LOC --> FACT[Fatos]
 ITEM --> FACT
 ACT[Atividade] --> FACT
 CAL[Calendário] --> FACT
 OTHER[UF em outra página do grupo] -->|filterChanges| UF[UF nesta página] --> LOC
```

A ponte bidirecional tem ciclo: não é DAG estrita. A DAG condensada agrupa Local/Catálogo em um componente. O filtro de medida Item é uma condição visual adicional não certificada.

## [DADO OMITIDO]. Grafo Superset antes desta etapa

```mermaid
flowchart LR
 GEO[Controles Geo] <-->|dependências diretas CNPJ| GEO2[Outros controles Geo]
 AP[AP] --> PROD[Marca/Hierarquia/Item]
 PROD <-->|mesma dimensão| PROD2[Outros atributos Produto]
 MASK[Máscaras locais] --> KPI[ChartData KPI]
```

Já é o estado parcialmente corrigido recebido, não o antigo encadeamento unilateral. Dependências de opções não são cascadeParentIds recursivos; evita-se limpar seleções por ciclo. Não há grupo cross-page PBIP nem ação nomeada de bookmark.

## [DADO OMITIDO]. Grafo Superset depois / equivalente desejado

Depois desta etapa, o grafo de produção é idêntico ao anterior: zero mudanças de produção. Para equivalência de transições, ainda seriam necessárias arestas externas UF/Rede/Produto sincronizados → máscaras locais e uma ação de restauração dos oito seletores/unidade com contrato de hierarquia. Não foram acrescentadas arestas inventadas Produto→AP/rate nem condicionais presumidas do Item.

```mermaid
flowchart LR
 EXTERNAL[Estado de grupo sincronizado] -. falta mapear .-> MASK[Máscaras locais]
 BOOKMARK[LimpaFiltrosVGPN] -. falta restauração certificada .-> MASK
 MASK --> GEO[Geo/CNPJ]
 MASK --> AP[AP] --> PRODUCT[Produto]
 MASK --> KPI[ChartData]
```

## [DADO OMITIDO]. Bookmarks e três estados

Inventariados todos os [DADO OMITIDO] arquivos, [DADO OMITIDO] visuais, [DADO OMITIDO] páginas. Critério de relevância: section/activeSection da página ou targetVisualNames intersectando seus visuais. Exatamente um relevante. Os outros [DADO OMITIDO] não alteram esta página por referências serializadas; inventário integral preservado no JSON.

LimpaFiltrosVGPN: applyOnlyToTargetVisuals=true, [DADO OMITIDO] targets; restaura general.filter AP IN unidade; demais seletores sem seleção restritiva, H1 com modo invertido e raiz vazia; projections/expansionStates disponíveis no payload. Valor não é seleção salva, página e seletor excluem valor. Data de ativação/execução não consta. selectedValues e hierarchyState com esses nomes literais não constam; estados reais usam filter, activeProjections, expansionStates e identityValues, não foram descartados.

Estado salvo PBIP: AP unidade e escopo contratado/Rede não nula/NOT valor. Estado restaurado: definido acima, independentemente de payloads não target. Estado Power BI vivo e bookmark ativo: UNKNOWN. Sem leitura de sessão viva nesta etapa.

## [DADO OMITIDO]. Sync, interações, persistência

| Grupo | Membros totais | Páginas | fieldChanges/filterChanges |
|---|---:|---:|---|
| Item | [DADO OMITIDO] | [DADO OMITIDO] | true/true |
| NM_BRAND | [DADO OMITIDO] | [DADO OMITIDO] | true/true |
| NM_HIERARCHY_LEVEL_1 | [DADO OMITIDO] | [DADO OMITIDO] | true/true |
| Rede | [DADO OMITIDO] | [DADO OMITIDO] | true/true |
| TIPO_LOCAL | [DADO OMITIDO] | [DADO OMITIDO] | true/true |
| UF | [DADO OMITIDO] | [DADO OMITIDO] | true/true |
| nm_activity_level1 | [DADO OMITIDO] | [DADO OMITIDO] | true/true |
| nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | true/true |

Todas as páginas, nomes, campos, IDs e estados desses membros estão em pbip_f1[DADO OMITIDO]_final_inventory_2[DADO OMITIDO].json. A busca literal filtersFrom/filtersTo retornou zero ocorrências nos visuais/bookmarks; ausência desses nomes não prova ausência de interações.

[DADO OMITIDO] interações explícitas nesta página, todas AP: [DADO OMITIDO] DataFilter e [DADO OMITIDO] NoFilter. Nenhum NoFilter aponta para os [DADO OMITIDO] cards mapeados. O JSON identifica targets; os [DADO OMITIDO] são bc6[DADO OMITIDO]ef2[DADO OMITIDO]a0[DADO OMITIDO]c4[DADO OMITIDO]dda8[DADO OMITIDO], [DADO OMITIDO]d7a0[DADO OMITIDO]b5[DADO OMITIDO]bd4[DADO OMITIDO], [DADO OMITIDO]a5dee8aeca4[DADO OMITIDO]d, [DADO OMITIDO]b7aa7[DADO OMITIDO]d3[DADO OMITIDO]b4a0[DADO OMITIDO]. Para os demais cards, não foi inventado override: medida/relações determinam efeito final. Giro continua calculando em unidade por DAX.

| Seleção | Opções | ChartData |
|---|---|---|
| Geo | outros Geo via CNPJ, ambos os sentidos | contexto Local/fatos |
| AP | Produto/Hierarquias/Marca/Item | AP→itens e leitura/remoção da medida; Giro fixo unidade |
| Produto | atributos da mesma dimensão; AP não | itens/fatos; MAX taxa preservado |
| Atividade | independente de Geo/Produto ordinários | códigos do agrupamento aprovado |
| Grupo externo PBIP | grupo sincronizado da página | contexto recebido PBIP; não mapeado automaticamente no Superset |

Persistência viva/URL/localStorage de seleções não foi inspecionada em navegador. Não é PASS UI nem razão numérica adicional.

## [DADO OMITIDO]. Cadeias testadas

Real Native Filter ChartData com Guest; não clique de browser. Cadeias: sem seleção→Rede→Rede+Bandeira→Rede+Bandeira+Local; sem seleção→Bandeira→Bandeira+Rede→Bandeira+Rede+Local; AP quilograma→Item→probes KPI; Produto→AP não reduz universo. Também cadeia Local→catálogo, busca além de [DADO OMITIDO] e cinco atividades→códigos KPI. Cada cenário registra seleções enviadas e opções retornadas. selected_mask_preserved/removed descrevem máscaras fornecidas, não uma observação de widget. Igualdade de navegação visual continua pendente.

## [DADO OMITIDO]. Counts de opções

Counts de referência = contrato relacional PBIP executado sobre Gold atual. Não são contagens do cache importado PBIP. A condição oculta Item continua excluída desta certificação.

| Cenário | Campo | Referência sobre Gold | Superset | Missing | Extra | Máscara preservada | Removida | s |
|---|---|---:|---:|---:|---:|---|---|---:|
| default | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['unidade'] | [] | [DADO OMITIDO] |
| default | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| default | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| default | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| default | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| default | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| default | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| default | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| default | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| default | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| default | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| default | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| default | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['unidade'] | [] | [DADO OMITIDO] |
| rede | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['ARMAZMATEUS'] | [] | [DADO OMITIDO] |
| rede | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede_band | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['unidade'] | [] | [DADO OMITIDO] |
| rede_band | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['ARMAZMATEUS'] | [] | [DADO OMITIDO] |
| rede_band | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['MATEUS SUPERMERCADOS'] | [] | [DADO OMITIDO] |
| rede_band | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede_band | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede_band | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede_band | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede_band | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede_band | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede_band | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede_band | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede_band | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede_band | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_local | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['unidade'] | [] | [DADO OMITIDO] |
| band_local | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_local | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['MATEUS SUPERMERCADOS'] | [] | [DADO OMITIDO] |
| band_local | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_local | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_local | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_local | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['[DADO OMITIDO] - MATEUS SUPERMERCADOS S.A. MIX BARRA DO CORDA'] | [] | [DADO OMITIDO] |
| band_local | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_local | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_local | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_local | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_local | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_local | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| local_reverse | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['unidade'] | [] | [DADO OMITIDO] |
| local_reverse | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| local_reverse | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| local_reverse | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| local_reverse | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| local_reverse | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| local_reverse | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['[DADO OMITIDO] - MATEUS SUPERMERCADOS S.A. MIX BARRA DO CORDA'] | [] | [DADO OMITIDO] |
| local_reverse | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| local_reverse | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| local_reverse | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| local_reverse | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| local_reverse | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| local_reverse | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| unit_to_kg | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['quilograma'] | [] | [DADO OMITIDO] |
| unit_to_kg | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| unit_to_kg | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['MATEUS SUPERMERCADOS'] | [] | [DADO OMITIDO] |
| unit_to_kg | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| unit_to_kg | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| unit_to_kg | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| unit_to_kg | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| unit_to_kg | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| unit_to_kg | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| unit_to_kg | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| unit_to_kg | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| unit_to_kg | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| unit_to_kg | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| item_does_not_filter_measure | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['quilograma'] | [] | [DADO OMITIDO] |
| item_does_not_filter_measure | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| item_does_not_filter_measure | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| item_does_not_filter_measure | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| item_does_not_filter_measure | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| item_does_not_filter_measure | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| item_does_not_filter_measure | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| item_does_not_filter_measure | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| item_does_not_filter_measure | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| item_does_not_filter_measure | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| item_does_not_filter_measure | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| item_does_not_filter_measure | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| item_does_not_filter_measure | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['[DADO OMITIDO] - Queijo Brie Fração [DADO OMITIDO]G President'] | [] | [DADO OMITIDO] |
| no_selection | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| no_selection | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| no_selection | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| no_selection | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| no_selection | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| no_selection | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| no_selection | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| no_selection | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| no_selection | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| no_selection | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| no_selection | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| no_selection | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| no_selection | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_first | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['unidade'] | [] | [DADO OMITIDO] |
| band_first | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_first | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['MATEUS SUPERMERCADOS'] | [] | [DADO OMITIDO] |
| band_first | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_first | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_first | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_first | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_first | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_first | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_first | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_first | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_first | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_first | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_then_rede | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['unidade'] | [] | [DADO OMITIDO] |
| band_then_rede | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['ARMAZMATEUS'] | [] | [DADO OMITIDO] |
| band_then_rede | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['MATEUS SUPERMERCADOS'] | [] | [DADO OMITIDO] |
| band_then_rede | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_then_rede | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_then_rede | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_then_rede | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_then_rede | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_then_rede | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_then_rede | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_then_rede | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_then_rede | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_then_rede | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_rede_local | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['unidade'] | [] | [DADO OMITIDO] |
| band_rede_local | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['ARMAZMATEUS'] | [] | [DADO OMITIDO] |
| band_rede_local | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['MATEUS SUPERMERCADOS'] | [] | [DADO OMITIDO] |
| band_rede_local | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_rede_local | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_rede_local | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_rede_local | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['[DADO OMITIDO] - MATEUS SUPERMERCADOS S.A. MIX BARRA DO CORDA'] | [] | [DADO OMITIDO] |
| band_rede_local | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_rede_local | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_rede_local | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_rede_local | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_rede_local | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| band_rede_local | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede_band_local | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['unidade'] | [] | [DADO OMITIDO] |
| rede_band_local | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['ARMAZMATEUS'] | [] | [DADO OMITIDO] |
| rede_band_local | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['MATEUS SUPERMERCADOS'] | [] | [DADO OMITIDO] |
| rede_band_local | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede_band_local | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede_band_local | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede_band_local | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['[DADO OMITIDO] - MATEUS SUPERMERCADOS S.A. MIX BARRA DO CORDA'] | [] | [DADO OMITIDO] |
| rede_band_local | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede_band_local | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede_band_local | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede_band_local | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede_band_local | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| rede_band_local | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| ap_kg_only | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['quilograma'] | [] | [DADO OMITIDO] |
| ap_kg_only | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| ap_kg_only | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| ap_kg_only | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| ap_kg_only | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| ap_kg_only | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| ap_kg_only | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| ap_kg_only | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| ap_kg_only | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| ap_kg_only | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| ap_kg_only | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| ap_kg_only | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| ap_kg_only | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| product_only_no_reverse | nm_measure | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| product_only_no_reverse | rede | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| product_only_no_reverse | bandeira | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| product_only_no_reverse | uf | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| product_only_no_reverse | cidade | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| product_only_no_reverse | tipo_local | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| product_only_no_reverse | loja | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| product_only_no_reverse | tp_activity_level | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| product_only_no_reverse | descricao_marca | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| product_only_no_reverse | hierarquia_1 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| product_only_no_reverse | hierarquia_2 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| product_only_no_reverse | hierarquia_3 | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [] | [] | [DADO OMITIDO] |
| product_only_no_reverse | item | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | [DADO OMITIDO] | ['[DADO OMITIDO] - Queijo Brie Fração [DADO OMITIDO]G President'] | [] | [DADO OMITIDO] |

## [DADO OMITIDO]. Missing/extra

[DADO OMITIDO] comparações = [DADO OMITIDO] cenários × [DADO OMITIDO] controles; zero missing, zero extra, zero duplicatas. Não certifica comparador Item nem navegação UI. [DADO OMITIDO] probes de opções com tenant [DADO OMITIDO]/[DADO OMITIDO] recusados; assinatura adulterada rejeitada e overrides de Guest bloqueados.

## [DADO OMITIDO]. Caso real CNPJ

Local [DADO OMITIDO], CNPJ [DADO OMITIDO]; Bandeira local MIX ATACADO e catálogo MATEUS SUPERMERCADOS. Local/rede/catálogo e cadeia inversa continuam passando. A loja real permanece elegível com Bandeira de catálogo; não se troca o campo pelo nome da Bandeira local. Nenhuma linha foi fabricada em produção.

## [DADO OMITIDO]. Regressões

[DADO OMITIDO] testes Python completos PASS ([DADO OMITIDO] anteriores + [DADO OMITIDO] novos); [DADO OMITIDO] frontend PASS ([DADO OMITIDO] + [DADO OMITIDO]); [DADO OMITIDO] opções PASS; ChartData default/filtrado [DADO OMITIDO][DADO OMITIDO] sem erro; Guest/RLS/overrides PASS. Os [DADO OMITIDO] arquivos existentes do snapshot continuam byte a byte iguais. Oito charts/SQL/params/IDs e [DADO OMITIDO] definições dos marts idênticos à etapa anterior e ao snapshot atual. Dois scripts solicitados continuam untracked.

Novos testes: sete casos COUNTROWS/IF controlados com comparador explicitamente pendente; escopo visual do filtro; targets/restauração AP do bookmark; sync cross-page; direção AP→Conversão→Produto e CNPJ; inventário completo de bookmarks. Casos são evidência lógica/serializada, não simulação certificada do engine DAX.

## [DADO OMITIDO]. Performance

Default: [DADO OMITIDO]s. Filtrado: [DADO OMITIDO]s. Etapa anterior: [DADO OMITIDO]s e [DADO OMITIDO]s. Consulta filtrada nesta execução levou cerca de [DADO OMITIDO] mais tempo, mas não houve mudança de produção; testes concorrentes e cache tornam a medição não isolada. Não atribuir regressão causal a F1[DADO OMITIDO]. SQL lento individual consta no log ChartData; nenhuma otimização efetuada.

[DADO OMITIDO] opções: [DADO OMITIDO]s sequenciais somados. Mais lenta: ([DADO OMITIDO], 'ap_kg_only', 'rede'). SQL de cada request está no JSON.

## [DADO OMITIDO]. Matriz KPI × F1[DADO OMITIDO]A/B/C/D

A=N/A sem Item escolhido / elegibilidade interativa pendente. B=PASS contexto explícito / navegação pendente. C=N/A sem invocar bookmark / ação não mapeada. D=PASS contexto explícito local / DIFFERENCE na transição cross-page. Essas letras não são um PASS geral da experiência. Relações por linha e closures completas estão no JSON final.

| KPI | Período | A salvo/interativo | B salvo/interativo | C salvo/interativo | D salvo/cross-page | Outras causas | Salvo | Completo |
|---|---|---|---|---|---|---|---|---|
| MARKUP | MTD | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | C1[DADO OMITIDO],C1[DADO OMITIDO] | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| MARKUP | Mês anterior | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | C1[DADO OMITIDO],C1[DADO OMITIDO] | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| MARKUP | Média U3M | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | C1[DADO OMITIDO],C1[DADO OMITIDO],C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| Venda qtd | MTD | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | nenhuma | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| Venda qtd | Mês anterior | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | nenhuma | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| Venda qtd | Média U3M | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | nenhuma | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| Estoque qtd | MTD | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | nenhuma | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| Estoque qtd | Mês anterior | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | nenhuma | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| Estoque qtd | Média U3M | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | nenhuma | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| Giro | MTD | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | nenhuma | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| Giro | Mês anterior | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | nenhuma | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| Giro | Média U3M | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | nenhuma | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| Estoque custo | MTD | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | C1[DADO OMITIDO] | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| Estoque custo | Mês anterior | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | C1[DADO OMITIDO] | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| Estoque custo | Média U3M | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | C1[DADO OMITIDO] | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| IVD - Excesso | MTD | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | F1[DADO OMITIDO],C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| IVD - Excesso | Mês anterior | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | F1[DADO OMITIDO],C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| IVD - Excesso | Média U3M | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | F1[DADO OMITIDO],C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| Venda sell out | MTD | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | nenhuma | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| Venda sell out | Mês anterior | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | nenhuma | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| Venda sell out | Média U3M | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| OSA | MTD | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | nenhuma | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| OSA | Mês anterior | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | nenhuma | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| OSA | Média U3M | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | nenhuma | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| Perda OSA | MTD | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | nenhuma | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| Perda OSA | Mês anterior | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | nenhuma | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| Perda OSA | Média U3M | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | nenhuma | SEMANTIC_MATCH | SEMANTIC_DIFFERENCE |
| ROI | Mês anterior | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | C1[DADO OMITIDO],C1[DADO OMITIDO] | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| ROI | Média U3M | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | C1[DADO OMITIDO],C1[DADO OMITIDO],C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| ROI | Anual [DADO OMITIDO]M | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | C1[DADO OMITIDO],C1[DADO OMITIDO] | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| Venda custo | MTD | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | C1[DADO OMITIDO] | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| Venda custo | Mês anterior | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | C1[DADO OMITIDO] | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| Venda custo | Média U3M | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | C1[DADO OMITIDO] | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| TVD - Pré-ruptura | MTD | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | F1[DADO OMITIDO],C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| TVD - Pré-ruptura | Mês anterior | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | F1[DADO OMITIDO],C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| TVD - Pré-ruptura | Média U3M | N/A / UNPROVEN | PASS / PENDING | N/A / UNMAPPED_ACTION | PASS / DIFFERENCE | F1[DADO OMITIDO],C0[DADO OMITIDO] | SEMANTIC_DIFFERENCE | SEMANTIC_DIFFERENCE |
| ROI | MTD | N/A | N/A | N/A | N/A | V0[DADO OMITIDO] | UNMAPPED | UNMAPPED |

### Caminhos F1[DADO OMITIDO]D individualizados

| KPI/período | Visual PBIP → medida raiz | Local→fato: relacionamento | Chart/dataset |
|---|---|---|---|
| MARKUP / MTD | [DADO OMITIDO]cff8[DADO OMITIDO]c5[DADO OMITIDO]c6e4[DADO OMITIDO] → MARKUP MTD | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| MARKUP / Mês anterior | [DADO OMITIDO]cff8[DADO OMITIDO]c5[DADO OMITIDO]c6e4[DADO OMITIDO] → MARKUP Mes Ant | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| MARKUP / Média U3M | [DADO OMITIDO]cff8[DADO OMITIDO]c5[DADO OMITIDO]c6e4[DADO OMITIDO] → MARKUP U3M | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| Venda qtd / MTD | [DADO OMITIDO]d1[DADO OMITIDO]a5[DADO OMITIDO]d0aa → Venda MTD | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| Venda qtd / Mês anterior | [DADO OMITIDO]d1[DADO OMITIDO]a5[DADO OMITIDO]d0aa → Venda Mes Ant | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| Venda qtd / Média U3M | [DADO OMITIDO]d1[DADO OMITIDO]a5[DADO OMITIDO]d0aa → Venda U3M | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| Estoque qtd / MTD | [DADO OMITIDO]a9c0a9[DADO OMITIDO]a0[DADO OMITIDO]cdb3d → Estoque MTD | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| Estoque qtd / Mês anterior | [DADO OMITIDO]a9c0a9[DADO OMITIDO]a0[DADO OMITIDO]cdb3d → Estoque Mes Ant | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| Estoque qtd / Média U3M | [DADO OMITIDO]a9c0a9[DADO OMITIDO]a0[DADO OMITIDO]cdb3d → Estoque U3M | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| Giro / MTD | [DADO OMITIDO]f2a3d5[DADO OMITIDO]e9b → Giro MTD | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| Giro / Mês anterior | [DADO OMITIDO]f2a3d5[DADO OMITIDO]e9b → Giro Mes Ant | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| Giro / Média U3M | [DADO OMITIDO]f2a3d5[DADO OMITIDO]e9b → Giro U3M | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| Estoque custo / MTD | [DADO OMITIDO]f3d5[DADO OMITIDO]d7 → Estoque Custo MTD | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| Estoque custo / Mês anterior | [DADO OMITIDO]f3d5[DADO OMITIDO]d7 → Estoque Custo Mes Ant | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| Estoque custo / Média U3M | [DADO OMITIDO]f3d5[DADO OMITIDO]d7 → Estoque Custo U3M | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| IVD - Excesso / MTD | [DADO OMITIDO]b0[DADO OMITIDO]a6b8d7[DADO OMITIDO]c7d0[DADO OMITIDO] → IVD MTD | [DADO OMITIDO]dc2c6a-b6[DADO OMITIDO][DADO OMITIDO]d3[DADO OMITIDO][DADO OMITIDO]b5[DADO OMITIDO]: FATOS_PARTICULAR_TVD_IVD | [DADO OMITIDO]/[DADO OMITIDO] |
| IVD - Excesso / Mês anterior | [DADO OMITIDO]b0[DADO OMITIDO]a6b8d7[DADO OMITIDO]c7d0[DADO OMITIDO] → IVD Mes Ant | [DADO OMITIDO]dc2c6a-b6[DADO OMITIDO][DADO OMITIDO]d3[DADO OMITIDO][DADO OMITIDO]b5[DADO OMITIDO]: FATOS_PARTICULAR_TVD_IVD | [DADO OMITIDO]/[DADO OMITIDO] |
| IVD - Excesso / Média U3M | [DADO OMITIDO]b0[DADO OMITIDO]a6b8d7[DADO OMITIDO]c7d0[DADO OMITIDO] → IVD U3M | [DADO OMITIDO]dc2c6a-b6[DADO OMITIDO][DADO OMITIDO]d3[DADO OMITIDO][DADO OMITIDO]b5[DADO OMITIDO]: FATOS_PARTICULAR_TVD_IVD | [DADO OMITIDO]/[DADO OMITIDO] |
| Venda sell out / MTD | [DADO OMITIDO]a3[DADO OMITIDO]c5[DADO OMITIDO]aa5[DADO OMITIDO]b0 → Venda sell out MTD | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| Venda sell out / Mês anterior | [DADO OMITIDO]a3[DADO OMITIDO]c5[DADO OMITIDO]aa5[DADO OMITIDO]b0 → Venda sell out Mes Ant | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| Venda sell out / Média U3M | [DADO OMITIDO]a3[DADO OMITIDO]c5[DADO OMITIDO]aa5[DADO OMITIDO]b0 → Venda sell out U3M | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| OSA / MTD | [DADO OMITIDO]cf4ee2b1[DADO OMITIDO] → % OSA MTD | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| OSA / Mês anterior | [DADO OMITIDO]cf4ee2b1[DADO OMITIDO] → % OSA Mes Ant | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| OSA / Média U3M | [DADO OMITIDO]cf4ee2b1[DADO OMITIDO] → % OSA U3M | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| Perda OSA / MTD | af9[DADO OMITIDO]b2[DADO OMITIDO]ba9b6[DADO OMITIDO]d1ae4 → Perda OSA Valor MTD | [DADO OMITIDO]cb7fe1b-a0ef-[DADO OMITIDO]f4[DADO OMITIDO]fc3-dfb3[DADO OMITIDO]ebfed6: FATOS_MENSAL_CAUSA_OSA | [DADO OMITIDO]/[DADO OMITIDO] |
| Perda OSA / Mês anterior | af9[DADO OMITIDO]b2[DADO OMITIDO]ba9b6[DADO OMITIDO]d1ae4 → Perda OSA Valor Mes Ant | [DADO OMITIDO]cb7fe1b-a0ef-[DADO OMITIDO]f4[DADO OMITIDO]fc3-dfb3[DADO OMITIDO]ebfed6: FATOS_MENSAL_CAUSA_OSA | [DADO OMITIDO]/[DADO OMITIDO] |
| Perda OSA / Média U3M | af9[DADO OMITIDO]b2[DADO OMITIDO]ba9b6[DADO OMITIDO]d1ae4 → Perda OSA Valor U3M | [DADO OMITIDO]cb7fe1b-a0ef-[DADO OMITIDO]f4[DADO OMITIDO]fc3-dfb3[DADO OMITIDO]ebfed6: FATOS_MENSAL_CAUSA_OSA | [DADO OMITIDO]/[DADO OMITIDO] |
| ROI / Mês anterior | d4[DADO OMITIDO]d0[DADO OMITIDO]cfbed7[DADO OMITIDO]c9[DADO OMITIDO]ee0 → ROI Mes Ant | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| ROI / Média U3M | d4[DADO OMITIDO]d0[DADO OMITIDO]cfbed7[DADO OMITIDO]c9[DADO OMITIDO]ee0 → ROI U3M | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| ROI / Anual [DADO OMITIDO]M | d4[DADO OMITIDO]d0[DADO OMITIDO]cfbed7[DADO OMITIDO]c9[DADO OMITIDO]ee0 → ROI Anual | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| Venda custo / MTD | d4f1e5d7[DADO OMITIDO]b3[DADO OMITIDO]b5[DADO OMITIDO]d6[DADO OMITIDO] → Venda Custo MTD | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| Venda custo / Mês anterior | d4f1e5d7[DADO OMITIDO]b3[DADO OMITIDO]b5[DADO OMITIDO]d6[DADO OMITIDO] → Venda Custo Mes Ant | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| Venda custo / Média U3M | d4f1e5d7[DADO OMITIDO]b3[DADO OMITIDO]b5[DADO OMITIDO]d6[DADO OMITIDO] → Venda Custo U3M | c9[DADO OMITIDO]f6b8[DADO OMITIDO][DADO OMITIDO]-af1c-[DADO OMITIDO]fd4[DADO OMITIDO]a0[DADO OMITIDO]de7a2: FATOS_PARTICULAR_HISTORICO | [DADO OMITIDO]/[DADO OMITIDO] |
| TVD - Pré-ruptura / MTD | dac3d0[DADO OMITIDO]b0[DADO OMITIDO]bc5[DADO OMITIDO]d9[DADO OMITIDO]a9[DADO OMITIDO] → TVD MTD | [DADO OMITIDO]dc2c6a-b6[DADO OMITIDO][DADO OMITIDO]d3[DADO OMITIDO][DADO OMITIDO]b5[DADO OMITIDO]: FATOS_PARTICULAR_TVD_IVD | [DADO OMITIDO]/[DADO OMITIDO] |
| TVD - Pré-ruptura / Mês anterior | dac3d0[DADO OMITIDO]b0[DADO OMITIDO]bc5[DADO OMITIDO]d9[DADO OMITIDO]a9[DADO OMITIDO] → TVD Mes Ant | [DADO OMITIDO]dc2c6a-b6[DADO OMITIDO][DADO OMITIDO]d3[DADO OMITIDO][DADO OMITIDO]b5[DADO OMITIDO]: FATOS_PARTICULAR_TVD_IVD | [DADO OMITIDO]/[DADO OMITIDO] |
| TVD - Pré-ruptura / Média U3M | dac3d0[DADO OMITIDO]b0[DADO OMITIDO]bc5[DADO OMITIDO]d9[DADO OMITIDO]a9[DADO OMITIDO] → TVD U3M | [DADO OMITIDO]dc2c6a-b6[DADO OMITIDO][DADO OMITIDO]d3[DADO OMITIDO][DADO OMITIDO]b5[DADO OMITIDO]: FATOS_PARTICULAR_TVD_IVD | [DADO OMITIDO]/[DADO OMITIDO] |

## [DADO OMITIDO]. SEMANTIC_MATCH final

Contrato completo: [DADO OMITIDO]. Recorte comprovado do estado salvo/contexto explícito: [DADO OMITIDO]. São Venda qtd [DADO OMITIDO], Estoque qtd [DADO OMITIDO], Giro [DADO OMITIDO], Venda sell out MTD/mês anterior [DADO OMITIDO], OSA [DADO OMITIDO], Perda OSA [DADO OMITIDO]. Não promover os [DADO OMITIDO] a MATCH irrestrito porque a transição de grupos externos possui caminho contextual não mapeado.

## [DADO OMITIDO]. SEMANTIC_DIFFERENCE final

Contrato completo: [DADO OMITIDO], agora por F1[DADO OMITIDO]D individualizada; não por herança F1[DADO OMITIDO]A/B/C ou por ausência de screenshot. Estado salvo/contexto explícito: [DADO OMITIDO], exclusivamente pelas causas congeladas. UNMAPPED=[DADO OMITIDO] (ROI MTD sem visual); NO_PBI_VALUE=[DADO OMITIDO]. Nenhum valor PBI foi estimado.

## [DADO OMITIDO]. Outras causas restantes

F1[DADO OMITIDO]/C0[DADO OMITIDO]: TVD e IVD, [DADO OMITIDO] pares. C1[DADO OMITIDO]: custo Venda/Estoque, ROI e Markup, [DADO OMITIDO] pares. C1[DADO OMITIDO]: ROI e Markup, [DADO OMITIDO] pares. C0[DADO OMITIDO]: U3M sell out/ROI/Markup, [DADO OMITIDO] pares. Há sobreposição. Todas preservadas; nenhuma correção de SQL, DAX, marts ou calendário.

## [DADO OMITIDO]. git diff --stat

```text
 scripts/publish_lactalis_marts.py                  | [DADO OMITIDO] ++++++++++++++-
 superset/Dockerfile                                |  [DADO OMITIDO] +
 superset/bootstrap_overview.py                     | [DADO OMITIDO] ++++++++++++++++------
 .../plugin-chart-neoretail-kpi/src/buildQuery.js   | [DADO OMITIDO] ++-
 .../src/transformProps.js                          | [DADO OMITIDO] ++++++++++--
 superset/validate_overview.py                      | [DADO OMITIDO] +++++++-
 [DADO OMITIDO] files changed, [DADO OMITIDO] insertions(+), [DADO OMITIDO] deletions(-)
```

Diff tracked idêntico ao inicial; novos dois untracked não aparecem no diffstat.

## [DADO OMITIDO]. git status

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

Snapshot inicial: pbip_f1[DADO OMITIDO]_final_stage_before_2[DADO OMITIDO].json. Inventário: pbip_f1[DADO OMITIDO]_final_inventory_2[DADO OMITIDO].json. Matriz com provas: pbi_superset_semantic_equivalence_f1[DADO OMITIDO]_final_2[DADO OMITIDO].json. Runtime: pbip_f1[DADO OMITIDO]_final_options_runtime_2[DADO OMITIDO].json e pbip_f1[DADO OMITIDO]_final_guest_rls_2[DADO OMITIDO].json. Logs final_* preservados.

## [DADO OMITIDO]. Sem commit/push

Branch feat/osa-industry-certification; HEAD [DADO OMITIDO]d2f5[DADO OMITIDO]b5[DADO OMITIDO]ead1bae9af6d2ef7b7[DADO OMITIDO]f9a4[DADO OMITIDO]ae. Nenhum commit, push, merge, rebase, mudança de branch, alteração da main ou da PR. Nenhuma publicação de mart, alteração de Bronze/Silver/Gold ou operação de limpeza/remoção de volumes.

Pendências exatas: coerção do comparador Item (A); navegação/tuplas/select-all das hierarquias (B); ação equivalente e teste de restauração do bookmark (C); transporte de grupos cross-page (D). Ordem/collation e UI não observada permanecem limites da evidência; não foram usadas como divergência numérica nem causa automática dos [DADO OMITIDO] pares.
