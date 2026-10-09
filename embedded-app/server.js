import express from "express";
import session from "express-session";
import fs from "node:fs";
import path from "node:path";
import YAML from "yaml";
import { createAssistantService, registerAssistantRoutes } from "./assistant/index.js";

const app = express();
const port = Number(process.env.PORT || 3000);
const configPath = process.env.TENANTS_CONFIG || "/app/config/tenants.yaml";
const tenantConfig = YAML.parse(fs.readFileSync(configPath, "utf8"));
const customers = tenantConfig.customers || {};
const users = tenantConfig.users || [];
const dashboards = tenantConfig.dashboards || {};
const navigation = tenantConfig.navigation || [];
const publishedCatalogPath = process.env.PUBLISHED_DASHBOARDS_CONFIG
  || "/app/generated/neoretail-published-dashboards.json";
const assistantService = createAssistantService({
  dashboards: Object.keys(dashboards),
});

function dashboardCatalog() {
  try {
    const dynamic = JSON.parse(fs.readFileSync(publishedCatalogPath, "utf8"));
    return { ...dashboards, ...(dynamic.dashboards || {}) };
  } catch (error) {
    if (error?.code !== "ENOENT") console.error("Catálogo publicado inválido:", error.message);
    return dashboards;
  }
}

app.disable("x-powered-by");
app.use(express.json({ limit: "32kb" }));
app.use(session({
  name: "neoretail.poc.sid",
  secret: process.env.SESSION_SECRET || "change-me-local-session",
  resave: false,
  saveUninitialized: false,
  cookie: { httpOnly: true, sameSite: "lax", secure: false, maxAge: 8 * 60 * 60 * 1000 },
}));
app.use("/api", (_req, res, next) => {
  res.set("Cache-Control", "no-store");
  next();
});

app.get("/health", (_req, res) => res.json({
  status: "ok", service: "neoretail-embedded", version: "9.1",
  dashboards: Object.keys(dashboardCatalog()).length,
  source: "azure-blob", analytics: "local-postgres",
}));

function customerList(identity) {
  return identity.allowedCustomerIds
    .filter((idCustomer) => customers[String(idCustomer)])
    .map((idCustomer) => ({ idCustomer, name: customers[String(idCustomer)].name }));
}

function authorizedDashboards(identity) {
  const customer = customers[String(identity.selectedCustomerId)];
  const modules = customer?.modules || [];
  return Object.entries(dashboardCatalog())
    .filter(([, item]) => !item.required_module || modules.includes(item.required_module))
    .map(([key, item]) => ({
      key,
      title: item.title,
      menuLabel: item.menu_label,
      section: item.section,
      embeddedId: String(item.embedded_id),
      embeddedHeight: Number(item.embedded_height || 1200),
    }));
}

function navigationFor(identity) {
  const allowed = authorizedDashboards(identity);
  return navigation.map((section) => ({
    key: section.key,
    label: section.label,
    items: allowed.filter((dashboard) => dashboard.section === section.key),
  })).filter((section) => section.items.length > 0);
}

function sessionPayload(req) {
  const identity = req.session.identity;
  if (!identity) return null;
  const customer = customers[String(identity.selectedCustomerId)];
  if (!customer || !identity.allowedCustomerIds.includes(identity.selectedCustomerId)) return null;
  return {
    username: identity.username,
    displayName: identity.displayName,
    idCustomer: identity.selectedCustomerId,
    customerName: customer.name,
    modules: customer.modules || [],
    availableCustomers: customerList(identity),
    publicSupersetUrl: process.env.PUBLIC_SUPERSET_URL || "http://localhost:8088",
    defaultDashboard: tenantConfig.default_dashboard || "overview",
    analyticsMode: process.env.ANALYTICS_MODE || "local_postgres",
    assistantEnabled: assistantService.enabled,
  };
}

function requireIdentity(req, res) {
  const payload = sessionPayload(req);
  if (!payload) {
    res.status(401).json({ error: "Sessão NeoRetail ausente." });
    return null;
  }
  return payload;
}

function authorizedDashboard(identity, key) {
  return authorizedDashboards(identity).find((dashboard) => dashboard.key === key) || null;
}

registerAssistantRoutes(app, { service: assistantService, requireIdentity });

app.post("/api/login", (req, res) => {
  const username = String(req.body?.username || "").trim();
  const password = String(req.body?.password || "");
  const user = users.find((candidate) => candidate.username === username);
  const expectedPassword = user?.password_env ? process.env[user.password_env] : null;
  if (!user || !expectedPassword || password !== expectedPassword) {
    return res.status(401).json({ error: "Usuário ou senha inválidos." });
  }
  const allowedCustomerIds = (user.allowed_customer_ids || []).map(Number);
  const selectedCustomerId = allowedCustomerIds.includes(Number(tenantConfig.default_customer_id))
    ? Number(tenantConfig.default_customer_id) : allowedCustomerIds[0];
  if (!selectedCustomerId || !customers[String(selectedCustomerId)]) {
    return res.status(403).json({ error: "Usuário sem indústria válida configurada." });
  }
  req.session.regenerate((error) => {
    if (error) return res.status(500).json({ error: "Não foi possível iniciar a sessão." });
    req.session.identity = {
      username: user.username, displayName: user.display_name,
      allowedCustomerIds, selectedCustomerId,
    };
    req.session.save(() => res.json({ ok: true }));
  });
});

app.post("/api/logout", (req, res) => {
  req.session.destroy(() => {
    res.clearCookie("neoretail.poc.sid");
    res.json({ ok: true });
  });
});

app.get("/api/session", (req, res) => {
  const payload = sessionPayload(req);
  if (!payload) return res.status(401).json({ authenticated: false });
  res.json({ authenticated: true, ...payload });
});

app.get("/api/catalog", (req, res) => {
  if (!requireIdentity(req, res)) return;
  res.json({
    product: {
      key: "neoretail", name: "NeoRetail 2.0",
      description: "Visibilidade de vendas, estoque, OSA e oportunidades em um só produto.",
    },
    dashboards: authorizedDashboards(req.session.identity),
    navigation: navigationFor(req.session.identity),
  });
});
 
app.post("/api/context", (req, res) => {
  const identity = req.session.identity;
  if (!identity) return res.status(401).json({ error: "Sessão NeoRetail ausente." });
  const idCustomer = Number(req.body?.idCustomer);
  if (!Number.isSafeInteger(idCustomer)
      || !identity.allowedCustomerIds.includes(idCustomer)
      || !customers[String(idCustomer)]) {
    return res.status(403).json({ error: "Indústria não autorizada para este usuário." });
  }
  identity.selectedCustomerId = idCustomer;
  req.session.save(() => res.json({
    ok: true, idCustomer, customerName: customers[String(idCustomer)].name,
  }));
});

async function supersetCredentials() {
  const base = process.env.SUPERSET_INTERNAL_URL || "http://superset:8088";
  const response = await fetch(`${base}/api/v1/security/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: process.env.SUPERSET_ADMIN_USERNAME || "admin",
      password: process.env.SUPERSET_ADMIN_PASSWORD || "admin",
      provider: "db", refresh: true,
    }),
  });
  if (!response.ok) throw new Error(`Login técnico no Superset falhou (${response.status}).`);
  const accessToken = (await response.json()).access_token;
  const csrfResponse = await fetch(`${base}/api/v1/security/csrf_token/`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!csrfResponse.ok) throw new Error(`Token CSRF do Superset falhou (${csrfResponse.status}).`);
  const csrfToken = (await csrfResponse.json()).result;
  const csrfCookies = typeof csrfResponse.headers.getSetCookie === "function"
    ? csrfResponse.headers.getSetCookie()
    : [csrfResponse.headers.get("set-cookie")].filter(Boolean);
  const cookie = csrfCookies.map((value) => value.split(";", 1)[0]).join("; ");
  return { accessToken, csrfToken, cookie };
}

app.post("/api/guest-token", async (req, res) => {
  const identity = req.session.identity;
  if (!identity || !sessionPayload(req)) {
    return res.status(401).json({ error: "Sessão NeoRetail ausente." });
  }
  const dashboardKey = String(req.body?.dashboardKey || "");
  const dashboard = authorizedDashboard(identity, dashboardKey);
  if (!dashboard) {
    return res.status(403).json({ error: "Dashboard não autorizado para esta sessão." });
  }
  const idCustomer = Number(identity.selectedCustomerId);
  const customer = customers[String(idCustomer)];
  const base = process.env.SUPERSET_INTERNAL_URL || "http://superset:8088";
  try {
    const { accessToken, csrfToken, cookie } = await supersetCredentials();
    const response = await fetch(`${base}/api/v1/security/guest_token/`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "X-CSRFToken": csrfToken,
        Cookie: cookie,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user: {
          username: identity.username,
          first_name: identity.displayName,
          last_name: customer.name,
        },
        resources: [{ type: "dashboard", id: dashboard.embeddedId }],
        rls: [{ clause: `id_customer = ${idCustomer}` }],
      }),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      return res.status(response.status).json({
        error: `Guest Token recusado pelo Superset (${response.status}).`,
        detail: body.message || "Revise o recurso embedded e as permissões do usuário técnico.",
      });
    }
    res.json({ token: body.token, dashboardKey });
  } catch (error) {
    res.status(502).json({ error: error.message });
  }
});

const publicRoot = path.resolve("public");
app.get("/", (_req, res) => res.redirect("/portal"));
app.get("/login", (_req, res) => res.sendFile(path.join(publicRoot, "login.html")));
app.get("/portal", (_req, res) => res.sendFile(path.join(publicRoot, "portal.html")));
app.get(["/app", "/dashboard"], (_req, res) => res.sendFile(path.join(publicRoot, "index.html")));
app.use(express.static(publicRoot, { extensions: ["html"], index: false }));

app.listen(port, "0.0.0.0", () => console.log(`NeoRetail Embedded disponível na porta ${port}`));
