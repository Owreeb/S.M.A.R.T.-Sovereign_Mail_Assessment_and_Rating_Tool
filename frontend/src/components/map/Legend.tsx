import React from 'react'

import { useTranslation } from 'react-i18next'

import { SOVEREIGNTY_LEGEND } from '@utils/sovereignty'

import styles from './Legend.module.scss'

const entries = SOVEREIGNTY_LEGEND

const Legend = (): React.ReactElement => {
  const { t } = useTranslation('map')

  return (
    <div className={styles.legend}>
      <p className={styles.title}>{t('legendTitle')}</p>
      {entries.map((entry) => (
        <div key={entry.level + entry.color} className={styles.row}>
          <svg className={styles.pin} width="12" height="18" viewBox="0 0 24 36" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M12 0C5.37 0 0 5.37 0 12c0 8.25 12 24 12 24s12-15.75 12-24C24 5.37 18.63 0 12 0z"
              fill={entry.color}
              stroke="#ffffff"
              strokeWidth="1.5"
            />
            <circle cx="12" cy="12" r="4.5" fill="#ffffff" />
          </svg>
          <span>
            {entry.index} – {t(`levels.${entry.level}`)}
          </span>
        </div>
      ))}
    </div>
  )
}

export default Legend
