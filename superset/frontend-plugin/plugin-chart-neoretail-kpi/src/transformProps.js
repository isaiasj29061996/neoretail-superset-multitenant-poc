import { getMetricLabel } from '@superset-ui/core';

const asArray = value => (Array.isArray(value) ? value : value ? [value] : []);
const metricLabel = metric => (metric ? getMetricLabel(metric) : null);
const columnName = column => typeof column === 'string' ? column : column?.column_name || column?.label;
const numeric = value => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value))
  ? Number(value)
  : null;
const asDate = value => {
  if (value == null || value === '') return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};
const monthKey = date => `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, '0')}`;
const shiftMonth = (date, offset) => monthKey(new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + offset, 1)));
const splitConfig = (value, fallback = []) => String(value || '').split('|').map(item => item.trim()).filter(Boolean).concat(fallback);
const semanticValue = (profile, components) => {
  if (!profile || profile === 'direct_average' || profile === 'stock_bundle') return components;
  const numerator = components[0];
  const denominator = components[1];
  if (profile === 'roi') {
    const stockCost = components[2];
    if (numerator === 0 || denominator === 0) return [0];
    if (numerator === null || denominator === null || stockCost === null || stockCost === 0) return [null];
    return [100 * (numerator - denominator) / stockCost];
  }
  if (profile === 'markup') {
    if (numerator === 0 || denominator === 0) return [0];
    if (numerator === null || denominator === null) return [null];
    return [100 * numerator / denominator];
  }
  if (profile === 'osa_bundle') {
    const osa = denominator === null || denominator === 0 ? null : 100 * (1 - numerator / denominator);
    return [osa, components[2] ?? null];
  }
  if (denominator === null || denominator === 0) return [null];
  if (profile === 'weighted_average') return [numerator / denominator];
  if (profile === 'one_minus_ratio') return [100 * (1 - numerator / denominator)];
  return components;
};
const semanticAggregate = (profile, rows, index) => {
  if (!profile) return null;
  if (profile === 'direct_average') {
    return rows.reduce((sum, row) => sum + (row?.values[index] ?? 0), 0) / 3;
  }
  if (profile === 'stock_bundle') {
    if (index === 0) return rows.reduce((sum, row) => sum + (row?.values[index] ?? 0), 0) / 3;
    const latestStock = rows.filter(Boolean).sort((left, right) => left.date - right.date).at(-1);
    return (latestStock?.values[index] ?? 0) / 3;
  }
  const components = [0, 0];
  rows.forEach(row => row?.components?.forEach((value, componentIndex) => {
    components[componentIndex] = (components[componentIndex] || 0) + (value ?? 0);
  }));
  if (profile === 'osa_bundle' && index === 1) return components[2] / 3;
  return semanticValue(profile, components)[index] ?? null;
};

const ALLOWED_ACTIVITY_LEVELS = [
  'Fast Mover', 'Slow Mover', 'Ultra Slow Mover', 'New Mover',
];

export default function transformProps(chartProps) {
  const { width, height, queriesData = [] } = chartProps;
  const normalizeKeys = source => Object.fromEntries(Object.entries(source || {})
    .filter(([, value]) => value !== undefined && value !== null)
    .map(([key, value]) => [key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`), value]));
  // Superset supplies persisted values in formData (camelCase) and may also
  // include incomplete/default values in rawFormData. Persisted values must win.
  const formData = { ...normalizeKeys(chartProps.rawFormData), ...normalizeKeys(chartProps.formData) };
  const variantCandidates = [
    chartProps.formData?.cardVariant,
    chartProps.formData?.card_variant,
    chartProps.rawFormData?.card_variant,
    chartProps.rawFormData?.cardVariant,
    formData.card_variant,
  ].filter(Boolean);
  // Custom variants may exist only in rawFormData while camelized formData
  // still carries the control's default "area". Prefer a specific variant.
  const variant = variantCandidates.find(value => value !== 'area') ?? variantCandidates[0] ?? 'area';
  const metrics = [...asArray(formData.metrics), formData.metric].filter(Boolean);
  const metricLabels = metrics.map(metricLabel);
  const dateColumn = columnName(formData.x_axis) || 'data';
  const groupColumn = columnName(asArray(formData.groupby)[0]);
  const labels = splitConfig(formData.metric_labels, metricLabels);
  const formats = splitConfig(formData.metric_formats, [formData.number_format_type || 'currency']);
  const directions = splitConfig(formData.metric_directions, [formData.lower_is_better === false ? 'higher' : 'lower']);
  const criticalLabel = metricLabel(formData.critical_metric);
  const riskLabel = metricLabel(formData.risk_metric);
  const semanticProfile = ['direct_average', 'stock_bundle', 'weighted_average', 'one_minus_ratio', 'osa_bundle', 'roi', 'markup'].includes(formData.semantic_profile)
    ? formData.semantic_profile
    : null;
  const normalize = (rows, grouped = false) => rows.map(row => ({
    date: asDate(row.__timestamp ?? row[dateColumn]),
    category: grouped ? String(row[groupColumn] ?? 'Outros') : null,
    values: metricLabels.map(label => numeric(row[label])),
    critical: numeric(row[criticalLabel]),
    risk: numeric(row[riskLabel]),
  })).filter(row => row.date).sort((left, right) => left.date - right.date);
  const applySemanticProfile = row => ({
    ...row,
    components: row.values,
    values: semanticValue(semanticProfile, row.values),
  });
  const timeline = normalize(queriesData[0]?.data || []).map(applySemanticProfile);
  const rankItems = (queriesData[0]?.data || []).map(row => ({
    category: String(row[groupColumn] ?? 'Outros'),
    value: numeric(row[metricLabels[0]]),
  })).sort((left, right) => right.value - left.value);
  const rankSeries = (queriesData[0]?.data || []).map(row => ({
    category: String(row[groupColumn] ?? 'Outros'),
    values: metricLabels.map(label => numeric(row[label])),
  })).sort((left, right) => right.values.reduce((sum, value) => sum + Math.abs(value), 0)
    - left.values.reduce((sum, value) => sum + Math.abs(value), 0));
  const grouped = normalize(queriesData[1]?.data || [], true).map(applySemanticProfile);
  const monthlyLastNonBlank = formData.semantic_period === 'month_last_nonblank';
  // The query deliberately stays daily. Native filters are evaluated by
  // Superset first; only then can we reproduce DAX LASTNONBLANK for each month
  // without summing every daily snapshot in that month.
  const semanticTimeline = monthlyLastNonBlank
    ? [...timeline.reduce((months, row) => months.set(monthKey(row.date), row), new Map()).values()]
    : timeline;
  const latest = semanticTimeline[semanticTimeline.length - 1] || null;
  const currentMonth = latest ? monthKey(latest.date) : null;
  const lastByMonth = new Map();
  semanticTimeline.forEach(row => lastByMonth.set(monthKey(row.date), row));
  const outputCount = semanticProfile === 'osa_bundle' ? 2
    : ['weighted_average', 'one_minus_ratio', 'roi', 'markup'].includes(semanticProfile) ? 1
      : metricLabels.length;
  const displayMetricLabels = labels.slice(0, outputCount);
  const indicators = displayMetricLabels.map((label, index) => {
    const previous = latest ? lastByMonth.get(shiftMonth(latest.date, -1)) : null;
    const prior = latest ? [-1, -2, -3].map(offset => lastByMonth.get(shiftMonth(latest.date, offset))) : [];
    return {
      label: labels[index] || label,
      format: formats[index] || formats[0] || 'number',
      lowerIsBetter: (directions[index] || directions[0]) !== 'higher',
      current: latest?.values[index] ?? null,
      previous: previous?.values[index] ?? null,
      // DAX contract: DIVIDE(M1 + M2 + M3, 3). Missing months do not
      // change the denominator and BLANK participates as zero in the sum.
      average: latest ? semanticAggregate(semanticProfile, prior, index) : null,
      annual: semanticProfile === 'roi' && latest
        ? semanticTimeline.slice(-12).reduce((sum, row) => sum + (row.values[0] ?? 0), 0)
        : null,
    };
  });
  const categories = new Map();
  grouped.filter(row => ALLOWED_ACTIVITY_LEVELS.includes(row.category)).forEach(row => {
    const entry = categories.get(row.category) || {};
    if (monthKey(row.date) === currentMonth) entry.current = row.values[0];
    if (latest && monthKey(row.date) === shiftMonth(latest.date, -1)) entry.previous = row.values[0];
    categories.set(row.category, entry);
  });
  return {
    width, height,
    title: formData.card_title || 'NeoRetail',
    helpText: formData.help_text || '',
    variant,
    accentColor: /^#[0-9a-f]{6}$/i.test(formData.accent_color || '') ? formData.accent_color : '#7C4AD9',
    analysisUrl: String(formData.analysis_url || '').trim(),
    showTasks: formData.show_tasks !== false,
    showAnnual: formData.show_annual === true,
    taskLabels: splitConfig(formData.task_labels, ['itens críticos', 'itens com risco']),
    chartStyles: splitConfig(formData.chart_styles, ['bar', 'bar', 'line']),
    timeGrain: monthlyLastNonBlank ? 'P1M' : (formData.time_grain_sqla || 'P1M'),
    summaryCount: Math.max(0, Number(formData.summary_count) || indicators.length),
    indicators,
    critical: latest?.critical || 0,
    risk: latest?.risk || 0,
    series: (monthlyLastNonBlank
      ? semanticTimeline
      : timeline.filter(row => monthKey(row.date) === currentMonth))
      .map(row => ({ date: row.date, value: row.values[0] })),
    timeline: semanticTimeline.map(row => ({ date: row.date, values: row.values })),
    bars: ALLOWED_ACTIVITY_LEVELS
      .filter(category => categories.has(category))
      .map(category => {
        const values = categories.get(category);
        return { category, current: values.current || 0, previous: values.previous || 0 };
      }),
    rankItems,
    rankSeries,
    hasData: ['rankbars', 'verticalbars', 'stackedrank'].includes(variant) ? rankItems.length > 0 : timeline.length > 0,
  };
}
