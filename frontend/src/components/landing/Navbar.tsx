import React from 'react'

import { useTranslation } from 'react-i18next'
import { Link, useLocation } from 'react-router-dom'

import LanguageSwitch from '@components/common/LanguageSwitch'

import styles from './Navbar.module.scss'

const Navbar = (): React.ReactElement => {
  const { t } = useTranslation('navbar')
  const { pathname } = useLocation()
  const onDashboard = pathname.startsWith('/dashboard')

  return (
    <header className={styles.navbar}>
      <a className={styles.invisibleLink} href="/">
        <div className={styles.brand}>
          <span className={styles.logo}>
            s.m.a.r<span className={styles.logoAccent}>.t.</span>
          </span>
          <span className={styles.tagline}>
            {t('tagline')}
            <br />
            DACH
          </span>
        </div>
      </a>
      <nav className={styles.links}>
        {onDashboard ? (
          <Link className={styles.link} to="/">
            {t('home')}
          </Link>
        ) : (
          <Link className={styles.link} to="/dashboard">
            {t('domainStatistics')}
          </Link>
        )}
        <LanguageSwitch />
      </nav>
    </header>
  )
}

export default Navbar
