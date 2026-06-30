import React from 'react'

import { useTranslation } from 'react-i18next'

import type { Organization } from '@models/organization'
import type { Share } from '@models/statisticsData.ts'

import styles from './TopShares.module.scss'
import VendorClassChart from './VendorClassChart.tsx'

type Props = {
  orgs: Organization[]
  hosters: Share[]
}

const ShareList = ({ title, items }: { title: string; items: Share[] }): React.ReactElement => {
  const maxShare = Math.max(...items.map((item) => item.share), 0.0001)

  return (
    <div className={styles.list}>
      <p className={styles.title}>{title}</p>
      <div className={styles.rows}>
        {items.map((item) => (
          <div key={item.name} className={styles.row}>
            <span className={styles.name} title={item.name}>
              {item.name}
            </span>
            <div className={styles.track}>
              <div className={styles.bar} style={{ width: `${Math.max((item.share / maxShare) * 100, 2)}%` }} />
            </div>
            <span className={styles.share}>{Math.round(item.share * 100)}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}

const TopShares = ({ orgs, hosters }: Props): React.ReactElement => {
  const { t } = useTranslation('statistics')

  return (
    <div className={styles.grid}>
      <VendorClassChart orgs={orgs} />
      <ShareList title={t('topHostersTitle')} items={hosters} />
    </div>
  )
}

export default TopShares
