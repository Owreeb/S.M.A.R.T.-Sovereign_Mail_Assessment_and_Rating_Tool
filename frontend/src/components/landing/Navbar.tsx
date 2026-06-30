import React from 'react'

import { useTranslation } from 'react-i18next'
import { Link, NavLink } from 'react-router-dom'

import LanguageSwitch from '@components/common/LanguageSwitch'

import styles from './Navbar.module.scss'

const linkClass = ({ isActive }: { isActive: boolean }): string =>
  isActive ? `${styles.link} ${styles.linkActive}` : styles.link

const Navbar = (): React.ReactElement => {
  const { t } = useTranslation('navbar')

  return (
    <header className={styles.navbar}>
      <Link className={styles.invisibleLink} to="/">
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
      </Link>
      <nav className={styles.links}>
        <NavLink className={linkClass} to="/" end>
          {t('home')}
        </NavLink>
        <NavLink className={linkClass} to="/dashboard">
          {t('domainStatistics')}
        </NavLink>
        <NavLink className={linkClass} to="/about">
          {t('about')}
        </NavLink>
        <LanguageSwitch />
      </nav>
    </header>
  )
}

export default Navbar
