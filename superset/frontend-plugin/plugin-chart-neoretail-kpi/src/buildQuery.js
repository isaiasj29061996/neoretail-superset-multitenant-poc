import { buildQueryContext } from '@superset-ui/core';

const asArray = value => (Array.isArray(value) ? value : value ? [value] : []);

export default function buildQuery(formData, options) {
  const variant = formData.card_variant || formData.cardVariant;
  if (variant === 'kpifilters') {
    // The toolbar is a chart only to make it a first-class dashboard layout
    // component. Its dataset is tenant/RLS-scoped and returns selector options,
    // not numeric KPIs. It must ignore its own native filters (see bootstrap).
    return buildQueryContext(formData, {
      ...options,
      buildQuery: base => [{
        ...base,
        columns: [
          'comparison_year', 'comparison_month',
          'comparison_year_month', 'comparison_kpi',
        ],
        metrics: asArray(formData.metrics),
        orderby: [],
        row_limit: 2000,
        time_range: 'No filter',
      }],
    });
  }
  const xAxis = formData.x_axis;
  if (!xAxis) throw new Error('Selecione a coluna temporal no eixo X do NeoRetail KPI Card.');
  const metrics = [...asArray(formData.metrics), formData.metric, formData.critical_metric, formData.risk_metric].filter(Boolean);
  const groupby = asArray(formData.groupby);
  return buildQueryContext(formData, {
    ...options,
    buildQuery: baseQueryObject => {
      const common = {
        ...baseQueryObject,
        metrics,
        orderby: [[xAxis, true]],
        row_limit: baseQueryObject.row_limit ?? 10000,
        extras: { ...baseQueryObject.extras, time_grain_sqla: baseQueryObject.extras?.time_grain_sqla ?? 'P1M' },
      };
      if (['rankbars', 'verticalbars', 'stackedrank', 'hierarchyrank'].includes(formData.card_variant) && groupby.length) {
        return [{ ...common, columns: groupby, orderby: metrics[0] ? [[metrics[0], false]] : [], row_limit: baseQueryObject.row_limit ?? 10 }];
      }
      const timelineScope = String(formData.timeline_query_scope || '').trim();
      const summaryScope = String(formData.summary_query_scope || '').trim();
      const withScope = (query, scope, grain = common.extras.time_grain_sqla) => ({
        ...query,
        columns: [xAxis],
        filters: scope
          ? [...(query.filters || []), { col: 'row_scope', op: 'IN', val: [scope] }]
          : query.filters,
        extras: { ...query.extras, time_grain_sqla: grain },
      });
      const queries = [withScope(common, timelineScope)];
      if (summaryScope) queries.push(withScope(common, summaryScope, 'P1M'));
      if (formData.card_variant === 'bars' && groupby.length) queries.push({
        ...common,
        columns: [xAxis, ...groupby],
        // The graph's activity categories must not narrow the headline DAX universe.
        extras: formData.pbip_headline_scope ? {
          ...common.extras,
          where: String(common.extras.where || '').replace("semantic_scope = 'all'", "semantic_scope = 'activity'"),
        } : common.extras,
      });
      if (formData.pbip_sellout_u3m ?? formData.pbipSelloutU3m) queries.push(withScope({
        ...common,
        extras: { ...common.extras, where: String(common.extras.where || '').replace("row_scope = 'monthly'", "row_scope = 'pbip_c05_u3m'") },
      }, 'pbip_c05_u3m', 'P1M'));
      return queries;
    },
  });
}
