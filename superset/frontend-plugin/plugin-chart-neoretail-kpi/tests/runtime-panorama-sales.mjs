// Runtime gate fed by persisted chart.params and real Superset query responses.
import { readFileSync } from 'node:fs';

const fixturePath = process.argv[2];
if (!fixturePath) throw new Error('Usage: node runtime-panorama-sales.mjs <fixture.json>');

const src = 'superset/frontend-plugin/plugin-chart-neoretail-kpi/src/';
const source = readFileSync(`${src}transformProps.js`, 'utf8')
  .replace(/^import .*;\r?\n/gm, '')
  .replace('export default function', 'return function');
const transform = new Function('getMetricLabel', source)(
  metric => typeof metric === 'string' ? metric : metric.label,
);
const camelize = key => key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
const toFormData = raw => Object.fromEntries(Object.entries(raw).map(([key, value]) => [camelize(key), value]));
const fixture = JSON.parse(readFileSync(fixturePath, 'utf8'));
let checks = 0;
const assert = (condition, message) => {
  if (!condition) throw new Error(message);
  checks += 1;
};
const close = (left, right) => Math.abs(left - right) <= Math.max(1e-7, Math.abs(right) * 1e-9);

for (const [name, chart] of Object.entries(fixture.charts)) {
  const props = transform({
    rawFormData: chart.rawFormData,
    formData: toFormData(chart.rawFormData),
    queriesData: chart.queriesData,
  });
  assert(props.indicators.length === 3, `${name}: expected exactly three indicators`);
  assert(props.timeline.every(point => point.values.length === 3), `${name}: expected exactly three rendered series`);
  assert(props.indicators.every(indicator => indicator.average !== null), `${name}: expected populated U3M`);

  if (name.includes('Quantidade')) {
    assert(!props.indicators.some(indicator => indicator.label.includes('Venda quantidade')), `${name}: technical sales component leaked`);
    const point = props.timeline.find(entry => entry.components[3] > 0);
    assert(Boolean(point), `${name}: missing eligible price point`);
    assert(close(point.values[2], point.components[2] / point.components[3]), `${name}: price is not numerator/count`);
  } else {
    assert(props.indicators[2].label === 'Markup', `${name}: missing Markup indicator`);
    const point = props.timeline.find(entry => entry.components[0] > 0 && entry.components[1] > 0);
    assert(Boolean(point), `${name}: missing Markup point`);
    assert(close(point.values[2], 100 * point.components[0] / point.components[1]), `${name}: Markup is not Sell Out/Cost`);
  }

  if (!name.includes('Resumo')) {
    assert(props.timelineLimit === 13, `${name}: timeline_limit did not reach renderer`);
    assert(props.summaryCount === 0, `${name}: summary_count zero did not reach renderer`);
    assert(props.timeline.slice(-props.timelineLimit).length === 13, `${name}: renderer does not display thirteen periods`);
    if (name.includes('semanal')) assert(props.timeline.length === 13, `${name}: weekly dataset must already be TOP 13`);
  }
}

console.log(`${checks} real-runtime Panorama sales checks passed.`);
