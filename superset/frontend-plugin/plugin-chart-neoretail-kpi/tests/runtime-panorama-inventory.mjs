// Runtime gate for Panorama Giro x ROI, OSA and Falta x Excesso.
import { readFileSync } from 'node:fs';

const fixturePath = process.argv[2];
if (!fixturePath) throw new Error('Usage: node runtime-panorama-inventory.mjs <fixture.json>');

const src = 'superset/frontend-plugin/plugin-chart-neoretail-kpi/src/';
const source = readFileSync(`${src}transformProps.js`, 'utf8')
  .replace(/^import .*;\r?\n/gm, '')
  .replace('export default function', 'return function');
const transform = new Function('getMetricLabel', source)(
  metric => typeof metric === 'string' ? metric : metric.label,
);
const camelize = key => key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
const toFormData = raw => Object.fromEntries(
  Object.entries(raw).map(([key, value]) => [camelize(key), value]),
);
const fixture = JSON.parse(readFileSync(fixturePath, 'utf8'));
let checks = 0;
const assert = (condition, message) => {
  if (!condition) throw new Error(message);
  checks += 1;
};
const close = (left, right) => (
  left === null && right === null
) || Math.abs(left - right) <= Math.max(1e-7, Math.abs(right) * 1e-9);

for (const [name, chart] of Object.entries(fixture.charts)) {
  const props = transform({
    rawFormData: chart.rawFormData,
    formData: toFormData(chart.rawFormData),
    queriesData: chart.queriesData,
  });
  const weekly = name.includes('semanal');

  assert(props.timelineLimit === 13, `${name}: timeline_limit did not reach renderer`);
  assert(props.timeline.length === 13, `${name}: expected exactly 13 rendered periods`);
  assert(chart.queriesData.length === (weekly ? 2 : 1), `${name}: unexpected query count`);
  if (weekly) {
    assert(chart.queriesData[1].data.length > 3, `${name}: missing monthly summary history`);
  }

  if (name.includes('Giro x ROI')) {
    assert(props.indicators.length === 3, `${name}: expected Stock Cost, ROI and Giro`);
    assert(props.indicators[0].label === 'Estoque Preço Custo', `${name}: Stock Cost label diverged`);
    assert(props.indicators[1].label === '% ROI', `${name}: ROI label diverged`);
    assert(props.indicators[2].label === 'Giro', `${name}: Giro label diverged`);
    assert(props.summaryLabels.join('|') === 'U3M|Anual|U3M', `${name}: summary labels diverged`);

    const roiPoint = props.timeline.find(point => (
      point.components[0] != null
      && point.components[1] > 0
      && point.components[2] > 0
      && point.components[3] > 0
    ));
    assert(Boolean(roiPoint), `${name}: no eligible ROI point`);
    const expectedRoi = 100 * (roiPoint.components[1] - roiPoint.components[2]) / roiPoint.components[3];
    assert(close(roiPoint.values[1], expectedRoi), `${name}: ROI formula diverged`);

    const giroPoint = props.timeline.find(point => point.components[5] > 0);
    assert(Boolean(giroPoint), `${name}: no eligible Giro point`);
    assert(close(giroPoint.values[2], giroPoint.components[4] / giroPoint.components[5]), `${name}: Giro formula diverged`);

    const zeroRoiPoint = props.timeline.find(point => (
      point.components[1] === 0 || point.components[2] === 0
    ));
    if (zeroRoiPoint) {
      assert(zeroRoiPoint.values[1] === null, `${name}: ROI zero should be BLANK only in timeline`);
    }
    assert(props.indicators[1].average !== null, `${name}: annual ROI summary missing`);
    assert(props.indicators[2].average !== null, `${name}: Giro U3M missing`);
  } else if (name.includes('OSA')) {
    assert(props.indicators.length === 3, `${name}: expected OSA/Ruptura/ISV`);
    assert(props.indicators.map(item => item.label).join('|') === '% OSA|% Ruptura|% ISV', `${name}: OSA labels diverged`);
    const point = props.timeline.find(entry => entry.components[1] > 0 && entry.components[3] > 0 && entry.components[5] > 0);
    assert(Boolean(point), `${name}: no eligible OSA point`);
    assert(close(point.values[0], 100 * (1 - point.components[0] / point.components[1])), `${name}: OSA formula diverged`);
    assert(close(point.values[1], 100 * point.components[2] / point.components[3]), `${name}: Ruptura denominator diverged`);
    assert(close(point.values[2], 100 * point.components[4] / point.components[5]), `${name}: ISV denominator diverged`);
    assert(props.indicators.every(item => item.average !== null), `${name}: OSA U3M summary missing`);
  } else if (name.includes('Falta x Excesso')) {
    assert(props.indicators.length === 2, `${name}: expected TVD/IVD only`);
    assert(props.indicators.map(item => item.label).join('|') === 'TVD - Risco|IVD - Excesso', `${name}: TVD/IVD labels diverged`);
    assert(props.timeline.every(point => point.values.length === 2), `${name}: unexpected technical series leaked`);
    assert(props.indicators.every(item => item.average !== null), `${name}: TVD/IVD U3M missing`);
  }
}

console.log(`${checks} real-runtime Panorama inventory checks passed.`);
