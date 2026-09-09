const base = process.env.SMOKE_BASE_URL || "http://localhost:3000";
const password = process.env.DEMO_USER_PASSWORD;
if (!password) throw new Error("DEMO_USER_PASSWORD não configurada");

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

const expectedCustomers = [259, 609, 16868];
let issuedTokens = 0;
for (const idCustomer of expectedCustomers) {
  const context = await request("/api/context", {
    method: "POST", body: JSON.stringify({ idCustomer }),
  });
  if (!context.response.ok) throw new Error(`Contexto ${idCustomer} falhou`);

  const catalog = await request("/api/catalog");
  if (!catalog.response.ok || catalog.body.dashboards?.length !== 4) {
    throw new Error(`Catálogo inválido para ${idCustomer}`);
  }
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

const denied = await request("/api/context", {
  method: "POST", body: JSON.stringify({ idCustomer: 999999 }),
});
if (denied.response.status !== 403) throw new Error("Cliente não autorizado foi aceito");

console.log(JSON.stringify({
  status: "ok", customers: expectedCustomers.length,
  dashboards: 4, guestTokens: issuedTokens, unauthorizedCustomer: 403,
}));
