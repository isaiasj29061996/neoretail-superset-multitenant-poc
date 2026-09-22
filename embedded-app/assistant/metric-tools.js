import { metricDefinition, metricGovernance } from "./catalog.js";

const PERIODS = new Set(["MTD", "M-1", "U3M"]);
const MAX_ROWS = 10;
const HISTORY_FILTERS = ["rede", "bandeira", "uf", "cidade", "tipo_local", "loja", "regiao", "item", "descricao_marca", "hierarquia_1", "hierarquia_2", "hierarquia_3"];
const OPPORTUNITY_FILTERS = [...HISTORY_FILTERS, "deposito"];

const METRIC_QUERIES = Object.freeze({
  sales: {
    source: "gold.nr_overview_quantity_default", filteredSource: "gold.nr_overview_quantity_detail",
    profile: "direct_average", defaultMeasure: "unidade", defaultComponents: ["SUM(sales_sum)"],
    filteredComponents: ["SUM(volume_unidades) * MAX(conversion_factor)"], dateColumn: "data", grain: "month", filters: HISTORY_FILTERS,
  },
  percentual_osa: {
    source: "gold.nr_overview_quantity_default", filteredSource: "gold.nr_overview_quantity_detail",
    profile: "one_minus_ratio", defaultMeasure: "unidade", defaultComponents: ["SUM(osa_problem_sum)", "SUM(osa_active_sum)"],
    filteredComponents: ["SUM(qtd_problemas_osa)", "SUM(qtd_item_ativo_osa)"], dateColumn: "data", grain: "month", filters: HISTORY_FILTERS,
  },
  tvd: {
    source: "gold.nr_tvd_daily_summary", filteredSource: "gold.nr_tvd_daily", profile: "direct_average",
    defaultComponents: ["SUM(tvd)"], filteredComponents: ["SUM(tvd)"], dateColumn: "data", grain: "latest_day_by_month", filters: OPPORTUNITY_FILTERS,
  },
  ivd: {
    source: "gold.nr_ivd_daily_summary", filteredSource: "gold.nr_ivd_daily", profile: "direct_average",
    defaultComponents: ["SUM(ivd)"], filteredComponents: ["SUM(ivd)"], dateColumn: "data", grain: "latest_day_by_month", filters: OPPORTUNITY_FILTERS,
  },
  stock: {
    source: "gold.nr_overview_quantity_default", filteredSource: "gold.nr_overview_quantity_detail",
    profile: "direct_average", defaultMeasure: "unidade", defaultComponents: ["SUM(stock_sum)"],
    filteredComponents: ["SUM(estoque_unidades)"], dateColumn: "data", grain: "month", filters: HISTORY_FILTERS,
  },
});

function toolError(code, message) { const error = new Error(message); error.code = code; return error; }
function assertTenant(tenantId) {
  if (!Number.isSafeInteger(tenantId) || tenantId <= 0) throw toolError("INVALID_TRUSTED_TENANT", "Tenant confiável inválido.");
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
    if (!column || (allowedColumns && !allowedColumns.has(column))) throw toolError("FILTER_NOT_ALLOWED", `Filtro não permitido: ${key}`);
    const values = Array.isArray(rawValue) ? rawValue : [rawValue];
    if (!values.length || values.length > 20 || values.some(value => typeof value !== "string" || value.length > 120)) {
      throw toolError("INVALID_FILTER", `Valor inválido para o filtro ${key}.`);
    }
    const placeholders = values.map(value => { params.push(value); return `$${params.length}`; });
    clauses.push(`${column} IN (${placeholders.join(", ")})`);
  }
  return clauses.length ? ` AND ${clauses.join(" AND ")}` : "";
}
function hasFilters(filters) { return Boolean(filters && typeof filters === "object" && !Array.isArray(filters) && Object.keys(filters).length); }
function componentSelect(expressions) { return expressions.map((expression, index) => `${expression} AS component_${index + 1}`).join(", "); }

function buildMetricSql(contract, catalog, filters, params) {
  const filtered = hasFilters(filters);
  const source = filtered ? contract.filteredSource : contract.source;
  const filterSql = buildFilters(catalog, filters, params, new Set(contract.filters));
  const measureSql = !filtered && contract.defaultMeasure ? ` AND nm_measure = '${contract.defaultMeasure}'` : "";
  let aggregate;
  if (filtered && contract === METRIC_QUERIES.sales) {
    aggregate = `WITH filtered AS (
      SELECT * FROM ${source} WHERE id_customer = $1${filterSql}
    ), monthly AS (
      SELECT DATE_TRUNC('month', data)::date AS period_date,
        SUM(COALESCE(volume_unidades, 0))::double precision AS volume_sum
      FROM filtered GROUP BY 1
    ), factors AS (
      SELECT DATE_TRUNC('month', d.data)::date AS period_date,
        MAX(c.conversion_rate)::double precision AS conversion_factor
      FROM (SELECT DISTINCT data, id_customer, id_item FROM filtered) d
      JOIN gold.dim_conversao c
        ON c.id_customer = d.id_customer AND c.id_item::text = d.id_item AND c.nm_measure = 'unidade'
      GROUP BY 1
    ) SELECT m.period_date, (m.volume_sum * f.conversion_factor)::double precision AS component_1
      FROM monthly m JOIN factors f USING (period_date)`;
  } else {
    const expressions = filtered ? contract.filteredComponents : contract.defaultComponents;
    aggregate = `SELECT DATE_TRUNC('month', ${contract.dateColumn})::date AS period_date,
      ${componentSelect(expressions)} FROM ${source}
      WHERE id_customer = $1${measureSql}${filterSql} GROUP BY 1`;
  }
  if (contract.grain === "latest_day_by_month") {
    const expressions = filtered ? contract.filteredComponents : contract.defaultComponents;
    aggregate = `WITH ranked_dates AS (
      SELECT ${contract.dateColumn}::date AS observation_date,
        ROW_NUMBER() OVER (PARTITION BY DATE_TRUNC('month', ${contract.dateColumn}) ORDER BY ${contract.dateColumn} DESC) AS row_number
      FROM ${contract.source} WHERE id_customer = $1
    ), target_dates AS (
      SELECT observation_date FROM ranked_dates WHERE row_number = 1 ORDER BY observation_date DESC LIMIT 13
    ), daily AS (
      SELECT source.${contract.dateColumn}::date AS observation_date, ${componentSelect(expressions)}
      FROM ${source} source JOIN target_dates ON target_dates.observation_date = source.${contract.dateColumn}::date
      WHERE source.id_customer = $1${filterSql} GROUP BY 1
    ) SELECT observation_date AS period_date,
      ${expressions.map((_expression, index) => `component_${index + 1}`).join(", ")}
      FROM daily`;
  }
  return { sql: `${aggregate} ORDER BY period_date DESC LIMIT 13`, source };
}

function numberOrNull(value) { return value === null || value === undefined ? null : Number(value); }
function monthKey(value) {
  if (value instanceof Date) return `${value.getUTCFullYear()}-${String(value.getUTCMonth() + 1).padStart(2, "0")}`;
  const match = String(value || "").match(/^(\d{4})-(\d{2})/);
  return match ? `${match[1]}-${match[2]}` : null;
}
function normalizeRows(rows = []) {
  return rows.map(row => ({
    periodDate: row.period_date, monthKey: monthKey(row.period_date),
    components: Object.keys(row).filter(key => /^component_\d+$/.test(key))
      .sort((a, b) => Number(a.split("_")[1]) - Number(b.split("_")[1])).map(key => numberOrNull(row[key])),
  }));
}
function shiftMonth(key, offset) {
  const [year, month] = key.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1 + offset, 1));
  return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, "0")}`;
}
function rowsForPeriod(rows, period) {
  if (!rows.length || !rows[0].monthKey) return [];
  const anchor = rows[0].monthKey;
  const offsets = period === "MTD" ? [0] : period === "M-1" ? [-1] : [-1, -2, -3];
  const byMonth = new Map(rows.map(row => [row.monthKey, row]));
  return offsets.map(offset => byMonth.get(shiftMonth(anchor, offset))).filter(Boolean);
}
function semanticValue(profile, components) {
  if (profile === "one_minus_ratio") {
    const [numerator, denominator] = components;
    if (numerator === null || denominator === null || denominator === 0) return null;
    return 100 * (1 - numerator / denominator);
  }
  return components[0] ?? null;
}
function aggregatePeriod(contract, selected, period) {
  if (!selected.length) return null;
  if (contract.profile === "one_minus_ratio") {
    if (selected.some(row => row.components[0] === null || row.components[1] === null)) return null;
    return semanticValue(contract.profile, [
      selected.reduce((sum, row) => sum + row.components[0], 0),
      selected.reduce((sum, row) => sum + row.components[1], 0),
    ]);
  }
  const values = selected.map(row => semanticValue(contract.profile, row.components)).filter(value => value !== null);
  if (!values.length) return null;
  const total = values.reduce((sum, value) => sum + value, 0);
  return period === "U3M" ? total / 3 : values[0];
}

export class MetricTools {
  constructor({ catalog, query }) { this.catalog = catalog; this.query = query; }
  contract(metricId) {
    const metric = metricDefinition(this.catalog, metricId);
    const contract = METRIC_QUERIES[metricId];
    if (!contract || contract.source !== metric.source || contract.filteredSource !== metric.filtered_source) {
      throw toolError("METRIC_CONTRACT_MISMATCH", "Contrato de métrica inconsistente.");
    }
    return { metric, contract };
  }
  async getMetric({ metricId, tenantId, period = "MTD", filters = {} }) {
    assertTenant(tenantId);
    const normalizedPeriod = normalizePeriod(period);
    const { metric, contract } = this.contract(metricId);
    const params = [tenantId];
    const queryPlan = buildMetricSql(contract, this.catalog, filters, params);
    const response = await this.query(queryPlan.sql, params);
    const selected = rowsForPeriod(normalizeRows(response.rows || []), normalizedPeriod);
    return {
      metricId, period: normalizedPeriod, value: aggregatePeriod(contract, selected, normalizedPeriod),
      snapshot: selected[0]?.periodDate || null, format: metric.format, filters,
      evidence: metricGovernance(metricId, metric, queryPlan.source),
    };
  }
  async getMetricComparison({ metricId, tenantId, currentPeriod = "MTD", comparisonPeriod = "M-1", filters = {} }) {
    const current = await this.getMetric({ metricId, tenantId, period: currentPeriod, filters });
    const previous = await this.getMetric({ metricId, tenantId, period: comparisonPeriod, filters });
    return {
      metricId, period: current.period, comparisonPeriod: previous.period, current: current.value, previous: previous.value,
      variation: current.value === null || previous.value === null ? null : current.value - previous.value,
      format: current.format, snapshot: current.snapshot, filters, evidence: current.evidence,
    };
  }
  async getMetricTimeseries({ metricId, tenantId, filters = {} }) {
    assertTenant(tenantId);
    const { metric, contract } = this.contract(metricId);
    const params = [tenantId];
    const queryPlan = buildMetricSql(contract, this.catalog, filters, params);
    const response = await this.query(queryPlan.sql, params);
    return {
      metricId,
      rows: normalizeRows(response.rows || []).slice(0, 12).map(row => ({ period: row.periodDate, value: semanticValue(contract.profile, row.components) })),
      format: metric.format, filters, evidence: metricGovernance(metricId, metric, queryPlan.source),
    };
  }
  async getOsaCauses({ tenantId, filters = {}, limit = 5 }) {
    assertTenant(tenantId);
    const safeLimit = Math.min(Math.max(Number(limit) || 5, 1), MAX_ROWS);
    const params = [tenantId];
    const filterSql = buildFilters(this.catalog, filters, params, new Set(HISTORY_FILTERS));
    params.push(safeLimit);
    const sql = `WITH latest AS (SELECT MAX(data)::date AS data FROM gold.nr_osa_industry_causes WHERE id_customer = $1)
      SELECT COALESCE(causa, motivo, 'Não identificado') AS label, SUM(COALESCE(perda_osa_valor, 0)) AS value
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
    const sql = `SELECT COALESCE(item, deposito, 'Não identificado') AS label, SUM(COALESCE(tvd, 0) + COALESCE(ivd, 0)) AS value
      FROM gold.nr_stock_tasks source WHERE source.id_customer = $1${filterSql}
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
      FROM gold.nr_panorama_opportunities_latest source WHERE source.id_customer = $1${filterSql}
      GROUP BY 1 ORDER BY value DESC NULLS LAST LIMIT $${params.length}`;
    const response = await this.query(sql, params);
    return { title: `Maiores oportunidades de ${metricId.toUpperCase()}`, rows: mapRankRows(response.rows), format: "currency", source: "gold.nr_panorama_opportunities_latest", filters };
  }
  explainMetric(metricId) {
    const metric = metricDefinition(this.catalog, metricId);
    return { description: metric.description, formula: metric.formula, evidence: metricGovernance(metricId, metric) };
  }
  getMetricGovernance(metricId) { const metric = metricDefinition(this.catalog, metricId); return metricGovernance(metricId, metric); }
}

function mapRankRows(rows = []) { return rows.map(row => ({ label: String(row.label), value: row.value === null ? null : Number(row.value) })); }
export const metricQueryContracts = METRIC_QUERIES;
