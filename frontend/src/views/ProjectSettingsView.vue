<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import Modal from '@/components/Modal.vue'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id as string
const projectStore = useProjectStore()

const loading = ref(true)
const error = ref('')

// Form state
const formName = ref('')
const formSlug = ref('')
const formDesc = ref('')
const saving = ref(false)
const saveError = ref('')
const saveSuccess = ref(false)

// Delete confirmation modal state
const showDeleteModal = ref(false)
const deleteConfirm = ref('')
const deleting = ref(false)
const deleteError = ref('')

const project = computed(() => projectStore.currentProject)

function populateForm() {
  if (project.value) {
    formName.value = project.value.name
    formSlug.value = project.value.slug
    formDesc.value = project.value.description || ''
  }
}

async function handleSave() {
  saveError.value = ''
  saveSuccess.value = false
  saving.value = true
  try {
    if (!formName.value.trim()) {
      saveError.value = 'Project name is required.'
      return
    }
    await projectStore.update(projectId, {
      name: formName.value.trim(),
      slug: formSlug.value.trim(),
      description: formDesc.value || undefined,
    })
    saveSuccess.value = true
    setTimeout(() => { saveSuccess.value = false }, 3000)
  } catch (err: any) {
    saveError.value = err?.response?.data?.detail || err?.message || 'Failed to save settings.'
  } finally {
    saving.value = false
  }
}

function openDeleteModal() {
  deleteConfirm.value = ''
  deleteError.value = ''
  showDeleteModal.value = true
}

async function handleDelete() {
  deleteError.value = ''
  if (deleteConfirm.value !== project.value?.name) {
    deleteError.value = 'Project name does not match.'
    return
  }
  deleting.value = true
  try {
    await projectStore.remove(projectId)
    showDeleteModal.value = false
    router.push({ name: 'projects' })
  } catch (err: any) {
    deleteError.value = err?.response?.data?.detail || err?.message || 'Failed to delete project.'
  } finally {
    deleting.value = false
  }
}

onMounted(async () => {
  error.value = ''
  try {
    await projectStore.fetchOne(projectId)
    populateForm()
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Failed to load project.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-6 max-w-2xl">
    <!-- Error -->
    <div v-if="error" class="p-3 bg-red-50 border border-red-200/60 rounded-[10px] text-sm text-red-700">
      {{ error }}
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-6">
      <div class="glass-card p-6 space-y-4 animate-pulse">
        <div class="h-5 bg-gray-200/50 rounded w-1/3" />
        <div class="h-4 bg-gray-100/50 rounded w-full" />
        <div class="h-4 bg-gray-100/50 rounded w-2/3" />
      </div>
    </div>

    <template v-else-if="project">
      <!-- General settings -->
      <div class="glass-card overflow-hidden">
        <div class="px-6 py-4 border-b border-blue-500/8">
          <h2 class="text-sm font-bold text-gray-900">General</h2>
          <p class="text-xs text-gray-500 mt-0.5">Update your project settings.</p>
        </div>

        <form @submit.prevent="handleSave" class="px-6 py-5 space-y-5">
          <!-- Save feedback -->
          <div v-if="saveError" class="p-3 bg-red-50 border border-red-200/60 rounded-[10px] text-sm text-red-700">
            {{ saveError }}
          </div>
          <div v-if="saveSuccess" class="p-3 bg-green-50 border border-green-200/60 rounded-[10px] text-sm text-green-700">
            Settings saved successfully.
          </div>

          <div>
            <label for="settings-name" class="block text-xs font-semibold text-gray-600 mb-1.5">Project Name</label>
            <input
              id="settings-name"
              v-model="formName"
              type="text"
              required
              class="input-glass"
            />
          </div>

          <div>
            <label for="settings-slug" class="block text-xs font-semibold text-gray-600 mb-1.5">Slug</label>
            <input
              id="settings-slug"
              v-model="formSlug"
              type="text"
              required
              class="input-glass"
            />
          </div>

          <div>
            <label for="settings-desc" class="block text-xs font-semibold text-gray-600 mb-1.5">Description</label>
            <textarea
              id="settings-desc"
              v-model="formDesc"
              rows="4"
              class="input-glass resize-none"
              placeholder="Describe your project..."
            />
          </div>

          <div class="flex justify-end">
            <button
              type="submit"
              :disabled="saving"
              class="btn-primary px-5 py-2 text-sm"
            >
              {{ saving ? 'Saving...' : 'Save Changes' }}
            </button>
          </div>
        </form>
      </div>

      <!-- Danger zone -->
      <div class="bg-white/70 backdrop-blur-xl border border-red-200/60 rounded-[14px] shadow-glass-sm">
        <div class="px-6 py-4 border-b border-red-200/60">
          <h2 class="text-sm font-bold text-red-700">Danger Zone</h2>
          <p class="text-xs text-gray-500 mt-0.5">Irreversible actions for this project.</p>
        </div>

        <div class="px-6 py-5 flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-900">Delete this project</p>
            <p class="text-xs text-gray-500">Once deleted, there is no going back.</p>
          </div>
          <button
            class="btn-danger px-4 py-2 text-sm"
            @click="openDeleteModal"
          >
            Delete Project
          </button>
        </div>
      </div>
    </template>

    <!-- Delete confirmation modal -->
    <Modal :show="showDeleteModal" title="Delete Project" @close="showDeleteModal = false">
      <div class="space-y-4">
        <div v-if="deleteError" class="p-3 bg-red-50 border border-red-200/60 rounded-[10px] text-sm text-red-700">
          {{ deleteError }}
        </div>

        <p class="text-sm text-gray-700">
          This will permanently delete the project
          <strong class="text-gray-900">{{ project?.name }}</strong>
          and all associated data. This action cannot be undone.
        </p>

        <div>
          <label for="delete-confirm" class="block text-xs font-semibold text-gray-600 mb-1.5">
            Type <strong>{{ project?.name }}</strong> to confirm
          </label>
          <input
            id="delete-confirm"
            v-model="deleteConfirm"
            type="text"
            class="input-glass"
            :placeholder="project?.name"
          />
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <button
            type="button"
            class="btn-secondary px-4 py-2 text-sm"
            @click="showDeleteModal = false"
          >
            Cancel
          </button>
          <button
            type="button"
            :disabled="deleting || deleteConfirm !== project?.name"
            class="btn-danger px-4 py-2 text-sm"
            @click="handleDelete"
          >
            {{ deleting ? 'Deleting...' : 'Delete Project' }}
          </button>
        </div>
      </div>
    </Modal>
  </div>
</template>
