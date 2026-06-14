import { useMemo, useState } from 'react'

import { FILTER_FIELDS, type FilterState } from '@constants/filterFields'
import type { Organization } from '@models/organization'

export type OrgFilters = {
  selected: FilterState
  filteredOrgs: Organization[]
  activeCount: number
  toggle: (key: string, value: string) => void
  reset: () => void
}

const emptyFilterState = (): FilterState => Object.fromEntries(FILTER_FIELDS.map((field) => [field.key, []]))

export const useOrgFilters = (orgs: Organization[]): OrgFilters => {
  const [selected, setSelected] = useState<FilterState>(emptyFilterState)

  const filteredOrgs = useMemo(
    () =>
      orgs.filter((org) =>
        FILTER_FIELDS.every((field) => {
          const chosen = selected[field.key]
          if (chosen.length === 0) return true
          const value = org[field.key]
          return Array.isArray(value) ? value.some((v) => chosen.includes(v)) : chosen.includes(value)
        }),
      ),
    [orgs, selected],
  )

  const activeCount = FILTER_FIELDS.reduce((sum, field) => sum + selected[field.key].length, 0)

  const toggle = (key: string, value: string): void =>
    setSelected((prev) => {
      const current = prev[key]
      const next = current.includes(value) ? current.filter((v) => v !== value) : [...current, value]
      return { ...prev, [key]: next }
    })

  const reset = (): void => setSelected(emptyFilterState())

  return { selected, filteredOrgs, activeCount, toggle, reset }
}
