import type { TFunction } from 'i18next'
import { describe, expect, test } from 'vitest'

import { categoryLabel, countryFilterLabel, vendorClassLabel } from '@utils/categoryUtils.ts'

const t = ((key: string) => key) as unknown as TFunction<'map'> & TFunction<'mail'>

describe('categoryLabel', () => {
  test('known category is translated', () => {
    expect(categoryLabel(t, 'hospital')).toStrictEqual('categories.hospital')
  })

  test('unknown category is returned as is', () => {
    expect(categoryLabel(t, 'foo')).toStrictEqual('foo')
  })
})

describe('countryFilterLabel', () => {
  test('known country maps to its key', () => {
    expect(countryFilterLabel(t, 'Deutschland')).toStrictEqual('countries.de')
  })

  test('unknown value is returned as is', () => {
    expect(countryFilterLabel(t, 'Frankreich')).toStrictEqual('Frankreich')
  })
})

describe('vendorClassLabel', () => {
  test('passes the key through the translator', () => {
    expect(vendorClassLabel(t, 'catPublic')).toStrictEqual('catPublic')
  })
})
