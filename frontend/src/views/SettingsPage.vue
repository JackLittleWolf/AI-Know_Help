<template>
  <div class="settings-page">
    <a-card :bordered="false" class="settings-card">
      <a-tabs tab-position="left" class="settings-tabs">

        <!-- LLM tab -->
        <a-tab-pane key="llm">
          <template #tab>
            <span><robot-outlined /> {{ t('settings.llm.tab') }}</span>
          </template>
          <div class="tab-content">
            <div class="tab-title">{{ t('settings.llm.title') }}</div>
            <div class="tab-body">
              <a-form :model="llm" layout="vertical">
                <a-form-item :label="t('settings.llm.provider')" name="provider">
                  <a-radio-group v-model:value="llm.provider" button-style="solid" @change="onLLMProviderChange">
                    <a-radio-button value="anthropic">Anthropic (Claude)</a-radio-button>
                    <a-radio-button value="openai">OpenAI</a-radio-button>
                    <a-radio-button value="custom">Custom</a-radio-button>
                  </a-radio-group>
                </a-form-item>

                <a-form-item v-if="llm.provider !== 'anthropic'" :label="t('settings.llm.baseUrl')" name="base_url">
                  <a-input v-model:value="llm.base_url" placeholder="https://api.openai.com/v1" allow-clear />
                  <div class="field-hint">{{ t('settings.llm.baseUrlHint') }}</div>
                </a-form-item>

                <a-form-item :label="t('settings.llm.apiKey')" name="api_key">
                  <a-input-password v-model:value="llm.api_key" :placeholder="llmKeyPlaceholder" allow-clear autocomplete="off" />
                  <div class="field-hint">{{ t('settings.llm.apiKeyHint') }}</div>
                </a-form-item>

                <a-form-item :label="t('settings.llm.model')" name="model">
                  <a-auto-complete v-model:value="llm.model" :options="llmModelOptions" :placeholder="t('settings.llm.model')" allow-clear />
                  <div class="field-hint">{{ llmModelHint }}</div>
                </a-form-item>

                <a-row :gutter="16">
                  <a-col :span="12">
                    <a-form-item :label="t('settings.llm.maxTokens')" name="max_tokens">
                      <a-input-number v-model:value="llm.max_tokens" :min="64" :max="32768" :step="256" style="width:100%" />
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item :label="t('settings.llm.temperature')" name="temperature">
                      <div class="slider-row">
                        <a-slider v-model:value="llm.temperature" :min="0" :max="2" :step="0.05" style="flex:1" />
                        <a-input-number v-model:value="llm.temperature" :min="0" :max="2" :step="0.05" :precision="2" style="width:72px;margin-left:8px" />
                      </div>
                      <div class="field-hint">{{ t('settings.llm.temperatureHint') }}</div>
                    </a-form-item>
                  </a-col>
                </a-row>

                <a-form-item>
                  <a-button :loading="llmTesting" @click="testLLM">
                    <template #icon><api-outlined /></template>{{ t('settings.llm.testBtn') }}
                  </a-button>
                  <a-tag v-if="llmTestResult === 'ok'" color="success" style="margin-left:10px">
                    <check-circle-outlined /> {{ t('settings.llm.testOk') }}
                  </a-tag>
                  <a-tag v-else-if="llmTestResult === 'fail'" color="error" style="margin-left:10px">
                    <close-circle-outlined /> {{ t('settings.llm.testFail') }}
                  </a-tag>
                  <span v-if="llmTestError" class="test-error">{{ llmTestError }}</span>
                </a-form-item>
              </a-form>
            </div>
          </div>
        </a-tab-pane>

        <!-- OCR tab -->
        <a-tab-pane key="ocr">
          <template #tab>
            <span><scan-outlined /> {{ t('settings.ocr.tab') }}</span>
          </template>
          <div class="tab-content">
            <div class="tab-title">{{ t('settings.ocr.title') }}</div>
            <div class="tab-body">
              <a-form :model="ocr" layout="vertical">
                <a-form-item :label="t('settings.ocr.mode')" name="provider">
                  <a-radio-group v-model:value="ocr.provider" button-style="solid" @change="onOCRProviderChange">
                    <a-radio-button value="local">{{ t('settings.ocr.local') }}</a-radio-button>
                    <a-radio-button value="external">{{ t('settings.ocr.external') }}</a-radio-button>
                  </a-radio-group>
                </a-form-item>

                <template v-if="ocr.provider === 'local'">
                  <a-form-item :label="t('settings.ocr.engine')" name="local_engine">
                    <a-select v-model:value="ocr.local_engine" style="width:280px">
                      <a-select-option value="rapidocr">RapidOCR</a-select-option>
                      <a-select-option value="paddleocr">PaddleOCR</a-select-option>
                    </a-select>
                  </a-form-item>
                  <a-row :gutter="16">
                    <a-col :span="12">
                      <a-form-item :label="t('settings.ocr.dpi')" name="dpi">
                        <a-input-number v-model:value="ocr.dpi" :min="72" :max="600" :step="50" style="width:100%" />
                        <div class="field-hint">{{ t('settings.ocr.dpiHint') }}</div>
                      </a-form-item>
                    </a-col>
                    <a-col :span="12">
                      <a-form-item :label="t('settings.ocr.lang')" name="lang">
                        <a-select v-model:value="ocr.lang" style="width:100%">
                          <a-select-option value="ch">{{ t('settings.ocr.langs.ch') }}</a-select-option>
                          <a-select-option value="en">{{ t('settings.ocr.langs.en') }}</a-select-option>
                          <a-select-option value="japan">{{ t('settings.ocr.langs.japan') }}</a-select-option>
                          <a-select-option value="korean">{{ t('settings.ocr.langs.korean') }}</a-select-option>
                          <a-select-option value="french">{{ t('settings.ocr.langs.french') }}</a-select-option>
                          <a-select-option value="german">{{ t('settings.ocr.langs.german') }}</a-select-option>
                        </a-select>
                        <div class="field-hint">{{ t('settings.ocr.langHint') }}</div>
                      </a-form-item>
                    </a-col>
                  </a-row>
                </template>

                <template v-else>
                  <a-form-item :label="t('settings.ocr.url')" name="external_url">
                    <a-input v-model:value="ocr.external_url" placeholder="https://your-ocr-service.com/ocr" allow-clear />
                    <div class="field-hint">{{ t('settings.ocr.urlHint') }}</div>
                  </a-form-item>
                  <a-form-item :label="t('settings.ocr.extKey')" name="external_api_key">
                    <a-input-password v-model:value="ocr.external_api_key" placeholder="Bearer token" allow-clear autocomplete="off" />
                    <div class="field-hint">{{ t('settings.ocr.extKeyHint') }}</div>
                  </a-form-item>
                  <a-form-item :label="t('settings.ocr.timeout')" name="external_timeout">
                    <a-input-number v-model:value="ocr.external_timeout" :min="5" :max="300" style="width:160px" />
                  </a-form-item>
                  <a-form-item>
                    <a-button :loading="ocrTesting" @click="testOCR">
                      <template #icon><api-outlined /></template>{{ t('settings.ocr.testBtn') }}
                    </a-button>
                    <a-tag v-if="ocrTestResult === 'ok'" color="success" style="margin-left:10px">
                      <check-circle-outlined /> {{ t('settings.ocr.testOk') }}
                    </a-tag>
                    <a-tag v-else-if="ocrTestResult === 'fail'" color="error" style="margin-left:10px">
                      <close-circle-outlined /> {{ t('settings.ocr.testFail') }}
                    </a-tag>
                    <span v-if="ocrTestError" class="test-error">{{ ocrTestError }}</span>
                  </a-form-item>
                </template>
              </a-form>
            </div>
          </div>
        </a-tab-pane>

        <!-- Skills tab -->
        <a-tab-pane key="skills">
          <template #tab>
            <span><bulb-outlined /> {{ t('settings.skills.tab') }}</span>
          </template>
          <div class="tab-content">
            <div class="tab-title">{{ t('settings.skills.title') }}</div>
            <div class="tab-body">
              <p class="field-hint" style="margin-bottom:16px">{{ t('settings.skills.hint') }}</p>

              <div class="skills-toolbar">
                <!-- Hidden file input for zip upload -->
                <input
                  ref="zipInputRef"
                  type="file"
                  accept=".zip"
                  style="display:none"
                  @change="onZipSelected"
                />
                <a-button type="primary" :loading="importingZip" @click="zipModalVisible = true">
                  <template #icon><upload-outlined /></template>
                  {{ t('settings.skills.importZipBtn') }}
                </a-button>
                <a-button @click="openTextModal">
                  <template #icon><file-text-outlined /></template>
                  {{ t('settings.skills.importTextBtn') }}
                </a-button>
              </div>

              <a-empty v-if="skills.length === 0" :description="t('settings.skills.empty')" style="margin-top:32px" />

              <div v-else class="skills-list">
                <div v-for="skill in skills" :key="skill.id" class="skill-item">
                  <div class="skill-item-header">
                    <span class="skill-item-name">{{ skill.name }}</span>
                    <div class="skill-item-badges">
                      <a-tag v-if="skill.has_scripts" color="purple" size="small">{{ t('settings.skills.hasScripts') }}</a-tag>
                      <a-tag v-if="skill.has_assets" color="cyan" size="small">{{ t('settings.skills.hasAssets') }}</a-tag>
                    </div>
                  </div>
                  <div class="skill-item-preview">{{ skill.skill_md.slice(0, 120) }}{{ skill.skill_md.length > 120 ? '…' : '' }}</div>
                  <div class="skill-item-actions">
                    <a-button size="small" type="text" @click="openPreview(skill)">
                      <template #icon><eye-outlined /></template>
                    </a-button>
                    <a-popconfirm :title="t('settings.skills.deleteConfirm')" @confirm="deleteSkill(skill.id)">
                      <a-button size="small" type="text" danger>
                        <template #icon><delete-outlined /></template>
                      </a-button>
                    </a-popconfirm>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </a-tab-pane>

      </a-tabs>

      <a-divider style="margin: 0 0 16px" />
      <div class="actions-bar">
        <a-space>
          <a-button type="primary" :loading="saving" @click="onSave">
            <template #icon><save-outlined /></template>{{ t('settings.save') }}
          </a-button>
          <a-button @click="onReset">{{ t('settings.reset') }}</a-button>
        </a-space>
      </div>
    </a-card>

    <!-- Paste SKILL.md modal -->
    <a-modal
      v-model:open="textModalVisible"
      :title="t('settings.skills.importTextTitle')"
      :ok-text="t('settings.skills.importConfirm')"
      :cancel-text="t('settings.skills.importCancel')"
      :confirm-loading="importingText"
      @ok="importFromText"
      @cancel="closeTextModal"
      width="640px"
    >
      <a-input
        v-model:value="customSkillName"
        :placeholder="t('settings.skills.customNamePlaceholder')"
        style="margin-top:8px;margin-bottom:8px"
      />
      <a-textarea
        v-model:value="pastedText"
        :placeholder="t('settings.skills.importTextPlaceholder')"
        :rows="14"
        style="font-family:monospace;font-size:13px"
      />
    </a-modal>

    <!-- ZIP name modal -->
    <a-modal
      v-model:open="zipModalVisible"
      :title="t('settings.skills.importZipTitle')"
      :ok-text="t('settings.skills.importZipSelectBtn')"
      :cancel-text="t('settings.skills.importCancel')"
      @ok="confirmZipName"
      @cancel="closeZipModal"
      width="480px"
    >
      <a-input
        v-model:value="zipSkillName"
        :placeholder="t('settings.skills.customNamePlaceholder')"
        style="margin-top:8px"
      />
    </a-modal>

    <!-- SKILL.md preview modal -->
    <a-modal
      v-model:open="previewModalVisible"
      :title="t('settings.skills.previewTitle') + ': ' + previewSkill?.name"
      :footer="null"
      width="720px"
    >
      <div class="skill-preview-box">
        <pre>{{ previewSkill?.skill_md }}</pre>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  ApiOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SaveOutlined,
  RobotOutlined,
  ScanOutlined,
  BulbOutlined,
  DeleteOutlined,
  UploadOutlined,
  FileTextOutlined,
  EyeOutlined,
} from '@ant-design/icons-vue'
import { useSettingsStore } from '@/stores/settings'
import http from '@/utils/http'
import type { LLMSettings, OCRSettings, PromptResponse, SkillMeta } from '@/types'

const { t } = useI18n()
const store = useSettingsStore()
const saving = ref(false)

// ── LLM ───────────────────────────────────────────────────────────────────────

const llm = reactive<LLMSettings>({
  provider: 'anthropic', api_key: '', base_url: '',
  model: 'claude-sonnet-4-6', max_tokens: 1024, temperature: 0.7,
})
const llmTesting = ref(false)
const llmTestResult = ref<'ok' | 'fail' | null>(null)
const llmTestError = ref('')

// ── OCR ───────────────────────────────────────────────────────────────────────

const ocr = reactive<OCRSettings>({
  provider: 'local', local_engine: 'rapidocr', dpi: 150, lang: 'ch',
  external_url: '', external_api_key: '', external_timeout: 30,
})
const ocrTesting = ref(false)
const ocrTestResult = ref<'ok' | 'fail' | null>(null)
const ocrTestError = ref('')

// ── Skills ────────────────────────────────────────────────────────────────────

const skills = ref<SkillMeta[]>([])
const zipInputRef = ref<HTMLInputElement | null>(null)
const importingZip = ref(false)
const zipModalVisible = ref(false)
const zipSkillName = ref('')
const textModalVisible = ref(false)
const importingText = ref(false)
const pastedText = ref('')
const customSkillName = ref('')
const previewModalVisible = ref(false)
const previewSkill = ref<SkillMeta | null>(null)

async function fetchSkills() {
  try {
    skills.value = await http.get<unknown, SkillMeta[]>('/skills')
  } catch {
    skills.value = []
  }
}

async function onZipSelected(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  importingZip.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    if (zipSkillName.value.trim()) {
      formData.append('name', zipSkillName.value.trim())
    }
    const skill = await http.post<unknown, SkillMeta>('/skills/from-zip', formData)
    skills.value.push(skill)
    message.success(t('settings.skills.importZipSuccess'))
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : t('settings.skills.importFail'))
  } finally {
    importingZip.value = false
    zipSkillName.value = ''
    ;(e.target as HTMLInputElement).value = ''
  }
}

function confirmZipName() {
  zipModalVisible.value = false
  zipInputRef.value?.click()
}

function closeZipModal() {
  zipModalVisible.value = false
  zipSkillName.value = ''
}

function openTextModal() {
  textModalVisible.value = true
}

function closeTextModal() {
  textModalVisible.value = false
  pastedText.value = ''
  customSkillName.value = ''
}

async function importFromText() {
  if (!pastedText.value.trim()) return
  importingText.value = true
  try {
    const skill = await http.post<unknown, SkillMeta>('/skills/from-text', {
      skill_md: pastedText.value.trim(),
      name: customSkillName.value.trim() || undefined,
    })
    skills.value.push(skill)
    message.success(t('settings.skills.importTextSuccess'))
    textModalVisible.value = false
    pastedText.value = ''
    customSkillName.value = ''
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : t('settings.skills.importFail'))
  } finally {
    importingText.value = false
  }
}

async function deleteSkill(id: string) {
  try {
    await http.delete(`/skills/${id}`)
    skills.value = skills.value.filter(s => s.id !== id)
    message.success(t('settings.skills.deleteOk'))
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : t('settings.skills.deleteFail'))
  }
}

function openPreview(skill: SkillMeta) {
  previewSkill.value = skill
  previewModalVisible.value = true
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────

onMounted(async () => {
  await store.fetch()
  Object.assign(llm, store.settings.llm)
  Object.assign(ocr, store.settings.ocr)
  await fetchSkills()
})

// ── LLM helpers ───────────────────────────────────────────────────────────────

const LLM_MODELS: Record<string, { value: string; label: string }[]> = {
  anthropic: [
    { value: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6' },
    { value: 'claude-opus-4-7', label: 'Claude Opus 4.7' },
    { value: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5' },
  ],
  openai: [
    { value: 'gpt-4o', label: 'GPT-4o' },
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
  ],
  custom: [],
}

const llmModelOptions = computed(() =>
  LLM_MODELS[llm.provider]?.map((m) => ({ value: m.value, label: m.label })) ?? []
)
const llmKeyPlaceholder = computed(() =>
  ({ anthropic: 'sk-ant-...', openai: 'sk-...', custom: 'Bearer token' }[llm.provider] ?? 'API Key')
)
const llmModelHint = computed(() =>
  ({ anthropic: 'claude-sonnet-4-6 recommended', openai: 'gpt-4o recommended', custom: 'Enter the model ID supported by your service' }[llm.provider] ?? '')
)

function onLLMProviderChange() {
  llmTestResult.value = null
  llmTestError.value = ''
  llm.model = ({ anthropic: 'claude-sonnet-4-6', openai: 'gpt-4o', custom: '' }[llm.provider] ?? '')
  if (llm.provider === 'anthropic') llm.base_url = ''
}
function onOCRProviderChange() {
  ocrTestResult.value = null
  ocrTestError.value = ''
}

async function onSave() {
  saving.value = true
  try {
    await store.save({ llm: { ...llm }, ocr: { ...ocr } })
    message.success(t('settings.saved'))
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : t('settings.saveFail'))
  } finally {
    saving.value = false
  }
}

async function testLLM() {
  llmTesting.value = true
  llmTestResult.value = null
  llmTestError.value = ''
  try {
    await store.save({ llm: { ...llm }, ocr: { ...ocr } })
    const res = await http.post<unknown, PromptResponse>('/prompt/generate', { content: 'test', type: 'general' })
    llmTestResult.value = res.code === 200 ? 'ok' : 'fail'
    if (res.code !== 200) llmTestError.value = res.message
  } catch (err: unknown) {
    llmTestResult.value = 'fail'
    llmTestError.value = err instanceof Error ? err.message : t('settings.llm.testFail')
  } finally {
    llmTesting.value = false
  }
}

async function testOCR() {
  ocrTesting.value = true
  ocrTestResult.value = null
  ocrTestError.value = ''
  try {
    const res = await http.post<unknown, { code: number; message: string }>('/settings/ocr/test', { ...ocr })
    ocrTestResult.value = res.code === 200 ? 'ok' : 'fail'
    if (res.code !== 200) ocrTestError.value = res.message
  } catch (err: unknown) {
    ocrTestResult.value = 'fail'
    ocrTestError.value = err instanceof Error ? err.message : t('settings.ocr.testFail')
  } finally {
    ocrTesting.value = false
  }
}

function onReset() {
  Object.assign(llm, { provider: 'anthropic', api_key: '', base_url: '', model: 'claude-sonnet-4-6', max_tokens: 1024, temperature: 0.7 })
  Object.assign(ocr, { provider: 'local', local_engine: 'rapidocr', dpi: 150, lang: 'ch', external_url: '', external_api_key: '', external_timeout: 30 })
  llmTestResult.value = null
  ocrTestResult.value = null
  llmTestError.value = ''
  ocrTestError.value = ''
}
</script>

<style scoped>
.settings-page {
  padding: 8px;
  height: calc(100vh - 112px);
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}
.settings-card { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; }
:deep(.settings-card .ant-card-body) { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; padding-bottom: 0; }
.settings-tabs { flex: 1; min-height: 0; overflow: hidden; }
:deep(.settings-tabs.ant-tabs-left) { height: 100%; overflow: hidden; }
:deep(.settings-tabs .ant-tabs-nav) { width: 140px; overflow-y: auto; align-self: stretch; }
:deep(.settings-tabs .ant-tabs-content-holder) { flex: 1; min-height: 0; overflow: hidden; }
:deep(.settings-tabs .ant-tabs-content) { height: 100%; }
:deep(.settings-tabs .ant-tabs-tabpane) { height: 100%; }
:deep(.ant-tabs-tab) { justify-content: flex-start; padding: 10px 16px; }
.tab-content { display: flex; flex-direction: column; height: 100%; }
.tab-title { flex-shrink: 0; font-size: 16px; font-weight: 600; color: #1a1a1a; padding: 0 24px 12px; border-bottom: 1px solid #f0f0f0; }
.tab-body { flex: 1; min-height: 0; overflow-y: auto; padding: 16px 24px 8px; }
.actions-bar { flex-shrink: 0; padding: 12px 0 12px 164px; }
.field-hint { font-size: 12px; color: #8c8c8c; margin-top: 4px; line-height: 1.5; }
.slider-row { display: flex; align-items: center; }
.test-error { margin-left: 8px; font-size: 12px; color: #ff4d4f; }

/* Skills */
.skills-toolbar { display: flex; gap: 8px; margin-bottom: 16px; }

.skills-list { display: flex; flex-direction: column; gap: 8px; }

.skill-item {
  padding: 12px 16px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  transition: border-color 0.2s;
}
.skill-item:hover { border-color: #d9d9d9; }

.skill-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.skill-item-name { font-weight: 600; font-size: 14px; color: #1a1a1a; }
.skill-item-badges { display: flex; gap: 4px; }

.skill-item-preview {
  font-size: 12px;
  color: #8c8c8c;
  line-height: 1.5;
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-word;
  margin-bottom: 8px;
}

.skill-item-actions { display: flex; gap: 4px; justify-content: flex-end; }

.skill-preview-box {
  max-height: 60vh;
  overflow-y: auto;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  padding: 16px;
}
.skill-preview-box pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  line-height: 1.7;
  font-family: monospace;
}
</style>
