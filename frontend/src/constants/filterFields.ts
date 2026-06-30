import type { Organization } from '@models/organization'
import { vendorCategoryMeta, worstVendorCategory } from '@utils/mailInsights'

export type FilterField = {
  key: string
  labelKey: string
  accessor: (org: Organization) => string | string[] | null
}

export const FILTER_FIELDS = [
  { key: 'providers', labelKey: 'providerLabel', accessor: (org: Organization) => org.providers },
  {
    key: 'vendorClass',
    labelKey: 'vendorClassLabel',
    accessor: (org: Organization) => vendorCategoryMeta(worstVendorCategory(org)).key,
  },
  { key: 'category', labelKey: 'categoryLabel', accessor: (org: Organization) => org.category },
  { key: 'country', labelKey: 'countryLabel', accessor: (org: Organization) => org.country },
] as const satisfies readonly FilterField[]

export type FilterKey = (typeof FILTER_FIELDS)[number]['key']
export type FilterState = Record<FilterKey, string[]>
