import { createI18n } from 'vue-i18n'

export const i18n = createI18n({
  legacy: false,
  locale: 'zh',
  messages: {
    zh: { app: { name: 'RSSReader' } },
    en: { app: { name: 'RSSReader' } }
  }
})

