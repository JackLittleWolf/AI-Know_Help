<template>
  <div class="chat-page">
    <!-- Message list — event delegation for code copy buttons -->
    <div class="messages" ref="msgList" @click="handleCopyClick">
      <div v-if="messages.length === 0" class="empty-hint">
        <comment-outlined class="empty-icon" />
        <p>{{ t('chat.empty') }}</p>
      </div>

      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="['msg-row', msg.role]"
      >
        <!-- Assistant avatar (left) -->
        <a-avatar v-if="msg.role === 'assistant'" class="avatar avatar-ai">
          <template #icon><robot-outlined /></template>
        </a-avatar>

        <div class="bubble-wrap" :class="msg.role">
          <template v-if="msg.role === 'user'">
            <div v-if="msg.files && msg.files.length" class="user-file-list">
              <div v-for="f in msg.files" :key="f" class="user-file-bubble">
                <div class="uf-icon">
                  <svg viewBox="0 0 24 24" width="32" height="32" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#71D278"/>
                    <path d="M14 2L20 8H14V2Z" fill="#5AB860"/>
                    <path d="M9 13L7 15L9 17" stroke="#1A1A1A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M15 13L17 15L15 17" stroke="#1A1A1A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M13 12L11 18" stroke="#1A1A1A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
                <div class="uf-info">
                  <span class="uf-name">{{ f }}</span>
                  <span class="uf-type">{{ getFileLabel(f) }}</span>
                </div>
              </div>
            </div>
            <div v-if="msg.content" class="user-text-bubble">
              <div class="user-text">{{ msg.content }}</div>
            </div>
          </template>

          <div v-else class="bubble">
            <div v-if="msg.loading" class="loading-dots">
              <span /><span /><span />
            </div>
            <template v-else>
              <div
                class="markdown-body"
                v-html="renderMarkdown(msg.content)"
              />
              <span v-if="msg.streaming" class="cursor" />
            </template>
          </div>
        </div>

        <!-- User avatar (right) -->
        <a-avatar v-if="msg.role === 'user'" class="avatar avatar-user">
          <template #icon><user-outlined /></template>
        </a-avatar>
      </div>
    </div>

    <!-- Doubao-style input panel -->
    <div class="input-panel">
      <div class="input-card" :class="{ focused: inputFocused }">

        <!-- Attached file cards — Doubao style, inside the card above textarea -->
        <div v-if="attachedFiles.length" class="file-preview-row">
          <div
            v-for="(f, i) in attachedFiles"
            :key="i"
            class="file-card"
          >
            <!-- File type icon block -->
            <div class="file-card-icon" :class="fileIconClass(f)">
              <span class="file-ext-label">{{ fileExt(f) }}</span>
            </div>
            <!-- File info -->
            <div class="file-card-info">
              <span class="file-card-name">{{ f.name }}</span>
              <span class="file-card-size">{{ formatSize(f.size) }}</span>
            </div>
            <!-- Remove -->
            <button class="file-card-remove" @click="removeFile(i)" type="button">
              <close-outlined />
            </button>
          </div>
        </div>

        <!-- Textarea -->
        <textarea
          ref="textareaRef"
          v-model="inputText"
          :placeholder="t('chat.placeholder')"
          class="db-textarea"
          rows="1"
          @keydown.enter.exact="onEnterKey"
          @compositionstart="isComposing = true"
          @compositionend="isComposing = false"
          @focus="inputFocused = true"
          @blur="inputFocused = false"
          @input="autoGrow"
        />

        <!-- Bottom toolbar -->
        <div class="card-toolbar">
          <!-- Left: attach button and agent selector -->
          <div class="toolbar-left">
            <a-upload
              :file-list="[]"
              :before-upload="onBeforeUpload"
              :multiple="true"
              :show-upload-list="false"
              accept=".txt,.md,.pdf,.docx,.png,.jpg,.jpeg,.bmp,.tiff,.webp,.csv"
            >
              <button class="tool-btn" type="button" title="上传文件">
                <paper-clip-outlined />
              </button>
            </a-upload>

            <div class="agent-selector">
              <a-select
                v-model:value="selectedAgentId"
                :options="agentOptions"
                placeholder="选择智能体"
                size="small"
                style="width: 140px"
                :bordered="false"
              />
            </div>
          </div>

          <!-- Right: hint + send/stop -->
          <div class="toolbar-right">
            <span class="key-hint">{{ inputText ? 'Enter 发送 · Shift+Enter 换行' : '' }}</span>

            <!-- Stop -->
            <button
              v-if="streaming"
              class="send-circle stop"
              type="button"
              @click="stopStream"
              title="停止生成"
            >
              <span class="stop-square" />
            </button>

            <!-- Send -->
            <button
              v-else
              class="send-circle"
              :class="{ active: canSend }"
              type="button"
              :disabled="!canSend"
              @click="sendMessage"
              title="发送"
            >
              <send-outlined />
            </button>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js'
import {
  CommentOutlined,
  PaperClipOutlined,
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  CloseOutlined,
} from '@ant-design/icons-vue'
import { getAgents } from '@/api/agents'

const { t } = useI18n()

interface Message {
  role: 'user' | 'assistant'
  content: string
  files?: string[]
  streaming?: boolean
  loading?: boolean
}

const messages = ref<Message[]>([])
const inputText = ref('')
const attachedFiles = ref<File[]>([])
const msgList = ref<HTMLElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const inputFocused = ref(false)
const streaming = ref(false)
let abortController: AbortController | null = null

const selectedAgentId = ref<string>('default')
const agentOptions = ref<{ value: string; label: string }[]>([])

onMounted(async () => {
  try {
    const agents = await getAgents()
    agentOptions.value = agents.map(a => ({
      value: a.id,
      label: a.name
    }))
    if (agents.length > 0 && !agents.find(a => a.id === selectedAgentId.value)) {
      selectedAgentId.value = agents[0].id
    }
  } catch (err) {
    console.error('Failed to load agents:', err)
  }
})

const canSend = computed(() => inputText.value.trim().length > 0 || attachedFiles.value.length > 0)

const isComposing = ref(false)

function onEnterKey(e: KeyboardEvent) {
  if (isComposing.value) return
  e.preventDefault()
  sendMessage()
}

// ── Language label map ───────────────────────────────────────
const LANG_LABELS: Record<string, string> = {
  javascript: 'JavaScript', js: 'JavaScript',
  typescript: 'TypeScript', ts: 'TypeScript',
  python: 'Python', py: 'Python',
  java: 'Java',
  c: 'C',
  cpp: 'C++', 'c++': 'C++',
  csharp: 'C#', cs: 'C#',
  go: 'Go',
  rust: 'Rust',
  swift: 'Swift',
  kotlin: 'Kotlin',
  ruby: 'Ruby', rb: 'Ruby',
  php: 'PHP',
  bash: 'Bash', sh: 'Shell', shell: 'Shell', zsh: 'Zsh',
  sql: 'SQL',
  html: 'HTML',
  css: 'CSS', scss: 'SCSS', sass: 'Sass', less: 'Less',
  json: 'JSON',
  yaml: 'YAML', yml: 'YAML',
  xml: 'XML',
  markdown: 'Markdown', md: 'Markdown',
  r: 'R',
  scala: 'Scala',
  dart: 'Dart',
  vue: 'Vue',
  svelte: 'Svelte',
  jsx: 'JSX', tsx: 'TSX',
  plaintext: '纯文本', text: '纯文本', plain: '纯文本',
}

// Code id → source text, for the copy handler
const codeRegistry = new Map<string, string>()

// Custom renderer: wrap code blocks with header + copy button + syntax highlighting
const renderer = new marked.Renderer()
renderer.code = function ({ text, lang }: { text: string; lang?: string }) {
  const raw = ((lang ?? '').toLowerCase().split(/[\s,{]/)[0]) || ''
  const label = (raw && LANG_LABELS[raw]) || raw || '纯文本'
  const id = Math.random().toString(36).slice(2, 10)
  codeRegistry.set(id, text)

  // Syntax highlight — known language uses targeted highlight, else auto-detect
  let highlighted: string
  try {
    if (raw && hljs.getLanguage(raw)) {
      highlighted = hljs.highlight(text, { language: raw, ignoreIllegals: true }).value
    } else {
      highlighted = hljs.highlightAuto(text).value
    }
  } catch {
    highlighted = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
  }

  return (
    `<div class="md-code-block">` +
      `<div class="md-code-header">` +
        `<span class="md-code-lang">${label}</span>` +
        `<button class="md-copy-btn" data-cid="${id}">` +
          `<svg class="copy-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">` +
            `<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>` +
          `</svg>` +
          `<span class="copy-label">复制代码</span>` +
        `</button>` +
      `</div>` +
      `<pre class="md-pre"><code class="hljs language-${raw}">${highlighted}</code></pre>` +
    `</div>`
  )
}

marked.use({ renderer, breaks: true })

function renderMarkdown(text: string): string {
  const html = marked.parse(text) as string
  return DOMPurify.sanitize(html, {
    ADD_ATTR: ['data-cid'],
    // highlight.js wraps tokens in <span class="hljs-*"> — keep them
    ALLOWED_TAGS: [
      ...DOMPurify.isSupported ? [] : [],
      'span', 'div', 'pre', 'code', 'button', 'svg', 'rect', 'path',
      'p', 'br', 'strong', 'em', 'del', 's',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li',
      'blockquote', 'hr',
      'table', 'thead', 'tbody', 'tr', 'th', 'td',
      'a', 'img',
    ],
    ALLOWED_ATTR: ['class', 'href', 'src', 'alt', 'title', 'target',
                   'viewBox', 'fill', 'stroke', 'stroke-width',
                   'x', 'y', 'width', 'height', 'rx', 'd',
                   'data-cid'],
  })
}

function handleCopyClick(e: MouseEvent) {
  const btn = (e.target as Element).closest<HTMLElement>('.md-copy-btn')
  if (!btn) return
  const code = codeRegistry.get(btn.dataset.cid ?? '') ?? ''
  navigator.clipboard.writeText(code).then(() => {
    const label = btn.querySelector<HTMLElement>('.copy-label')
    if (!label) return
    label.textContent = '已复制 ✓'
    btn.classList.add('copied')
    setTimeout(() => {
      label.textContent = '复制代码'
      btn.classList.remove('copied')
    }, 2000)
  })
}

function autoGrow() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 180) + 'px'
}

function onBeforeUpload(file: File) {
  attachedFiles.value.push(file)
  return false
}

function removeFile(index: number) {
  attachedFiles.value.splice(index, 1)
}

// ── File card helpers ────────────────────────────────────────
function fileExt(f: File): string {
  const dot = f.name.lastIndexOf('.')
  return dot >= 0 ? f.name.slice(dot + 1).toUpperCase() : 'FILE'
}

function getFileNameExt(filename: string): string {
  const parts = filename.split('.')
  return parts.length > 1 ? parts.pop()! : ''
}

function getFileLabel(filename: string): string {
  const ext = getFileNameExt(filename).toLowerCase()
  return LANG_LABELS[ext] || ext.toUpperCase() || '文件'
}

const EXT_CLASS: Record<string, string> = {
  pdf: 'ext-pdf', docx: 'ext-doc', doc: 'ext-doc',
  xlsx: 'ext-xls', xls: 'ext-xls', csv: 'ext-xls',
  pptx: 'ext-ppt', ppt: 'ext-ppt',
  png: 'ext-img', jpg: 'ext-img', jpeg: 'ext-img',
  bmp: 'ext-img', tiff: 'ext-img', webp: 'ext-img',
  txt: 'ext-txt', md: 'ext-txt',
}

function fileIconClass(f: File): string {
  const ext = fileExt(f).toLowerCase()
  return EXT_CLASS[ext] ?? 'ext-default'
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

let rafId = 0
function scheduleScroll() {
  if (rafId) return
  rafId = requestAnimationFrame(() => {
    rafId = 0
    if (msgList.value) msgList.value.scrollTop = msgList.value.scrollHeight
  })
}

async function scrollToBottom() {
  await nextTick()
  if (msgList.value) msgList.value.scrollTop = msgList.value.scrollHeight
}

function stopStream() {
  abortController?.abort()
  streaming.value = false
  const last = messages.value[messages.value.length - 1]
  if (last?.role === 'assistant') {
    last.streaming = false
  }
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text && attachedFiles.value.length === 0) return
  if (streaming.value) return

  messages.value.push({
    role: 'user',
    content: text,
    files: attachedFiles.value.map(f => f.name),
  })

  const filesToSend = [...attachedFiles.value]
  inputText.value = ''
  attachedFiles.value = []
  // Reset textarea height
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }
  await scrollToBottom()

  messages.value.push({ role: 'assistant', content: '', streaming: true, loading: true })
  // Get the reactive proxy (not the raw object) so mutations trigger DOM updates
  const assistantMsg = messages.value[messages.value.length - 1]
  await scrollToBottom()

  const form = new FormData()
  form.append('message', text)
  form.append('session_id', Date.now().toString())
  
  // Extract history (excluding the currently added user message and empty assistant message)
  const historyToSent = messages.value
    .slice(0, -2)
    .map(m => {
      let content = m.content
      if (m.role === 'user' && m.files && m.files.length) {
        content = `[历史附件: ${m.files.join(', ')}]\n\n${content}`
      }
      return { role: m.role, content }
    })
  form.append('history', JSON.stringify(historyToSent))
  if (selectedAgentId.value) {
    form.append('agent_id', selectedAgentId.value)
  }

  filesToSend.forEach(f => form.append('files', f))

  abortController = new AbortController()
  streaming.value = true

  try {
    const resp = await fetch('/api/chat/stream', {
      method: 'POST',
      body: form,
      signal: abortController.signal,
    })

    if (!resp.ok) {
      assistantMsg.content = `请求失败: ${resp.status}`
      assistantMsg.streaming = false
      streaming.value = false
      return
    }

    const reader = resp.body!.getReader()
    const decoder = new TextDecoder()
    let buf = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const lines = buf.split('\n')
      buf = lines.pop() ?? ''
      for (const line of lines) {
        if (!line.startsWith('data:')) continue
        const data = line.slice(5).trim()
        if (data === '[DONE]') {
          assistantMsg.streaming = false
          streaming.value = false
          break
        }
        try {
          const parsed = JSON.parse(data)
          if (parsed.error) {
            assistantMsg.loading = false
            assistantMsg.content += `\n\n**错误:** ${parsed.error}`
          } else if (parsed.text) {
            assistantMsg.loading = false
            assistantMsg.content += parsed.text
            scheduleScroll()
          }
        } catch {
          // ignore malformed lines
        }
      }
    }
  } catch (err: unknown) {
    if ((err as Error).name !== 'AbortError') {
      assistantMsg.loading = false
      assistantMsg.content += '\n\n**连接中断**'
    }
  } finally {
    assistantMsg.loading = false
    assistantMsg.streaming = false
    streaming.value = false
    await scrollToBottom()
  }
}
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 112px);
  background: #f5f7fa;
  border-radius: 8px;
  overflow: hidden;
}

/* Messages area */
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.empty-hint {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #bbb;
  gap: 8px;
  margin-top: 80px;
}

.empty-icon { font-size: 48px; }

/* Message rows — avatar + bubble side by side */
.msg-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.msg-row.user  { flex-direction: row-reverse; }
.msg-row.assistant { flex-direction: row; }

/* Avatars */
.avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  line-height: 36px;
  font-size: 18px;
}
.avatar-ai   { background: #1677ff; color: #fff; }
.avatar-user { background: #52c41a; color: #fff; }

/* Bubble wrapper constrains max-width */
.bubble-wrap {
  display: flex;
  flex-direction: column;
  max-width: calc(72% - 46px);
}
.bubble-wrap.user      { align-items: flex-end; gap: 10px; }
.bubble-wrap.assistant { align-items: flex-start; }

.bubble {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  word-break: break-word;
}

.msg-row.assistant .bubble {
  background: #fff;
  color: #1a1a1a;
  border-top-left-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.user-file-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-end;
}

.user-file-bubble {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f4f4f4;
  border-radius: 16px;
  padding: 12px 16px;
  max-width: 100%;
}

.uf-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
}

.uf-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.uf-name {
  font-size: 15px;
  color: #1a1a1a;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.uf-type {
  font-size: 13px;
  color: #999;
  line-height: 1.4;
  margin-top: 2px;
}

.user-text-bubble {
  background: #f4f4f4;
  color: #1a1a1a;
  border-radius: 16px;
  border-top-right-radius: 4px;
  padding: 12px 16px;
  line-height: 1.6;
  word-break: break-word;
  font-size: 15px;
}

.user-text { white-space: pre-wrap; }

/* Loading dots */
.loading-dots {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 2px 4px;
  height: 24px;
}
.loading-dots span {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #1677ff;
  animation: bounce 1.2s ease-in-out infinite;
}
.loading-dots span:nth-child(1) { animation-delay: 0s; }
.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40%           { transform: translateY(-6px); opacity: 1; }
}

/* Streaming cursor */
.cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: #1677ff;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 0.8s step-end infinite;
}
@keyframes blink { 0%, 100% { opacity: 1 } 50% { opacity: 0 } }

/* Markdown styles */
:deep(.markdown-body) {
  font-size: 14px;
  line-height: 1.7;
}
:deep(.markdown-body h1),
:deep(.markdown-body h2),
:deep(.markdown-body h3) {
  margin: 0.6em 0 0.3em;
  font-weight: 600;
}
:deep(.markdown-body h1) { font-size: 1.3em; }
:deep(.markdown-body h2) { font-size: 1.15em; }
:deep(.markdown-body h3) { font-size: 1.05em; }
:deep(.markdown-body p) { margin: 0.4em 0; }
:deep(.markdown-body ul),
:deep(.markdown-body ol) { padding-left: 1.4em; margin: 0.3em 0; }
:deep(.markdown-body li) { margin: 0.15em 0; }
:deep(.markdown-body code) {
  background: #f0f2f5;
  padding: 0.15em 0.4em;
  border-radius: 3px;
  font-size: 0.88em;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}
:deep(.markdown-body pre) {
  background: #1e1e2e;
  color: #cdd6f4;
  border-radius: 6px;
  padding: 12px 16px;
  overflow-x: auto;
  margin: 0.5em 0;
}
:deep(.markdown-body pre code) {
  background: none;
  padding: 0;
  font-size: 0.86em;
  color: inherit;
}

/* ── Code block with header (language + copy) ── */
:deep(.md-code-block) {
  border-radius: 10px;
  margin: 0.6em 0;
  overflow: hidden;
  border: 1px solid #e4e6ea;
  background: #282c34;
}

:deep(.md-code-header) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 14px;
  background: #f3f4f6;
  border-bottom: 1px solid #e4e6ea;
}

:deep(.md-code-lang) {
  font-size: 12px;
  color: #6b7280;
  font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
  user-select: none;
  font-weight: 500;
  letter-spacing: 0.02em;
}

:deep(.md-copy-btn) {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: transparent;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  font-size: 12px;
  padding: 3px 8px;
  border-radius: 5px;
  transition: background 0.15s, color 0.15s;
  font-family: inherit;
}
:deep(.md-copy-btn:hover) {
  background: #e5e7eb;
  color: #374151;
}
:deep(.md-copy-btn.copied) { color: #16a34a; }

:deep(.copy-icon) {
  width: 13px;
  height: 13px;
  flex-shrink: 0;
}

:deep(.md-pre) {
  margin: 0;
  padding: 0;
  overflow-x: auto;
  line-height: 1.65;
}
/* Let .hljs theme CSS own the code block colors */
:deep(.md-pre .hljs) {
  padding: 14px 16px;
  background: #282c34;
  font-size: 13.5px;
  font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
  border-radius: 0;
}
:deep(.markdown-body blockquote) {
  border-left: 3px solid #d0d0d0;
  margin: 0.4em 0;
  padding: 0.2em 0.8em;
  color: #666;
}
:deep(.markdown-body table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.5em 0;
}
:deep(.markdown-body th),
:deep(.markdown-body td) {
  border: 1px solid #e0e0e0;
  padding: 6px 10px;
}
:deep(.markdown-body th) { background: #f5f7fa; font-weight: 600; }
:deep(.markdown-body a) { color: #1677ff; text-decoration: none; }
:deep(.markdown-body a:hover) { text-decoration: underline; }
:deep(.markdown-body hr) { border: none; border-top: 1px solid #e0e0e0; margin: 0.8em 0; }

/* ── Input panel (Doubao style) ────────────────────────────── */
.input-panel {
  padding: 12px 20px 16px;
  background: #f5f7fa;
}

.input-card {
  background: #fff;
  border-radius: 16px;
  border: 1.5px solid #e4e6ea;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  transition: border-color 0.2s, box-shadow 0.2s;
  overflow: hidden;
}
.input-card.focused {
  border-color: #1677ff;
  box-shadow: 0 2px 16px rgba(22, 119, 255, 0.12);
}

/* File chip row inside card */
/* ── File preview cards (Doubao style) ─────────────────────── */
.file-preview-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 12px 0;
}

.file-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  width: 200px;
  background: #f7f8fa;
  border: 1px solid #e4e6ea;
  border-radius: 10px;
  padding: 8px 10px;
  transition: border-color 0.15s;
}
.file-card:hover { border-color: #c0c4cc; }

/* Coloured ext icon block */
.file-card-icon {
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ext-pdf     { background: #fff1f0; }
.ext-doc     { background: #e6f4ff; }
.ext-xls     { background: #f0fff4; }
.ext-ppt     { background: #fff7e6; }
.ext-img     { background: #f0f5ff; }
.ext-txt     { background: #f5f5f5; }
.ext-default { background: #f0f2f5; }

.file-ext-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.01em;
  line-height: 1;
}
.ext-pdf     .file-ext-label { color: #cf1322; }
.ext-doc     .file-ext-label { color: #096dd9; }
.ext-xls     .file-ext-label { color: #237804; }
.ext-ppt     .file-ext-label { color: #d46b08; }
.ext-img     .file-ext-label { color: #531dab; }
.ext-txt     .file-ext-label { color: #595959; }
.ext-default .file-ext-label { color: #8c8fa3; }

.file-card-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.file-card-name {
  font-size: 12px;
  font-weight: 500;
  color: #1a1a1a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.file-card-size {
  font-size: 11px;
  color: #9ca3af;
}

.file-card-remove {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #6b7280;
  color: #fff;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  opacity: 0;
  transition: opacity 0.15s, background 0.15s;
  padding: 0;
  line-height: 1;
}
.file-card:hover .file-card-remove { opacity: 1; }
.file-card-remove:hover { background: #374151; }

/* Textarea — no border, no outline, grows with content */
.db-textarea {
  display: block;
  width: 100%;
  min-height: 44px;
  max-height: 180px;
  padding: 12px 14px 6px;
  font-size: 14px;
  line-height: 1.65;
  color: #1a1a1a;
  background: transparent;
  border: none;
  outline: none;
  resize: none;
  font-family: inherit;
  box-sizing: border-box;
  overflow-y: auto;
}
.db-textarea::placeholder { color: #b0b5be; }

/* Bottom toolbar */
.card-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 10px 10px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Icon buttons in toolbar */
.tool-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 8px;
  font-size: 16px;
  color: #8c8fa3;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  padding: 0;
}
.tool-btn:hover {
  background: #f0f2f5;
  color: #1677ff;
}

/* Key hint */
.key-hint {
  font-size: 11px;
  color: #c0c4cc;
  padding-right: 4px;
  user-select: none;
}

/* Send / Stop circle button */
.send-circle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 50%;
  font-size: 15px;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s;
  padding: 0;
  background: #e4e6ea;
  color: #a0a4b0;
}
.send-circle.active {
  background: #1677ff;
  color: #fff;
}
.send-circle.active:hover {
  background: #0958d9;
  transform: scale(1.06);
}
.send-circle:disabled {
  cursor: default;
}
.send-circle.stop {
  background: #1a1a1a;
  color: #fff;
}
.send-circle.stop:hover {
  background: #333;
  transform: scale(1.06);
}

/* Stop icon — solid square */
.stop-square {
  display: inline-block;
  width: 11px;
  height: 11px;
  background: #fff;
  border-radius: 2px;
}
</style>
