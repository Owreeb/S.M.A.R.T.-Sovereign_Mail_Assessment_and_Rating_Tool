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
      diffLabel: t('diffThisWeek'),
    },
    {
      title: t('sovereigntyIndexTitle'),
      value: currentData.overview.sovereigntyIndex,
      diff: getDiffOrZero(currentData.overview.sovereigntyIndex, previousData?.overview.sovereigntyIndex),
      diffLabel: t('diffLastMonth'),
    },
    {
      title: t('sovereignSystemsTitle'),
      value: `${currentData.overview.sovereignSystems * 100}%`,
      diff: getDiffOrZero(currentData.overview.sovereignSystems, previousData?.overview.sovereignSystems) * 100,
      diffLabel: t('diffSinceQ1'),
    },
    {
      title: t('hyperscalerRatioTitle'),
      value: `${currentData.overview.hyperscalerRatio * 100}%`,
      diff: getDiffOrZero(currentData.overview.hyperscalerRatio, previousData?.overview.hyperscalerRatio) * 100,
      diffLabel: t('diffSinceQ1'),
    },
    {
      title: t('domainsScannedTitle'),
      value: currentData.overview.domainsScanned,
      diff: getDiffOrZero(currentData.overview.domainsScanned, previousData?.overview.domainsScanned),
      diffLabel: t('diffThisWeek'),
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
          />
        ))}
      </div>
    </div>
  )
}

export default StatisticsGrid
