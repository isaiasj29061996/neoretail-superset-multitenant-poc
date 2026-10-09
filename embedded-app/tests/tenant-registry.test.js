import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";
import test from "node:test";
import YAML from "yaml";
import { buildAuthorizedCustomers, loadRegistryText, loadTenantRegistry, resolveTenant } from "../tenant-registry.js";

const root = process.env.NEORETAIL_REPO_ROOT || path.resolve(import.meta.dirname, "../..");
const registryPath = path.join(root, "config/customers.yaml");
const registry = loadTenantRegistry(registryPath);
const authorization = YAML.parse(fs.readFileSync(path.join(root, "config/tenants.yaml"), "utf8"));
const expected = [["ambev", 142, "AMBEV"], ["pandurata", 17066, "PANDURATA"], ["lactalis", 290, "LACTALIS"], ["safira", 16868, "SAFIRA"]];
function modified(mutate) {
  const document = structuredClone(registry.document);
  mutate(document);
  return () => loadRegistryText(YAML.stringify(document));
}

for (const [key, id, name] of expected) {
  test(`resolves ${key} by key, ID and name`, () => {
    const context = resolveTenant(registry, key);
    assert.deepEqual(context, resolveTenant(registry, id));
    assert.deepEqual(context, resolveTenant(registry, name.toLowerCase()));
    assert.equal(context.gold_schema, `gold_${key}`);
    assert.equal(context.id_customer, id);
  });
}
test("AMBEV remains available but is not automatically executed", () => {
  assert.equal(resolveTenant(registry).id_customer, 142);
  assert.throws(() => resolveTenant(registry, 142, { automatic: true }), /inactive/);
  assert.deepEqual(registry.identities.filter(row => row.execution_active).map(row => row.tenant_key), ["pandurata"]);
});
test("pending source and inactive selection fail closed", () => {
  for (const key of ["pandurata", "lactalis", "safira"]) {
    assert.equal(resolveTenant(registry, key).source_prefix, null);
    assert.throws(() => resolveTenant(registry, key, { requireSource: true }), /Pending source/);
  }
  assert.throws(() => resolveTenant(registry, "pandurata", { automatic: true }), /Pending/);
  assert.throws(() => resolveTenant(registry, "lactalis", { automatic: true }), /inactive/);
});
test("unknown and disabled tenants are rejected", () => {
  for (const value of ["unknown", 999999, true, "142 OR 1=1"]) assert.throws(() => resolveTenant(registry, value));
  const disabled = modified(d => { d.customers[0].enabled = false; })();
  assert.throws(() => resolveTenant(disabled, 142), /disabled/);
});
for (const field of ["tenant_key", "id_customer", "nm_customer", "gold_schema"]) {
  test(`rejects duplicate ${field}`, () => {
    assert.throws(modified(d => { d.customers[1][field] = d.customers[0][field]; }), /Duplicate/);
  });
}
test("duplicate YAML keys and unsafe identifiers are rejected", () => {
  assert.throws(() => loadRegistryText(fs.readFileSync(registryPath, "utf8") + "\ndefault_customer: 17066"));
  for (const [field, value] of [
    ["gold_schema", "gold.x"], ["gold_schema", 'gold";DROP SCHEMA gold;'], ["gold_schema", "a".repeat(64)],
    ["tenant_key", "bad-key"], ["id_customer", true], ["id_customer", "142"],
    ["execution_active", "false"], ["source_prefix", "<confirmar>"], ["source_prefix", "../other"],
  ]) assert.throws(modified(d => { d.customers[0][field] = value; }));
});
test("missing source fields allow resolution but block source execution", () => {
  for (const field of ["source_prefix", "source_layout"]) {
    const pending = modified(d => { delete d.customers[0][field]; })();
    assert.equal(resolveTenant(pending, 142).id_customer, 142);
    assert.throws(() => resolveTenant(pending, 142, { requireSource: true }), /Pending/);
  }
});
test("authorization stays separate; active selection grants no access", () => {
  const customers = buildAuthorizedCustomers(registry, authorization);
  assert.equal(customers["142"].name, "AMBEV");
  assert.deepEqual(customers["142"].modules, ["visao_industria", "tarefas", "exportacao_diaria", "exportacao_mensal"]);
  assert.deepEqual(customers["17066"].modules, []);
  assert.deepEqual(authorization.users[0].allowed_customer_ids, [142]);
  assert.throws(() => buildAuthorizedCustomers(registry, { ...authorization, customers: {} }), /Duplicate identity/);
  assert.throws(() => buildAuthorizedCustomers(registry, { ...authorization, users: [{ allowed_customer_ids: [999999] }] }));
  assert.throws(() => buildAuthorizedCustomers(registry, { ...authorization, customer_access: { unknown: { modules: [] } } }));
});
test("server consumes canonical registry and preserves trusted RLS/context", () => {
  const server = fs.readFileSync(path.join(root, "embedded-app/server.js"), "utf8");
  assert.match(server, /buildAuthorizedCustomers\(registry, tenantConfig\)/);
  assert.match(server, /allowedCustomerIds.includes\(idCustomer\)/);
  assert.match(server, /id_customer = \$\{idCustomer\}/);
  assert.match(server, /app.post\("\/api\/context"/);
});
test("HTTP login/session/context preserve baseline access and deny ungranted tenants", async t => {
  const port = 38119;
  const child = spawn(process.execPath, ["server.js"], {
    cwd: path.resolve(import.meta.dirname, ".."),
    env: {
      ...process.env, PORT: String(port), ASSISTANT_ENABLED: "false",
      TENANTS_CONFIG: path.join(root, "config/tenants.yaml"), CUSTOMERS_CONFIG_PATH: registryPath,
      PUBLISHED_DASHBOARDS_CONFIG: "/tmp/no-published-tenant-test.json",
      DEMO_USER_PASSWORD: "isolated-test-fixture", SESSION_SECRET: "isolated-test-session",
    },
    stdio: ["ignore", "pipe", "pipe"],
  });
  t.after(() => child.kill());
  let ready = false;
  for (let attempt = 0; attempt < 100; attempt += 1) {
    try {
      ready = (await fetch(`http://127.0.0.1:${port}/health`)).ok;
      if (ready) break;
    } catch {}
    await new Promise(resolve => setTimeout(resolve, 20));
  }
  assert.equal(ready, true, "isolated backend did not start");
  const login = await fetch(`http://127.0.0.1:${port}/api/login`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: "demo.multitenant", password: "isolated-test-fixture" }),
  });
  assert.equal(login.status, 200);
  const cookie = login.headers.get("set-cookie").split(";")[0];
  const headers = { Cookie: cookie, "Content-Type": "application/json" };
  const session = await (await fetch(`http://127.0.0.1:${port}/api/session`, { headers })).json();
  assert.equal(session.idCustomer, 142);
  assert.deepEqual(session.availableCustomers, [{ idCustomer: 142, name: "AMBEV" }]);
  assert.deepEqual(session.modules, authorization.customer_access.ambev.modules);
  for (const idCustomer of [17066, 290, 16868, 999999, "142 OR 1=1"]) {
    const denied = await fetch(`http://127.0.0.1:${port}/api/context`, {
      method: "POST", headers, body: JSON.stringify({ idCustomer }),
    });
    assert.equal(denied.status, 403);
  }
  const allowed = await fetch(`http://127.0.0.1:${port}/api/context`, {
    method: "POST", headers, body: JSON.stringify({ idCustomer: 142 }),
  });
  assert.equal(allowed.status, 200);
  const catalog = await (await fetch(`http://127.0.0.1:${port}/api/catalog`, { headers })).json();
  assert.equal(catalog.dashboards.length, Object.keys(authorization.dashboards).length);
});
// Run in an isolated combined Python/Node test container. Missing Python is
// reported as a skip in a standalone Node image, never mistaken for parity.
test("pipeline Python and Embedded Node return identical contexts", t => {
  if (process.env.TENANT_PYTHON_CONTEXTS_B64) {
    const contexts = JSON.parse(Buffer.from(process.env.TENANT_PYTHON_CONTEXTS_B64, "base64").toString("utf8"));
    assert.equal(contexts.length, expected.length);
    for (const [key, id] of expected) {
      assert.deepEqual(contexts.find(context => context.id_customer === id), resolveTenant(registry, key));
    }
    return;
  }
  const python = process.env.TENANT_TEST_PYTHON || "python";
  const probe = spawnSync(python, ["--version"], { encoding: "utf8" });
  if (probe.error) return t.skip("Python unavailable; run combined parity validation");
  for (const [key] of expected) {
    const result = spawnSync(python, ["-m", "neoretail_local.customers", "--config", registryPath, "--tenant", key], {
      encoding: "utf8", env: { ...process.env, PYTHONPATH: path.join(root, "local-engine"), PYTHONDONTWRITEBYTECODE: "1" },
    });
    assert.equal(result.status, 0, result.stderr);
    assert.deepEqual(JSON.parse(result.stdout), resolveTenant(registry, key));
  }
});
