import React from 'react'

import { useTranslation } from 'react-i18next'

import type { StatisticsData } from '@models/statisticsData.ts'

import styles from './OverviewSection.module.scss'
import StatisticsGrid from './StatisticsGrid.tsx'
import TopShares from './TopShares.tsx'

type Props = {
  currentData: StatisticsData
  previousData?: StatisticsData
}

const OverviewSection = ({ currentData, previousData }: Props): React.ReactElement => {
  const { t } = useTranslation('statistics')

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>{t('overviewTitle')}</h2>
      <StatisticsGrid currentData={currentData} previousData={previousData} />
      <TopShares vendors={currentData.topMailVendors} hosters={currentData.topHosters} />
    </section>
  )
}

export default OverviewSection
