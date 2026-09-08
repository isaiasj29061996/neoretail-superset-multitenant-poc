import fs from 'node:fs';

const presetPath = '/src/superset-frontend/src/visualizations/presets/MainPreset.js';
let source = fs.readFileSync(presetPath, 'utf8');

const importLine = "import NeoRetailKpiChartPlugin from '../../../plugins/plugin-chart-neoretail-kpi/src';\n";
if (!source.includes('NeoRetailKpiChartPlugin')) {
  source = `${importLine}${source}`;
}

const registration = "new NeoRetailKpiChartPlugin().configure({ key: 'neoretail-kpi-card' }),";
if (!source.includes("key: 'neoretail-kpi-card'")) {
  const anchors = ['const plugins = [', 'plugins: ['];
  const anchor = anchors.find(candidate => source.includes(candidate));
  if (!anchor) {
    throw new Error(`Nao foi possivel localizar a lista de plugins em ${presetPath}`);
  }
  source = source.replace(anchor, `${anchor}\n      ${registration}`);
}

fs.writeFileSync(presetPath, source);
console.log('NeoRetail KPI Card registrado no MainPreset.');
