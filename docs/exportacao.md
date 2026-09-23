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

O seletor oferece Venda, cobertura, estoque, estoque em trânsito, ISV, OSA,
perdas OSA e preço médio. O dataset injeta somente o indicador selecionado por
uma allowlist; ele não multiplica mais cada linha física por todos os indicadores.
O limite do chart e do Superset é de 100.000 linhas por consulta/exportação.

Serving marts:

- `gold.nr_export_daily`
- `gold.nr_export_monthly`
- `gold.nr_export_daily_retail_summary`
- `gold.nr_export_monthly_retail_summary`
- `gold.nr_filter_options` para as listas dimensionais

O filtro `Indicador` usa um dataset de nove linhas. Os demais filtros usam a mart
leve de opções, enquanto ano/mês/dia continuam ligados ao período real de cada
dataset de exportação.

A aba `Varejo` usa o resumo por período e rede no estado padrão. Ao receber um
filtro que exige produto, loja ou outra dimensão ausente do resumo, o dataset
virtual seleciona automaticamente a mart detalhada e preserva o filtro.

Bootstrap:

- `superset/bootstrap_export.py`

No embedded, controles de chart ficam visíveis apenas para dashboards da seção `export`, permitindo usar o menu de download do Superset sem alterar as outras áreas do produto.
