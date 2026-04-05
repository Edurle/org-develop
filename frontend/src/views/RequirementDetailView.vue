<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRequirementStore } from '@/stores/requirement'
import { useSpecificationStore } from '@/stores/specification'
import { useTaskStore } from '@/stores/task'
import { useTestcaseStore } from '@/stores/testcase'
import { useCoverageStore } from '@/stores/coverage'
import { useIterationStore } from '@/stores/iteration'
import StatusBadge from '@/components/StatusBadge.vue'
import EmptyState from '@/components/EmptyState.vue'
import Modal from '@/components/Modal.vue'
import type { SpecType } from '@/types'

const route = useRoute()
const router = useRouter()
const reqStore = useRequirementStore()
const specStore = useSpecificationStore()
const taskStore = useTaskStore()
const tcStore = useTestcaseStore()
const coverageStore = useCoverageStore()
const iterStore = useIterationStore()

const projectId = computed(() => route.params.id as string)
const reqId = computed(() => route.params.reqId as string)

const loading = ref(false)
const error = ref('')
const activeTab = ref<'specs' | 'dev' | 'test' | 'coverage'>('specs')

// Expand state
const expandedSpecId = ref<string | null>(null)
const expandedTestTaskId = ref<string | null>(null)

// Create spec modal
const showCreateSpecModal = ref(false)
const newSpecTitle = ref('')
const newSpecType = ref<SpecType>('api')

// Create dev task modal
const showCreateDevTaskModal = ref(false)
const newDevTaskTitle = ref('')
const newDevTaskSpecVersionId = ref('')
const newDevTaskEstimate = ref<number | null>(null)

// Create test task modal
const showCreateTestTaskModal = ref(false)
const newTestTaskTitle = ref('')

// Coverage check
const coverageSufficient = ref<boolean | null>(null)

const priorityColorMap: Record<string, string> = {
  low: 'bg-gradient-to-br from-gray-50 to-gray-100/50 text-gray-600 border-gray-200/60',
  medium: 'bg-gradient-to-br from-blue-50 to-blue-100/50 text-blue-700 border-blue-200/60',
  high: 'bg-gradient-to-br from-orange-50 to-orange-100/50 text-orange-700 border-orange-200/60',
  critical: 'bg-gradient-to-br from-red-50 to-red-100/50 text-red-700 border-red-200/60',
}

const specTypeOptions: SpecType[] = ['api', 'data', 'flow', 'ui']
const specTypeColorMap: Record<string, string> = {
  api: 'bg-gradient-to-br from-indigo-50 to-indigo-100/50 text-indigo-700 border-indigo-200/60',
  data: 'bg-gradient-to-br from-teal-50 to-teal-100/50 text-teal-700 border-teal-200/60',
  flow: 'bg-gradient-to-br from-amber-50 to-amber-100/50 text-amber-700 border-amber-200/60',
  ui: 'bg-gradient-to-br from-pink-50 to-pink-100/50 text-pink-700 border-pink-200/60',
}

const currentReq = computed(() => reqStore.currentRequirement)

// Status transition logic
const statusActions = computed(() => {
  if (!currentReq.value) return []
  const s = currentReq.value.status
  switch (s) {
    case 'draft':
      return [{ label: 'Start Spec Writing', status: 'spec_writing' }]
    case 'spec_writing':
      return [{ label: 'Submit for Review', status: 'spec_review' }]
    case 'spec_review':
      return [
        { label: 'Lock', status: 'spec_locked' },
        { label: 'Reject', status: 'spec_rejected' },
      ]
    case 'spec_locked':
      return [{ label: 'Start Development', status: 'in_progress' }]
    case 'in_progress':
      return [{ label: 'Start Testing', status: 'testing' }]
    case 'testing':
      return [{ label: 'Mark Done', status: 'done' }]
    default:
      return []
  }
})

const devTasksForReq = computed(() =>
  taskStore.devTasks.filter((t) => t.requirement_id === reqId.value),
)
const testTasksForReq = computed(() =>
  taskStore.testTasks.filter((t) => t.requirement_id === reqId.value),
)

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString()
}

async function loadAll() {
  loading.value = true
  error.value = ''
  try {
    await Promise.all([
      reqStore.fetchOne(reqId.value),
      specStore.fetchList(reqId.value),
      iterStore.fetchList(projectId.value),
      taskStore.fetchDevTasks(projectId.value),
      taskStore.fetchTestTasks(projectId.value),
    ])
  } catch (e: any) {
    error.value = e?.message || 'Failed to load requirement'
  } finally {
    loading.value = false
  }
}

async function handleStatusTransition(newStatus: string) {
  if (!currentReq.value) return
  try {
    await reqStore.updateStatus(currentReq.value.id, newStatus)
  } catch (e: any) {
    error.value = e?.message || 'Failed to update status'
  }
}

async function toggleSpecExpand(specId: string) {
  if (expandedSpecId.value === specId) {
    expandedSpecId.value = null
  } else {
    expandedSpecId.value = specId
    await specStore.fetchVersions(specId)
  }
}

async function toggleTestTaskExpand(taskId: string) {
  if (expandedTestTaskId.value === taskId) {
    expandedTestTaskId.value = null
  } else {
    expandedTestTaskId.value = taskId
    await tcStore.fetchList(taskId)
  }
}

function openCreateSpecModal() {
  newSpecTitle.value = ''
  newSpecType.value = 'api'
  showCreateSpecModal.value = true
}

async function handleCreateSpec() {
  if (!newSpecTitle.value.trim()) return
  try {
    await specStore.create(reqId.value, {
      spec_type: newSpecType.value,
      title: newSpecTitle.value.trim(),
    })
    showCreateSpecModal.value = false
  } catch (e: any) {
    error.value = e?.message || 'Failed to create specification'
  }
}

function openCreateDevTaskModal() {
  newDevTaskTitle.value = ''
  newDevTaskSpecVersionId.value = ''
  newDevTaskEstimate.value = null
  showCreateDevTaskModal.value = true
}

async function handleCreateDevTask() {
  if (!newDevTaskTitle.value.trim() || !newDevTaskSpecVersionId.value) return
  try {
    await taskStore.createDevTask(reqId.value, {
      spec_version_id: newDevTaskSpecVersionId.value,
      iteration_id: currentReq.value?.iteration_id ?? '',
      title: newDevTaskTitle.value.trim(),
      estimate_hours: newDevTaskEstimate.value ?? undefined,
    })
    showCreateDevTaskModal.value = false
  } catch (e: any) {
    error.value = e?.message || 'Failed to create dev task'
  }
}

function openCreateTestTaskModal() {
  newTestTaskTitle.value = ''
  showCreateTestTaskModal.value = true
}

async function handleCreateTestTask() {
  if (!newTestTaskTitle.value.trim()) return
  try {
    await taskStore.createTestTask(reqId.value, {
      iteration_id: currentReq.value?.iteration_id ?? '',
      title: newTestTaskTitle.value.trim(),
    })
    showCreateTestTaskModal.value = false
  } catch (e: any) {
    error.value = e?.message || 'Failed to create test task'
  }
}

async function loadCoverage() {
  try {
    await coverageStore.fetchReport(reqId.value)
    const check = await coverageStore.checkSufficient(reqId.value)
    coverageSufficient.value = check.sufficient
  } catch (e: any) {
    error.value = e?.message || 'Failed to load coverage'
  }
}

watch(activeTab, (tab) => {
  if (tab === 'coverage') {
    loadCoverage()
  }
})

function navigateToSpec(specId: string) {
  router.push(`/projects/${projectId.value}/requirements/${reqId.value}/specs/${specId}`)
}

// Collect all spec version IDs for the dev task modal
const allSpecVersions = computed(() => {
  const versions: { id: string; label: string }[] = []
  for (const spec of specStore.specs) {
    for (const ver of specStore.versions.filter((v) => v.spec_id === spec.id)) {
      versions.push({
        id: ver.id,
        label: `${spec.title} v${ver.version} (${ver.status})`,
      })
    }
  }
  return versions
})

onMounted(loadAll)
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- Loading -->
    <div v-if="loading" class="py-12 text-center text-gray-500">Loading...</div>

    <!-- Error -->
    <div v-else-if="error" class="p-3 rounded-[10px] border border-red-200/60 bg-red-50 text-red-700 text-sm">
      {{ error }}
    </div>

    <!-- Not found -->
    <EmptyState v-else-if="!currentReq" title="Requirement not found" description="The requirement you are looking for does not exist." />

    <template v-else>
      <!-- Header -->
      <div class="mb-6">
        <div class="flex items-center gap-3 mb-2">
          <button
            class="text-gray-400 hover:text-gray-600 transition-colors"
            @click="router.push(`/projects/${projectId}/requirements`)"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <h1 class="text-2xl font-bold text-gray-900">{{ currentReq.title }}</h1>
          <StatusBadge :status="currentReq.status" />
          <span :class="['badge-base', priorityColorMap[currentReq.priority] ?? 'bg-gradient-to-br from-gray-50 to-gray-100/50 text-gray-600 border-gray-200/60']">
            {{ currentReq.priority.charAt(0).toUpperCase() + currentReq.priority.slice(1) }}
          </span>
        </div>

        <!-- Status transition buttons -->
        <div v-if="statusActions.length > 0" class="flex items-center gap-2 mt-3">
          <button
            v-for="action in statusActions"
            :key="action.status"
            class="px-4 py-2 text-sm font-medium rounded-lg transition-colors"
            :class="action.status === 'spec_rejected'
              ? 'btn-danger'
              : action.status === 'done'
                ? 'text-white bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700'
                : 'btn-primary'"
            @click="handleStatusTransition(action.status)"
          >
            {{ action.label }}
          </button>
        </div>
      </div>

      <!-- Tabs -->
      <div class="border-b border-blue-500/8 mb-6">
        <nav class="flex gap-6">
          <button
            v-for="tab in (['specs', 'dev', 'test', 'coverage'] as const)"
            :key="tab"
            :class="[
              'pb-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === tab
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700',
            ]"
            @click="activeTab = tab"
          >
            {{ tab === 'specs' ? 'Specifications' : tab === 'dev' ? 'Dev Tasks' : tab === 'test' ? 'Test Tasks' : 'Coverage' }}
          </button>
        </nav>
      </div>

      <!-- Specifications Tab -->
      <div v-if="activeTab === 'specs'">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">Specifications</h2>
          <button
            class="btn-primary"
            @click="openCreateSpecModal"
          >
            Create Spec
          </button>
        </div>

        <EmptyState
          v-if="specStore.specs.length === 0"
          title="No specifications"
          description="Create a specification to define requirements in detail."
          action-label="Create Spec"
          @action="openCreateSpecModal"
        />

        <div v-else class="space-y-3">
          <div
            v-for="spec in specStore.specs"
            :key="spec.id"
            class="glass-card overflow-hidden"
          >
            <div
              class="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-blue-500/[0.01] transition-colors"
              @click="toggleSpecExpand(spec.id)"
            >
              <div class="flex items-center gap-3">
                <span :class="['badge-base', specTypeColorMap[spec.spec_type] ?? 'bg-gradient-to-br from-gray-50 to-gray-100/50 text-gray-600 border-gray-200/60']">
                  {{ spec.spec_type.toUpperCase() }}
                </span>
                <span class="font-medium text-gray-900">{{ spec.title }}</span>
                <span class="text-xs text-gray-500">v{{ spec.current_version }}</span>
              </div>
              <div class="flex items-center gap-2">
                <button
                  class="text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
                  @click.stop="navigateToSpec(spec.id)"
                >
                  Open
                </button>
                <svg
                  :class="['w-4 h-4 text-gray-400 transition-transform', expandedSpecId === spec.id ? 'rotate-180' : '']"
                  fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>

            <!-- Expanded versions -->
            <div v-if="expandedSpecId === spec.id" class="border-t border-blue-500/5 px-5 py-3 bg-blue-500/[0.01]">
              <div v-if="specStore.versions.filter(v => v.spec_id === spec.id).length === 0" class="text-sm text-gray-500">
                No versions yet.
              </div>
              <div v-else class="space-y-2">
                <div
                  v-for="ver in specStore.versions.filter(v => v.spec_id === spec.id)"
                  :key="ver.id"
                  class="flex items-center justify-between py-1"
                >
                  <div class="flex items-center gap-2">
                    <span class="text-sm text-gray-700">Version {{ ver.version }}</span>
                    <StatusBadge :status="ver.status" size="sm" />
                  </div>
                  <span class="text-xs text-gray-400">{{ formatDate(ver.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Dev Tasks Tab -->
      <div v-if="activeTab === 'dev'">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">Dev Tasks</h2>
          <button
            class="btn-primary"
            @click="openCreateDevTaskModal"
          >
            Create Dev Task
          </button>
        </div>

        <EmptyState
          v-if="devTasksForReq.length === 0"
          title="No dev tasks"
          description="Create a development task to start implementation."
          action-label="Create Dev Task"
          @action="openCreateDevTaskModal"
        />

        <div v-else class="glass-card overflow-hidden">
          <table class="w-full text-sm">
            <thead class="border-b border-blue-500/5 bg-blue-500/[0.02]">
              <tr>
                <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">Title</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">Status</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">Assignee</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">Est. Hours</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">Created</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-blue-500/5">
              <tr
                v-for="task in devTasksForReq"
                :key="task.id"
                class="hover:bg-blue-500/[0.01] transition-colors"
              >
                <td class="px-4 py-3 font-medium text-gray-900">{{ task.title }}</td>
                <td class="px-4 py-3"><StatusBadge :status="task.status" size="sm" /></td>
                <td class="px-4 py-3 text-gray-500">{{ task.assignee_id ?? 'Unassigned' }}</td>
                <td class="px-4 py-3 text-gray-500">{{ task.estimate_hours ?? '-' }}</td>
                <td class="px-4 py-3 text-gray-500">{{ formatDate(task.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Test Tasks Tab -->
      <div v-if="activeTab === 'test'">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">Test Tasks</h2>
          <button
            class="btn-primary"
            @click="openCreateTestTaskModal"
          >
            Create Test Task
          </button>
        </div>

        <EmptyState
          v-if="testTasksForReq.length === 0"
          title="No test tasks"
          description="Create a test task to start verification."
          action-label="Create Test Task"
          @action="openCreateTestTaskModal"
        />

        <div v-else class="space-y-3">
          <div
            v-for="task in testTasksForReq"
            :key="task.id"
            class="glass-card overflow-hidden"
          >
            <div
              class="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-blue-500/[0.01] transition-colors"
              @click="toggleTestTaskExpand(task.id)"
            >
              <div class="flex items-center gap-3">
                <span class="font-medium text-gray-900">{{ task.title }}</span>
                <StatusBadge :status="task.status" size="sm" />
              </div>
              <svg
                :class="['w-4 h-4 text-gray-400 transition-transform', expandedTestTaskId === task.id ? 'rotate-180' : '']"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </div>

            <!-- Expanded test cases -->
            <div v-if="expandedTestTaskId === task.id" class="border-t border-blue-500/5 px-5 py-3 bg-blue-500/[0.01]">
              <div v-if="tcStore.testCases.length === 0" class="text-sm text-gray-500">
                No test cases yet.
              </div>
              <div v-else class="space-y-2">
                <div
                  v-for="tc in tcStore.testCases"
                  :key="tc.id"
                  class="flex items-center justify-between py-1"
                >
                  <div class="flex items-center gap-2">
                    <span class="text-sm text-gray-700">{{ tc.title }}</span>
                    <StatusBadge :status="tc.status" size="sm" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Coverage Tab -->
      <div v-if="activeTab === 'coverage'">
        <div v-if="!coverageStore.report" class="py-12 text-center text-gray-500">
          Loading coverage...
        </div>

        <template v-else>
          <!-- Summary cards -->
          <div class="grid grid-cols-3 gap-4 mb-6">
            <div class="glass-card p-5 text-center">
              <div class="text-2xl font-bold text-gray-900">{{ coverageStore.report.total_clauses }}</div>
              <div class="text-sm text-gray-500 mt-1">Total Clauses</div>
            </div>
            <div class="glass-card p-5 text-center">
              <div class="text-2xl font-bold text-green-600">{{ coverageStore.report.covered_clauses }}</div>
              <div class="text-sm text-gray-500 mt-1">Covered</div>
            </div>
            <div class="glass-card p-5 text-center">
              <div class="text-2xl font-bold text-blue-600">
                {{ coverageStore.report.total_clauses > 0
                  ? Math.round((coverageStore.report.covered_clauses / coverageStore.report.total_clauses) * 100)
                  : 0 }}%
              </div>
              <div class="text-sm text-gray-500 mt-1">Overall Coverage</div>
            </div>
          </div>

          <!-- Progress bars by severity -->
          <div class="glass-card p-4 mb-6">
            <h3 class="text-sm font-bold text-gray-900 mb-3">Coverage by Severity</h3>
            <div class="space-y-3">
              <div>
                <div class="flex items-center justify-between text-sm mb-1">
                  <span class="font-medium text-gray-700">MUST</span>
                  <span :class="coverageStore.report.must_coverage_pct === 100 ? 'text-green-600' : 'text-red-600'" class="font-medium">
                    {{ coverageStore.report.must_coverage_pct.toFixed(1) }}%
                  </span>
                </div>
                <div class="w-full bg-gray-100 rounded-full h-2">
                  <div
                    class="h-2 rounded-full transition-all"
                    :class="coverageStore.report.must_coverage_pct === 100 ? 'bg-gradient-to-r from-green-400 to-green-500' : 'bg-gradient-to-r from-red-400 to-red-500'"
                    :style="{ width: coverageStore.report.must_coverage_pct + '%' }"
                  />
                </div>
              </div>
              <div>
                <div class="flex items-center justify-between text-sm mb-1">
                  <span class="font-medium text-gray-700">SHOULD</span>
                  <span :class="coverageStore.report.should_coverage_pct >= 80 ? 'text-green-600' : coverageStore.report.should_coverage_pct >= 50 ? 'text-yellow-600' : 'text-red-600'" class="font-medium">
                    {{ coverageStore.report.should_coverage_pct.toFixed(1) }}%
                  </span>
                </div>
                <div class="w-full bg-gray-100 rounded-full h-2">
                  <div
                    class="h-2 rounded-full transition-all"
                    :class="coverageStore.report.should_coverage_pct >= 80 ? 'bg-gradient-to-r from-green-400 to-green-500' : coverageStore.report.should_coverage_pct >= 50 ? 'bg-gradient-to-r from-yellow-400 to-yellow-500' : 'bg-gradient-to-r from-red-400 to-red-500'"
                    :style="{ width: coverageStore.report.should_coverage_pct + '%' }"
                  />
                </div>
              </div>
              <div>
                <div class="flex items-center justify-between text-sm mb-1">
                  <span class="font-medium text-gray-700">MAY</span>
                  <span class="text-gray-500 font-medium">
                    {{ coverageStore.report.may_coverage_pct.toFixed(1) }}%
                  </span>
                </div>
                <div class="w-full bg-gray-100 rounded-full h-2">
                  <div
                    class="h-2 rounded-full bg-gradient-to-r from-gray-300 to-gray-400 transition-all"
                    :style="{ width: coverageStore.report.may_coverage_pct + '%' }"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- Uncovered clauses table -->
          <div v-if="coverageStore.report.uncovered_clauses.length > 0" class="glass-card overflow-hidden">
            <div class="px-4 py-3 border-b border-blue-500/8">
              <h3 class="text-sm font-bold text-gray-900">Uncovered Clauses</h3>
            </div>
            <table class="w-full text-sm">
              <thead class="border-b border-blue-500/5 bg-blue-500/[0.02]">
                <tr>
                  <th class="text-left px-4 py-2 text-xs font-semibold text-gray-500">Clause ID</th>
                  <th class="text-left px-4 py-2 text-xs font-semibold text-gray-500">Title</th>
                  <th class="text-left px-4 py-2 text-xs font-semibold text-gray-500">Severity</th>
                  <th class="text-left px-4 py-2 text-xs font-semibold text-gray-500">Category</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-blue-500/5">
                <tr
                  v-for="clause in coverageStore.report.uncovered_clauses"
                  :key="clause.id"
                  class="hover:bg-blue-500/[0.01]"
                >
                  <td class="px-4 py-2 font-mono text-xs text-gray-700">{{ clause.clause_id }}</td>
                  <td class="px-4 py-2 text-gray-900">{{ clause.title }}</td>
                  <td class="px-4 py-2">
                    <span :class="[
                      'badge-base',
                      clause.severity === 'must' ? 'bg-gradient-to-br from-red-50 to-red-100/50 text-red-700 border-red-200/60' :
                      clause.severity === 'should' ? 'bg-gradient-to-br from-amber-50 to-amber-100/50 text-amber-700 border-amber-200/60' :
                      'bg-gradient-to-br from-gray-50 to-gray-100/50 text-gray-600 border-gray-200/60',
                    ]">
                      {{ clause.severity.toUpperCase() }}
                    </span>
                  </td>
                  <td class="px-4 py-2 text-gray-500">{{ clause.category }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <EmptyState
            v-else
            title="All clauses covered"
            description="Every specification clause has associated test coverage."
          />
        </template>
      </div>
    </template>

    <!-- Create Spec Modal -->
    <Modal :show="showCreateSpecModal" title="New Specification" @close="showCreateSpecModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Title</label>
          <input
            v-model="newSpecTitle"
            type="text"
            placeholder="Specification title"
            class="input-glass"
            @keyup.enter="handleCreateSpec"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Type</label>
          <select
            v-model="newSpecType"
            class="select-glass"
          >
            <option v-for="t in specTypeOptions" :key="t" :value="t">{{ t.toUpperCase() }}</option>
          </select>
        </div>
      </div>
      <div class="flex justify-end gap-3 mt-6">
        <button
          class="btn-secondary"
          @click="showCreateSpecModal = false"
        >
          Cancel
        </button>
        <button
          class="btn-primary"
          :disabled="!newSpecTitle.trim()"
          @click="handleCreateSpec"
        >
          Create
        </button>
      </div>
    </Modal>

    <!-- Create Dev Task Modal -->
    <Modal :show="showCreateDevTaskModal" title="New Dev Task" @close="showCreateDevTaskModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Title</label>
          <input
            v-model="newDevTaskTitle"
            type="text"
            placeholder="Dev task title"
            class="input-glass"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Spec Version</label>
          <select
            v-model="newDevTaskSpecVersionId"
            class="select-glass"
          >
            <option value="">Select version</option>
            <option v-for="sv in allSpecVersions" :key="sv.id" :value="sv.id">{{ sv.label }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Estimate Hours</label>
          <input
            v-model.number="newDevTaskEstimate"
            type="number"
            min="0"
            placeholder="Optional"
            class="input-glass"
          />
        </div>
      </div>
      <div class="flex justify-end gap-3 mt-6">
        <button
          class="btn-secondary"
          @click="showCreateDevTaskModal = false"
        >
          Cancel
        </button>
        <button
          class="btn-primary"
          :disabled="!newDevTaskTitle.trim() || !newDevTaskSpecVersionId"
          @click="handleCreateDevTask"
        >
          Create
        </button>
      </div>
    </Modal>

    <!-- Create Test Task Modal -->
    <Modal :show="showCreateTestTaskModal" title="New Test Task" @close="showCreateTestTaskModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Title</label>
          <input
            v-model="newTestTaskTitle"
            type="text"
            placeholder="Test task title"
            class="input-glass"
            @keyup.enter="handleCreateTestTask"
          />
        </div>
      </div>
      <div class="flex justify-end gap-3 mt-6">
        <button
          class="btn-secondary"
          @click="showCreateTestTaskModal = false"
        >
          Cancel
        </button>
        <button
          class="btn-primary"
          :disabled="!newTestTaskTitle.trim()"
          @click="handleCreateTestTask"
        >
          Create
        </button>
      </div>
    </Modal>
  </div>
</template>
