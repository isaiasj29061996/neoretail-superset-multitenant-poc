// Cyclic PBIP dimension contexts are not destructive parent/child cascades.
// The default path is the original Superset behavior, including other pages.
export function selectorDependencyIds(filter) {
  if (filter?.controlValues?.pbipSelectorContext !== true) {
    return filter?.cascadeParentIds;
  }
  const ids = filter.controlValues.pbipContextParentIds;
  if (!Array.isArray(ids)) return [];
  return [...new Set(ids)].filter(id => typeof id === 'string' && id !== filter.id);
}

export function selectorOptionLabel(value, formatted, formData) {
  if (formData?.pbipSelectorContext !== true) return formatted;
  const label = formData.pbipOptionLabels?.[String(value)];
  return typeof label === 'string' ? label : formatted;
}

export function selectorFilterValues(values, formData) {
  if (formData?.pbipSelectorContext !== true || !formData.pbipOptionValueCodes || values == null) return values;
  const expanded = values.flatMap(value => formData.pbipOptionValueCodes[String(value)] ?? [value]);
  return [...new Set(expanded)];
}
