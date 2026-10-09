import fs from "node:fs";
import YAML from "yaml";

// Python and Node consume the same canonical document. Cross-runtime tests
// protect this small resolver contract; authorization is a separate document.
export function loadRegistryText(text) {
  const document = YAML.parse(text, { uniqueKeys: true });
  if (document?.version !== "9.0" || !Array.isArray(document.customers) || !document.customers.length) {
    throw new Error("Invalid tenant registry");
  }
  const identities = document.customers.map(row => {
    if (!row || !Number.isSafeInteger(row.id_customer) || row.id_customer <= 0) throw new Error("Invalid id_customer");
    for (const field of ["tenant_key", "gold_schema"]) {
      if (typeof row[field] !== "string" || !/^[a-z][a-z0-9_]{0,62}$/.test(row[field])) throw new Error(`Invalid ${field}`);
    }
    if (typeof row.nm_customer !== "string" || !row.nm_customer.trim()) throw new Error("Missing nm_customer");
    if (typeof row.execution_active !== "boolean" || (row.enabled !== undefined && typeof row.enabled !== "boolean")) {
      throw new Error("Invalid execution/enabled flag");
    }
    const source = {};
    for (const field of ["source_prefix", "source_layout"]) {
      const value = row[field] ?? null;
      if (value !== null && (typeof value !== "string" || !value.trim() || /[<>\\\\]/.test(value) || value.split("/").includes(".."))) {
        throw new Error(`Invalid ${field}`);
      }
      source[field] = value === null ? null : value.trim().replace(/^\/+|\/+$/g, "");
      if (value !== null && !source[field]) throw new Error(`Invalid ${field}`);
    }
    return {
      tenant_key: row.tenant_key, id_customer: row.id_customer,
      nm_customer: row.nm_customer.trim().toUpperCase(),
      display_name: String(row.display_name || row.nm_customer).trim(),
      gold_schema: row.gold_schema, ...source,
      execution_active: row.execution_active, enabled: row.enabled ?? true,
    };
  });
  for (const field of ["tenant_key", "id_customer", "nm_customer", "gold_schema"]) {
    if (new Set(identities.map(row => row[field])).size !== identities.length) throw new Error(`Duplicate ${field}`);
  }
  const owners = new Map();
  for (const identity of identities) {
    for (const selector of [identity.tenant_key.toUpperCase(), identity.nm_customer]) {
      if (owners.has(selector) && owners.get(selector) !== identity.id_customer) throw new Error("Ambiguous tenant selector");
      owners.set(selector, identity.id_customer);
    }
  }
  return { document, identities };
}

export function loadTenantRegistry(file) {
  return loadRegistryText(fs.readFileSync(file, "utf8"));
}

export function resolveTenant(registry, selector, { requireSource = false, automatic = false } = {}) {
  const requested = String(selector ?? registry.document.default_customer ?? "").trim().toUpperCase();
  const matches = registry.identities.filter(row => [row.tenant_key.toUpperCase(), row.nm_customer, String(row.id_customer)].includes(requested));
  if (matches.length !== 1) throw new Error("Unknown or ambiguous tenant");
  const context = matches[0];
  if (!context.enabled) throw new Error("Tenant disabled");
  if (automatic && !context.execution_active) throw new Error("Tenant inactive for automatic execution");
  if ((requireSource || automatic) && (!context.source_prefix || !context.source_layout)) throw new Error("Pending source configuration");
  return context;
}

export function buildAuthorizedCustomers(registry, authorization) {
  if (authorization.customers !== undefined) throw new Error("Duplicate identity: use customer_access and canonical customers.yaml");
  const access = authorization.customer_access || {};
  for (const [key, definition] of Object.entries(access)) {
    const context = resolveTenant(registry, key);
    if (context.tenant_key !== key || !Array.isArray(definition.modules) || definition.modules.some(value => typeof value !== "string")) {
      throw new Error("Invalid customer_access");
    }
  }
  for (const user of authorization.users || []) {
    for (const id of user.allowed_customer_ids || []) {
      if (!Number.isSafeInteger(id) || resolveTenant(registry, id).id_customer !== id) throw new Error("Invalid user tenant permission");
    }
  }
  resolveTenant(registry, authorization.default_customer_id);
  return Object.fromEntries(registry.identities.filter(row => row.enabled).map(context => [
    String(context.id_customer),
    { name: context.display_name, modules: access[context.tenant_key]?.modules || [], context },
  ]));
}
