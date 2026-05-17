<template>
  <div class="agents-page">
    <div class="header-actions">
      <a-button type="primary" @click="openAddModal">
        <template #icon><plus-outlined /></template>
        {{ t('agents.add') }}
      </a-button>
    </div>

    <a-table :dataSource="agents" :columns="columns" rowKey="id" :loading="loading" bordered>
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'icon'">
          <a-avatar v-if="isUploadedIcon(record.icon)" size="small" :src="record.icon" />
          <a-avatar v-else size="small">
            <template #icon><component :is="getAgentIcon(record.icon)" /></template>
          </a-avatar>
        </template>
        <template v-if="column.key === 'action'">
          <div class="action-btns">
            <a-button type="link" size="small" @click="openEditModal(record)">
              {{ t('agents.edit') }}
            </a-button>
            <a-popconfirm
              :title="t('agents.confirm_delete')"
              @confirm="handleDelete(record.id)"
              :disabled="isBuiltInAgent(record.id)"
            >
              <a-button type="link" danger size="small" :disabled="isBuiltInAgent(record.id)">
                {{ t('agents.delete') }}
              </a-button>
            </a-popconfirm>
          </div>
        </template>
      </template>
    </a-table>

    <a-modal
      v-model:open="modalVisible"
      :title="editingId ? t('agents.edit') : t('agents.add')"
      @ok="handleSave"
      @cancel="modalVisible = false"
      :confirmLoading="saving"
    >
      <a-form :model="form" layout="vertical">
        <a-form-item :label="t('agents.name')" required>
          <a-input v-model:value="form.name" />
        </a-form-item>
        <a-form-item :label="t('agents.description')">
          <a-input v-model:value="form.description" />
        </a-form-item>
        <a-form-item :label="t('agents.icon')">
          <div class="icon-picker">
            <div class="icon-preview">
              <a-avatar v-if="isUploadedIcon(form.icon)" :src="form.icon" :size="40" />
              <a-avatar v-else :size="40">
                <template #icon><component :is="getAgentIcon(form.icon)" /></template>
              </a-avatar>
            </div>
            <a-select
              :value="isUploadedIcon(form.icon) ? undefined : form.icon"
              allow-clear
              class="system-icon-select"
              :placeholder="t('agents.icon_placeholder')"
              @change="selectSystemIcon"
            >
              <a-select-option v-for="option in iconOptions" :key="option.value" :value="option.value">
                <span class="icon-option">
                  <component :is="getAgentIcon(option.value)" />
                  <span>{{ option.label }}</span>
                </span>
              </a-select-option>
            </a-select>
            <a-upload
              :before-upload="beforeIconUpload"
              :show-upload-list="false"
              accept="image/png,image/jpeg,image/webp,image/gif,image/svg+xml"
            >
              <a-button>
                <template #icon><upload-outlined /></template>
                {{ t('agents.icon_upload') }}
              </a-button>
            </a-upload>
          </div>
        </a-form-item>
        <a-form-item :label="t('agents.system_prompt')" required>
          <a-textarea v-model:value="form.system_prompt" :rows="6" />
        </a-form-item>
        <a-form-item :label="t('agents.skills')">
          <a-select
            v-model:value="form.skills"
            mode="multiple"
            allow-clear
            style="width: 100%"
            :placeholder="t('agents.skills_placeholder')"
          >
            <a-select-option v-for="skill in skills" :key="skill.id" :value="skill.id">
              {{ skill.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('agents.kb_ids')">
          <a-select
            v-model:value="form.kb_ids"
            mode="multiple"
            allow-clear
            style="width: 100%"
            :placeholder="t('agents.kb_ids_placeholder')"
          >
            <a-select-option v-for="kb in kbList" :key="kb.id" :value="kb.id">
              {{ kb.name }}
              <span style="color:#8c8c8c;font-size:11px;margin-left:4px">
                ({{ kb.doc_count }} 文档)
              </span>
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item :label="t('agents.nodes')">
          <div class="node-list">
            <div v-for="(node, index) in form.nodes" :key="`${index}-${node.id}`" class="node-card">
              <div class="node-card-header">
                <span>{{ t('agents.node') }} {{ index + 1 }}</span>
                <a-button type="link" danger size="small" @click="removeNode(index)">
                  {{ t('agents.remove_node') }}
                </a-button>
              </div>
              <a-input
                v-model:value="node.name"
                :placeholder="t('agents.node_name_placeholder')"
                class="node-field"
              />
              <a-input
                v-model:value="node.id"
                :placeholder="t('agents.node_id_placeholder')"
                class="node-field"
              />
              <a-textarea
                v-model:value="node.description"
                :rows="2"
                :placeholder="t('agents.node_description_placeholder')"
              />
            </div>
            <a-button block @click="addNode">
              {{ t('agents.add_node') }}
            </a-button>
          </div>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import type { Component } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import {
  ApiOutlined,
  BulbOutlined,
  PlusOutlined,
  RobotOutlined,
  ScanOutlined,
  ThunderboltOutlined,
  UploadOutlined,
} from '@ant-design/icons-vue'
import { getAgents, createAgent, updateAgent, deleteAgent, type Agent, type AgentNode } from '@/api/agents'
import { listKBs } from '@/api/knowledge'
import http from '@/utils/http'
import type { KnowledgeBase, SkillMeta } from '@/types'

const { t } = useI18n()

const loading = ref(false)
const agents = ref<Agent[]>([])
const skills = ref<SkillMeta[]>([])
const kbList = ref<KnowledgeBase[]>([])
const DEFAULT_AGENT_ICON = 'robot'

const agentIconMap: Record<string, Component> = {
  robot: RobotOutlined,
  code: ApiOutlined,
  prompt: BulbOutlined,
  action: ThunderboltOutlined,
  ocr: ScanOutlined,
}

const iconOptions = computed(() => [
  { value: 'robot', label: t('agents.icon_robot') },
  { value: 'code', label: t('agents.icon_code') },
  { value: 'prompt', label: t('agents.icon_prompt') },
  { value: 'action', label: t('agents.icon_action') },
  { value: 'ocr', label: t('agents.icon_ocr') },
])

const columns = computed(() => [
  { title: t('agents.icon'), key: 'icon', width: 96, align: 'center' },
  { title: t('agents.name'), dataIndex: 'name', key: 'name', width: 200 },
  { title: t('agents.description'), dataIndex: 'description', key: 'description' },
  { title: t('agents.nodes_count'), key: 'nodes', width: 110, customRender: ({ record }: { record: Agent }) => record.nodes?.length ?? 0 },
  { title: t('agents.action'), key: 'action', width: 150, align: 'center' },
])

const loadData = async () => {
  loading.value = true
  try {
    const [loadedAgents, loadedSkills, loadedKBs] = await Promise.all([
      getAgents(),
      http.get<unknown, SkillMeta[]>('/skills'),
      listKBs(),
    ])
    agents.value = loadedAgents
    skills.value = loadedSkills
    kbList.value = loadedKBs
  } catch (err) {
    message.error('Failed to load agents')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})

const modalVisible = ref(false)
const saving = ref(false)
const editingId = ref<string | null>(null)
const form = ref<Omit<Agent, 'id'> & { id?: string }>({
  name: '',
  description: '',
  system_prompt: '',
  icon: DEFAULT_AGENT_ICON,
  skills: [],
  kb_ids: [],
  nodes: [],
})

const createEmptyNode = (): AgentNode => ({
  id: '',
  name: '',
  description: '',
})

const openAddModal = () => {
  editingId.value = null
  form.value = { name: '', description: '', system_prompt: '', icon: DEFAULT_AGENT_ICON, skills: [], kb_ids: [], nodes: [] }
  modalVisible.value = true
}

const openEditModal = (record: Agent) => {
  editingId.value = record.id
  form.value = {
    ...record,
    icon: record.icon || DEFAULT_AGENT_ICON,
    skills: record.skills || [],
    kb_ids: record.kb_ids || [],
    nodes: (record.nodes || []).map(node => ({ ...node })),
  }
  modalVisible.value = true
}

const isBuiltInAgent = (id: string) => ['default', 'prompt-engineer', 'code-generator', 'file-processor'].includes(id)

const isUploadedIcon = (icon?: string) => Boolean(icon?.startsWith('data:image/'))

const getAgentIcon = (icon?: string) => agentIconMap[icon || DEFAULT_AGENT_ICON] || RobotOutlined

const selectSystemIcon = (icon?: string) => {
  form.value.icon = icon || DEFAULT_AGENT_ICON
}

const beforeIconUpload = (file: File): boolean => {
  if (!file.type.startsWith('image/')) {
    message.warning(t('agents.icon_upload_image_only'))
    return false
  }
  if (file.size > 1024 * 1024) {
    message.warning(t('agents.icon_upload_too_large'))
    return false
  }

  const reader = new FileReader()
  reader.onload = () => {
    if (typeof reader.result === 'string') {
      form.value.icon = reader.result
    }
  }
  reader.readAsDataURL(file)
  return false
}

const addNode = () => {
  if (!form.value.nodes) form.value.nodes = []
  form.value.nodes.push(createEmptyNode())
}

const removeNode = (index: number) => {
  form.value.nodes?.splice(index, 1)
}

const slugifyNodeId = (value: string) => value
  .trim()
  .toLowerCase()
  .replace(/[^a-z0-9]+/g, '-')
  .replace(/^-+|-+$/g, '')

const normalizeNodes = (nodes: AgentNode[] = []): AgentNode[] => {
  const normalized: AgentNode[] = []
  nodes.forEach((node, index) => {
    const name = node.name.trim()
    if (!name) return
    const description = (node.description || '').trim()
    const id = slugifyNodeId(node.id || name || `node-${index + 1}`) || `node-${index + 1}`
    normalized.push({ id, name, description })
  })
  return normalized
}

const handleSave = async () => {
  if (!form.value.name || !form.value.system_prompt) {
    message.warning('Name and System Prompt are required')
    return
  }
  saving.value = true
  const icon = form.value.icon || DEFAULT_AGENT_ICON
  const nodes = normalizeNodes(form.value.nodes || [])
  try {
    if (editingId.value) {
      await updateAgent({ ...form.value, id: editingId.value, icon, nodes } as Agent)
      message.success(t('agents.update_success'))
    } else {
      // Create new without sending id field
      const newAgentData = {
        name: form.value.name,
        description: form.value.description,
        system_prompt: form.value.system_prompt,
        icon,
        skills: form.value.skills || [],
        nodes,
      }
      await createAgent(newAgentData)
      message.success(t('agents.create_success'))
    }
    modalVisible.value = false
    loadData()
  } catch (err) {
    message.error('Save failed')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id: string) => {
  try {
    await deleteAgent(id)
    message.success(t('agents.delete_success'))
    loadData()
  } catch (err) {
    message.error('Delete failed')
  }
}
</script>

<style scoped>
.agents-page {
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  min-height: calc(100vh - 112px);
}
.header-actions {
  margin-bottom: 16px;
  display: flex;
  justify-content: flex-end;
}
.action-btns {
  display: flex;
  gap: 8px;
  justify-content: center;
}

:deep(.ant-table-thead > tr > th) {
  white-space: nowrap;
}

.icon-option {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.icon-picker {
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon-preview {
  flex: 0 0 auto;
}

.system-icon-select {
  flex: 1;
  min-width: 0;
}

.node-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.node-card {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px;
  background: #fafafa;
}

.node-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  font-weight: 600;
}

.node-field {
  margin-bottom: 8px;
}
</style>
