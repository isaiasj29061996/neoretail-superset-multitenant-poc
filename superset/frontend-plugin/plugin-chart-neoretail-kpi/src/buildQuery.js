import { buildQueryContext } from '@superset-ui/core';

export default function buildQuery(formData, options) {
  const xAxis =
    typeof formData.x_axis === 'string'
      ? formData.x_axis
      : formData.x_axis?.column_name;

  const metrics = [
    formData.metric,
    formData.critical_metric,
    formData.risk_metric,
  ].filter(Boolean);

  return buildQueryContext(formData, options, baseQueryObject => [
    {
      ...baseQueryObject,
      columns: [],
      granularity: xAxis,
      is_timeseries: Boolean(xAxis),
      metrics,
      orderby: [],
      row_limit: formData.row_limit || 10000,
      time_grain: formData.time_grain_sqla || 'P1D',
    },
  ]);
}