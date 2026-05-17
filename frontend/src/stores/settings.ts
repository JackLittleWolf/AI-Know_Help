import { defineStore } from 'pinia'
import { ref } from 'vue'
import http from '@/utils/http'
import type { AppSettings, AppSettingsResponse, LLMSettings, OCRSettings, StorageSettings } from '@/types'

const DEFAULT_LLM: LLMSettings = {
  provider: 'anthropic',
  api_key: '',
  base_url: '',
  model: 'claude-sonnet-4-6',
  max_tokens: 1024,
  temperature: 0.7,
  enable_thinking: false,
  thinking_budget_tokens: 10000,
}

const DEFAULT_OCR: OCRSettings = {
  provider: 'local',
  local_engine: 'rapidocr',
  dpi: 150,
  lang: 'ch',
  external_url: '',
  external_api_key: '',
  external_timeout: 30,
}

const DEFAULT_STORAGE: StorageSettings = {
  upload_dir: '/tmp/ocr_uploads',
}

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<AppSettings>({
    llm: { ...DEFAULT_LLM },
    ocr: { ...DEFAULT_OCR },
    storage: { ...DEFAULT_STORAGE },
    mcp: { servers: [] },
  })
  const loaded = ref(false)

  async function fetch() {
    const res = await http.get<unknown, AppSettingsResponse>('/settings')
    if (res.code === 200 && res.data) {
      settings.value = res.data
      loaded.value = true
    }
  }

  async function save(data: AppSettings): Promise<void> {
    const res = await http.put<unknown, AppSettingsResponse>('/settings', data)
    if (res.code === 200 && res.data) {
      settings.value = res.data
    }
  }

  return { settings, loaded, fetch, save }
})
