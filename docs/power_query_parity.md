# Paridade Power Query na Silver

## Evidencia utilizada

As regras desta versao foram extraidas de `NeoRetail Pocket RF.SemanticModel`,
em TMDL. O parametro `_nomeCliente` vale `3CORACOES`. Credenciais e tokens do
Blob nao fazem parte do pacote; a execucao usa somente o `.env` local.

## Fronteira de responsabilidade

- Bronze: copia os Parquets sem alterar as colunas de negocio e acrescenta
  somente metadados de linhagem.
- Silver: reproduz selecao, uniao, filtros, joins, nomes, nulos e tipos das
  consultas M.
- Camada semantica/Gold: recebe colunas calculadas e medidas DAX. Elas nao sao
  simuladas na Silver.

Variacoes comprovadas de schema entre o Blob e o M sao declaradas como aliases.
No fato diario, `DIAS_SEM_VENDAS` (Parquet) e consolidada em
`dias_sem_venda` (nome canonico da Silver/Power Query).

## Dimensoes M reproduzidas

| Consulta M | Silver | Regra principal |
|---|---|---|
| `DIM_CUSTOMER` | `dim_customer` | deduplica, tipa e filtra `3CORACOES` |
| `AUX_CONTRATADO_LOCAL` | `aux_contratado_local` | filtra cliente e exclui GPA, GPA2 e MLUIZA |
| `DIM_ITENS` | `dim_itens` | inner join com cliente, cria Item, renomeia hierarquias e deduplica ID_ITEM |
| `DIM_CONVERSAO` | `dim_conversao` | inner join com cliente e ordena ID_ITEM |
| `DIM_CATALOGO_PRODUTOS` | `dim_catalogo_produtos` | filtra industria e fixa MEDIDA como unidade |
| `AUX_CONTRATADO_SEGMENTO` | `aux_contratado_segmento` | normaliza e restringe os seis segmentos de mercado |
| `DIM_LOCAL` | `dim_local` | cruza varejistas contratados, formata CNPJ e deriva regiao/loja |
| `DIM_CATALOGO_LOCAL` | `dim_catalogo_local` | prepara o cadastro usado por FATO_MERCADO e exclui a rede GPA |
| `DIM_NIVEL_ATIVIDADE` | `dim_nivel_atividade` | deriva a dimensao apos consolidar o fato de nivel de atividade |

`DIM_LOCAL` exige a nova fonte Bronze
`DIMENSAO/DIMENSAO_VAREJO_CONTRATADO.snappy.parquet`, agora carregada em 02A.

## Fatos M reproduzidos

| Consulta M | Familia Bronze | Silver |
|---|---|---|
| `FATOS_PARTICULAR_DIARIA` | `fato_diaria` | `fato_diaria` |
| `FATOS_PARTICULAR_SEMANAL` | `semanal` | `fato_semanal` |
| `FATOS_PARTICULAR_HISTORICO` | `fato_historico` | `fato_historico` |
| `FATOS_PARTICULAR_TVD_IVD` | `fato_ivd_tvd` | `fato_ivd_tvd` |
| `FATOS_MENSAL_CAUSA_OSA` | `mensal_causa_osa` | `fato_mensal_causa_osa` |
| `FATOS_PARTICULAR_NIVEL_ATIVIDADE` | `fato_nivel_atividade` | `fato_nivel_atividade` |
| `FATOS_PRECO` | `fato_preco` | `fato_preco` |
| `CALCULO_OPORTUNIDADES` | `etl_calc_v2` | `etl_calc_v2` e `calculo_oportunidades` |

`ETL_CALC` sem `V2` continua disponível apenas como staging tecnico. O modelo
atual consulta explicitamente `ETL_CALC_V2`.

## Ordem de execucao

```powershell
.\run-local-pipeline.ps1 -Step 02A
.\run-local-pipeline.ps1 -Step 02B -Family all
.\run-local-pipeline.ps1 -Step 03A
.\run-local-pipeline.ps1 -Step 03B
.\run-local-pipeline.ps1 -Step 03C
.\run-local-pipeline.ps1 -Step 03D
```

`FATO_MERCADO` está fora do pipeline da POC e não participa da Silver nem do
quality gate.

## Validacao

O teste executavel dentro do container cobre datas derivadas, tipos, tratamento
de nulos, filtro do cliente, varejistas contratados, CNPJ e segmentos:

```powershell
docker compose exec -T local-engine pytest -q /workspace/local-engine/tests
```

O gate operacional continua sendo:

```powershell
.\run-local-pipeline.ps1 -Step 03D
```

O resultado fica em `audit.silver_quality_gate`.

## Colunas que nao pertencem a Silver

As oito colunas calculadas DAX de `CALCULO_OPORTUNIDADES` permanecem para a
etapa de modelo semantico/Gold: `nivel_de_atividade_tvd`,
`nivel_de_atividade_ivd`, `nivel_de_atividade_osa`, `flag_ruptura`,
`flag_item_sem_venda`, `flag_problema_osa`, `flag_metrica_padrao_osa` e
`status_ruptura`. A consulta M nao cria essas colunas; portanto, criá-las em 03
seria alterar a regra original.
