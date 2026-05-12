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
          <a-avatar size="small">
            <template #icon><robot-outlined /></template>
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
              :disabled="record.id === 'default'"
            >
              <a-button type="link" danger size="small" :disabled="record.id === 'default'">
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
        <a-form-item :label="t('agents.system_prompt')" required>
          <a-textarea v-model:value="form.system_prompt" :rows="6" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { PlusOutlined, RobotOutlined } from '@ant-design/icons-vue'
import { getAgents, createAgent, updateAgent, deleteAgent, type Agent } from '@/api/agents'

const { t } = useI18n()

const loading = ref(false)
const agents = ref<Agent[]>([])

const columns = [
  { title: t('agents.icon'), key: 'icon', width: 80, align: 'center' },
  { title: t('agents.name'), dataIndex: 'name', key: 'name', width: 200 },
  { title: t('agents.description'), dataIndex: 'description', key: 'description' },
  { title: t('agents.action'), key: 'action', width: 150, align: 'center' },
]

const loadData = async () => {
  loading.value = true
  try {
    agents.value = await getAgents()
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
  icon: 'robot'
})

const openAddModal = () => {
  editingId.value = null
  form.value = { name: '', description: '', system_prompt: '', icon: 'robot' }
  modalVisible.value = true
}

const openEditModal = (record: Agent) => {
  editingId.value = record.id
  form.value = { ...record }
  modalVisible.value = true
}

const handleSave = async () => {
  if (!form.value.name || !form.value.system_prompt) {
    message.warning('Name and System Prompt are required')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await updateAgent({ ...form.value, id: editingId.value } as Agent)
      message.success(t('agents.update_success'))
    } else {
      // Create new without sending id field
      const newAgentData = {
        name: form.value.name,
        description: form.value.description,
        system_prompt: form.value.system_prompt,
        icon: form.value.icon
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
</style>
