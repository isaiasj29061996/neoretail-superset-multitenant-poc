# Certificação semântica — Visão Geral

## Critério

Esta auditoria compara fórmula, contexto temporal, filtros, granularidade, `BLANK`/zero, conversão, contagem, dimensões e isolamento por `id_customer`. Valores absolutos do snapshot local não são referência numérica ao Power BI.

`CERTIFICADA` exige regra equivalente, teste semântico e filtros/RLS preservados. `PARCIAL` indica dependência original indisponível. `DIVERGENTE` indica regra conhecida ainda diferente. `PENDENTE` indica ausência de contrato ou implementação.

## Resultado por visual

| Card | Componente | Implementação atual | Status | Evidência |
|---|---|---|---|---|
| TVD | base, último ponto, exclusões e tarefas | mart diário, `LASTNONBLANK` por Ano/Mês, exclusão nas duas dimensões e contagem sem `DISTINCT` | CERTIFICADA | testes de fechamento, lacuna, local e alertas |
| TVD | M0, M-1 e U3M | maior mês com dado, deslocamentos mensais e `(M1+M2+M3)/3` | PARCIAL | falta `0_0_CALENDARIO[M0…M-3/U3M]` |
| IVD | base, último ponto, exclusões e tarefas | mesma mecânica; risco usa `REGRA_CRITICO='U'` | CERTIFICADA | testes de fechamento, local e risco `U` |
| IVD | M0, M-1 e U3M | maior mês com dado e denominador fixo 3 | PARCIAL | âncora original ausente |
| Giro | fórmula e barras | `SUM(giro positivo)/COUNT(giro positivo)`; quatro atividades permitidas | CERTIFICADA | teste ponderado e allowlist ordenada |
| Giro | âncora temporal | mês máximo disponível | PARCIAL | flags M0/M-1 ausentes |
| OSA | percentual | `1 - SUM(problemas)/SUM(ativos)`; zero retorna `BLANK` | CERTIFICADA | razão dos totais e divisor zero |
| OSA | Perda R$ | `gold.fato_mensal_causa_osa`: `SUM(qtd_perda)*MAX(fator)*AVG(preço)` | CERTIFICADA | 27 meses; delta máximo `1,68e-7` |
| OSA | críticos | `COUNT(id_item)`, problemas M0 > 0 e relação `F → Fast Mover` | CERTIFICADA | relação provada; 3.866 linhas |
| OSA | risco | `COUNT(id_item)`, problemas M0 > 0 e atividade `S` | CERTIFICADA | 3.279 linhas; sem `DISTINCT` |
| OSA | períodos | razão recalculada e Perda U3M / 3 | PARCIAL | fórmula certificada; calendário ausente |
| Vendas | Sell out | decisão faturamento/fallback por região, com fator no volume e preço | CERTIFICADA | recalculado depois dos filtros |
| Vendas | custo | soma linha a linha `volume × custo` | CERTIFICADA | componente aditivo |
| Vendas | quantidade | `valor` usa faturamento; demais medidas usam volume × fator | CERTIFICADA | seletor e taxa diferente de 1 |
| Vendas | períodos | MTD/M-1 e medida U3M / 3 | PARCIAL | fórmula certificada; calendário ausente |
| Estoque | custo | soma `estoque_medio × avg_price_cost` | CERTIFICADA | componente aditivo |
| Estoque | quantidade | `MAX(MES_ANO)`, `SUM(estoque) × fator`; U3M reproduz medida / 3 | CERTIFICADA | perfil `stock_bundle` |
| Estoque | âncora temporal | mês máximo disponível | PARCIAL | flags do calendário ausentes |
| ROI | atual, anterior e U3M | zero se sell out ou custo é zero; U3M recalcula componentes | CERTIFICADA | testes dos zeros e U3M |
| ROI | anual 12M | soma dos ROI mensais dos últimos 12 pontos, exibida como `Anual 12M` | PARCIAL | fórmula testada; âncora depende do calendário ausente |
| ROI | barras | mês atual/anterior; quatro atividades em ordem fixa | CERTIFICADA | teste de perfil e categorias |
| Markup | atual, anterior e U3M | zero nos ramos DAX; U3M = sell out agregado / custo agregado | CERTIFICADA | não usa média de percentuais |
| Markup | barras | mês atual/anterior; quatro atividades em ordem fixa | CERTIFICADA | allowlist renderizada |

Não há componente com regra conhecida ainda `DIVERGENTE`. As classificações `PARCIAL` restantes decorrem da ausência do contrato original de calendário.

## Conversão selecionável

O dashboard publica filtro de seleção única `Medida`, com padrão visual explícito `unidade`. O padrão não está embutido nas fórmulas: o usuário pode selecionar `hectolitro`, `libra`, `litro`, `quilograma`, `tonelada`, `unidade` ou `valor`. Mais de uma seleção ou nenhuma seleção reproduz `SELECTEDVALUE` inválido e retorna `BLANK`/sem linhas nas métricas dependentes.

Junções usam `id_customer + id_item + nm_measure`. `valor` implementa o ramo de faturamento de Venda Histórico; nenhuma taxa `valor` foi inventada em `dim_conversao`.

## Serving e filtros

O caminho sem filtro detalhado usa:

```text
gold.nr_overview_semantic_default  → 833 linhas / 328 KiB
gold.nr_osa_semantic_default       → 189 linhas / 56 KiB
```

O primeiro mart mantém os escopos `all`, para cards sem atividade e `SUMX` regional sobre o contexto inteiro, e `activity`, para Giro, ROI e Markup.

Quando Rede, Bandeira, UF, Cidade, Tipo local, Loja, Região, atividade, Marca, hierarquia ou Item é filtrado, o dataset empurra o predicado para a fonte e só então recalcula região, fator, OSA e alertas. RLS permanece em `id_customer`; junções de localização, item, conversão e atividade incluem o tenant.

## Categorias das barras

Somente estas categorias são retornadas/renderizadas, nesta ordem:

1. Fast Mover;
2. Slow Mover;
3. Ultra Slow Mover;
4. New Mover.

`Outros`, Non Mover, Não Informado, nulo e classificações adicionais são descartados. Categorias ausentes não são fabricadas.

## Calendário ainda parcial

A busca em `config/`, `docs/`, `local-engine/`, SQLs e arquivos versionados não encontrou TMDL nem definição de:

```text
0_0_CALENDARIO[M0]
0_0_CALENDARIO[M-1]
0_0_CALENDARIO[M-2]
0_0_CALENDARIO[M-3]
0_0_CALENDARIO[U3M]
```

A implementação conserva a âncora no maior mês com dado e registra `PENDENTE_CALENDARIO_M0`. Nenhum período dependente foi declarado totalmente certificado sem essa evidência.

## Validação e performance

- 12 testes Python específicos da Visão Geral;
- suíte consolidada de contratos e pipeline;
- 51 verificações JavaScript do plugin;
- oito consultas integradas do Superset sem erro;
- fallback com `Rede=ANGELONI`, medida `unidade` e tenant 142 sem erro;
- sell out regional: 27 meses, delta máximo `5,96e-8`;
- Perda OSA: 27 meses, delta máximo `1,68e-7`;
- alertas OSA: 3.866 críticos e 3.279 em risco, iguais à consulta independente;
- SQL compacto: `0,465 ms` em `EXPLAIN (ANALYZE, BUFFERS)`;
- oito charts após bootstrap: `1,768 s` na primeira execução e `0,601 s` com cache aquecido;
- caminho filtrado exato (`ANGELONI`): `4,425 s` para os oito charts.

O baseline anterior era `1,530 s` na primeira execução registrada. A medição fria atual variou acima dele e a aquecida ficou abaixo. O serving compacto permaneceu submilissegundo; a variação fria está no ciclo de metadata/cache/execução do Superset e deve continuar monitorada.

## Arquivos principais desta rodada

- `analytics-db/marts/39_overview_semantic_certification.sql`;
- `analytics-db/marts/30_neoretail_serving_marts.sql`;
- `analytics-db/marts/31_overview_performance.sql`;
- `superset/bootstrap_overview.py`;
- `superset/validate_overview.py`;
- plugin React e testes;
- testes Python;
- este documento.

## Resposta objetiva

As fórmulas conhecidas dos oito cards agora equivalem às regras fornecidas do Power BI, incluindo conversão, `SUMX` regional, Perda OSA, alertas sem `DISTINCT`, ROI, Markup e barras por atividade. A equivalência temporal completa ainda não pode ser afirmada para componentes M0/M-1/U3M/12M porque a definição original das flags de calendário não está disponível no projeto.
