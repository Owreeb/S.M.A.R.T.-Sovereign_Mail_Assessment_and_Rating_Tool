import React from 'react'

import { useTranslation } from 'react-i18next'
import { NavLink } from 'react-router-dom'

import LanguageSwitch from '@components/common/LanguageSwitch'

import styles from './Navbar.module.scss'

const linkClass = ({ isActive }: { isActive: boolean }): string =>
  isActive ? `${styles.link} ${styles.linkActive}` : styles.link

const Navbar = (): React.ReactElement => {
  const { t } = useTranslation('navbar')

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
        <NavLink className={linkClass} to="/" end>
          {t('home')}
        </NavLink>
        <NavLink className={linkClass} to="/dashboard">
          {t('domainStatistics')}
        </NavLink>
        <NavLink className={linkClass} to="/score-info">
          {t('scoreInfo')}
        </NavLink>
        <LanguageSwitch />
      </nav>
    </header>
  )
}

export default Navbar
