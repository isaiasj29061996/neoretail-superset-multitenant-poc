import React from 'react';

import NeoRetailKpi from './NeoRetailKpi';
import formatValue from './formatValue';

const trend = (value, reference, lowerIsBetter) => {
  if (value == null || reference == null) return { symbol: '', color: '#8A929C' };
  if (value === reference) return { symbol: '•', color: '#8A929C' };
  const increased = value > reference;
  return {
    symbol: increased ? '↑' : '↓',
    color: (lowerIsBetter ? !increased : increased) ? '#4D9669' : '#D0342C',
  };
};

const styles = {
  card: {
    boxSizing: 'border-box', width: '100%', height: '100%', minHeight: 250,
    overflow: 'hidden', border: '1px solid #DCE4EA', borderRadius: 8,
    background: '#FFF', color: '#333', fontFamily: 'Inter, Segoe UI, Arial, sans-serif',
  },
  header: {
    display: 'flex', alignItems: 'center', gap: 7, height: 43, padding: '0 15px',
    borderBottom: '1px solid #EDF0F4', fontSize: 14,
  },
  info: {
    display: 'inline-grid', placeItems: 'center', width: 14, height: 14, padding: 0,
    border: '1px solid #8B929B', borderRadius: '50%', background: 'transparent',
    color: '#737A83', fontSize: 9, fontWeight: 700,
  },
  section: { display: 'block', margin: '9px 12px 1px', color: '#333', fontSize: 11, fontWeight: 600 },
  metrics: {
    display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 8,
    padding: '9px 12px 8px',
  },
  label: { display: 'block', marginBottom: 6, color: '#666', fontSize: 10 },
  value: {
    display: 'block', overflow: 'hidden', color: '#0F477E', fontSize: 13,
    fontWeight: 700, whiteSpace: 'nowrap', textOverflow: 'ellipsis',
  },
  taskTitle: { display: 'block', margin: '3px 12px 7px', color: '#146398', fontSize: 10 },
  task: {
    margin: '0 9px 5px', padding: '5px 8px', background: '#FFBD14',
    color: '#252525', fontSize: 10, textAlign: 'center',
  },
  action: {
    display: 'block', width: '100%', padding: '7px 12px 9px', border: 0,
    background: 'transparent', color: '#8A8F96', fontSize: 10,
    textAlign: 'center', textDecoration: 'none',
  },
};

function ValuesTriplet({ indicator, values, showTrends }) {
  const current = trend(values.current, values.previous, indicator.lowerIsBetter);
  const previous = trend(values.previous, values.average, indicator.lowerIsBetter);
  return <div style={styles.metrics}>
    <div>
      <span style={styles.label}>MTD</span>
      <span style={styles.value}>
        {showTrends && <b style={{ color: current.color, fontSize: 17 }}>{current.symbol} </b>}
        {formatValue(values.current, indicator.format)}
      </span>
    </div>
    <div>
      <span style={styles.label}>Mês anterior</span>
      <span style={styles.value}>
        {showTrends && <b style={{ color: previous.color, fontSize: 17 }}>{previous.symbol} </b>}
        {formatValue(values.previous, indicator.format)}
      </span>
    </div>
    <div>
      <span style={styles.label}>Média U3M</span>
      <span style={styles.value}>{formatValue(values.average, indicator.format)}</span>
    </div>
  </div>;
}

function Tasks({ critical, risk, labels }) {
  return <>
    <span style={styles.taskTitle}>Tarefas do dia</span>
    <div style={styles.task}>{new Intl.NumberFormat('pt-BR').format(critical)} {labels[0]}</div>
    <div style={styles.task}>{new Intl.NumberFormat('pt-BR').format(risk)} {labels[1]}</div>
  </>;
}

function QuantityComparison(props) {
  const {
    width, height, title, helpText, variant, indicators, timeline,
    showTasks, critical, risk, taskLabels, analysisUrl,
  } = props;
  const indicator = indicators?.[0];
  if (!indicator || !props.hasData) {
    return <div style={{ ...styles.card, width, height, display: 'grid', placeItems: 'center', color: '#6C727A' }}>
      Sem dados para os filtros selecionados.
    </div>;
  }
  const showTrends = variant !== 'quantitycompareplain';
  const comparisons = indicators.map(entry => ({
    indicator: entry,
    lastYear: entry.lastYear || { current: null, previous: null, average: null },
  }));
  return <div data-neoretail-variant={variant} style={{ ...styles.card, width, height }}>
    <header style={styles.header}>
      <strong>{title}</strong><span style={styles.info} title={helpText}>i</span>
    </header>
    {comparisons.map(({ indicator: entry, lastYear }) => <React.Fragment key={entry.label}>
      <span style={styles.section}>{indicators.length > 1 ? `${entry.label} — ano atual` : 'Ano atual'}</span>
      <ValuesTriplet indicator={entry} values={entry} showTrends={showTrends} />
      <span style={styles.section}>{indicators.length > 1 ? `${entry.label} — ano anterior` : 'Ano anterior'}</span>
      <ValuesTriplet indicator={entry} values={lastYear} showTrends={showTrends} />
    </React.Fragment>)}
    {showTasks && <Tasks critical={critical} risk={risk} labels={taskLabels} />}
    {showTasks && (analysisUrl
      ? <a href={analysisUrl} target="_top" rel="noreferrer" style={styles.action}>Ir para análise ›</a>
      : <span style={styles.action}>Ir para análise ›</span>)}
  </div>;
}

export default function NeoRetailKpiRouter(props) {
  if (props.variant === 'quantitycompare' || props.variant === 'quantitycompareplain') {
    return <QuantityComparison {...props} />;
  }
  return <NeoRetailKpi {...props} />;
}
