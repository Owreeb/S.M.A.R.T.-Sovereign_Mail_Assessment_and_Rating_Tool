import { describe, expect, test } from 'vitest'

import { SOVEREIGNTY_LEGEND, UNKNOWN_LEGEND, sovereigntyColor, sovereigntyLevel } from '@utils/sovereignty.ts'

describe('sovereigntyLevel', () => {
  test('null is unbekannt', () => {
    expect(sovereigntyLevel(null)).toStrictEqual('unbekannt')
  })

  test('1 is sehr-hoch', () => {
    expect(sovereigntyLevel(1)).toStrictEqual('sehr-hoch')
  })

  test('6 is sehr-niedrig', () => {
    expect(sovereigntyLevel(6)).toStrictEqual('sehr-niedrig')
  })

  test('unknown index is unbekannt', () => {
    expect(sovereigntyLevel(99)).toStrictEqual('unbekannt')
  })
})

describe('sovereigntyColor', () => {
  test('null is the unknown color', () => {
    expect(sovereigntyColor(null)).toStrictEqual('#adb5bd')
  })

  test('1 is green', () => {
    expect(sovereigntyColor(1)).toStrictEqual('#2f9e44')
  })

  test('unknown index is the unknown color', () => {
    expect(sovereigntyColor(99)).toStrictEqual('#adb5bd')
  })
})

describe('SOVEREIGNTY_LEGEND', () => {
  test('has six entries', () => {
    expect(SOVEREIGNTY_LEGEND).toHaveLength(6)
  })

  test('first entry is index 1', () => {
    expect(SOVEREIGNTY_LEGEND[0]).toStrictEqual({ index: 1, color: '#2f9e44', level: 'sehr-hoch' })
  })

  test('unknown legend is unbekannt', () => {
    expect(UNKNOWN_LEGEND).toStrictEqual({ color: '#adb5bd', level: 'unbekannt' })
  })
})
