<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useTaskStore } from '@/stores/task'
import StatusBadge from '@/components/StatusBadge.vue'
import EmptyState from '@/components/EmptyState.vue'
import GlassButton from '@/components/GlassButton.vue'

const { t } = useI18n()
const route = useRoute()
const taskStore = useTaskStore()

const projectId = computed(() => route.params.id as string)

const loading = ref(false)
const error = ref('')
const activeTab = ref<'dev' | 'test'>('dev')

const taskStatusOptions = ['open', 'in_progress', 'review', 'done', 'blocked']

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString()
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    await Promise.all([
      taskStore.fetchDevTasks(projectId.value),
      taskStore.fetchTestTasks(projectId.value),
    ])
  } catch (e: any) {
    error.value = e?.message || 'Failed to load tasks'
  } finally {
    loading.value = false
  }
}

async function handleClaim(taskId: string) {
  try {
    await taskStore.claimDevTask(taskId)
  } catch (e: any) {
    error.value = e?.message || 'Failed to claim task'
  }
}

async function handleStatusChange(taskId: string, status: string) {
  try {
    await taskStore.updateDevTaskStatus(taskId, status)
  } catch (e: any) {
    error.value = e?.message || 'Failed to update task status'
  }
}

onMounted(loadData)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-xl font-bold text-gray-900">{{ t('project.projectTasks') }}</h1>
    </div>

    <!-- Error -->
    <div v-if="error" class="p-3 bg-red-50 border border-red-200/60 rounded-[14px] text-sm text-red-700">
      {{ error }}
    </div>

    <!-- Tabs -->
    <div>
      <nav class="flex gap-3">
        <button
          :class="[
            'px-5 py-2.5 text-sm font-medium rounded-full border transition-all backdrop-blur-sm',
            activeTab === 'dev'
              ? 'bg-white/60 border-white/50 text-blue-600 shadow-[0_2px_8px_rgba(59,130,246,0.12)]'
              : 'bg-white/30 border-white/30 text-gray-500 hover:bg-white/40 hover:text-gray-700',
          ]"
          @click="activeTab = 'dev'"
        >
          {{ t('project.devTasksLabel') }} ({{ taskStore.devTasks.length }})
        </button>
        <button
          :class="[
            'px-5 py-2.5 text-sm font-medium rounded-full border transition-all backdrop-blur-sm',
            activeTab === 'test'
              ? 'bg-white/60 border-white/50 text-blue-600 shadow-[0_2px_8px_rgba(59,130,246,0.12)]'
              : 'bg-white/30 border-white/30 text-gray-500 hover:bg-white/40 hover:text-gray-700',
          ]"
          @click="activeTab = 'test'"
        >
          {{ t('project.testTasksLabel') }} ({{ taskStore.testTasks.length }})
        </button>
      </nav>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="py-12 text-center text-gray-500">{{ t('common.loading') }}</div>

    <!-- Dev Tasks Tab -->
    <template v-else-if="activeTab === 'dev'">
      <EmptyState
        v-if="taskStore.devTasks.length === 0"
        :title="t('task.noDevTasks')"
        :description="t('task.noDevTasksDesc')"
      />

      <div v-else class="glass-card overflow-hidden">
        <table class="w-full text-sm">
          <thead class="border-b border-blue-500/5 bg-blue-500/[0.02]">
            <tr>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('common.title') }}</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('common.status') }}</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('task.assignee') }}</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('task.estHours') }}</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('common.created') }}</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('common.actions') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-blue-500/5">
            <tr
              v-for="task in taskStore.devTasks"
              :key="task.id"
              class="hover:bg-blue-500/[0.01] transition-colors"
            >
              <td class="px-5 py-3 font-medium text-gray-900">{{ task.title }}</td>
              <td class="px-5 py-3">
                <StatusBadge :status="task.status" size="sm" />
              </td>
              <td class="px-5 py-3 text-gray-500">{{ task.assignee_id ?? t('task.unassigned') }}</td>
              <td class="px-5 py-3 text-gray-500">{{ task.estimate_hours ?? '-' }}</td>
              <td class="px-5 py-3 text-gray-500">{{ formatDate(task.created_at) }}</td>
              <td class="px-5 py-3">
                <div class="flex items-center gap-2">
                  <!-- Claim button for open tasks -->
                  <GlassButton
                    v-if="task.status === 'open'"
                    size="small"
                    @click="handleClaim(task.id)"
                  >
                    {{ t('task.claim') }}
                  </GlassButton>
                  <!-- Status dropdown for transitions -->
                  <select
                    id="task-status"
                    class="select-glass !w-auto !py-1.5 !px-2 text-xs"
                    :value="task.status"
                    @change="handleStatusChange(task.id, ($event.target as HTMLSelectElement).value)"
                  >
                    <option v-for="s in taskStatusOptions" :key="s" :value="s">
                      {{ s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) }}
                    </option>
                  </select>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- Test Tasks Tab -->
    <template v-else-if="activeTab === 'test'">
      <EmptyState
        v-if="taskStore.testTasks.length === 0"
        :title="t('task.noTestTasks')"
        :description="t('task.noTestTasksDesc')"
      />

      <div v-else class="glass-card overflow-hidden">
        <table class="w-full text-sm">
          <thead class="border-b border-blue-500/5 bg-blue-500/[0.02]">
            <tr>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('common.title') }}</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('common.status') }}</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('project.requirementCol') }}</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('common.created') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-blue-500/5">
            <tr
              v-for="task in taskStore.testTasks"
              :key="task.id"
              class="hover:bg-blue-500/[0.01] transition-colors"
            >
              <td class="px-5 py-3 font-medium text-gray-900">{{ task.title }}</td>
              <td class="px-5 py-3">
                <StatusBadge :status="task.status" size="sm" />
              </td>
              <td class="px-5 py-3">
                <router-link
                  :to="`/projects/${projectId}/requirements/${task.requirement_id}`"
                  class="text-blue-600 hover:text-blue-800 text-sm font-medium bg-white/40 border border-white/30 rounded-full px-3 py-1 backdrop-blur-sm transition-all"
                >
                  {{ task.requirement_id }}
                </router-link>
              </td>
              <td class="px-5 py-3 text-gray-500">{{ formatDate(task.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
