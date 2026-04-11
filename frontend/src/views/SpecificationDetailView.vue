<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useSpecificationStore } from '@/stores/specification'
import StatusBadge from '@/components/StatusBadge.vue'
import EmptyState from '@/components/EmptyState.vue'
import Modal from '@/components/Modal.vue'
import GlassButton from '@/components/GlassButton.vue'
import type { Severity, ClauseCategory, SpecClause } from '@/types'

const { t } = useI18n()
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

// Edit clause (reuses add clause modal)
const isEditingClause = ref(false)
const editClauseDbId = ref('')

// Delete clause confirmation
const showDeleteClauseConfirm = ref(false)
const deleteClauseDbId = ref('')
const deleteClauseTitle = ref('')

const currentSpec = computed(() => specStore.currentSpec)

const severityOptions: Severity[] = ['must', 'should', 'may']
const categoryOptions: ClauseCategory[] = ['functional', 'validation', 'security', 'performance', 'ui_element']

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
    error.value = e?.message || t('specification.errorLoadFailed')
  } finally {
    loading.value = false
  }
}

async function handleCreateVersion() {
  try {
    await specStore.createVersion(specId.value, {})
    await specStore.fetchVersions(specId.value)
  } catch (e: any) {
    error.value = e?.message || t('specification.errorLoadFailed')
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
    error.value = e?.message || t('specification.errorInvalidJson')
  }
}

async function handleLock(versionId: string) {
  try {
    await specStore.lock(versionId)
  } catch (e: any) {
    error.value = e?.message || t('specification.errorLockFailed')
  }
}

async function handleReject(versionId: string) {
  try {
    await specStore.reject(versionId)
  } catch (e: any) {
    error.value = e?.message || t('specification.errorRejectFailed')
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
    error.value = e?.message || t('specification.errorCreateClause')
  }
}

function openEditClauseModal(clause: SpecClause) {
  isEditingClause.value = true
  editClauseDbId.value = clause.id
  newClauseId.value = clause.clause_id
  newClauseTitle.value = clause.title
  newClauseDescription.value = clause.description
  newClauseCategory.value = clause.category
  newClauseSeverity.value = clause.severity
  showAddClauseModal.value = true
}

async function handleSaveClause() {
  if (isEditingClause.value) {
    try {
      await specStore.updateClause(editClauseDbId.value, {
        clause_id: newClauseId.value.trim(),
        title: newClauseTitle.value.trim(),
        description: newClauseDescription.value.trim(),
        category: newClauseCategory.value,
        severity: newClauseSeverity.value,
      })
      showAddClauseModal.value = false
      isEditingClause.value = false
    } catch (e: any) {
      error.value = e?.message || t('specification.errorUpdateClause')
    }
  } else {
    await handleAddClause()
  }
}

function closeClauseModal() {
  showAddClauseModal.value = false
  isEditingClause.value = false
}

function openDeleteClauseConfirm(clause: SpecClause) {
  deleteClauseDbId.value = clause.id
  deleteClauseTitle.value = clause.title
  showDeleteClauseConfirm.value = true
}

async function handleDeleteClause() {
  try {
    await specStore.removeClause(deleteClauseDbId.value)
    showDeleteClauseConfirm.value = false
  } catch (e: any) {
    error.value = e?.message || t('specification.errorDeleteClause')
  }
}

onMounted(loadAll)
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- Loading -->
    <div v-if="loading" class="py-12 text-center text-gray-500">{{ t('common.loading') }}</div>

    <!-- Error -->
    <div v-else-if="error" class="p-3 bg-red-50 border border-red-200/60 rounded-[14px] text-red-700 text-sm mb-4">
      {{ error }}
    </div>

    <EmptyState v-else-if="!currentSpec" :title="t('specification.specNotFound')" />

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
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-sm font-bold text-gray-900">{{ t('specification.versions') }}</h2>
          <GlassButton @click="handleCreateVersion">{{ t('specification.createVersion') }}</GlassButton>
        </div>
        <div v-if="specStore.versions.length === 0" class="text-sm text-gray-500 py-4">{{ t('specification.noVersions') }}</div>
        <div v-else class="space-y-3">
          <div v-for="ver in specStore.versions" :key="ver.id" class="glass-card overflow-hidden">
            <div class="flex items-center justify-between px-5 py-3">
              <div class="flex items-center gap-3">
                <span class="font-medium text-gray-900 text-sm">{{ t('specification.version', { n: ver.version }) }}</span>
                <StatusBadge :status="ver.status" size="sm" />
                <span class="text-xs text-gray-400">{{ formatDate(ver.created_at) }}</span>
              </div>
              <div class="flex items-center gap-2">
                <template v-if="ver.status === 'draft'">
                  <GlassButton v-if="editingVersionId !== ver.id" variant="ghost" size="small" @click="startEdit(ver)">{{ t('specification.editContent') }}</GlassButton>
                  <GlassButton variant="ghost" size="small" @click="selectVersionForClauses(ver.id)">{{ t('specification.viewClauses') }}</GlassButton>
                  <GlassButton variant="warning" size="small" @click="specStore.submitForReview(ver.id)">{{ t('specification.submitForReview') }}</GlassButton>
                </template>
                <template v-if="ver.status === 'reviewing'">
                  <GlassButton variant="success" size="small" @click="handleLock(ver.id)">{{ t('specification.lock') }}</GlassButton>
                  <GlassButton variant="danger" size="small" @click="handleReject(ver.id)">{{ t('specification.reject') }}</GlassButton>
                  <GlassButton variant="ghost" size="small" @click="selectVersionForClauses(ver.id)">{{ t('specification.viewClauses') }}</GlassButton>
                </template>
                <template v-if="ver.status === 'locked' || ver.status === 'rejected'">
                  <GlassButton variant="ghost" size="small" @click="selectVersionForClauses(ver.id)">{{ t('specification.viewClauses') }}</GlassButton>
                </template>
              </div>
            </div>
            <div v-if="editingVersionId === ver.id" class="border-t border-blue-500/5 px-5 py-3 bg-blue-500/[0.01]">
              <textarea id="spec-content" v-model="editContent" class="input-glass font-mono h-64 resize-y" :placeholder="t('specification.jsonContent')" />
              <div class="flex items-center justify-end gap-2 mt-2">
                <GlassButton variant="secondary" size="small" @click="cancelEdit">{{ t('common.cancel') }}</GlassButton>
                <GlassButton size="small" @click="saveContent">{{ t('specification.saveAsNewVersion') }}</GlassButton>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Clauses section -->
      <div v-if="specStore.currentVersion">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-sm font-bold text-gray-900">{{ t('specification.clauses') + ' (' + t('specification.version', { n: specStore.currentVersion.version }) + ')' }}</h2>
          <GlassButton v-if="specStore.currentVersion.status === 'draft'" @click="openAddClauseModal">{{ t('specification.addClause') }}</GlassButton>
        </div>
        <EmptyState v-if="specStore.clauses.length === 0" :title="t('specification.noClauses')" :description="t('specification.noClausesDesc')" :action-label="specStore.currentVersion.status === 'draft' ? t('specification.addClause') : undefined" @action="openAddClauseModal" />
        <div v-else class="glass-card overflow-hidden">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-blue-500/5 bg-blue-500/[0.02]">
                <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('specification.clauseId') }}</th>
                <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('common.title') }}</th>
                <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('common.type') }}</th>
                <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('specification.severityLabel') }}</th>
                <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('common.description') }}</th>
                <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('common.actions') }}</th>
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
                <td class="px-5 py-3">
                  <template v-if="specStore.currentVersion?.status === 'draft'">
                    <div class="flex items-center gap-2">
                      <GlassButton variant="ghost" size="small" @click="openEditClauseModal(clause)">{{ t('common.edit') }}</GlassButton>
                      <GlassButton variant="danger" size="small" @click="openDeleteClauseConfirm(clause)">{{ t('common.delete') }}</GlassButton>
                    </div>
                  </template>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Add/Edit Clause Modal -->
      <Modal :show="showAddClauseModal" :title="isEditingClause ? t('specification.editClause') : t('specification.addClause')" @close="closeClauseModal">
        <div class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('specification.clauseId') }}</label>
            <input id="clause-id" v-model="newClauseId" type="text" :placeholder="t('specification.clauseIdPlaceholder')" class="input-glass" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('specification.clauseTitle') }}</label>
            <input id="clause-title" v-model="newClauseTitle" type="text" :placeholder="t('specification.clauseTitle')" class="input-glass" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('specification.clauseDescription') }}</label>
            <textarea id="clause-description" v-model="newClauseDescription" :placeholder="t('specification.clauseDescription')" class="input-glass resize-y" rows="3" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('specification.category') }}</label>
              <select id="clause-category" v-model="newClauseCategory" class="select-glass">
                <option v-for="cat in categoryOptions" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-600 mb-1.5">{{ t('specification.severityLabel') }}</label>
              <select id="clause-severity" v-model="newClauseSeverity" class="select-glass">
                <option v-for="sev in severityOptions" :key="sev" :value="sev">{{ sev.toUpperCase() }}</option>
              </select>
            </div>
          </div>
        </div>
        <template #footer>
          <GlassButton variant="secondary" @click="closeClauseModal">{{ t('common.cancel') }}</GlassButton>
          <GlassButton :disabled="!newClauseId.trim() || !newClauseTitle.trim()" @click="handleSaveClause">{{ isEditingClause ? t('common.save') : t('specification.addClause') }}</GlassButton>
        </template>
      </Modal>

      <!-- Delete Clause Confirmation Modal -->
      <Modal :show="showDeleteClauseConfirm" :title="t('specification.deleteClause')" @close="showDeleteClauseConfirm = false">
        <p class="text-sm text-gray-600">
          {{ t('specification.deleteClauseConfirm', { title: deleteClauseTitle }) }}
        </p>
        <div class="flex justify-end gap-3 mt-6">
          <GlassButton variant="secondary" @click="showDeleteClauseConfirm = false">{{ t('common.cancel') }}</GlassButton>
          <GlassButton variant="danger" @click="handleDeleteClause">{{ t('common.delete') }}</GlassButton>
        </div>
      </Modal>
    </template>
  </div>
</template>
