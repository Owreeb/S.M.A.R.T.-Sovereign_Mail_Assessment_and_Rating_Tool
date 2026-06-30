import type { SovereigntyLevel } from '@models/organization.ts'

const LEVEL_BY_INDEX: Record<number, SovereigntyLevel> = {
  1: 'sehr-hoch',
  2: 'hoch',
  3: 'mittel',
  4: 'niedrig',
  5: 'sehr-niedrig',
  6: 'sehr-niedrig',
}

const COLOR_BY_INDEX: Record<number, string> = {
  1: '#2f9e44', // Grün
  2: '#74b816', // Hellgrün
  3: '#f2cc0c', // Gelb
  4: '#f76707', // Orange
  5: '#e03131', // Rot
  6: '#c92a2a', // Dunkelrot
}

const UNKNOWN_COLOR = '#adb5bd' // Grau

export const sovereigntyLevel = (index: number | null): SovereigntyLevel =>
  index == null ? 'unbekannt' : (LEVEL_BY_INDEX[index] ?? 'unbekannt')

export const sovereigntyColor = (index: number | null): string =>
  index == null ? UNKNOWN_COLOR : (COLOR_BY_INDEX[index] ?? UNKNOWN_COLOR)

export const SOVEREIGNTY_LEGEND: { index: number; color: string; level: SovereigntyLevel }[] = [1, 2, 3, 4, 5, 6].map(
  (index) => ({ index, color: COLOR_BY_INDEX[index], level: LEVEL_BY_INDEX[index] }),
)

export const UNKNOWN_LEGEND = { color: UNKNOWN_COLOR, level: 'unbekannt' as SovereigntyLevel }
