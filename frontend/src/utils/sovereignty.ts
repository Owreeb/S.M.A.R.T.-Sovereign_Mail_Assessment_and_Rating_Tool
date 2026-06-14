const scoreColor = (index: number): string => {
  if (index >= 9) return '#1c7ed6' // Blau
  if (index >= 8) return '#2f9e44' // Grün
  if (index >= 6) return '#74b816' // Hellgrün
  if (index >= 4) return '#f2cc0c' // Gelb
  if (index >= 2) return '#f76707' // Orange
  return '#e03131' // Rot
}

export { scoreColor }
