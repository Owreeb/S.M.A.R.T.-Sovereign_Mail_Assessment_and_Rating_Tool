import React from 'react'

import { useTranslation } from 'react-i18next'

import type { Organization } from '@models/organization'
import type { StatisticsData } from '@models/statisticsData.ts'

import styles from './OverviewSection.module.scss'
import StatisticsGrid from './StatisticsGrid.tsx'
import TopShares from './TopShares.tsx'

type Props = {
  currentData: StatisticsData
  previousData?: StatisticsData
  orgs: Organization[]
}

const OverviewSection = ({ currentData, previousData, orgs }: Props): React.ReactElement => {
  const { t } = useTranslation('statistics')

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>{t('overviewTitle')}</h2>
      <StatisticsGrid currentData={currentData} previousData={previousData} />
      <TopShares orgs={orgs} hosters={currentData.topHosters} />
    </section>
  )
}

export default OverviewSection
