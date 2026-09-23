import { metricGovernance } from "./catalog.js";

const METRIC_PATTERNS = [
  ["percentual_osa", /\bosa\b/i],
  ["tvd", /\btvd\b|pré[- ]?ruptura/i],
  ["ivd", /\bivd\b|excesso de estoque/i],
  ["sales", /vend(a|as|emos)|sell[ -]?out|faturamento/i],
  ["stock", /\bestoque\b/i],
];

const POLICY_ATTACK = /ignore (?:suas|as) regras|ignore a governan[cç]a|agora (?:você|voce) é administrador|todos os (?:clientes|tenants)|(?:tenant|cliente|id_customer)\s*\d+|(?:troque|altere|mude).*(?:tenant|cliente)|(?:faça|faca|gere|execute).*(?:select|sql|direto no banco)|credenciais?|senhas?|connection string|(?:redefin(?:a|ir)|use outra|troque a).*(?:f[oó]rmula|m[eé]trica)|bypass.*(?:cat[aá]logo|governan[cç]a)/i;

function explicitMetric(text) {
  for (const [metricId, pattern] of METRIC_PATTERNS) if (pattern.test(String(text || ""))) return metricId;
  return null;
}

function metricFromQuestion(question, context = {}, history = []) {
  const current = explicitMetric(question);
  if (current) return current;
  if (typeof context.metricId === "string") return context.metricId;
  const safeHistory = Array.isArray(history) ? history.slice(-8).reverse() : [];
  for (const item of safeHistory) {
    const historical = explicitMetric(item?.content);
    if (historical) return historical;
  }
  return null;
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

function evidencePayload({ tenantId, tenantName, filters, result, evidence, metricId }) {
  return {
    tenantId,
    tenantName,
    metricId: metricId || null,
    period: result?.period || null,
    filters,
    source: evidence?.source || result?.source || null,
    defaultSource: evidence?.defaultSource || null,
    filteredSource: evidence?.filteredSource || null,
    formulaVersion: evidence?.formulaVersion || null,
    technicalStatus: evidence?.technicalStatus || null,
    businessStatus: evidence?.businessStatus || null,
    temporalStatus: evidence?.temporalStatus || null,
    additionalStatuses: evidence?.additionalStatuses || [],
    validator: evidence?.evidence?.validator || null,
    contract: evidence?.evidence?.contract || null,
    snapshot: result?.snapshot || null,
  };
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
        answer: "Não posso alterar o tenant, executar SQL livre, revelar credenciais ou substituir fórmulas e regras governadas. O contexto permanece definido pela sessão NeoRetail.",
        intent: "policy_refusal",
        toolCalled: null,
        metricId: explicitMetric(message),
        evidence: [{ tenantId, tenantName, governanceStatus: "authorization_enforced" }],
      };
    }

    const metricId = metricFromQuestion(message, safeContext, history);
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
    } else if (/\btvd\b/i.test(message) && /\bivd\b/i.test(message) && !/fonte|origem|mart/i.test(message)) {
      intent = "multi_metric";
      toolCalled = "get_metric";
      const items = await Promise.all(["tvd", "ivd"].map(async id => {
        const item = await this.tools.getMetric({ metricId: id, tenantId, filters });
        return { metricId: id, displayName: item.evidence.displayName, value: item.value, format: item.format, snapshot: item.snapshot, source: item.evidence.source };
      }));
      result = { items, period: "MTD" };
      evidence = { source: items.map(item => item.source).join(", "), technicalStatus: "mixed", businessStatus: "pending", temporalStatus: "PARCIAL_CALENDARIO" };
    } else if (/onde|maior|ranking|principais/i.test(message) && ["tvd", "ivd"].includes(metricId)) {
      intent = "top_opportunities";
      toolCalled = "get_top_opportunities";
      result = await this.tools.getTopOpportunities({ tenantId, metricId, filters });
      evidence = metricGovernance(metricId, this.catalog.metrics[metricId], result.source);
    } else {
      if (!metricId || !this.catalog.metrics[metricId]) {
        return {
          answer: "Ainda não consigo responder essa pergunta no escopo governado. Posso ajudar com Vendas, OSA, TVD, IVD e Estoque.",
          intent: "unsupported",
          toolCalled: null,
          metricId: null,
          evidence: [{ tenantId, tenantName, governanceStatus: "unsupported_intent" }],
        };
      }
      if (/vers[aã]o.*f[oó]rmula|f[oó]rmula.*vers[aã]o/i.test(message)) {
        intent = "metric_formula_version";
        toolCalled = "get_metric_formula_version";
        result = this.tools.getMetricFormulaVersion(metricId);
        evidence = result.evidence;
      } else if (/\bfonte\b|origem.*dados|\bmart\b/i.test(message)) {
        intent = "metric_source";
        toolCalled = "get_metric_source";
        result = this.tools.getMetricSource(metricId);
        evidence = result.evidence;
      } else if (/como .*calcul|o que (é|e|significa)|definição|definicao/i.test(message)) {
        intent = "explain_metric";
        toolCalled = "explain_metric";
        result = this.tools.explainMetric(metricId);
        evidence = result.evidence;
      } else if (/certific|pendente|governan|status.*(?:t[eé]cnic|neg[oó]cio|temporal)/i.test(message)) {
        intent = "metric_governance";
        toolCalled = "get_metric_governance";
        evidence = this.tools.getMetricGovernance(metricId);
        result = { ...evidence, certificationQuestion: /certific/i.test(message) };
      } else if (/varia[cç][aã]o|pontos? percentuais|\bp\.?p\.?\b/i.test(message)) {
        intent = "metric_variation";
        toolCalled = "get_metric_comparison";
        result = await this.tools.getMetricComparison({ metricId, tenantId, filters });
        evidence = result.evidence;
      } else if (/compar|m[eê]s anterior|caiu|subiu/i.test(message)) {
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

    const immutableContext = { intent, result, evidence, tenant: { id: tenantId, name: tenantName }, filters, authorization: "trusted_session" };
    const generated = await this.provider.generate(structuredMessages(message, history), immutableContext);
    const answer = typeof generated === "string" && generated.trim()
      ? generated.trim()
      : "Não encontrei dados para essa consulta no contexto atual.";
    return {
      answer,
      intent,
      toolCalled,
      metricId: metricId || null,
      data: result,
      evidence: [evidencePayload({ tenantId, tenantName, filters, result, evidence, metricId })],
    };
  }
}
