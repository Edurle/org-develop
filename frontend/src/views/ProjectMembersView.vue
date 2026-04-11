<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useProjectStore } from '@/stores/project'
import { teamApi, userApi } from '@/api/endpoints'
import Modal from '@/components/Modal.vue'
import GlassButton from '@/components/GlassButton.vue'
import type { TeamMemberDetail, User } from '@/types'

const { t } = useI18n()
const route = useRoute()
const projectId = route.params.id as string

const projectStore = useProjectStore()

const loading = ref(true)
const error = ref('')
const members = ref<TeamMemberDetail[]>([])

const showAddModal = ref(false)
const searchQuery = ref('')
const searchResults = ref<User[]>([])
const searching = ref(false)
const selectedUser = ref<User | null>(null)
const addForm = ref({ roles: 'developer' })
const adding = ref(false)
const addError = ref('')

const showRemoveModal = ref(false)
const removingMember = ref<TeamMemberDetail | null>(null)
const removing = ref(false)

const showRoleModal = ref(false)
const editingMember = ref<TeamMemberDetail | null>(null)
const editRole = ref('')
const updatingRole = ref(false)

const memberUserIds = computed(() => new Set(members.value.map((m) => m.user_id)))

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString()
}

function displayName(member: TeamMemberDetail): string {
  return member.user?.display_name || member.user?.username || member.user_id
}

function displayAvatar(member: TeamMemberDetail): string {
  const name = displayName(member)
  return name.slice(0, 2).toUpperCase()
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
      const res = await teamApi.membersDetail(teamId)
      members.value = res.data
    }
  } catch (err: any) {
    error.value = err?.response?.data?.detail || t('project.failedLoadMembers')
  } finally {
    loading.value = false
  }
}

async function searchUsers(query: string) {
  if (!query || query.length < 1) {
    searchResults.value = []
    return
  }
  searching.value = true
  try {
    const res = await userApi.list(query)
    searchResults.value = res.data.filter((u) => !memberUserIds.value.has(u.id))
  } catch {
    searchResults.value = []
  } finally {
    searching.value = false
  }
}

function openAddModal() {
  selectedUser.value = null
  searchQuery.value = ''
  searchResults.value = []
  addForm.value = { roles: 'developer' }
  addError.value = ''
  showAddModal.value = true
}

function selectUser(user: User) {
  selectedUser.value = user
  searchQuery.value = ''
  searchResults.value = []
}

function clearSelectedUser() {
  selectedUser.value = null
}

async function handleAddMember() {
  addError.value = ''
  adding.value = true
  try {
    if (!selectedUser.value) {
      addError.value = t('project.selectUser')
      return
    }
    const teamId = projectStore.currentProject?.team_id
    if (!teamId) {
      addError.value = t('project.projectTeamNotFound')
      return
    }
    await teamApi.addMember(teamId, {
      user_id: selectedUser.value.id,
      roles: addForm.value.roles,
    })
    await loadMembers()
    showAddModal.value = false
  } catch (err: any) {
    addError.value = err?.response?.data?.detail || err?.message || t('project.failedAddMember')
  } finally {
    adding.value = false
  }
}

function openRemoveModal(member: TeamMemberDetail) {
  removingMember.value = member
  showRemoveModal.value = true
}

async function handleRemoveMember() {
  if (!removingMember.value) return
  removing.value = true
  try {
    const teamId = projectStore.currentProject?.team_id
    if (!teamId) return
    await teamApi.removeMember(teamId, removingMember.value.user_id)
    await loadMembers()
    showRemoveModal.value = false
    removingMember.value = null
  } catch (err: any) {
    error.value = err?.response?.data?.detail || t('project.failedRemoveMember')
  } finally {
    removing.value = false
  }
}

function openRoleModal(member: TeamMemberDetail) {
  editingMember.value = member
  editRole.value = member.roles
  showRoleModal.value = true
}

async function handleUpdateRole() {
  if (!editingMember.value) return
  updatingRole.value = true
  try {
    const teamId = projectStore.currentProject?.team_id
    if (!teamId) return
    await teamApi.updateMember(teamId, editingMember.value.user_id, {
      roles: editRole.value,
    })
    await loadMembers()
    showRoleModal.value = false
    editingMember.value = null
  } catch (err: any) {
    error.value = err?.response?.data?.detail || t('project.failedUpdateRole')
  } finally {
    updatingRole.value = false
  }
}

let searchTimeout: ReturnType<typeof setTimeout> | null = null
function onSearchInput(val: string) {
  searchQuery.value = val
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => searchUsers(val), 300)
}

onMounted(loadMembers)
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">{{ t('project.members') }}</h1>
        <p class="mt-1 text-sm text-gray-500">{{ t('project.manageMembers') }}</p>
      </div>
      <GlassButton size="large" @click="openAddModal">
        {{ t('project.addMember') }}
      </GlassButton>
    </div>

    <div v-if="error" class="p-3 bg-red-50 border border-red-200/60 rounded-[10px] text-sm text-red-700">
      {{ error }}
    </div>

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

    <div v-else-if="members.length === 0" class="glass-card px-5 py-12 text-center">
      <p class="text-sm text-gray-500">{{ t('project.noMembers') }}</p>
    </div>

    <div v-else class="glass-card overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-blue-500/5 bg-blue-500/[0.02]">
            <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">{{ t('project.userId') }}</th>
            <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">{{ t('project.role') }}</th>
            <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">{{ t('project.joined') }}</th>
            <th class="px-5 py-3 text-right text-xs font-semibold text-gray-500"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-blue-500/5">
          <tr v-for="member in members" :key="member.id" class="hover:bg-blue-500/[0.01] transition-colors">
            <td class="px-5 py-3">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-xs font-medium text-white">
                  {{ displayAvatar(member) }}
                </div>
                <div>
                  <span class="text-gray-900 font-medium">{{ displayName(member) }}</span>
                  <p v-if="member.user?.email" class="text-xs text-gray-400">{{ member.user.email }}</p>
                </div>
              </div>
            </td>
            <td class="px-5 py-3">
              <button
                class="capitalize text-gray-600 hover:text-blue-600 transition-colors cursor-pointer"
                @click="openRoleModal(member)"
              >
                {{ member.roles }}
              </button>
            </td>
            <td class="px-5 py-3 text-gray-400">{{ formatDate(member.joined_at) }}</td>
            <td class="px-5 py-3 text-right">
              <button
                class="text-xs text-red-400 hover:text-red-600 transition-colors cursor-pointer"
                @click="openRemoveModal(member)"
              >
                {{ t('project.remove') }}
              </button>
            </td>
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
          <label class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('project.selectUser') }}</label>
          <div v-if="selectedUser" class="flex items-center gap-2 p-2 bg-blue-50 rounded-[10px]">
            <div class="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-xs font-medium text-white">
              {{ (selectedUser.display_name || selectedUser.username).slice(0, 2).toUpperCase() }}
            </div>
            <div class="flex-1">
              <p class="text-sm font-medium text-gray-900">{{ selectedUser.display_name || selectedUser.username }}</p>
              <p class="text-xs text-gray-400">{{ selectedUser.email }}</p>
            </div>
            <button type="button" class="text-gray-400 hover:text-gray-600 cursor-pointer" @click="clearSelectedUser">✕</button>
          </div>
          <div v-else class="relative">
            <input
              type="text"
              class="input-glass w-full"
              :placeholder="t('project.searchUsersPlaceholder')"
              :value="searchQuery"
              @input="onSearchInput(($event.target as HTMLInputElement).value)"
            />
            <div v-if="searching" class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
              {{ t('project.loadingUsers') }}
            </div>
            <div v-if="searchResults.length > 0" class="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-[10px] shadow-lg max-h-48 overflow-y-auto">
              <button
                v-for="u in searchResults"
                :key="u.id"
                type="button"
                class="w-full px-3 py-2 text-left hover:bg-blue-50 transition-colors flex items-center gap-2 cursor-pointer"
                @click="selectUser(u)"
              >
                <div class="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-xs font-medium text-white">
                  {{ (u.display_name || u.username).slice(0, 2).toUpperCase() }}
                </div>
                <div>
                  <p class="text-sm text-gray-900">{{ u.display_name || u.username }}</p>
                  <p class="text-xs text-gray-400">{{ u.email }}</p>
                </div>
              </button>
            </div>
            <div v-if="searchQuery && !searching && searchResults.length === 0 && !selectedUser" class="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-[10px] shadow-lg p-3 text-center text-sm text-gray-400">
              {{ t('project.noUsersFound') }}
            </div>
          </div>
        </div>

        <div>
          <label for="add-member-role" class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('project.role') }}</label>
          <select id="add-member-role" v-model="addForm.roles" class="select-glass">
            <option value="team_admin">{{ t('team.teamAdmin') }}</option>
            <option value="product_owner">{{ t('team.productOwner') }}</option>
            <option value="designer">{{ t('team.designer') }}</option>
            <option value="developer">{{ t('team.developer') }}</option>
            <option value="tester">{{ t('team.tester') }}</option>
            <option value="viewer">{{ t('team.viewer') }}</option>
          </select>
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <GlassButton variant="secondary" @click="showAddModal = false">
            {{ t('common.cancel') }}
          </GlassButton>
          <GlassButton type="submit" :loading="adding" :disabled="!selectedUser">
            {{ adding ? t('project.adding') : t('project.addMember') }}
          </GlassButton>
        </div>
      </form>
    </Modal>

    <!-- Remove Member Modal -->
    <Modal :show="showRemoveModal" :title="t('project.confirmRemove')" @close="showRemoveModal = false">
      <div class="space-y-4">
        <p class="text-sm text-gray-600">
          {{ t('project.confirmRemoveMsg') }}
        </p>
        <div v-if="removingMember" class="p-3 bg-red-50 rounded-[10px] flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-gradient-to-br from-red-400 to-red-500 flex items-center justify-center text-xs font-medium text-white">
            {{ displayAvatar(removingMember) }}
          </div>
          <div>
            <p class="text-sm font-medium text-gray-900">{{ displayName(removingMember) }}</p>
            <p class="text-xs text-gray-400">{{ removingMember.user?.email }}</p>
          </div>
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <GlassButton variant="secondary" @click="showRemoveModal = false">
            {{ t('common.cancel') }}
          </GlassButton>
          <GlassButton variant="danger" :loading="removing" @click="handleRemoveMember">
            {{ t('project.removeMember') }}
          </GlassButton>
        </div>
      </div>
    </Modal>

    <!-- Update Role Modal -->
    <Modal :show="showRoleModal" :title="t('project.updateRole')" @close="showRoleModal = false">
      <form @submit.prevent="handleUpdateRole" class="space-y-4">
        <div v-if="editingMember" class="p-3 bg-blue-50 rounded-[10px] flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-xs font-medium text-white">
            {{ displayAvatar(editingMember) }}
          </div>
          <div>
            <p class="text-sm font-medium text-gray-900">{{ displayName(editingMember) }}</p>
            <p class="text-xs text-gray-400">{{ editingMember.user?.email }}</p>
          </div>
        </div>

        <div>
          <label for="edit-role" class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('project.role') }}</label>
          <select id="edit-role" v-model="editRole" class="select-glass">
            <option value="team_admin">{{ t('team.teamAdmin') }}</option>
            <option value="product_owner">{{ t('team.productOwner') }}</option>
            <option value="designer">{{ t('team.designer') }}</option>
            <option value="developer">{{ t('team.developer') }}</option>
            <option value="tester">{{ t('team.tester') }}</option>
            <option value="viewer">{{ t('team.viewer') }}</option>
          </select>
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <GlassButton variant="secondary" @click="showRoleModal = false">
            {{ t('common.cancel') }}
          </GlassButton>
          <GlassButton type="submit" :loading="updatingRole">
            {{ t('project.updateRole') }}
          </GlassButton>
        </div>
      </form>
    </Modal>
  </div>
</template>
