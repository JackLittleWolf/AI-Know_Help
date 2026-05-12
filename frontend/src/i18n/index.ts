import { createI18n } from 'vue-i18n'
import zh from './zh'
import en from './en'
import ja from './ja'

export type Locale = 'zh' | 'en' | 'ja'

const saved = (localStorage.getItem('locale') as Locale) || 'zh'

export const i18n = createI18n({
  legacy: false,
  locale: saved,
  fallbackLocale: 'zh',
  messages: { zh, en, ja },
})
