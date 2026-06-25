import type { TFunction } from 'i18next'

export const CATEGORY_KEYS = ['hospital', 'university', 'city', 'courthouse'] as const
type CategoryKey = (typeof CATEGORY_KEYS)[number]

const isKnownCategory = (value: string): value is CategoryKey => (CATEGORY_KEYS as readonly string[]).includes(value)

// Translate a known category tag, falling back to the raw value for unknown ones.
export const categoryLabel = (t: TFunction<'map'>, category: string): string =>
  isKnownCategory(category) ? t(`categories.${category}`) : category
