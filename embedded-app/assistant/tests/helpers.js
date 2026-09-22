export const catalog = {
  metrics: {
    sales: {
      display_name: "Vendas", formula_version: "v1", formula: "SUM(faturamento)",
      description: "Venda", source: "gold.nr_overview_history", periods: ["MTD", "M-1", "U3M"],
      format: "currency", statuses: { technical: "discovery", business: "pending", temporal: "PARCIAL_CALENDARIO" },
      ai: { query_allowed: true, explain_allowed: true },
    },
    percentual_osa: {
      display_name: "% OSA", formula_version: "v1", formula: "100 * razão", description: "OSA",
      source: "gold.nr_overview_history", periods: ["MTD", "M-1", "U3M"], format: "percent",
      statuses: { technical: "discovery", business: "pending", temporal: "PARCIAL_CALENDARIO" },
      ai: { query_allowed: true, explain_allowed: true },
    },
    tvd: {
      display_name: "TVD", formula_version: "v1", formula: "SUM(tvd)", description: "TVD",
      source: "gold.nr_tvd_daily", periods: ["MTD", "M-1", "U3M"], format: "currency",
      statuses: { technical: "discovery", business: "pending" }, ai: { query_allowed: true, explain_allowed: true },
    },
    ivd: {
      display_name: "IVD", formula_version: "v1", formula: "SUM(ivd)", description: "IVD",
      source: "gold.nr_panorama_opportunities", periods: ["MTD", "M-1", "U3M"], format: "currency",
      statuses: { technical: "discovery", business: "pending" }, ai: { query_allowed: true, explain_allowed: true },
    },
    stock: {
      display_name: "Estoque", formula_version: "v1", formula: "SUM(estoque)", description: "Estoque",
      source: "gold.nr_overview_history", periods: ["MTD", "M-1", "U3M"], format: "number",
      statuses: { technical: "discovery", business: "pending" }, ai: { query_allowed: true, explain_allowed: true },
    },
  },
  filters: { rede: "rede", uf: "uf", item: "item" },
};

export function fakeProvider() {
  return {
    name: "mock", model: "test",
    async health() { return { available: true, provider: "mock", model: "test" }; },
    async generate(_messages, context) { return `intent=${context.intent}`; },
  };
}
