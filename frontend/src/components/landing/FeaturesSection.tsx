import React from 'react'

import { useTranslation } from 'react-i18next'

import { IconChartBar, IconMapPin, IconShieldCheck } from '@tabler/icons-react'

import styles from './FeaturesSection.module.scss'

type Feature = {
  icon: React.ReactNode
  title: string
  description: string
}

const FeaturesSection = (): React.ReactElement => {
  const { t } = useTranslation('features')

  const features: Feature[] = [
    {
      icon: <IconShieldCheck size={32} stroke={1.5} color="#f0792e" />,
      title: t('sovereigntyIndexTitle'),
      description: t('sovereigntyIndexDescription'),
    },
    {
      icon: <IconMapPin size={32} stroke={1.5} color="#f0792e" />,
      title: t('dachCoverageTitle'),
      description: t('dachCoverageDescription'),
    },
    {
      icon: <IconChartBar size={32} stroke={1.5} color="#f0792e" />,
      title: t('transparentStatsTitle'),
      description: t('transparentStatsDescription'),
    },
  ]

  return (
    <section className={styles.section}>
      <div className={styles.grid}>
        {features.map((feature) => (
          <div key={feature.title} className={styles.card}>
            <div className={styles.icon}>{feature.icon}</div>
            <div className={styles.title}>{feature.title}</div>
            <div className={styles.description}>{feature.description}</div>
          </div>
        ))}
      </div>
    </section>
  )
}

export default FeaturesSection
