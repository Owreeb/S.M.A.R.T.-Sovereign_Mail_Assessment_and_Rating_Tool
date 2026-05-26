import React from 'react'

import { IconChartBar, IconMapPin, IconShieldCheck } from '@tabler/icons-react'

import styles from './FeaturesSection.module.scss'

type Feature = {
  icon: React.ReactNode
  title: string
  description: string
}

const features: Feature[] = [
  {
    icon: <IconShieldCheck size={32} stroke={1.5} color="#f0792e" />,
    title: 'Souveränitätsindex',
    description: 'Jede Domain erhält einen Score von 0–10 basierend auf Provider und Serverstandort.',
  },
  {
    icon: <IconMapPin size={32} stroke={1.5} color="#f0792e" />,
    title: 'DACH-Abdeckung',
    description: 'Wir erfassen Behörden, Universitäten und Unternehmen in Deutschland, Österreich und der Schweiz.',
  },
  {
    icon: <IconChartBar size={32} stroke={1.5} color="#f0792e" />,
    title: 'Transparente Statistiken',
    description: 'Aktuelle Verteilung zwischen souveränen Anbietern, teilweise-souveränen und Hyperscaler-Nutzern.',
  },
]

const FeaturesSection = (): React.ReactElement => {
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
