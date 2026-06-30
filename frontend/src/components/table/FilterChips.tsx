import React from 'react'

import { useTranslation } from 'react-i18next'

import { FILTER_FIELDS, type FilterKey, type FilterState } from '@constants/filterFields'
import { IconX } from '@tabler/icons-react'
import { categoryLabel, countryFilterLabel, vendorClassLabel } from '@utils/categoryUtils'

import styles from './FilterChips.module.scss'

type Props = {
  selected: FilterState
  activeCount: number
  onRemove: (key: FilterKey, value: string) => void
  onReset: () => void
}

const FilterChips = ({ selected, activeCount, onRemove, onReset }: Props): React.ReactElement | null => {
  const { t } = useTranslation(['table', 'map'])
  const { t: tMap } = useTranslation('map')
  const { t: tMail } = useTranslation('mail')

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
            <span>
              {field.key === 'category'
                ? categoryLabel(tMap, value)
                : field.key === 'country'
                  ? countryFilterLabel(tMap, value)
                  : field.key === 'vendorClass'
                    ? vendorClassLabel(tMail, value)
                    : value}
            </span>
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
