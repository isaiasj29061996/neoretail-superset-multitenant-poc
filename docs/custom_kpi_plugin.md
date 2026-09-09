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

## Diagnostico e validacao do plugin

Este plugin exige uma serie diaria: Results deve conter a coluna temporal e
as tres metricas configuradas. `MAX(tvd_mtd)` sobre `gold.vw_kpi_card_tvd`
pertence ao card agregado antigo e nao fornece o historico diario necessario.
Em charts existentes, confira o dataset e reaplique a configuracao TVD acima.

No Superset 6, o callback de `buildQueryContext` deve ser fornecido no segundo
argumento, diretamente ou em `options.buildQuery`. O eixo entra em `columns`
e o grao temporal em `extras.time_grain_sqla`. O transformador aceita tanto
`rawFormData` (snake_case) quanto `formData` (camelCase).

Teste unitario, a partir da raiz do repositorio, com Node.js instalado:

```powershell
node superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/regression.mjs
```

O teste usa doubles das dependencias Superset; nao substitui a validacao no
frontend compilado. Depois do build, confirme em Results uma linha por dia com
TVD, criticos e risco, os comparativos mensais e os filtros nativos. Execute
tambem o teste de isolamento por cliente do runbook V9.

## Visao geral da industria

O plugin tambem possui variantes de area, barras comparativas, indicadores
multiplos e OSA com tarefas. A miniatura e incorporada aos metadados do plugin,
sem depender de um arquivo externo.

O cadastro reproduzivel dos dois datasets, oito graficos, filtros em cascata e
dashboard fica em `superset/bootstrap_overview.py`. Ele altera somente os
metadados do Superset; o dataset historico e virtual e consulta a Gold sem criar
tabelas ou views:

```powershell
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/bootstrap_overview.py
```

Validacao das consultas dos oito graficos:

```powershell
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/validate_overview.py
```

## Panorama da industria

As variantes `panorama` e `rankbars` atendem aos evolutivos combinados e aos
comparativos horizontais. O dashboard usa abas do Superset para reproduzir os
bookmarks Valor/Quantidade, Mensal/Semanal, Estoque/Giro e ROI/OSA/Falta e
Excesso, alem das alternancias de ranking e analise detalhada.

O cadastro reproduzivel esta em `superset/bootstrap_panorama.py`. Os datasets
criados por ele sao virtuais e somente consultam a Gold. A industria inicial e
`3CORACOES`, identificada por `id_customer = 259`, configurada como valor padrao
do filtro nativo de industria.

```powershell
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/bootstrap_panorama.py
docker compose exec -T superset /app/.venv/bin/python /app/pythonpath/validate_panorama.py
```

## OSA da industria

O dashboard de OSA em valor e criado por `superset/bootstrap_osa_industry.py`.
Ele usa o historico para o evolutivo e rankings e a fato mensal de causas para
as colunas empilhadas e barras por motivo/causa. A validacao reproduzivel fica
em `superset/validate_osa_industry.py`.
