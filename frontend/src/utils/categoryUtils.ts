import type { ParseKeys, TFunction } from 'i18next'

export const CATEGORY_KEYS = ['hospital', 'university', 'city', 'courthouse', 'newspaper', 'political party'] as const
type CategoryKey = (typeof CATEGORY_KEYS)[number]

const isKnownCategory = (value: string): value is CategoryKey => (CATEGORY_KEYS as readonly string[]).includes(value)

export const categoryLabel = (t: TFunction<'map'>, category: string): string =>
  isKnownCategory(category) ? t(`categories.${category}`) : category

export const COUNTRY_FILTER_VALUES = ['Deutschland', 'Schweiz', 'Österreich'] as const

const COUNTRY_LABEL_KEY: Record<string, 'countries.de' | 'countries.ch' | 'countries.at'> = {
  Deutschland: 'countries.de',
  Schweiz: 'countries.ch',
  Österreich: 'countries.at',
}

export const countryFilterLabel = (t: TFunction<'map'>, value: string): string => {
  const key = COUNTRY_LABEL_KEY[value]
  return key ? t(key) : value
}

export const vendorClassLabel = (t: TFunction<'mail'>, key: string): string => t(key as ParseKeys<'mail'>) as string
