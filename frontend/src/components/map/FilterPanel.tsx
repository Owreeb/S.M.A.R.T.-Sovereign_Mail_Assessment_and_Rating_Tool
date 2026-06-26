import React, { useState } from 'react'

import type { TFunction } from 'i18next'
import { useTranslation } from 'react-i18next'

import { FILTER_FIELDS, type FilterField, type FilterKey, type FilterState } from '@constants/filterFields'
import type { Organization } from '@models/organization'
import { IconChevronDown, IconX } from '@tabler/icons-react'
import { COUNTRY_FILTER_VALUES, categoryLabel, countryFilterLabel } from '@utils/categoryUtils'

import styles from './FilterPanel.module.scss'

type Props = {
  orgs: Organization[]
  selected: FilterState
  open: boolean
  onToggle: (key: FilterKey, value: string) => void
  onReset: () => void
  onClose: () => void
}

const optionsFor = (orgs: Organization[], field: FilterField): string[] => {
  // The country filter is limited to DE/CH/AT regardless of stray data values.
  if (field.key === 'country') return [...COUNTRY_FILTER_VALUES]

  const values = new Set<string>()
  orgs.forEach((org) => {
    const value = org[field.key]
    if (Array.isArray(value)) value.forEach((v) => values.add(v))
    else if (value != null) values.add(value)
  })
  return [...values].sort((a, b) => a.localeCompare(b))
}

const optionLabel = (field: FilterField, value: string, t: TFunction<'map'>): string => {
  if (field.key === 'category') return categoryLabel(t, value)
  if (field.key === 'country') return countryFilterLabel(t, value)
  return value
}

const FilterPanel = ({ orgs, selected, open, onToggle, onReset, onClose }: Props): React.ReactElement => {
  const { t } = useTranslation('map')
  const [openSection, setOpenSection] = useState<string | null>(null)

  const toggleOpen = (key: string): void => setOpenSection((prev) => (prev === key ? null : key))

  const activeCount = FILTER_FIELDS.reduce((sum, field) => sum + selected[field.key].length, 0)

  return (
    <div className={`${styles.panel} ${open ? styles.panelOpen : ''}`}>
      <div className={styles.header}>
        <span className={styles.headerTitle}>{t('filter')}</span>
        <div className={styles.headerRight}>
          {activeCount > 0 && <span className={styles.activeCount}>{t('filterActive', { count: activeCount })}</span>}
          <button type="button" className={styles.close} onClick={onClose} aria-label={t('filterClose')}>
            <IconX size={16} />
          </button>
        </div>
      </div>

      <div className={styles.sections}>
        {FILTER_FIELDS.map((field) => {
          const isOpen = openSection === field.key
          const count = selected[field.key].length
          return (
            <div key={field.key} className={styles.section}>
              <button
                type="button"
                className={`${styles.sectionHeader} ${isOpen ? styles.sectionHeaderActive : ''}`}
                onClick={() => toggleOpen(field.key)}
              >
                <span className={styles.sectionLabel}>
                  {t(field.labelKey)}
                  {count > 0 && <span className={styles.badge}>{count}</span>}
                </span>
                <IconChevronDown className={`${styles.chevron} ${isOpen ? styles.chevronOpen : ''}`} size={16} />
              </button>
              {isOpen && (
                <div className={styles.options}>
                  {optionsFor(orgs, field).map((value) => (
                    <label key={value} className={styles.option}>
                      <input
                        type="checkbox"
                        checked={selected[field.key].includes(value)}
                        onChange={() => onToggle(field.key, value)}
                      />
                      <span>{optionLabel(field, value, t)}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div className={styles.footer}>
        <button
          type="button"
          className={`${styles.reset} ${activeCount > 0 ? styles.resetActive : ''}`}
          onClick={onReset}
        >
          {t('filterReset')}
        </button>
      </div>
    </div>
  )
}

export default FilterPanel
