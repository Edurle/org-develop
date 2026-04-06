<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRequirementStore } from '@/stores/requirement'
import { useIterationStore } from '@/stores/iteration'
import StatusBadge from '@/components/StatusBadge.vue'
import EmptyState from '@/components/EmptyState.vue'
import Modal from '@/components/Modal.vue'
import type { Priority } from '@/types'

const route = useRoute()
const router = useRouter()
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
    error.value = e?.message || 'Failed to load requirements'
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
    error.value = e?.message || 'Failed to create requirement'
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
      <h1 class="text-2xl font-bold text-gray-900">Requirements</h1>
      <button
        class="btn-primary px-5 py-2.5 text-sm"
        @click="openCreateModal"
      >
        New Requirement
      </button>
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
        <option value="">All Statuses</option>
        <option v-for="s in statusOptions" :key="s" :value="s">{{ s.replace(/_/g, ' ') }}</option>
      </select>

      <select
        v-model="iterationFilter"
        class="select-glass !w-auto"
        @change="applyFilters"
      >
        <option value="">All Iterations</option>
        <option v-for="iter in iterStore.iterations" :key="iter.id" :value="iter.id">{{ iter.name }}</option>
      </select>

      <select
        v-model="priorityFilter"
        class="select-glass !w-auto"
      >
        <option value="">All Priorities</option>
        <option v-for="p in priorityOptions" :key="p" :value="p">{{ p.charAt(0).toUpperCase() + p.slice(1) }}</option>
      </select>

      <button
        class="text-xs text-gray-500 hover:text-gray-700 transition-colors"
        @click="statusFilter = ''; iterationFilter = ''; priorityFilter = ''; applyFilters()"
      >
        Clear Filters
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="py-12 text-center text-gray-500">Loading...</div>

    <!-- Empty state -->
    <EmptyState
      v-else-if="reqStore.requirements.length === 0"
      title="No requirements yet"
      description="Create your first requirement to get started."
      action-label="New Requirement"
      @action="openCreateModal"
    />

    <EmptyState
      v-else-if="filteredRequirements.length === 0"
      title="No matching requirements"
      description="Try adjusting your filters."
    />

    <!-- Table -->
    <div v-else class="glass-card overflow-hidden">
      <table class="w-full text-sm">
        <thead class="border-b border-blue-500/5 bg-blue-500/[0.02]">
          <tr>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">Title</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">Priority</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">Status</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">Iteration</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">Created</th>
            <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">Actions</th>
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
                {{ req.priority.charAt(0).toUpperCase() + req.priority.slice(1) }}
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
              <button
                class="text-blue-600 hover:text-blue-800 text-xs font-semibold transition-colors"
                @click.stop="navigateToReq(req.id)"
              >
                View
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Requirement Modal -->
    <Modal :show="showCreateModal" title="New Requirement" @close="showCreateModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Title</label>
          <input
            id="req-title"
            v-model="newTitle"
            type="text"
            placeholder="Requirement title"
            class="input-glass"
            @keyup.enter="handleCreate"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Priority</label>
          <select
            id="req-priority"
            v-model="newPriority"
            class="select-glass"
          >
            <option v-for="p in priorityOptions" :key="p" :value="p">{{ p.charAt(0).toUpperCase() + p.slice(1) }}</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Iteration</label>
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
        <button
          class="btn-secondary"
          @click="showCreateModal = false"
        >
          Cancel
        </button>
        <button
          class="btn-primary"
          :disabled="!newTitle.trim() || !newIterationId"
          @click="handleCreate"
        >
          Create
        </button>
      </div>
    </Modal>
  </div>
</template>
