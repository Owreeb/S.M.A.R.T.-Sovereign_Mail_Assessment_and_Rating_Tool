import React from 'react'

import { Group, Paper, SimpleGrid, Text } from '@mantine/core'
import type { StatisticsData } from '@models/statisticsData.ts'
import {
  IconArrowDownRight,
  IconArrowRight,
  IconArrowUpRight,
  IconBriefcase2,
  IconCircleDottedLetterI,
  IconMailCog,
  IconPlugConnected,
  IconReportAnalytics,
} from '@tabler/icons-react'
import { getDiffOrZero, selectByDiff } from '@utils/statisticsUtils.ts'

import styles from './StatisticsGrid.module.scss'

type Props = {
  currentData: StatisticsData
  previousData?: StatisticsData
}

const StatisticsGrid = ({ currentData, previousData }: Props): React.ReactElement => {
  const gridData = [
    {
      title: 'ORGANISATIONEN GESCANNT',
      icon: IconBriefcase2,
      value: currentData.overview.orgsScanned,
      diff: getDiffOrZero(currentData.overview.orgsScanned, previousData?.overview.orgsScanned),
    },
    {
      title: 'Ø SOUVERÄNITÄTSINDEX',
      icon: IconCircleDottedLetterI,
      value: currentData.overview.sovereigntyIndex,
      diff: getDiffOrZero(currentData.overview.sovereigntyIndex, previousData?.overview.sovereigntyIndex),
    },
    {
      title: 'SOUVERÄNE SYSTEME',
      icon: IconMailCog,
      value: currentData.overview.sovereignSystems,
      diff: getDiffOrZero(currentData.overview.sovereignSystems, previousData?.overview.sovereignSystems),
    },
    {
      title: 'HYPERSCALER-ANTEIL',
      icon: IconPlugConnected,
      value: currentData.overview.hyperscalerRatio,
      diff: getDiffOrZero(currentData.overview.hyperscalerRatio, previousData?.overview.hyperscalerRatio),
    },
    {
      title: 'DOMAINS ANALYSIERT',
      icon: IconReportAnalytics,
      value: currentData.overview.domainsScanned,
      diff: getDiffOrZero(currentData.overview.domainsScanned, previousData?.overview.domainsScanned),
    },
  ]

  const stats = gridData.map((stat) => {
    const DiffIcon = selectByDiff(stat.diff, IconArrowUpRight, IconArrowDownRight, IconArrowRight)

    return (
      <Paper withBorder p="md" radius="md" key={stat.title}>
        <Group justify="space-between">
          <Text size="xs" c="dimmed" className={styles.title}>
            {stat.title}
          </Text>
          <stat.icon className={styles.icon} size={22} stroke={1.5} />
        </Group>

        <Group align="flex-end" gap="xs" mt={25}>
          <Text c={selectByDiff(stat.diff, 'teal', 'red')} className={styles.value}>
            {stat.value}
          </Text>
          {DiffIcon && (
            <Text c={stat.diff! > 0 ? 'teal' : 'red'} fz="sm" fw={500} className={styles.diff}>
              <span>{Math.round(stat.diff * 100) / 100}%</span>
              <DiffIcon size={16} stroke={1.5} />
            </Text>
          )}
        </Group>
      </Paper>
    )
  })

  return (
    <div className={styles.root}>
      <SimpleGrid cols={{ base: 1, xs: 3, md: 5 }}>{stats}</SimpleGrid>
    </div>
  )
}

export default StatisticsGrid
