import React from 'react'

import styles from './Legend.module.scss'

const entries: { color: string; label: string }[] = [
  { color: '#1c7ed6', label: '9 - 10' },
  { color: '#2f9e44', label: '8' },
  { color: '#74b816', label: '6 - 7' },
  { color: '#f2cc0c', label: '4 - 5' },
  { color: '#f76707', label: '2 - 3' },
  { color: '#e03131', label: '0 - 1' },
]

const Legend = (): React.ReactElement => {
  return (
    <div className={styles.legend}>
      <p className={styles.title}>Souveränität</p>
      {entries.map((entry) => (
        <div key={entry.label} className={styles.row}>
          <svg className={styles.pin} width="12" height="18" viewBox="0 0 24 36" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M12 0C5.37 0 0 5.37 0 12c0 8.25 12 24 12 24s12-15.75 12-24C24 5.37 18.63 0 12 0z"
              fill={entry.color}
              stroke="#ffffff"
              strokeWidth="1.5"
            />
            <circle cx="12" cy="12" r="4.5" fill="#ffffff" />
          </svg>
          <span>{entry.label}</span>
        </div>
      ))}
    </div>
  )
}

export default Legend
