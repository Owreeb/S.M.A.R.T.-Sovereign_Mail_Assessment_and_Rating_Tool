import React from 'react'

import { useTranslation } from 'react-i18next'

import type { Share } from '@models/statisticsData.ts'

import styles from './TopShares.module.scss'

type Props = {
  vendors: Share[]
  hosters: Share[]
}

const ShareList = ({ title, items }: { title: string; items: Share[] }): React.ReactElement => (
  <div className={styles.list}>
    <p className={styles.title}>{title}</p>
    {items.map((item) => (
      <div key={item.name} className={styles.row}>
        <div className={styles.bar} style={{ width: `${item.share * 100}%` }} />
        <span className={styles.name}>{item.name}</span>
        <span className={styles.share}>{Math.round(item.share * 100)}%</span>
      </div>
    ))}
  </div>
)

const TopShares = ({ vendors, hosters }: Props): React.ReactElement => {
  const { t } = useTranslation('statistics')

  return (
    <div className={styles.grid}>
      <ShareList title={t('topMailVendorsTitle')} items={vendors} />
      <ShareList title={t('topHostersTitle')} items={hosters} />
    </div>
  )
}

export default TopShares
