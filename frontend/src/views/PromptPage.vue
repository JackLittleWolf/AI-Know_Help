<template>
  <div class="prompt-page">
    <SplitPane :default-left-width="420">
      <template #left>
        <div class="panel">
          <a-card :title="t('prompt.input.title')" :bordered="false">
            <a-form layout="vertical">
              <a-form-item :label="t('prompt.input.typeLabel')">
                <a-select v-model:value="promptType" style="width: 100%">
                  <a-select-option value="general">{{ t('prompt.input.types.general') }}</a-select-option>
                  <a-select-option value="code">{{ t('prompt.input.types.code') }}</a-select-option>
                  <a-select-option value="summary">{{ t('prompt.input.types.summary') }}</a-select-option>
                  <a-select-option value="analysis">{{ t('prompt.input.types.analysis') }}</a-select-option>
                  <a-select-option value="translation">{{ t('prompt.input.types.translation') }}</a-select-option>
                </a-select>
              </a-form-item>

              <a-form-item :label="t('prompt.input.skillsLabel')">
                <div class="skills-grid">
                  <a-empty
                    v-if="skills.length === 0"
                    :description="t('prompt.input.skillsEmpty')"
                    style="margin: 0; font-size: 12px;"
                  />
                  <a-tooltip
                    v-for="skill in skills"
                    :key="skill.id"
                    :title="skill.skill_md.slice(0, 200)"
                    placement="right"
                  >
                    <a-tag
                      :color="selectedSkills.includes(skill.id) ? 'blue' : 'default'"
                      class="skill-tag"
                      @click="toggleSkill(skill.id)"
                    >
                      {{ skill.name }}
                    </a-tag>
                  </a-tooltip>
                </div>
              </a-form-item>

              <a-form-item label=" ">
                <a-textarea
                  v-model:value="inputContent"
                  :placeholder="t('prompt.input.placeholder')"
                  :rows="10"
                  :maxlength="5000"
                  show-count
                  allow-clear
                />
              </a-form-item>

              <a-form-item>
                <a-button
                  type="primary"
                  block
                  :loading="generating"
                  :disabled="!inputContent.trim()"
                  @click="generatePrompt"
                >
                  <template #icon><thunderbolt-outlined /></template>
                  {{ t('prompt.input.generate') }}
                </a-button>
              </a-form-item>
            </a-form>
          </a-card>
        </div>
      </template>

      <template #right>
        <div class="panel">
          <a-card :bordered="false">
            <template #title>{{ t('prompt.result.title') }}</template>
            <template #extra>
              <a-space v-if="promptData">
                <a-button size="small" @click="copyPrompt">
                  <template #icon><copy-outlined /></template>
                  {{ t('prompt.result.copy') }}
                </a-button>
                <a-button size="small" :loading="validating" @click="validatePrompt">
                  <template #icon><check-circle-outlined /></template>
                  {{ t('prompt.result.validate') }}
                </a-button>
              </a-space>
            </template>

            <div v-if="generating" class="generating-state">
              <a-spin size="large" />
              <p class="generating-text">{{ t('prompt.result.generating') }}</p>
            </div>

            <a-empty v-else-if="!promptData" :description="t('prompt.result.empty')" />

            <div v-else class="result-content">
              <div class="result-section">
                <div class="section-label">{{ t('prompt.result.promptLabel') }}</div>
                <div class="prompt-box">
                  <pre class="prompt-text">{{ promptData.generated_prompt }}</pre>
                </div>
              </div>

              <div v-if="promptData.explanation" class="result-section">
                <div class="section-label">{{ t('prompt.result.explanationLabel') }}</div>
                <a-alert :message="promptData.explanation" type="info" show-icon />
              </div>

              <div v-if="validationResult" class="result-section">
                <div class="section-label">{{ t('prompt.result.validationLabel') }}</div>
                <div class="validation-box">
                  <pre class="validation-text">{{ validationResult }}</pre>
                </div>
              </div>

              <!-- Test prompt section -->
              <a-divider />
              <div class="result-section">
                <div class="section-label">{{ t('prompt.test.title') }}</div>
                <a-textarea
                  v-model:value="testInput"
                  :placeholder="t('prompt.test.placeholder')"
                  :rows="4"
                  :maxlength="2000"
                  show-count
                  allow-clear
                />
                <a-button
                  type="default"
                  :loading="testing"
                  :disabled="!testInput.trim()"
                  @click="runTest"
                >
                  <template #icon><play-circle-outlined /></template>
                  {{ t('prompt.test.run') }}
                </a-button>
                <div v-if="testResult !== null">
                  <div class="section-label" style="margin-top: 8px;">{{ t('prompt.test.resultLabel') }}</div>
                  <div class="test-result-box">
                    <pre class="prompt-text">{{ testResult }}</pre>
                  </div>
                </div>
              </div>
            </div>
          </a-card>
        </div>
      </template>
    </SplitPane>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  ThunderboltOutlined,
  CopyOutlined,
  CheckCircleOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons-vue'
import SplitPane from '@/components/SplitPane.vue'
import http from '@/utils/http'
import type { PromptData, PromptResponse, SkillMeta, TestPromptResponse } from '@/types'

const { t } = useI18n()
const inputContent = ref('')
const promptType = ref('general')
const selectedSkills = ref<string[]>([])
const skills = ref<SkillMeta[]>([])
const generating = ref(false)
const validating = ref(false)
const testing = ref(false)
const promptData = ref<PromptData | null>(null)
const validationResult = ref<string | null>(null)
const testInput = ref('')
const testResult = ref<string | null>(null)

onMounted(async () => {
  try {
    skills.value = await http.get<unknown, SkillMeta[]>('/skills')
  } catch {
    // fall back to empty
  }
})

function toggleSkill(key: string) {
  const idx = selectedSkills.value.indexOf(key)
  if (idx === -1) {
    selectedSkills.value.push(key)
  } else {
    selectedSkills.value.splice(idx, 1)
  }
}

async function generatePrompt() {
  if (!inputContent.value.trim()) return
  generating.value = true
  promptData.value = null
  validationResult.value = null
  try {
    const res = await http.post<unknown, PromptResponse>('/prompt/generate', {
      content: inputContent.value,
      type: promptType.value,
      skills: selectedSkills.value,
    })
    if (res.code === 200 && res.data) {
      promptData.value = res.data
      message.success(t('prompt.result.success'))
    } else {
      message.error(res.message || t('prompt.result.success'))
    }
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : t('prompt.result.success'))
  } finally {
    generating.value = false
  }
}

async function copyPrompt() {
  if (!promptData.value) return
  await navigator.clipboard.writeText(promptData.value.generated_prompt)
  message.success(t('prompt.result.copied'))
}

async function validatePrompt() {
  if (!promptData.value) return
  validating.value = true
  try {
    const res = await http.post<unknown, PromptResponse>('/prompt/generate', {
      content: `Please test the following prompt with a brief response:\n\n${promptData.value.generated_prompt}`,
      type: 'general',
    })
    if (res.code === 200 && res.data) {
      validationResult.value = res.data.generated_prompt
      message.success(t('prompt.result.validateSuccess'))
    }
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : t('prompt.result.validateSuccess'))
  } finally {
    validating.value = false
  }
}

async function runTest() {
  if (!promptData.value) {
    message.warning(t('prompt.test.noPrompt'))
    return
  }
  if (!testInput.value.trim()) return
  testing.value = true
  testResult.value = null
  try {
    const res = await http.post<unknown, TestPromptResponse>('/prompt/test', {
      prompt: promptData.value.generated_prompt,
      user_input: testInput.value,
    })
    if (res.code === 200 && res.data) {
      testResult.value = res.data.result
      message.success(t('prompt.test.success'))
    } else {
      message.error(res.message)
    }
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : t('prompt.test.success'))
  } finally {
    testing.value = false
  }
}
</script>

<style scoped>
.prompt-page { height: calc(100vh - 112px); }
.panel { padding: 8px; height: 100%; }

.skills-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.skill-tag {
  cursor: pointer;
  user-select: none;
  transition: all 0.2s;
}

.generating-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 0;
  gap: 16px;
}
.generating-text { color: #8c8c8c; margin: 0; }

.result-content { display: flex; flex-direction: column; gap: 20px; }
.result-section { display: flex; flex-direction: column; gap: 8px; }
.section-label { font-weight: 600; color: #1677ff; font-size: 13px; }

.prompt-box, .validation-box {
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.prompt-text, .validation-text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.7;
}
</style>
