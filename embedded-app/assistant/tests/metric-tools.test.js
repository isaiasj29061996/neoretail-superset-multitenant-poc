import assert from "node:assert/strict";
import test from "node:test";
import { MetricTools, metricQueryContracts } from "../metric-tools.js";
import { catalog } from "./helpers.js";

test("metric query binds tenant and filters instead of interpolating values", async () => {
  const calls = [];
  const tools = new MetricTools({
    catalog,
    query: async (sql, params) => {
      calls.push({ sql, params });
      return { rows: [{ period_date: "2026-09-01", value: "74.12" }] };
    },
  });
  const result = await tools.getMetric({ metricId: "percentual_osa", tenantId: 142, filters: { rede: "REDE-SECRETA" } });
  assert.equal(result.value, 74.12);
  assert.deepEqual(calls[0].params, [142, "REDE-SECRETA"]);
  assert.match(calls[0].sql, /id_customer = \$1/);
  assert.match(calls[0].sql, /rede IN \(\$2\)/);
  assert.doesNotMatch(calls[0].sql, /REDE-SECRETA/);
});

test("trusted tenant is mandatory and unknown filters are rejected", async () => {
  const tools = new MetricTools({ catalog, query: async () => ({ rows: [] }) });
  await assert.rejects(() => tools.getMetric({ metricId: "sales", tenantId: null }), { code: "INVALID_TRUSTED_TENANT" });
  await assert.rejects(() => tools.getMetric({ metricId: "sales", tenantId: 142, filters: { id_customer: "259" } }), { code: "FILTER_NOT_ALLOWED" });
  await assert.rejects(() => tools.getMetric({ metricId: "secret_metric", tenantId: 142 }), { code: "METRIC_NOT_ALLOWED" });
  await assert.rejects(() => tools.getMetric({ metricId: "sales", tenantId: 142, period: "ALL" }), { code: "PERIOD_NOT_ALLOWED" });
});

test("periods follow the existing latest, previous and prior-three contract", async () => {
  const rows = [
    { period_date: "2026-09-01", value: "100" },
    { period_date: "2026-08-01", value: "80" },
    { period_date: "2026-07-01", value: "70" },
    { period_date: "2026-06-01", value: "60" },
  ];
  const tools = new MetricTools({ catalog, query: async () => ({ rows }) });
  assert.equal((await tools.getMetric({ metricId: "sales", tenantId: 142, period: "MTD" })).value, 100);
  assert.equal((await tools.getMetric({ metricId: "sales", tenantId: 142, period: "M-1" })).value, 80);
  assert.equal((await tools.getMetric({ metricId: "sales", tenantId: 142, period: "U3M" })).value, 70);
});

test("BLANK is preserved and comparison does not fabricate variation", async () => {
  const tools = new MetricTools({ catalog, query: async () => ({ rows: [{ period_date: "2026-09-01", value: null }] }) });
  const value = await tools.getMetric({ metricId: "percentual_osa", tenantId: 142 });
  assert.equal(value.value, null);
  const comparison = await tools.getMetricComparison({ metricId: "percentual_osa", tenantId: 142 });
  assert.equal(comparison.variation, null);
});

test("all numeric sources are fixed allowlisted marts", () => {
  assert.deepEqual(Object.keys(metricQueryContracts).sort(), ["ivd", "percentual_osa", "sales", "stock", "tvd"]);
  for (const contract of Object.values(metricQueryContracts)) {
    assert.match(contract.source, /^gold\.nr_[a-z_]+$/);
    assert.doesNotMatch(contract.expression, /;|--|\/\*/);
  }
});

test("rankings have a hard maximum row limit", async () => {
  const calls = [];
  const tools = new MetricTools({ catalog, query: async (sql, params) => {
    calls.push({ sql, params });
    return { rows: [{ label: "A", value: "10" }] };
  } });
  await tools.getOsaCauses({ tenantId: 142, limit: 999 });
  assert.equal(calls[0].params.at(-1), 10);
  assert.match(calls[0].sql, /LIMIT \$2/);
});
