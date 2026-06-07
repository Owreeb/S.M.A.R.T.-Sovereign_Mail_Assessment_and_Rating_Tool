import React from 'react'

import { useTranslation } from 'react-i18next'

import { IconScale, IconShieldLock, IconWorld } from '@tabler/icons-react'

import styles from './SovereigntySection.module.scss'

type Highlight = {
  icon: React.ReactNode
  title: string
  description: string
}

const SovereigntySection = (): React.ReactElement => {
  const { t } = useTranslation('sovereignty')

  const highlights: Highlight[] = [
    {
      icon: <IconWorld size={24} stroke={1.5} color="#1f4ea1" />,
      title: t('highlights.euLocationTitle'),
      description: t('highlights.euLocationDescription'),
    },
    {
      icon: <IconShieldLock size={24} stroke={1.5} color="#7a6645" />,
      title: t('highlights.point2Title'),
      description: t('highlights.point2Description'),
    },
    {
      icon: <IconScale size={24} stroke={1.5} color="#5a5a5a" />,
      title: t('highlights.point3Title'),
      description: t('highlights.point3Description'),
    },
  ]

  return (
    <section id="hintergrund" className={styles.section}>
      <div className={styles.inner}>
        <div className={styles.copy}>
          <div className={styles.eyebrow}>{t('eyebrow')}</div>
          <h2 className={styles.heading}>
            {t('headingLine1')}
            <br />
            {t('headingLine2')}
          </h2>
          <p className={styles.paragraph}>
            <strong>{t('paragraph1Strong')}</strong> {t('paragraph1')}
          </p>
          <p className={styles.paragraph}>{t('paragraph2')}</p>
          <p className={styles.paragraph}>{t('paragraph3')}</p>
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
