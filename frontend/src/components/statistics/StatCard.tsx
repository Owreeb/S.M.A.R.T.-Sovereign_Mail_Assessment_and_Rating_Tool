import React from 'react'

import styles from './StatCard.module.scss'

type Props = {
  title: string
  value: React.ReactNode
  diff: number
  diffLabel?: string
}

const StatCard = ({ title, value, diff, diffLabel }: Props): React.ReactElement => {
  const isPositive = diff >= 0
  const diffclass = isPositive ? styles.positive : styles.negative
  const arrow = isPositive ? '↑' : '↓'
  const sign = isPositive ? '+' : ''

  return (
    <div className={styles.card}>
      <div className={styles.title}>{title}</div>
      <div className={`${styles.value} ${diffclass}`}>{value}</div>
      <div className={`${styles.diff} ${diffclass}`}>
        <span className={styles.arrow}>{arrow}</span>
        <span>
          {sign}
          {Math.round(diff * 100) / 100}
          {diffLabel ? ` ${diffLabel}` : ''}
        </span>
      </div>
    </div>
  )
}

export default StatCard
