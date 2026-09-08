import { ChartMetadata, ChartPlugin, t } from '@superset-ui/core';

import buildQuery from './buildQuery';
import controlPanel from './controlPanel';
import transformProps from './transformProps';

export default class NeoRetailKpiChartPlugin extends ChartPlugin {
  constructor() {
    const metadata = new ChartMetadata({
      category: t('KPI'),
      description: t(
        'Card NeoRetail com comparativos, tendência diária, tarefas e navegação.',
      ),
      name: t('NeoRetail KPI Card'),
      tags: [t('KPI'), t('NeoRetail')],
    });

    super({
      buildQuery,
      controlPanel,
      loadChart: () => import('./NeoRetailKpi'),
      metadata,
      transformProps,
    });
  }
}
