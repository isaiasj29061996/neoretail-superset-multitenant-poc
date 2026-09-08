# Plugin NeoRetail KPI Card

O visual e um plugin React proprio registrado no `MainPreset` do Superset 6.
Ele nao usa Handlebars nem Jinja.

## Build

O primeiro build baixa o codigo-fonte do Superset 6.0.0 e compila o frontend.
Ele e mais demorado que os builds anteriores.

```powershell
docker compose build --no-cache superset
docker compose up -d --force-recreate superset
```

Depois atualize o navegador com `Ctrl + Shift + R`. Em `Create a new chart`,
pesquise por `NeoRetail KPI Card`.

## Dataset

Use `gold.vw_mart_visao_industria`. Recrie a view antes de configurar o chart:

```powershell
.\create-superset-kpi-views.ps1
```

## Configuracao TVD

- X-axis: `data`
- Time grain: `Day`
- Time range: `No filter`, durante a primeira validacao
- Metrica principal: `SUM(tvd_simplificado)`
- Itens criticos:
  `COUNT(DISTINCT CASE WHEN regra_critico = 'CRITICO' AND COALESCE(oportunidade_tvd, 0) > 0 THEN opportunity_key END)`
- Itens com risco:
  `COUNT(DISTINCT CASE WHEN regra_critico = 'F' AND COALESCE(oportunidade_tvd, 0) > 0 THEN opportunity_key END)`
- Titulo: `TVD - Pre-ruptura`
- Menor valor e melhor: ligado
- Mostrar tarefas: ligado
- Destino: vazio ate a pagina TVD existir

## Configuracao IVD

Duplique o chart e altere:

- Metrica principal: `SUM(ivd_simplificado)`
- Nas duas metricas de tarefa, use `oportunidade_ivd` no lugar de
  `oportunidade_tvd`.
- Titulo: `IVD - Excesso`

## Calculos do componente

- MTD: ultimo dia com valor do mes mais recente retornado.
- Mes anterior: ultimo dia com valor do mes anterior.
- Media U3M: media dos fechamentos dos tres meses anteriores.
- Area: evolucao diaria do mes mais recente.

Filtros nativos e o RLS entram no QueryObject criado pelo Superset antes dos
dados chegarem ao componente React.
