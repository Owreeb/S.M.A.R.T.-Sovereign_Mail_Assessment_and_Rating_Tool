export const FILTER_FIELDS = [
  { key: 'provider', labelKey: 'providerLabel', isArray: true },
  { key: 'category', labelKey: 'categoryLabel', isArray: false },
] as const

export type FilterField = (typeof FILTER_FIELDS)[number]
export type FilterState = Record<string, string[]>
