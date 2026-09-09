import React from 'react';

const formatValue = (value, type) => {
  const options = type === 'decimal'
    ? { minimumFractionDigits: 2, maximumFractionDigits: 2 }
    : type === 'currency'
    ? { style: 'currency', currency: 'BRL', notation: 'compact', maximumFractionDigits: 2 }
    : type === 'percent'
      ? { style: 'percent', maximumFractionDigits: 2 }
      : { notation: 'compact', maximumFractionDigits: 2 };
  return new Intl.NumberFormat('pt-BR', options).format(type === 'percent' ? value / 100 : value);
};
const trend = (value, reference, lowerIsBetter) => {
  if (value === reference) return { symbol: '•', color: '#8A929C' };
  const increased = value > reference;
  return { symbol: increased ? '↑' : '↓', color: (lowerIsBetter ? !increased : increased) ? '#4D9669' : '#D0342C' };
};
const areaPoints = (series, width = 300, height = 94) => {
  if (!series.length) return { line: '', polygon: '' };
  const values = series.map(row => row.value);
  const min = Math.min(...values); const max = Math.max(...values); const range = Math.max(max - min, 1);
  const line = series.map((row, index) => `${(series.length === 1 ? width / 2 : index / (series.length - 1) * width).toFixed(2)},${(height - 8 - (row.value - min) / range * (height - 24)).toFixed(2)}`).join(' ');
  return { line, polygon: `0,${height} ${line} ${width},${height}` };
};
const styles = {
  card: { boxSizing: 'border-box', width: '100%', height: '100%', minHeight: 250, overflow: 'hidden', border: '1px solid #DCE4EA', borderRadius: 8, background: '#FFF', color: '#333', fontFamily: 'Inter, Segoe UI, Arial, sans-serif' },
  header: { display: 'flex', alignItems: 'center', gap: 7, height: 43, padding: '0 15px', borderBottom: '1px solid #EDF0F4', fontSize: 14 },
  info: { display: 'inline-grid', placeItems: 'center', width: 14, height: 14, padding: 0, border: '1px solid #8B929B', borderRadius: '50%', background: 'transparent', color: '#737A83', fontSize: 9, fontWeight: 700 },
  metrics: { display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 8, padding: '15px 12px 8px' },
  label: { display: 'block', marginBottom: 6, color: '#666', fontSize: 10 },
  value: { display: 'block', overflow: 'hidden', color: '#0F477E', fontSize: 13, fontWeight: 700, whiteSpace: 'nowrap', textOverflow: 'ellipsis' },
  section: { display: 'block', margin: '6px 12px 2px', color: '#333', fontSize: 11, fontWeight: 600 },
  taskTitle: { display: 'block', margin: '3px 12px 7px', color: '#146398', fontSize: 10 },
  task: { margin: '0 9px 5px', padding: '5px 8px', background: '#FFBD14', color: '#252525', fontSize: 10, textAlign: 'center' },
  action: { display: 'block', width: '100%', padding: '7px 12px 9px', border: 0, background: 'transparent', color: '#8A8F96', fontSize: 10, textAlign: 'center', textDecoration: 'none' },
};

const MetricTriplet = ({ indicator }) => {
  const current = trend(indicator.current, indicator.previous, indicator.lowerIsBetter);
  const previous = trend(indicator.previous, indicator.average, indicator.lowerIsBetter);
  return <div style={styles.metrics}>
    <div><span style={styles.label}>MTD</span><span style={styles.value}><b style={{ color: current.color, fontSize: 17 }}>{current.symbol}</b> {formatValue(indicator.current, indicator.format)}</span></div>
    <div><span style={styles.label}>Mês anterior</span><span style={styles.value}><b style={{ color: previous.color, fontSize: 17 }}>{previous.symbol}</b> {formatValue(indicator.previous, indicator.format)}</span></div>
    <div><span style={styles.label}>Média U3M</span><span style={styles.value}>{formatValue(indicator.average, indicator.format)}</span></div>
  </div>;
};
const Tasks = ({ critical, risk, labels }) => <>
  <span style={styles.taskTitle}>Tarefas do dia</span>
  <div style={styles.task}>{new Intl.NumberFormat('pt-BR').format(critical)} {labels[0]}</div>
  <div style={styles.task}>{new Intl.NumberFormat('pt-BR').format(risk)} {labels[1]}</div>
</>;

const HeadlineArea = ({ indicator, timeline, accentColor }) => {
  const observations = timeline.map(point => ({ value: point.values[0] }));
  const points = areaPoints(observations, 600, 130);
  return <div style={{ display: 'grid', gridTemplateRows: '54px 1fr', height: 'calc(100% - 44px)', padding: '8px 18px 0' }}>
    <strong style={{ alignSelf: 'center', color: '#0F477E', fontSize: 28 }}>{formatValue(indicator.current, indicator.format)}</strong>
    <svg viewBox="0 0 600 130" preserveAspectRatio="none" role="img" aria-label={`Evolução de ${indicator.label}`} style={{ width: '100%', height: '100%', minHeight: 100, borderBottom: '1px solid #D9DDE3' }}>
      <polygon points={points.polygon} fill={accentColor} fillOpacity="0.42" />
      <polyline points={points.line} fill="none" stroke={accentColor} strokeWidth="1.8" />
    </svg>
  </div>;
};

const Panorama = ({ indicators, timeline, chartStyles, summaryCount }) => {
  const points = timeline.slice(-12);
  const colors = ['#00557C', '#4F86BF', '#858585', '#7C4AD9'];
  const maxima = indicators.map((_, metricIndex) => Math.max(1, ...points.map(point => Math.abs(point.values[metricIndex] || 0))));
  const pointX = index => 22 + (points.length === 1 ? 390 : index / (points.length - 1) * 780);
  const pointY = (metricIndex, value) => 190 - Math.abs(value || 0) / maxima[metricIndex] * 145;
  const linePath = metricIndex => points.map((point, index) => {
    const x = pointX(index);
    const y = pointY(metricIndex, point.values[metricIndex]);
    return `${index ? 'L' : 'M'} ${x.toFixed(1)} ${y.toFixed(1)}`;
  }).join(' ');
  return <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr', height: 'calc(100% - 44px)' }}>
    <div style={{ padding: '10px 16px', borderRight: '1px solid #E2E6EA' }}>{indicators.slice(0, summaryCount).map(indicator => <div key={indicator.label} style={{ marginBottom: 13 }}><b style={{ display: 'block', fontSize: 11 }}>{indicator.label}</b><div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', marginTop: 5 }}><span><small style={styles.label}>MTD</small><strong style={styles.value}>{formatValue(indicator.current, indicator.format)}</strong></span><span><small style={styles.label}>U3M</small><strong style={styles.value}>{formatValue(indicator.average, indicator.format)}</strong></span></div></div>)}</div>
    <svg viewBox="0 0 840 225" preserveAspectRatio="none" style={{ width: '100%', height: '100%', minHeight: 230 }}>
      <line x1="20" y1="190" x2="820" y2="190" stroke="#D8DDE2" />
      {indicators.map((indicator, metricIndex) => chartStyles[metricIndex] === 'hidden' ? null : chartStyles[metricIndex] === 'line'
        ? <g key={indicator.label}>
          <path d={linePath(metricIndex)} fill="none" stroke={colors[metricIndex]} strokeWidth="3" />
          {points.map((point, index) => {
            const x = pointX(index); const y = pointY(metricIndex, point.values[metricIndex]);
            const labelY = y < 22 ? y + 15 : y - 8;
            return <g key={`${indicator.label}-point-${index}`}>
              <circle cx={x} cy={y} r="2.7" fill={colors[metricIndex]} />
              <text x={x} y={labelY} textAnchor="middle" fontSize="8" fontWeight="700" fill={colors[metricIndex]} stroke="#FFF" strokeWidth="3" paintOrder="stroke">{formatValue(point.values[metricIndex], indicator.format)}</text>
            </g>;
          })}
        </g>
        : points.map((point, index) => {
          const slot = 780 / Math.max(points.length, 1); const barWidth = Math.min(24, slot / (indicators.length + 1));
          const h = Math.abs(point.values[metricIndex] || 0) / maxima[metricIndex] * 145;
          const x = 22 + index * slot + metricIndex * barWidth; const y = 190 - h;
          return <g key={`${indicator.label}-${index}`}>
            <rect x={x} y={y} width={barWidth - 2} height={h} fill={colors[metricIndex]} />
            <text x={x + (barWidth - 2) / 2} y={Math.max(12, y - 5)} textAnchor="middle" fontSize="8" fontWeight="700" fill={colors[metricIndex]} stroke="#FFF" strokeWidth="3" paintOrder="stroke">{formatValue(point.values[metricIndex], indicator.format)}</text>
          </g>;
        }))}
      {points.map((point, index) => <text key={point.date.toISOString()} x={22 + index * (780 / Math.max(points.length, 1))} y="210" fontSize="9" fill="#666">{point.date.toLocaleDateString('pt-BR', { month: 'short', timeZone: 'UTC' })}</text>)}
    </svg>
  </div>;
};

const StackedBars = ({ indicators, timeline }) => {
  const points = timeline.slice(-8);
  const colors = ['#17376F', '#07567E', '#1095C6', '#7C43DF'];
  return <div style={{ display: 'flex', alignItems: 'end', gap: 22, height: 'calc(100% - 78px)', padding: '18px 55px 28px' }}>{points.map(point => {
    const total = Math.max(1, point.values.reduce((sum, value) => sum + Math.abs(value), 0));
    return <div key={point.date.toISOString()} style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'end' }}><div style={{ height: '100%', display: 'flex', flexDirection: 'column-reverse', justifyContent: 'start' }}>{point.values.map((value, index) => <div key={indicators[index]?.label || index} title={`${indicators[index]?.label}: ${formatValue(value, 'percent')}`} style={{ display: 'grid', placeItems: 'center', minHeight: value ? 16 : 0, height: `${Math.abs(value) / total * 100}%`, background: colors[index], color: '#fff', fontSize: 9 }}>{Math.abs(value) >= 5 ? formatValue(value, 'percent') : ''}</div>)}</div><span style={{ marginTop: 6, color: '#666', fontSize: 9, textAlign: 'center' }}>{point.date.toLocaleDateString('pt-BR', { month: 'long', timeZone: 'UTC' })}</span></div>;
  })}</div>;
};

const VerticalBars = ({ items, format }) => {
  const visible = items.slice(0, 15); const max = Math.max(1, ...visible.map(item => Math.abs(item.value)));
  return <div style={{ display: 'flex', alignItems: 'end', gap: 12, height: 'calc(100% - 58px)', padding: '18px 40px 35px' }}>{visible.map((item, index) => <div key={item.category} style={{ flex: 1, minWidth: 0, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'end' }}><span style={{ marginBottom: 4, color: '#666', fontSize: 8, textAlign: 'center' }}>{formatValue(item.value, format)}</span><div style={{ height: `${Math.max(1, Math.abs(item.value) / max * 92)}%`, background: index ? '#55BCE9' : '#00557C' }} /><span title={item.category} style={{ height: 30, marginTop: 5, overflow: 'hidden', color: '#666', fontSize: 8, textAlign: 'center' }}>{item.category}</span></div>)}</div>;
};

const StackedRankBars = ({ items, indicators }) => {
  const visible = items.slice(0, 10);
  const colors = ['#7C43DF', '#C91878', '#1095C6', '#07567E'];
  const totals = visible.map(item => item.values.reduce((sum, value) => sum + Math.abs(value), 0));
  const max = Math.max(1, ...totals);
  return <div style={{ display: 'grid', gridTemplateRows: '1fr 24px', height: 'calc(100% - 58px)', padding: '14px 24px 8px' }}>
    <div style={{ display: 'flex', alignItems: 'end', gap: 7, minHeight: 0 }}>{visible.map((item, itemIndex) => {
      const total = Math.max(1, totals[itemIndex]);
      return <div key={item.category} style={{ flex: 1, minWidth: 0, height: '100%', display: 'grid', gridTemplateRows: '1fr 45px', alignItems: 'end' }}>
        <div style={{ width: '100%', height: `${Math.max(2, total / max * 100)}%`, display: 'flex', flexDirection: 'column-reverse', justifySelf: 'center' }}>{item.values.map((value, metricIndex) => {
          const share = Math.abs(value) / total * 100;
          return <div key={indicators[metricIndex]?.label || metricIndex} title={`${indicators[metricIndex]?.label}: ${formatValue(value, indicators[metricIndex]?.format || 'number')}`} style={{ display: 'grid', placeItems: 'center', minHeight: value ? 17 : 0, height: `${share}%`, background: colors[metricIndex], color: '#FFF', fontSize: 8, fontWeight: 700 }}>{share >= 7 ? formatValue(value, indicators[metricIndex]?.format || 'number') : ''}</div>;
        })}</div>
        <span title={item.category} style={{ paddingTop: 5, overflow: 'hidden', color: '#666', fontSize: 8, lineHeight: 1.2, textAlign: 'center' }}>{item.category}</span>
      </div>;
    })}</div>
    <div style={{ display: 'flex', justifyContent: 'center', gap: 14, paddingTop: 5 }}>{indicators.map((indicator, index) => <span key={indicator.label} style={{ color: '#666', fontSize: 9 }}><i style={{ display: 'inline-block', width: 9, height: 9, marginRight: 4, background: colors[index] }} />{indicator.label}</span>)}</div>
  </div>;
};

const RankBars = ({ items, format }) => {
  const max = Math.max(1, ...items.map(item => Math.abs(item.value)));
  return <div style={{ padding: '12px 16px' }}>{items.slice(0, 10).map(item => <div key={item.category} style={{ display: 'grid', gridTemplateColumns: '105px 1fr 75px', gap: 7, alignItems: 'center', marginBottom: 9 }}><span style={{ overflow: 'hidden', fontSize: 10, textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.category}</span><span style={{ display: 'block', height: 18, width: `${Math.max(1, Math.abs(item.value) / max * 100)}%`, background: '#00557C' }} /><span style={{ color: '#666', fontSize: 9 }}>{formatValue(item.value, format)}</span></div>)}</div>;
};

export default function NeoRetailKpi(props) {
  const { width, height, title, helpText, variant, accentColor, analysisUrl, showTasks, taskLabels, chartStyles, summaryCount, indicators, critical, risk, series, timeline, bars, rankItems, rankSeries, hasData } = props;
  if (!hasData || !indicators.length) return <div style={{ ...styles.card, display: 'grid', placeItems: 'center', color: '#6C727A' }}>Sem dados para os filtros selecionados.</div>;
  const points = areaPoints(series);
  const maxBar = Math.max(1, ...bars.flatMap(item => [item.current, item.previous]));
  return <div data-neoretail-variant={variant} style={{ ...styles.card, width, height }}>
    <header style={styles.header}><strong>{title}</strong><span style={styles.info} title={helpText}>i</span></header>
    {variant === 'panorama' ? <Panorama indicators={indicators} timeline={timeline} chartStyles={chartStyles} summaryCount={summaryCount} /> : variant === 'headlinearea' ? <HeadlineArea indicator={indicators[0]} timeline={timeline} accentColor={accentColor} /> : variant === 'stackedrank' ? <StackedRankBars items={rankSeries} indicators={indicators} /> : variant === 'stacked' ? <StackedBars indicators={indicators} timeline={timeline} /> : variant === 'verticalbars' ? <VerticalBars items={rankItems} format={indicators[0]?.format || 'number'} /> : variant === 'rankbars' ? <RankBars items={rankItems} format={indicators[0]?.format || 'number'} /> : variant === 'multi' || variant === 'osa' ? indicators.map(indicator => <div key={indicator.label}><span style={styles.section}>{indicator.label}</span><MetricTriplet indicator={indicator} /></div>) : <MetricTriplet indicator={indicators[0]} />}
    {variant === 'area' && <svg viewBox="0 0 300 94" preserveAspectRatio="none" role="img" aria-label={`Evolução de ${title}`} style={{ display: 'block', width: 'calc(100% - 24px)', height: Math.max(65, Math.min(130, height - 225)), margin: '0 12px 7px', borderBottom: '1px solid #D9DDE3' }}><polygon points={points.polygon} fill={accentColor} fillOpacity="0.4" /><polyline points={points.line} fill="none" stroke={accentColor} strokeWidth="1.6" /></svg>}
    {variant === 'bars' && <div style={{ display: 'flex', alignItems: 'end', justifyContent: 'space-around', gap: 8, height: Math.max(90, height - 190), padding: '5px 18px 0' }}>{bars.map(item => <div key={item.category} style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'end' }}><div style={{ height: 'calc(100% - 25px)', display: 'flex', alignItems: 'end', justifyContent: 'center', gap: 2 }}><span style={{ width: 22, height: `${Math.max(2, item.current / maxBar * 100)}%`, background: '#0070A3' }} /><span style={{ width: 22, height: `${Math.max(2, item.previous / maxBar * 100)}%`, background: '#8C8C8C' }} /></div><span style={{ height: 25, color: '#777', fontSize: 9, textAlign: 'center' }}>{item.category}</span></div>)}</div>}
    {(variant === 'area' || variant === 'osa') && showTasks && <Tasks critical={critical} risk={risk} labels={taskLabels} />}
    {(variant === 'area' || variant === 'osa') && (analysisUrl ? <a href={analysisUrl} target="_top" rel="noreferrer" style={styles.action}>Ir para análise ›</a> : <span style={styles.action}>Ir para análise ›</span>)}
  </div>;
}
