# Multi-tenant fast-track — execution evidence

## Review state

Work in progress; no commit, push, PR or merge. The original repository and the
earlier TenantContext worktree are preserved. This report is updated as each gate
completes; an authorized context is not proof of a loaded tenant.

Base: `origin/feat/osa-industry-certification`,
`6257e491242d265b9c742633580dcf928416f8be` (integrated PR #16).
Branch/worktree: `feat/multitenant-fasttrack`, `.worktrees/multitenant-fasttrack`.

## Architecture and safeguards

- `config/customers.yaml` is the canonical identity/source registry; user grants
  remain separate in `config/tenants.yaml`.
- Python and Node resolve the same validated TenantContext. Physical schemas
  come from the registry, never from arbitrary request text.
- Gold publication aligns named columns, rejects null/foreign/fractional IDs, enforces
  database identity constraints and rolls back failed promotions. Staging cleanup
  also covers failed JDBC writes. Gold lake writes require canonical tenant scope
  and reject invalid identities before overwriting a partition. No global tenant
  deletion is performed.
- The original versioned SQL is tokenized and only qualified relation identifiers
  are redirected. Comments, literals, Jinja, formulas, aliases, joins, conversion
  rules and windows are retained. Mart rebuilds run in one transaction and restore
  existing serving views in that transaction; failure rolls back both.
- Shared `serving` views use explicit columns and `UNION ALL`, strict column/type
  equivalence and identity checks across all participating tenant relations.
  Partial refresh uses `--keep-published-tenants`, retaining existing registered
  sources in the same publication transaction. Unknown/legacy dependencies fail
  closed rather than silently removing another published tenant.
- Dataset source migration is an administrative operation, not a tenant-switch
  operation. Dataset IDs/UUIDs and dashboard/chart identities remain shared.
- Source-only SQL migration preserves certified column metadata without expensive
  re-reflection. Actual formula changes still require normal metadata reflection.
- One necessary RLS adaptation: Export indicator options now project customer
  identity from the shared customer source. The nine original labels, formulas,
  dataset ID/UUID, existing column/metric IDs and native-filter targets remain
  unchanged. The only added metadata column is `id_customer` in
  `nr_export_indicators`. The original static list failed real Guest RLS with
  `column id_customer does not exist`; no RLS exemption was introduced.
- AMBEV 142 is excluded from DEV grants and automatic execution. Its local data
  was initially preserved, then removed only after the user explicitly approved
  the exact cleanup scope. Code, Git history, fixtures, Azure source, audit rows
  and shared volumes remain preserved. The four old OSA objects were included
  in that approved local cleanup and are not new runtime sources.
- Guest tests call Superset's permission validation with actual signed tokens and
  chart/native-filter context. Native filter defaults are applied by chart scope,
  not by the options datasource ID. The old profiler's injected 142 filter is
  removed from test queries; tenant isolation comes from JWT RLS.

## Runtime

All three services use this worktree through `docker-compose.fasttrack.yml` and
the regular Compose file. The original root `.env` is referenced explicitly;
credentials are not copied to this worktree or committed. Existing database/Redis
volumes are retained. The Embedded image is built from this worktree; Engine and
Superset Python imports/mounts are verified by hashes.

```powershell
docker compose --project-directory <fasttrack-worktree> --env-file <original-root>/.env -f <fasttrack-worktree>/docker-compose.yml -f <fasttrack-worktree>/docker-compose.fasttrack.yml up -d --no-deps --no-build local-engine superset embedded-app
python scripts/validate_fasttrack_runtime.py
```

`generated/fasttrack_runtime_manifest.json` records image IDs, bind sources,
effective Python import paths and hashes. Generated evidence is ignored by Git;
it does not contain credentials or JWTs. Linux shell line endings are enforced by
`.gitattributes`. Spark uses `local[2]` and a 1 GB driver. Tenants are sequential.

## Tenant gates

### PANDURATA 17066 — passed initial gate

Actual prefix: `FATO/CUSTOMER/DAILY/NM_CUSTOMER=PANDURATA`.
Layout: `partitioned_customer_daily_v1`; 40 files, 759,499,313 source bytes.
Full load: 46,908,758 rows, 2024-10-01 through 2026-10-05, only ID 17066.
All 40 cached-source footers confirm those same rows/dates and 759,499,313 bytes;
loaded ETags are recorded in `generated/fasttrack_loaded_source_17066.json`.
Pipeline, lake identity checks, Gold, versioned marts and 55 serving relations
passed. Real Guest gate: 91 chart checks across 8 dashboards, 114 native-filter
checks, 32 UF/Item IN/NOT IN inventory checks, 43 identity probes, 172 negative
token queries and 2 warmed-cache checks. Tampered signatures were rejected.

### LACTALIS 290 - passed complete gate

Actual prefix: `FATO/CUSTOMER/DAILY/NM_CUSTOMER=LACTALIS`.
Layout: `partitioned_customer_daily_v1`; 172 files, 2,266,219,618 source bytes.
The corporate dimension confirms `290 = LACTALIS`; all six configured dimensions
are available. Full Bronze load and read-only audit passed: 115,518,964 records,
only ID 290, no null identity, no empty/unclassified source files. Full Silver
date range: 2024-05-01 through 2026-10-05. Steps 03A through 08 completed,
including 20 validation checks and Gold publication. Versioned marts committed;
Full read-only identity audit passed: 34 lake tables and 55 SQL relations, only
ID 290. Serving publication passed for 17066 and 290 across 55 equivalent
column/type contracts. The combined actual Embedded-issued Guest gate passed.
Across both tenants: 182 populated chart queries, 456 native-filter checks,
64 inventory UF/Item IN/NOT IN checks, 12 OSA period checks, 172 identity/isolation
checks, 258 denied-token queries and four actual warmed-cache hits. All chart
queries were nonempty; tenant cache keys are disjoint. Tokens were renewed 64
times; the final cache/context loop retained still-valid tokens, and a modified
signature was rejected. Evidence: `generated/fasttrack_guest_17066_290.json`.

The first mart transaction failed at the final detail script after 2,385 seconds:
PostgreSQL 16.15/alpine logged SIGSEGV (signal 11), then recovered automatically.
The container was not OOM-killed. Read-only post-recovery checks confirmed rollback
to the 13 previously committed LACTALIS Gold relations and preservation of all
55 PANDURATA relations and its 55 serving views (none referencing LACTALIS).
The failed logs/checkpoint are retained under `generated/fasttrack_lactalis_sigsegv_*`.
The retry disables JIT only within the mart transaction; no versioned SQL,
formula, global database setting or source data changes. A disposable PostgreSQL
rollback/idempotence probe passed again after this execution setting change.
JIT is an unconfirmed failure hypothesis, not a proven PostgreSQL root cause.
The retry committed successfully after 2,400.4 seconds with JIT disabled.

A later full remote footer audit reports 115,505,884 rows, the same date range,
172 files and two historical schema variants. All remote ETags changed since
loading. A read-only audit of the cached Parquets confirms exactly the loaded
115,518,964 rows and original 2,266,219,618 bytes. This is an intact loaded source
snapshot, not a claim to reflect the later source rewrite. Its version manifest
is retained in `generated/fasttrack_lactalis_source_versions.json`. Future source
preflight binds footer reads to ETags; downloads bind content to the inspected
ETag, preserve the previous cache on failure and clean only their own partials.

### SAFIRA 16868 - pipeline/identity/serving passed; final Guest pending

Actual prefix: `FATO/CUSTOMER/DAILY/NM_CUSTOMER=SAFIRA`.
Layout: `partitioned_customer_daily_v1`; 26 files, 90,741,514 bytes and
7,305,944 records across 2024-09-01 through 2026-10-03, verified from all
Parquet footers with ETag-bound reads. No empty files, one schema variant.
All six dimensions are available; corporate identity confirms `16868 = SAFIRA`.
Source and execution were enabled only after the combined PANDURATA/LACTALIS
Guest gate passed. The complete (1.0 fraction) load passed: 7,305,944 rows,
only ID 16868 and no null identities. Steps 03A-08 passed; marts committed in
172.5 seconds. Read-only identity audit passed across 34 lake tables and 55 SQL
relations. Shared serving publication passed for all three tenants, 55 views
with identical column/type contracts. The final three-tenant Guest gate was interrupted for disk pressure; it has not passed.
The size-based SQL footprint estimate is about 3.24 GiB before lake and temporary
query overhead; it is an estimate, and host free capacity is monitored throughout.
Evidence: `generated/fasttrack_source_16868.json`, `generated/fasttrack_capacity.json`.
The loaded cache matches all 26 preflight ETags, row count and date range:
`generated/fasttrack_loaded_source_16868.json`.

## Tests and metadata

- Node/Assistant: 47 passed, zero skipped, including live Python/Node parity.
- Embedded runtime: context 17066 → 290 → 16868 → 17066, actual Guest issuance,
  body tampering ignored, five invalid contexts and unknown dashboard rejected.
- Spark Power Query parity reexecuted: 5 passed in 50.39 seconds.
- Disposable PostgreSQL publisher probe: passed named-column reorder, identity
  guards, null constraints, staging cleanup and failed-promotion rollback.
- Disposable mart probe: passed serving restoration, repeat execution and induced
  failure rollback without changing another tenant's sentinel data. The latest
  mart probe also passed selected-tenant retention and rejection of unknown
  serving dependencies (1 passed, 1.64 seconds). Probe
  containers were removed; production POC databases were not used for those tests.
- Architecture/fast-track after canonical Export dependency correction: 25 passed.
- Full contract suite after source snapshot and Gold safeguards: 559 passed, exactly two preexisting
  failures (seven-vs-eight dashboard assertion and old textual OSA layout
  assertion), in the final 39.02-second run. Neither is relaxed. Node/Assistant was also
  reexecuted: 47 passed, zero skipped. Final tenant configuration will be
  rechecked if it changes after the last gate.
- Metadata comparison passed: 8 dashboards, 102 registered charts (91 linked to
  dashboards), 59 datasets. Native defaults unchanged. Second source migration
  reported `changed: []`; exact post-migration metadata comparison passed.
  The read-only comparison also passed again after PostgreSQL crash recovery.
  After the AMBEV cleanup, full baseline and exact idempotence comparisons also
  passed (`generated/fasttrack_metadata_post_cleanup.log`).
  Final source migration again returned `changed: []`; the full original-baseline
  comparison and exact second snapshot passed (no native defaults changed).

Preserved dashboard catalog (91 distinct linked charts):

| Dashboard ID | Area | Charts |
| --- | --- | --- |
| 1 | Overview | 8 |
| 2 | Panorama | 36 |
| 3 | OSA original | 7 |
| 4 | Stock Optimization | 10 |
| 5 | Overview Quantity | 8 |
| 6 | Export daily | 4 |
| 7 | Export monthly | 4 |
| 8 | OSA Certified | 14 |

Evidence commands:

```text
python -m neoretail_local.tenant_source_audit --tenant <key>
python -m neoretail_local.candidates --customer <key> --sample-fraction 1.0
python scripts/run_fasttrack_tenant.py --tenant <key>
python -m neoretail_local.tenant_audit --tenant <key>
python -m neoretail_local.marts --tenant <key> --serving-tenants <published keys>
python scripts/validate_fasttrack_gates.py --tenants <published IDs>
```

## Limits and remaining gates

Cross-tenant positive/negative tests with actual PANDURATA and LACTALIS data
passed. SAFIRA source/load passed; the final three-tenant Guest gate is pending. DEV
context authorization alone does not complete SAFIRA's data gate. No Power
BI numeric homologation or new visual approval is claimed by these query tests.
The integrated browser inventory returned no enabled apps or browsers in this
session. Automated Guest queries therefore do not replace final manual visual
inspection of the Embedded dashboards.
The complete isolation matrix, final file list, diff statistics and Git status
will be recorded after execution. Resource limits are monitored without deleting
historical AMBEV data.

## Capacity checkpoint

During combined Guest validation, Windows C: free capacity fell to about
13.3 GiB; later readings were about 14.1 GiB. PostgreSQL temporary query spills
and the Docker virtual disk must be considered before another full load. An
online `fstrim` of the PostgreSQL volume reported 45,848,989,696 bytes of
already-free filesystem blocks, with no files, tables or volumes removed.
Windows did not immediately recover that physical capacity; this is not proof
that another full tenant fits. Evidence: `generated/fasttrack_disk_reclaim.json`.
At that capacity checkpoint AMBEV data and tenant checkpoints were preserved.
The subsequently approved AMBEV cleanup is documented below.
After LACTALIS passed, SAFIRA source/capacity checks supported a sequential load.
A later host reading showed 23.8 GiB free before the approved AMBEV cleanup.
Monitoring continues, and the full three-tenant validation is still required.

## Explicitly authorized AMBEV local cleanup

The user subsequently requested removal of AMBEV to reclaim resources, then
explicitly approved the exact irreversible local scope while preserving audit.
An initial broader action including audit deletion was rejected by automatic
approval review; that action was never executed. The approved execution retained
all audit records and removed only:

- 59 relations in legacy `gold`, after null/foreign identity and external
  dependency checks; all were ID 142 or empty. The four old OSA objects belong
  to this removed legacy scope.
- 35 exact `/data/lake/{bronze,silver,gold}/<table>/id_customer=142` or AMBEV
  raw-cache paths, after Parquet identity and absolute-path/symlink checks.

Inventory: 44,254,937,088 SQL bytes plus 5,956,509,617 lake/cache bytes
(about 46.8 GiB total). No volumes, Superset metadata, Azure files, repository
files, Git history, fixtures or other tenant data were removed. No reset script
was run. Post-check found 55 relations each in `gold_pandurata`, `gold_lactalis`,
`gold_safira` and `serving`, with no remaining legacy Gold relations.

Evidence: `generated/ambev_cleanup_inventory.json`,
`generated/ambev_cleanup_removed.json`, `generated/ambev_cleanup.log`.
Post-cleanup trim reported 54,453,698,560 already-free bytes; Windows C: remained
at about 23.94 GiB free immediately afterward. Windows RAM measured 27.03 GiB
used out of 31.69 GiB, 4.67 GiB available (85%); this snapshot is not a claim
that deletion alone explains RAM changes. Evidence:
`generated/ambev_cleanup_trim.json`, `generated/ambev_cleanup_memory.json`.

## Working-tree file inventory

Current status files (including two shell files affected only by LF normalization;
no staging or commits):

```text
.gitattributes
config/customers.yaml
config/tenants.yaml
docker-compose.fasttrack.yml
docs/multitenant_fasttrack.md
docs/multitenant_runtime_osa_reconciliation.md
docs/multitenant_tenant_context_pr1.md
docs/osa_additional_objects_ddl_audit.sql
embedded-app/Dockerfile
embedded-app/package.json
embedded-app/server.js
embedded-app/smoke.mjs
embedded-app/tenant-registry.js
embedded-app/tests/fasttrack-runtime.mjs
embedded-app/tests/tenant-registry.test.js
local-engine/entrypoint.sh
local-engine/neoretail_local/candidates.py
local-engine/neoretail_local/customers.py
local-engine/neoretail_local/gold_serving.py
local-engine/neoretail_local/marts.py
local-engine/neoretail_local/partitioned_daily.py
local-engine/neoretail_local/partitioned_validation.py
local-engine/neoretail_local/pipeline.py
local-engine/neoretail_local/postgres_serving.py
local-engine/neoretail_local/settings.py
local-engine/neoretail_local/tenant_audit.py
local-engine/neoretail_local/tenant_source_audit.py
local-engine/tests/fixtures/tenant_context_baseline_authorization.yaml
local-engine/tests/fixtures/tenant_context_pending_registry.yaml
local-engine/tests/test_bootstrap_architecture.py
local-engine/tests/test_local_contracts.py
local-engine/tests/test_multitenant_fasttrack.py
local-engine/tests/test_power_query_runtime.py
local-engine/tests/test_tenant_context.py
local-engine/tests/test_tenant_marts_integration.py
local-engine/tests/test_tenant_publisher_integration.py
local-engine/tests/test_tenant_source_metadata.py
run-local-pipeline.ps1
run-multitenant-refresh.ps1
scripts/run_fasttrack_tenant.py
scripts/validate_fasttrack_gates.py
scripts/validate_fasttrack_node.py
scripts/validate_fasttrack_runtime.py
scripts/validate_project.py
superset/bootstrap_export.py
superset/bootstrap_overview.py
superset/bootstrap_panorama.py
superset/bootstrap_serving.py
superset/bootstrap_stock_optimization.py
superset/init.sh
superset/neoretail_bootstrap/core/metadata.py
superset/neoretail_bootstrap/core/sql_sources.py
superset/neoretail_bootstrap/export/__init__.py
superset/neoretail_bootstrap/export/options.py
superset/neoretail_bootstrap/serving/__init__.py
superset/neoretail_bootstrap/serving/metadata.py
superset/validate_fasttrack_guest.py
superset/validate_fasttrack_metadata.py
```


## Latest storage intervention (2026-10-06)

The user prioritized recovering host disk capacity after Windows C: fell below
5 GiB. The three-tenant Guest run was explicitly interrupted; its log is retained
as `generated/fasttrack_guest_17066_290_16868_interrupted_for_disk.log`.
233 charts had completed (91 PANDURATA, 91 LACTALIS, 51 SAFIRA), with no empty
chart. This partial run is not a completed Guest/isolation/cache gate.

Docker containers were gracefully stopped and the filesystem trimmed. Offline
VHD compaction reached Windows UAC but could not proceed: administrator
credentials are unavailable. No VHD compaction or additional tenant-data deletion
occurred. Docker was restarted; all seven running containers are healthy, the
actual runtime proof passed, and each of the three tenant Gold schemas plus
serving still contains 55 relations. The interruption and administrator barrier
are operational limits, not a claim of a functional regression.

At the user's request, reproducible unused resources were removed: all Docker
build cache (Docker reported 31.75 GB), 12 explicitly inventoried images not used
by any container, 168.6 MB pip download cache and an old 244.4 MB VS Code temp
installer. Only old, unlocked cache files under four explicit Chrome/Edge/VS Code
cache roots were additionally targeted; recent and locked files were retained.
Volumes, all remaining tenant data, audit, source code, Git, original worktrees,
user documents, browser cookies/history and crash diagnostics were preserved.
Docker frees its internal blocks; large physical host reclamation still needs
administrator-assisted VHD compaction. Final cleanup figures are recorded in
`generated/storage_cleanup_summary.json` and
`generated/windows_old_cache_cleanup.json`. The heavy final three-tenant gate
remains pending sufficient host capacity; it was not restarted into disk pressure.
