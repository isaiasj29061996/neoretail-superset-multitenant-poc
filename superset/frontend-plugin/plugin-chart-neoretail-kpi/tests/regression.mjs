// Run from the repository root: node superset/frontend-plugin/plugin-chart-neoretail-kpi/tests/regression.mjs
// Unit tests with Superset dependency doubles; these do not replace an integration build.
import { readFileSync } from 'node:fs';

const src = 'superset/frontend-plugin/plugin-chart-neoretail-kpi/src/';
const load = (name, dependencies) => {
  const source = readFileSync(`${src}${name}.js`, 'utf8')
    .replace(/^import .*;\r?\n/gm, '')
    .replace('export default function', 'return function');
  return new Function(...Object.keys(dependencies), source)(...Object.values(dependencies));
};
let checks = 0;
const equal = (actual, expected, message) => {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(`${message}: ${JSON.stringify(actual)} != ${JSON.stringify(expected)}`);
  }
  checks += 1;
};
const baseQuery = {
  filters: [{ col: 'uf', op: 'IN', val: ['SP'] }],
  time_range: '2026-05-01 : 2026-09-01',
  extras: { where: 'id_location IS NOT NULL', time_grain_sqla: 'P1D' },
  row_limit: 5000,
};
const buildQuery = load('buildQuery', {
  // Superset 6 accepts only the second argument as options/callback.
  buildQueryContext: (formData, options) => {
    equal(options.ownState, { marker: true }, 'Preserve context options');
    return { queries: options.buildQuery ? options.buildQuery(baseQuery) : [baseQuery] };
  },
});
const raw = {
  x_axis: 'data', metric: 'TVD', critical_metric: 'Criticos', risk_metric: 'Risco',
};
const query = buildQuery(raw, { ownState: { marker: true } }).queries[0];
equal(query.columns, ['data'], 'Include temporal axis');
equal(query.metrics, ['TVD', 'Criticos', 'Risco'], 'Request all three metrics');
equal(query.filters, baseQuery.filters, 'Preserve native filters');
equal(query.time_range, baseQuery.time_range, 'Preserve time range');
equal(query.extras, baseQuery.extras, 'Preserve SQL extras and daily grain');
equal(query.row_limit, 5000, 'Preserve effective row limit');
equal(query.orderby, [['data', true]], 'Order daily observations');
const bars = buildQuery({ ...raw, card_variant: 'bars', groupby: ['activity_level'] }, { ownState: { marker: true } }).queries;
equal(bars.length, 2, 'Bar cards request summary and grouped series');
equal(bars[1].columns, ['data', 'activity_level'], 'Group bars by activity');
const stackedRank = buildQuery({ ...raw, metrics: ['TVD', 'IVD'], metric: undefined, card_variant: 'stackedrank', groupby: ['rede'] }, { ownState: { marker: true } }).queries;
equal(stackedRank.length, 1, 'Stacked ranking requests one grouped query');
equal(stackedRank[0].columns, ['rede'], 'Stacked ranking groups by category without date');
let missingAxisRejected = false;
try { buildQuery({ metric: 'TVD' }); } catch (error) {
  missingAxisRejected = error.message.includes('coluna temporal');
}
equal(missingAxisRejected, true, 'Reject a missing temporal axis');

const transform = load('transformProps', {
  getMetricLabel: metric => typeof metric === 'string' ? metric : metric.label,
});
const formData = { xAxis: 'snapshot', metrics: [{ label: 'TVD' }, 'Qtd'], criticalMetric: 'Criticos', riskMetric: 'Risco', cardTitle: 'Meu TVD', helpText: 'Detalhes', cardVariant: 'multi', metricLabels: 'Valor|Quantidade', metricFormats: 'currency|number', metricDirections: 'lower|higher', showTasks: false, accentColor: '#123abc', analysisUrl: ' /tvd ' };
const rows = [
  { snapshot: '2026-08-02', TVD: '15', Qtd: 8, Criticos: '7', Risco: '9' },
  { snapshot: '2026-05-31', TVD: 30, Qtd: 2 },
  { snapshot: '2026-07-31', TVD: 60, Qtd: 6 },
  { snapshot: '2026-06-30', TVD: 90, Qtd: 4 },
  { snapshot: '2026-08-01', TVD: 20, Qtd: 7 },
  { snapshot: null, TVD: 999 },
  { snapshot: 'invalid', TVD: 999 },
  { snapshot: NaN, TVD: 999 },
];
const result = transform({ width: 400, height: 300, formData, queriesData: [{ data: rows }] });
equal([result.indicators[0].current, result.indicators[0].previous, result.indicators[0].average], [15, 60, 60], 'Monthly closing calculations');
equal([result.indicators[1].label, result.indicators[1].format, result.indicators[1].lowerIsBetter], ['Quantidade', 'number', false], 'Per-metric presentation');
equal([result.critical, result.risk], [7, 9], 'Read task labels from camelCase props');
equal(result.series.map(row => row.value), [20, 15], 'Sort and retain latest month');
equal([result.title, result.helpText, result.variant], ['Meu TVD', 'Detalhes', 'multi'], 'Read presentation options');
equal(result.timeGrain, 'P1M', 'Expose time grain to the renderer');
const weeklyResult = transform({
  formData: { ...formData, timeGrainSqla: 'P1W' },
  queriesData: [{ data: rows }],
});
equal(weeklyResult.timeGrain, 'P1W', 'Preserve weekly grain for week labels');
const precedence = transform({
  formData: { ...formData, cardVariant: 'panorama' },
  rawFormData: { card_variant: 'area', chart_styles: undefined },
  queriesData: [{ data: rows }],
});
equal(precedence.variant, 'panorama', 'Persisted camelCase variant wins over stale raw defaults');
const rawSpecificVariant = transform({
  formData: { ...formData, cardVariant: 'area' },
  rawFormData: { card_variant: 'stacked' },
  queriesData: [{ data: rows }],
});
equal(rawSpecificVariant.variant, 'stacked', 'Specific raw variant wins over camelCase area default');
equal([result.showTasks, result.accentColor, result.analysisUrl], [false, '#123abc', '/tvd'], 'Preserve false flags and custom styles');
equal(result.hasData, true, 'Daily results are usable');
const groupedResult = transform({
  formData: { ...formData, cardVariant: 'stackedrank', groupby: ['rede'] },
  queriesData: [{ data: [{ rede: 'B', TVD: 4, Qtd: 8 }, { rede: 'A', TVD: 10, Qtd: 20 }] }],
});
equal(groupedResult.rankSeries[0], { category: 'A', values: [10, 20] }, 'Stacked ranking sorts categories by combined value');
equal(groupedResult.hasData, true, 'Grouped stacked ranking has data without a date column');
const transformRows = data => transform({ rawFormData: raw, queriesData: [{ data }] });
equal(transformRows([{ TVD: 100 }]).hasData, false, 'An aggregate without date is not a daily series');
equal(transformRows([]).hasData, false, 'Empty query response');
equal(transformRows([{ data: null, TVD: 100 }]).hasData, false, 'Null date is not January 1970');
equal(transformRows([{ __timestamp: Date.UTC(2026, 7, 2), TVD: 0 }]).hasData, true, 'Accept epoch timestamps and zero metrics');
equal(transformRows([{ data: '2026-08-02', TVD: 42, Criticos: 3, Risco: 4 }]).critical, 3, 'Support rawFormData');
console.log(`${checks} regression checks passed (Superset dependency doubles).`);
