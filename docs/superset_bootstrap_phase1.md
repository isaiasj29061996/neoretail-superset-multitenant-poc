# Superset bootstrap modularization — Phase 1

Scope: move shared construction/persistence helpers without changing SQL,
formulas, datasets, chart defaults, layouts, identifiers or public entry points.

## Dependency audit before extraction

All nine `superset/bootstrap_*.py` files were audited.

| Consumer | Provider | Imported symbols before Phase 1 |
| --- | --- | --- |
| overview_quantity | overview | `_jinja_filter_predicates`, `chart_params`, `metric`, `overview_native_filters`, `position_json`, `upsert_chart`, `upsert_dataset` |
| panorama | overview | `HISTORY_SQL`, `M`, `_jinja_filter_predicates`, `metric`, `overview_native_filters`, `upsert_dataset` |
| panorama | overview_quantity | `Q`, `quantity_semantic_sql` |
| osa_industry | overview | `HISTORY_SQL`, `M`, `OVERVIEW_M`, `metric`, `native_filters`, `upsert_dataset` |
| osa_industry | panorama | `Layout`, `custom_params`, `table_params`, `upsert_chart` |
| osa_industry_certified | overview | `_jinja_filter_predicates`, `metric`, `overview_native_filters`, `upsert_dataset` |
| osa_industry_certified | panorama | `Layout`, `WEEKLY_FILTER_COLUMNS`, `comparison_pivot_params`, `custom_params`, `formatted_metric`, `upsert_chart` |
| stock_optimization | overview | `headline_semantic_sql`, `metric`, `upsert_dataset` |
| stock_optimization | panorama | `Layout`, `custom_params`, `upsert_chart` |
| export | overview | `metric`, `upsert_dataset` |
| export | panorama | `Layout`, `upsert_chart` |
| osa_certified_matrices (auxiliary) | overview / panorama | `_jinja_filter_predicates` / `WEEKLY_FILTER_COLUMNS`, `formatted_metric` |

Analytics and Embedded do not import other bootstraps. Analytics owns database
registration and access permissions; Embedded owns embedding and tenant RLS
publication. Neither is moved into this dashboard-helper core.

## Shared helpers extracted

| Core module | Symbols | Why shared |
| --- | --- | --- |
| metrics | `metric`, `formatted_metric` | Build metric descriptors and deterministic option names; receive expressions rather than define business formulas. |
| filters | `_jinja_filter_predicates` | Builds the same dimension IN/NOT IN Jinja predicates for Overview, Quantity, Panorama and OSA; preserves the existing dimension allowlist and alias overrides. |
| metadata | `upsert_dataset` | Common ORM lifecycle for datasets in all dashboard families. |
| metadata | `upsert_overview_chart`, `upsert_chart` | Existing persistence variants shared by Overview/Quantity and Panorama/OSA/Stock/Export respectively. Keep descriptions, lookup behavior and legacy-title migration distinct. |
| chart_params | `chart_params`, `custom_params` | Shared card renderer parameter builders; existing default values stay intact. |
| chart_params | `table_params`, `comparison_pivot_params` | Shared table/pivot renderer contracts used by Panorama and OSA, including individual metric formats. |
| layout | `Layout` | Shared deterministic layout tree builder used by Panorama, OSA, Stock and Export. All existing sizing and ordering defaults remain intact. |

The Overview chart helper is imported as `upsert_chart` at its existing public
locations. Every moved symbol remains available through its previous bootstrap
module for compatibility; in-repository consumers import generic helpers from
core directly.

## Structure and ownership after Phase 1

```text
superset/
  bootstrap_*.py                  # existing executable public entry points
  neoretail_bootstrap/
    __init__.py
    core/
      __init__.py
      metrics.py
      filters.py
      metadata.py
      chart_params.py
      layout.py
```

The domain directories below are Phase 2 destinations, not empty packages
created during Phase 1:

| Area | Current owner / contents retained |
| --- | --- |
| overview | `bootstrap_overview.py`: history SQL, `M`, `OVERVIEW_M`, semantic SQL, native filter definitions, two-row layout preset, dashboard orchestration |
| overview_quantity | `bootstrap_overview_quantity.py`: `Q`, conversion/quantity semantic SQL, orchestration |
| panorama | `bootstrap_panorama.py`: weekly columns, all semantic SQL, metric expressions, controls, chart specifications and orchestration |
| osa | Both OSA bootstraps plus `osa_certified_matrices.py`: cause/period semantics, metric definitions, matrices and orchestration |
| stock_optimization | Its bootstrap: opportunities/tasks SQL, filters, renderer-specific task parameters and orchestration |
| export | Its bootstrap: indicators, export SQL, filters, pivot configuration and orchestration |

Remaining cross-bootstrap imports are explicit domain contracts: Overview
SQL/metrics/native filters/layout preset; Quantity metrics/SQL; Panorama weekly
dimension mapping. Export has no remaining cross-bootstrap import. OSA and
Stock still depend transitively on domain owners; Phase 1 does not claim full
screen isolation.

## Validation and risks

`test_bootstrap_architecture.py` discovers every bootstrap and rejects imports
of generic helpers from another bootstrap, wildcard imports and bare module
imports. Only the explicit domain allowlist above is permitted. Core cannot
import bootstraps or Superset runtime. SQLite-backed tests verify dataset/chart
identity reuse, unchanged metadata fetch behavior and legacy-title migration.

The extraction was checked against the pre-edit sources using AST comparisons:
all moved bodies are identical (except the Overview helper's internal name),
and all other non-import statements in all nine bootstraps and OSA matrices
are unchanged. This includes SQL literals, expressions and `main` functions.

Deployment must supply the new `neoretail_bootstrap` package alongside the
public scripts on the Python path. Existing directory mounts do so without a
Compose change; copying individual scripts alone is no longer sufficient.
No database migration or chart/dataset identifier reassignment is introduced.

Phase 2 should move retained domain contracts into their owning packages first,
preserving public re-exports, then move each screen's orchestration separately.
Assign independent screen packages to developers; serialize changes to core
and certify each migration against existing SQL and persisted metadata.

## Validation results — 2026-10-05

Tests ran in the Local Engine container against an isolated copy of this
working directory, not its `/repo` mount (which points to another worktree).
The pre-existing Overview test's `/repo` preference was redirected only in
the temporary test copy. No project test was weakened to bypass a failure.

```text
python -m pytest 
  local-engine/tests/test_bootstrap_architecture.py
  local-engine/tests/test_panorama_comparison_contracts.py
  local-engine/tests/test_panorama_inventory_tabs_contracts.py
  local-engine/tests/test_panorama_kpi_dimension_contracts.py
  local-engine/tests/test_panorama_sales_contracts.py
  local-engine/tests/test_panorama_stock_contracts.py
  local-engine/tests/test_osa_industry_certified_contracts.py
  local-engine/tests/test_overview_metric_semantics.py
  local-engine/tests/test_local_contracts.py
  -q -p no:cacheprovider
```

Result: **98 passed, 2 failed**. All **13 new architecture/persistence tests
passed**. Both failures were independently reproduced against the original
bootstraps and original tests: **85 passed, 2 failed** before extraction.

* `test_value_and_quantity_dashboard_isolated_from_legacy_page` expects the
  literal spacing `("Valor",[` in the OSA source. The existing source uses
  different whitespace. Neither the OSA layout nor that test was changed.
* `test_v9_customer_registry_and_embedded_rls` expects a dashboard catalog
  without `osa_certified`, which the existing tenant configuration includes.
  Neither the tenant configuration nor that test was changed.

Three existing Panorama tests were updated solely to inspect helper
definitions in core instead of their previous bootstrap file locations.
`git diff --check` passed for the Phase 1 files. The unrelated pre-existing
whitespace change in `embedded-app/server.js` was preserved.

Runtime validation used the installed Superset application and actual
metadata database. The following eight entry points ran with the original
sources, then the refactored sources, then the refactored sources again:
Overview, Overview Quantity, Panorama, legacy OSA, certified OSA, Stock
Optimization, Export and Embedded. Session commits were replaced by flushes
in the validation harness and the transaction was rolled back in `finally`.
Real metadata fetching and Analytics read queries were executed.

All three snapshots matched for dataset SQL/schema/database/columns/metrics,
chart parameters/descriptions/datasource/viz type, dashboard layouts/CSS/native
filters/chart associations, embedding, existing IDs and UUIDs. Panorama
retained its 36 charts. This verifies equivalence and metadata idempotency
for the populated environment; it is not a fresh-database or visual UI test.
Analytics was audited and verified unchanged by AST, but was not executed
because its main function performs Analytics schema DDL outside the metadata
transaction. No frontend, Compose or tenant configuration was edited.

Temporary audit scripts and original-source snapshots reside under the
Git-ignored `generated/` directory. No files were staged; no commit, push or
merge was performed.

## Pre-PR audit — branch, tests and image packaging

This audit did not create a branch/worktree, transport changes, commit, push
or merge. Only the remote reference was fetched and this report was extended.

### Base and proposed transport (not executed)

The remote was checked directly and fetched on 2026-10-05. The latest
`origin/feat/osa-industry-certification` is `1d8127a0c3d45de049e7afbbb3072781adde63c3`,
the merge of PR #12. Current `HEAD` is `41bd81e23da8a77e5cda2ae7ef4200e177ddc367`.
HEAD is an ancestor of that base, and both tree hashes are
`cc3dbaecd82d050d2673a17c758fa59956396580`: tracked committed content is identical.

Safest transport procedure, after authorization:

1. Refresh the remote again, record the chosen base hash and verify the new
   branch/worktree path does not exist. If the base advances, review its diff
   before applying the refactor.
2. Back up the 20 explicitly allowed files listed below, plus an independent
   backup/hash of the pre-existing `embedded-app/server.js` change. Export a
   binary patch using `git diff --binary --output=<backup>/phase1.patch HEAD --`
   followed by the 11 tracked Phase 1 paths. Git's `--output` avoids PowerShell
   redirection encoding problems. Capture the nine new files separately;
   ordinary `git diff` does not include them.
3. Create an isolated worktree at `.worktrees/superset-bootstrap-core`, with
   branch `refactor/superset-bootstrap-core` based on the recorded remote
   commit. Do not switch/reset/stash the dirty source worktree. Do not carry
   the old branch's commit history or cherry-pick its bug-fix commit.
4. Run `git apply --check` against the new worktree before applying the patch.
   Copy only the nine explicit new-file paths, not the whole repository or
   the whole Superset directory. Exclude caches and `generated/` artifacts.
5. Compare the target manifest against these 20 files, confirm `server.js` has
   zero diff against the new base, and confirm its source backup/hash still
   matches. Verify the source worktree was left intact.
6. Re-run architecture, Panorama, Overview and OSA contracts plus metadata
   parity/idempotency validation. Report known baseline failures explicitly.
   Leave all changes unstaged; commit/push/merge require a later instruction.

Using a whole-worktree stash or whole-directory copy would risk carrying the
unrelated frontend change. No transport has been performed during this audit.

### Panorama test changes

* Comparison: six existing literal assertions now inspect `core/chart_params.py`
  where the pivot/default parameter builders live. Expected pivot type,
  ordering, row limit and individual formats are unchanged. Metric expressions,
  hierarchy/tab assertions and obsolete-ranking guards remain in Panorama.
* Inventory: the AST loader's path for `_jinja_filter_predicates` changed from
  Overview to `core/filters.py`. This is the only modification to that file.
* Sales: the source path for the `remove_filter=True` assertion changed from
  Overview to `core/filters.py`. This is the only modification to that file.

The test names and assertion counts are unchanged: Comparison 9 tests / 74
assertions; Inventory 13 test functions / 68 assertions; Sales 8 tests / 40
assertions. Parameter expansion gives 33 executed cases, all passing in the
isolated Local Engine test copy during this audit. No tests/assertions were
removed, skipped, disabled or relaxed.

The Inventory test bodies, decorators and cases are identical to HEAD.
Explicit cases remain `uf IN RJ`, `uf NOT IN RJ`, `item IN item-test` and
`item NOT IN item-test`. They render actual Jinja SQL, require the weekly
source `gold.nr_panorama_inventory_weekly_detail w`, require `w.<dimension>`
in its predicates, require the governed monthly source with alias `f`, and
reject invalid `l`, `i`, `h` references in the rendered SQL. The additional
13-dimension × IN/NOT IN loop still rejects `l`, `i`, `h`, `f` in the weekly
fragment and verifies the monthly predicates.

### Packaging diagnosis and future change (not implemented)

`docker-compose.yml` builds from `./superset`. Both `superset-init` and
`superset` bind-mount `./superset:/app/pythonpath:ro`, hiding image contents at
that destination. The current running container's mount is specifically
`.worktrees/osa-industry/superset`, not this dirty source worktree.

The final Dockerfile stage copies only `superset_config.py`,
`neoretail_publication.py`, `smoke_publication.py`, `bootstrap_analytics.py` and
`init.sh` to `/app/pythonpath`. It copies compiled frontend assets separately.
Neither the other dashboard bootstraps nor `osa_certified_matrices.py` nor
`neoretail_bootstrap/` is copied into the image. No root or Superset
`.dockerignore` currently exists.

The actual running image was inspected using a temporary container with no
volumes, no network and a read-only filesystem. Its `/app/pythonpath` contains
exactly those five files; `bootstrap_panorama.py` and `neoretail_bootstrap/`
are absent. `PYTHONPATH=/app/pythonpath` and that directory is on `sys.path`
both with and without the bind mount, inherited from the Superset base image.
The problem is missing packaged files, not Python import-path configuration.

`init.sh` executes only Analytics. `run-ambev-35-full.ps1` and
`run-osa-certified.ps1` execute dashboard scripts via `docker compose exec`
at `/app/pythonpath`; they do not copy code into the container. `validate.ps1`
builds the image but does not check bootstrap/package imports without mounts.

For the requested standalone-image capability, the minimal future Dockerfile
addition, after its existing Python COPY and before `USER superset`, is:

```dockerfile
COPY bootstrap_*.py osa_certified_matrices.py /app/pythonpath/
COPY neoretail_bootstrap/ /app/pythonpath/neoretail_bootstrap/
```

For validator/profiler scripts to work without mounts as well, package those
top-level Python files explicitly, or replace the existing Python COPY with
`COPY *.py init.sh /app/pythonpath/` while retaining the separate package COPY.
Keep the new package inside the `./superset` build context. The verified base
image already supplies PYTHONPATH; no Compose edit is required for packaging.
Validate a rebuilt image without volumes by importing the core and all public
bootstrap modules, without invoking `main` or connecting to databases. Runtime
tenant configuration, secrets and database services remain separate deployment
inputs; this packaging change concerns application code only.

The current Phase 1 therefore works when the complete source directory is
supplied, but standalone-image packaging is not yet satisfied. Dockerfile,
Compose, deployment scripts and functional code were not edited in this audit.

### Exact Phase 1 manifest

Tracked modifications (11):

```text
local-engine/tests/test_panorama_comparison_contracts.py
local-engine/tests/test_panorama_inventory_tabs_contracts.py
local-engine/tests/test_panorama_sales_contracts.py
superset/bootstrap_export.py
superset/bootstrap_osa_industry.py
superset/bootstrap_osa_industry_certified.py
superset/bootstrap_overview.py
superset/bootstrap_overview_quantity.py
superset/bootstrap_panorama.py
superset/bootstrap_stock_optimization.py
superset/osa_certified_matrices.py
```

New files (9):

```text
docs/superset_bootstrap_phase1.md
local-engine/tests/test_bootstrap_architecture.py
superset/neoretail_bootstrap/__init__.py
superset/neoretail_bootstrap/core/__init__.py
superset/neoretail_bootstrap/core/chart_params.py
superset/neoretail_bootstrap/core/filters.py
superset/neoretail_bootstrap/core/layout.py
superset/neoretail_bootstrap/core/metadata.py
superset/neoretail_bootstrap/core/metrics.py
```

Excluded: the pre-existing `embedded-app/server.js` whitespace change; all
Git-ignored `generated/` snapshots, archives and audit/validation scripts;
Python caches. Other files, including Dockerfile, Compose and tenant configs,
have no Phase 1 changes to transport.
