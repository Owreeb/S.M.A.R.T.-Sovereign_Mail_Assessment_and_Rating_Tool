import { describe, expect, test } from 'vitest'

import { EU_EEA_CH, countryTier, tierColor, worstTier } from '@utils/countryUtils.ts'

describe('countryTier', () => {
  test('DE is de', () => {
    expect(countryTier('DE')).toStrictEqual('de')
  })

  test('EU member is eu', () => {
    expect(countryTier('FR')).toStrictEqual('eu')
  })

  test('US is us', () => {
    expect(countryTier('US')).toStrictEqual('us')
  })

  test('unknown is other', () => {
    expect(countryTier('XX')).toStrictEqual('other')
  })
})

describe('worstTier', () => {
  test('only DE stays de', () => {
    expect(worstTier(['DE'])).toStrictEqual('de')
  })

  test('DE and EU becomes eu', () => {
    expect(worstTier(['DE', 'FR'])).toStrictEqual('eu')
  })

  test('US wins over everything', () => {
    expect(worstTier(['DE', 'FR', 'US'])).toStrictEqual('us')
  })

  test('other wins over eu', () => {
    expect(worstTier(['FR', 'XX'])).toStrictEqual('other')
  })
})

describe('tierColor', () => {
  test('returns the de color', () => {
    expect(tierColor('de')).toStrictEqual('#2f9e44')
  })

  test('returns the us color', () => {
    expect(tierColor('us')).toStrictEqual('#e03131')
  })
})

describe('EU_EEA_CH', () => {
  test('contains AT', () => {
    expect(EU_EEA_CH.has('AT')).toStrictEqual(true)
  })

  test('does not contain US', () => {
    expect(EU_EEA_CH.has('US')).toStrictEqual(false)
  })
})
