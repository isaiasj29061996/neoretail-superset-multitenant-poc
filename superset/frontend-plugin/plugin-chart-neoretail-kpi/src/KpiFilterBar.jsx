import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useDispatch, useSelector } from 'react-redux';
import { updateDataMask } from 'src/dataMask/actions';

// These are the existing governed native filters. Updating their data masks
// (instead of maintaining a second independent chart state) keeps all three
// hierarchy charts, bookmarked filters and the standard Superset filter bar
// synchronized. The bootstrap scopes these filters to the three KPI charts.
export const KPI_FILTER_IDS = Object.freeze({
  year: 'NATIVE_FILTER-panorama-kpi-year',
  month: 'NATIVE_FILTER-panorama-kpi-month',
  kpi: 'NATIVE_FILTER-panorama-kpi-selector',
});

const MONTH_NAMES = [
  'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
  'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
];

const fallbackKpis = [
  'Venda R$', 'Estoque qtd', '%OSA', '%Ruptura', '%Item sem Venda',
  'Cobertura de estoque', 'Giro de estoque', '%ROI',
  'TVD - Pré-Ruptura', 'IVD - Excesso de estoque',
];

const button = {
  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
  gap: 12, width: '100%', minHeight: 31, padding: '5px 9px',
  border: '1px solid #ccd6df', borderRadius: 3, background: '#fff',
  fontSize: 12, color: '#333', cursor: 'pointer', textAlign: 'left',
};

const selected = (mask, column) => {
  const values = mask?.extraFormData?.filters?.find(
    filter => filter.col === column && filter.op === 'IN',
  )?.val ?? mask?.filterState?.value;
  if (values == null) return [];
  return (Array.isArray(values) ? values : [values]).filter(
    item => item != null && item !== '',
  );
};

const makeMask = (column, values, label) => ({
  extraFormData: values.length ? {
    filters: [{ col: column, op: 'IN', val: values }],
  } : {},
  filterState: {
    value: values.length ? values : undefined,
    label: values.length ? label : undefined,
  },
  ownState: {},
});

// Popovers are portaled to document.body: the KPI toolbar occupies one short
// dashboard row, whose Superset chart wrapper would otherwise clip both menus.
function Popup({ open, anchorRef, align = 'left', width = 240, children, onClose }) {
  const popupRef = useRef(null);
  const [style, setStyle] = useState(null);
  useEffect(() => {
    if (!open) return undefined;
    const position = () => {
      if (!anchorRef.current) return;
      const rect = anchorRef.current.getBoundingClientRect();
      const left = align === 'right' ? rect.right - width : rect.left;
      const clampedLeft = Math.max(8, Math.min(left, window.innerWidth - width - 8));
      const roomBelow = window.innerHeight - rect.bottom - 12;
      const maxHeight = Math.min(380, Math.max(160, roomBelow));
      setStyle({
        position: 'fixed',
        top: rect.bottom + 3,
        left: clampedLeft,
        width,
        maxHeight,
        overflowY: 'auto',
        zIndex: 11000,
        padding: '9px 9px 11px',
        borderRadius: 5,
        border: '1px solid #cbd6df',
        boxShadow: '0 7px 24px rgba(2,22,40,.18)',
        background: '#fff',
        color: '#333',
        fontFamily: 'Inter, Segoe UI, Arial, sans-serif',
        fontSize: 12,
      });
    };
    const outside = event => {
      if (!popupRef.current?.contains(event.target)
        && !anchorRef.current?.contains(event.target)) onClose();
    };
    position();
    document.addEventListener('pointerdown', outside);
    window.addEventListener('resize', position);
    window.addEventListener('scroll', position, true);
    return () => {
      document.removeEventListener('pointerdown', outside);
      window.removeEventListener('resize', position);
      window.removeEventListener('scroll', position, true);
    };
  }, [open, anchorRef, align, width, onClose]);
  if (!open || !style) return null;
  return createPortal(
    <div ref={popupRef} style={style} role="dialog" aria-label="Filtros dos KPIs">
      {children}
    </div>, document.body,
  );
}

const optionRow = {
  display: 'flex', alignItems: 'center', gap: 7, padding: '5px 4px',
  cursor: 'pointer', minHeight: 27,
};

export default function KpiFilterBar({ width, height, filterOptions = [] }) {
  const dispatch = useDispatch();
  const masks = useSelector(state => state.dataMask || {});
  const yearMask = masks[KPI_FILTER_IDS.year];
  const monthMask = masks[KPI_FILTER_IDS.month];
  const kpiMask = masks[KPI_FILTER_IDS.kpi];
  const yearAnchor = useRef(null);
  const kpiAnchor = useRef(null);
  const [openMenu, setOpenMenu] = useState(null);

  const years = useMemo(() => [...new Set(filterOptions.map(row => Number(row.year))
    .filter(Number.isFinite))].sort((a, b) => b - a), [filterOptions]);
  const yearValues = selected(yearMask, 'comparison_year');
  const activeYear = years.includes(Number(yearValues[0]))
    ? Number(yearValues[0]) : years[0];
  const months = useMemo(() => [...new Map(filterOptions
    .filter(row => Number(row.year) === activeYear)
    .map(row => [row.monthKey, { key: row.monthKey, number: row.month, name: MONTH_NAMES[row.month - 1] }]))
    .values()].sort((a, b) => a.number - b.number), [filterOptions, activeYear]);
  const allMonthKeys = months.map(month => month.key);
  const rawMonths = selected(monthMask, 'comparison_year_month');
  const chosenMonths = rawMonths.filter(key => allMonthKeys.includes(key));
  const allMonths = chosenMonths.length === 0 || chosenMonths.length === months.length;
  const kpis = useMemo(() => [...new Map(filterOptions
    .slice().sort((a, b) => a.kpiOrder - b.kpiOrder)
    .map(row => [row.kpi, row.kpi])).values()],
    [filterOptions]);
  const availableKpis = kpis.length ? kpis : fallbackKpis;
  const rawKpi = selected(kpiMask, 'comparison_kpi')[0];
  const currentKpi = availableKpis.includes(rawKpi) ? rawKpi : availableKpis[0];

  const write = useCallback((id, col, values, label) => {
    dispatch(updateDataMask(id, makeMask(col, values, label)));
  }, [dispatch]);

  const chooseYear = nextYear => {
    // Clear dependent month first so the old year's months cannot linger in
    // the query while the native year filter refreshes.
    write(KPI_FILTER_IDS.month, 'comparison_year_month', [], undefined);
    write(KPI_FILTER_IDS.year, 'comparison_year', [nextYear], String(nextYear));
  };
  const chooseMonth = (monthKey, checked) => {
    const current = allMonths ? allMonthKeys : chosenMonths;
    const next = checked
      ? [...new Set([...current, monthKey])]
      : current.filter(item => item !== monthKey);
    // No filter means all available months. If every month is selected,
    // restore the fast, annual preaggregated path.
    const values = next.length === months.length ? [] : next;
    write(
      KPI_FILTER_IDS.month, 'comparison_year_month', values,
      values.map(key => key.split(' · ')[1]).join(', '),
    );
  };

  if (!filterOptions.length) {
    return <div data-neoretail-variant="kpifilters"
      style={{ padding: 18, color: '#6c727a', background: '#fff' }}>
      Carregando opções de Ano, Mês e Visualização por…
    </div>;
  }

  return <div data-neoretail-variant="kpifilters" data-test="neoretail-kpi-filter-bar"
    style={{
      boxSizing: 'border-box', display: 'flex', alignItems: 'center',
      justifyContent: 'space-between', gap: 16, flexWrap: 'wrap',
      width, minHeight: Math.max(78, height || 78), padding: '12px 20px',
      background: '#fff', borderRadius: 7, border: '1px solid #e2e8ef',
      color: '#303740', fontFamily: 'Inter, Segoe UI, Arial, sans-serif',
    }}>
    <div style={{ display: 'flex', alignItems: 'end', gap: 22, flexWrap: 'wrap' }}>
      <div style={{ width: 185 }}>
        <label style={{ display: 'block', fontSize: 11, marginBottom: 4 }}>Ano / Mês</label>
        <button type="button" style={button} ref={yearAnchor}
          aria-haspopup="dialog" aria-expanded={openMenu === 'date'}
          onClick={() => setOpenMenu(openMenu === 'date' ? null : 'date')}>
          <span>{activeYear || 'Selecionar período'}{chosenMonths.length
            ? ` · ${chosenMonths.length} mês(es)` : ''}</span><span>⌄</span>
        </button>
      </div>
      <h3 style={{ fontSize: 17, fontWeight: 650, margin: '0 0 5px' }}>
        Comparativo de KPIs por dimensão
      </h3>
    </div>
    <div style={{ width: 230 }}>
      <label style={{ display: 'block', fontSize: 11, marginBottom: 4 }}>Visualização por</label>
      <button type="button" style={button} ref={kpiAnchor}
        aria-haspopup="dialog" aria-expanded={openMenu === 'kpi'}
        onClick={() => setOpenMenu(openMenu === 'kpi' ? null : 'kpi')}>
        <span>{currentKpi}</span><span>⌄</span>
      </button>
    </div>
    <Popup open={openMenu === 'date'} anchorRef={yearAnchor}
      onClose={() => setOpenMenu(null)} width={245}>
      <div style={{ fontWeight: 600, padding: '5px 4px 9px' }}>Selecionar ano e mês</div>
      {years.map(year => <div key={year} style={{ borderTop: '1px solid #f0f2f4' }}>
        <label style={{ ...optionRow, fontWeight: 550 }}>
          <input type="radio" name="neoretail-kpi-year"
            checked={year === activeYear} onChange={() => chooseYear(year)} />
          {year}
        </label>
        {year === activeYear && <div style={{ paddingLeft: 16, paddingBottom: 6 }}>
          <label style={{ ...optionRow, fontWeight: 550 }}>
            <input type="checkbox" checked={allMonths}
              onChange={event => write(
                KPI_FILTER_IDS.month, 'comparison_year_month',
                event.target.checked ? [] : allMonthKeys.slice(0, 1),
                event.target.checked ? undefined : (months[0]?.name || ''),
              )} />
            Todos os meses
          </label>
          {months.map(month => <label key={month.key} style={optionRow}>
            <input type="checkbox"
              checked={allMonths || chosenMonths.includes(month.key)}
              onChange={event => chooseMonth(month.key, event.target.checked)} />
            {month.name}
          </label>)}
        </div>}
      </div>)}
    </Popup>
    <Popup open={openMenu === 'kpi'} anchorRef={kpiAnchor}
      align="right" onClose={() => setOpenMenu(null)} width={255}>
      <div style={{ fontWeight: 600, padding: '5px 4px 9px' }}>Visualização por</div>
      {availableKpis.map(kpi => <label key={kpi} style={optionRow}>
        <input type="radio" name="neoretail-kpi-selector" checked={kpi === currentKpi}
          onChange={() => {
            write(KPI_FILTER_IDS.kpi, 'comparison_kpi', [kpi], kpi);
            setOpenMenu(null);
          }} />
        {kpi}
      </label>)}
    </Popup>
  </div>;
}
