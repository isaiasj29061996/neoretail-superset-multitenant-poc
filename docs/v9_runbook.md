# Runbook V9

## Primeiro teste recomendado

Use o cliente 259, que já foi validado na V8.1:

```powershell
.\run-local-pipeline.ps1 -Step 02A -Customer 259
.\run-local-pipeline.ps1 -Step 02B -Customer 259
.\run-local-pipeline.ps1 -Step 03A -Customer 259
.\run-local-pipeline.ps1 -Step 03B -Customer 259
.\run-local-pipeline.ps1 -Step 03C -Customer 259
.\run-local-pipeline.ps1 -Step 03D -Customer 259
.\run-local-pipeline.ps1 -Step 04 -Customer 259
.\run-local-pipeline.ps1 -Step 05 -Customer 259
.\run-local-pipeline.ps1 -Step 06 -Customer 259
.\run-local-pipeline.ps1 -Step 07 -Customer 259
.\run-local-pipeline.ps1 -Step 08 -Customer 259
.\create-superset-kpi-views.ps1
```

Depois repita com 609 e 16868 ou execute `run-multitenant-refresh.ps1`.

## Dataset no Superset

Cadastre `gold.vw_mart_visao_industria` uma única vez. Marque `data` como coluna
temporal e habilite como filtráveis as colunas `rede`, `bandeira`, `uf`,
`cidade`, `tipo_local`, `loja`, `descricao_marca`, `item` e
`tp_activity_level`.

Crie Native Filters no dashboard e defina dependências em cascata, por exemplo:

`rede → bandeira → uf → cidade → loja`.

Não crie filtro visível de `id_customer`: esse contexto pertence ao backend e
ao RLS.

## Teste de isolamento obrigatório

1. Abra o portal com o cliente 259 e registre contagens/TVD.
2. Troque para 609; a página renova o Guest Token.
3. Confirme que os números mudaram e que nenhuma linha de 259 aparece.
4. Repita com 16868.
5. Tente enviar ao endpoint um ID não autorizado e confirme HTTP 403.

Esse teste deve passar antes de construir os charts finais.
