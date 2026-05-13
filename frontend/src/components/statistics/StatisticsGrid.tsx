import React from 'react'

import type { StatisticsData } from '@models/statisticsData.ts'
import { getDiffOrZero } from '@utils/statisticsUtils.ts'

import StatCard from './StatCard'
import styles from './StatisticsGrid.module.scss'

type Props = {
  currentData: StatisticsData
  previousData?: StatisticsData
}

const StatisticsGrid = ({ currentData, previousData }: Props): React.ReactElement => {
  const gridData = [
    {
      title: 'ORGANISATIONEN GESCANNT',
      value: currentData.overview.orgsScanned,
      diff: getDiffOrZero(currentData.overview.orgsScanned, previousData?.overview.orgsScanned),
      diffLabel: 'diese Woche',
    },
    {
      title: 'Ø SOUVERÄNITÄTSINDEX',
      value: currentData.overview.sovereigntyIndex,
      diff: getDiffOrZero(currentData.overview.sovereigntyIndex, previousData?.overview.sovereigntyIndex),
      diffLabel: 'Vormonat',
    },
    {
      title: 'SOUVERÄNE SYSTEME',
      value: `${currentData.overview.sovereignSystems * 100}%`,
      diff: getDiffOrZero(currentData.overview.sovereignSystems, previousData?.overview.sovereignSystems) * 100,
      diffLabel: 'seit Q1',
    },
    {
      title: 'HYPERSCALER-ANTEIL',
      value: `${currentData.overview.hyperscalerRatio * 100}%`,
      diff: getDiffOrZero(currentData.overview.hyperscalerRatio, previousData?.overview.hyperscalerRatio) * 100,
      diffLabel: 'seit Q1',
    },
    {
      title: 'DOMAINS ANALYSIERT',
      value: currentData.overview.domainsScanned,
      diff: getDiffOrZero(currentData.overview.domainsScanned, previousData?.overview.domainsScanned),
      diffLabel: 'diese Woche',
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
