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
const formatValue = load('formatValue', {});
equal(formatValue(null, 'percent'), '—', 'Format preserves null as BLANK');
equal(formatValue(undefined, 'currency'), '—', 'Format preserves undefined as BLANK');
equal(formatValue(0, 'percent'), '0%', 'Format preserves a legitimate numeric zero');
const formData = { xAxis: 'snapshot', metrics: [{ label: 'TVD' }, 'Qtd'], criticalMetric: 'Criticos', riskMetric: 'Risco', cardTitle: 'Meu TVD', helpText: 'Detalhes', cardVariant: 'multi', metricLabels: 'Valor|Quantidade', metricFormats: 'currency|number', metricDirections: 'lower|higher', semanticProfile: 'direct_average', showTasks: false, accentColor: '#123abc', analysisUrl: ' /tvd ' };
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
const monthlySemantic = transform({
  formData: {
    ...formData,
    cardVariant: 'area',
    timeGrainSqla: 'P1D',
    semanticPeriod: 'month_last_nonblank',
  },
  queriesData: [{ data: [
    { snapshot: '2026-02-28', TVD: 90, Qtd: 9 },
    { snapshot: '2026-04-30', TVD: 30, Qtd: 3 },
    { snapshot: '2026-05-10', TVD: 5, Qtd: 1 },
    { snapshot: '2026-05-25', TVD: 20, Qtd: 2 },
  ] }],
});
equal(
  monthlySemantic.timeline.map(row => [row.date.toISOString().slice(0, 10), row.values[0]]),
  [['2026-02-28', 90], ['2026-04-30', 30], ['2026-05-25', 20]],
  'Deliver one last-nonblank observation per year/month',
);
equal(
  [monthlySemantic.indicators[0].current, monthlySemantic.indicators[0].previous, monthlySemantic.indicators[0].average],
  [20, 30, 40],
  'MTD, M-1 and fixed-denominator U3M match the DAX contract with a missing month',
);
equal(monthlySemantic.series.length, 3, 'Monthly area series includes the available month closings');
equal(monthlySemantic.timeGrain, 'P1M', 'Monthly semantic series exposes year/month grain');
equal(
  [monthlySemantic.indicators[0].lastYear.current, monthlySemantic.indicators[0].lastYear.previous, monthlySemantic.indicators[0].lastYear.average],
  [null, null, null],
  'Missing prior-year months remain BLANK instead of zero',
);
const weighted = transform({
  formData: {
    xAxis: 'data', metrics: ['Giro soma', 'Giro contagem'], metricLabels: 'Giro',
    metricFormats: 'number', semanticProfile: 'weighted_average', cardVariant: 'bars',
    groupby: ['activity_level'],
  },
  queriesData: [{ data: [
    { data: '2026-02-01', 'Giro soma': 100, 'Giro contagem': 10 },
    { data: '2026-03-01', 'Giro soma': 20, 'Giro contagem': 1 },
    { data: '2026-04-01', 'Giro soma': 30, 'Giro contagem': 3 },
    { data: '2026-05-01', 'Giro soma': 40, 'Giro contagem': 2 },
  ] }, { data: [] }],
});
equal(weighted.indicators.length, 1, 'Weighted semantic profile exposes one business metric');
equal(
  [weighted.indicators[0].current, weighted.indicators[0].previous, weighted.indicators[0].average],
  [20, 10, 150 / 14],
  'Giro U3M recalculates sum/count across the full context',
);
const osaRatio = transform({
  formData: {
    xAxis: 'data', metrics: ['Problemas', 'Ativos'], metricLabels: '% OSA',
    metricFormats: 'percent', semanticProfile: 'one_minus_ratio', cardVariant: 'osa',
  },
  queriesData: [{ data: [
    { data: '2026-02-01', Problemas: 1, Ativos: 10 },
    { data: '2026-03-01', Problemas: 9, Ativos: 10 },
    { data: '2026-04-01', Problemas: 0, Ativos: 80 },
    { data: '2026-05-01', Problemas: 2, Ativos: 20 },
  ] }],
});
equal(osaRatio.indicators[0].current, 90, 'OSA current month recalculates one minus the ratio');
equal(osaRatio.indicators[0].average, 90, 'OSA U3M uses totals instead of averaging monthly percentages');
const osaBlank = transform({
  formData: {
    xAxis: 'data', metrics: ['Problemas', 'Ativos'], semanticProfile: 'one_minus_ratio',
  },
  queriesData: [{ data: [{ data: '2026-05-01', Problemas: 2, Ativos: 0 }] }],
});
equal(osaBlank.indicators[0].current, null, 'OSA preserves BLANK when the active denominator is zero');
equal(osaBlank.indicators[0].average, null, 'OSA U3M preserves BLANK when every denominator is absent or zero');
const directSum = transform({
  formData: { xAxis: 'data', metrics: ['Perda'], semanticProfile: 'direct_sum' },
  queriesData: [{ data: [
    { data: '2026-02-01', Perda: 10 }, { data: '2026-03-01', Perda: 20 },
    { data: '2026-04-01', Perda: 30 }, { data: '2026-05-01', Perda: 40 },
  ] }],
});
equal(directSum.indicators[0].average, 60, 'Loss U3M sums the three prior months without dividing by three');
const quantityRatios = transform({
  formData: { xAxis: 'data', metrics: ['Numerador', 'Denominador'], semanticProfile: 'ratio_percent' },
  queriesData: [{ data: [
    { data: '2026-02-01', Numerador: 1, Denominador: 10 },
    { data: '2026-03-01', Numerador: 2, Denominador: 20 },
    { data: '2026-04-01', Numerador: 3, Denominador: 30 },
    { data: '2026-05-01', Numerador: 4, Denominador: 40 },
  ] }],
});
equal(quantityRatios.indicators[0].average, 10, 'Quantity percentages recalculate the ratio over U3M totals');
const coverage = transform({
  formData: { xAxis: 'data', metrics: ['Estoque', 'Demanda'], semanticProfile: 'ratio' },
  queriesData: [{ data: [
    { data: '2026-02-01', Estoque: 100, Demanda: 10 },
    { data: '2026-03-01', Estoque: 200, Demanda: 20 },
    { data: '2026-04-01', Estoque: 300, Demanda: 30 },
    { data: '2026-05-01', Estoque: 400, Demanda: 40 },
  ] }],
});
equal(coverage.indicators[0].average, 10, 'Coverage U3M divides aggregated stock by aggregated demand');
const coverageBlank = transform({
  formData: { xAxis: 'data', metrics: ['Estoque', 'Demanda'], semanticProfile: 'ratio' },
  queriesData: [{ data: [
    { data: '2025-04-01', Estoque: 100, Demanda: 10 },
    { data: '2025-05-01', Estoque: 100, Demanda: 0 },
    { data: '2026-05-01', Estoque: 400, Demanda: 0 },
  ] }],
});
equal(coverageBlank.indicators[0].current, null, 'Coverage preserves BLANK when current demand is zero');
equal(coverageBlank.indicators[0].lastYear.current, null, 'Coverage LY preserves BLANK when its demand is zero');
equal(coverageBlank.indicators[0].lastYear.previous, 10, 'Coverage LY keeps a legitimate prior-month ratio');
const missingNumerator = transform({
  formData: { xAxis: 'data', metrics: ['Soma', 'Contagem'], semanticProfile: 'weighted_average' },
  queriesData: [{ data: [{ data: '2026-05-01', Soma: null, Contagem: 10 }] }],
});
equal(missingNumerator.indicators[0].current, null, 'A missing numerator remains BLANK with a valid denominator');
const zeroVersusBlank = transform({
  formData: { xAxis: 'data', metrics: ['Perda'], semanticProfile: 'direct_sum' },
  queriesData: [{ data: [
    { data: '2026-04-01', Perda: null },
    { data: '2026-05-01', Perda: 0 },
  ] }],
});
equal(
  [zeroVersusBlank.indicators[0].current, zeroVersusBlank.indicators[0].previous],
  [0, null],
  'A legitimate zero remains distinct from a BLANK month',
);
const priceLyPending = transform({
  formData: {
    xAxis: 'data', metrics: ['Preco soma', 'Preco contagem'],
    semanticProfile: 'weighted_average', semanticDisableLy: true,
  },
  queriesData: [{ data: [
    { data: '2025-05-01', 'Preco soma': 100, 'Preco contagem': 10 },
    { data: '2026-05-01', 'Preco soma': 200, 'Preco contagem': 10 },
  ] }],
});
equal(
  priceLyPending.indicators[0].lastYear,
  { current: null, previous: null, average: null },
  'Price LY stays BLANK while the original DAX definition is unavailable',
);
const distribution = transform({
  formData: {
    xAxis: 'data', metrics: ['Lojas', 'Itens', 'Lojas U3M', 'Itens U3M'],
    metricLabels: 'Lojas|Itens', semanticProfile: 'distribution_bundle',
  },
  queriesData: [{ data: [
    { data: '2026-03-01', Lojas: 2, Itens: 3, 'Lojas U3M': 8, 'Itens U3M': 9 },
    { data: '2026-04-01', Lojas: 4, Itens: 5, 'Lojas U3M': 10, 'Itens U3M': 11 },
    { data: '2026-05-01', Lojas: 6, Itens: 7, 'Lojas U3M': 12, 'Itens U3M': 13 },
  ] }],
});
equal(distribution.indicators.map(item => item.current), [6, 7], 'Distribution exposes stores and items');
equal(distribution.indicators.map(item => item.average), [10, 11], 'Distribution uses precomputed distinct U3M cardinality');
const osaBundle = transform({
  formData: {
    xAxis: 'data', metrics: ['Problemas', 'Ativos', 'Perda'],
    metricLabels: '% OSA|Perda OSA', metricFormats: 'percent|currency',
    semanticProfile: 'osa_bundle', cardVariant: 'osa',
  },
  queriesData: [{ data: [
    { data: '2026-02-01', Problemas: 1, Ativos: 10, Perda: 30 },
    { data: '2026-03-01', Problemas: 9, Ativos: 10, Perda: 60 },
    { data: '2026-04-01', Problemas: 0, Ativos: 80, Perda: 90 },
    { data: '2026-05-01', Problemas: 2, Ativos: 20, Perda: 120 },
  ] }],
});
equal(osaBundle.indicators.map(item => item.current), [90, 120], 'OSA bundle restores percentage and loss');
equal(osaBundle.indicators[1].average, 60, 'OSA loss U3M divides the full measure by three');
const osaBundleBlank = transform({
  formData: {
    xAxis: 'data', metrics: ['Problemas', 'Ativos', 'Perda'],
    metricLabels: '% OSA|Perda OSA', semanticProfile: 'osa_bundle',
  },
  queriesData: [{ data: [{ data: '2026-05-01', Problemas: null, Ativos: 10, Perda: null }] }],
});
equal(osaBundleBlank.indicators.map(item => item.current), [null, null], 'OSA bundle preserves missing numerators as BLANK');
const roi = transform({
  formData: {
    xAxis: 'data', metrics: ['Sellout', 'Custo', 'Estoque'], metricLabels: 'ROI',
    metricFormats: 'percent', semanticProfile: 'roi', showAnnual: true, cardVariant: 'bars', groupby: ['activity_level'],
  },
  queriesData: [{ data: [
    { data: '2025-06-01', Sellout: 150, Custo: 100, Estoque: 100 },
    { data: '2025-07-01', Sellout: 0, Custo: 100, Estoque: 100 },
    { data: '2025-08-01', Sellout: 100, Custo: 0, Estoque: 100 },
    { data: '2026-03-01', Sellout: 200, Custo: 100, Estoque: 100 },
    { data: '2026-04-01', Sellout: 300, Custo: 200, Estoque: 200 },
    { data: '2026-05-01', Sellout: 400, Custo: 200, Estoque: 200 },
  ] }, { data: [] }],
});
equal(roi.timeline.slice(1, 3).map(row => row.values[0]), [0, 0], 'ROI returns zero for zero sellout or zero cost');
equal(roi.indicators[0].average, 100 * (500 - 300) / 300, 'ROI U3M is recalculated over U3M components');
equal(roi.indicators[0].annual, 300, 'ROI annual sums monthly ROI values instead of averaging');
equal(roi.showAnnual, true, 'ROI exposes its annual 12M summary to the renderer');
const markup = transform({
  formData: { xAxis: 'data', metrics: ['Sellout', 'Custo'], metricLabels: 'Markup', semanticProfile: 'markup' },
  queriesData: [{ data: [
    { data: '2026-02-01', Sellout: 100, Custo: 50 },
    { data: '2026-03-01', Sellout: 200, Custo: 100 },
    { data: '2026-04-01', Sellout: 0, Custo: 100 },
    { data: '2026-05-01', Sellout: 300, Custo: 150 },
  ] }],
});
equal(markup.indicators[0].average, 100 * 300 / 250, 'Markup U3M divides aggregated sellout by aggregated cost');
const stock = transform({
  formData: { xAxis: 'data', metrics: ['Custo', 'Qtd'], metricLabels: 'Custo|Qtd', semanticProfile: 'stock_bundle' },
  queriesData: [{ data: [
    { data: '2026-02-01', Custo: 30, Qtd: 300 },
    { data: '2026-03-01', Custo: 60, Qtd: 600 },
    { data: '2026-04-01', Custo: 90, Qtd: 900 },
    { data: '2026-05-01', Custo: 120, Qtd: 1200 },
  ] }],
});
equal(stock.indicators.map(item => item.average), [60, 300], 'Stock U3M uses cost/3 and latest MES_ANO quantity/3');
const activityBars = transform({
  formData: { xAxis: 'data', metrics: ['Soma', 'Contagem'], metricLabels: 'Giro', semanticProfile: 'weighted_average', cardVariant: 'bars', groupby: ['activity_level'] },
  queriesData: [{ data: [{ data: '2026-05-01', Soma: 10, Contagem: 2 }] }, { data: [
    { data: '2026-05-01', activity_level: 'Outros', Soma: 99, Contagem: 1 },
    { data: '2026-05-01', activity_level: 'New Mover', Soma: 4, Contagem: 2 },
    { data: '2026-05-01', activity_level: 'Fast Mover', Soma: 8, Contagem: 2 },
    { data: '2026-05-01', activity_level: 'Ultra Slow Mover', Soma: 6, Contagem: 2 },
    { data: '2026-05-01', activity_level: 'Slow Mover', Soma: 10, Contagem: 2 },
    { data: '2026-05-01', activity_level: 'Non Mover', Soma: 99, Contagem: 1 },
  ] }],
});
equal(activityBars.bars.map(item => item.category), ['Fast Mover', 'Slow Mover', 'Ultra Slow Mover', 'New Mover'], 'Activity bars enforce the certified category order');
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
const panoramaQuantity = transform({
  formData: {
    xAxis: 'data', metrics: ['Venda', 'Perda', 'Preco soma', 'Preco contagem'],
    metricLabels: 'Sell out Volume|Perda OSA|Preco Medio',
    metricSemantics: 'direct_average:0:1|direct_sum:1:1|weighted_average:2:2',
    cardVariant: 'panorama',
  },
  queriesData: [{ data: [
    { data: '2026-02-01', Venda: 10, Perda: 1, 'Preco soma': 100, 'Preco contagem': 10 },
    { data: '2026-03-01', Venda: 20, Perda: 2, 'Preco soma': 200, 'Preco contagem': 20 },
    { data: '2026-04-01', Venda: 30, Perda: 3, 'Preco soma': 300, 'Preco contagem': 30 },
    { data: '2026-05-01', Venda: 40, Perda: 4, 'Preco soma': 400, 'Preco contagem': 40 },
  ] }],
});
equal(panoramaQuantity.indicators.map(item => item.current), [40, 4, 10], 'Panorama quantity derives three outputs from four additive components');
equal(panoramaQuantity.indicators.map(item => item.average), [20, 6, 10], 'Panorama quantity applies average, sum and weighted U3M per metric');
const panoramaValue = transform({
  formData: {
    xAxis: 'data', metrics: ['Sellout', 'Custo'],
    metricLabels: 'Sell out Venda|Sell out Custo|Markup',
    metricSemantics: 'direct_average:0:1|direct_average:1:1|markup_blank:0:2',
    cardVariant: 'panorama',
  },
  queriesData: [{ data: [
    { data: '2026-02-01', Sellout: 100, Custo: 50 },
    { data: '2026-03-01', Sellout: 200, Custo: 100 },
    { data: '2026-04-01', Sellout: 300, Custo: 100 },
    { data: '2026-05-01', Sellout: 0, Custo: 150 },
  ] }],
});
equal(panoramaValue.indicators.map(item => item.average), [200, 250 / 3, 240], 'Panorama value averages components and recomputes U3M markup');
equal(panoramaValue.timeline.at(-1).values[2], null, 'Panorama markup line preserves BLANK when its result is zero');
console.log(`${checks} regression checks passed (Superset dependency doubles).`);
