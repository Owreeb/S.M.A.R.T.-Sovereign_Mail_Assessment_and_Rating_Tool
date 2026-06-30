import { describe, expect, test } from 'vitest'

import type { MailSystem, MailSystemRole, MailSystems, Organization } from '@models/organization'
import {
  UNKNOWN_CATEGORY,
  hostingCountries,
  hostingResidency,
  roleGroups,
  scoreHistogram,
  sovereigntyBySector,
  vendorCategoryMeta,
  vendorClassDistribution,
  worstVendorCategory,
} from '@utils/mailInsights.ts'

const mailSystem = (overrides: Partial<MailSystem> = {}): MailSystem => ({
  software: null,
  vendor: null,
  vendor_country: null,
  vendor_country_rating: null,
  vendor_category: null,
  vendor_category_rating: null,
  open_source_rating: null,
  countries: [],
  hosters: [],
  proxy: null,
  ...overrides,
})

const emptySystems = (): MailSystems => ({ smtp_in: [], imap_pop3: [], smtp_out: [], webmailer: [] })

const org = (overrides: Partial<Organization> = {}): Organization => ({
  org: 'Org',
  domain: null,
  email_domain: null,
  category: 'hospital',
  wikidata_url: null,
  city: null,
  state: null,
  country: null,
  lat: null,
  long: null,
  last_checked: null,
  sovereignty_index: null,
  providers: [],
  hosters: [],
  mail_systems: emptySystems(),
  ...overrides,
})

const withSystems = (
  role: MailSystemRole,
  systems: MailSystem[],
  overrides: Partial<Organization> = {},
): Organization => org({ mail_systems: { ...emptySystems(), [role]: systems }, ...overrides })

describe('vendorCategoryMeta', () => {
  test('known category', () => {
    expect(vendorCategoryMeta('US Hyperscaler')).toStrictEqual({ key: 'catHyperscaler', color: '#e03131' })
  })

  test('null is unknown', () => {
    expect(vendorCategoryMeta(null)).toStrictEqual(UNKNOWN_CATEGORY)
  })

  test('unrecognised is unknown', () => {
    expect(vendorCategoryMeta('foo')).toStrictEqual(UNKNOWN_CATEGORY)
  })
})

describe('worstVendorCategory', () => {
  test('picks the highest ranked category', () => {
    const o = org({
      mail_systems: {
        ...emptySystems(),
        smtp_in: [mailSystem({ vendor_category: 'EU Software Vendor' })],
        smtp_out: [mailSystem({ vendor_category: 'US Hyperscaler' })],
      },
    })
    expect(worstVendorCategory(o)).toStrictEqual('US Hyperscaler')
  })

  test('null when no categories', () => {
    expect(worstVendorCategory(org())).toBeNull()
  })
})

describe('hostingCountries', () => {
  test('collects sorted unique codes including proxy', () => {
    const o = withSystems('smtp_in', [
      mailSystem({ countries: ['FR', 'DE'], proxy: mailSystem({ countries: ['US', 'DE'] }) }),
    ])
    expect(hostingCountries(o)).toStrictEqual(['DE', 'FR', 'US'])
  })
})

describe('roleGroups', () => {
  test('returns only non-empty roles', () => {
    const o = withSystems('smtp_in', [mailSystem()])
    const groups = roleGroups(o)
    expect(groups).toHaveLength(1)
    expect(groups[0].role).toStrictEqual('smtp_in')
  })
})

describe('scoreHistogram', () => {
  test('counts per index and fills the rest with zero', () => {
    const result = scoreHistogram([
      org({ sovereignty_index: 1 }),
      org({ sovereignty_index: 1 }),
      org({ sovereignty_index: 3 }),
      org({ sovereignty_index: null }),
    ])
    expect(result).toHaveLength(6)
    expect(result[0]).toStrictEqual({ index: 1, count: 2 })
    expect(result[2]).toStrictEqual({ index: 3, count: 1 })
    expect(result[5]).toStrictEqual({ index: 6, count: 0 })
  })
})

describe('sovereigntyBySector', () => {
  test('averages per category sorted ascending', () => {
    const result = sovereigntyBySector([
      org({ category: 'a', sovereignty_index: 2 }),
      org({ category: 'a', sovereignty_index: 4 }),
      org({ category: 'b', sovereignty_index: 1 }),
    ])
    expect(result).toStrictEqual([
      { category: 'b', count: 1, average: 1 },
      { category: 'a', count: 2, average: 3 },
    ])
  })
})

describe('hostingResidency', () => {
  test('counts and shares per tier', () => {
    const result = hostingResidency([
      withSystems('smtp_in', [mailSystem({ countries: ['DE'] })], { sovereignty_index: 1 }),
      withSystems('smtp_in', [mailSystem({ countries: ['US'] })], { sovereignty_index: 5 }),
      org({ sovereignty_index: null }),
    ])
    const de = result.find((r) => r.tier === 'de')!
    const us = result.find((r) => r.tier === 'us')!
    expect(de).toStrictEqual({ tier: 'de', count: 1, share: 0.5 })
    expect(us).toStrictEqual({ tier: 'us', count: 1, share: 0.5 })
  })
})

describe('vendorClassDistribution', () => {
  test('counts and shares per vendor class', () => {
    const result = vendorClassDistribution([
      withSystems('smtp_in', [mailSystem({ vendor_category: 'US Hyperscaler' })]),
      org(),
    ])
    const hyperscaler = result.find((r) => r.key === 'catHyperscaler')!
    const unknown = result.find((r) => r.key === 'catUnknown')!
    expect(hyperscaler).toStrictEqual({ key: 'catHyperscaler', color: '#e03131', count: 1, share: 0.5 })
    expect(unknown).toStrictEqual({ key: 'catUnknown', color: '#adb5bd', count: 1, share: 0.5 })
  })
})
