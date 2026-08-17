import React from 'react'

import { useTranslation } from 'react-i18next'

import styles from './Footer.module.scss'

const Footer = (): React.ReactElement => {
  const { t } = useTranslation('footer')

  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.top}>
          <div className={styles.brandColumn}>
            <span className={styles.logo}>
              s.m.a.r<span className={styles.logoAccent}>.t.</span>
            </span>
            <span className={styles.tagline}>{t('tagline')}</span>
          </div>
          <div className={styles.contactColumn}>
            <div className={styles.contactHeading}>{t('contactHeading')}</div>
            <div className={styles.contactLine}>{t('organization')}</div>
            <div className={styles.contactLine}>{t('address')}</div>
          </div>
        </div>
        <div className={styles.divider} />
        <div className={styles.bottom}>
          <span className={styles.copy}>{t('copyright')}</span>
        </div>
      </div>
    </footer>
  )
}

export default Footer
