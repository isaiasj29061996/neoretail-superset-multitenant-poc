import fs from "node:fs";
import YAML from "yaml";

export function loadMetricCatalog(filePath) {
  const catalog = YAML.parse(fs.readFileSync(filePath, "utf8"));
  if (!catalog?.metrics || !catalog?.filters) {
    throw new Error("Catálogo semântico do assistente inválido.");
  }
  return Object.freeze(catalog);
}

export function metricDefinition(catalog, metricId) {
  const metric = catalog.metrics[String(metricId || "")];
  if (!metric || metric.ai?.query_allowed !== true) {
    const error = new Error("Métrica não permitida pelo catálogo governado.");
    error.code = "METRIC_NOT_ALLOWED";
    throw error;
  }
  return metric;
}

export function metricGovernance(metricId, metric) {
  return {
    metricId,
    displayName: metric.display_name,
    source: metric.source,
    formulaVersion: metric.formula_version,
    technicalStatus: metric.statuses?.technical || "unknown",
    businessStatus: metric.statuses?.business || "unknown",
    temporalStatus: metric.statuses?.temporal || null,
    owners: metric.owners || {},
    evidence: metric.evidence || {},
  };
}
