# Pipeline local 00-08 com Silver 03A-03D

## Execucao recomendada

```powershell
.\run-local-pipeline.ps1
```

O comando executa `python -m neoretail_local.pipeline --step all` dentro do
`local-engine`. Cada etapa tambem possui um notebook Jupytext em
`local-engine`. A etapa Bronze usada pela POC possui dois subfluxos:

- `02A`: dimensoes com paths aprovados;
- `02B`: fatos candidatos por industria.

Os caminhos podem ser executados pelo PowerShell:

```powershell
.\run-local-pipeline.ps1 -Step 02A
.\run-local-pipeline.ps1 -Step 02B -Family fato_ivd_tvd
```

O `all` nao executa automaticamente `02B`, porque a materializacao de
todos os candidatos e volumosa e deve ser disparada conscientemente.

Depois de materializar as familias necessarias, execute a Silver completa:

```powershell
.\run-local-pipeline.ps1 -Step 03
```

Ou acompanhe cada responsabilidade separadamente:

```powershell
.\run-local-pipeline.ps1 -Step 03A  # dimensoes
.\run-local-pipeline.ps1 -Step 03B  # fatos por familia/varejista
.\run-local-pipeline.ps1 -Step 03C  # calculo_oportunidades via ETL_CALC_V2
.\run-local-pipeline.ps1 -Step 03D  # validacao Bronze x Silver
```

`FATO_MERCADO` foi excluida do pipeline da POC. Candidatos antigos de mercado
que ainda existam no lake nao sao lidos pela Silver nem pelo quality gate.

## Camadas

- Raw cache: copia tecnica controlada por ETag dos arquivos aprovados ou candidatos.
- Bronze: dados fieis ao Parquet, com candidatos isolados por familia e varejo.
- Silver: nomes canonicos, strings tratadas, uniao tolerante a schema drift,
  `tenant_id`, linhagem, consolidacao de oportunidades e quality gate.
- Gold: objetos liberados para consumo e publicados no PostgreSQL.
- Audit: inventario, prontidao de metricas e quality gate.

## Idempotencia

- O cache nao baixa novamente um Blob com o mesmo ETag.
- Escritas de lake usam `overwrite` por tabela.
- Publicacoes JDBC usam `overwrite` por tabela Gold.
- Schemas PostgreSQL usam `CREATE SCHEMA IF NOT EXISTS`.

## Gates

As etapas 04 e 06 retornam `blocked` quando
`config/approved_facts.yaml` estiver vazio. Isso e esperado e nao libera fatos
sem evidencia. A etapa 08 valida dimensoes Gold e somente os fatos aprovados.

## Fatos candidatos da 3CORACOES

O prefixo `PARTICULAR_3/3CORACOES` possui nove familias reconhecidas por regex.
A ingestao preserva cada arquivo em uma tabela Bronze independente e adiciona:

- `_source_file`;
- `_retailer`;
- `_fact_family`;
- `_candidate_status`;
- `_ingested_at`.

Use primeiro:

```powershell
.\ingest-fact-candidates.ps1 -InventoryOnly
```

Depois carregue uma familia de cada vez, por exemplo:

```powershell
.\ingest-fact-candidates.ps1 -Family etl_calc_v2
.\ingest-fact-candidates.ps1 -Family fato_diaria
```

O catalogo fica em `audit.fact_candidate_inventory` e o resumo local em
`generated/fact_candidate_ingestion.json`. Esse fluxo nao altera
`approved_facts.yaml`. A etapa 03B pode consolidar candidatos na Silver para
validacao tecnica, mas somente fatos aprovados podem chegar a Gold.

Arquivos existentes com zero linhas recebem status `empty_source`, nao geram
tabela Bronze e nao interrompem os demais candidatos da familia.

## Reconstrucao do Power Query

O contrato `config/power_query_contracts.yaml` registra oito consultas
dimensionais, nove familias particulares e a evidencia de que
`CALCULO_OPORTUNIDADES` consome os
arquivos `ETL_CALC_V2` por varejista. A etapa 03:

- normaliza nomes como `Nivel de atividade TVD` para `nivel_de_atividade_tvd`;
- rejeita colisoes de nomes apos normalizacao;
- remove somente duplicidades exatamente iguais de dimensoes;
- nao remove fatos sem uma chave de negocio comprovada;
- une colunas ausentes e resolve conflitos tecnicos de tipo explicitamente;
- preserva metadados de origem e adiciona linhagem Silver;
- grava `audit.opportunity_readiness` e `audit.silver_quality_gate`.

As colunas-fonte do `ETL_CALC_V2` sao preservadas. A marcacao
`power_query_m_exact_dax_deferred_to_semantic_layer` significa que as consultas
M foram reproduzidas, enquanto formulas e colunas calculadas DAX continuam na
camada semantica. Ela nao autoriza criar TVD, IVD, OSA ou oportunidade por
aproximacao.

## Lake format

`LOCAL_LAKE_FORMAT=parquet` e o padrao mais simples e confiavel no localhost.
`LOCAL_LAKE_FORMAT=delta` ativa `delta-spark`, podendo exigir acesso ao Maven
na primeira inicializacao do Spark para resolver os JARs.
