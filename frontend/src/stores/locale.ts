import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { i18n, type Locale } from '@/i18n'
import zhCN from 'ant-design-vue/es/locale/zh_CN'
import enUS from 'ant-design-vue/es/locale/en_US'
import jaJP from 'ant-design-vue/es/locale/ja_JP'

const ANT_LOCALES = { zh: zhCN, en: enUS, ja: jaJP }

const LABELS: Record<Locale, string> = { zh: '中文', en: 'English', ja: '日本語' }

export const useLocaleStore = defineStore('locale', () => {
  const locale = ref<Locale>((localStorage.getItem('locale') as Locale) || 'zh')

  const antLocale = computed(() => ANT_LOCALES[locale.value])
  const label = computed(() => LABELS[locale.value])

  function setLocale(l: Locale) {
    locale.value = l
    i18n.global.locale.value = l
    localStorage.setItem('locale', l)
  }

  return { locale, antLocale, label, setLocale }
})
