import assert from "node:assert/strict";
import test from "node:test";
import { MetricTools, metricQueryContracts } from "../metric-tools.js";
import { catalog } from "./helpers.js";

test("metric query binds tenant and filters and reports the actual filtered mart", async () => {
  const calls = [];
  const tools = new MetricTools({ catalog, query: async (sql, params) => {
    calls.push({ sql, params });
    return { rows: [{ period_date: "2026-09-01", component_1: "25.88", component_2: "100" }] };
  } });
  const result = await tools.getMetric({ metricId: "percentual_osa", tenantId: 142, filters: { rede: "REDE-SECRETA" } });
  assert.equal(result.value, 74.12);
  assert.equal(result.evidence.source, "gold.nr_overview_quantity_detail");
  assert.deepEqual(calls[0].params, [142, "REDE-SECRETA"]);
  assert.match(calls[0].sql, /id_customer = \$1/);
  assert.match(calls[0].sql, /rede IN \(\$2\)/);
  assert.doesNotMatch(calls[0].sql, /REDE-SECRETA/);
});

test("default query uses compact semantic mart and fixed unidade measure", async () => {
  let call;
  const tools = new MetricTools({ catalog, query: async (sql, params) => {
    call = { sql, params };
    return { rows: [{ period_date: "2026-09-01", component_1: "10" }] };
  } });
  const result = await tools.getMetric({ metricId: "sales", tenantId: 142 });
  assert.equal(result.evidence.source, "gold.nr_overview_quantity_default");
  assert.match(call.sql, /nm_measure = 'unidade'/);
  assert.deepEqual(call.params, [142]);
});

test("trusted tenant is mandatory and unknown filters are rejected", async () => {
  const tools = new MetricTools({ catalog, query: async () => ({ rows: [] }) });
  await assert.rejects(() => tools.getMetric({ metricId: "sales", tenantId: null }), { code: "INVALID_TRUSTED_TENANT" });
  await assert.rejects(() => tools.getMetric({ metricId: "sales", tenantId: 142, filters: { id_customer: "259" } }), { code: "FILTER_NOT_ALLOWED" });
  await assert.rejects(() => tools.getMetric({ metricId: "secret_metric", tenantId: 142 }), { code: "METRIC_NOT_ALLOWED" });
  await assert.rejects(() => tools.getMetric({ metricId: "sales", tenantId: 142, period: "ALL" }), { code: "PERIOD_NOT_ALLOWED" });
});

test("period selection uses exact month offsets and U3M keeps the fixed divisor three", async () => {
  const rows = [
    { period_date: "2026-09-01", component_1: "100" },
    { period_date: "2026-08-01", component_1: "80" },
    { period_date: "2026-06-01", component_1: "60" },
  ];
  const tools = new MetricTools({ catalog, query: async () => ({ rows }) });
  assert.equal((await tools.getMetric({ metricId: "sales", tenantId: 142, period: "MTD" })).value, 100);
  assert.equal((await tools.getMetric({ metricId: "sales", tenantId: 142, period: "M-1" })).value, 80);
  assert.equal((await tools.getMetric({ metricId: "sales", tenantId: 142, period: "U3M" })).value, (80 + 60) / 3);
});

test("OSA recomposes additive components for MTD, M-1 and U3M", async () => {
  const rows = [
    { period_date: "2026-09-01", component_1: "25.873091", component_2: "100" },
    { period_date: "2026-08-01", component_1: "24.576818", component_2: "100" },
    { period_date: "2026-07-01", component_1: "30", component_2: "100" },
    { period_date: "2026-06-01", component_1: "27.36097", component_2: "100" },
  ];
  const tools = new MetricTools({ catalog, query: async () => ({ rows }) });
  assert.ok(Math.abs((await tools.getMetric({ metricId: "percentual_osa", tenantId: 142, period: "MTD" })).value - 74.126909) < 1e-9);
  assert.ok(Math.abs((await tools.getMetric({ metricId: "percentual_osa", tenantId: 142, period: "M-1" })).value - 75.423182) < 1e-9);
  assert.ok(Math.abs((await tools.getMetric({ metricId: "percentual_osa", tenantId: 142, period: "U3M" })).value - 72.687404) < 1e-9);
});

test("BLANK is preserved for a zero denominator and comparison does not fabricate variation", async () => {
  const tools = new MetricTools({ catalog, query: async () => ({ rows: [{ period_date: "2026-09-01", component_1: "0", component_2: "0" }] }) });
  assert.equal((await tools.getMetric({ metricId: "percentual_osa", tenantId: 142 })).value, null);
  assert.equal((await tools.getMetricComparison({ metricId: "percentual_osa", tenantId: 142 })).variation, null);
});

test("all numeric sources and filtered sources are fixed allowlisted marts", () => {
  assert.deepEqual(Object.keys(metricQueryContracts).sort(), ["ivd", "percentual_osa", "sales", "stock", "tvd"]);
  for (const contract of Object.values(metricQueryContracts)) {
    assert.match(contract.source, /^gold\.nr_[a-z_]+$/);
    assert.match(contract.filteredSource, /^gold\.nr_[a-z_]+$/);
    for (const expression of [...contract.defaultComponents, ...contract.filteredComponents]) assert.doesNotMatch(expression, /;|--|\/\*/);
  }
});

test("TVD and IVD select compact defaults and detail marts only when filtered", async () => {
  const calls = [];
  const tools = new MetricTools({ catalog, query: async sql => { calls.push(sql); return { rows: [] }; } });
  await tools.getMetric({ metricId: "tvd", tenantId: 142 });
  await tools.getMetric({ metricId: "ivd", tenantId: 142, filters: { uf: "SP" } });
  assert.match(calls[0], /gold\.nr_tvd_daily_summary/);
  assert.match(calls[1], /gold\.nr_ivd_daily/);
  assert.match(calls[1], /target_dates/);
  assert.match(calls[1], /JOIN target_dates/);
  assert.match(calls[1], /FROM gold\.nr_ivd_daily source JOIN target_dates/);
});

test("rankings have a hard maximum row limit", async () => {
  const calls = [];
  const tools = new MetricTools({ catalog, query: async (sql, params) => { calls.push({ sql, params }); return { rows: [{ label: "A", value: "10" }] }; } });
  await tools.getOsaCauses({ tenantId: 142, limit: 999 });
  assert.equal(calls[0].params.at(-1), 10);
  assert.match(calls[0].sql, /LIMIT \$2/);
});
