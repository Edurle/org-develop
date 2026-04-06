<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { orgApi, teamApi } from '@/api/endpoints'
import Modal from '@/components/Modal.vue'
import EmptyState from '@/components/EmptyState.vue'
import type { Organization, Team } from '@/types'

const { t } = useI18n()

const loading = ref(true)
const orgs = ref<Organization[]>([])
const teams = ref<Team[]>([])

// New org modal state
const showNewOrgModal = ref(false)
const orgForm = ref({ name: '', slug: '' })
const creatingOrg = ref(false)
const orgError = ref('')

// New team modal state
const showNewTeamModal = ref(false)
const teamForm = ref({ org_id: '', name: '', slug: '' })
const creatingTeam = ref(false)
const teamError = ref('')

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString()
}

function teamsForOrg(orgId: string): Team[] {
  return teams.value.filter((t) => t.org_id === orgId)
}

function openNewOrgModal() {
  orgForm.value = { name: '', slug: '' }
  orgError.value = ''
  showNewOrgModal.value = true
}

function openNewTeamModal(orgId?: string) {
  teamForm.value = { org_id: orgId || '', name: '', slug: '' }
  teamError.value = ''
  showNewTeamModal.value = true
}

async function handleCreateOrg() {
  orgError.value = ''
  creatingOrg.value = true
  try {
    const slug = orgForm.value.slug || orgForm.value.name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '')
    if (!orgForm.value.name.trim()) {
      orgError.value = t('team.organizationName')
      return
    }
    const res = await orgApi.create({ name: orgForm.value.name.trim(), slug })
    orgs.value.push(res.data)
    showNewOrgModal.value = false
  } catch (err: any) {
    orgError.value = err?.response?.data?.detail || err?.message || t('team.failedCreateOrg')
  } finally {
    creatingOrg.value = false
  }
}

async function handleCreateTeam() {
  teamError.value = ''
  creatingTeam.value = true
  try {
    const slug = teamForm.value.slug || teamForm.value.name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '')
    if (!teamForm.value.name.trim()) {
      teamError.value = t('team.teamNameRequired')
      return
    }
    if (!teamForm.value.org_id) {
      teamError.value = t('team.selectOrganization')
      return
    }
    const res = await teamApi.create({
      org_id: teamForm.value.org_id,
      name: teamForm.value.name.trim(),
      slug,
    })
    teams.value.push(res.data)
    showNewTeamModal.value = false
  } catch (err: any) {
    teamError.value = err?.response?.data?.detail || err?.message || t('team.failedCreateTeam')
  } finally {
    creatingTeam.value = false
  }
}

onMounted(async () => {
  try {
    const [orgRes, teamRes] = await Promise.all([
      orgApi.list(),
      teamApi.list(),
    ])
    orgs.value = orgRes.data
    teams.value = teamRes.data
  } catch {
    // partial data is fine
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">{{ t('team.title') }}</h1>
        <p class="mt-1 text-sm text-gray-500">{{ t('team.subtitle') }}</p>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-6">
      <div v-for="i in 2" :key="i" class="glass-card p-5 animate-pulse">
        <div class="h-5 bg-gray-200 rounded w-1/3 mb-4" />
        <div class="h-4 bg-gray-100 rounded w-1/4 mb-3" />
        <div class="h-3 bg-gray-100 rounded w-1/2" />
      </div>
    </div>

    <!-- Empty state -->
    <EmptyState
      v-else-if="orgs.length === 0"
      :title="t('team.noOrganizations')"
      :description="t('team.noOrganizationsDesc')"
      :action-label="t('team.newOrganization')"
      @action="openNewOrgModal"
    />

    <!-- Org + teams list -->
    <div v-else class="space-y-6">
      <div
        v-for="org in orgs"
        :key="org.id"
        class="glass-card overflow-hidden"
      >
        <!-- Org header -->
        <div class="flex items-center justify-between px-5 py-4 border-b border-blue-500/8">
          <div>
            <h2 class="text-sm font-bold text-gray-900">{{ org.name }}</h2>
            <p class="text-xs text-gray-400 mt-0.5">{{ org.slug }} &middot; {{ t('common.createdAt', { date: formatDate(org.created_at) }) }}</p>
          </div>
          <button
            class="btn-ghost px-3 py-1.5 text-xs"
            @click="openNewTeamModal(org.id)"
          >
            {{ t('team.addTeam') }}
          </button>
        </div>

        <!-- Teams under this org -->
        <div class="divide-y divide-blue-500/5">
          <div
            v-for="team in teamsForOrg(org.id)"
            :key="team.id"
            class="px-5 py-3 flex items-center justify-between hover:bg-blue-500/[0.01] transition-colors"
          >
            <div>
              <span class="text-sm font-medium text-gray-800">{{ team.name }}</span>
              <span class="text-xs text-gray-400 ml-2">{{ team.slug }}</span>
            </div>
            <span class="text-xs text-gray-400">{{ formatDate(team.created_at) }}</span>
          </div>
          <div
            v-if="teamsForOrg(org.id).length === 0"
            class="px-5 py-4 text-sm text-gray-400 text-center"
          >
            {{ t('team.noTeamsYet') }}
          </div>
        </div>
      </div>

      <!-- New org button at the bottom -->
      <div class="flex justify-center">
        <button
          class="btn-secondary px-5 py-2.5 text-sm"
          @click="openNewOrgModal"
        >
          {{ t('team.newOrganization') }}
        </button>
      </div>
    </div>

    <!-- New Org Modal -->
    <Modal :show="showNewOrgModal" :title="t('team.newOrganization')" @close="showNewOrgModal = false">
      <form @submit.prevent="handleCreateOrg" class="space-y-4">
        <div v-if="orgError" class="p-3 bg-red-50 border border-red-200/60 rounded-[10px] text-sm text-red-700">
          {{ orgError }}
        </div>

        <div>
          <label for="org-name" class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('common.name') }}</label>
          <input
            id="org-name"
            v-model="orgForm.name"
            type="text"
            required
            class="input-glass"
            placeholder="Acme Inc."
          />
        </div>

        <div>
          <label for="org-slug" class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('common.slug') }}</label>
          <input
            id="org-slug"
            v-model="orgForm.slug"
            type="text"
            class="input-glass"
            placeholder="auto-generated-from-name"
          />
          <p class="mt-1 text-xs text-gray-400">{{ t('common.autoSlug') }}</p>
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <button
            type="button"
            class="btn-secondary px-4 py-2 text-sm"
            @click="showNewOrgModal = false"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            type="submit"
            :disabled="creatingOrg"
            class="btn-primary px-5 py-2 text-sm"
          >
            {{ creatingOrg ? t('common.creating') : t('team.createOrganization') }}
          </button>
        </div>
      </form>
    </Modal>

    <!-- New Team Modal -->
    <Modal :show="showNewTeamModal" :title="t('team.newTeam')" @close="showNewTeamModal = false">
      <form @submit.prevent="handleCreateTeam" class="space-y-4">
        <div v-if="teamError" class="p-3 bg-red-50 border border-red-200/60 rounded-[10px] text-sm text-red-700">
          {{ teamError }}
        </div>

        <div>
          <label for="team-org" class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('team.title') }}</label>
          <select
            id="team-org"
            v-model="teamForm.org_id"
            required
            class="select-glass"
          >
            <option value="" disabled>{{ t('team.selectAnOrganization') }}</option>
            <option v-for="org in orgs" :key="org.id" :value="org.id">{{ org.name }}</option>
          </select>
        </div>

        <div>
          <label for="team-name" class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('common.name') }}</label>
          <input
            id="team-name"
            v-model="teamForm.name"
            type="text"
            required
            class="input-glass"
            placeholder="Backend Team"
          />
        </div>

        <div>
          <label for="team-slug" class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('common.slug') }}</label>
          <input
            id="team-slug"
            v-model="teamForm.slug"
            type="text"
            class="input-glass"
            placeholder="auto-generated-from-name"
          />
          <p class="mt-1 text-xs text-gray-400">{{ t('common.autoSlug') }}</p>
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <button
            type="button"
            class="btn-secondary px-4 py-2 text-sm"
            @click="showNewTeamModal = false"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            type="submit"
            :disabled="creatingTeam"
            class="btn-primary px-5 py-2 text-sm"
          >
            {{ creatingTeam ? t('common.creating') : t('team.createTeam') }}
          </button>
        </div>
      </form>
    </Modal>
  </div>
</template>
