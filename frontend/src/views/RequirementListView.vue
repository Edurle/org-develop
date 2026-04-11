<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useRequirementStore } from '@/stores/requirement'
import { useIterationStore } from '@/stores/iteration'
import StatusBadge from '@/components/StatusBadge.vue'
import EmptyState from '@/components/EmptyState.vue'
import Modal from '@/components/Modal.vue'
import GlassButton from '@/components/GlassButton.vue'
import type { Priority, Requirement } from '@/types'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const reqStore = useRequirementStore()
const iterStore = useIterationStore()

const projectId = computed(() => route.params.id as string)

// Filters
const statusFilter = ref('')
const iterationFilter = ref('')
const priorityFilter = ref('')

const statusOptions = [
  'draft', 'spec_writing', 'spec_review', 'spec_locked',
  'spec_rejected', 'in_progress', 'testing', 'done', 'cancelled',
]
const priorityOptions: Priority[] = ['low', 'medium', 'high', 'critical']

// New requirement modal
const showCreateModal = ref(false)
const newTitle = ref('')
const newPriority = ref<Priority>('medium')
const newIterationId = ref('')

// Edit requirement modal
const showEditModal = ref(false)
const editId = ref('')
const editTitle = ref('')
const editPriority = ref<Priority>('medium')

// Delete confirmation
const showDeleteConfirm = ref(false)
const deleteTargetId = ref('')
const deleteTargetTitle = ref('')

const loading = ref(false)
const error = ref('')

const filteredRequirements = computed(() => {
  return reqStore.requirements.filter((r) => {
    if (statusFilter.value && r.status !== statusFilter.value) return false
    if (iterationFilter.value && r.iteration_id !== iterationFilter.value) return false
    if (priorityFilter.value && r.priority !== priorityFilter.value) return false
    return true
  })
})

const priorityColorMap: Record<string, string> = {
  low: 'bg-gradient-to-br from-gray-50 to-gray-100/50 text-gray-600 border-gray-200/60',
  medium: 'bg-gradient-to-br from-blue-50 to-blue-100/50 text-blue-700 border-blue-200/60',
  high: 'bg-gradient-to-br from-orange-50 to-orange-100/50 text-orange-700 border-orange-200/60',
  critical: 'bg-gradient-to-br from-red-50 to-red-100/50 text-red-700 border-red-200/60',
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString()
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    await Promise.all([
      reqStore.fetchList(projectId.value),
      iterStore.fetchList(projectId.value),
    ])
  } catch (e: any) {
    error.value = e?.message || t('requirement.errorLoadFailed')
  } finally {
    loading.value = false
  }
}

function openCreateModal() {
  newTitle.value = ''
  newPriority.value = 'medium'
  newIterationId.value = iterStore.iterations[0]?.id ?? ''
  showCreateModal.value = true
}

async function handleCreate() {
  if (!newTitle.value.trim() || !newIterationId.value) return
  try {
    await reqStore.create(projectId.value, {
      iteration_id: newIterationId.value,
      title: newTitle.value.trim(),
      priority: newPriority.value,
    })
    showCreateModal.value = false
  } catch (e: any) {
    error.value = e?.message || t('requirement.errorCreateFailed')
  }
}

function openEditModal(req: Requirement) {
  editId.value = req.id
  editTitle.value = req.title
  editPriority.value = req.priority
  showEditModal.value = true
}

async function handleEdit() {
  if (!editTitle.value.trim()) return
  try {
    await reqStore.update(editId.value, {
      title: editTitle.value.trim(),
      priority: editPriority.value,
    })
    showEditModal.value = false
  } catch (e: any) {
    error.value = e?.message || t('requirement.errorUpdateFailed')
  }
}

function openDeleteConfirm(req: Requirement) {
  deleteTargetId.value = req.id
  deleteTargetTitle.value = req.title
  showDeleteConfirm.value = true
}

async function handleDelete() {
  try {
    await reqStore.remove(deleteTargetId.value)
    showDeleteConfirm.value = false
  } catch (e: any) {
    error.value = e?.message || t('requirement.errorDeleteFailed')
  }
}

function navigateToReq(reqId: string) {
  router.push(`/projects/${projectId.value}/requirements/${reqId}`)
}

function applyFilters() {
  reqStore.fetchList(projectId.value, {
    iteration_id: iterationFilter.value || undefined,
    status: statusFilter.value || undefined,
  })
}

onMounted(loadData)
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">{{ t('requirement.title') }}</h1>
      <GlassButton size="large" @click="openCreateModal">
        {{ t('requirement.newRequirement') }}
      </GlassButton>
    </div>

    <!-- Error -->
    <div v-if="error" class="mb-4 p-3 rounded-[10px] border border-red-200/60 bg-red-50 text-red-700 text-sm">
      {{ error }}
    </div>

    <!-- Filter bar -->
    <div class="flex items-center gap-3 mb-4">
      <select
        id="filter-status"
        v-model="statusFilter"
        class="select-glass !w-auto"
        @change="applyFilters"
      >
        <option value="">{{ t('requirement.allStatuses') }}</option>
        <option v-for="s in statusOptions" :key="s" :value="s">{{ t('status.' + s) }}</option>
      </select>

      <select
        v-model="iterationFilter"
        class="select-glass !w-auto"
        @change="applyFilters"
      >
        <option value="">{{ t('requirement.allIterations') }}</option>
        <option v-for="iter in iterStore.iterations" :key="iter.id" :value="iter.id">{{ iter.name }}</option>
      </select>

      <select
        v-model="priorityFilter"
        class="select-glass !w-auto"
      >
        <option value="">{{ t('requirement.allPriorities') }}</option>
        <option v-for="p in priorityOptions" :key="p" :value="p">{{ t('priority.' + p) }}</option>
      </select>

      <GlassButton variant="ghost" size="small" @click="statusFilter = ''; iterationFilter = ''; priorityFilter = ''; applyFilters()">
        {{ t('common.clearFilters') }}
      </GlassButton>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="py-12 text-center text-gray-500">{{ t('common.loading') }}</div>

    <!-- Empty state -->
    <EmptyState
      v-else-if="reqStore.requirements.length === 0"
      :title="t('requirement.noRequirements')"
      :description="t('requirement.noRequirementsDesc')"
      :action-label="t('requirement.newRequirement')"
      @action="openCreateModal"
    />

    <EmptyState
      v-else-if="filteredRequirements.length === 0"
      :title="t('requirement.noMatchingRequirements')"
      :description="t('requirement.noMatchingRequirementsDesc')"
    />

    <!-- Table -->
    <div v-else class="glass-card overflow-hidden">
      <table class="w-full text-sm">
        <thead class="border-b border-blue-500/5 bg-blue-500/[0.02]">
          <tr>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">{{ t('common.title') }}</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">{{ t('common.priority') }}</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">{{ t('common.status') }}</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">{{ t('iteration.title') }}</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">{{ t('common.created') }}</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">{{ t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-blue-500/5">
          <tr
            v-for="req in filteredRequirements"
            :key="req.id"
            class="hover:bg-blue-500/[0.01] cursor-pointer transition-colors"
            @click="navigateToReq(req.id)"
          >
            <td class="px-4 py-3 font-medium text-gray-900">{{ req.title }}</td>
            <td class="px-4 py-3">
              <span :class="['badge-base', priorityColorMap[req.priority] ?? 'bg-gradient-to-br from-gray-50 to-gray-100/50 text-gray-600 border-gray-200/60']">
                {{ t('priority.' + req.priority) }}
              </span>
            </td>
            <td class="px-4 py-3">
              <StatusBadge :status="req.status" size="sm" />
            </td>
            <td class="px-4 py-3 text-gray-600">
              {{ iterStore.iterations.find(i => i.id === req.iteration_id)?.name ?? '-' }}
            </td>
            <td class="px-4 py-3 text-gray-500">{{ formatDate(req.created_at) }}</td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <GlassButton
                  variant="ghost"
                  size="small"
                  @click.stop="navigateToReq(req.id)"
                >
                  {{ t('common.view') }}
                </GlassButton>
                <GlassButton
                  variant="ghost"
                  size="small"
                  @click.stop="openEditModal(req)"
                >
                  {{ t('common.edit') }}
                </GlassButton>
                <GlassButton
                  v-if="req.status === 'draft' || req.status === 'cancelled'"
                  variant="danger"
                  size="small"
                  @click.stop="openDeleteConfirm(req)"
                >
                  {{ t('common.delete') }}
                </GlassButton>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Requirement Modal -->
    <Modal :show="showCreateModal" :title="t('requirement.newRequirement')" @close="showCreateModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('common.title') }}</label>
          <input
            id="req-title"
            v-model="newTitle"
            type="text"
            :placeholder="t('requirement.requirementTitle')"
            class="input-glass"
            @keyup.enter="handleCreate"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('common.priority') }}</label>
          <select
            id="req-priority"
            v-model="newPriority"
            class="select-glass"
          >
            <option v-for="p in priorityOptions" :key="p" :value="p">{{ t('priority.' + p) }}</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('iteration.title') }}</label>
          <select
            id="req-iteration"
            v-model="newIterationId"
            class="select-glass"
          >
            <option v-for="iter in iterStore.iterations" :key="iter.id" :value="iter.id">{{ iter.name }}</option>
          </select>
        </div>
      </div>

      <div class="flex justify-end gap-3 mt-6">
        <GlassButton variant="secondary" @click="showCreateModal = false">
          {{ t('common.cancel') }}
        </GlassButton>
        <GlassButton :disabled="!newTitle.trim() || !newIterationId" @click="handleCreate">
          {{ t('common.create') }}
        </GlassButton>
      </div>
    </Modal>

    <!-- Edit Requirement Modal -->
    <Modal :show="showEditModal" :title="t('requirement.editRequirement')" @close="showEditModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('common.title') }}</label>
          <input
            v-model="editTitle"
            type="text"
            :placeholder="t('requirement.requirementTitle')"
            class="input-glass"
            @keyup.enter="handleEdit"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('common.priority') }}</label>
          <select v-model="editPriority" class="select-glass">
            <option v-for="p in priorityOptions" :key="p" :value="p">{{ t('priority.' + p) }}</option>
          </select>
        </div>
      </div>
      <div class="flex justify-end gap-3 mt-6">
        <GlassButton variant="secondary" @click="showEditModal = false">{{ t('common.cancel') }}</GlassButton>
        <GlassButton :disabled="!editTitle.trim()" @click="handleEdit">{{ t('common.save') }}</GlassButton>
      </div>
    </Modal>

    <!-- Delete Confirmation Modal -->
    <Modal :show="showDeleteConfirm" :title="t('requirement.deleteRequirement')" @close="showDeleteConfirm = false">
      <p class="text-sm text-gray-600">
        {{ t('requirement.deleteConfirmText', { title: deleteTargetTitle }) }}
      </p>
      <div class="flex justify-end gap-3 mt-6">
        <GlassButton variant="secondary" @click="showDeleteConfirm = false">{{ t('common.cancel') }}</GlassButton>
        <GlassButton variant="danger" @click="handleDelete">{{ t('common.delete') }}</GlassButton>
      </div>
    </Modal>
  </div>
</template>
