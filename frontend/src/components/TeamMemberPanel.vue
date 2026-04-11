<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { teamApi, userApi } from '@/api/endpoints'
import Modal from '@/components/Modal.vue'
import GlassButton from '@/components/GlassButton.vue'
import type { TeamMemberDetail, User } from '@/types'

const props = defineProps<{
  teamId: string
}>()

defineEmits<{
  (e: 'changed'): void
}>()

const { t } = useI18n()

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

function displayName(member: TeamMemberDetail): string {
  return member.user?.display_name || member.user?.username || member.user_id
}

function displayAvatar(member: TeamMemberDetail): string {
  const name = displayName(member)
  return name.slice(0, 2).toUpperCase()
}

function roleLabel(role: string): string {
  const map: Record<string, string> = {
    team_admin: t('team.teamAdmin'),
    product_owner: t('team.productOwner'),
    designer: t('team.designer'),
    developer: t('team.developer'),
    tester: t('team.tester'),
    viewer: t('team.viewer'),
  }
  return map[role] || role
}

async function loadMembers() {
  loading.value = true
  error.value = ''
  try {
    const res = await teamApi.membersDetail(props.teamId)
    members.value = res.data
  } catch {
    error.value = t('team.failedLoadMembers')
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
      addError.value = t('team.selectUser')
      return
    }
    await teamApi.addMember(props.teamId, {
      user_id: selectedUser.value.id,
      roles: addForm.value.roles,
    })
    await loadMembers()
    showAddModal.value = false
  } catch (err: any) {
    addError.value = err?.response?.data?.detail || err?.message || t('team.failedAddMember')
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
    await teamApi.removeMember(props.teamId, removingMember.value.user_id)
    await loadMembers()
    showRemoveModal.value = false
    removingMember.value = null
  } catch {
    error.value = t('team.failedRemoveMember')
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
    await teamApi.updateMember(props.teamId, editingMember.value.user_id, {
      roles: editRole.value,
    })
    await loadMembers()
    showRoleModal.value = false
    editingMember.value = null
  } catch {
    error.value = t('team.failedUpdateRole')
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

watch(() => props.teamId, () => loadMembers(), { immediate: true })
</script>

<template>
  <div class="border-t border-blue-500/5">
    <div v-if="error" class="px-5 py-2">
      <p class="text-sm text-red-600">{{ error }}</p>
    </div>

    <div v-if="loading" data-testid="member-loading" class="px-5 py-3 space-y-2">
      <div v-for="i in 3" :key="i" class="flex items-center gap-3 animate-pulse">
        <div class="h-6 w-6 bg-gray-200/50 rounded-full" />
        <div class="h-3 bg-gray-200/50 rounded w-1/3" />
      </div>
    </div>

    <div v-else-if="members.length === 0" data-testid="no-members" class="px-5 py-3 text-center">
      <p class="text-xs text-gray-400">{{ t('team.noMembers') }}</p>
    </div>

    <div v-else class="divide-y divide-blue-500/3">
      <div
        v-for="member in members"
        :key="member.id"
        data-testid="member-row"
        class="px-5 py-2 flex items-center justify-between hover:bg-blue-500/[0.01] transition-colors"
      >
        <div class="flex items-center gap-2.5 min-w-0">
          <div class="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-[10px] font-medium text-white flex-shrink-0">
            {{ displayAvatar(member) }}
          </div>
          <div class="min-w-0">
            <span class="text-xs font-medium text-gray-800 truncate block">{{ displayName(member) }}</span>
            <span class="text-[10px] text-gray-400">{{ member.user?.email }}</span>
          </div>
        </div>
        <div class="flex items-center gap-2 flex-shrink-0">
          <button
            class="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors cursor-pointer capitalize"
            @click="openRoleModal(member)"
          >
            {{ roleLabel(member.roles) }}
          </button>
          <button
            class="text-[10px] text-red-400 hover:text-red-600 transition-colors cursor-pointer"
            @click="openRemoveModal(member)"
          >
            {{ t('team.remove') }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="!loading" class="px-5 py-2 border-t border-blue-500/3">
      <button
        data-testid="add-member-btn"
        class="text-xs text-blue-500 hover:text-blue-700 transition-colors cursor-pointer"
        @click="openAddModal"
      >
        + {{ t('team.addMember') }}
      </button>
    </div>

    <!-- Add Member Modal -->
    <Modal :show="showAddModal" :title="t('team.addMember')" @close="showAddModal = false">
      <form data-testid="add-member-modal" @submit.prevent="handleAddMember" class="space-y-4">
        <div v-if="addError" class="p-3 bg-red-50 border border-red-200/60 rounded-[10px] text-sm text-red-700">
          {{ addError }}
        </div>

        <div>
          <label class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('team.selectUser') }}</label>
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
              :placeholder="t('team.searchUsersPlaceholder')"
              :value="searchQuery"
              @input="onSearchInput(($event.target as HTMLInputElement).value)"
            />
            <div v-if="searching" class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">
              {{ t('team.loadingMembers') }}
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
              {{ t('team.noUsersFound') }}
            </div>
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('team.role') }}</label>
          <select v-model="addForm.roles" data-testid="role-select" class="select-glass">
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
            {{ adding ? t('team.adding') : t('team.addMember') }}
          </GlassButton>
        </div>
      </form>
    </Modal>

    <!-- Remove Member Modal -->
    <Modal :show="showRemoveModal" :title="t('team.confirmRemove')" @close="showRemoveModal = false">
      <div data-testid="remove-modal" class="space-y-4">
        <p class="text-sm text-gray-600">{{ t('team.confirmRemoveMsg') }}</p>
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
            {{ t('team.removeMember') }}
          </GlassButton>
        </div>
      </div>
    </Modal>

    <!-- Update Role Modal -->
    <Modal :show="showRoleModal" :title="t('team.updateRole')" @close="showRoleModal = false">
      <form data-testid="role-modal" @submit.prevent="handleUpdateRole" class="space-y-4">
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
          <label class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('team.role') }}</label>
          <select v-model="editRole" class="select-glass">
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
            {{ t('team.updateRole') }}
          </GlassButton>
        </div>
      </form>
    </Modal>
  </div>
</template>
