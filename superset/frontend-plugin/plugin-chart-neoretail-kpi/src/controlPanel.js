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
        [
          {
            name: 'x_axis',
            config: {
              ...sharedControls.x_axis,
              validators: [validateNonEmpty],
              description: t('Selecione data como coluna temporal no dataset gold.vw_mart_visao_industria.'),
            },
          },
        ],
        ['time_grain_sqla'],
        ['time_range'],
        ['metrics'],
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
        ['groupby'],
        ['row_limit'],
      ],
    },
    {
      label: t('Apresentação'),
      expanded: true,
      controlSetRows: [
        [
          {
            name: 'card_variant',
            config: {
              type: 'SelectControl',
              label: t('Tipo de card'),
              default: 'area',
              choices: [
                ['area', t('Área com tarefas')],
                ['bars', t('Barras comparativas')],
                ['multi', t('Indicadores múltiplos')],
                ['osa', t('OSA com tarefas')],
                ['panorama', t('Evolutivo panorama')],
                ['panoramasummary', t('Resumo do evolutivo panorama')],
                ['rankbars', t('Ranking em barras')],
                ['stacked', t('Colunas empilhadas')],
                ['verticalbars', t('Barras verticais')],
                ['headlinearea', t('Indicador com área')],
                ['stackedrank', t('Ranking empilhado')],
              ],
              renderTrigger: true,
            },
          },
        ],
        [
          {
            name: 'chart_styles',
            config: { type: 'TextControl', label: t('Estilos das séries'), description: t('bar ou line; separe por |.'), default: 'bar|bar|line', renderTrigger: true },
          },
        ],
        [
          {
            name: 'summary_count',
            config: { type: 'TextControl', label: t('Quantidade de resumos'), default: '', renderTrigger: true },
          },
        ],
        [
          {
            name: 'metric_semantics',
            config: {
              type: 'TextControl',
              label: t('Semantica das metricas'),
              description: t('Perfil:inicio:quantidade; separe as saidas por |.'),
              default: '',
              renderTrigger: true,
            },
          },
        ],
        [
          {
            name: 'timeline_limit',
            config: {
              type: 'TextControl',
              label: t('Limite de periodos'),
              default: '12',
              renderTrigger: true,
            },
          },
        ],
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
            name: 'metric_labels',
            config: { type: 'TextControl', label: t('Rótulos das métricas'), description: t('Separe por |.'), default: '', renderTrigger: true },
          },
        ],
        [
          {
            name: 'metric_formats',
            config: { type: 'TextControl', label: t('Formatos'), description: t('currency, number ou percent; separe por |.'), default: 'currency', renderTrigger: true },
          },
        ],
        [
          {
            name: 'metric_directions',
            config: { type: 'TextControl', label: t('Direção favorável'), description: t('higher ou lower; separe por |.'), default: 'lower', renderTrigger: true },
          },
        ],
        [
          {
            name: 'task_labels',
            config: { type: 'TextControl', label: t('Rótulos das tarefas'), description: t('Separe por |.'), default: 'itens críticos|itens com risco', renderTrigger: true },
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
            name: 'show_annual',
            config: {
              type: 'CheckboxControl',
              label: t('Mostrar anual 12M'),
              default: false,
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
