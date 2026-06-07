import i18n from '../i18n/i18n'

const getCurrentLocale = (): 'de' | 'en' => {
  const lang = i18n.language
  if (lang === 'en' || lang === 'de') {
    return lang
  }
  return 'de'
}

const changeInterfaceLanguage = async (language: string): Promise<void> => {
  localStorage.setItem('smart_lang', language)
  await i18n.changeLanguage(language)
}

export { getCurrentLocale, changeInterfaceLanguage }
