import React from 'react'

import styles from './Footer.module.scss'

const Footer = (): React.ReactElement => {
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.top}>
          <div className={styles.brandColumn}>
            <span className={styles.logo}>
              s.m.a.r<span className={styles.logoAccent}>.t.</span>
            </span>
            <span className={styles.tagline}>E-Mail-Souveränität im DACH-Raum</span>
          </div>
          <div className={styles.contactColumn}>
            <div className={styles.contactHeading}>Kontakt</div>
            <a className={styles.contactLine} href="mailto:hapa1037@h-ka.de">
              hapa1037@h-ka.de
            </a>
            <div className={styles.contactLine}>MORPH Labs</div>
            <div className={styles.contactLine}>Moltkestraße 30, 76133 Karlsruhe</div>
          </div>
        </div>
        <div className={styles.divider} />
        <div className={styles.bottom}>
          <span className={styles.copy}>© 2026 MORPH lab</span>
          <nav className={styles.legalLinks}>
            <a className={styles.legalLink} href="#impressum">
              Impressum
            </a>
            <a className={styles.legalLink} href="#datenschutz">
              Datenschutz
            </a>
            <a className={styles.legalLink} href="#agb">
              AGB
            </a>
          </nav>
        </div>
      </div>
    </footer>
  )
}

export default Footer
