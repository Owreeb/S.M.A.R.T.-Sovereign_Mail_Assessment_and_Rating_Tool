import React from 'react'

import { Link } from 'react-router-dom'

import heroBanner from '@assets/hero-banner.png'

import styles from './Hero.module.scss'

const Hero = (): React.ReactElement => {
  return (
    <section className={styles.hero} style={{ backgroundImage: `url(${heroBanner})` }}>
      <div className={styles.overlay} />
      <div className={styles.content}>
        <h1 className={styles.title}>
          E-Mail Souveränität
          <br />
          in Deutschland —
          <br />
          auf einen Blick.
        </h1>
        <p className={styles.subtitle}>
          Wir analysieren, welche Domains wirklich souverän betrieben werden — und wer noch auf Hyperscaler setzt.
        </p>
        <Link className={styles.cta} to="/dashboard">
          DOMAIN-STATISTIK ANSEHEN →
        </Link>
        <a className={styles.scrollLink} href="#hintergrund">
          Mehr erfahren ↓
        </a>
      </div>
    </section>
  )
}

export default Hero
