<template>
  <div class="kb-page">
    <!-- Left: KB list -->
    <div class="kb-sider">
      <a-button type="primary" block @click="showCreateModal = true" class="create-btn">
        <template #icon><plus-outlined /></template>
        {{ t('knowledge.createBtn') }}
      </a-button>
      <div class="kb-list">
        <div
          v-for="kb in kbList"
          :key="kb.id"
          :class="['kb-item', { active: activeKbId === kb.id }]"
          @click="selectKb(kb.id)"
        >
          <div class="kb-item-main">
            <database-outlined class="kb-icon" />
            <div class="kb-item-info">
              <div class="kb-item-name">{{ kb.name }}</div>
              <div class="kb-item-meta">
                {{ t('knowledge.docCount', { n: kb.doc_count }) }} ·
                {{ t('knowledge.chunkCount', { n: kb.chunk_count }) }}
              </div>
            </div>
          </div>
          <a-popconfirm
            :title="t('knowledge.deleteKBConfirm')"
            @confirm.stop="deleteKb(kb.id)"
            @click.stop
          >
            <delete-outlined class="kb-delete" @click.stop />
          </a-popconfirm>
        </div>
        <div v-if="kbList.length === 0" class="kb-empty">
          <inbox-outlined style="font-size:32px;color:#d9d9d9" />
          <p>{{ t('knowledge.empty') }}</p>
        </div>
      </div>
    </div>

    <!-- Right: content -->
    <div class="kb-content">
      <template v-if="activeKb">
        <div class="kb-header">
          <span class="kb-title">{{ activeKb.name }}</span>
          <span v-if="activeKb.description" class="kb-desc">{{ activeKb.description }}</span>
        </div>
        <a-tabs v-model:activeKey="activeTab" class="kb-tabs">
          <!-- Documents tab -->
          <a-tab-pane key="docs" :tab="t('knowledge.docTab')">
            <a-upload-dragger
              :multiple="true"
              :show-upload-list="false"
              :before-upload="handleUpload"
              accept=".pdf,.docx,.doc,.xlsx,.xls,.pptx,.ppt,.txt,.md"
              class="upload-dragger"
            >
              <p class="ant-upload-drag-icon"><inbox-outlined /></p>
              <p class="ant-upload-text">{{ t('knowledge.uploadHint') }}</p>
            </a-upload-dragger>

            <!-- Upload progress -->
            <div v-if="uploadingFiles.length" class="upload-progress-list">
              <div v-for="uf in uploadingFiles" :key="uf.name" class="upload-progress-item">
                <file-outlined />
                <span class="uf-name">{{ uf.name }}</span>
                <a-progress :percent="uf.percent" size="small" style="flex:1;min-width:80px" />
              </div>
            </div>

            <a-table
              :data-source="docList"
              :columns="docColumns"
              :loading="docsLoading"
              row-key="id"
              size="small"
              class="doc-table"
              :pagination="{ pageSize: 10, showSizeChanger: false }"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'file_size'">
                  {{ formatSize(record.file_size) }}
                </template>
                <template v-if="column.key === 'created_at'">
                  {{ formatDate(record.created_at) }}
                </template>
                <template v-if="column.key === 'action'">
                  <a-popconfirm
                    :title="t('knowledge.deleteDocConfirm')"
                    @confirm="deleteDoc(record.id)"
                  >
                    <a-button type="link" danger size="small">
                      <delete-outlined />
                    </a-button>
                  </a-popconfirm>
                </template>
              </template>
            </a-table>
          </a-tab-pane>

          <!-- Search tab -->
          <a-tab-pane key="search" :tab="t('knowledge.searchTab')">
            <div class="search-bar">
              <a-input
                v-model:value="searchQuery"
                :placeholder="t('knowledge.searchPlaceholder')"
                allow-clear
                @press-enter="doSearch"
              >
                <template #suffix>
                  <a-button type="primary" size="small" :loading="searching" @click="doSearch">
                    {{ t('knowledge.search') }}
                  </a-button>
                </template>
              </a-input>
            </div>
            <div v-if="searchResults.length" class="search-results">
              <div v-for="(r, i) in searchResults" :key="i" class="search-result-card">
                <div class="sr-header">
                  <span class="sr-source"><file-outlined /> {{ r.filename }}</span>
                  <a-tag color="blue">{{ t('knowledge.score') }}: {{ (r.score * 100).toFixed(1) }}%</a-tag>
                </div>
                <div class="sr-content">{{ r.content }}</div>
              </div>
            </div>
            <a-empty v-else-if="searchDone" :description="t('knowledge.noResults')" />
          </a-tab-pane>
        </a-tabs>
      </template>
      <div v-else class="kb-placeholder">
        <database-outlined style="font-size:48px;color:#d9d9d9" />
        <p>{{ t('knowledge.empty') }}</p>
      </div>
    </div>

    <!-- Create KB modal -->
    <a-modal
      v-model:open="showCreateModal"
      :title="t('knowledge.createBtn')"
      @ok="createKb"
      :confirm-loading="creating"
    >
      <a-form layout="vertical">
        <a-form-item :label="t('knowledge.nameLabel')">
          <a-input v-model:value="newKbName" :placeholder="t('knowledge.namePlaceholder')" />
        </a-form-item>
        <a-form-item :label="t('knowledge.descLabel')">
          <a-textarea v-model:value="newKbDesc" :placeholder="t('knowledge.descPlaceholder')" :rows="2" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  DatabaseOutlined,
  DeleteOutlined,
  InboxOutlined,
  FileOutlined,
} from '@ant-design/icons-vue'
import {
  listKBs,
  createKB,
  deleteKB,
  listDocs,
  uploadDoc,
  deleteDoc as apiDeleteDoc,
  searchKB,
} from '@/api/knowledge'
import type { KnowledgeBase, KnowledgeDocument, SearchResult } from '@/types'

const { t } = useI18n()

// ── State ─────────────────────────────────────────────────────────────────────
const kbList = ref<KnowledgeBase[]>([])
const activeKbId = ref<string | null>(null)
const activeKb = computed(() => kbList.value.find(k => k.id === activeKbId.value) ?? null)

const docList = ref<KnowledgeDocument[]>([])
const docsLoading = ref(false)
const activeTab = ref('docs')

const showCreateModal = ref(false)
const newKbName = ref('')
const newKbDesc = ref('')
const creating = ref(false)

interface UploadingFile { name: string; percent: number }
const uploadingFiles = ref<UploadingFile[]>([])

const searchQuery = ref('')
const searchResults = ref<SearchResult[]>([])
const searching = ref(false)
const searchDone = ref(false)

// ── Table columns ─────────────────────────────────────────────────────────────
const docColumns = computed(() => [
  { title: '文件名', dataIndex: 'filename', key: 'filename', ellipsis: true },
  { title: '类型', dataIndex: 'file_type', key: 'file_type', width: 70 },
  { title: '大小', dataIndex: 'file_size', key: 'file_size', width: 90 },
  { title: '分块数', dataIndex: 'chunk_count', key: 'chunk_count', width: 80 },
  { title: '上传时间', dataIndex: 'created_at', key: 'created_at', width: 160 },
  { title: '操作', key: 'action', width: 70 },
])

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(loadKbs)

async function loadKbs() {
  try {
    kbList.value = await listKBs()
  } catch (e: any) {
    message.error(e.message)
  }
}

async function selectKb(id: string) {
  activeKbId.value = id
  activeTab.value = 'docs'
  searchResults.value = []
  searchDone.value = false
  await loadDocs(id)
}

async function loadDocs(kbId: string) {
  docsLoading.value = true
  try {
    docList.value = await listDocs(kbId)
  } catch (e: any) {
    message.error(e.message)
  } finally {
    docsLoading.value = false
  }
}

// ── KB CRUD ───────────────────────────────────────────────────────────────────
async function createKb() {
  if (!newKbName.value.trim()) return
  creating.value = true
  try {
    const kb = await createKB(newKbName.value.trim(), newKbDesc.value.trim())
    kbList.value.unshift(kb)
    showCreateModal.value = false
    newKbName.value = ''
    newKbDesc.value = ''
    message.success(t('knowledge.createSuccess'))
    await selectKb(kb.id)
  } catch (e: any) {
    message.error(e.message)
  } finally {
    creating.value = false
  }
}

async function deleteKb(id: string) {
  try {
    await deleteKB(id)
    kbList.value = kbList.value.filter(k => k.id !== id)
    if (activeKbId.value === id) {
      activeKbId.value = null
      docList.value = []
    }
    message.success(t('knowledge.deleteSuccess'))
  } catch (e: any) {
    message.error(e.message)
  }
}

// ── Upload ────────────────────────────────────────────────────────────────────
function handleUpload(file: File) {
  if (!activeKbId.value) return false
  const kbId = activeKbId.value
  const uf: UploadingFile = { name: file.name, percent: 0 }
  uploadingFiles.value.push(uf)

  const timer = setInterval(() => {
    if (uf.percent < 80) uf.percent += 10
  }, 200)

  uploadDoc(kbId, file)
    .then(doc => {
      clearInterval(timer)
      uf.percent = 100
      docList.value.unshift(doc)
      // Update kb counts
      const kb = kbList.value.find(k => k.id === kbId)
      if (kb) { kb.doc_count++; kb.chunk_count += doc.chunk_count }
      message.success(`${file.name} ${t('knowledge.uploadSuccess')}`)
    })
    .catch(e => {
      clearInterval(timer)
      message.error(`${file.name} ${t('knowledge.uploadFail')}: ${e.message}`)
    })
    .finally(() => {
      setTimeout(() => {
        uploadingFiles.value = uploadingFiles.value.filter(u => u !== uf)
      }, 1500)
    })

  return false // prevent default upload
}

// ── Delete doc ────────────────────────────────────────────────────────────────
async function deleteDoc(docId: string) {
  if (!activeKbId.value) return
  try {
    const doc = docList.value.find(d => d.id === docId)
    await apiDeleteDoc(activeKbId.value, docId)
    docList.value = docList.value.filter(d => d.id !== docId)
    const kb = kbList.value.find(k => k.id === activeKbId.value)
    if (kb && doc) { kb.doc_count = Math.max(0, kb.doc_count - 1); kb.chunk_count = Math.max(0, kb.chunk_count - doc.chunk_count) }
    message.success(t('knowledge.deleteSuccess'))
  } catch (e: any) {
    message.error(e.message)
  }
}

// ── Search ────────────────────────────────────────────────────────────────────
async function doSearch() {
  if (!searchQuery.value.trim() || !activeKbId.value) return
  searching.value = true
  searchDone.value = false
  try {
    searchResults.value = await searchKB(searchQuery.value.trim(), [activeKbId.value])
    searchDone.value = true
  } catch (e: any) {
    message.error(e.message)
  } finally {
    searching.value = false
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function formatDate(iso: string): string {
  return iso ? iso.replace('T', ' ').slice(0, 16) : ''
}
</script>

<style scoped>
.kb-page {
  display: flex;
  height: calc(100vh - 112px);
  gap: 0;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

.kb-sider {
  width: 240px;
  flex-shrink: 0;
  border-right: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  background: #fafafa;
}

.create-btn { margin: 12px; width: calc(100% - 24px); }

.kb-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 8px;
}

.kb-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
  margin-bottom: 2px;
}
.kb-item:hover { background: #f0f5ff; }
.kb-item.active { background: #e6f4ff; }

.kb-item-main { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; }
.kb-icon { color: #1677ff; font-size: 16px; flex-shrink: 0; }
.kb-item-info { min-width: 0; }
.kb-item-name { font-size: 13px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kb-item-meta { font-size: 11px; color: #8c8c8c; }
.kb-delete { color: #bfbfbf; font-size: 13px; flex-shrink: 0; }
.kb-delete:hover { color: #ff4d4f; }

.kb-empty { text-align: center; padding: 32px 16px; color: #bfbfbf; font-size: 13px; }

.kb-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px 20px;
}

.kb-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 12px;
}
.kb-title { font-size: 16px; font-weight: 600; }
.kb-desc { font-size: 13px; color: #8c8c8c; }

.kb-tabs { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
:deep(.ant-tabs-content-holder) { overflow-y: auto; }

.upload-dragger { margin-bottom: 12px; }

.upload-progress-list { margin-bottom: 8px; }
.upload-progress-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 12px;
}
.uf-name { max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.doc-table { margin-top: 4px; }

.search-bar { margin-bottom: 16px; }
:deep(.search-bar .ant-input-suffix) { display: flex; align-items: center; }

.search-results { display: flex; flex-direction: column; gap: 12px; }
.search-result-card {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 12px 16px;
  background: #fafafa;
}
.sr-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.sr-source { font-size: 12px; color: #595959; display: flex; align-items: center; gap: 4px; }
.sr-content { font-size: 13px; color: #1a1a1a; line-height: 1.6; white-space: pre-wrap; }

.kb-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #bfbfbf;
  gap: 12px;
  font-size: 14px;
}
</style>
