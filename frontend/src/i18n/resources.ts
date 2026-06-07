import deCommon from './locales/de/common'
import deFeatures from './locales/de/features'
import deFooter from './locales/de/footer'
import deHero from './locales/de/hero'
import deMap from './locales/de/map'
import deNavbar from './locales/de/navbar'
import deSovereignty from './locales/de/sovereignty'
import deStatistics from './locales/de/statistics'
import enCommon from './locales/en/common'
import enFeatures from './locales/en/features'
import enFooter from './locales/en/footer'
import enHero from './locales/en/hero'
import enMap from './locales/en/map'
import enNavbar from './locales/en/navbar'
import enSovereignty from './locales/en/sovereignty'
import enStatistics from './locales/en/statistics'

const langEn = {
  common: enCommon,
  navbar: enNavbar,
  hero: enHero,
  sovereignty: enSovereignty,
  features: enFeatures,
  footer: enFooter,
  statistics: enStatistics,
  map: enMap,
} as const

const langDe: typeof langEn = {
  common: deCommon,
  navbar: deNavbar,
  hero: deHero,
  sovereignty: deSovereignty,
  features: deFeatures,
  footer: deFooter,
  statistics: deStatistics,
  map: deMap,
}

export const resources = {
  en: langEn,
  de: langDe,
}
