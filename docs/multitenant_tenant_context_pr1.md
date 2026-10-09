# PR 1 — Canonical tenant registry and TenantContext

Historical report of the isolated TenantContext implementation reused by the
fast-track. Its pending-source/runtime statements describe that earlier snapshot,
not the current `feat/multitenant-fasttrack` execution. See
`multitenant_fasttrack.md` for the current source evidence and gates.

## Base and scope

- Base: origin/feat/osa-industry-certification, 6257e491242d265b9c742633580dcf928416f8be.
- Branch: feat/multitenant-tenant-context.
- Separate worktree: .worktrees/multitenant-tenant-context.
- No commit, push, merge, deployment, pipeline load, schema creation or data deletion.
- The original worktree, including its previous embedded-app/server.js changes, was not modified or copied.
- Approved future architecture: Gold per tenant with id_customer, provisional shared consumption schema serving, shared dashboards and mandatory Guest Token/RLS.
- Those physical changes are NOT implemented in this PR.

## Canonical identity

config/customers.yaml is the only customer identity list. Its existing list format/version 9.0 is preserved to avoid an unnecessary format migration.

| key | id_customer | name | future Gold schema | execution_active | source |
|---|---:|---|---|---|---|
| ambev | 142 | AMBEV | gold_ambev | false | Existing verified-code baseline prefix/layout preserved |
| pandurata | 17066 | PANDURATA | gold_pandurata | true | prefix/layout null, pending source evidence |
| lactalis | 290 | LACTALIS | gold_lactalis | false | prefix/layout null, pending source evidence |
| safira | 16868 | SAFIRA | gold_safira | false | prefix/layout null, pending source evidence |

The new names/IDs come from the approved request; they have NOT been verified against Azure DIM_CUSTOMER in this implementation. No prefix/layout was inferred from the AMBEV naming convention.

The manual default remains 142 for baseline compatibility. Automatic refresh uses execution_active, not that default.

## TenantContext contract

Python: neoretail_local.customers.TenantContext, frozen dataclass:

- tenant_key, id_customer, nm_customer, display_name, gold_schema;
- source_prefix and source_layout, nullable until evidenced;
- execution_active, enabled;
- derived partition and source_ready.

Customer remains an alias for existing internal imports; resolve_customer remains an alias for resolve_tenant. Existing internal consumers use the resolver rather than constructing Customer directly. Modules are deliberately excluded from identity.

Node: embedded-app/tenant-registry.js returns the same serialized context fields. The two small language adapters share the canonical YAML and have an executed Python/Node parity test; no separate tenant service or generated identity copy is introduced.

Registry validation rejects duplicate YAML keys and duplicate tenant keys, IDs, normalized names and Gold schemas. It rejects ambiguous key/name selectors, unsafe physical identifiers, non-positive/non-safe IDs, invalid boolean flags and invalid source placeholders/paths. Physical identifiers use lower-case [a-z][a-z0-9_]{0,62}.

An existing inactive tenant can be resolved for an explicit baseline operation. Automatic execution additionally requires execution_active and complete source configuration. enabled=false retains its distinct unavailable-tenant semantics.

Resolution without source readiness is allowed for identity/authorization. Settings.from_env requires source readiness before Azure credentials, schema setup, Spark or publishing can occur.

## Authorization and integration

config/tenants.yaml keeps dashboard/navigation definitions, default UI selection, user allowed_customer_ids and customer_access keyed by canonical tenant key. It no longer repeats customer names or a second identity list.

The current user still has only [142]. AMBEV retains exactly the four product modules it had. Registering or activating PANDURATA does not grant that user permission or make a new UI selection available.

Embedded reads customers.yaml beside TENANTS_CONFIG, overridable by CUSTOMERS_CONFIG_PATH, and joins identity with customer_access at startup. It rejects an old second customers identity catalog and references to unknown tenants. availableCustomers, session fields, /api/context, dashboard checks and Guest RLS clause remain unchanged.

Pipeline Settings exposes tenant_context and separately resolves customer_modules from tenants.yaml. The quality gate reads those same existing entitlements; its empty-catalog rule/formula is not changed.

Pipeline --customer and --tenant resolve key, ID or corporate name through the same resolver. run-local-pipeline.ps1 -Customer 17066 reaches that resolution and stops on pending source metadata. Its AMBEV-specific dispatch is left for the pipeline PR.

Automatic run-multitenant-refresh.ps1 no longer defaults to [142]. It preflights --active --require-source before the loop. Today this intentionally fails for pending PANDURATA and starts no refresh. Explicit -CustomerIds 142 remains a manual baseline operation.

Example identity-only operation (no Spark/database):

    python -m neoretail_local.customers --config config/customers.yaml --tenant pandurata

Required-source and automatic probes intentionally fail until origin evidence is supplied:

    python -m neoretail_local.customers --config config/customers.yaml --active --require-source
    python -m neoretail_local.pipeline --tenant pandurata --step 00

In a host test, supply CUSTOMERS_CONFIG_PATH explicitly. Containers retain their existing /workspace/config path.

## Packaging

The only Dockerfile change is embedded-app/Dockerfile adding tenant-registry.js to the existing runtime COPY. Without this line the new backend import would be absent from an image. Docker Compose and the Superset Dockerfile are unchanged.

Built image: neoretail-tenant-context:review. The module's three exported functions were imported successfully in a fresh container with no volumes/bind mounts. Configuration is still provided through the existing deployment config mount; this check proves code packaging, not runtime alignment.

## Validation

All tests used disposable containers, read-only source mounts and no external network. Temporary work files lived inside containers removed with --rm. No production services were replaced.

- Python full suite: 548 passed, 2 failed (the same two baseline failures; see below).
- New Python TenantContext suite: 43 cases, included in the full suite.
- Node tenant/HTTP/parity plus existing Assistant regression: 47 passed, zero failed/skipped.
- Real HTTP test: login/session/catalog, inactive-but-authorized AMBEV accepted; all three ungranted tenants and an injected selector denied.
- Python contexts were computed in the Python image and compared with the Node resolver for all four tenants; there was no parity skip.
- PowerShell parser: passed.
- Embedded image build and resolver import without volumes: passed.
- git diff --check: passed.

Baseline failures were reproduced on the previous clean OSA modularization worktree, whose tree equals the integrated base:

1. test_v9_customer_registry_and_embedded_rls still expects seven dashboard keys although osa_certified is the eighth.
2. test_value_and_quantity_dashboard_isolated_from_legacy_page still expects a textual layout literal absent from the already-refactored source.

Those assertions were not removed or relaxed. The existing customer list assertion was expanded from exact [142] to exact [142,17066,290,16868]; AMBEV default/name/prefix/layout and Embedded RLS checks remain. validate_project's identity checks were likewise expanded, with explicit null-source and activation assertions. All business SQL, formulas, aliases, marts, charts, datasets, UUIDs, layouts and frontend source remain unchanged.

The first network-disabled Spark run needed hostname localhost and SPARK_LOCAL_IP=127.0.0.1 to avoid an isolated-container hostname error. Final results above use that test-environment correction. A new CLI test was also given its explicit read-only registry path; no product assertion was weakened.

## Remaining prerequisites and decisions

See multitenant_runtime_osa_reconciliation.md and osa_additional_objects_ddl_audit.sql.

- Runtime alignment must happen in a separate deployment/PR after resolving the dirty old OSA worktree.
- Confirm new source prefixes/layouts and corporate identities from the source.
- Decide whether the local OSA performance experiment should be separately certified/versioned or retired.
- No new tenant is authorized or loaded. No live multi-tenant Guest isolation or PBI reconciliation is claimed.
- Gold publication still targets existing gold. gold_schema is only context metadata for PR 2.
- Retention/publication profiles, serving, schema ACL/database RLS and PBI windows remain later work.
