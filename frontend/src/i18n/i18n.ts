import i18n, { init, t, use } from 'i18next'
import { initReactI18next } from 'react-i18next'

import { resources } from './resources'

// eslint-disable-next-line react-hooks/rules-of-hooks
use(initReactI18next)

export const defaultNS = 'common'

init({
  lng: localStorage.getItem('smart_lang') || 'de',
  fallbackLng: 'de',
  debug: false,
  resources,
  defaultNS,
  keySeparator: '.',
  interpolation: { escapeValue: false },
  initImmediate: false,
})

export { t }
export default i18n
