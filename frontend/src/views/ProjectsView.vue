<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { teamApi } from '@/api/endpoints'
import Modal from '@/components/Modal.vue'
import EmptyState from '@/components/EmptyState.vue'
import type { Team } from '@/types'

const router = useRouter()
const projectStore = useProjectStore()

const loading = ref(true)
const teams = ref<Team[]>([])
const showNewModal = ref(false)

const form = ref({
  name: '',
  slug: '',
  description: '',
  team_id: '',
})
const creating = ref(false)
const createError = ref('')

const slugFromName = computed(() =>
  form.value.name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
)

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString()
}

function openNewModal() {
  form.value = { name: '', slug: '', description: '', team_id: '' }
  createError.value = ''
  showNewModal.value = true
}

async function handleCreate() {
  createError.value = ''
  creating.value = true
  try {
    const slug = form.value.slug || slugFromName.value
    if (!form.value.name.trim()) {
      createError.value = 'Project name is required.'
      return
    }
    if (!form.value.team_id) {
      createError.value = 'Please select a team.'
      return
    }
    const project = await projectStore.create({
      team_id: form.value.team_id,
      name: form.value.name.trim(),
      slug,
      description: form.value.description || undefined,
    })
    showNewModal.value = false
    router.push({ name: 'project-detail', params: { id: project.id } })
  } catch (err: any) {
    createError.value = err?.response?.data?.detail || err?.message || 'Failed to create project.'
  } finally {
    creating.value = false
  }
}

function goToProject(id: string) {
  router.push({ name: 'project-detail', params: { id } })
}

onMounted(async () => {
  try {
    await Promise.all([
      projectStore.fetchList(),
      teamApi.list().then((res) => { teams.value = res.data }),
    ])
  } catch {
    // data may still be partial
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
        <h1 class="text-xl font-bold text-gray-900">Projects</h1>
        <p class="mt-1 text-sm text-gray-500">Manage your projects across teams.</p>
      </div>
      <button class="btn-primary px-5 py-2.5 text-sm" @click="openNewModal">
        + New Project
      </button>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
      <div v-for="i in 6" :key="i" class="glass-card p-5 animate-pulse">
        <div class="h-5 bg-gray-200/50 rounded w-3/4 mb-3" />
        <div class="h-4 bg-gray-100/50 rounded w-1/3 mb-4" />
        <div class="h-3 bg-gray-100/50 rounded w-full mb-2" />
        <div class="h-3 bg-gray-100/50 rounded w-2/3" />
      </div>
    </div>

    <!-- Empty state -->
    <EmptyState
      v-else-if="projectStore.projects.length === 0"
      title="No projects yet"
      description="Create your first project to get started with requirements and tasks."
      action-label="New Project"
      @action="openNewModal"
    />

    <!-- Project grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
      <div
        v-for="(project, index) in projectStore.projects"
        :key="project.id"
        class="glass-card p-5 hover:shadow-glass-md hover:-translate-y-0.5 cursor-pointer"
        :style="{ animation: `fadeInUp 0.4s ease ${index * 80}ms both` }"
        @click="goToProject(project.id)"
      >
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-white font-bold text-sm shrink-0">
            {{ project.name.charAt(0).toUpperCase() }}
          </div>
          <div class="min-w-0">
            <h3 class="text-sm font-bold text-gray-900 truncate">{{ project.name }}</h3>
            <p class="text-[11px] text-gray-400">{{ formatDate(project.created_at) }}</p>
          </div>
        </div>
        <p v-if="project.description" class="text-xs text-gray-500 mb-3 line-clamp-2 leading-relaxed">
          {{ project.description }}
        </p>
        <div class="flex items-center justify-between pt-3 border-t border-blue-500/5">
          <span class="text-[11px] text-gray-400">{{ project.slug }}</span>
        </div>
      </div>
    </div>

    <!-- New Project Modal -->
    <Modal :show="showNewModal" title="New Project" @close="showNewModal = false">
      <form @submit.prevent="handleCreate" class="space-y-4">
        <div v-if="createError" class="p-3 bg-red-50 border border-red-200/60 rounded-[10px] text-sm text-red-700">
          {{ createError }}
        </div>
        <div>
          <label for="proj-name" class="block text-xs font-semibold text-gray-600 mb-1.5">Name</label>
          <input id="proj-name" v-model="form.name" type="text" required class="input-glass" placeholder="My Project" />
        </div>
        <div>
          <label for="proj-slug" class="block text-xs font-semibold text-gray-600 mb-1.5">Slug</label>
          <input id="proj-slug" v-model="form.slug" type="text" :placeholder="slugFromName || 'auto-generated-from-name'" class="input-glass" />
          <p class="mt-1 text-[11px] text-gray-400">Leave empty to auto-generate from name.</p>
        </div>
        <div>
          <label for="proj-desc" class="block text-xs font-semibold text-gray-600 mb-1.5">Description</label>
          <textarea id="proj-desc" v-model="form.description" rows="3" class="input-glass resize-none" placeholder="Optional project description..." />
        </div>
        <div>
          <label for="proj-team" class="block text-xs font-semibold text-gray-600 mb-1.5">Team</label>
          <select id="proj-team" v-model="form.team_id" required class="select-glass">
            <option value="" disabled>Select a team</option>
            <option v-for="team in teams" :key="team.id" :value="team.id">{{ team.name }}</option>
          </select>
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button type="button" class="btn-secondary px-4 py-2 text-sm" @click="showNewModal = false">Cancel</button>
          <button type="submit" :disabled="creating" class="btn-primary px-5 py-2 text-sm">
            {{ creating ? 'Creating...' : 'Create Project' }}
          </button>
        </div>
      </form>
    </Modal>
  </div>
</template>
