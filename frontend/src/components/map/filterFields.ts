export const FILTER_FIELDS = [
  { key: 'provider', label: 'Provider', isArray: true },
  { key: 'category', label: 'Kategorie', isArray: false },
] as const

export type FilterField = (typeof FILTER_FIELDS)[number]
export type FilterState = Record<string, string[]>
