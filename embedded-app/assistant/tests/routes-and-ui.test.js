import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import { registerAssistantRoutes } from "../index.js";

function responseRecorder() {
  return {
    statusCode: 200, body: null,
    status(code) { this.statusCode = code; return this; },
    json(body) { this.body = body; return this; },
  };
}

test("route rejects every client-side tenant override before orchestration", async () => {
  const routes = {};
  const app = { get(path, handler) { routes[`GET ${path}`] = handler; }, post(path, handler) { routes[`POST ${path}`] = handler; } };
  let called = false;
  const service = {
    enabled: true,
    provider: { name: "mock", model: "test" },
    auditSalt: "test",
    logger: { info() {} },
    async health() { return { status: "ok" }; },
    orchestrator: { async answer() { called = true; return {}; } },
  };
  registerAssistantRoutes(app, { service, requireIdentity: () => ({ username: "u", idCustomer: 142, customerName: "AMBEV" }) });
  for (const body of [
    { message: "OSA", tenantId: 259 },
    { message: "OSA", context: { idCustomer: 259 } },
    { message: "OSA", context: { filters: { id_customer: 259 } } },
  ]) {
    const res = responseRecorder();
    await routes["POST /api/assistant/chat"]({ body }, res);
    assert.equal(res.statusCode, 403);
    assert.equal(res.body.errorCode, "TENANT_OVERRIDE_FORBIDDEN");
  }
  assert.equal(called, false);
});

test("assistant UI is optional and never sends tenant authority", () => {
  const html = fs.readFileSync(new URL("../../public/index.html", import.meta.url), "utf8");
  const frontend = fs.readFileSync(new URL("../../public/app.bundle.js", import.meta.url), "utf8");
  assert.match(html, /id="assistant-panel"/);
  assert.match(html, /id="assistant-open"[^>]+hidden/);
  assert.match(frontend, /assistantEnabled/);
  assert.match(frontend, /\/api\/assistant\/chat/);
  assert.doesNotMatch(frontend, /tenantId:getIdentity|idCustomer:getIdentity/);
});
