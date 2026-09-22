import assert from "node:assert/strict";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { loadMetricCatalog, metricGovernance } from "../catalog.js";

const here = dirname(fileURLToPath(import.meta.url));
const catalog = loadMetricCatalog(resolve(here, "../../../config/assistant_metrics.yaml"));

test("catalog maps every metric to its authoritative compact and filtered marts", () => {
  const expected = {
    sales: ["gold.nr_overview_quantity_default", "gold.nr_overview_quantity_detail", "RECONCILED"],
    percentual_osa: ["gold.nr_overview_quantity_default", "gold.nr_overview_quantity_detail", "RECONCILED"],
    stock: ["gold.nr_overview_quantity_default", "gold.nr_overview_quantity_detail", "RECONCILED"],
    tvd: ["gold.nr_tvd_daily_summary", "gold.nr_tvd_daily", "CERTIFICADA"],
    ivd: ["gold.nr_ivd_daily_summary", "gold.nr_ivd_daily", "CERTIFICADA"],
  };
  for (const [metricId, [source, filteredSource, technicalStatus]] of Object.entries(expected)) {
    const metric = catalog.metrics[metricId];
    assert.equal(metric.source, source);
    assert.equal(metric.filtered_source, filteredSource);
    assert.equal(metric.statuses.technical, technicalStatus);
    assert.equal(metric.statuses.business, "pending");
    assert.equal(metric.statuses.temporal, "PARCIAL_CALENDARIO");
    assert.ok(metric.evidence.validator);
    assert.ok(metric.evidence.contract);
  }
});

test("governance evidence records the actual source without losing the declared contract", () => {
  const metric = catalog.metrics.percentual_osa;
  const evidence = metricGovernance("percentual_osa", metric, metric.filtered_source);
  assert.equal(evidence.source, "gold.nr_overview_quantity_detail");
  assert.equal(evidence.defaultSource, "gold.nr_overview_quantity_default");
  assert.equal(evidence.filteredSource, "gold.nr_overview_quantity_detail");
  assert.equal(evidence.evidence.validator, "superset/validate_overview_quantity.py");
});
