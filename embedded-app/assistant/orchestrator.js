import { metricGovernance } from "./catalog.js";

const METRIC_PATTERNS = [
  ["percentual_osa", /\bosa\b/i],
  ["tvd", /\btvd\b|pré[- ]?ruptura/i],
  ["ivd", /\bivd\b|excesso de estoque/i],
  ["sales", /vend(a|as|emos)|sell[ -]?out|faturamento/i],
  ["stock", /\bestoque\b/i],
];

const POLICY_ATTACK = /ignore (?:suas|as) regras|ignore a governan[cç]a|agora (?:você|voce) é administrador|todos os (?:clientes|tenants)|(?:tenant|cliente|id_customer)\s*\d+|gere sql|execute (?:sql|direto no banco)|credenciais?|senhas?|connection string|redefin(?:a|ir).*(?:f[oó]rmula|m[eé]trica)|bypass.*(?:cat[aá]logo|governan[cç]a)/i;

function metricFromQuestion(question, context = {}) {
  for (const [metricId, pattern] of METRIC_PATTERNS) if (pattern.test(question)) return metricId;
  return typeof context.metricId === "string" ? context.metricId : null;
}

function cleanContext(context, dashboards) {
  if (!context || typeof context !== "object" || Array.isArray(context)) return { filters: {} };
  const dashboard = context.dashboard == null ? null : String(context.dashboard);
  if (dashboard && !dashboards.has(dashboard)) {
    const error = new Error("Dashboard fora do catálogo autorizado.");
    error.code = "DASHBOARD_NOT_ALLOWED";
    throw error;
  }
  const chart = context.chart == null ? null : String(context.chart);
  if (chart && !/^[a-z0-9_-]{1,100}$/i.test(chart)) {
    const error = new Error("Contexto de chart inválido.");
    error.code = "INVALID_CHART_CONTEXT";
    throw error;
  }
  return { dashboard, chart, metricId: context.metricId, filters: context.filters || {} };
}

function structuredMessages(question, history = []) {
  const safeHistory = Array.isArray(history) ? history.slice(-6) : [];
  return [
    ...safeHistory
      .filter(item => ["user", "assistant"].includes(item?.role) && typeof item?.content === "string")
      .map(item => ({ role: item.role, content: item.content.slice(0, 1000) })),
    { role: "user", content: question },
  ];
}

export class AnalyticsOrchestrator {
  constructor({ tools, provider, catalog, dashboards = [] }) {
    this.tools = tools;
    this.provider = provider;
    this.catalog = catalog;
    this.dashboards = new Set(dashboards);
  }

  async answer({ question, tenantId, tenantName, context = {}, history = [] }) {
    const message = String(question || "").trim();
    if (!message || message.length > 1000) {
      const error = new Error("A pergunta deve conter entre 1 e 1000 caracteres.");
      error.code = "INVALID_QUESTION";
      throw error;
    }
    const safeContext = cleanContext(context, this.dashboards);
    if (POLICY_ATTACK.test(message)) {
      return {
        answer: "Não posso alterar tenant, executar SQL livre, acessar outros clientes ou revelar credenciais. O contexto permanece definido pela sessão NeoRetail.",
        intent: "policy_refusal",
        toolCalled: null,
        evidence: [{ tenantId, tenantName, governanceStatus: "authorization_enforced" }],
      };
    }

    const metricId = metricFromQuestion(message, safeContext);
    const filters = safeContext.filters;
    let intent;
    let toolCalled;
    let result;
    let evidence;

    if (/causas?|motivos?/i.test(message) && /osa/i.test(message)) {
      intent = "osa_causes";
      toolCalled = "get_osa_causes";
      result = await this.tools.getOsaCauses({ tenantId, filters });
      evidence = { source: result.source, technicalStatus: "discovery", businessStatus: "pending" };
    } else if (/tarefas?/i.test(message) && /estoque|crític|critic/i.test(message)) {
      intent = "stock_tasks";
      toolCalled = "get_stock_tasks";
      result = await this.tools.getStockTasks({ tenantId, filters });
      evidence = { source: result.source, technicalStatus: "discovery", businessStatus: "pending" };
    } else if (/onde|maior|ranking|principais/i.test(message) && ["tvd", "ivd"].includes(metricId)) {
      intent = "top_opportunities";
      toolCalled = "get_top_opportunities";
      result = await this.tools.getTopOpportunities({ tenantId, metricId, filters });
      evidence = metricGovernance(metricId, this.catalog.metrics[metricId], result.source);
    } else if (/\btvd\b/i.test(message) && /\bivd\b/i.test(message)) {
      intent = "multi_metric";
      toolCalled = "get_metric";
      const items = await Promise.all(["tvd", "ivd"].map(async id => {
        const item = await this.tools.getMetric({ metricId: id, tenantId, filters });
        return { metricId: id, displayName: item.evidence.displayName, value: item.value, format: item.format, snapshot: item.snapshot, source: item.evidence.source };
      }));
      result = { items, period: "MTD" };
      evidence = { source: items.map(item => item.source).join(", "), technicalStatus: "mixed", businessStatus: "pending", temporalStatus: "PARCIAL_CALENDARIO" };
    } else {
      if (!metricId || !this.catalog.metrics[metricId]) {
        return {
          answer: "Ainda não consigo responder essa pergunta no escopo governado. Posso ajudar com Vendas, OSA, TVD, IVD e Estoque.",
          intent: "unsupported",
          toolCalled: null,
          evidence: [{ tenantId, tenantName, governanceStatus: "unsupported_intent" }],
        };
      }
      if (/como .*calcul|o que (é|e|significa)|definição|definicao/i.test(message)) {
        intent = "explain_metric";
        toolCalled = "explain_metric";
        result = this.tools.explainMetric(metricId);
        evidence = result.evidence;
      } else if (/certific|pendente|governan|status/i.test(message)) {
        intent = "metric_governance";
        toolCalled = "get_metric_governance";
        evidence = this.tools.getMetricGovernance(metricId);
        result = evidence;
      } else if (/compar|m[eê]s anterior|caiu|subiu|varia/i.test(message)) {
        intent = "metric_comparison";
        toolCalled = "get_metric_comparison";
        result = await this.tools.getMetricComparison({ metricId, tenantId, filters });
        evidence = result.evidence;
      } else {
        intent = "metric_value";
        toolCalled = "get_metric";
        result = await this.tools.getMetric({ metricId, tenantId, filters });
        evidence = result.evidence;
      }
    }

    const immutableContext = {
      intent,
      result,
      evidence,
      tenant: { id: tenantId, name: tenantName },
      filters,
      authorization: "trusted_session",
    };
    const answer = await this.provider.generate(structuredMessages(message, history), immutableContext);
    return {
      answer,
      intent,
      toolCalled,
      metricId: metricId || null,
      evidence: [{
        tenantId,
        tenantName,
        period: result?.period || null,
        filters,
        source: evidence?.source || result?.source || null,
        formulaVersion: evidence?.formulaVersion || null,
        technicalStatus: evidence?.technicalStatus || null,
        businessStatus: evidence?.businessStatus || null,
        temporalStatus: evidence?.temporalStatus || null,
        additionalStatuses: evidence?.additionalStatuses || [],
        validator: evidence?.evidence?.validator || null,
        contract: evidence?.evidence?.contract || null,
        snapshot: result?.snapshot || null,
      }],
    };
  }
}
