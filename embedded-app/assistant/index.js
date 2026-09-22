import { loadMetricCatalog } from "./catalog.js";
import { createReadOnlyQuery } from "./database.js";
import { MetricTools } from "./metric-tools.js";
import { AnalyticsOrchestrator } from "./orchestrator.js";
import { auditEvent, newRequestId, safeUserId } from "./audit.js";
import { createProvider } from "./providers.js";

function enabled(value) {
  return String(value || "false").toLowerCase() === "true";
}

function errorStatus(code) {
  if (["TENANT_OVERRIDE_FORBIDDEN", "FILTER_NOT_ALLOWED"].includes(code)) return 403;
  if (["OLLAMA_UNAVAILABLE", "MODEL_NOT_FOUND", "INVALID_PROVIDER_RESPONSE"].includes(code)) return 503;
  return 400;
}

export function createAssistantService({ env = process.env, dashboards = [], logger = console, queryOverride = null, providerOverride = null } = {}) {
  const isEnabled = enabled(env.ASSISTANT_ENABLED);
  const catalogPath = env.ASSISTANT_METRIC_CATALOG || "/app/config/assistant_metrics.yaml";
  if (!isEnabled) {
    return {
      enabled: false,
      provider: null,
      async health() { return { status: "disabled", enabled: false, available: false }; },
    };
  }

  const catalog = loadMetricCatalog(catalogPath);
  const database = queryOverride ? null : createReadOnlyQuery({
    host: env.ANALYTICS_DB_HOST,
    port: env.ANALYTICS_DB_PORT,
    database: env.ANALYTICS_DB_NAME,
    user: env.ANALYTICS_DB_USER,
    password: env.ANALYTICS_DB_PASSWORD,
    statementTimeoutMs: env.ASSISTANT_SQL_TIMEOUT_MS,
  });
  const query = queryOverride || database.query;
  const provider = providerOverride || createProvider({
    provider: env.LLM_PROVIDER || "mock",
    baseUrl: env.OLLAMA_BASE_URL,
    model: env.OLLAMA_MODEL,
    timeoutMs: env.LLM_TIMEOUT_MS,
  });
  const tools = new MetricTools({ catalog, query });
  const orchestrator = new AnalyticsOrchestrator({ tools, provider, catalog, dashboards });

  return {
    enabled: true,
    provider,
    catalog,
    orchestrator,
    logger,
    auditSalt: env.ASSISTANT_AUDIT_SALT || env.SESSION_SECRET || "neoretail-assistant",
    async health() {
      const providerHealth = await provider.health();
      return {
        status: providerHealth.available ? "ok" : "degraded",
        enabled: true,
        ...providerHealth,
      };
    },
    close: () => database?.close(),
  };
}

export function registerAssistantRoutes(app, { service, requireIdentity }) {
  app.get("/api/assistant/health", async (_req, res) => {
    const health = await service.health();
    res.status(health.status === "ok" || health.status === "disabled" ? 200 : 503).json(health);
  });

  app.post("/api/assistant/chat", async (req, res) => {
    const startedAt = Date.now();
    const requestId = newRequestId();
    const identity = requireIdentity(req, res);
    if (!identity) return;
    if (!service.enabled) return res.status(404).json({ error: "Assistente não habilitado.", errorCode: "ASSISTANT_DISABLED", requestId });
    if (req.body?.tenantId !== undefined || req.body?.idCustomer !== undefined
        || req.body?.context?.tenantId !== undefined || req.body?.context?.idCustomer !== undefined
        || req.body?.context?.filters?.id_customer !== undefined) {
      return res.status(403).json({ error: "O tenant é definido exclusivamente pela sessão.", errorCode: "TENANT_OVERRIDE_FORBIDDEN", requestId });
    }
    const event = {
      request_id: requestId,
      safe_user_or_session_id: safeUserId(identity.username, service.auditSalt),
      tenant_id: identity.idCustomer,
      question: req.body?.message,
      provider: service.provider.name,
      model: service.provider.model,
    };
    try {
      const response = await service.orchestrator.answer({
        question: req.body?.message,
        tenantId: identity.idCustomer,
        tenantName: identity.customerName,
        context: req.body?.context,
        history: req.body?.history,
      });
      auditEvent({
        ...event,
        intent: response.intent,
        tool_called: response.toolCalled,
        metric_id: response.metricId,
        period: response.evidence?.[0]?.period,
        filters: response.evidence?.[0]?.filters,
        source_mart: response.evidence?.[0]?.source,
        governance_status: response.evidence?.[0]?.technicalStatus,
        latency_ms: Date.now() - startedAt,
        success: true,
        error_code: null,
      }, service.logger);
      res.json({ requestId, ...response });
    } catch (error) {
      const errorCode = error.code || "ASSISTANT_ERROR";
      auditEvent({
        ...event,
        intent: null,
        tool_called: null,
        metric_id: null,
        period: null,
        filters: {},
        source_mart: null,
        governance_status: null,
        latency_ms: Date.now() - startedAt,
        success: false,
        error_code: errorCode,
      }, service.logger);
      res.status(errorStatus(errorCode)).json({ error: error.message, errorCode, requestId });
    }
  });
}
