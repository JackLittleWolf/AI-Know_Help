import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import MainLayout from '@/components/layout/MainLayout.vue'
import OcrPage from '@/views/OcrPage.vue'
import PromptPage from '@/views/PromptPage.vue'
import SettingsPage from '@/views/SettingsPage.vue'
import ChatPage from '@/views/ChatPage.vue'
import AgentsPage from '@/views/AgentsPage.vue'
import KnowledgeBasePage from '@/views/KnowledgeBasePage.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: MainLayout,
    redirect: '/ocr',
    children: [
      { path: 'ocr', name: 'OCR', component: OcrPage },
      { path: 'prompt', name: 'Prompt', component: PromptPage },
      { path: 'chat', name: 'Chat', component: ChatPage },
      { path: 'agents', name: 'Agents', component: AgentsPage },
      { path: 'knowledge', name: 'Knowledge', component: KnowledgeBasePage },
      { path: 'settings', name: 'Settings', component: SettingsPage },
    ],
  },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
