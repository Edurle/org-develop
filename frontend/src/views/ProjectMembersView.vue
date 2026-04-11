<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useProjectStore } from '@/stores/project'
import { teamApi } from '@/api/endpoints'
import Modal from '@/components/Modal.vue'
import GlassButton from '@/components/GlassButton.vue'
import type { TeamMember } from '@/types'

const { t } = useI18n()
const route = useRoute()
const projectId = route.params.id as string

const projectStore = useProjectStore()

const loading = ref(true)
const error = ref('')
const members = ref<TeamMember[]>([])

// Add member modal state
const showAddModal = ref(false)
const addForm = ref({ user_id: '', roles: 'member' })
const adding = ref(false)
const addError = ref('')

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString()
}

async function loadMembers() {
  loading.value = true
  error.value = ''
  try {
    if (!projectStore.currentProject) {
      await projectStore.fetchOne(projectId)
    }
    const teamId = projectStore.currentProject?.team_id
    if (teamId) {
      const res = await teamApi.members(teamId)
      members.value = res.data
    }
  } catch (err: any) {
    error.value = err?.response?.data?.detail || t('project.failedLoadMembers')
  } finally {
    loading.value = false
  }
}

function openAddModal() {
  addForm.value = { user_id: '', roles: 'member' }
  addError.value = ''
  showAddModal.value = true
}

async function handleAddMember() {
  addError.value = ''
  adding.value = true
  try {
    if (!addForm.value.user_id.trim()) {
      addError.value = t('project.userIdRequired')
      return
    }
    const teamId = projectStore.currentProject?.team_id
    if (!teamId) {
      addError.value = t('project.projectTeamNotFound')
      return
    }
    const res = await teamApi.addMember(teamId, {
      user_id: addForm.value.user_id.trim(),
      roles: addForm.value.roles,
    })
    members.value.push(res.data)
    showAddModal.value = false
  } catch (err: any) {
    addError.value = err?.response?.data?.detail || err?.message || t('project.failedAddMember')
  } finally {
    adding.value = false
  }
}

onMounted(loadMembers)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">{{ t('project.members') }}</h1>
        <p class="mt-1 text-sm text-gray-500">{{ t('project.manageMembers') }}</p>
      </div>
      <GlassButton size="large" @click="openAddModal">
        {{ t('project.addMember') }}
      </GlassButton>
    </div>

    <!-- Error -->
    <div v-if="error" class="p-3 bg-red-50 border border-red-200/60 rounded-[10px] text-sm text-red-700">
      {{ error }}
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="glass-card overflow-hidden">
      <div class="divide-y divide-blue-500/5">
        <div v-for="i in 4" :key="i" class="px-5 py-4 animate-pulse flex items-center gap-4">
          <div class="h-8 w-8 bg-gray-200/50 rounded-full" />
          <div class="flex-1 space-y-2">
            <div class="h-4 bg-gray-200/50 rounded w-1/4" />
            <div class="h-3 bg-gray-100/50 rounded w-1/3" />
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="members.length === 0"
      class="glass-card px-5 py-12 text-center"
    >
      <p class="text-sm text-gray-500">{{ t('project.noMembers') }}</p>
    </div>

    <!-- Members table -->
    <div v-else class="glass-card overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-blue-500/5 bg-blue-500/[0.02]">
            <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">{{ t('project.userId') }}</th>
            <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">{{ t('project.role') }}</th>
            <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">{{ t('project.joined') }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-blue-500/5">
          <tr v-for="member in members" :key="member.id" class="hover:bg-blue-500/[0.01] transition-colors">
            <td class="px-5 py-3">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-xs font-medium text-white">
                  {{ member.user_id.slice(0, 2).toUpperCase() }}
                </div>
                <span class="text-gray-900 font-medium">{{ member.user_id }}</span>
              </div>
            </td>
            <td class="px-5 py-3 capitalize text-gray-600">{{ member.roles }}</td>
            <td class="px-5 py-3 text-gray-400">{{ formatDate(member.joined_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add Member Modal -->
    <Modal :show="showAddModal" :title="t('project.addMember')" @close="showAddModal = false">
      <form @submit.prevent="handleAddMember" class="space-y-4">
        <div v-if="addError" class="p-3 bg-red-50 border border-red-200/60 rounded-[10px] text-sm text-red-700">
          {{ addError }}
        </div>

        <div>
          <label for="member-user-id" class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('project.userId') }}</label>
          <input
            id="member-user-id"
            v-model="addForm.user_id"
            type="text"
            required
            class="input-glass"
            :placeholder="t('project.enterUserId')"
          />
        </div>

        <div>
          <label for="member-role" class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('project.role') }}</label>
          <select
            id="member-role"
            v-model="addForm.roles"
            class="select-glass"
          >
            <option value="admin">{{ t('project.admin') }}</option>
            <option value="member">{{ t('project.memberRole') }}</option>
            <option value="viewer">{{ t('project.viewer') }}</option>
          </select>
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <GlassButton
            variant="secondary"
            @click="showAddModal = false"
          >
            {{ t('common.cancel') }}
          </GlassButton>
          <GlassButton
            type="submit"
            :loading="adding"
          >
            {{ adding ? t('project.adding') : t('project.addMember') }}
          </GlassButton>
        </div>
      </form>
    </Modal>
  </div>
</template>
