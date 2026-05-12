<template>
  <a-layout class="main-layout">
    <!-- Sider -->
    <a-layout-sider
      v-model:collapsed="collapsed"
      :trigger="null"
      collapsible
      :width="220"
      :collapsed-width="64"
      class="sider"
      breakpoint="lg"
      @breakpoint="onBreakpoint"
    >
      <div class="logo">
        <img src="/logo.svg" alt="logo" class="logo-img" />
        <span v-if="!collapsed" class="logo-text">{{ t('nav.title') }}</span>
      </div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        theme="dark"
        mode="inline"
        @click="onMenuClick"
      >
        <a-menu-item key="/ocr">
          <template #icon><scan-outlined /></template>
          <span>{{ t('nav.ocr') }}</span>
        </a-menu-item>
        <a-menu-item key="/prompt">
          <template #icon><bulb-outlined /></template>
          <span>{{ t('nav.prompt') }}</span>
        </a-menu-item>
        <a-menu-item key="/chat">
          <template #icon><comment-outlined /></template>
          <span>{{ t('nav.chat') }}</span>
        </a-menu-item>
        <a-menu-item key="/agents">
          <template #icon><robot-outlined /></template>
          <span>{{ t('nav.agents') }}</span>
        </a-menu-item>
        <a-menu-item key="/settings">
          <template #icon><setting-outlined /></template>
          <span>{{ t('nav.settings') }}</span>
        </a-menu-item>
      </a-menu>
      <div class="sider-trigger" @click="collapsed = !collapsed">
        <menu-fold-outlined v-if="!collapsed" />
        <menu-unfold-outlined v-else />
      </div>
    </a-layout-sider>

    <!-- Content -->
    <a-layout>
      <a-layout-header class="header">
        <span class="page-title">{{ pageTitle }}</span>
        <div class="header-right">
          <a-dropdown>
            <a-button type="text" class="lang-btn">
              <template #icon><global-outlined /></template>
              {{ localeStore.label }}
            </a-button>
            <template #overlay>
              <a-menu @click="(e: any) => localeStore.setLocale(e.key as any)">
                <a-menu-item key="zh">中文</a-menu-item>
                <a-menu-item key="en">English</a-menu-item>
                <a-menu-item key="ja">日本語</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>
      <a-layout-content class="content">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  ScanOutlined,
  BulbOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  GlobalOutlined,
  CommentOutlined,
  RobotOutlined,
} from '@ant-design/icons-vue'
import { useLocaleStore } from '@/stores/locale'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const localeStore = useLocaleStore()
const collapsed = ref(false)

const selectedKeys = ref<string[]>([route.path])
watch(() => route.path, (path) => { selectedKeys.value = [path] })

const pageTitle = computed(() => {
  const map: Record<string, string> = {
    '/ocr': t('header.ocr'),
    '/prompt': t('header.prompt'),
    '/chat': t('header.chat'),
    '/settings': t('header.settings'),
  }
  return map[route.path] ?? t('nav.title')
})

function onMenuClick({ key }: { key: string }) { router.push(key) }
function onBreakpoint(broken: boolean) { collapsed.value = broken }
</script>

<style scoped>
.main-layout { min-height: 100vh; }

.sider {
  position: fixed;
  left: 0; top: 0; bottom: 0;
  z-index: 100;
  overflow: auto;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.06);
  white-space: nowrap;
  overflow: hidden;
  padding: 0 12px;
}

.logo-img { width: 32px; height: 32px; flex-shrink: 0; }

.sider-trigger {
  position: absolute;
  bottom: 0;
  width: 100%;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.65);
  cursor: pointer;
  background: rgba(0, 0, 0, 0.2);
  transition: color 0.3s;
}
.sider-trigger:hover { color: #fff; }

.header {
  background: #fff;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  position: sticky;
  top: 0;
  z-index: 99;
}

.page-title { font-size: 18px; font-weight: 600; color: #1a1a1a; }

.header-right { display: flex; align-items: center; gap: 8px; }

.lang-btn { color: #595959; font-size: 13px; }

.content { margin: 24px; min-height: calc(100vh - 112px); }

:deep(.ant-layout) { margin-left: 220px; transition: margin-left 0.2s; }
:deep(.ant-layout-sider-collapsed) ~ .ant-layout { margin-left: 64px; }
</style>
