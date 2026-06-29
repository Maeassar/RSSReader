import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './styles.css'

import App from './App.vue'
import { router } from './router'
import { i18n } from './i18n'
import { usePreferencesStore } from './stores/preferences'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia).use(router).use(i18n).use(ElementPlus)

usePreferencesStore(pinia).applyPreferences()

app.mount('#app')
