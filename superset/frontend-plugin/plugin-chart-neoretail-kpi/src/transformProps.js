import { getMetricLabel } from '@superset-ui/core';

const metricLabel = metric => (metric ? getMetricLabel(metric) : null);

const xAxisName = xAxis => {
  if (typeof xAxis === 'string') return xAxis;
  return xAxis?.column_name || xAxis?.label || 'data';
};

const numeric = value => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
};

const asDate = value => {
  if (typeof value === 'number') return new Date(value);
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const monthKey = date => `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, '0')}`;

const shiftMonth = (date, offset) => {
  const shifted = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + offset, 1));
  return monthKey(shifted);
};

export default function transformProps(chartProps) {
  const { width, height, formData, queriesData = [] } = chartProps;
  const rows = queriesData[0]?.data || [];
  const dateColumn = xAxisName(formData.x_axis);
  const primaryLabel = metricLabel(formData.metric);
  const criticalLabel = metricLabel(formData.critical_metric);
  const riskLabel = metricLabel(formData.risk_metric);

  const daily = rows
    .map(row => ({
      date: asDate(row.__timestamp ?? row[dateColumn]),
      value: numeric(row[primaryLabel]),
      critical: numeric(row[criticalLabel]),
      risk: numeric(row[riskLabel]),
    }))
    .filter(row => row.date)
    .sort((left, right) => left.date - right.date);

  const lastByMonth = new Map();
  daily.forEach(row => lastByMonth.set(monthKey(row.date), row));
  const latest = daily[daily.length - 1] || null;
  const currentMonth = latest ? monthKey(latest.date) : null;
  const previous = latest ? lastByMonth.get(shiftMonth(latest.date, -1)) : null;
  const priorMonths = latest
    ? [-1, -2, -3]
        .map(offset => lastByMonth.get(shiftMonth(latest.date, offset)))
        .filter(Boolean)
    : [];
  const averageU3m = priorMonths.length
    ? priorMonths.reduce((total, row) => total + row.value, 0) / priorMonths.length
    : 0;

  return {
    width,
    height,
    title: formData.card_title || 'TVD - Pré-ruptura',
    helpText: formData.help_text || '',
    formatType: formData.number_format_type || 'currency',
    lowerIsBetter: formData.lower_is_better !== false,
    showTasks: formData.show_tasks !== false,
    accentColor: /^#[0-9a-f]{6}$/i.test(formData.accent_color || '')
      ? formData.accent_color
      : '#7C4AD9',
    analysisUrl: String(formData.analysis_url || '').trim(),
    mtd: latest?.value || 0,
    previous: previous?.value || 0,
    averageU3m,
    critical: latest?.critical || 0,
    risk: latest?.risk || 0,
    series: daily.filter(row => monthKey(row.date) === currentMonth),
    hasData: daily.length > 0,
  };
}
