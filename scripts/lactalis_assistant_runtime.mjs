// Execute inside embedded-app with its existing environment; prints no credentials.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createAssistantService } from '/app/assistant/index.js';
import { createReadOnlyQuery } from '/app/assistant/database.js';

let cookie = '';
async function request(path, body) {
  const started = performance.now();
  const response = await fetch(`http://localhost:3000${path}`, {
    method: body ? 'POST' : 'GET',
    headers: { 'Content-Type': 'application/json', ...(cookie ? { Cookie: cookie } : {}) },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  const value = response.headers.get('set-cookie');
  if (value) cookie = value.split(';')[0];
  return { status: response.status, body: await response.json(), milliseconds: Math.round(performance.now() - started) };
}
assert.equal((await request('/api/login', { username: 'demo.multitenant', password: process.env.DEMO_USER_PASSWORD })).status, 200);
const identity = (await request('/api/session')).body;
assert.equal(identity.idCustomer, 290);
assert.deepEqual(identity.availableCustomers.map(c => c.idCustomer), [290]);
const health = await request('/api/assistant/health');
assert.equal(health.status, 200);
assert.equal(health.body.status, 'ok');
assert.equal(health.body.provider, process.env.LLM_PROVIDER || 'mock');
const value = await request('/api/assistant/chat', { message: 'Como está o OSA este mês?' });
assert.equal(value.status, 200, JSON.stringify(value.body));
assert.equal(value.body.intent, 'metric_value');
assert.equal(value.body.evidence[0].tenantId, 290);
assert.ok(value.body.answer);
console.log(JSON.stringify({ stage: 'metric_value', passed: true, milliseconds: value.milliseconds }));
const source = await request('/api/assistant/chat', { message: 'Qual é a fonte usada para calcular o OSA?' });
assert.equal(source.status, 200, JSON.stringify(source.body));
assert.equal(source.body.intent, 'metric_source');
assert.equal(source.body.data.source, 'gold.nr_overview_quantity_default');
console.log(JSON.stringify({ stage: 'metric_source', passed: true, milliseconds: source.milliseconds }));
const governance = await request('/api/assistant/chat', { message: 'Qual é o status técnico, de negócio e temporal do OSA?' });
assert.equal(governance.status, 200, JSON.stringify(governance.body));
assert.equal(governance.body.intent, 'metric_governance');
assert.equal(governance.body.evidence[0].tenantId, 290);
console.log(JSON.stringify({ stage: 'metric_governance', passed: true, milliseconds: governance.milliseconds }));
const denied = [];
for (const other of [142, 17066, 609]) {
  const response = await request('/api/assistant/chat', { message: 'Como está o OSA?', tenantId: other });
  assert.equal(response.status, 403);
  assert.equal(response.body.errorCode, 'TENANT_OVERRIDE_FORBIDDEN');
  denied.push(other);
}
const database = createReadOnlyQuery({ host: process.env.ANALYTICS_DB_HOST, port: process.env.ANALYTICS_DB_PORT,
  database: process.env.ANALYTICS_DB_NAME, user: process.env.ANALYTICS_DB_USER, password: process.env.ANALYTICS_DB_PASSWORD,
  statementTimeoutMs: process.env.ASSISTANT_SQL_TIMEOUT_MS });
const parameters = [];
const service = createAssistantService({ env: { ...process.env, LLM_PROVIDER: 'mock' }, queryOverride: async (sql, params) => {
  assert.equal(params[0], identity.idCustomer);
  assert.match(sql, /id_customer = \$1/);
  parameters.push(params[0]);
  return database.query(sql, params);
} });
try {
  // Same production Tool against the actual DB; compare with the authenticated HTTP result.
  const tool = await service.orchestrator.answer({ question: 'Como está o OSA este mês?', tenantId: identity.idCustomer, tenantName: identity.customerName });
  assert.equal(tool.data.value, value.body.data.value);
  assert.ok(parameters.length);
  const report = { passed: true, tenant: 290, health: health.body, metric: value.body.metricId,
    question: 'Como está o OSA este mês?', answer: value.body.answer, tool_called: value.body.toolCalled,
    source_answer: source.body.answer, governance_answer: governance.body.answer,
    timings_ms: { value: value.milliseconds, source: source.milliseconds, governance: governance.milliseconds },
    value: value.body.data.value, source: source.body.data.source, governance: governance.body.evidence[0],
    http_intents: [value.body.intent, source.body.intent, governance.body.intent],
    production_tool_sql_parameters: parameters, denied_tenant_overrides: denied };
  fs.writeFileSync('/tmp/lactalis_assistant_runtime.json', JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
} finally { await database.close(); }
