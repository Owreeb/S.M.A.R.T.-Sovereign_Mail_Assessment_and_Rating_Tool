import type { MailSystem, MailSystemRole, Organization } from '@models/organization'

import { worstTier } from './countryUtils'

export const ROLE_ORDER: MailSystemRole[] = ['smtp_in', 'imap_pop3', 'smtp_out', 'webmailer']

export const VENDOR_CATEGORY_META: Record<string, { key: string; color: string }> = {
  'Community / Public Sector / Gemeinwohl': { key: 'catPublic', color: '#2f9e44' },
  'EU Software Vendor': { key: 'catEuVendor', color: '#74b816' },
  'EU Subsidiary of Foreign Vendor': { key: 'catEuSub', color: '#f2cc0c' },
  'International Vendor': { key: 'catIntl', color: '#f76707' },
  'US Hyperscaler': { key: 'catHyperscaler', color: '#e03131' },
}

export const UNKNOWN_CATEGORY = { key: 'catUnknown', color: '#adb5bd' }

export const vendorCategoryMeta = (category: string | null): { key: string; color: string } =>
  (category && VENDOR_CATEGORY_META[category]) || UNKNOWN_CATEGORY

export const VENDOR_CLASS_KEYS = [
  ...Object.values(VENDOR_CATEGORY_META).map((m) => m.key),
  UNKNOWN_CATEGORY.key,
] as const

const systemsOf = (org: Organization): MailSystem[] => Object.values(org.mail_systems).flat()

export const hasMailSystems = (org: Organization): boolean => systemsOf(org).length > 0

const CATEGORY_RANK: Record<string, number> = {
  'Community / Public Sector / Gemeinwohl': 1,
  'EU Software Vendor': 2,
  'EU Subsidiary of Foreign Vendor': 3,
  'International Vendor': 4,
  'US Hyperscaler': 5,
}

export const worstVendorCategory = (org: Organization): string | null => {
  let worst: string | null = null
  let rank = 0
  for (const system of systemsOf(org)) {
    if (!system.vendor_category) continue
    const r = CATEGORY_RANK[system.vendor_category] ?? 0
    if (r > rank) {
      rank = r
      worst = system.vendor_category
    }
  }
  return worst
}

export const hostingCountries = (org: Organization): string[] => {
  const codes = new Set<string>()
  for (const system of systemsOf(org)) {
    system.countries.forEach((c) => codes.add(c))
    system.proxy?.countries.forEach((c) => codes.add(c))
  }
  return [...codes].sort()
}

export type RoleGroup = { role: MailSystemRole; systems: MailSystem[] }

export const roleGroups = (org: Organization): RoleGroup[] =>
  ROLE_ORDER.map((role) => ({ role, systems: org.mail_systems[role] ?? [] })).filter(
    (group) => group.systems.length > 0,
  )

export type ScoreBucket = { index: number; count: number }

export const scoreHistogram = (orgs: Organization[]): ScoreBucket[] => {
  const counts = new Map<number, number>()
  for (const org of orgs) {
    if (org.sovereignty_index == null) continue
    counts.set(org.sovereignty_index, (counts.get(org.sovereignty_index) ?? 0) + 1)
  }
  return [1, 2, 3, 4, 5, 6].map((index) => ({ index, count: counts.get(index) ?? 0 }))
}

export type SectorStat = { category: string; count: number; average: number }

export const sovereigntyBySector = (orgs: Organization[]): SectorStat[] => {
  const groups = new Map<string, number[]>()
  for (const org of orgs) {
    if (org.sovereignty_index == null) continue
    const list = groups.get(org.category) ?? []
    list.push(org.sovereignty_index)
    groups.set(org.category, list)
  }
  return [...groups.entries()]
    .map(([category, values]) => ({
      category,
      count: values.length,
      average: values.reduce((sum, v) => sum + v, 0) / values.length,
    }))
    .sort((a, b) => a.average - b.average)
}

export type ResidencyStat = { tier: 'de' | 'eu' | 'other' | 'us'; count: number; share: number }

export const hostingResidency = (orgs: Organization[]): ResidencyStat[] => {
  const counts: Record<ResidencyStat['tier'], number> = { de: 0, eu: 0, other: 0, us: 0 }
  let total = 0
  for (const org of orgs) {
    const countries = hostingCountries(org)
    if (countries.length === 0) continue
    counts[worstTier(countries)] += 1
    total += 1
  }
  return (['de', 'eu', 'other', 'us'] as const).map((tier) => ({
    tier,
    count: counts[tier],
    share: total ? counts[tier] / total : 0,
  }))
}

export type VendorClassStat = { key: string; color: string; count: number; share: number }

const colorForKey = (key: string): string =>
  Object.values(VENDOR_CATEGORY_META).find((m) => m.key === key)?.color ?? UNKNOWN_CATEGORY.color

export const vendorClassDistribution = (orgs: Organization[]): VendorClassStat[] => {
  const counts = new Map<string, number>()
  for (const org of orgs) {
    const key = vendorCategoryMeta(worstVendorCategory(org)).key
    counts.set(key, (counts.get(key) ?? 0) + 1)
  }
  const total = orgs.length
  return VENDOR_CLASS_KEYS.map((key) => ({
    key,
    color: colorForKey(key),
    count: counts.get(key) ?? 0,
    share: total ? (counts.get(key) ?? 0) / total : 0,
  }))
}
