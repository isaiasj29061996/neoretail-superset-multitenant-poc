# Runtime origin and additional OSA objects — read-only reconciliation

Observed 2026-10-06. No container recreation, database write, mart refresh or object deletion was performed.

## Exact bind mounts

R = C:\Users\ijusto\Downloads\NeoRetail_V8_1_LOCAL_POSTGRES_POWERQUERY_COMPLETO\NeoRetail_V8_1_LOCAL_POSTGRES

O = R\.worktrees\osa-industry

| Running container | Source | Destination |
|---|---|---|
| neoretail-v9-multitenant-superset-1 | O\config | /app/config |
| same | O\superset | /app/pythonpath |
| same | O\certs | /certs |
| same | O\generated | /generated |
| neoretail-v9-multitenant-local-engine-1 | O | /repo |
| same | O\config | /workspace/config |
| same | O\local-engine | /workspace/local-engine |
| same | O\generated | /workspace/generated |
| same | O\certs | /certs |
| neoretail-v9-multitenant-embedded-app-1 | R\config | /app/config |
| same | R\generated | /app/generated |

Named database/lake volumes are separate from these source mounts and must be retained.

## Cause and smallest safe alignment

The Docker labels prove Superset/Local Engine were created from O/docker-compose.yml, with project.working_dir=O. Embedded was created from R/docker-compose.yml plus R/docker-compose.assistant.yml, with project.working_dir=R. Both launches used the same project name neoretail-v9-multitenant, allowing services recreated separately from different directories to coexist in one project.

The integrated Compose already uses relative source paths. No Compose edit is required to make its services resolve one origin; the operational problem is the launch directory/config-file set and previously built images.

Recommended separate deployment:

1. Choose a clean, reviewed integrated worktree and record its HEAD and source hashes. Do not deploy the current uncommitted implementation as an integrated release.
2. Inventory the old dirty OSA changes, including its untracked performance SQL and bootstrap consumers. Preserve them separately for review; do not copy them into this PR.
3. Use one explicit --project-directory and one coherent -f file set, all from that worktree, plus the approved existing external env/cert locations. Do not print or commit secrets.
4. Use the existing project/volume identities; do not run down -v, reset-ambev-local-data.ps1 or remove database/lake volumes.
5. Build Embedded from that root (its server/bundle are image content), and rebuild Superset/Local Engine if packaged content/dependencies differ. Recreate, rather than merely restart, source-mounted services so mount origins change.
6. Recreate Superset and Local Engine, rebuild/recreate Embedded. Align the superset-init definition too; running it must be separately controlled because it can mutate metadata. Do not rerun all initialization just to prove source provenance.
7. Keep generated publication metadata and certificates under explicit approved paths; reconcile the two current generated catalogs before replacing either.
8. Validate health, source identity and regression, then do the UI check.

No runtime correction was applied here: the active OSA worktree has uncommitted implementation changes and consumers of the four additional objects. Blindly switching its mounts could replace that implementation. This exceeds identity-only PR 1.

## Proposed proof of one version

Acceptance must verify bytes as well as HEAD; a dirty checkout can report the same commit while executing changed files.

- Before deployment: clean git status, expected integrated HEAD, manifest of SHA-256 values for canonical config, Python package/entrypoint, Superset bootstraps/domain modules and Embedded server/resolver/bundle.
- docker inspect: all compose working_dir/config_files/build contexts and bind sources match the approved root or explicitly approved external operational paths.
- Local Engine: compare git -C /repo rev-parse HEAD plus hashes of the actually imported module __file__ paths.
- Superset: compare hashes under /app/pythonpath and /app/config; verify PYTHONPATH/import locations.
- Embedded: compare /app/server.js and /app/tenant-registry.js hashes with that build's source manifest, and bundled frontend hash with the build artifact. HEAD cannot be inferred from a config mount because backend code is inside the image.
- Compare customers.yaml bytes in all three services.
- Exercise session/catalog/guest-token context and required dashboard queries after deployment.

A commit label alone or docker compose restart alone is insufficient proof.

## Additional OSA object provenance

Concrete local origin found:

- O/analytics-db/marts/45_osa_certified_semantic.sql is untracked and declares the four marts.
- O/run-osa-certified.ps1 has an uncommitted call to create-superset-kpi-views.ps1 -Only 45_osa_certified_semantic.sql.
- O/superset/bootstrap_osa_industry_certified.py has uncommitted compact monthly, weekly and causes consumers.
- O/superset/osa_certified_matrices.py has an uncommitted compact matrix consumer.
- O/superset/validate_osa_industry_certified.py has uncommitted assertions for all four optimized paths.

This is a local performance experiment, absent from the integrated 6257e49 tree, rather than an established generated object of the integrated product. The matching local DDL/call chain establishes a plausible and concrete provenance; the database has no DDL history proving who executed that file or when.

## Current database definitions, dependencies and consumers

The reconstructed current DDL and all four indexes are captured in osa_additional_objects_ddl_audit.sql. That file is an audit snapshot only, not a migration to execute.

| Materialized view (gold) | Current direct Gold dependencies | Populated |
|---|---|---|
| nr_osa_monthly_default | dim_conversao, fato_historico, fato_mensal_causa_osa, nr_conversion_options | yes |
| nr_osa_weekly_default | calculo_oportunidades, dim_conversao, fato_semanal, nr_conversion_options | yes |
| nr_osa_causes_default | dim_conversao, fato_mensal_causa_osa, nr_conversion_options | yes |
| nr_osa_matrix_default | dim_conversao, dim_itens, dim_local, fato_historico, fato_mensal_causa_osa, nr_conversion_options | yes |

Read-only PostgreSQL catalog checks found zero dependent views/materialized views. Superset metadata checks found zero datasets whose physical name or stored SQL references these four objects, and consequently zero charts reached through those matching datasets. This does not rule out ad-hoc SQL, external consumers or future execution of the dirty bootstrap.

PostgreSQL's standard catalogs do not provide reliable creation/modification timestamps for these objects. No DDL audit history was available in this investigation; filesystem edit timestamps would not prove database creation. Dates remain unknown.

## Recommended disposition

Preserve all four objects now. They are not part of the integrated version's required object generation, but local mounted source still contains consumers.

Decide separately:

- If the performance experiment is retained: certify it against the integrated semantics, including filtered fallback, period controls, conversion factors, JWT and metadata idempotency; then version its generators and consumers together in a dedicated PR.
- If it is retired: first align runtime/remove every consumer and prove non-use; only then consider a separate reviewed cleanup with backup/rollback.

No DROP, restore of the untracked SQL into product code, or mart regeneration is authorized by this reconciliation itself.
