import { ChartMetadata, ChartPlugin, t } from '@superset-ui/core';

import buildQuery from './buildQuery';
import controlPanel from './controlPanel';
import transformProps from './transformProps';

const thumbnail = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(`
<svg xmlns="http://www.w3.org/2000/svg" width="240" height="160" viewBox="0 0 240 160">
  <rect width="240" height="160" rx="10" fill="#e7f0f5"/>
  <rect x="12" y="10" width="216" height="140" rx="8" fill="white" stroke="#dce4ea"/>
  <text x="25" y="32" font-family="Arial" font-size="14" font-weight="700" fill="#333">NeoRetail KPI</text>
  <text x="25" y="58" font-family="Arial" font-size="9" fill="#666">MTD</text><text x="91" y="58" font-family="Arial" font-size="9" fill="#666">Mês anterior</text><text x="166" y="58" font-family="Arial" font-size="9" fill="#666">Média U3M</text>
  <text x="25" y="76" font-family="Arial" font-size="12" font-weight="700" fill="#0f477e">R$ 15,2K</text><text x="91" y="76" font-family="Arial" font-size="12" font-weight="700" fill="#0f477e">R$ 93,6K</text><text x="166" y="76" font-family="Arial" font-size="12" font-weight="700" fill="#0f477e">R$ 121K</text>
  <path d="M25 93 L89 93 L143 108 L215 140 L25 140 Z" fill="#c8b2ef"/><path d="M25 93 L89 93 L143 108 L215 140" fill="none" stroke="#7c4ad9" stroke-width="2"/>
</svg>`)}`;

export default class NeoRetailKpiChartPlugin extends ChartPlugin {
  constructor() {
    const metadata = new ChartMetadata({
      category: t('KPI'),
      description: t(
        'Card NeoRetail com comparativos, tendência diária, tarefas e navegação.',
      ),
      name: t('NeoRetail KPI Card'),
      tags: [t('KPI'), t('NeoRetail')],
      thumbnail,
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
