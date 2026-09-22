export default function formatValue(value, type) {
  if (value === null || value === undefined) return '—';
  const options = type === 'decimal'
    ? { minimumFractionDigits: 2, maximumFractionDigits: 2 }
    : type === 'currency'
      ? { style: 'currency', currency: 'BRL', notation: 'compact', maximumFractionDigits: 2 }
      : type === 'percent'
        ? { style: 'percent', maximumFractionDigits: 2 }
        : { notation: 'compact', maximumFractionDigits: 2 };
  return new Intl.NumberFormat('pt-BR', options).format(type === 'percent' ? value / 100 : value);
}
