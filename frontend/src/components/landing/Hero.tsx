import React from 'react'

import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import heroBanner from '@assets/hero-banner.png'

import styles from './Hero.module.scss'

const Hero = (): React.ReactElement => {
  const { t } = useTranslation('hero')

  return (
    <section className={styles.hero} style={{ backgroundImage: `url(${heroBanner})` }}>
      <div className={styles.overlay} />
      <div className={styles.content}>
        <h1 className={styles.title}>
          {t('titleLine1')}
          <br />
          {t('titleLine2')}
          <br />
          {t('titleLine3')}
        </h1>
        <p className={styles.subtitle}>{t('subtitle')}</p>
        <Link className={styles.cta} to="/dashboard">
          {t('cta')}
        </Link>
        <a className={styles.scrollLink} href="#hintergrund">
          {t('scrollLink')}
        </a>
      </div>
    </section>
  )
}

export default Hero
