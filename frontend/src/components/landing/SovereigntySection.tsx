import React from 'react'

import { IconScale, IconShieldLock, IconWorld } from '@tabler/icons-react'

import styles from './SovereigntySection.module.scss'

type Highlight = {
  icon: React.ReactNode
  title: string
  description: string
}

const highlights: Highlight[] = [
  {
    icon: <IconWorld size={24} stroke={1.5} color="#1f4ea1" />,
    title: 'EU-Serverstandort',
    description: 'Server befinden sich innerhalb der EU',
  },
  {
    icon: <IconShieldLock size={24} stroke={1.5} color="#7a6645" />,
    title: 'Punkt #2',
    description: 'Text zu Punkt #2',
  },
  {
    icon: <IconScale size={24} stroke={1.5} color="#5a5a5a" />,
    title: 'Punkt #3',
    description: 'Text zu Punkt #3',
  },
]

const SovereigntySection = (): React.ReactElement => {
  return (
    <section id="hintergrund" className={styles.section}>
      <div className={styles.inner}>
        <div className={styles.copy}>
          <div className={styles.eyebrow}>HINTERGRUND</div>
          <h2 className={styles.heading}>
            Was ist digitale
            <br />
            Souveränität?
          </h2>
          <p className={styles.paragraph}>
            <strong>PRÜFEN:</strong> Digitale Souveränität beschreibt die Fähigkeit von Organisationen, ihre digitale
            Infrastruktur selbst zu kontrollieren — unabhängig von großen Tech-Konzernen wie Google, Microsoft oder
            Amazon.
          </p>
          <p className={styles.paragraph}>
            Im E-Mail-Bereich bedeutet das: Wer verarbeitet Ihre Nachrichten? Wo liegen die Server?
          </p>
          <p className={styles.paragraph}>
            Souveräne Systeme werden in Deutschland oder der EU betrieben, von Anbietern ohne Abhängigkeit von
            US-amerikanischen Cloud-Plattformen.
          </p>
        </div>
        <div className={styles.highlights}>
          {highlights.map((item) => (
            <div key={item.title} className={styles.highlightCard}>
              <div className={styles.highlightIcon}>{item.icon}</div>
              <div>
                <div className={styles.highlightTitle}>{item.title}</div>
                <div className={styles.highlightDescription}>{item.description}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default SovereigntySection
