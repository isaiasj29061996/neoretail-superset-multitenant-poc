> Cópia para GitHub: números de origem e identificadores numéricos omitidos. Original integral exige backup externo. Não usar esta cópia como fixture ou SQL executável.

# Reconstrução Lactalis only — auditoria inicial

Status: interrompida antes de ingestão; ambiente ainda não reconstruído.

## Git

- Checkout inicial: fix/panorama-weekly-filter-contract, [DADO OMITIDO]bd8[DADO OMITIDO]e, com alterações locais preservadas.
- Worktree candidata: .worktrees/osa-industry.
- Branch: feat/osa-industry-certification.
- Commit: [DADO OMITIDO]a1[DADO OMITIDO]dc1[DADO OMITIDO]eeabedf9[DADO OMITIDO]ee5[DADO OMITIDO].
- feat/panorama-stock-certification é ancestral da branch OSA (merge-base exit [DADO OMITIDO]).
- A worktree OSA também contém alterações locais, incluindo serving OSA não rastreado; nada foi sobrescrito.
- Main, commits, merges e push não foram alterados.

## Identidade

- Evidência atual: consulta somente leitura a DIMENSAO/DIMENSAO_CUSTOMER.snappy.parquet no Azure, registrada em generated/lactalis_identity_current_source.json. Uma única correspondência: ID_CUSTOMER [DADO OMITIDO], NM_CUSTOMER LACTALIS. A fonte contém somente ID_CUSTOMER e NM_CUSTOMER.
- Referências locais adicionais: .worktrees/multitenant-fasttrack/config/customers.yaml e docs/multitenant_fasttrack.md. Essas referências incluem alterações locais não commitadas; não foram tratadas como prova de dados atuais.
- id_customer/tenant: [DADO OMITIDO].
- Nome: LACTALIS; tenant_key: lactalis.
- Prefixo: FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS.
- Layout: partitioned_customer_daily_v1.
- Schema do registro multitenant: gold_lactalis.
- manufacturer_id separado: não identificado. Não foi presumido que seja [DADO OMITIDO].
- Evidências históricas de carga não representam validação ou contagens deste novo ambiente.
- Configuração atual da worktree OSA habilita somente AMBEV [DADO OMITIDO] e usa gold nos marts; adaptação explícita é necessária.

## Fluxo encontrado, ainda não executado

[DADO OMITIDO] setup → [DADO OMITIDO] discovery → [DADO OMITIDO] dimensões Bronze + [DADO OMITIDO]B candidatos por cliente → [DADO OMITIDO]A dimensões Silver → [DADO OMITIDO]B fatos Silver → [DADO OMITIDO]C oportunidades → [DADO OMITIDO]D validação → [DADO OMITIDO] aprovação → [DADO OMITIDO] dimensões Gold → [DADO OMITIDO] fatos Gold → [DADO OMITIDO] readiness → [DADO OMITIDO] quality gate → SQL serving atual, incluindo [DADO OMITIDO]_osa_certified_semantic.sql → Superset init/bootstraps → embedded → validators/ChartData/RLS.

O runner all não executa [DADO OMITIDO]B. A etapa [DADO OMITIDO] grava dimensões completas sem filtro de tenant na Bronze. Não deve ser executada como está para este pedido. O runner OSA também contém valores e imagem padrão da execução anterior; precisa de seleção explícita Lactalis e revisão dos validators.

## Infraestrutura e configuração

Docker Desktop foi iniciado no caminho instalado em AppData/Local/Programs/DockerDesktop. Engine responde com versão [DADO OMITIDO]. Auditoria inicial mostra nenhum container, imagem ou volume. docker system df: imagens, containers, volumes e build cache todos [DADO OMITIDO] B. Acesso ao pipe exige execução fora do sandbox.

C: livre = [DADO OMITIDO] bytes ([DADO OMITIDO] GiB); usado = [DADO OMITIDO] bytes. analytics_data e local_lake não existem. Banco Analytics e top [DADO OMITIDO] tabelas indisponíveis, pois nenhum banco foi criado.

.env existe no checkout inicial e na worktree OSA. Valores e segredos não foram exibidos; configuração obrigatória ainda não foi integralmente validada.

## Bloqueios e resultado

[DADO OMITIDO]. Confirmar se existe manufacturer_id separado e sua relação com tenant [DADO OMITIDO] antes da ingestão. A dimensão corporativa consultada não contém esse campo; atribuir [DADO OMITIDO] também a manufacturer_id seria uma suposição. Interrupção conforme a regra explícita de parar perante ambiguidade de identificação.
[DADO OMITIDO]. Preparar filtro explícito também para as dimensões Bronze; preservar comportamento padrão e testar a alteração.
[DADO OMITIDO]. Resolver registro/roteamento Lactalis na worktree OSA e compatibilidade de gold versus gold_lactalis.

Não houve build, ingestão, criação de banco, marts ou dashboards. Linhas Bronze/Silver/Gold, schemas, ausência de outros clientes nos dados, validators, performance, embedded e RLS permanecem não validados. Não houve remoção de volumes ou restauração de dados antigos. A tarefa não está concluída.
