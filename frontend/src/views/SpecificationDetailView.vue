<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useSpecificationStore } from '@/stores/specification'
import StatusBadge from '@/components/StatusBadge.vue'
import EmptyState from '@/components/EmptyState.vue'
import Modal from '@/components/Modal.vue'
import type { Severity, ClauseCategory } from '@/types'

const route = useRoute()
const specStore = useSpecificationStore()

const reqId = computed(() => route.params.reqId as string)
const specId = computed(() => route.params.specId as string)

const loading = ref(false)
const error = ref('')

// Editing state
const editingVersionId = ref<string | null>(null)
const editContent = ref('')

// Add clause modal
const showAddClauseModal = ref(false)
const newClauseId = ref('')
const newClauseTitle = ref('')
const newClauseDescription = ref('')
const newClauseCategory = ref<ClauseCategory>('functional')
const newClauseSeverity = ref<Severity>('must')

const currentSpec = computed(() => specStore.currentSpec)

const severityOptions: Severity[] = ['must', 'should', 'may']
const categoryOptions: ClauseCategory[] = ['functional', 'validation', 'security', 'performance', 'ui_element']

const specTypeColorMap: Record<string, string> = {
  api: 'bg-gradient-to-br from-indigo-50 to-indigo-100/50 text-indigo-700 border-indigo-200/60',
  data: 'bg-gradient-to-br from-teal-50 to-teal-100/50 text-teal-700 border-teal-200/60',
  flow: 'bg-gradient-to-br from-amber-50 to-amber-100/50 text-amber-700 border-amber-200/60',
  ui: 'bg-gradient-to-br from-pink-50 to-pink-100/50 text-pink-700 border-pink-200/60',
}

const severityColorMap: Record<string, string> = {
  must: 'bg-gradient-to-br from-red-50 to-red-100/50 text-red-700 border-red-200/60',
  should: 'bg-gradient-to-br from-amber-50 to-amber-100/50 text-amber-700 border-amber-200/60',
  may: 'bg-gradient-to-br from-gray-50 to-gray-100/50 text-gray-600 border-gray-200/60',
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString()
}

async function loadAll() {
  loading.value = true
  error.value = ''
  try {
    await specStore.fetchList(reqId.value)
    const spec = specStore.specs.find((s) => s.id === specId.value)
    if (spec) {
      specStore.currentSpec = spec
    }
    await specStore.fetchVersions(specId.value)
  } catch (e: any) {
    error.value = e?.message || 'Failed to load specification'
  } finally {
    loading.value = false
  }
}

function startEdit(version: { id: string; content: Record<string, unknown> }) {
  editingVersionId.value = version.id
  editContent.value = JSON.stringify(version.content, null, 2)
}

function cancelEdit() {
  editingVersionId.value = null
  editContent.value = ''
}

async function saveContent() {
  if (!editingVersionId.value) return
  try {
    const parsed = JSON.parse(editContent.value)
    await specStore.createVersion(specId.value, parsed)
    await specStore.fetchVersions(specId.value)
    editingVersionId.value = null
  } catch (e: any) {
    error.value = e?.message || 'Invalid JSON content'
  }
}

async function handleLock(versionId: string) {
  try {
    await specStore.lock(versionId)
  } catch (e: any) {
    error.value = e?.message || 'Failed to lock version'
  }
}

async function handleReject(versionId: string) {
  try {
    await specStore.reject(versionId)
  } catch (e: any) {
    error.value = e?.message || 'Failed to reject version'
  }
}

async function selectVersionForClauses(versionId: string) {
  await specStore.fetchClauses(versionId)
  specStore.currentVersion = specStore.versions.find((v) => v.id === versionId) ?? null
}

function openAddClauseModal() {
  newClauseId.value = ''
  newClauseTitle.value = ''
  newClauseDescription.value = ''
  newClauseCategory.value = 'functional'
  newClauseSeverity.value = 'must'
  showAddClauseModal.value = true
}

async function handleAddClause() {
  if (!newClauseId.value.trim() || !newClauseTitle.value.trim() || !specStore.currentVersion) return
  try {
    await specStore.createClause(specStore.currentVersion.id, {
      clause_id: newClauseId.value.trim(),
      title: newClauseTitle.value.trim(),
      description: newClauseDescription.value.trim(),
      category: newClauseCategory.value,
      severity: newClauseSeverity.value,
    })
    showAddClauseModal.value = false
  } catch (e: any) {
    error.value = e?.message || 'Failed to create clause'
  }
}

onMounted(loadAll)
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- Loading -->
    <div v-if="loading" class="py-12 text-center text-gray-500">Loading...</div>

    <!-- Error -->
    <div v-else-if="error" class="p-3 bg-red-50 border border-red-200/60 rounded-[14px] text-red-700 text-sm mb-4">
      {{ error }}
    </div>

    <EmptyState v-else-if="!currentSpec" title="Specification not found" />

    <template v-else>
      <!-- Header -->
      <div class="mb-6">
        <h1 class="text-xl font-bold text-gray-900 mb-1">{{ currentSpec.title }}</h1>
        <span :class="['badge-base', specTypeColorMap[currentSpec.spec_type] ?? 'bg-gray-50 text-gray-600 border-gray-200/60']">
          {{ currentSpec.spec_type.toUpperCase() }}
        </span>
      </div>

      <!-- Version list -->
      <div class="mb-8">
        <h2 class="text-sm font-bold text-gray-900 mb-3">Versions</h2>
        <div v-if="specStore.versions.length === 0" class="text-sm text-gray-500 py-4">No versions yet.</div>
        <div v-else class="space-y-3">
          <div v-for="ver in specStore.versions" :key="ver.id" class="glass-card overflow-hidden">
            <div class="flex items-center justify-between px-5 py-3">
              <div class="flex items-center gap-3">
                <span class="font-medium text-gray-900 text-sm">Version {{ ver.version }}</span>
                <StatusBadge :status="ver.status" size="sm" />
                <span class="text-xs text-gray-400">{{ formatDate(ver.created_at) }}</span>
              </div>
              <div class="flex items-center gap-2">
                <template v-if="ver.status === 'draft'">
                  <button v-if="editingVersionId !== ver.id" class="btn-ghost px-3 py-1.5 text-xs" @click="startEdit(ver)">Edit Content</button>
                  <button class="btn-ghost px-3 py-1.5 text-xs" @click="selectVersionForClauses(ver.id)">View Clauses</button>
                  <button class="px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-50 border border-amber-200/60 rounded-[10px] hover:bg-amber-100 transition-colors cursor-pointer" @click="specStore.submitForReview(ver.id)">Submit for Review</button>
                </template>
                <template v-if="ver.status === 'reviewing'">
                  <button class="px-3 py-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200/60 rounded-[10px] hover:bg-emerald-100 transition-colors cursor-pointer" @click="handleLock(ver.id)">Lock</button>
                  <button class="px-3 py-1.5 text-xs font-medium text-red-700 bg-red-50 border border-red-200/60 rounded-[10px] hover:bg-red-100 transition-colors cursor-pointer" @click="handleReject(ver.id)">Reject</button>
                  <button class="btn-ghost px-3 py-1.5 text-xs" @click="selectVersionForClauses(ver.id)">View Clauses</button>
                </template>
                <template v-if="ver.status === 'locked' || ver.status === 'rejected'">
                  <button class="btn-ghost px-3 py-1.5 text-xs" @click="selectVersionForClauses(ver.id)">View Clauses</button>
                </template>
              </div>
            </div>
            <div v-if="editingVersionId === ver.id" class="border-t border-blue-500/5 px-5 py-3 bg-blue-500/[0.01]">
              <textarea v-model="editContent" class="input-glass font-mono h-64 resize-y" placeholder="JSON content" />
              <div class="flex items-center justify-end gap-2 mt-2">
                <button class="btn-secondary px-3 py-1.5 text-xs" @click="cancelEdit">Cancel</button>
                <button class="btn-primary px-3 py-1.5 text-xs" @click="saveContent">Save as New Version</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Clauses section -->
      <div v-if="specStore.currentVersion">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-sm font-bold text-gray-900">Clauses (Version {{ specStore.currentVersion.version }})</h2>
          <button v-if="specStore.currentVersion.status === 'draft'" class="btn-primary px-4 py-2 text-sm" @click="openAddClauseModal">Add Clause</button>
        </div>
        <EmptyState v-if="specStore.clauses.length === 0" title="No clauses" description="Add clauses to define specific requirements within this version." :action-label="specStore.currentVersion.status === 'draft' ? 'Add Clause' : undefined" @action="openAddClauseModal" />
        <div v-else class="glass-card overflow-hidden">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-blue-500/5 bg-blue-500/[0.02]">
                <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Clause ID</th>
                <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Title</th>
                <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Category</th>
                <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Severity</th>
                <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Description</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-blue-500/5">
              <tr v-for="clause in specStore.clauses" :key="clause.id" class="hover:bg-blue-500/[0.01] transition-colors">
                <td class="px-5 py-3 font-mono text-xs text-gray-600">{{ clause.clause_id }}</td>
                <td class="px-5 py-3 font-medium text-gray-900">{{ clause.title }}</td>
                <td class="px-5 py-3 text-gray-500">{{ clause.category }}</td>
                <td class="px-5 py-3">
                  <span :class="['badge-base', severityColorMap[clause.severity] ?? 'bg-gray-50 text-gray-600 border-gray-200/60']">
                    {{ clause.severity.toUpperCase() }}
                  </span>
                </td>
                <td class="px-5 py-3 text-gray-600 max-w-xs truncate">{{ clause.description }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Add Clause Modal -->
      <Modal :show="showAddClauseModal" title="Add Clause" @close="showAddClauseModal = false">
        <div class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-gray-600 mb-1.5">Clause ID</label>
            <input v-model="newClauseId" type="text" placeholder="e.g. REQ-001" class="input-glass" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-600 mb-1.5">Title</label>
            <input v-model="newClauseTitle" type="text" placeholder="Clause title" class="input-glass" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-600 mb-1.5">Description</label>
            <textarea v-model="newClauseDescription" placeholder="Clause description" class="input-glass resize-y" rows="3" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-gray-600 mb-1.5">Category</label>
              <select v-model="newClauseCategory" class="select-glass">
                <option v-for="cat in categoryOptions" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-600 mb-1.5">Severity</label>
              <select v-model="newClauseSeverity" class="select-glass">
                <option v-for="sev in severityOptions" :key="sev" :value="sev">{{ sev.toUpperCase() }}</option>
              </select>
            </div>
          </div>
        </div>
        <template #footer>
          <button class="btn-secondary px-4 py-2 text-sm" @click="showAddClauseModal = false">Cancel</button>
          <button class="btn-primary px-5 py-2 text-sm" :disabled="!newClauseId.trim() || !newClauseTitle.trim()" @click="handleAddClause">Add Clause</button>
        </template>
      </Modal>
    </template>
  </div>
</template>
