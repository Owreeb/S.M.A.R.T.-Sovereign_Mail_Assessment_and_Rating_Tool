import React from 'react'

import { useTranslation } from 'react-i18next'

import type { StatisticsData } from '@models/statisticsData.ts'
import { getDiffOrZero } from '@utils/statisticsUtils.ts'

import StatCard from './StatCard'
import styles from './StatisticsGrid.module.scss'

type Props = {
  currentData: StatisticsData
  previousData?: StatisticsData
}

const StatisticsGrid = ({ currentData, previousData }: Props): React.ReactElement => {
  const { t } = useTranslation('statistics')

  const gridData = [
    {
      title: t('orgsScannedTitle'),
      value: currentData.overview.orgsScanned,
      diff: getDiffOrZero(currentData.overview.orgsScanned, previousData?.overview.orgsScanned),
      diffLabel: t('diffSinceLastScan'),
    },
    {
      title: t('sovereigntyIndexTitle'),
      value: currentData.overview.sovereigntyIndex,
      diff: getDiffOrZero(currentData.overview.sovereigntyIndex, previousData?.overview.sovereigntyIndex),
      diffLabel: t('diffSinceLastScan'),
      isReversed: true,
    },
    {
      title: t('domainsScannedTitle'),
      value: currentData.overview.domainsScanned,
      diff: getDiffOrZero(currentData.overview.domainsScanned, previousData?.overview.domainsScanned),
      diffLabel: t('diffSinceLastScan'),
    },
  ]

  return (
    <div className={styles.wrapper}>
      <div className={styles.gridDataContainer}>
        {gridData.map((stat) => (
          <StatCard
            key={stat.title}
            title={stat.title}
            value={stat.value}
            diff={stat.diff}
            diffLabel={stat.diffLabel}
            isReversed={stat.isReversed ?? false}
          />
        ))}
      </div>
    </div>
  )
}

export default StatisticsGrid
