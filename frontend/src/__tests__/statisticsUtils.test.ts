import { describe, expect, test } from 'vitest'

import { getDiffOrZero, selectByDiff } from '@utils/statisticsUtils.ts'

describe('Test getting diff between two values or undefined', () => {
  test('expect difference of 5', () => {
    expect(getDiffOrZero(10, 5)).toStrictEqual(5)
  })

  test('expect 0 return for undefined comparison', () => {
    expect(getDiffOrZero(10, undefined)).toStrictEqual(0)
  })
})

describe('Test returning value based on difference', () => {
  test('expect "positive" to be returned with diff 1', () => {
    expect(selectByDiff(1, 'positive', 'negative', 'neutral')).toStrictEqual('positive')
  })

  test('expect "positive" to be returned with diff -1', () => {
    expect(selectByDiff(-1, 'positive', 'negative', 'neutral')).toStrictEqual('negative')
  })

  test('expect "neutral" to be returned with diff 0', () => {
    expect(selectByDiff(0, 'positive', 'negative', 'neutral')).toStrictEqual('neutral')
  })
})
