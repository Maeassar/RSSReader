import { createRouter, createWebHistory } from 'vue-router'

import AISettingsView from '../views/AISettingsView.vue'
import FeedManageView from '../views/FeedManageView.vue'
import ReaderView from '../views/ReaderView.vue'
import SettingsView from '../views/SettingsView.vue'
import StatsView from '../views/StatsView.vue'
import TagsView from '../views/TagsView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: ReaderView },
    { path: '/feeds', component: FeedManageView },
    { path: '/tags', component: TagsView },
    { path: '/ai', component: AISettingsView },
    { path: '/stats', component: StatsView },
    { path: '/settings', component: SettingsView }
  ]
})

