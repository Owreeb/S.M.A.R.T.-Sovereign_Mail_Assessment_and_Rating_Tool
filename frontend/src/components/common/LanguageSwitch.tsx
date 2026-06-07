import React from 'react'

import { useTranslation } from 'react-i18next'

import { changeInterfaceLanguage } from '@utils/translationUtils'

import styles from './LanguageSwitch.module.scss'

const LANGUAGES = ['de', 'en'] as const

const LanguageSwitch = (): React.ReactElement => {
  const { t, i18n } = useTranslation('common')
  const current = i18n.language === 'en' ? 'en' : 'de'

  return (
    <div className={styles.switch} role="group" aria-label={t('languageSwitchLabel')}>
      {LANGUAGES.map((lang) => (
        <button
          key={lang}
          type="button"
          className={`${styles.option} ${current === lang ? styles.active : ''}`}
          onClick={() => changeInterfaceLanguage(lang)}
          aria-pressed={current === lang}
        >
          {lang === 'de' ? t('germanShort') : t('englishShort')}
        </button>
      ))}
    </div>
  )
}

export default LanguageSwitch
