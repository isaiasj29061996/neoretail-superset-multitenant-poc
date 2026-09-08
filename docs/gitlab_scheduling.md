# GitLab CI e atualização diária

O arquivo `.gitlab-ci.yml` possui validação e um job de refresh. O runner de
refresh precisa ser Windows, ter Docker Desktop/Engine disponível e possuir a
tag `windows-docker`.

Cadastre as credenciais somente como variáveis protegidas e mascaradas do
GitLab CI/CD. Não versione `.env`.

Variáveis mínimas:

- `AZURE_STORAGE_CONNECTION_STRING`
- `SUPERSET_SECRET_KEY`
- `GUEST_TOKEN_JWT_SECRET`
- `SUPERSET_ADMIN_PASSWORD`
- `ANALYTICS_DB_PASSWORD`
- `EMBED_SESSION_SECRET`
- `DEMO_USER_PASSWORD` apenas para a POC

Crie schedules separados quando os horários reais forem confirmados. Cada
schedule pode executar todos os IDs ou chamar o script com `-CustomerIds` para
um grupo específico. O pipeline materializa um snapshot novo; o Superset não
consulta o Blob durante a navegação do usuário.

Na produção Databricks, o schedule do GitLab deve disparar um Databricks Job e
acompanhar sua conclusão. O processamento fica no Databricks Workflows e o
Superset consulta somente a Gold pelo SQL Warehouse.
