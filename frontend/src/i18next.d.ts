import { defaultNS } from './i18n/i18n'
import { resources } from './i18n/resources'

declare module 'i18next' {
  interface CustomTypeOptions {
    returnObjects: true
    defaultNS: typeof defaultNS
    resources: typeof resources.en
  }
}
