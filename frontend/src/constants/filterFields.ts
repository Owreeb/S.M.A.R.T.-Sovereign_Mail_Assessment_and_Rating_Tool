import type { Organization } from '@models/organization'

export const FILTER_FIELDS = [
  { key: 'providers', labelKey: 'providerLabel', isArray: true },
  { key: 'category', labelKey: 'categoryLabel', isArray: false },
  { key: 'country', labelKey: 'countryLabel', isArray: false },
] as const satisfies readonly { key: keyof Organization; labelKey: string; isArray: boolean }[]

export type FilterField = (typeof FILTER_FIELDS)[number]
export type FilterKey = FilterField['key']
export type FilterState = Record<FilterKey, string[]>
