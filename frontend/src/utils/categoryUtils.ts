import type { TFunction } from 'i18next'

export const CATEGORY_KEYS = ['hospital', 'university', 'city', 'courthouse'] as const
type CategoryKey = (typeof CATEGORY_KEYS)[number]

const isKnownCategory = (value: string): value is CategoryKey => (CATEGORY_KEYS as readonly string[]).includes(value)

// Translate a known category tag, falling back to the raw value for unknown ones.
export const categoryLabel = (t: TFunction<'map'>, category: string): string =>
  isKnownCategory(category) ? t(`categories.${category}`) : category

// The only countries offered in the country filter (raw org.country data
// values), in display order: Germany, Switzerland, Austria.
export const COUNTRY_FILTER_VALUES = ['Deutschland', 'Schweiz', 'Österreich'] as const

const COUNTRY_LABEL_KEY: Record<string, 'countries.de' | 'countries.ch' | 'countries.at'> = {
  Deutschland: 'countries.de',
  Schweiz: 'countries.ch',
  Österreich: 'countries.at',
}

// Translate a country filter value, falling back to the raw value.
export const countryFilterLabel = (t: TFunction<'map'>, value: string): string => {
  const key = COUNTRY_LABEL_KEY[value]
  return key ? t(key) : value
}
