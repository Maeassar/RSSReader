import { createI18n } from 'vue-i18n'

export const i18n = createI18n({
  legacy: false,
  locale: 'zh',
  messages: {
    zh: { app: { name: 'Ripple' } },
    en: { app: { name: 'Ripple' } }
  }
})

