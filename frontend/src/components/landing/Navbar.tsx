import React from 'react'

import { Link, useLocation } from 'react-router-dom'

import styles from './Navbar.module.scss'

const Navbar = (): React.ReactElement => {
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
            E-MAIL SOUVERÄNITÄT
            <br />
            DACH
          </span>
        </div>
      </a>
      <nav className={styles.links}>
        {onDashboard ? (
          <Link className={styles.link} to="/">
            HOME
          </Link>
        ) : (
          <Link className={styles.link} to="/dashboard">
            DOMAIN-STATISTIK
          </Link>
        )}
      </nav>
    </header>
  )
}

export default Navbar
