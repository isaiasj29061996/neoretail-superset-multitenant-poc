import { getMetricLabel } from '@superset-ui/core';

const asArray = value => (Array.isArray(value) ? value : value ? [value] : []);
const metricLabel = metric => (metric ? getMetricLabel(metric) : null);
const columnName = column => typeof column === 'string' ? column : column?.column_name || column?.label;
const numeric = value => Number.isFinite(Number(value)) ? Number(value) : 0;
const asDate = value => {
  if (value == null || value === '') return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};
const monthKey = date => `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, '0')}`;
const shiftMonth = (date, offset) => monthKey(new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + offset, 1)));
const splitConfig = (value, fallback = []) => String(value || '').split('|').map(item => item.trim()).filter(Boolean).concat(fallback);

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
  const normalize = (rows, grouped = false) => rows.map(row => ({
    date: asDate(row.__timestamp ?? row[dateColumn]),
    category: grouped ? String(row[groupColumn] ?? 'Outros') : null,
    values: metricLabels.map(label => numeric(row[label])),
    critical: numeric(row[criticalLabel]),
    risk: numeric(row[riskLabel]),
  })).filter(row => row.date).sort((left, right) => left.date - right.date);
  const timeline = normalize(queriesData[0]?.data || []);
  const rankItems = (queriesData[0]?.data || []).map(row => ({
    category: String(row[groupColumn] ?? 'Outros'),
    value: numeric(row[metricLabels[0]]),
  })).sort((left, right) => right.value - left.value);
  const rankSeries = (queriesData[0]?.data || []).map(row => ({
    category: String(row[groupColumn] ?? 'Outros'),
    values: metricLabels.map(label => numeric(row[label])),
  })).sort((left, right) => right.values.reduce((sum, value) => sum + Math.abs(value), 0)
    - left.values.reduce((sum, value) => sum + Math.abs(value), 0));
  const grouped = normalize(queriesData[1]?.data || [], true);
  const latest = timeline[timeline.length - 1] || null;
  const currentMonth = latest ? monthKey(latest.date) : null;
  const lastByMonth = new Map();
  timeline.forEach(row => lastByMonth.set(monthKey(row.date), row));
  const indicators = metricLabels.map((label, index) => {
    const previous = latest ? lastByMonth.get(shiftMonth(latest.date, -1)) : null;
    const prior = latest ? [-1, -2, -3].map(offset => lastByMonth.get(shiftMonth(latest.date, offset))).filter(Boolean) : [];
    return {
      label: labels[index] || label,
      format: formats[index] || formats[0] || 'number',
      lowerIsBetter: (directions[index] || directions[0]) !== 'higher',
      current: latest?.values[index] ?? 0,
      previous: previous?.values[index] ?? 0,
      average: prior.length ? prior.reduce((sum, row) => sum + row.values[index], 0) / prior.length : 0,
    };
  });
  const categories = new Map();
  grouped.forEach(row => {
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
    taskLabels: splitConfig(formData.task_labels, ['itens críticos', 'itens com risco']),
    chartStyles: splitConfig(formData.chart_styles, ['bar', 'bar', 'line']),
    timeGrain: formData.time_grain_sqla || 'P1M',
    summaryCount: Math.max(0, Number(formData.summary_count) || metricLabels.length),
    indicators,
    critical: latest?.critical || 0,
    risk: latest?.risk || 0,
    series: timeline.filter(row => monthKey(row.date) === currentMonth).map(row => ({ date: row.date, value: row.values[0] })),
    timeline: timeline.map(row => ({ date: row.date, values: row.values })),
    bars: [...categories].map(([category, values]) => ({ category, current: values.current || 0, previous: values.previous || 0 })),
    rankItems,
    rankSeries,
    hasData: ['rankbars', 'verticalbars', 'stackedrank'].includes(variant) ? rankItems.length > 0 : timeline.length > 0,
  };
}
