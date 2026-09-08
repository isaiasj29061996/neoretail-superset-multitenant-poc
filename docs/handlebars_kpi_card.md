# Card KPI NeoRetail como um unico visual

O Superset 6 ja inclui o tipo de grafico `Handlebars`. Ele recebe o resultado de
uma consulta e renderiza HTML, CSS e SVG dentro de um unico chart. O primeiro
template reproduz o card `TVD - Pre-ruptura`.

## 1. Criar a view semantica

No PowerShell, na raiz do projeto:

```powershell
.\create-superset-kpi-views.ps1
docker compose restart superset
```

## 2. Registrar o dataset

No Superset, crie um dataset fisico com:

- Database: `NeoRetail Gold - PostgreSQL Local`
- Schema: `gold`
- Table: `vw_kpi_card_tvd`

## 3. Criar o chart unico

1. Selecione o dataset `vw_kpi_card_tvd`.
2. Em `All charts > Other`, escolha `Handlebars`.
3. Em `Query mode`, selecione `Raw records`.
4. Em `Columns`, inclua todas as colunas da view.
5. Deixe `Row limit` em `100`. No Embedded, o `id_customer` vira do Guest Token.
6. Cole `superset/chart-templates/neoretail_kpi_card_tvd.html` em
   `Handlebars Template`.
7. Cole `superset/chart-templates/neoretail_kpi_card_tvd.css` em `CSS Styles`.
8. Execute e salve como `TVD - Pre-ruptura | Card`.

O visual e um unico chart e responde aos filtros aplicaveis ao dataset, inclusive
`id_customer`. A primeira view e agregada por cliente. Filtros de loja, item e
varejista serao adicionados quando o mart amplo de filtros for construido.

## Seguranca

A sanitizacao HTML permanece ligada. `superset_config.py` libera somente CSS e
as tags SVG usadas pelo card; scripts continuam bloqueados.
