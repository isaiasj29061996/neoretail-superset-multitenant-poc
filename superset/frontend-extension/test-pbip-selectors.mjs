import assert from 'node:assert/strict';
import { selectorDependencyIds, selectorOptionLabel, selectorFilterValues } from './pbipSelectorDependencies.mjs';

let checks = 0;
function check(actual, expected) { assert.deepEqual(actual, expected); checks += 1; }
const band = {
  id: 'band', cascadeParentIds: ['rede'],
  controlValues: { pbipSelectorContext: true, pbipContextParentIds: ['rede', 'loja', 'uf', 'band', 'loja'] },
};
check(selectorDependencyIds(band), ['rede', 'loja', 'uf']);
check(selectorDependencyIds({ id: 'loja', controlValues: { pbipSelectorContext: true, pbipContextParentIds: ['band', 'uf'] } }), ['band', 'uf']);
check(selectorDependencyIds({ ...band, controlValues: {} }), ['rede']);
check(selectorDependencyIds({ ...band, controlValues: { ...band.controlValues, pbipSelectorContext: false } }), ['rede']);
check(selectorDependencyIds({ id: 'measure', controlValues: { pbipSelectorContext: true, pbipContextParentIds: [] } }), []);
check(selectorDependencyIds({ id: 'item', controlValues: { pbipSelectorContext: true, pbipContextParentIds: ['measure', 'brand'] } }), ['measure', 'brand']);
check(selectorDependencyIds(undefined), undefined);
check(selectorDependencyIds({ ...band, controlValues: { pbipSelectorContext: true } }), []);
// Selection changes are projected as dependencies; they never mutate another
// selector's data mask or invent a reverse edge into conversion dimensions.
const masks = { rede: ['ARMAZMATEUS'], band: ['MATEUS SUPERMERCADOS'], loja: ['real-location'], uf: [] };
const previous = structuredClone(masks);
check(selectorDependencyIds(band).map(id => masks[id]), [['ARMAZMATEUS'], ['real-location'], []]);
check(masks, previous);
check(selectorOptionLabel('F', 'F', { pbipSelectorContext: true, pbipOptionLabels: { F: 'Fast Mover' } }), 'Fast Mover');
check(selectorOptionLabel('F', 'F', { pbipOptionLabels: { F: 'Fast Mover' } }), 'F');
check(selectorOptionLabel('unknown', 'original', { pbipSelectorContext: true, pbipOptionLabels: { F: 'Fast Mover' } }), 'original');
const grouped = { pbipSelectorContext: true, pbipOptionValueCodes: { 'Não Informado': ['I', 'W'], 'Fast Mover': ['F'] } };
check(selectorFilterValues(['Não Informado'], grouped), ['I', 'W']);
check(selectorFilterValues(['Não Informado', 'Fast Mover'], grouped), ['I', 'W', 'F']);
check(selectorFilterValues(['Não Informado', 'Não Informado'], grouped), ['I', 'W']);
check(selectorFilterValues(['Não Informado'], { ...grouped, pbipSelectorContext: false }), ['Não Informado']);
check(selectorFilterValues(null, grouped), null);
console.log(JSON.stringify({ pbip_selector_frontend: 'passed', checks }));
