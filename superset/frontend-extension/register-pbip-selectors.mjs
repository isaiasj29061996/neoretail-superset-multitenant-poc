import fs from 'node:fs';

const base = process.env.SUPERSET_FRONTEND_ROOT || '/src/superset-frontend';
const target = `${base}/src/dashboard/components/nativeFilters/FilterBar/FilterControls/state.ts`;
let source = fs.readFileSync(target, 'utf8');
const original = 'state => state.nativeFilters.filters[id]?.cascadeParentIds,';
const replacement = 'state => selectorDependencyIds(state.nativeFilters.filters[id]),';
const importLine = "import { selectorDependencyIds } from '../../../../pbipSelectorDependencies.mjs';\n";
if (!source.includes(replacement)) {
  if (!source.includes(original)) throw new Error('Superset selector hook anchor changed');
  source = importLine + source.replace(original, replacement);
  fs.writeFileSync(target, source);
}
fs.copyFileSync('/tmp/pbipSelectorDependencies.mjs', `${base}/src/dashboard/pbipSelectorDependencies.mjs`);
const selectPath = `${base}/src/filters/components/Select/SelectFilterPlugin.tsx`;
let select = fs.readFileSync(selectPath, 'utf8');
if (!select.includes('selectorOptionLabel')) {
  const labelAnchor = 'labelFormatter(value, datatype)';
  if (!select.includes(labelAnchor)) throw new Error('Superset option label anchor changed');
  select = "import { selectorOptionLabel, selectorFilterValues } from 'src/dashboard/pbipSelectorDependencies.mjs';\n" +
    select.replaceAll(labelAnchor, 'selectorOptionLabel(value, labelFormatter(value, datatype), formData)');
  const maskAnchor = 'col,\n          values,';
  const inverseAnchor = 'col,\n          filterState.value,';
  if (!select.includes(maskAnchor) || !select.includes(inverseAnchor)) throw new Error('Superset select data mask anchor changed');
  select = select.replace(maskAnchor, 'col,\n          selectorFilterValues(values, formData),')
    .replace(inverseAnchor, 'col,\n          selectorFilterValues(filterState.value, formData),');
  fs.writeFileSync(selectPath, select);
}
console.log('PBIP opt-in selector dependencies registered. Legacy cascade path retained.');
