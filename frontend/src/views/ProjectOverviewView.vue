<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useProjectStore } from '@/stores/project'
import { useIterationStore } from '@/stores/iteration'
import { useRequirementStore } from '@/stores/requirement'
import StatusBadge from '@/components/StatusBadge.vue'
import Modal from '@/components/Modal.vue'

const { t } = useI18n()
const route = useRoute()
const projectId = route.params.id as string

const projectStore = useProjectStore()
const iterationStore = useIterationStore()
const requirementStore = useRequirementStore()

const loading = ref(true)
const error = ref('')

// Inline editing state
const editingName = ref(false)
const editingDesc = ref(false)
const editName = ref('')
const editDesc = ref('')
const saving = ref(false)

// Create iteration state
const showCreateModal = ref(false)
const newIterName = ref('')
const newStartDate = ref('')
const newEndDate = ref('')

const project = computed(() => projectStore.currentProject)
const activeIterations = computed(() =>
  iterationStore.iterations.filter((i) => i.status === 'planning' || i.status === 'active')
)
const recentRequirements = computed(() =>
  requirementStore.requirements.slice(0, 5)
)

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString()
}

function startEditName() {
  if (!project.value) return
  editName.value = project.value.name
  editingName.value = true
}

function startEditDesc() {
  if (!project.value) return
  editDesc.value = project.value.description || ''
  editingDesc.value = true
}

async function saveName() {
  if (!project.value || !editName.value.trim()) return
  saving.value = true
  try {
    await projectStore.update(project.value.id, { name: editName.value.trim() })
    editingName.value = false
  } catch (err: any) {
    error.value = err?.response?.data?.detail || t('project.failedUpdateName')
  } finally {
    saving.value = false
  }
}

async function saveDesc() {
  if (!project.value) return
  saving.value = true
  try {
    await projectStore.update(project.value.id, { description: editDesc.value })
    editingDesc.value = false
  } catch (err: any) {
    error.value = err?.response?.data?.detail || t('project.failedUpdateDesc')
  } finally {
    saving.value = false
  }
}

function openCreateIterModal() {
  newIterName.value = ''
  newStartDate.value = ''
  newEndDate.value = ''
  showCreateModal.value = true
}

async function handleCreateIter() {
  if (!newIterName.value.trim()) return
  try {
    await iterationStore.create(projectId, {
      name: newIterName.value.trim(),
      start_date: newStartDate.value || undefined,
      end_date: newEndDate.value || undefined,
    })
    showCreateModal.value = false
  } catch (err: any) {
    error.value = err?.response?.data?.detail || t('iteration.errorCreateFailed')
  }
}

onMounted(async () => {
  error.value = ''
  loading.value = true
  try {
    await Promise.all([
      projectStore.fetchOne(projectId),
      iterationStore.fetchList(projectId),
      requirementStore.fetchList(projectId),
    ])
  } catch (err: any) {
    error.value = err?.response?.data?.detail || t('project.failedLoadProject')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-6">
    <!-- Error banner -->
    <div v-if="error" class="p-3 bg-red-50 border border-red-200/60 rounded-[10px] text-sm text-red-700">
      {{ error }}
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="space-y-6">
      <div class="animate-pulse">
        <div class="h-7 bg-gray-200/50 rounded w-1/3 mb-2" />
        <div class="h-4 bg-gray-100/50 rounded w-2/3" />
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div v-for="i in 3" :key="i" class="glass-card p-5 animate-pulse">
          <div class="h-4 bg-gray-200/50 rounded w-20 mb-3" />
          <div class="h-6 bg-gray-100/50 rounded w-12" />
        </div>
      </div>
    </div>

    <template v-else-if="project">
      <!-- Project header -->
      <div>
        <div class="flex items-center gap-2">
          <h1 v-if="!editingName" class="text-2xl font-bold text-gray-900">
            {{ project.name }}
          </h1>
          <div v-else class="flex items-center gap-2">
            <input
              v-model="editName"
              type="text"
              class="input-glass !py-1 !text-lg !font-bold"
              @keyup.enter="saveName"
              @keyup.escape="editingName = false"
            />
            <button
              class="btn-primary !px-2 !py-1 text-xs"
              :disabled="saving"
              @click="saveName"
            >
              {{ t('common.save') }}
            </button>
            <button
              class="btn-secondary !px-2 !py-1 text-xs"
              @click="editingName = false"
            >
              {{ t('common.cancel') }}
            </button>
          </div>
          <button
            v-if="!editingName"
            class="btn-secondary !p-1.5 !rounded-full"
            :title="t('common.edit')"
            @click="startEditName"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
          </button>
        </div>

        <div class="mt-2 flex items-center gap-2">
          <p v-if="!editingDesc" class="text-sm text-gray-500">
            {{ project.description || t('project.noDesc') }}
          </p>
          <div v-else class="flex items-start gap-2 flex-1">
            <textarea
              v-model="editDesc"
              rows="2"
              class="input-glass flex-1 resize-none !text-sm"
              @keyup.escape="editingDesc = false"
            />
            <button
              class="btn-primary !px-2 !py-1 text-xs"
              :disabled="saving"
              @click="saveDesc"
            >
              {{ t('common.save') }}
            </button>
            <button
              class="btn-secondary !px-2 !py-1 text-xs"
              @click="editingDesc = false"
            >
              {{ t('common.cancel') }}
            </button>
          </div>
          <button
            v-if="!editingDesc"
            class="btn-secondary !p-1.5 !rounded-full"
            :title="t('common.edit')"
            @click="startEditDesc"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Quick stats -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="glass-card p-5">
          <span class="text-sm font-medium text-gray-500">{{ t('project.requirements') }}</span>
          <p class="mt-1 text-2xl font-bold text-gray-900">{{ requirementStore.requirements.length }}</p>
        </div>
        <div class="glass-card p-5">
          <span class="text-sm font-medium text-gray-500">{{ t('project.iterations') }}</span>
          <p class="mt-1 text-2xl font-bold text-gray-900">{{ iterationStore.iterations.length }}</p>
        </div>
        <div class="glass-card p-5">
          <span class="text-sm font-medium text-gray-500">{{ t('project.membersStat') }}</span>
          <p class="mt-1 text-2xl font-bold text-gray-900">--</p>
        </div>
      </div>

      <!-- Active iterations -->
      <div class="glass-card overflow-hidden">
        <div class="px-5 py-4 border-b border-blue-500/8 flex items-center justify-between">
          <h2 class="text-sm font-bold text-gray-900">{{ t('project.activeIterations') }}</h2>
          <button
            class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-white/80 border border-blue-500/10 text-gray-700 hover:bg-blue-50/80 hover:border-blue-500/20 transition-all"
            @click="openCreateIterModal"
          >
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
            </svg>
            {{ t('iteration.newIteration') }}
          </button>
        </div>
        <div v-if="activeIterations.length === 0" class="px-5 py-8 text-center text-sm text-gray-400">
          {{ t('project.noActiveIterations') }}
        </div>
        <div v-else class="divide-y divide-blue-500/5">
          <div
            v-for="iter in activeIterations"
            :key="iter.id"
            class="px-5 py-3 flex items-center justify-between hover:bg-blue-500/[0.01] transition-colors"
          >
            <div>
              <span class="text-sm font-medium text-gray-800">{{ iter.name }}</span>
              <span v-if="iter.start_date" class="text-xs text-gray-400 ml-2">
                {{ formatDate(iter.start_date) }}
                <span v-if="iter.end_date"> - {{ formatDate(iter.end_date) }}</span>
              </span>
            </div>
            <StatusBadge :status="iter.status" size="sm" />
          </div>
        </div>
      </div>

      <!-- Recent requirements table -->
      <div class="glass-card overflow-hidden">
        <div class="px-5 py-4 border-b border-blue-500/8">
          <h2 class="text-sm font-bold text-gray-900">{{ t('project.recentRequirements') }}</h2>
        </div>
        <div v-if="recentRequirements.length === 0" class="px-5 py-8 text-center text-sm text-gray-400">
          {{ t('project.noRequirementsYet') }}
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-blue-500/5 bg-blue-500/[0.02]">
                <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">{{ t('common.title') }}</th>
                <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">{{ t('common.priority') }}</th>
                <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">{{ t('common.status') }}</th>
                <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">{{ t('common.created') }}</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-blue-500/5">
              <tr v-for="req in recentRequirements" :key="req.id" class="hover:bg-blue-500/[0.01] transition-colors">
                <td class="px-5 py-3 text-gray-900">{{ req.title }}</td>
                <td class="px-5 py-3 capitalize text-gray-600">{{ req.priority }}</td>
                <td class="px-5 py-3">
                  <StatusBadge :status="req.status" size="sm" />
                </td>
                <td class="px-5 py-3 text-gray-400">{{ formatDate(req.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- Create iteration modal -->
    <Modal :show="showCreateModal" :title="t('iteration.newIteration')" @close="showCreateModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('iteration.iterationName') }}</label>
          <input
            v-model="newIterName"
            type="text"
            class="input-glass"
            @keyup.enter="handleCreateIter"
          />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('iteration.startDate') }}</label>
            <input v-model="newStartDate" type="date" class="input-glass" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('iteration.endDate') }}</label>
            <input v-model="newEndDate" type="date" class="input-glass" />
          </div>
        </div>
      </div>
      <div class="flex justify-end gap-3 mt-6">
        <button class="btn-secondary" @click="showCreateModal = false">{{ t('common.cancel') }}</button>
        <button class="btn-primary" :disabled="!newIterName.trim()" @click="handleCreateIter">{{ t('iteration.create') }}</button>
      </div>
    </Modal>
  </div>
</template>
