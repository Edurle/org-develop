<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useRequirementStore } from '@/stores/requirement'
import { useSpecificationStore } from '@/stores/specification'
import { useTaskStore } from '@/stores/task'
import { useTestcaseStore } from '@/stores/testcase'
import { useCoverageStore } from '@/stores/coverage'
import { useIterationStore } from '@/stores/iteration'
import { useProjectStore } from '@/stores/project'
import { teamApi } from '@/api/endpoints'
import StatusBadge from '@/components/StatusBadge.vue'
import EmptyState from '@/components/EmptyState.vue'
import Modal from '@/components/Modal.vue'
import GlassButton from '@/components/GlassButton.vue'
import type { SpecType, Priority, DevTask, TestCase, TeamMemberDetail } from '@/types'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const reqStore = useRequirementStore()
const specStore = useSpecificationStore()
const taskStore = useTaskStore()
const tcStore = useTestcaseStore()
const coverageStore = useCoverageStore()
const iterStore = useIterationStore()
const projectStore = useProjectStore()

const projectId = computed(() => route.params.projectId as string)
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
const showSpecGuide = ref(false)

const specGuides = computed(() => [
  {
    type: 'api' as SpecType,
    label: t('specGuide.apiLabel'),
    desc: t('specGuide.apiDesc'),
    example: t('specGuide.apiExample'),
  },
  {
    type: 'data' as SpecType,
    label: t('specGuide.dataLabel'),
    desc: t('specGuide.dataDesc'),
    example: t('specGuide.dataExample'),
  },
  {
    type: 'flow' as SpecType,
    label: t('specGuide.flowLabel'),
    desc: t('specGuide.flowDesc'),
    example: t('specGuide.flowExample'),
  },
  {
    type: 'ui' as SpecType,
    label: t('specGuide.uiLabel'),
    desc: t('specGuide.uiDesc'),
    example: t('specGuide.uiExample'),
  },
  {
    type: 'rule' as SpecType,
    label: t('specGuide.ruleLabel'),
    desc: t('specGuide.ruleDesc'),
    example: t('specGuide.ruleExample'),
  },
  {
    type: 'security' as SpecType,
    label: t('specGuide.securityLabel'),
    desc: t('specGuide.securityDesc'),
    example: t('specGuide.securityExample'),
  },
  {
    type: 'event' as SpecType,
    label: t('specGuide.eventLabel'),
    desc: t('specGuide.eventDesc'),
    example: t('specGuide.eventExample'),
  },
  {
    type: 'config' as SpecType,
    label: t('specGuide.configLabel'),
    desc: t('specGuide.configDesc'),
    example: t('specGuide.configExample'),
  },
])

// Create dev task modal
const showCreateDevTaskModal = ref(false)
const newDevTaskTitle = ref('')
const newDevTaskSpecVersionId = ref('')
const newDevTaskEstimate = ref<number | null>(null)

// Create test task modal
const showCreateTestTaskModal = ref(false)
const newTestTaskTitle = ref('')

// Edit requirement modal
const showEditReqModal = ref(false)
const editReqTitle = ref('')
const editReqPriority = ref<Priority>('medium')

// Edit dev task modal
const showEditDevTaskModal = ref(false)
const editDevTaskId = ref('')
const editDevTaskTitle = ref('')
const editDevTaskEstimate = ref<number | null>(null)
const editDevTaskAssigneeId = ref<string | null>(null)

// Team members for assignee selection
const teamMembers = ref<TeamMemberDetail[]>([])
const teamMembersLoaded = ref(false)

// Delete dev task confirmation
const showDeleteDevTaskConfirm = ref(false)
const deleteDevTaskId = ref('')
const deleteDevTaskTitle = ref('')

// Edit test case modal
const showEditTcModal = ref(false)
const editTcId = ref('')
const editTcTitle = ref('')
const editTcPreconditions = ref('')
const editTcSteps = ref('')
const editTcExpected = ref('')
const editTcActual = ref('')

// Delete test case confirmation
const showDeleteTcConfirm = ref(false)
const deleteTcId = ref('')
const deleteTcTitle = ref('')

// Coverage check
const coverageSufficient = ref<boolean | null>(null)

const priorityColorMap: Record<string, string> = {
  low: 'bg-gradient-to-br from-gray-50 to-gray-100/50 text-gray-600 border-gray-200/60',
  medium: 'bg-gradient-to-br from-blue-50 to-blue-100/50 text-blue-700 border-blue-200/60',
  high: 'bg-gradient-to-br from-orange-50 to-orange-100/50 text-orange-700 border-orange-200/60',
  critical: 'bg-gradient-to-br from-red-50 to-red-100/50 text-red-700 border-red-200/60',
}

const specTypeOptions: SpecType[] = ['api', 'data', 'flow', 'ui', 'rule', 'security', 'event', 'config']
const specTypeColorMap: Record<string, string> = {
  api: 'bg-gradient-to-br from-indigo-50 to-indigo-100/50 text-indigo-700 border-indigo-200/60',
  data: 'bg-gradient-to-br from-teal-50 to-teal-100/50 text-teal-700 border-teal-200/60',
  flow: 'bg-gradient-to-br from-amber-50 to-amber-100/50 text-amber-700 border-amber-200/60',
  ui: 'bg-gradient-to-br from-pink-50 to-pink-100/50 text-pink-700 border-pink-200/60',
  rule: 'bg-gradient-to-br from-purple-50 to-purple-100/50 text-purple-700 border-purple-200/60',
  security: 'bg-gradient-to-br from-red-50 to-red-100/50 text-red-700 border-red-200/60',
  event: 'bg-gradient-to-br from-cyan-50 to-cyan-100/50 text-cyan-700 border-cyan-200/60',
  config: 'bg-gradient-to-br from-lime-50 to-lime-100/50 text-lime-700 border-lime-200/60',
}

const currentReq = computed(() => reqStore.currentRequirement)

// Status transition logic
const statusActions = computed(() => {
  if (!currentReq.value) return []
  const s = currentReq.value.status
  switch (s) {
    case 'draft':
      return [{ label: t('requirement.startSpecWriting'), status: 'spec_writing' }]
    case 'spec_writing':
      return [{ label: t('requirement.submitForReview'), status: 'spec_review' }]
    case 'spec_review':
      return [
        { label: t('requirement.lock'), status: 'spec_locked' },
        { label: t('requirement.reject'), status: 'spec_rejected' },
      ]
    case 'spec_locked':
      return [{ label: t('requirement.startDevelopment'), status: 'in_progress' }]
    case 'in_progress':
      return [{ label: t('requirement.startTesting'), status: 'testing' }]
    case 'testing':
      return [{ label: t('requirement.markDone'), status: 'done' }]
    default:
      return []
  }
})

const devTasksForReq = computed(() =>
  taskStore.devTasks.filter((task) => task.requirement_id === reqId.value),
)
const testTasksForReq = computed(() =>
  taskStore.testTasks.filter((task) => task.requirement_id === reqId.value),
)

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString()
}

async function loadAll() {
  loading.value = true
  error.value = ''
  try {
    await Promise.all([
      projectStore.fetchOne(projectId.value),
      reqStore.fetchOne(reqId.value),
      specStore.fetchList(reqId.value),
      iterStore.fetchList(projectId.value),
      taskStore.fetchDevTasks(projectId.value),
      taskStore.fetchTestTasks(projectId.value),
    ])
    await loadTeamMembers()
  } catch (e: any) {
    error.value = e?.message || t('requirement.errorLoadFailed')
  } finally {
    loading.value = false
  }
}

async function loadTeamMembers() {
  const teamId = projectStore.currentProject?.team_id
  if (!teamId) return
  try {
    const res = await teamApi.membersDetail(teamId)
    teamMembers.value = res.data
    teamMembersLoaded.value = true
  } catch {
    // silently ignore — assignee selector will just be empty
  }
}

async function handleStatusTransition(newStatus: string) {
  if (!currentReq.value) return
  try {
    await reqStore.updateStatus(currentReq.value.id, newStatus)
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || t('requirement.errorUpdateFailed')
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
    error.value = e?.message || t('specification.errorLoadFailed')
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
    error.value = e?.response?.data?.detail || e?.message || t('requirement.errorUpdateFailed')
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
    error.value = e?.response?.data?.detail || e?.message || t('requirement.errorUpdateFailed')
  }
}

async function loadCoverage() {
  try {
    await coverageStore.fetchReport(reqId.value)
    const check = await coverageStore.checkSufficient(reqId.value)
    coverageSufficient.value = check.sufficient
  } catch (e: any) {
    error.value = e?.message || t('coverage.loadFailed')
  }
}

watch(activeTab, (tab) => {
  if (tab === 'coverage') {
    loadCoverage()
  }
})

// Requirement edit
function openEditReqModal() {
  if (!currentReq.value) return
  editReqTitle.value = currentReq.value.title
  editReqPriority.value = currentReq.value.priority
  showEditReqModal.value = true
}

async function handleEditReq() {
  if (!editReqTitle.value.trim()) return
  try {
    await reqStore.update(currentReq.value!.id, {
      title: editReqTitle.value.trim(),
      priority: editReqPriority.value,
    })
    showEditReqModal.value = false
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || t('requirement.errorUpdateFailed')
  }
}

// Dev task edit/delete
function openEditDevTaskModal(task: DevTask) {
  editDevTaskId.value = task.id
  editDevTaskTitle.value = task.title
  editDevTaskEstimate.value = task.estimate_hours
  editDevTaskAssigneeId.value = task.assignee_id
  showEditDevTaskModal.value = true
}

async function handleEditDevTask() {
  if (!editDevTaskTitle.value.trim()) return
  try {
    await taskStore.updateDevTask(editDevTaskId.value, {
      title: editDevTaskTitle.value.trim(),
      estimate_hours: editDevTaskEstimate.value,
      assignee_id: editDevTaskAssigneeId.value,
    })
    showEditDevTaskModal.value = false
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || t('requirement.errorUpdateFailed')
  }
}

function openDeleteDevTaskConfirm(task: DevTask) {
  deleteDevTaskId.value = task.id
  deleteDevTaskTitle.value = task.title
  showDeleteDevTaskConfirm.value = true
}

async function handleDeleteDevTask() {
  try {
    await taskStore.removeDevTask(deleteDevTaskId.value)
    showDeleteDevTaskConfirm.value = false
  } catch (e: any) {
    error.value = e?.message || t('requirement.errorDeleteFailed')
  }
}

// Test case edit/delete
function openEditTcModal(tc: TestCase) {
  editTcId.value = tc.id
  editTcTitle.value = tc.title
  editTcPreconditions.value = tc.preconditions ?? ''
  editTcSteps.value = tc.steps
  editTcExpected.value = tc.expected_result
  editTcActual.value = tc.actual_result ?? ''
  showEditTcModal.value = true
}

async function handleEditTc() {
  if (!editTcTitle.value.trim()) return
  try {
    await tcStore.update(editTcId.value, {
      title: editTcTitle.value.trim(),
      preconditions: editTcPreconditions.value || undefined,
      steps: editTcSteps.value,
      expected_result: editTcExpected.value,
      actual_result: editTcActual.value || undefined,
    })
    showEditTcModal.value = false
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || t('requirement.errorUpdateFailed')
  }
}

function openDeleteTcConfirm(tc: TestCase) {
  deleteTcId.value = tc.id
  deleteTcTitle.value = tc.title
  showDeleteTcConfirm.value = true
}

async function handleDeleteTc() {
  try {
    await tcStore.remove(deleteTcId.value)
    showDeleteTcConfirm.value = false
  } catch (e: any) {
    error.value = e?.message || t('requirement.errorDeleteFailed')
  }
}

function navigateToSpec(specId: string) {
  router.push(`/projects/${projectId.value}/requirements/${reqId.value}/specs/${specId}`)
}

const canCreateDevTask = computed(() => {
  const s = currentReq.value?.status
  return s === 'spec_locked' || s === 'in_progress' || s === 'testing'
})

// Collect all spec version IDs for the dev task modal
const allSpecVersions = computed(() => {
  const versions: { id: string; label: string }[] = []
  for (const spec of specStore.specs) {
    for (const ver of specStore.versions.filter((v) => v.spec_id === spec.id && v.status === 'locked')) {
      versions.push({
        id: ver.id,
        label: `${spec.title} v${ver.version}`,
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
    <div v-if="loading" class="py-12 text-center text-gray-500">{{ t('common.loading') }}</div>

    <!-- Error -->
    <div v-else-if="error" class="p-3 rounded-[10px] border border-red-200/60 bg-red-50 text-red-700 text-sm">
      {{ error }}
    </div>

    <!-- Not found -->
    <EmptyState v-else-if="!currentReq" :title="t('requirement.requirementNotFound')" :description="t('requirement.requirementNotFoundDesc')" />

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
            {{ t('priority.' + currentReq.priority) }}
          </span>
          <button
            class="text-sm text-gray-400 hover:text-gray-600 transition-colors ml-2"
            @click="openEditReqModal"
            :title="t('requirement.editRequirement')"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
          </button>
        </div>

        <!-- Status transition buttons -->
        <div v-if="statusActions.length > 0" class="flex items-center gap-2 mt-3">
          <GlassButton
            v-for="action in statusActions"
            :key="action.status"
            :variant="action.status === 'spec_rejected' ? 'danger' : action.status === 'done' ? 'success' : 'primary'"
            @click="handleStatusTransition(action.status)"
          >
            {{ action.label }}
          </GlassButton>
        </div>
      </div>

      <!-- Tabs -->
      <div class="mb-6">
        <nav class="flex gap-3">
          <button
            v-for="tab in (['specs', 'dev', 'test', 'coverage'] as const)"
            :key="tab"
            :class="[
              'px-5 py-2.5 text-sm font-medium rounded-full border transition-all backdrop-blur-sm',
              activeTab === tab
                ? 'bg-white/60 border-white/50 text-blue-600 shadow-[0_2px_8px_rgba(59,130,246,0.12)]'
                : 'bg-white/30 border-white/30 text-gray-500 hover:bg-white/40 hover:text-gray-700',
            ]"
            @click="activeTab = tab"
          >
            {{ tab === 'specs' ? t('requirement.specifications') : tab === 'dev' ? t('requirement.devTasks') : tab === 'test' ? t('requirement.testTasks') : t('requirement.coverage') }}
          </button>
        </nav>
      </div>

      <!-- Specifications Tab -->
      <div v-if="activeTab === 'specs'">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">{{ t('requirement.specifications') }}</h2>
          <GlassButton
            @click="openCreateSpecModal"
          >
            {{ t('specification.createSpec') }}
          </GlassButton>
        </div>

        <EmptyState
          v-if="specStore.specs.length === 0"
          :title="t('specification.noSpecs')"
          :description="t('specification.noSpecsDesc')"
          :action-label="t('specification.createSpec')"
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
                  {{ t('specType.' + spec.spec_type) }}
                </span>
                <span class="font-medium text-gray-900">{{ spec.title }}</span>
                <span class="text-xs text-gray-500">v{{ spec.current_version }}</span>
              </div>
              <div class="flex items-center gap-2">
                <GlassButton variant="ghost" size="small" @click.stop="navigateToSpec(spec.id)">
                  {{ t('common.view') }}
                </GlassButton>
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
                {{ t('specification.noVersions') }}
              </div>
              <div v-else class="space-y-2">
                <div
                  v-for="ver in specStore.versions.filter(v => v.spec_id === spec.id)"
                  :key="ver.id"
                  class="flex items-center justify-between py-1"
                >
                  <div class="flex items-center gap-2">
                    <span class="text-sm text-gray-700">{{ t('specification.version', { n: ver.version }) }}</span>
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
          <h2 class="text-lg font-semibold text-gray-900">{{ t('requirement.devTasks') }}</h2>
          <GlassButton
            :disabled="!canCreateDevTask"
            @click="openCreateDevTaskModal"
          >
            {{ t('task.createDevTask') }}
          </GlassButton>
        </div>

        <EmptyState
          v-if="devTasksForReq.length === 0"
          :title="t('task.noDevTasks')"
          :description="t('task.noDevTasksDesc')"
          :action-label="canCreateDevTask ? t('task.createDevTask') : undefined"
          @action="openCreateDevTaskModal"
        />

        <div v-else class="glass-card overflow-hidden">
          <table class="w-full text-sm">
            <thead class="border-b border-blue-500/5 bg-blue-500/[0.02]">
              <tr>
                <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">{{ t('common.title') }}</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">{{ t('common.status') }}</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">{{ t('task.assignee') }}</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">{{ t('task.estHours') }}</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">{{ t('common.created') }}</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500">{{ t('common.actions') }}</th>
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
                <td class="px-4 py-3 text-gray-500">{{ task.assignee ? (task.assignee.display_name || task.assignee.username) : t('task.unassigned') }}</td>
                <td class="px-4 py-3 text-gray-500">{{ task.estimate_hours ?? '-' }}</td>
                <td class="px-4 py-3 text-gray-500">{{ formatDate(task.created_at) }}</td>
                <td class="px-4 py-3">
                  <div class="flex items-center gap-2">
                    <GlassButton variant="ghost" size="small" @click="openEditDevTaskModal(task)">
                      {{ t('common.edit') }}
                    </GlassButton>
                    <GlassButton
                      v-if="task.status === 'open'"
                      variant="danger"
                      size="small"
                      @click="openDeleteDevTaskConfirm(task)"
                    >
                      {{ t('common.delete') }}
                    </GlassButton>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Test Tasks Tab -->
      <div v-if="activeTab === 'test'">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900">{{ t('requirement.testTasks') }}</h2>
          <GlassButton @click="openCreateTestTaskModal">
            {{ t('task.createTestTask') }}
          </GlassButton>
        </div>

        <EmptyState
          v-if="testTasksForReq.length === 0"
          :title="t('task.noTestTasks')"
          :description="t('task.noTestTasksDesc')"
          :action-label="t('task.createTestTask')"
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
                {{ t('task.noTestCases') }}
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
                  <div class="flex items-center gap-2">
                    <GlassButton variant="ghost" size="small" @click.stop="openEditTcModal(tc)">
                      {{ t('common.edit') }}
                    </GlassButton>
                    <GlassButton
                      v-if="tc.status === 'pending'"
                      variant="danger"
                      size="small"
                      @click.stop="openDeleteTcConfirm(tc)"
                    >
                      {{ t('common.delete') }}
                    </GlassButton>
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
          {{ t('coverage.loadingCoverage') }}
        </div>

        <template v-else>
          <!-- Summary cards -->
          <div class="grid grid-cols-3 gap-4 mb-6">
            <div class="glass-card p-5 text-center">
              <div class="text-2xl font-bold text-gray-900">{{ coverageStore.report.total_clauses }}</div>
              <div class="text-sm text-gray-500 mt-1">{{ t('coverage.totalClauses') }}</div>
            </div>
            <div class="glass-card p-5 text-center">
              <div class="text-2xl font-bold text-green-600">{{ coverageStore.report.covered_clauses }}</div>
              <div class="text-sm text-gray-500 mt-1">{{ t('coverage.covered') }}</div>
            </div>
            <div class="glass-card p-5 text-center">
              <div class="text-2xl font-bold text-blue-600">
                {{ coverageStore.report.total_clauses > 0
                  ? Math.round((coverageStore.report.covered_clauses / coverageStore.report.total_clauses) * 100)
                  : 0 }}%
              </div>
              <div class="text-sm text-gray-500 mt-1">{{ t('coverage.overallCoverage') }}</div>
            </div>
          </div>

          <!-- Progress bars by severity -->
          <div class="glass-card p-4 mb-6">
            <h3 class="text-sm font-bold text-gray-900 mb-3">{{ t('coverage.coverageBySeverity') }}</h3>
            <div class="space-y-3">
              <div>
                <div class="flex items-center justify-between text-sm mb-1">
                  <span class="font-medium text-gray-700">{{ t('severity.must') }}</span>
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
                  <span class="font-medium text-gray-700">{{ t('severity.should') }}</span>
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
                  <span class="font-medium text-gray-700">{{ t('severity.may') }}</span>
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
              <h3 class="text-sm font-bold text-gray-900">{{ t('coverage.uncoveredClauses') }}</h3>
            </div>
            <table class="w-full text-sm">
              <thead class="border-b border-blue-500/5 bg-blue-500/[0.02]">
                <tr>
                  <th class="text-left px-4 py-2 text-xs font-semibold text-gray-500">{{ t('coverage.clauseId') }}</th>
                  <th class="text-left px-4 py-2 text-xs font-semibold text-gray-500">{{ t('coverage.clauseTitle') }}</th>
                  <th class="text-left px-4 py-2 text-xs font-semibold text-gray-500">{{ t('coverage.severity') }}</th>
                  <th class="text-left px-4 py-2 text-xs font-semibold text-gray-500">{{ t('coverage.category') }}</th>
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
            :title="t('coverage.allClausesCovered')"
            :description="t('coverage.allClausesCoveredDesc')"
          />
        </template>
      </div>
    </template>

    <!-- Create Spec Modal -->
    <Modal :show="showCreateSpecModal" :title="t('specification.newSpecification')" @close="showCreateSpecModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('common.title') }}</label>
          <input
            v-model="newSpecTitle"
            type="text"
            :placeholder="t('specification.specTitle')"
            class="input-glass"
            @keyup.enter="handleCreateSpec"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('common.type') }}</label>
          <select
            v-model="newSpecType"
            class="select-glass"
          >
            <option v-for="opt in specTypeOptions" :key="opt" :value="opt">{{ t('specType.' + opt) }}</option>
          </select>
        </div>

        <!-- Spec Type Guide -->
        <div class="border border-gray-200/60 rounded-lg overflow-hidden">
          <button
            class="w-full flex items-center justify-between px-4 py-2.5 text-sm font-medium text-gray-600 hover:bg-gray-50/50 transition-colors"
            @click="showSpecGuide = !showSpecGuide"
          >
            <span>{{ t('specification.typeGuide') }}</span>
            <svg class="w-4 h-4 transition-transform" :class="{ 'rotate-180': showSpecGuide }" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
          </button>
          <div v-show="showSpecGuide" class="px-4 pb-4 text-xs text-gray-500 space-y-3 max-h-80 overflow-y-auto">
            <div v-for="guide in specGuides" :key="guide.type" class="space-y-1">
              <div class="flex items-center gap-1.5">
                <span :class="['inline-block px-1.5 py-0.5 rounded text-xs font-medium border', specTypeColorMap[guide.type] ?? '']">{{ t('specType.' + guide.type) }}</span>
                <span class="text-gray-700 font-medium">{{ guide.label }}</span>
              </div>
              <p class="text-gray-500 leading-relaxed">{{ guide.desc }}</p>
              <pre class="bg-gray-50/80 rounded p-2 text-xs text-gray-600 whitespace-pre-wrap font-mono leading-relaxed border border-gray-100">{{ guide.example }}</pre>
            </div>
          </div>
        </div>
      </div>
      <div class="flex justify-end gap-3 mt-6">
        <GlassButton variant="secondary" @click="showCreateSpecModal = false">
          {{ t('common.cancel') }}
        </GlassButton>
        <GlassButton
          :disabled="!newSpecTitle.trim()"
          @click="handleCreateSpec"
        >
          {{ t('common.create') }}
        </GlassButton>
      </div>
    </Modal>

    <!-- Create Dev Task Modal -->
    <Modal :show="showCreateDevTaskModal" :title="t('task.newDevTask')" @close="showCreateDevTaskModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('common.title') }}</label>
          <input
            v-model="newDevTaskTitle"
            type="text"
            :placeholder="t('task.devTaskTitle')"
            class="input-glass"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('task.specVersion') }}</label>
          <select
            v-model="newDevTaskSpecVersionId"
            class="select-glass"
          >
            <option value="">{{ t('task.selectVersion') }}</option>
            <option v-for="sv in allSpecVersions" :key="sv.id" :value="sv.id">{{ sv.label }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('task.estimateHours') }}</label>
          <input
            v-model.number="newDevTaskEstimate"
            type="number"
            min="0"
            :placeholder="t('task.optional')"
            class="input-glass"
          />
        </div>
      </div>
      <div class="flex justify-end gap-3 mt-6">
        <GlassButton variant="secondary" @click="showCreateDevTaskModal = false">
          {{ t('common.cancel') }}
        </GlassButton>
        <GlassButton
          :disabled="!newDevTaskTitle.trim() || !newDevTaskSpecVersionId"
          @click="handleCreateDevTask"
        >
          {{ t('common.create') }}
        </GlassButton>
      </div>
    </Modal>

    <!-- Create Test Task Modal -->
    <Modal :show="showCreateTestTaskModal" :title="t('task.newTestTask')" @close="showCreateTestTaskModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('common.title') }}</label>
          <input
            v-model="newTestTaskTitle"
            type="text"
            :placeholder="t('task.testTaskTitle')"
            class="input-glass"
            @keyup.enter="handleCreateTestTask"
          />
        </div>
      </div>
      <div class="flex justify-end gap-3 mt-6">
        <GlassButton variant="secondary" @click="showCreateTestTaskModal = false">
          {{ t('common.cancel') }}
        </GlassButton>
        <GlassButton
          :disabled="!newTestTaskTitle.trim()"
          @click="handleCreateTestTask"
        >
          {{ t('common.create') }}
        </GlassButton>
      </div>
    </Modal>

    <!-- Edit Requirement Modal -->
    <Modal :show="showEditReqModal" :title="t('requirement.editRequirement')" @close="showEditReqModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('common.title') }}</label>
          <input
            v-model="editReqTitle"
            type="text"
            :placeholder="t('requirement.requirementTitle')"
            class="input-glass"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('common.priority') }}</label>
          <select v-model="editReqPriority" class="select-glass">
            <option value="low">{{ t('priority.low') }}</option>
            <option value="medium">{{ t('priority.medium') }}</option>
            <option value="high">{{ t('priority.high') }}</option>
            <option value="critical">{{ t('priority.critical') }}</option>
          </select>
        </div>
      </div>
      <div class="flex justify-end gap-3 mt-6">
        <GlassButton variant="secondary" @click="showEditReqModal = false">{{ t('common.cancel') }}</GlassButton>
        <GlassButton :disabled="!editReqTitle.trim()" @click="handleEditReq">{{ t('common.save') }}</GlassButton>
      </div>
    </Modal>

    <!-- Edit Dev Task Modal -->
    <Modal :show="showEditDevTaskModal" :title="t('task.editDevTask')" @close="showEditDevTaskModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('common.title') }}</label>
          <input
            v-model="editDevTaskTitle"
            type="text"
            :placeholder="t('task.devTaskTitle')"
            class="input-glass"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('task.estimateHours') }}</label>
          <input
            v-model.number="editDevTaskEstimate"
            type="number"
            min="0"
            :placeholder="t('task.optional')"
            class="input-glass"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('task.assignee') }}</label>
          <select v-model="editDevTaskAssigneeId" class="select-glass">
            <option :value="null">{{ t('task.unassigned') }}</option>
            <option v-for="m in teamMembers" :key="m.user_id" :value="m.user_id">
              {{ m.user.display_name || m.user.username }}
            </option>
          </select>
        </div>
      </div>
      <div class="flex justify-end gap-3 mt-6">
        <GlassButton variant="secondary" @click="showEditDevTaskModal = false">{{ t('common.cancel') }}</GlassButton>
        <GlassButton :disabled="!editDevTaskTitle.trim()" @click="handleEditDevTask">{{ t('common.save') }}</GlassButton>
      </div>
    </Modal>

    <!-- Delete Dev Task Confirmation -->
    <Modal :show="showDeleteDevTaskConfirm" :title="t('task.deleteDevTask')" @close="showDeleteDevTaskConfirm = false">
      <p class="text-sm text-gray-600">
        {{ t('task.deleteDevTaskConfirm', { title: deleteDevTaskTitle }) }}
      </p>
      <div class="flex justify-end gap-3 mt-6">
        <GlassButton variant="secondary" @click="showDeleteDevTaskConfirm = false">{{ t('common.cancel') }}</GlassButton>
        <GlassButton variant="danger" @click="handleDeleteDevTask">{{ t('common.delete') }}</GlassButton>
      </div>
    </Modal>

    <!-- Edit Test Case Modal -->
    <Modal :show="showEditTcModal" :title="t('testcase.editTestCase')" @close="showEditTcModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('common.title') }}</label>
          <input
            v-model="editTcTitle"
            type="text"
            :placeholder="t('testcase.testCaseTitle')"
            class="input-glass"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('testcase.preconditions') }}</label>
          <textarea
            v-model="editTcPreconditions"
            :placeholder="t('testcase.preconditionsPlaceholder')"
            class="input-glass"
            rows="2"
          ></textarea>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('testcase.steps') }}</label>
          <textarea
            v-model="editTcSteps"
            :placeholder="t('testcase.stepsPlaceholder')"
            class="input-glass"
            rows="3"
          ></textarea>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('testcase.expectedResult') }}</label>
          <textarea
            v-model="editTcExpected"
            :placeholder="t('testcase.expectedResultPlaceholder')"
            class="input-glass"
            rows="2"
          ></textarea>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ t('testcase.actualResult') }}</label>
          <textarea
            v-model="editTcActual"
            :placeholder="t('testcase.actualResultPlaceholder')"
            class="input-glass"
            rows="2"
          ></textarea>
        </div>
      </div>
      <div class="flex justify-end gap-3 mt-6">
        <GlassButton variant="secondary" @click="showEditTcModal = false">{{ t('common.cancel') }}</GlassButton>
        <GlassButton :disabled="!editTcTitle.trim()" @click="handleEditTc">{{ t('common.save') }}</GlassButton>
      </div>
    </Modal>

    <!-- Delete Test Case Confirmation -->
    <Modal :show="showDeleteTcConfirm" :title="t('testcase.deleteTestCase')" @close="showDeleteTcConfirm = false">
      <p class="text-sm text-gray-600">
        {{ t('testcase.deleteTestCaseConfirm', { title: deleteTcTitle }) }}
      </p>
      <div class="flex justify-end gap-3 mt-6">
        <GlassButton variant="secondary" @click="showDeleteTcConfirm = false">{{ t('common.cancel') }}</GlassButton>
        <GlassButton variant="danger" @click="handleDeleteTc">{{ t('common.delete') }}</GlassButton>
      </div>
    </Modal>
  </div>
</template>
