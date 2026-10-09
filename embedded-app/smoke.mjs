import fs from "node:fs";
import YAML from "yaml";

const base = process.env.SMOKE_BASE_URL || "http://localhost:3000";
const password = process.env.DEMO_USER_PASSWORD;
if (!password) throw new Error("DEMO_USER_PASSWORD não configurada");

const tenantConfigPath = process.env.TENANTS_CONFIG || "/app/config/tenants.yaml";
const tenantConfig = YAML.parse(fs.readFileSync(tenantConfigPath, "utf8"));

function expectedDashboardIds(idCustomer) {
  const modules = new Set(tenantConfig.customers?.[String(idCustomer)]?.modules || []);
  return Object.entries(tenantConfig.dashboards || {})
    .filter(([, dashboard]) => !dashboard.required_module || modules.has(dashboard.required_module))
    .map(([dashboardId]) => dashboardId);
}

function assertSameDashboardSet(idCustomer, catalog) {
  const expected = expectedDashboardIds(idCustomer);
  const actual = (catalog.dashboards || []).map((dashboard) => dashboard.key);
  const actualSet = new Set(actual);
  if (actualSet.size !== actual.length) {
    throw new Error(`Catálogo contém dashboards duplicados para ${idCustomer}`);
  }
  const missing = expected.filter((dashboardId) => !actualSet.has(dashboardId));
  const unexpected = actual.filter((dashboardId) => !expected.includes(dashboardId));
  if (missing.length || unexpected.length) {
    throw new Error(
      `Contrato de dashboards inválido para ${idCustomer}: `
      + `faltando=[${missing.join(",")}], inesperados=[${unexpected.join(",")}]`,
    );
  }
  const navigationIds = (catalog.navigation || [])
    .flatMap((section) => section.items || [])
    .map((dashboard) => dashboard.key);
  if (new Set(navigationIds).size !== navigationIds.length
      || navigationIds.some((dashboardId) => !actualSet.has(dashboardId))
      || actual.some((dashboardId) => !navigationIds.includes(dashboardId))) {
    throw new Error(`Navegação inconsistente com o catálogo para ${idCustomer}`);
  }
  return actual.length;
}

let cookie = "";
async function request(path, options = {}) {
  const response = await fetch(`${base}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(cookie ? { Cookie: cookie } : {}),
      ...(options.headers || {}),
    },
  });
  const setCookie = response.headers.get("set-cookie");
  if (setCookie) cookie = setCookie.split(";", 1)[0];
  const body = await response.json().catch(() => ({}));
  return { response, body };
}

const login = await request("/api/login", {
  method: "POST",
  body: JSON.stringify({ username: "demo.multitenant", password }),
});
if (!login.response.ok) throw new Error(`Login falhou: ${login.response.status}`);

const expectedCustomers = [Number(process.env.NEORETAIL_VALIDATION_CUSTOMER || 142)];
let issuedTokens = 0;
let authorizedDashboards = 0;
for (const idCustomer of expectedCustomers) {
  const context = await request("/api/context", {
    method: "POST", body: JSON.stringify({ idCustomer }),
  });
  if (!context.response.ok) throw new Error(`Contexto ${idCustomer} falhou`);

  const catalog = await request("/api/catalog");
  if (!catalog.response.ok || !Array.isArray(catalog.body.dashboards)) {
    throw new Error(`Catálogo inválido para ${idCustomer}`);
  }
  authorizedDashboards += assertSameDashboardSet(idCustomer, catalog.body);
  for (const dashboard of catalog.body.dashboards) {
    const guest = await request("/api/guest-token", {
      method: "POST", body: JSON.stringify({ dashboardKey: dashboard.key }),
    });
    if (!guest.response.ok || !guest.body.token) {
      throw new Error(
        `Guest Token falhou: ${idCustomer}/${dashboard.key} `
        + `(${guest.response.status}: ${guest.body.detail || guest.body.error || "sem detalhe"})`,
      );
    }
    const payload = JSON.parse(Buffer.from(guest.body.token.split(".")[1], "base64url"));
    const clauses = (payload.rls_rules || []).map((rule) => rule.clause);
    if (!clauses.includes(`id_customer = ${idCustomer}`)) {
      throw new Error(`RLS incorreto: ${idCustomer}/${dashboard.key}`);
    }
    if (!payload.resources?.some((resource) => resource.id === dashboard.embeddedId)) {
      throw new Error(`Recurso incorreto: ${dashboard.key}`);
    }
    issuedTokens += 1;
  }
}

const deniedCustomers = [259, 609, 16868, 999999];
for (const idCustomer of deniedCustomers) {
  const denied = await request("/api/context", {
    method: "POST", body: JSON.stringify({ idCustomer }),
  });
  if (denied.response.status !== 403) {
    throw new Error(`Cliente não autorizado foi aceito: ${idCustomer}`);
  }
}

console.log(JSON.stringify({
  status: "ok", customers: expectedCustomers.length,
  dashboards: authorizedDashboards, guestTokens: issuedTokens,
  deniedCustomers: deniedCustomers.length,
}));
