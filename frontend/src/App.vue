<template>
  <a-config-provider :locale="localeStore.antLocale">
    <router-view />
  </a-config-provider>
</template>

<script setup lang="ts">
import { useLocaleStore } from '@/stores/locale'
const localeStore = useLocaleStore()
</script>
