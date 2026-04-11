import { createI18n } from 'vue-i18n'
import en from './en.json'
import zhCN from './zh-CN.json'

export type MessageSchema = typeof en

const SUPPORTED_LOCALES = ['en', 'zh-CN'] as const
export type SupportedLocale = typeof SUPPORTED_LOCALES[number]

function detectLocale(): SupportedLocale {
  const stored = localStorage.getItem('locale')
  if (stored && SUPPORTED_LOCALES.includes(stored as SupportedLocale)) {
    return stored as SupportedLocale
  }
  const browserLang = navigator.language
  if (browserLang.startsWith('zh')) return 'zh-CN'
  return 'en'
}

const i18n = createI18n<[MessageSchema], SupportedLocale>({
  locale: detectLocale(),
  fallbackLocale: 'en',
  messages: { en, 'zh-CN': zhCN },
})

export function setLocale(locale: SupportedLocale): void {
  ;(i18n.global.locale as any).value = locale
  localStorage.setItem('locale', locale)
  document.documentElement.setAttribute('lang', locale)
}

export function currentLocale(): SupportedLocale {
  return (i18n.global.locale as any).value as SupportedLocale
}

export function toggleLocale(): void {
  setLocale(currentLocale() === 'en' ? 'zh-CN' : 'en')
}

export default i18n
