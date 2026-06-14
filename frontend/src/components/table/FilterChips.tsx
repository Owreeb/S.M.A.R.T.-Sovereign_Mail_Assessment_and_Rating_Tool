import React from 'react'

import { useTranslation } from 'react-i18next'

import { FILTER_FIELDS, type FilterState } from '@constants/filterFields'
import { IconX } from '@tabler/icons-react'

import styles from './FilterChips.module.scss'

type Props = {
  selected: FilterState
  activeCount: number
  onRemove: (key: string, value: string) => void
  onReset: () => void
}

const capitalize = (value: string): string => value.charAt(0).toUpperCase() + value.slice(1)

const FilterChips = ({ selected, activeCount, onRemove, onReset }: Props): React.ReactElement | null => {
  const { t } = useTranslation(['table', 'map'])

  if (activeCount === 0) return null

  return (
    <div className={styles.chips}>
      <span className={styles.intro}>{t('filteredBy')}</span>
      {FILTER_FIELDS.flatMap((field) =>
        selected[field.key].map((value) => (
          <button
            key={`${field.key}-${value}`}
            type="button"
            className={styles.chip}
            onClick={() => onRemove(field.key, value)}
          >
            <span className={styles.chipLabel}>{t(`map:${field.labelKey}`)}:</span>
            <span>{field.key === 'category' ? capitalize(value) : value}</span>
            <IconX size={13} />
          </button>
        )),
      )}
      <button type="button" className={styles.clear} onClick={onReset}>
        {t('map:filterReset')}
      </button>
    </div>
  )
}

export default FilterChips
