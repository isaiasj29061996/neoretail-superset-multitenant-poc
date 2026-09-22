import assert from "node:assert/strict";
import test from "node:test";
import { MockProvider, OllamaProvider, SYSTEM_PROMPT, createProvider } from "../providers.js";

function response(status, body) {
  return { ok: status >= 200 && status < 300, status, async json() { return body; } };
}

test("provider abstraction defaults to deterministic mock", async () => {
  const provider = createProvider({ provider: "mock" });
  assert.ok(provider instanceof MockProvider);
  assert.equal((await provider.health()).available, true);
  assert.match(SYSTEM_PROMPT, /não possui autoridade/i);
});

test("ollama health covers online, missing model and offline", async () => {
  const online = new OllamaProvider({ baseUrl: "http://ollama", model: "llama3.1:8b", fetchImpl: async () => response(200, { models: [{ name: "llama3.1:8b" }] }) });
  assert.equal((await online.health()).available, true);
  const missing = new OllamaProvider({ baseUrl: "http://ollama", model: "llama3.1:8b", fetchImpl: async () => response(200, { models: [] }) });
  assert.equal((await missing.health()).errorCode, "MODEL_NOT_FOUND");
  const offline = new OllamaProvider({ baseUrl: "http://ollama", model: "llama3.1:8b", fetchImpl: async () => { throw new Error("offline"); } });
  assert.equal((await offline.health()).errorCode, "OLLAMA_UNAVAILABLE");
});

test("ollama receives structured context but no database credentials", async () => {
  let requestBody;
  const provider = new OllamaProvider({
    baseUrl: "http://ollama", model: "llama3.1:8b",
    fetchImpl: async (_url, options) => { requestBody = JSON.parse(options.body); return response(200, { message: { content: "Resposta" } }); },
  });
  const answer = await provider.generate([{ role: "user", content: "OSA?" }], { result: { value: 74.12 }, authorization: "trusted_session" });
  assert.equal(answer, "Resposta");
  const serialized = JSON.stringify(requestBody);
  assert.doesNotMatch(serialized, /ANALYTICS_DB_PASSWORD|postgresql:\/\//);
  assert.match(serialized, /trusted_session/);
  assert.equal(requestBody.messages[0].role, "system");
  assert.match(requestBody.messages[0].content, /Contexto autorizado e imutável/);
  assert.equal(requestBody.messages.at(-1).role, "user");
});

test("invalid response and model errors fail closed", async () => {
  const invalid = new OllamaProvider({ baseUrl: "http://ollama", model: "x", fetchImpl: async () => response(200, {}) });
  await assert.rejects(() => invalid.generate([], {}), { code: "INVALID_PROVIDER_RESPONSE" });
  const missing = new OllamaProvider({ baseUrl: "http://ollama", model: "x", fetchImpl: async () => response(404, {}) });
  await assert.rejects(() => missing.generate([], {}), { code: "MODEL_NOT_FOUND" });
});

test("ollama requests honor the configured timeout", async () => {
  const keepEventLoopAlive = setTimeout(() => {}, 100);
  const provider = new OllamaProvider({
    baseUrl: "http://ollama",
    model: "llama3.1:8b",
    timeoutMs: 5,
    fetchImpl: async (_url, options) => new Promise((_resolve, reject) => {
      options.signal.addEventListener("abort", () => reject(options.signal.reason), { once: true });
    }),
  });

  try {
    await assert.rejects(() => provider.generate([], {}), error => error?.name === "TimeoutError");
  } finally {
    clearTimeout(keepEventLoopAlive);
  }
});
