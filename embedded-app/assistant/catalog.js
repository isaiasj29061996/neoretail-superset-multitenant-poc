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

export function metricGovernance(metricId, metric, actualSource = null) {
  return {
    metricId,
    displayName: metric.display_name,
    source: actualSource || metric.source,
    defaultSource: metric.source,
    filteredSource: metric.filtered_source || null,
    formulaVersion: metric.formula_version,
    technicalStatus: metric.statuses?.technical || "unknown",
    businessStatus: metric.statuses?.business || "unknown",
    temporalStatus: metric.statuses?.temporal || null,
    additionalStatuses: metric.statuses?.additional || [],
    owners: metric.owners || {},
    evidence: metric.evidence || {},
  };
}
