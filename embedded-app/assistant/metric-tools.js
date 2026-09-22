import { metricDefinition, metricGovernance } from "./catalog.js";

const PERIODS = new Set(["MTD", "M-1", "U3M"]);
const MAX_ROWS = 10;
const HISTORY_FILTERS = ["rede", "bandeira", "uf", "cidade", "tipo_local", "loja", "regiao", "item", "descricao_marca", "hierarquia_1", "hierarquia_2", "hierarquia_3"];
const OPPORTUNITY_FILTERS = [...HISTORY_FILTERS, "deposito"];

const METRIC_QUERIES = Object.freeze({
  sales: {
    source: "gold.nr_overview_history",
    expression: "CASE WHEN SUM(faturamento) > 0 THEN SUM(faturamento) ELSE SUM(volume_unidades * avg_sales_price) END",
    dateColumn: "data",
    grain: "month",
    filters: HISTORY_FILTERS,
  },
  percentual_osa: {
    source: "gold.nr_overview_history",
    expression: "100.0 * (1 - SUM(qtd_problemas_osa) / NULLIF(SUM(qtd_item_ativo_osa), 0))",
    dateColumn: "data",
    grain: "month",
    filters: HISTORY_FILTERS,
  },
  tvd: {
    source: "gold.nr_tvd_daily",
    expression: "SUM(tvd)",
    dateColumn: "data",
    grain: "latest_day_by_month",
    filters: OPPORTUNITY_FILTERS,
  },
  ivd: {
    source: "gold.nr_panorama_opportunities",
    expression: "SUM(ivd_simplificado)",
    dateColumn: "data",
    grain: "latest_day_by_month",
    filters: OPPORTUNITY_FILTERS,
  },
  stock: {
    source: "gold.nr_overview_history",
    expression: "SUM(estoque_unidades)",
    dateColumn: "data",
    grain: "month",
    filters: HISTORY_FILTERS,
  },
});

function toolError(code, message) {
  const error = new Error(message);
  error.code = code;
  return error;
}

function assertTenant(tenantId) {
  if (!Number.isSafeInteger(tenantId) || tenantId <= 0) {
    throw toolError("INVALID_TRUSTED_TENANT", "Tenant confiável inválido.");
  }
}

function normalizePeriod(period) {
  const value = String(period || "MTD").toUpperCase();
  if (!PERIODS.has(value)) throw toolError("PERIOD_NOT_ALLOWED", "Período não permitido.");
  return value;
}

function buildFilters(catalog, filters, params, allowedColumns = null) {
  if (!filters || typeof filters !== "object" || Array.isArray(filters)) return "";
  const clauses = [];
  for (const [key, rawValue] of Object.entries(filters)) {
    const column = catalog.filters[key];
    if (!column || (allowedColumns && !allowedColumns.has(column))) {
      throw toolError("FILTER_NOT_ALLOWED", `Filtro não permitido: ${key}`);
    }
    const values = Array.isArray(rawValue) ? rawValue : [rawValue];
    if (!values.length || values.length > 20 || values.some(value => typeof value !== "string" || value.length > 120)) {
      throw toolError("INVALID_FILTER", `Valor inválido para o filtro ${key}.`);
    }
    const placeholders = values.map(value => {
      params.push(value);
      return `$${params.length}`;
    });
    clauses.push(`${column} IN (${placeholders.join(", ")})`);
  }
  return clauses.length ? ` AND ${clauses.join(" AND ")}` : "";
}

export class MetricTools {
  constructor({ catalog, query }) {
    this.catalog = catalog;
    this.query = query;
  }

  async getMetric({ metricId, tenantId, period = "MTD", filters = {} }) {
    assertTenant(tenantId);
    const normalizedPeriod = normalizePeriod(period);
    const metric = metricDefinition(this.catalog, metricId);
    const query = METRIC_QUERIES[metricId];
    if (!query || query.source !== metric.source) throw toolError("METRIC_CONTRACT_MISMATCH", "Contrato de métrica inconsistente.");
    const params = [tenantId];
    const filterSql = buildFilters(this.catalog, filters, params, new Set(query.filters));
    const sql = query.grain === "latest_day_by_month"
      ? `WITH daily AS (
          SELECT ${query.dateColumn}::date AS period_date, ${query.expression} AS value
          FROM ${query.source}
          WHERE id_customer = $1${filterSql}
          GROUP BY 1
        ), ranked AS (
          SELECT period_date, value,
            ROW_NUMBER() OVER (PARTITION BY DATE_TRUNC('month', period_date) ORDER BY period_date DESC) AS row_number
          FROM daily
        ) SELECT period_date, value FROM ranked WHERE row_number = 1 ORDER BY period_date DESC LIMIT 4`
      : `SELECT DATE_TRUNC('month', ${query.dateColumn})::date AS period_date, ${query.expression} AS value
          FROM ${query.source}
          WHERE id_customer = $1${filterSql}
          GROUP BY 1 ORDER BY period_date DESC LIMIT 4`;
    const response = await this.query(sql, params);
    const rows = response.rows || [];
    const selected = normalizedPeriod === "MTD" ? rows.slice(0, 1)
      : normalizedPeriod === "M-1" ? rows.slice(1, 2) : rows.slice(1, 4);
    const values = selected
      .map(row => row.value === null || row.value === undefined ? null : Number(row.value))
      .filter(value => value !== null);
    const value = normalizedPeriod === "U3M"
      ? (values.length ? values.reduce((sum, item) => sum + item, 0) / values.length : null)
      : (values[0] ?? null);
    return {
      metricId,
      period: normalizedPeriod,
      value,
      snapshot: selected[0]?.period_date || null,
      format: metric.format,
      filters,
      evidence: metricGovernance(metricId, metric),
    };
  }

  async getMetricComparison({ metricId, tenantId, currentPeriod = "MTD", comparisonPeriod = "M-1", filters = {} }) {
    const current = await this.getMetric({ metricId, tenantId, period: currentPeriod, filters });
    const previous = await this.getMetric({ metricId, tenantId, period: comparisonPeriod, filters });
    const variation = current.value === null || previous.value === null ? null : current.value - previous.value;
    return {
      metricId,
      period: current.period,
      comparisonPeriod: previous.period,
      current: current.value,
      previous: previous.value,
      variation,
      format: current.format,
      snapshot: current.snapshot,
      filters,
      evidence: current.evidence,
    };
  }

  async getMetricTimeseries({ metricId, tenantId, filters = {} }) {
    assertTenant(tenantId);
    const metric = metricDefinition(this.catalog, metricId);
    const query = METRIC_QUERIES[metricId];
    const params = [tenantId];
    const filterSql = buildFilters(this.catalog, filters, params, new Set(query.filters));
    const sql = `SELECT DATE_TRUNC('month', ${query.dateColumn})::date AS period, ${query.expression} AS value
      FROM ${query.source}
      WHERE id_customer = $1${filterSql}
      GROUP BY 1 ORDER BY 1 DESC LIMIT 12`;
    const response = await this.query(sql, params);
    return {
      metricId,
      rows: (response.rows || []).map(row => ({ period: row.period, value: row.value === null ? null : Number(row.value) })),
      format: metric.format,
      filters,
      evidence: metricGovernance(metricId, metric),
    };
  }

  async getOsaCauses({ tenantId, filters = {}, limit = 5 }) {
    assertTenant(tenantId);
    const safeLimit = Math.min(Math.max(Number(limit) || 5, 1), MAX_ROWS);
    const params = [tenantId];
    const filterSql = buildFilters(this.catalog, filters, params, new Set(HISTORY_FILTERS));
    params.push(safeLimit);
    const sql = `WITH latest AS (
      SELECT MAX(data)::date AS data FROM gold.nr_osa_industry_causes WHERE id_customer = $1
    ) SELECT COALESCE(causa, motivo, 'Não identificado') AS label,
      SUM(COALESCE(perda_osa_valor, 0)) AS value
      FROM gold.nr_osa_industry_causes source CROSS JOIN latest
      WHERE source.id_customer = $1 AND source.data::date = latest.data${filterSql}
      GROUP BY 1 ORDER BY value DESC NULLS LAST LIMIT $${params.length}`;
    const response = await this.query(sql, params);
    return { title: "Maiores causas de perda OSA", rows: mapRankRows(response.rows), format: "currency", source: "gold.nr_osa_industry_causes", filters };
  }

  async getStockTasks({ tenantId, filters = {}, limit = 5 }) {
    assertTenant(tenantId);
    const safeLimit = Math.min(Math.max(Number(limit) || 5, 1), MAX_ROWS);
    const params = [tenantId];
    const filterSql = buildFilters(this.catalog, filters, params, new Set(OPPORTUNITY_FILTERS));
    params.push(safeLimit);
    const sql = `SELECT COALESCE(item, deposito, 'Não identificado') AS label,
      SUM(COALESCE(tvd, 0) + COALESCE(ivd, 0)) AS value
      FROM gold.nr_stock_tasks source
      WHERE source.id_customer = $1${filterSql}
        AND (COALESCE(tvd, 0) > 0 OR COALESCE(ivd, 0) > 0)
      GROUP BY 1 ORDER BY value DESC NULLS LAST LIMIT $${params.length}`;
    const response = await this.query(sql, params);
    return { title: "Tarefas de estoque mais críticas", rows: mapRankRows(response.rows), format: "currency", source: "gold.nr_stock_tasks", filters };
  }

  async getTopOpportunities({ tenantId, metricId = "tvd", filters = {}, limit = 5 }) {
    assertTenant(tenantId);
    if (!["tvd", "ivd"].includes(metricId)) throw toolError("METRIC_NOT_ALLOWED", "Oportunidade não permitida.");
    const safeLimit = Math.min(Math.max(Number(limit) || 5, 1), MAX_ROWS);
    const params = [tenantId];
    const filterSql = buildFilters(this.catalog, filters, params, new Set(OPPORTUNITY_FILTERS));
    params.push(safeLimit);
    const column = metricId === "tvd" ? "tvd_simplificado" : "ivd_simplificado";
    const sql = `SELECT COALESCE(item, rede, 'Não identificado') AS label, SUM(COALESCE(${column}, 0)) AS value
      FROM gold.nr_panorama_opportunities_latest source
      WHERE source.id_customer = $1${filterSql}
      GROUP BY 1 ORDER BY value DESC NULLS LAST LIMIT $${params.length}`;
    const response = await this.query(sql, params);
    return { title: `Maiores oportunidades de ${metricId.toUpperCase()}`, rows: mapRankRows(response.rows), format: "currency", source: "gold.nr_panorama_opportunities_latest", filters };
  }

  explainMetric(metricId) {
    const metric = metricDefinition(this.catalog, metricId);
    return { description: metric.description, formula: metric.formula, evidence: metricGovernance(metricId, metric) };
  }

  getMetricGovernance(metricId) {
    const metric = metricDefinition(this.catalog, metricId);
    return metricGovernance(metricId, metric);
  }
}

function mapRankRows(rows = []) {
  return rows.map(row => ({ label: String(row.label), value: row.value === null ? null : Number(row.value) }));
}

export const metricQueryContracts = METRIC_QUERIES;
