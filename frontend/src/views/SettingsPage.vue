<template>
  <div class="settings-page">
    <a-card v-if="settingsUnlocked" :bordered="false" class="settings-card">
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

                <a-form-item :label="t('settings.llm.enableThinking')" name="enable_thinking">
                  <a-switch v-model:checked="llm.enable_thinking" />
                  <div class="field-hint">{{ t('settings.llm.enableThinkingHint') }}</div>
                </a-form-item>

                <a-form-item
                  v-if="llm.enable_thinking"
                  :label="t('settings.llm.thinkingBudgetTokens')"
                  name="thinking_budget_tokens"
                >
                  <a-input-number
                    v-model:value="llm.thinking_budget_tokens"
                    :min="1024"
                    :max="64000"
                    :step="1024"
                    style="width:280px"
                  />
                  <div class="field-hint">{{ t('settings.llm.thinkingBudgetHint') }}</div>
                </a-form-item>

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

        <!-- Storage tab -->
        <a-tab-pane key="storage">
          <template #tab>
            <span><upload-outlined /> {{ t('settings.storage.tab') }}</span>
          </template>
          <div class="tab-content">
            <div class="tab-title">{{ t('settings.storage.title') }}</div>
            <div class="tab-body">
              <a-form :model="storage" layout="vertical">
                <a-form-item :label="t('settings.storage.uploadDir')" name="upload_dir">
                  <a-input v-model:value="storage.upload_dir" :placeholder="t('settings.storage.uploadDirPlaceholder')" allow-clear />
                  <div class="field-hint">{{ t('settings.storage.uploadDirHint') }}</div>
                </a-form-item>
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

        <!-- MCP tab -->
        <a-tab-pane key="mcp">
          <template #tab>
            <span><api-outlined /> {{ t('settings.mcp.tab') }}</span>
          </template>
          <div class="tab-content">
            <div class="tab-title">{{ t('settings.mcp.title') }}</div>
            <div class="tab-body">
              <p class="field-hint" style="margin-bottom:16px">{{ t('settings.mcp.hint') }}</p>

              <div class="mcp-toolbar">
                <a-button type="primary" @click="addMCPServer">
                  <template #icon><plus-outlined /></template>
                  {{ t('settings.mcp.addServer') }}
                </a-button>
              </div>

              <a-empty v-if="mcpServers.length === 0" :description="t('settings.mcp.empty')" style="margin-top:32px" />

              <div v-else class="mcp-server-list">
                <div v-for="(srv, idx) in mcpServers" :key="idx" class="mcp-server-item">
                  <div class="mcp-server-header">
                    <a-switch v-model:checked="srv.enabled" size="small" />
                    <span class="mcp-server-index">#{{ idx + 1 }}</span>
                    <a-button size="small" type="text" danger @click="removeMCPServer(idx)">
                      <template #icon><delete-outlined /></template>
                      {{ t('settings.mcp.removeServer') }}
                    </a-button>
                  </div>
                  <a-form layout="vertical" style="margin-top:8px">
                    <a-row :gutter="12">
                      <a-col :span="8">
                        <a-form-item :label="t('settings.mcp.serverName')">
                          <a-input v-model:value="srv.name" :placeholder="t('settings.mcp.serverNamePlaceholder')" allow-clear />
                        </a-form-item>
                      </a-col>
                      <a-col :span="10">
                        <a-form-item :label="t('settings.mcp.serverUrl')">
                          <a-input v-model:value="srv.url" :placeholder="t('settings.mcp.serverUrlPlaceholder')" allow-clear />
                        </a-form-item>
                      </a-col>
                      <a-col :span="6">
                        <a-form-item :label="t('settings.mcp.serverApiKey')">
                          <a-input-password v-model:value="srv.api_key" :placeholder="t('settings.mcp.serverApiKeyPlaceholder')" allow-clear autocomplete="off" />
                        </a-form-item>
                      </a-col>
                    </a-row>
                    <a-form-item style="margin-bottom:0">
                      <a-button size="small" :loading="mcpTestingIdx === idx" @click="testMCPServer(idx)">
                        <template #icon><api-outlined /></template>{{ t('settings.mcp.testBtn') }}
                      </a-button>
                      <a-tag v-if="mcpTestResults[idx] === 'ok'" color="success" style="margin-left:8px">
                        <check-circle-outlined /> {{ t('settings.mcp.testOk') }}
                      </a-tag>
                      <a-tag v-else-if="mcpTestResults[idx] === 'fail'" color="error" style="margin-left:8px">
                        <close-circle-outlined /> {{ t('settings.mcp.testFail') }}
                      </a-tag>
                      <span v-if="mcpTestErrors[idx]" class="test-error">{{ mcpTestErrors[idx] }}</span>
                    </a-form-item>
                  </a-form>
                </div>
              </div>
            </div>
          </div>
        </a-tab-pane>

        <!-- Knowledge Base tab -->
        <a-tab-pane key="knowledge">
          <template #tab>
            <span><database-outlined /> {{ t('settings.knowledge.tab') }}</span>
          </template>
          <div class="tab-content">
            <div class="tab-title">{{ t('settings.knowledge.embeddingTitle') }}</div>
            <div class="tab-body">
              <a-form :model="embedding" layout="vertical">
                <a-form-item :label="t('settings.knowledge.embeddingProvider')">
                  <a-radio-group v-model:value="embedding.provider" button-style="solid">
                    <a-radio-button value="ollama">Ollama</a-radio-button>
                    <a-radio-button value="openai">OpenAI</a-radio-button>
                    <a-radio-button value="huggingface">HuggingFace</a-radio-button>
                  </a-radio-group>
                </a-form-item>

                <template v-if="embedding.provider === 'ollama'">
                  <a-row :gutter="12">
                    <a-col :span="14">
                      <a-form-item :label="t('settings.knowledge.ollamaBaseUrl')">
                        <a-input v-model:value="embedding.ollama_base_url" placeholder="http://localhost:11434" allow-clear />
                      </a-form-item>
                    </a-col>
                    <a-col :span="10">
                      <a-form-item :label="t('settings.knowledge.ollamaModel')">
                        <a-input v-model:value="embedding.ollama_model" placeholder="nomic-embed-text" allow-clear />
                      </a-form-item>
                    </a-col>
                  </a-row>
                </template>

                <template v-if="embedding.provider === 'openai'">
                  <a-form-item :label="t('settings.knowledge.openaiApiKey')">
                    <a-input-password v-model:value="embedding.openai_api_key" placeholder="sk-..." allow-clear autocomplete="off" />
                  </a-form-item>
                  <a-row :gutter="12">
                    <a-col :span="14">
                      <a-form-item :label="t('settings.knowledge.openaiBaseUrl')">
                        <a-input v-model:value="embedding.openai_base_url" placeholder="https://api.openai.com/v1" allow-clear />
                      </a-form-item>
                    </a-col>
                    <a-col :span="10">
                      <a-form-item :label="t('settings.knowledge.openaiModel')">
                        <a-input v-model:value="embedding.openai_model" placeholder="text-embedding-3-small" allow-clear />
                      </a-form-item>
                    </a-col>
                  </a-row>
                </template>

                <template v-if="embedding.provider === 'huggingface'">
                  <a-form-item :label="t('settings.knowledge.hfModelName')">
                    <a-input v-model:value="embedding.hf_model_name" placeholder="BAAI/bge-small-zh-v1.5" allow-clear />
                  </a-form-item>
                </template>

                <a-row :gutter="12">
                  <a-col :span="12">
                    <a-form-item :label="t('settings.knowledge.chunkSize')">
                      <a-input-number v-model:value="embedding.chunk_size" :min="100" :max="4000" :step="100" style="width:100%" />
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item :label="t('settings.knowledge.chunkOverlap')">
                      <a-input-number v-model:value="embedding.chunk_overlap" :min="0" :max="500" :step="10" style="width:100%" />
                    </a-form-item>
                  </a-col>
                </a-row>
              </a-form>

              <a-divider />
              <div class="tab-title" style="margin-bottom:16px">{{ t('settings.knowledge.vdbTitle') }}</div>
              <a-form :model="vectorDb" layout="vertical">
                <a-form-item :label="t('settings.knowledge.vdbProvider')">
                  <a-radio-group v-model:value="vectorDb.provider" button-style="solid">
                    <a-radio-button value="chroma">Chroma</a-radio-button>
                    <a-radio-button value="qdrant">Qdrant</a-radio-button>
                    <a-radio-button value="milvus">Milvus</a-radio-button>
                    <a-radio-button value="pgvector">PGVector</a-radio-button>
                  </a-radio-group>
                </a-form-item>

                <template v-if="vectorDb.provider === 'chroma'">
                  <a-form-item :label="t('settings.knowledge.chromaPersistDir')">
                    <a-input v-model:value="vectorDb.chroma_persist_dir" placeholder="./data/chroma" allow-clear />
                  </a-form-item>
                </template>

                <template v-if="vectorDb.provider === 'qdrant'">
                  <a-row :gutter="12">
                    <a-col :span="14">
                      <a-form-item :label="t('settings.knowledge.qdrantUrl')">
                        <a-input v-model:value="vectorDb.qdrant_url" placeholder="http://localhost:6333" allow-clear />
                      </a-form-item>
                    </a-col>
                    <a-col :span="10">
                      <a-form-item :label="t('settings.knowledge.qdrantApiKey')">
                        <a-input-password v-model:value="vectorDb.qdrant_api_key" allow-clear autocomplete="off" />
                      </a-form-item>
                    </a-col>
                  </a-row>
                </template>

                <template v-if="vectorDb.provider === 'milvus'">
                  <a-row :gutter="12">
                    <a-col :span="14">
                      <a-form-item :label="t('settings.knowledge.milvusUri')">
                        <a-input v-model:value="vectorDb.milvus_uri" placeholder="http://localhost:19530" allow-clear />
                      </a-form-item>
                    </a-col>
                    <a-col :span="10">
                      <a-form-item :label="t('settings.knowledge.milvusToken')">
                        <a-input-password v-model:value="vectorDb.milvus_token" allow-clear autocomplete="off" />
                      </a-form-item>
                    </a-col>
                  </a-row>
                </template>

                <template v-if="vectorDb.provider === 'pgvector'">
                  <a-form-item :label="t('settings.knowledge.pgvectorDsn')">
                    <a-input-password v-model:value="vectorDb.pgvector_dsn" placeholder="postgresql://user:pass@localhost:5432/dbname" allow-clear autocomplete="off" />
                  </a-form-item>
                </template>

                <a-form-item>
                  <a-button :loading="kbTesting" @click="testKBConnection">
                    <template #icon><api-outlined /></template>{{ t('settings.knowledge.testBtn') }}
                  </a-button>
                  <a-tag v-if="kbTestResult === 'ok'" color="success" style="margin-left:10px">
                    <check-circle-outlined /> {{ t('settings.knowledge.testOk') }}
                  </a-tag>
                  <a-tag v-else-if="kbTestResult === 'fail'" color="error" style="margin-left:10px">
                    <close-circle-outlined /> {{ t('settings.knowledge.testFail') }}
                  </a-tag>
                  <span v-if="kbTestError" class="test-error">{{ kbTestError }}</span>
                </a-form-item>
              </a-form>
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

    <a-modal
      v-model:open="passwordModalVisible"
      :title="t('settings.password.title')"
      :ok-text="t('settings.password.confirm')"
      :cancel-text="t('settings.password.close')"
      :confirm-loading="verifyingPassword"
      :closable="true"
      :mask-closable="false"
      width="420px"
      @ok="verifySettingsPassword"
      @cancel="closeSettingsPasswordModal"
    >
      <a-form layout="vertical" @submit.prevent="verifySettingsPassword">
        <a-form-item :label="t('settings.password.label')">
          <a-input-password
            v-model:value="settingsPassword"
            :placeholder="t('settings.password.placeholder')"
            autocomplete="current-password"
            @press-enter="verifySettingsPassword"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
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
  PlusOutlined,
  DatabaseOutlined,
} from '@ant-design/icons-vue'
import { useSettingsStore } from '@/stores/settings'
import http from '@/utils/http'
import type { LLMSettings, MCPServerSettings, OCRSettings, PromptResponse, SkillMeta, StorageSettings, EmbeddingSettings, VectorDBSettings } from '@/types'

const { t } = useI18n()
const router = useRouter()
const store = useSettingsStore()
const saving = ref(false)
const settingsUnlocked = ref(false)
const passwordModalVisible = ref(true)
const verifyingPassword = ref(false)
const settingsPassword = ref('')

// ── LLM ───────────────────────────────────────────────────────────────────────

const llm = reactive<LLMSettings>({
  provider: 'anthropic', api_key: '', base_url: '',
  model: 'claude-sonnet-4-6', max_tokens: 1024, temperature: 0.7,
  enable_thinking: false, thinking_budget_tokens: 10000,
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

// ── Storage ───────────────────────────────────────────────────────────────────

const storage = reactive<StorageSettings>({
  upload_dir: '/tmp/ocr_uploads',
})

// ── MCP ───────────────────────────────────────────────────────────────────────

const mcpServers = ref<MCPServerSettings[]>([])
const mcpTestingIdx = ref<number | null>(null)
const mcpTestResults = ref<Record<number, 'ok' | 'fail'>>({})
const mcpTestErrors = ref<Record<number, string>>({})

// ── Embedding & Vector DB ─────────────────────────────────────────────────────

const embedding = reactive<EmbeddingSettings>({
  provider: 'ollama',
  ollama_base_url: 'http://localhost:11434',
  ollama_model: 'nomic-embed-text',
  openai_api_key: '',
  openai_base_url: '',
  openai_model: 'text-embedding-3-small',
  hf_model_name: 'BAAI/bge-small-zh-v1.5',
  chunk_size: 500,
  chunk_overlap: 50,
})

const vectorDb = reactive<VectorDBSettings>({
  provider: 'chroma',
  chroma_persist_dir: './data/chroma',
  qdrant_url: 'http://localhost:6333',
  qdrant_api_key: '',
  milvus_uri: 'http://localhost:19530',
  milvus_token: '',
  pgvector_dsn: '',
})

const kbTesting = ref(false)
const kbTestResult = ref<'ok' | 'fail' | null>(null)
const kbTestError = ref('')

async function testKBConnection() {
  kbTesting.value = true
  kbTestResult.value = null
  kbTestError.value = ''
  try {
    await store.save({
      llm: { ...llm }, ocr: { ...ocr }, storage: { ...storage },
      mcp: { servers: mcpServers.value.map(s => ({ ...s })) },
      embedding: { ...embedding }, vector_db: { ...vectorDb },
    })
    const res = await http.post<unknown, { code: number; message: string }>('/knowledge/test-connection', {})
    kbTestResult.value = res.code === 200 ? 'ok' : 'fail'
    if (res.code !== 200) kbTestError.value = res.message
  } catch (err: unknown) {
    kbTestResult.value = 'fail'
    kbTestError.value = err instanceof Error ? err.message : t('settings.knowledge.testFail')
  } finally {
    kbTesting.value = false
  }
}

function addMCPServer() {
  mcpServers.value.push({ name: '', url: '', api_key: '', enabled: true })
}

function removeMCPServer(idx: number) {
  mcpServers.value.splice(idx, 1)
  delete mcpTestResults.value[idx]
  delete mcpTestErrors.value[idx]
}

async function testMCPServer(idx: number) {
  const srv = mcpServers.value[idx]
  if (!srv.url) return
  mcpTestingIdx.value = idx
  delete mcpTestResults.value[idx]
  delete mcpTestErrors.value[idx]
  try {
    const res = await http.post<unknown, { code: number; message: string }>('/settings/mcp/test', {
      name: srv.name,
      url: srv.url,
      api_key: srv.api_key,
      enabled: srv.enabled,
    })
    mcpTestResults.value[idx] = res.code === 200 ? 'ok' : 'fail'
    if (res.code !== 200) mcpTestErrors.value[idx] = res.message
  } catch (err: unknown) {
    mcpTestResults.value[idx] = 'fail'
    mcpTestErrors.value[idx] = err instanceof Error ? err.message : t('settings.mcp.testFail')
  } finally {
    mcpTestingIdx.value = null
  }
}

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
  passwordModalVisible.value = true
})

async function loadSettingsPageData() {
  await store.fetch()
  Object.assign(llm, store.settings.llm)
  Object.assign(ocr, store.settings.ocr)
  Object.assign(storage, store.settings.storage ?? { upload_dir: '/tmp/ocr_uploads' })
  mcpServers.value = (store.settings.mcp?.servers ?? []).map(s => ({ ...s }))
  if (store.settings.embedding) Object.assign(embedding, store.settings.embedding)
  if (store.settings.vector_db) Object.assign(vectorDb, store.settings.vector_db)
  await fetchSkills()
}

async function verifySettingsPassword() {
  if (!settingsPassword.value.trim()) {
    message.warning(t('settings.password.required'))
    return
  }
  verifyingPassword.value = true
  try {
    await http.post<unknown, { code: number; message: string }>('/settings/verify-password', {
      password: settingsPassword.value,
    })
    settingsUnlocked.value = true
    passwordModalVisible.value = false
    settingsPassword.value = ''
    await loadSettingsPageData()
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : t('settings.password.fail'))
  } finally {
    verifyingPassword.value = false
  }
}

function closeSettingsPasswordModal() {
  passwordModalVisible.value = false
  router.push('/ocr')
}

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
  ({
    anthropic: t('settings.llm.modelHintAnthropic'),
    openai: t('settings.llm.modelHintOpenAI'),
    custom: t('settings.llm.modelHintCustom'),
  }[llm.provider] ?? '')
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
    await store.save({
      llm: { ...llm },
      ocr: { ...ocr },
      storage: { ...storage },
      mcp: { servers: mcpServers.value.map(s => ({ ...s })) },
      embedding: { ...embedding },
      vector_db: { ...vectorDb },
    })
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
    await store.save({
      llm: { ...llm },
      ocr: { ...ocr },
      storage: { ...storage },
      mcp: { servers: mcpServers.value.map(s => ({ ...s })) },
      embedding: { ...embedding },
      vector_db: { ...vectorDb },
    })
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
  Object.assign(llm, {
    provider: 'anthropic',
    api_key: '',
    base_url: '',
    model: 'claude-sonnet-4-6',
    max_tokens: 1024,
    temperature: 0.7,
    enable_thinking: false,
    thinking_budget_tokens: 10000,
  })
  Object.assign(ocr, { provider: 'local', local_engine: 'rapidocr', dpi: 150, lang: 'ch', external_url: '', external_api_key: '', external_timeout: 30 })
  Object.assign(storage, { upload_dir: '/tmp/ocr_uploads' })
  mcpServers.value = []
  mcpTestResults.value = {}
  mcpTestErrors.value = {}
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

/* MCP */
.mcp-toolbar { margin-bottom: 16px; }

.mcp-server-list { display: flex; flex-direction: column; gap: 12px; }

.mcp-server-item {
  padding: 14px 16px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  transition: border-color 0.2s;
}
.mcp-server-item:hover { border-color: #d9d9d9; }

.mcp-server-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.mcp-server-index { font-size: 12px; color: #8c8c8c; flex: 1; }
</style>
