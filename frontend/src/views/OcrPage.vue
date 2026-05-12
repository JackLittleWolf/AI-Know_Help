<template>
  <div class="ocr-page">
    <SplitPane :default-left-width="420">
      <template #left>
        <div class="panel">
          <a-card :title="t('ocr.upload.title')" :bordered="false">
            <!-- Upload area -->
            <a-upload-dragger
              v-model:file-list="fileList"
              :before-upload="beforeUpload"
              :custom-request="handleUpload"
              :show-upload-list="false"
              accept=".jpg,.jpeg,.png,.bmp,.tiff,.tif,.pdf,.docx,.xlsx,.pptx"
              class="upload-dragger"
            >
              <p class="ant-upload-drag-icon">
                <inbox-outlined />
              </p>
              <p class="ant-upload-text">{{ t('ocr.upload.drag') }}</p>
              <p class="ant-upload-hint">{{ t('ocr.upload.hint') }}</p>
            </a-upload-dragger>

            <!-- File info -->
            <div v-if="currentFile" class="file-info">
              <div class="file-meta">
                <file-outlined class="file-icon" />
                <span class="file-name">{{ currentFile.name }}</span>
                <span class="file-size">{{ formatSize(currentFile.size) }}</span>
              </div>
              <a-progress
                v-if="uploading"
                :percent="uploadProgress"
                status="active"
                class="upload-progress"
              />
            </div>

            <!-- File preview -->
            <div v-if="previewSrc || (ocrData && ocrData.content[0]?.preview_b64)" class="file-preview">
              <a-divider>{{ t('ocr.upload.preview') }}</a-divider>

              <!-- Toolbar -->
              <div class="preview-toolbar">
                <!-- Page nav (multi-page only) -->
                <template v-if="totalPreviewPages > 1">
                  <a-button size="small" :disabled="previewPage <= 1" @click="previewPage--">
                    <template #icon><left-outlined /></template>
                  </a-button>
                  <span class="page-indicator">{{ previewPage }} / {{ totalPreviewPages }}</span>
                  <a-button size="small" :disabled="previewPage >= totalPreviewPages" @click="previewPage++">
                    <template #icon><right-outlined /></template>
                  </a-button>
                  <a-divider type="vertical" />
                </template>
                <!-- Zoom -->
                <a-button size="small" :disabled="zoom <= 0.25" @click="zoom = +(zoom - 0.25).toFixed(2)">
                  <template #icon><zoom-out-outlined /></template>
                </a-button>
                <span class="zoom-label">{{ Math.round(zoom * 100) }}%</span>
                <a-button size="small" :disabled="zoom >= 3" @click="zoom = +(zoom + 0.25).toFixed(2)">
                  <template #icon><zoom-in-outlined /></template>
                </a-button>
                <a-button size="small" @click="zoom = 1">
                  <template #icon><fullscreen-exit-outlined /></template>
                </a-button>
              </div>

              <!-- Image viewport -->
              <div class="preview-viewport">
                <img
                  v-if="currentPreviewSrc"
                  :src="currentPreviewSrc"
                  alt="预览"
                  class="preview-image"
                  :style="{ width: zoom * 100 + '%' }"
                />
                <div v-else class="preview-placeholder">
                  <file-text-outlined />
                  <span>{{ currentFile?.name }}</span>
                </div>
              </div>
            </div>
          </a-card>
        </div>
      </template>

      <template #right>
        <div class="panel">
          <a-card :bordered="false">
            <template #title>
              <span>{{ t('ocr.result.title') }}</span>
              <span v-if="ocrData" class="result-meta">
                {{ t('ocr.result.pages', { n: ocrData.total_pages }) }}
              </span>
            </template>
            <template #extra>
              <a-space v-if="ocrData">
                <a-button size="small" @click="copyAll">
                  <template #icon><copy-outlined /></template>
                  {{ t('ocr.result.copyAll') }}
                </a-button>
                <a-dropdown>
                  <a-button size="small">
                    <template #icon><download-outlined /></template>
                    {{ t('ocr.result.export') }}
                  </a-button>
                  <template #overlay>
                    <a-menu>
                      <a-menu-item @click="exportAs('txt')">{{ t('ocr.result.exportTxt') }}</a-menu-item>
                      <a-menu-item @click="exportAs('json')">{{ t('ocr.result.exportJson') }}</a-menu-item>
                      <a-menu-item @click="exportAs('md')">{{ t('ocr.result.exportMd') }}</a-menu-item>
                    </a-menu>
                  </template>
                </a-dropdown>
              </a-space>
            </template>

            <!-- Loading state -->
            <div v-if="processing" class="processing-state">
              <a-spin size="large" />
              <p class="processing-text">{{ t('ocr.result.processing') }}</p>
            </div>

            <!-- Empty state -->
            <a-empty v-else-if="!ocrData" :description="t('ocr.result.empty')" />

            <!-- Results -->
            <div v-else class="results">
              <div
                v-for="page in ocrData.content"
                :key="page.page"
                class="page-section"
              >
                <a-divider v-if="ocrData.total_pages > 1" orientation="left">
                  {{ t('ocr.result.page', { n: page.page }) }}
                </a-divider>
                <div
                  v-for="(block, idx) in page.text_blocks"
                  :key="idx"
                  class="block"
                >
                  <div class="block-label">{{ block.label }}</div>
                  <!-- Text block -->
                  <div v-if="block.type === 'text'" class="text-block">
                    <pre class="text-content">{{ block.value }}</pre>
                  </div>
                  <!-- Table block -->
                  <div v-else-if="block.type === 'table'" class="table-block">
                    <a-table
                      :data-source="block.value as Record<string, unknown>[]"
                      :columns="getColumns(block.value as Record<string, unknown>[])"
                      :pagination="{ pageSize: 10, showSizeChanger: true }"
                      size="small"
                      bordered
                      :scroll="{ x: 'max-content' }"
                    />
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
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import type { UploadFile } from 'ant-design-vue'
import {
  InboxOutlined,
  FileOutlined,
  FileTextOutlined,
  CopyOutlined,
  DownloadOutlined,
  LeftOutlined,
  RightOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  FullscreenExitOutlined,
} from '@ant-design/icons-vue'
import SplitPane from '@/components/SplitPane.vue'
import http from '@/utils/http'
import type { OCRData, OCRResponse } from '@/types'

const { t } = useI18n()

const fileList = ref<UploadFile[]>([])
const currentFile = ref<File | null>(null)
const previewSrc = ref<string | null>(null)   // ObjectURL for images
const uploading = ref(false)
const uploadProgress = ref(0)
const processing = ref(false)
const ocrData = ref<OCRData | null>(null)

// preview state
const previewPage = ref(1)
const zoom = ref(1)

const isImage = computed(() => /\.(jpg|jpeg|png|bmp|tiff|tif)$/i.test(currentFile.value?.name ?? ''))

const totalPreviewPages = computed(() => ocrData.value?.total_pages ?? (previewSrc.value ? 1 : 0))

const currentPreviewSrc = computed(() => {
  // After OCR: use per-page base64 thumbnails
  if (ocrData.value) {
    const page = ocrData.value.content.find((p) => p.page === previewPage.value)
    if (page?.preview_b64) return `data:image/png;base64,${page.preview_b64}`
  }
  // Before OCR: image ObjectURL (single page)
  return previewSrc.value
})

// Reset page when new file loaded
watch(ocrData, () => { previewPage.value = 1 })

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function beforeUpload(file: File): boolean {
  currentFile.value = file
  ocrData.value = null
  previewPage.value = 1
  zoom.value = 1
  if (previewSrc.value) { URL.revokeObjectURL(previewSrc.value); previewSrc.value = null }
  if (isImage.value) previewSrc.value = URL.createObjectURL(file)
  return true
}

async function handleUpload({ file }: { file: File }) {
  uploading.value = true
  uploadProgress.value = 0
  processing.value = false

  const formData = new FormData()
  formData.append('file', file)

  try {
    // Simulate upload progress
    const timer = setInterval(() => {
      if (uploadProgress.value < 90) uploadProgress.value += 10
    }, 100)

    const res = await http.post<unknown, OCRResponse>('/ocr/process', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    clearInterval(timer)
    uploadProgress.value = 100
    uploading.value = false
    processing.value = true

    // Small delay to show processing state
    await new Promise((r) => setTimeout(r, 300))
    processing.value = false

    if (res.code === 200 && res.data) {
      ocrData.value = res.data
      message.success(t('ocr.result.success'))
    } else {
      message.error(res.message || '识别失败')
    }
  } catch (err: unknown) {
    uploading.value = false
    processing.value = false
    message.error(err instanceof Error ? err.message : t('ocr.result.uploadFail'))
  }
}

function getColumns(rows: Record<string, unknown>[]) {
  if (!rows.length) return []
  return Object.keys(rows[0]).map((key) => ({
    title: key,
    dataIndex: key,
    key,
    ellipsis: true,
  }))
}

function getAllText(): string {
  if (!ocrData.value) return ''
  return ocrData.value.content
    .flatMap((page) =>
      page.text_blocks.map((b) =>
        typeof b.value === 'string'
          ? `[${b.label}]\n${b.value}`
          : `[${b.label}]\n${JSON.stringify(b.value, null, 2)}`
      )
    )
    .join('\n\n')
}

async function copyAll() {
  await navigator.clipboard.writeText(getAllText())
      message.success(t('ocr.result.copied'))
}

function toMarkdown(): string {
  if (!ocrData.value) return ''
  const stem = ocrData.value.filename.replace(/\.[^.]+$/, '')
  const lines: string[] = [`# ${stem}`, '']

  for (const page of ocrData.value.content) {
    if (ocrData.value.total_pages > 1) {
      lines.push(`## 第 ${page.page} 页`, '')
    }
    for (const block of page.text_blocks) {
      lines.push(`### ${block.label}`, '')
      if (typeof block.value === 'string') {
        lines.push(block.value, '')
      } else {
        const rows = block.value as Record<string, unknown>[]
        if (rows.length) {
          const headers = Object.keys(rows[0])
          lines.push('| ' + headers.join(' | ') + ' |')
          lines.push('| ' + headers.map(() => '---').join(' | ') + ' |')
          for (const row of rows) {
            lines.push('| ' + headers.map((h) => String(row[h] ?? '')).join(' | ') + ' |')
          }
          lines.push('')
        }
      }
    }
  }
  return lines.join('\n')
}

function exportAs(format: 'txt' | 'json' | 'md') {
  if (!ocrData.value) return
  let content: string
  let mime: string
  let ext: string

  if (format === 'json') {
    content = JSON.stringify(ocrData.value, null, 2)
    mime = 'application/json'
    ext = 'json'
  } else if (format === 'md') {
    content = toMarkdown()
    mime = 'text/markdown'
    ext = 'md'
  } else {
    content = getAllText()
    mime = 'text/plain'
    ext = 'txt'
  }

  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ocr_result.${ext}`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.ocr-page {
  height: calc(100vh - 112px);
}

.panel {
  padding: 8px;
  height: 100%;
}

.upload-dragger {
  margin-bottom: 16px;
}

.file-info {
  margin-top: 12px;
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.file-icon {
  color: #1677ff;
  font-size: 18px;
}

.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.file-size {
  color: #8c8c8c;
  font-size: 12px;
  white-space: nowrap;
}

.upload-progress {
  margin-top: 4px;
}

.file-preview {
  margin-top: 8px;
}

.preview-toolbar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-bottom: none;
  border-radius: 4px 4px 0 0;
}

.page-indicator,
.zoom-label {
  font-size: 12px;
  color: #595959;
  min-width: 48px;
  text-align: center;
}

.preview-viewport {
  overflow: auto;
  max-height: 360px;
  border: 1px solid #f0f0f0;
  border-radius: 0 0 4px 4px;
  background: #f5f5f5;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 8px;
}

.preview-image {
  display: block;
  min-width: 60px;
  border-radius: 2px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.12);
  transition: width 0.15s ease;
}

.preview-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px;
  background: #fafafa;
  border-radius: 4px;
  color: #8c8c8c;
  font-size: 32px;
}

.preview-placeholder span {
  font-size: 14px;
}

.processing-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 0;
  gap: 16px;
}

.processing-text {
  color: #8c8c8c;
  margin: 0;
}

.result-meta {
  margin-left: 8px;
  font-size: 12px;
  color: #8c8c8c;
  font-weight: normal;
}

.page-section {
  margin-bottom: 16px;
}

.block {
  margin-bottom: 16px;
}

.block-label {
  font-weight: 600;
  color: #1677ff;
  margin-bottom: 6px;
  font-size: 13px;
}

.text-block {
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  padding: 12px;
}

.text-content {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.6;
}

.table-block {
  overflow-x: auto;
}
</style>
