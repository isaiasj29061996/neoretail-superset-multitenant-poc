# Exportação de dados

A seção `Exportação` reproduz a navegação de referência do Power BI com duas páginas embedded:

- `Histórico dia`
- `Histórico mês`

Cada página contém quatro abas internas:

- `Varejo`
- `Produto`
- `Geral`
- `Resumo`

Os filtros seguem o padrão visual de referência: Rede, Bandeira, UF/Cidade, Tipo local/Loja, Nível de atividade, Descrição marca, Hierarquias, Item, Unidade de medida, Indicador e período.

A primeira versão usa `Venda` como indicador e deixa a estrutura pronta para ampliar outros indicadores depois.

Serving marts:

- `gold.nr_export_daily`
- `gold.nr_export_monthly`

Bootstrap:

- `superset/bootstrap_export.py`

No embedded, controles de chart ficam visíveis apenas para dashboards da seção `export`, permitindo usar o menu de download do Superset sem alterar as outras áreas do produto.
