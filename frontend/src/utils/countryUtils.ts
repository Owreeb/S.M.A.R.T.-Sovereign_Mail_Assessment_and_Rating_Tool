export const EU_EEA_CH = new Set([
  'AT',
  'FR',
  'IT',
  'ES',
  'NL',
  'BE',
  'PL',
  'SE',
  'FI',
  'DK',
  'IE',
  'PT',
  'GR',
  'CZ',
  'SK',
  'HU',
  'RO',
  'BG',
  'HR',
  'SI',
  'LT',
  'LV',
  'EE',
  'LU',
  'MT',
  'CY',
  'NO',
  'IS',
  'LI',
  'CH',
])

export type CountryTier = 'de' | 'eu' | 'other' | 'us'

export const countryTier = (code: string): CountryTier => {
  if (code === 'DE') return 'de'
  if (EU_EEA_CH.has(code)) return 'eu'
  if (code === 'US') return 'us'
  return 'other'
}

const TIER_ORDER: Record<CountryTier, number> = { de: 0, eu: 1, other: 2, us: 3 }

export const worstTier = (codes: string[]): CountryTier => {
  let worst: CountryTier = 'de'
  for (const code of codes) {
    const tier = countryTier(code)
    if (TIER_ORDER[tier] > TIER_ORDER[worst]) worst = tier
  }
  return worst
}

const TIER_COLOR: Record<CountryTier, string> = {
  de: '#2f9e44',
  eu: '#74b816',
  other: '#f76707',
  us: '#e03131',
}

export const tierColor = (tier: CountryTier): string => TIER_COLOR[tier]
