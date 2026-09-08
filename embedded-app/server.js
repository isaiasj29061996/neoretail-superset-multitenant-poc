import express from "express";
import session from "express-session";
import fs from "node:fs";
import path from "node:path";
import YAML from "yaml";

const app = express();
const port = Number(process.env.PORT || 3000);
const configPath = process.env.TENANTS_CONFIG || "/app/config/tenants.yaml";
const tenantConfig = YAML.parse(fs.readFileSync(configPath, "utf8"));
const customers = tenantConfig.customers || {};
const users = tenantConfig.users || [];

app.use(express.json());
app.use(
  session({
    name: "neoretail.poc.sid",
    secret: process.env.SESSION_SECRET || "change-me-local-session",
    resave: false,
    saveUninitialized: false,
    cookie: { httpOnly: true, sameSite: "lax", secure: false, maxAge: 8 * 60 * 60 * 1000 },
  }),
);

app.get("/health", (_req, res) => res.json({
  status: "ok",
  service: "neoretail-embedded",
  version: "9.0",
  source: "azure-blob",
  analytics: "local-postgres",
}));

app.post("/api/login", (req, res) => {
  const username = String(req.body?.username || "").trim();
  const password = String(req.body?.password || "");
  const user = users.find((candidate) => candidate.username === username);
  const expectedPassword = user?.password_env
    ? process.env[user.password_env]
    : null;
  if (!user || !expectedPassword || password !== expectedPassword) {
    return res.status(401).json({ error: "Usuário ou senha inválidos." });
  }
  const allowedCustomerIds = (user.allowed_customer_ids || []).map(Number);
  const selectedCustomerId = allowedCustomerIds.includes(Number(tenantConfig.default_customer_id))
    ? Number(tenantConfig.default_customer_id)
    : allowedCustomerIds[0];
  if (!selectedCustomerId || !customers[String(selectedCustomerId)]) {
    return res.status(403).json({ error: "Usuário sem cliente válido configurado." });
  }

  req.session.identity = {
    username: user.username,
    displayName: user.display_name,
    allowedCustomerIds,
    selectedCustomerId,
  };
  res.json({ ok: true });
});

app.post("/api/logout", (req, res) => {
  req.session.destroy(() => res.json({ ok: true }));
});

function sessionPayload(req) {
  const identity = req.session.identity;
  if (!identity) return null;
  const customer = customers[String(identity.selectedCustomerId)];
  if (!customer || !identity.allowedCustomerIds.includes(identity.selectedCustomerId)) {
    return null;
  }
  return {
    username: identity.username,
    displayName: identity.displayName,
    idCustomer: identity.selectedCustomerId,
    customerName: customer.name,
    modules: customer.modules || [],
    availableCustomers: identity.allowedCustomerIds.map((idCustomer) => ({
      idCustomer,
      name: customers[String(idCustomer)]?.name || String(idCustomer),
    })),
    publicSupersetUrl: process.env.PUBLIC_SUPERSET_URL || "http://localhost:8088",
    dashboardId: process.env.SUPERSET_EMBEDDED_DASHBOARD_ID || null,
    dashboardConfigured: Boolean(process.env.SUPERSET_EMBEDDED_DASHBOARD_ID),
    analyticsMode: process.env.ANALYTICS_MODE || "local_postgres",
  };
}

app.get("/api/session", (req, res) => {
  const payload = sessionPayload(req);
  if (!payload) return res.status(401).json({ authenticated: false });
  res.json({ authenticated: true, ...payload });
});

app.post("/api/context", (req, res) => {
  const identity = req.session.identity;
  if (!identity) return res.status(401).json({ error: "Sessão NeoRetail ausente." });
  const idCustomer = Number(req.body?.idCustomer);
  if (!Number.isSafeInteger(idCustomer)
      || !identity.allowedCustomerIds.includes(idCustomer)
      || !customers[String(idCustomer)]) {
    return res.status(403).json({ error: "Cliente não autorizado para este usuário." });
  }
  identity.selectedCustomerId = idCustomer;
  req.session.save(() => res.json({ ok: true, idCustomer }));
});

async function supersetAccessToken() {
  const base = process.env.SUPERSET_INTERNAL_URL || "http://superset:8088";
  const response = await fetch(`${base}/api/v1/security/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: process.env.SUPERSET_ADMIN_USERNAME || "admin",
      password: process.env.SUPERSET_ADMIN_PASSWORD || "admin",
      provider: "db",
      refresh: true,
    }),
  });
  if (!response.ok) throw new Error(`Login técnico no Superset falhou (${response.status}).`);
  return (await response.json()).access_token;
}

app.post("/api/guest-token", async (req, res) => {
  const identity = req.session.identity;
  if (!identity) return res.status(401).json({ error: "Sessão NeoRetail ausente." });

  const dashboardId = process.env.SUPERSET_EMBEDDED_DASHBOARD_ID;
  if (!dashboardId) {
    return res.status(503).json({
      error: "Dashboard embedded ainda não configurado.",
      action: "Defina SUPERSET_EMBEDDED_DASHBOARD_ID no .env após habilitar o dashboard no Superset.",
    });
  }

  const idCustomer = Number(identity.selectedCustomerId);
  if (!Number.isSafeInteger(idCustomer)
      || !identity.allowedCustomerIds.includes(idCustomer)
      || !customers[String(idCustomer)]) {
    return res.status(403).json({ error: "Cliente não autorizado para esta sessão." });
  }
  const customer = customers[String(idCustomer)];
  const base = process.env.SUPERSET_INTERNAL_URL || "http://superset:8088";
  try {
    const accessToken = await supersetAccessToken();
    const response = await fetch(`${base}/api/v1/security/guest_token/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user: {
          username: identity.username,
          first_name: identity.displayName,
          last_name: customer.name,
        },
        resources: [{ type: "dashboard", id: dashboardId }],
        rls: [{ clause: `id_customer = ${idCustomer}` }],
      }),
    });

    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      return res.status(response.status).json({
        error: `Guest Token recusado pelo Superset (${response.status}).`,
        detail: body.message || "Revise EMBEDDED_SUPERSET, dashboard UUID e permissões do usuário técnico.",
      });
    }
    res.json({ token: body.token });
  } catch (error) {
    res.status(502).json({ error: error.message });
  }
});

app.use(express.static(path.resolve("public"), { extensions: ["html"] }));
app.get(["/", "/login"], (_req, res) => res.sendFile(path.resolve("public/login.html")));
app.get(["/portal", "/dashboard"], (_req, res) => res.sendFile(path.resolve("public/index.html")));

app.listen(port, "0.0.0.0", () => console.log(`NeoRetail Embedded disponível na porta ${port}`));
