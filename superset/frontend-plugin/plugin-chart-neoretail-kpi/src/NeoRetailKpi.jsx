import React from 'react';

const formatValue = (value, type) => {
  const options = type === 'currency'
    ? { style: 'currency', currency: 'BRL', notation: 'compact', maximumFractionDigits: 2 }
    : type === 'percent'
      ? { style: 'percent', maximumFractionDigits: 2 }
      : { notation: 'compact', maximumFractionDigits: 2 };
  return new Intl.NumberFormat('pt-BR', options).format(type === 'percent' ? value / 100 : value);
};

const trend = (value, reference, lowerIsBetter) => {
  if (value === reference) return { symbol: '•', color: '#8A929C' };
  const increased = value > reference;
  const favorable = lowerIsBetter ? !increased : increased;
  return {
    symbol: increased ? '↑' : '↓',
    color: favorable ? '#4D9669' : '#D34A3F',
  };
};

const areaPoints = (series, width = 300, height = 94) => {
  if (!series.length) return { line: '', polygon: '' };
  const values = series.map(row => row.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(max - min, 1);
  const line = series.map((row, index) => {
    const x = series.length === 1 ? width / 2 : (index / (series.length - 1)) * width;
    const y = height - 8 - ((row.value - min) / range) * (height - 24);
    return `${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(' ');
  return { line, polygon: `0,${height} ${line} ${width},${height}` };
};

const styles = {
  card: { boxSizing: 'border-box', width: '100%', height: '100%', minHeight: 300, overflow: 'hidden', border: '1px solid #E6EAF0', borderRadius: 8, background: '#FFF', color: '#333', fontFamily: 'Inter, Segoe UI, Arial, sans-serif' },
  header: { display: 'flex', alignItems: 'center', gap: 7, height: 43, padding: '0 15px', borderBottom: '1px solid #EDF0F4', fontSize: 14 },
  info: { display: 'inline-grid', placeItems: 'center', width: 14, height: 14, padding: 0, border: '1px solid #8B929B', borderRadius: '50%', background: 'transparent', color: '#737A83', fontSize: 9, fontWeight: 700, cursor: 'help' },
  metrics: { display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 8, padding: '20px 12px 8px' },
  label: { display: 'block', marginBottom: 7, color: '#6C727A', fontSize: 10 },
  value: { display: 'block', overflow: 'hidden', color: '#0F477E', fontSize: 13, fontWeight: 700, whiteSpace: 'nowrap', textOverflow: 'ellipsis' },
  section: { display: 'block', margin: '0 12px 7px', color: '#146398', fontSize: 10 },
  task: { margin: '0 9px 5px', padding: '5px 8px', background: '#FFB719', color: '#252525', fontSize: 10, textAlign: 'center' },
  action: { display: 'block', width: '100%', padding: '9px 12px 11px', border: 0, background: 'transparent', color: '#8A8F96', fontSize: 10, textAlign: 'center', textDecoration: 'none' },
};

export default function NeoRetailKpi(props) {
  const {
    width, height, title, helpText, formatType, lowerIsBetter, showTasks,
    accentColor, analysisUrl, mtd, previous, averageU3m, critical, risk,
    series, hasData,
  } = props;

  if (!hasData) {
    return <div style={{ ...styles.card, display: 'grid', placeItems: 'center', color: '#6C727A' }}>Sem dados para os filtros selecionados.</div>;
  }

  const currentTrend = trend(mtd, previous, lowerIsBetter);
  const previousTrend = trend(previous, averageU3m, lowerIsBetter);
  const points = areaPoints(series);
  const taskHeight = showTasks ? 110 : 32;
  const areaHeight = Math.max(70, Math.min(150, height - 43 - 75 - taskHeight));

  return (
    <div style={{ ...styles.card, width, height }}>
      <header style={styles.header}>
        <strong>{title}</strong>
        <button type="button" style={styles.info} title={helpText} aria-label={helpText || 'Informações sobre o indicador'}>i</button>
      </header>

      <div style={styles.metrics}>
        <div><span style={styles.label}>MTD</span><span style={styles.value}><b style={{ color: currentTrend.color, fontSize: 17 }}>{currentTrend.symbol}</b> {formatValue(mtd, formatType)}</span></div>
        <div><span style={styles.label}>Mês anterior</span><span style={styles.value}><b style={{ color: previousTrend.color, fontSize: 17 }}>{previousTrend.symbol}</b> {formatValue(previous, formatType)}</span></div>
        <div><span style={styles.label}>Média U3M</span><span style={styles.value}>{formatValue(averageU3m, formatType)}</span></div>
      </div>

      <svg viewBox="0 0 300 94" preserveAspectRatio="none" role="img" aria-label={`Evolução diária de ${title}`} style={{ display: 'block', width: 'calc(100% - 24px)', height: areaHeight, margin: '0 12px 7px', borderBottom: '1px solid #D9DDE3' }}>
        <polygon points={points.polygon} fill={accentColor} fillOpacity="0.38" />
        <polyline points={points.line} fill="none" stroke={accentColor} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>

      {showTasks && (
        <>
          <span style={styles.section}>Tarefas do dia</span>
          <div style={styles.task}>{new Intl.NumberFormat('pt-BR').format(critical)} itens críticos</div>
          <div style={styles.task}>{new Intl.NumberFormat('pt-BR').format(risk)} itens com risco</div>
        </>
      )}

      {analysisUrl ? (
        <a href={analysisUrl} target="_top" rel="noreferrer" style={styles.action}>Ir para análise ›</a>
      ) : (
        <button type="button" disabled aria-disabled="true" style={{ ...styles.action, cursor: 'default' }}>Ir para análise ›</button>
      )}
    </div>
  );
}
