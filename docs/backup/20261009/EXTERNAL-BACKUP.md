# Backup externo obrigatório — privado e fora desta máquina

## Estado constatado

Docker Engine não respondeu em 09/10/2026: não foi possível verificar volumes, executar dumps ou testar restauração dos bancos. Existe `%LOCALAPPDATA%/Docker/wsl/disk/docker_data.vhdx`, tamanho lógico 132268425216 bytes (~123,2 GiB), e `wsl/main/ext4.vhdx`. O tamanho não comprova integridade nem quais volumes existem. A cópia externa ainda NÃO foi realizada.

## Copiar para SSD externo ou armazenamento privado criptografado

- `.env` da raiz, osa-industry, governed-assistant e governed-assistant-ambev, sem publicar valores; certificados/chaves privados eventualmente existentes; preservar especialmente SUPERSET_SECRET_KEY, GUEST_TOKEN_JWT_SECRET, credenciais PostgreSQL/Azure e configurações de login. A chave antiga do Superset é necessária para descriptografar conexões da metadata DB restaurada.
- Diretório completo do projeto, incluindo `.git`, `.worktrees` e `generated` de cada worktree, como cópia externa privada adicional. O índice/estado WIP e exclusões locais são preservados por essa cópia; reconstruir worktrees em outra máquina com `git worktree add`, sem confiar nos caminhos absolutos antigos.
- Dois fixtures reais listados no README; relatórios integrais, JSON de resultados, Parquet, SQL replay, manifests/ETags e provas não sanitizadas em todos os `generated`.
- PBIP/PBIX originais em Downloads: `NeoRetail Pocket RF.pbip`, `.Report`, `.SemanticModel`, todas as variantes `.pbix` relevantes. O antigo `NeoRetail Pocket RF.Report.zip` não foi encontrado no caminho informado anteriormente; o PBIP extraído em osa-industry/generated existe e deve ser copiado integralmente, inclusive cache privado se desejado.
- `%USERPROFILE%/.codex/attachments`, prompts/anexos e configurações necessárias; segredos de ferramentas em cofre privado. Não copiar perfis Chrome/cookies para GitHub.
- Bancos Analytics e metadata Superset; lake Bronze/Silver/Gold e raw-cache. O Compose osa-industry declara `superset_metadata`, `analytics_data`, `redis_data`, `local_lake`; prefixo de projeto `neoretail-v9-multitenant`. `local_lake` monta `/data`, incluindo lake e raw-cache. Nomes completos esperados: `neoretail-v9-multitenant_superset_metadata`, `neoretail-v9-multitenant_analytics_data`, `neoretail-v9-multitenant_redis_data`, `neoretail-v9-multitenant_local_lake`. Confirmar os volumes realmente existentes com Engine ativo; esta é a configuração declarada, não inventário de volumes verificado.
- Apresentações, roteiros e versões NeoRetail exclusivas em Downloads que estejam fora deste repositório.

## Caminho preferido: dumps lógicos e volumes consistentes

1. Iniciar somente Docker Desktop/Engine, sem pipeline. Na worktree que representa o Compose ativo, registrar `docker compose ps -a`, `docker volume ls` e `docker inspect` dos volumes/mounts. Não publicar o inspect completo: pode conter variáveis sensíveis.
2. Definir um destino em OUTRO dispositivo/cofre privado, com espaço suficiente. Não tratar `C:` como backup resistente à formatação. Use criptografia e restrinja acesso.
3. Para cada banco, produzir dump dentro do container e copiar em binário com `docker cp` (não usar redirecionamento textual PowerShell para dumps binários):

```powershell
docker compose exec -T analytics-db pg_dump -U analytics -d analytics -Fc -f /tmp/neoretail-analytics-preformat.dump
$cid = docker compose ps -q analytics-db
docker cp "${cid}:/tmp/neoretail-analytics-preformat.dump" "E:/NeoRetail-private/analytics.dump"
docker compose exec -T superset-db pg_dump -U superset -d superset -Fc -f /tmp/neoretail-metadata-preformat.dump
$cid = docker compose ps -q superset-db
docker cp "${cid}:/tmp/neoretail-metadata-preformat.dump" "E:/NeoRetail-private/superset-metadata.dump"
```

Ajustar destino, usuários e nomes de banco ao `.env` real. Checar exit code após CADA comando. Esses comandos são procedimento, NÃO foram executados por esta rodada.

4. Parar serviços que escrevem durante a exportação consistente dos volumes (sem `down -v`); arquivar cada volume com ferramenta Docker compatível e mount de origem somente leitura. Não tar PostgreSQL ativo como se fosse backup consistente. Não excluir volumes nem arquivos.
5. Se o Engine não voltar: encerrar Docker Desktop, parar WSL de forma controlada e copiar os VHDX completos para dispositivo externo. Manter cópia intacta; essa alternativa física deve ser testada com versão compatível do Docker/WSL. Não copiar VHDX em uso. Não houve parada/cópia nesta rodada.
6. Gerar manifesto SHA256 de arquivos copiados; conferir no destino. Dumps: validar `pg_restore --list` e efetuar restauração de teste em bancos/volumes descartáveis e isolados, preservando a cópia original. Verificar tabelas, counts, tenants, datas, dashboards, configurações e acesso com a chave preservada.

## Critério para formatar

Somente depois de: branches verificadas por fetch/checkout independente; backup privado em outro dispositivo; hashes conferidos; dumps/bancos restaurados em teste; PBIP, fixtures e segredos localizados no destino. Neste momento o backup externo e a restauração dos dados NÃO estão comprovados: **a máquina ainda não está liberada para formatação**.
