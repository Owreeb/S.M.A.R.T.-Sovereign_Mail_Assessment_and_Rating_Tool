export const getDiffOrZero = (current: number, previous?: number) => {
  if (!previous) {
    return 0
  }

  return current - previous
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const selectByDiff = (diff: number | undefined, positive: any, negative: any, neutral?: any) => {
  if (!diff) {
    return undefined
  }
  if (diff === 0 && neutral) {
    return neutral
  }
  return diff > 0 ? positive : negative
}
