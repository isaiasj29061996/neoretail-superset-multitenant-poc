import { t, validateNonEmpty } from '@superset-ui/core';
import { sharedControls } from '@superset-ui/chart-controls';

const metricControl = label => ({
  ...sharedControls.metric,
  label,
  validators: [validateNonEmpty],
});

export default {
  controlPanelSections: [
    {
      label: t('Consulta'),
      expanded: true,
      controlSetRows: [
        ['x_axis'],
        ['time_grain_sqla'],
        ['time_range'],
        [
          {
            name: 'metric',
            config: metricControl(t('Métrica principal')),
          },
        ],
        [
          {
            name: 'critical_metric',
            config: metricControl(t('Itens críticos')),
          },
        ],
        [
          {
            name: 'risk_metric',
            config: metricControl(t('Itens com risco')),
          },
        ],
        ['adhoc_filters'],
        ['row_limit'],
      ],
    },
    {
      label: t('Apresentação'),
      expanded: true,
      controlSetRows: [
        [
          {
            name: 'card_title',
            config: {
              type: 'TextControl',
              label: t('Título'),
              default: 'TVD - Pré-ruptura',
              renderTrigger: true,
            },
          },
        ],
        [
          {
            name: 'help_text',
            config: {
              type: 'TextControl',
              label: t('Explicação do indicador'),
              default: 'Estimativa de venda em risco por pré-ruptura.',
              renderTrigger: true,
            },
          },
        ],
        [
          {
            name: 'number_format_type',
            config: {
              type: 'SelectControl',
              label: t('Formato'),
              default: 'currency',
              choices: [
                ['currency', t('Moeda (R$)')],
                ['number', t('Número')],
                ['percent', t('Percentual')],
              ],
              renderTrigger: true,
            },
          },
        ],
        [
          {
            name: 'lower_is_better',
            config: {
              type: 'CheckboxControl',
              label: t('Menor valor é melhor'),
              default: true,
              renderTrigger: true,
            },
          },
        ],
        [
          {
            name: 'show_tasks',
            config: {
              type: 'CheckboxControl',
              label: t('Mostrar tarefas do dia'),
              default: true,
              renderTrigger: true,
            },
          },
        ],
        [
          {
            name: 'accent_color',
            config: {
              type: 'TextControl',
              label: t('Cor da área'),
              default: '#7C4AD9',
              renderTrigger: true,
            },
          },
        ],
        [
          {
            name: 'analysis_url',
            config: {
              type: 'TextControl',
              label: t('Destino de Ir para análise'),
              default: '',
              description: t('Pode permanecer vazio enquanto a página detalhada não existir.'),
              renderTrigger: true,
            },
          },
        ],
      ],
    },
  ],
};
