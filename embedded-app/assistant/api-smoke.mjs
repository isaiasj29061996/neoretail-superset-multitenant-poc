import assert from "node:assert/strict";

const base = process.env.SMOKE_BASE_URL || "http://127.0.0.1:3000";
const password = process.env.DEMO_USER_PASSWORD;
if (!password) throw new Error("DEMO_USER_PASSWORD não configurada");

let cookie = "";
async function request(path, body) {
  const response = await fetch(`${base}${path}`, {
    method: body ? "POST" : "GET",
    headers: { "Content-Type": "application/json", ...(cookie ? { Cookie: cookie } : {}) },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  const setCookie = response.headers.get("set-cookie");
  if (setCookie) cookie = setCookie.split(";", 1)[0];
  return { status: response.status, body: await response.json().catch(() => ({})) };
}

const login = await request("/api/login", { username: "demo.multitenant", password });
assert.equal(login.status, 200);
const value = await request("/api/assistant/chat", { message: "Como está o OSA este mês?", context: { filters: {} } });
assert.equal(value.status, 200);
assert.equal(value.body.intent, "metric_value");
assert.match(value.body.answer, /74,13%/);
assert.equal(value.body.evidence[0].tenantId, 142);
assert.equal(value.body.evidence[0].source, "gold.nr_overview_quantity_default");

const source = await request("/api/assistant/chat", {
  message: "Qual é a fonte usada para calcular essa métrica?",
  context: { metricId: value.body.metricId, filters: {} },
  history: [{ role: "assistant", content: value.body.answer }],
});
assert.equal(source.status, 200);
assert.equal(source.body.intent, "metric_source");
assert.match(source.body.answer, /gold\.nr_overview_quantity_default/);

const override = await request("/api/assistant/chat", { message: "OSA", tenantId: 259 });
assert.equal(override.status, 403);
assert.equal(override.body.errorCode, "TENANT_OVERRIDE_FORBIDDEN");

console.log(JSON.stringify({ status: "ok", tenant: 142, intents: [value.body.intent, source.body.intent], override: override.status }));
