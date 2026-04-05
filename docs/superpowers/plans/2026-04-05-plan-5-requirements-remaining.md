# Plan 5: Requirements, Specs & Remaining Pages

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the requirement list, requirement detail (with tabs and coverage), specification detail, coverage report, and teams pages with glass effects and new visual styles.

**Architecture:** All pages adopt glass-card containers, glass-wrapped tables with blue-tinted headers, input-glass/select-glass for forms, gradient severity badges, and progress bars with gradient fills. The teams page uses glass org cards.

**Tech Stack:** UnoCSS shortcuts (from Plan 1), Vue 3 SFC

**Depends on:** Plan 1 (theme tokens), Plan 2 (components)

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/src/views/RequirementListView.vue` | Modify | Glass table + glass filter bar |
| `frontend/src/views/RequirementDetailView.vue` | Modify | Glass tabs, cards, coverage |
| `frontend/src/views/SpecificationDetailView.vue` | Modify | Glass version cards, clause table |
| `frontend/src/views/CoverageReportView.vue` | Modify | Glass cards, gradient progress bars |
| `frontend/src/views/TeamsView.vue` | Modify | Glass org cards |

---

### Task 1: Requirements List Page

**Files:**
- Modify: `frontend/src/views/RequirementListView.vue`

- [ ] **Step 1: Update template with glass styles**

Replace the `<template>` section with:

```vue
<template>
  <div class="max-w-6xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-bold text-gray-900">Requirements</h1>
      <button class="btn-primary px-5 py-2.5 text-sm" @click="openCreateModal">
        New Requirement
      </button>
    </div>

    <!-- Error -->
    <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200/60 rounded-[14px] text-red-700 text-sm">
      {{ error }}
    </div>

    <!-- Filter bar -->
    <div class="flex items-center gap-3 mb-4">
      <select v-model="statusFilter" class="select-glass !w-auto" @change="applyFilters">
        <option value="">All Statuses</option>
        <option v-for="s in statusOptions" :key="s" :value="s">{{ s.replace(/_/g, ' ') }}</option>
      </select>
      <select v-model="iterationFilter" class="select-glass !w-auto" @change="applyFilters">
        <option value="">All Iterations</option>
        <option v-for="iter in iterStore.iterations" :key="iter.id" :value="iter.id">{{ iter.name }}</option>
      </select>
      <select v-model="priorityFilter" class="select-glass !w-auto">
        <option value="">All Priorities</option>
        <option v-for="p in priorityOptions" :key="p" :value="p">{{ p.charAt(0).toUpperCase() + p.slice(1) }}</option>
      </select>
      <button class="text-xs text-gray-500 hover:text-gray-700 transition-colors" @click="statusFilter = ''; iterationFilter = ''; priorityFilter = ''; applyFilters()">
        Clear Filters
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="py-12 text-center text-gray-500">Loading...</div>

    <!-- Empty states -->
    <EmptyState v-else-if="reqStore.requirements.length === 0" title="No requirements yet" description="Create your first requirement to get started." action-label="New Requirement" @action="openCreateModal" />
    <EmptyState v-else-if="filteredRequirements.length === 0" title="No matching requirements" description="Try adjusting your filters." />

    <!-- Table -->
    <div v-else class="glass-card overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-blue-500/5 bg-blue-500/[0.02]">
            <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Title</th>
            <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Priority</th>
            <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Status</th>
            <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Iteration</th>
            <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Created</th>
            <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-blue-500/5">
          <tr
            v-for="req in filteredRequirements"
            :key="req.id"
            class="hover:bg-blue-500/[0.01] cursor-pointer transition-colors"
            @click="navigateToReq(req.id)"
          >
            <td class="px-5 py-3 font-medium text-gray-900">{{ req.title }}</td>
            <td class="px-5 py-3">
              <span :class="['badge-base', priorityColorMap[req.priority] ?? 'bg-gray-50 text-gray-600 border-gray-200/60']">
                {{ req.priority.charAt(0).toUpperCase() + req.priority.slice(1) }}
              </span>
            </td>
            <td class="px-5 py-3"><StatusBadge :status="req.status" size="sm" /></td>
            <td class="px-5 py-3 text-gray-600">{{ iterStore.iterations.find(i => i.id === req.iteration_id)?.name ?? '-' }}</td>
            <td class="px-5 py-3 text-gray-400">{{ formatDate(req.created_at) }}</td>
            <td class="px-5 py-3">
              <button class="text-blue-600 hover:text-blue-800 text-xs font-semibold transition-colors" @click.stop="navigateToReq(req.id)">View</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Requirement Modal -->
    <Modal :show="showCreateModal" title="New Requirement" @close="showCreateModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-gray-600 mb-1.5">Title</label>
          <input v-model="newTitle" type="text" placeholder="Requirement title" class="input-glass" @keyup.enter="handleCreate" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-gray-600 mb-1.5">Priority</label>
          <select v-model="newPriority" class="select-glass">
            <option v-for="p in priorityOptions" :key="p" :value="p">{{ p.charAt(0).toUpperCase() + p.slice(1) }}</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-semibold text-gray-600 mb-1.5">Iteration</label>
          <select v-model="newIterationId" class="select-glass">
            <option v-for="iter in iterStore.iterations" :key="iter.id" :value="iter.id">{{ iter.name }}</option>
          </select>
        </div>
      </div>
      <template #footer>
        <button class="btn-secondary px-4 py-2 text-sm" @click="showCreateModal = false">Cancel</button>
        <button class="btn-primary px-5 py-2 text-sm" :disabled="!newTitle.trim() || !newIterationId" @click="handleCreate">Create</button>
      </template>
    </Modal>
  </div>
</template>
```

Also update the `priorityColorMap` in the `<script setup>` to use gradient badge styles:

```typescript
const priorityColorMap: Record<string, string> = {
  low: 'bg-gradient-to-br from-gray-50 to-gray-100/50 text-gray-600 border-gray-200/60',
  medium: 'bg-gradient-to-br from-blue-50 to-blue-100/50 text-blue-700 border-blue-200/60',
  high: 'bg-gradient-to-br from-orange-50 to-orange-100/50 text-orange-700 border-orange-200/60',
  critical: 'bg-gradient-to-br from-red-50 to-red-100/50 text-red-700 border-red-200/60',
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/RequirementListView.vue
git commit -m "feat(ui): glass requirement list with filter bar and gradient badges"
```

---

### Task 2: Requirement Detail Page

**Files:**
- Modify: `frontend/src/views/RequirementDetailView.vue`

- [ ] **Step 1: Update template with glass styles**

Replace the `<template>` section with:

```vue
<template>
  <div class="max-w-6xl mx-auto">
    <!-- Loading -->
    <div v-if="loading" class="py-12 text-center text-gray-500">Loading...</div>

    <!-- Error -->
    <div v-else-if="error" class="p-3 bg-red-50 border border-red-200/60 rounded-[14px] text-red-700 text-sm">
      {{ error }}
    </div>

    <EmptyState v-else-if="!currentReq" title="Requirement not found" description="The requirement you are looking for does not exist." />

    <template v-else>
      <!-- Header -->
      <div class="mb-6">
        <div class="flex items-center gap-3 mb-2">
          <button class="text-gray-400 hover:text-gray-600 transition-colors" @click="router.push(`/projects/${projectId}/requirements`)">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <h1 class="text-xl font-bold text-gray-900">{{ currentReq.title }}</h1>
          <StatusBadge :status="currentReq.status" />
          <span :class="['badge-base', priorityColorMap[currentReq.priority] ?? 'bg-gray-50 text-gray-600 border-gray-200/60']">
            {{ currentReq.priority.charAt(0).toUpperCase() + currentReq.priority.slice(1) }}
          </span>
        </div>

        <!-- Status transition buttons -->
        <div v-if="statusActions.length > 0" class="flex items-center gap-2 mt-3">
          <button
            v-for="action in statusActions"
            :key="action.status"
            class="px-4 py-2 text-sm font-medium rounded-[10px] transition-all duration-150"
            :class="action.status === 'spec_rejected'
              ? 'btn-danger'
              : action.status === 'done'
                ? 'bg-gradient-to-br from-green-500 to-green-600 text-white rounded-[10px] font-semibold shadow-[0_2px_8px_rgba(16,185,129,0.3)] hover:shadow-[0_4px_16px_rgba(16,185,129,0.4)] hover:-translate-y-px transition-all duration-150 cursor-pointer'
                : 'btn-primary'"
            @click="handleStatusTransition(action.status)"
          >
            {{ action.label }}
          </button>
        </div>
      </div>

      <!-- Tabs -->
      <div class="flex gap-1 border-b border-blue-500/8 mb-6">
        <button
          v-for="tab in (['specs', 'dev', 'test', 'coverage'] as const)"
          :key="tab"
          :class="[
            'pb-2.5 text-sm font-medium border-b-2 transition-all duration-200 -mb-px',
            activeTab === tab
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700',
          ]"
          @click="activeTab = tab"
        >
          {{ tab === 'specs' ? 'Specifications' : tab === 'dev' ? 'Dev Tasks' : tab === 'test' ? 'Test Tasks' : 'Coverage' }}
        </button>
      </div>

      <!-- Specifications Tab -->
      <div v-if="activeTab === 'specs'">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-sm font-bold text-gray-900">Specifications</h2>
          <button class="btn-primary px-4 py-2 text-sm" @click="openCreateSpecModal">Create Spec</button>
        </div>
        <EmptyState v-if="specStore.specs.length === 0" title="No specifications" description="Create a specification to define requirements in detail." action-label="Create Spec" @action="openCreateSpecModal" />
        <div v-else class="space-y-3">
          <div v-for="spec in specStore.specs" :key="spec.id" class="glass-card overflow-hidden">
            <div class="flex items-center justify-between px-5 py-3 cursor-pointer hover:bg-blue-500/[0.01] transition-colors" @click="toggleSpecExpand(spec.id)">
              <div class="flex items-center gap-3">
                <span :class="['badge-base', specTypeColorMap[spec.spec_type] ?? 'bg-gray-50 text-gray-600 border-gray-200/60']">
                  {{ spec.spec_type.toUpperCase() }}
                </span>
                <span class="font-medium text-gray-900 text-sm">{{ spec.title }}</span>
                <span class="text-xs text-gray-400">v{{ spec.current_version }}</span>
              </div>
              <div class="flex items-center gap-2">
                <button class="text-xs text-blue-600 hover:text-blue-800 font-semibold transition-colors" @click.stop="navigateToSpec(spec.id)">Open</button>
                <svg :class="['w-4 h-4 text-gray-400 transition-transform', expandedSpecId === spec.id ? 'rotate-180' : '']" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
            <div v-if="expandedSpecId === spec.id" class="border-t border-blue-500/5 px-5 py-3 bg-blue-500/[0.01]">
              <div v-if="specStore.versions.filter(v => v.spec_id === spec.id).length === 0" class="text-sm text-gray-500">No versions yet.</div>
              <div v-else class="space-y-2">
                <div v-for="ver in specStore.versions.filter(v => v.spec_id === spec.id)" :key="ver.id" class="flex items-center justify-between py-1">
                  <div class="flex items-center gap-2">
                    <span class="text-sm text-gray-700">Version {{ ver.version }}</span>
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
          <h2 class="text-sm font-bold text-gray-900">Dev Tasks</h2>
          <button class="btn-primary px-4 py-2 text-sm" @click="openCreateDevTaskModal">Create Dev Task</button>
        </div>
        <EmptyState v-if="devTasksForReq.length === 0" title="No dev tasks" description="Create a development task to start implementation." action-label="Create Dev Task" @action="openCreateDevTaskModal" />
        <div v-else class="glass-card overflow-hidden">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-blue-500/5 bg-blue-500/[0.02]">
                <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Title</th>
                <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Status</th>
                <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Assignee</th>
                <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Est. Hours</th>
                <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Created</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-blue-500/5">
              <tr v-for="task in devTasksForReq" :key="task.id" class="hover:bg-blue-500/[0.01] transition-colors">
                <td class="px-5 py-3 font-medium text-gray-900">{{ task.title }}</td>
                <td class="px-5 py-3"><StatusBadge :status="task.status" size="sm" /></td>
                <td class="px-5 py-3 text-gray-500">{{ task.assignee_id ?? 'Unassigned' }}</td>
                <td class="px-5 py-3 text-gray-500">{{ task.estimate_hours ?? '-' }}</td>
                <td class="px-5 py-3 text-gray-400">{{ formatDate(task.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Test Tasks Tab -->
      <div v-if="activeTab === 'test'">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-sm font-bold text-gray-900">Test Tasks</h2>
          <button class="btn-primary px-4 py-2 text-sm" @click="openCreateTestTaskModal">Create Test Task</button>
        </div>
        <EmptyState v-if="testTasksForReq.length === 0" title="No test tasks" description="Create a test task to start verification." action-label="Create Test Task" @action="openCreateTestTaskModal" />
        <div v-else class="space-y-3">
          <div v-for="task in testTasksForReq" :key="task.id" class="glass-card overflow-hidden">
            <div class="flex items-center justify-between px-5 py-3 cursor-pointer hover:bg-blue-500/[0.01] transition-colors" @click="toggleTestTaskExpand(task.id)">
              <div class="flex items-center gap-3">
                <span class="font-medium text-gray-900 text-sm">{{ task.title }}</span>
                <StatusBadge :status="task.status" size="sm" />
              </div>
              <svg :class="['w-4 h-4 text-gray-400 transition-transform', expandedTestTaskId === task.id ? 'rotate-180' : '']" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
            <div v-if="expandedTestTaskId === task.id" class="border-t border-blue-500/5 px-5 py-3 bg-blue-500/[0.01]">
              <div v-if="tcStore.testCases.length === 0" class="text-sm text-gray-500">No test cases yet.</div>
              <div v-else class="space-y-2">
                <div v-for="tc in tcStore.testCases" :key="tc.id" class="flex items-center justify-between py-1">
                  <div class="flex items-center gap-2">
                    <span class="text-sm text-gray-700">{{ tc.title }}</span>
                    <StatusBadge :status="tc.status" size="sm" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Coverage Tab -->
      <div v-if="activeTab === 'coverage'">
        <div v-if="!coverageStore.report" class="py-12 text-center text-gray-500">Loading coverage...</div>
        <template v-else>
          <div class="grid grid-cols-3 gap-3 mb-6">
            <div class="glass-card p-5 text-center">
              <div class="text-2xl font-bold text-gray-900">{{ coverageStore.report.total_clauses }}</div>
              <div class="text-xs text-gray-500 mt-1">Total Clauses</div>
            </div>
            <div class="glass-card p-5 text-center">
              <div class="text-2xl font-bold text-emerald-600">{{ coverageStore.report.covered_clauses }}</div>
              <div class="text-xs text-gray-500 mt-1">Covered</div>
            </div>
            <div class="glass-card p-5 text-center">
              <div class="text-2xl font-bold text-blue-600">
                {{ coverageStore.report.total_clauses > 0 ? Math.round((coverageStore.report.covered_clauses / coverageStore.report.total_clauses) * 100) : 0 }}%
              </div>
              <div class="text-xs text-gray-500 mt-1">Overall Coverage</div>
            </div>
          </div>

          <div class="glass-card p-5 mb-6">
            <h3 class="text-xs font-bold text-gray-700 mb-4">Coverage by Severity</h3>
            <div class="space-y-4">
              <div>
                <div class="flex items-center justify-between text-sm mb-1.5">
                  <span class="font-semibold text-gray-700">MUST</span>
                  <span :class="coverageStore.report.must_coverage_pct === 100 ? 'text-emerald-600' : 'text-red-500'" class="font-semibold text-xs">
                    {{ coverageStore.report.must_coverage_pct.toFixed(1) }}%
                  </span>
                </div>
                <div class="w-full bg-gray-100 rounded-full h-2">
                  <div class="h-2 rounded-full transition-all duration-700" :class="coverageStore.report.must_coverage_pct === 100 ? 'bg-gradient-to-r from-emerald-400 to-emerald-500' : 'bg-gradient-to-r from-red-400 to-red-500'" :style="{ width: coverageStore.report.must_coverage_pct + '%' }" />
                </div>
              </div>
              <div>
                <div class="flex items-center justify-between text-sm mb-1.5">
                  <span class="font-semibold text-gray-700">SHOULD</span>
                  <span :class="coverageStore.report.should_coverage_pct >= 80 ? 'text-emerald-600' : coverageStore.report.should_coverage_pct >= 50 ? 'text-amber-600' : 'text-red-500'" class="font-semibold text-xs">
                    {{ coverageStore.report.should_coverage_pct.toFixed(1) }}%
                  </span>
                </div>
                <div class="w-full bg-gray-100 rounded-full h-2">
                  <div class="h-2 rounded-full transition-all duration-700" :class="coverageStore.report.should_coverage_pct >= 80 ? 'bg-gradient-to-r from-emerald-400 to-emerald-500' : coverageStore.report.should_coverage_pct >= 50 ? 'bg-gradient-to-r from-amber-400 to-amber-500' : 'bg-gradient-to-r from-red-400 to-red-500'" :style="{ width: coverageStore.report.should_coverage_pct + '%' }" />
                </div>
              </div>
              <div>
                <div class="flex items-center justify-between text-sm mb-1.5">
                  <span class="font-semibold text-gray-700">MAY</span>
                  <span class="text-gray-400 font-semibold text-xs">{{ coverageStore.report.may_coverage_pct.toFixed(1) }}%</span>
                </div>
                <div class="w-full bg-gray-100 rounded-full h-2">
                  <div class="h-2 rounded-full bg-gradient-to-r from-gray-300 to-gray-400 transition-all duration-700" :style="{ width: coverageStore.report.may_coverage_pct + '%' }" />
                </div>
              </div>
            </div>
          </div>

          <div v-if="coverageStore.report.uncovered_clauses.length > 0" class="glass-card overflow-hidden">
            <div class="px-5 py-3 border-b border-blue-500/8">
              <h3 class="text-xs font-bold text-gray-700">Uncovered Clauses</h3>
            </div>
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-blue-500/5">
                  <th class="text-left px-5 py-2 text-xs font-semibold text-gray-500">Clause ID</th>
                  <th class="text-left px-5 py-2 text-xs font-semibold text-gray-500">Title</th>
                  <th class="text-left px-5 py-2 text-xs font-semibold text-gray-500">Severity</th>
                  <th class="text-left px-5 py-2 text-xs font-semibold text-gray-500">Category</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-blue-500/5">
                <tr v-for="clause in coverageStore.report.uncovered_clauses" :key="clause.id">
                  <td class="px-5 py-2 font-mono text-xs text-gray-600">{{ clause.clause_id }}</td>
                  <td class="px-5 py-2 text-gray-900">{{ clause.title }}</td>
                  <td class="px-5 py-2">
                    <span :class="['badge-base', clause.severity === 'must' ? 'bg-gradient-to-br from-red-50 to-red-100/50 text-red-700 border-red-200/60' : clause.severity === 'should' ? 'bg-gradient-to-br from-amber-50 to-amber-100/50 text-amber-700 border-amber-200/60' : 'bg-gray-50 text-gray-600 border-gray-200/60']">
                      {{ clause.severity.toUpperCase() }}
                    </span>
                  </td>
                  <td class="px-5 py-2 text-gray-500">{{ clause.category }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <EmptyState v-else title="All clauses covered" description="Every specification clause has associated test coverage." />
        </template>
      </div>
    </template>

    <!-- Create Spec Modal -->
    <Modal :show="showCreateSpecModal" title="New Specification" @close="showCreateSpecModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-gray-600 mb-1.5">Title</label>
          <input v-model="newSpecTitle" type="text" placeholder="Specification title" class="input-glass" @keyup.enter="handleCreateSpec" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-gray-600 mb-1.5">Type</label>
          <select v-model="newSpecType" class="select-glass">
            <option v-for="t in specTypeOptions" :key="t" :value="t">{{ t.toUpperCase() }}</option>
          </select>
        </div>
      </div>
      <template #footer>
        <button class="btn-secondary px-4 py-2 text-sm" @click="showCreateSpecModal = false">Cancel</button>
        <button class="btn-primary px-5 py-2 text-sm" :disabled="!newSpecTitle.trim()" @click="handleCreateSpec">Create</button>
      </template>
    </Modal>

    <!-- Create Dev Task Modal -->
    <Modal :show="showCreateDevTaskModal" title="New Dev Task" @close="showCreateDevTaskModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-gray-600 mb-1.5">Title</label>
          <input v-model="newDevTaskTitle" type="text" placeholder="Dev task title" class="input-glass" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-gray-600 mb-1.5">Spec Version</label>
          <select v-model="newDevTaskSpecVersionId" class="select-glass">
            <option value="">Select version</option>
            <option v-for="sv in allSpecVersions" :key="sv.id" :value="sv.id">{{ sv.label }}</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-semibold text-gray-600 mb-1.5">Estimate Hours</label>
          <input v-model.number="newDevTaskEstimate" type="number" min="0" placeholder="Optional" class="input-glass" />
        </div>
      </div>
      <template #footer>
        <button class="btn-secondary px-4 py-2 text-sm" @click="showCreateDevTaskModal = false">Cancel</button>
        <button class="btn-primary px-5 py-2 text-sm" :disabled="!newDevTaskTitle.trim() || !newDevTaskSpecVersionId" @click="handleCreateDevTask">Create</button>
      </template>
    </Modal>

    <!-- Create Test Task Modal -->
    <Modal :show="showCreateTestTaskModal" title="New Test Task" @close="showCreateTestTaskModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-gray-600 mb-1.5">Title</label>
          <input v-model="newTestTaskTitle" type="text" placeholder="Test task title" class="input-glass" @keyup.enter="handleCreateTestTask" />
        </div>
      </div>
      <template #footer>
        <button class="btn-secondary px-4 py-2 text-sm" @click="showCreateTestTaskModal = false">Cancel</button>
        <button class="btn-primary px-5 py-2 text-sm" :disabled="!newTestTaskTitle.trim()" @click="handleCreateTestTask">Create</button>
      </template>
    </Modal>
  </div>
</template>
```

Also update the color maps in `<script setup>`:

```typescript
const priorityColorMap: Record<string, string> = {
  low: 'bg-gradient-to-br from-gray-50 to-gray-100/50 text-gray-600 border-gray-200/60',
  medium: 'bg-gradient-to-br from-blue-50 to-blue-100/50 text-blue-700 border-blue-200/60',
  high: 'bg-gradient-to-br from-orange-50 to-orange-100/50 text-orange-700 border-orange-200/60',
  critical: 'bg-gradient-to-br from-red-50 to-red-100/50 text-red-700 border-red-200/60',
}

const specTypeColorMap: Record<string, string> = {
  api: 'bg-gradient-to-br from-indigo-50 to-indigo-100/50 text-indigo-700 border-indigo-200/60',
  data: 'bg-gradient-to-br from-teal-50 to-teal-100/50 text-teal-700 border-teal-200/60',
  flow: 'bg-gradient-to-br from-amber-50 to-amber-100/50 text-amber-700 border-amber-200/60',
  ui: 'bg-gradient-to-br from-pink-50 to-pink-100/50 text-pink-700 border-pink-200/60',
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/RequirementDetailView.vue
git commit -m "feat(ui): glass requirement detail with tabs and coverage visualization"
```

---

### Task 3: Specification Detail Page

**Files:**
- Modify: `frontend/src/views/SpecificationDetailView.vue`

- [ ] **Step 1: Update template with glass styles**

Replace the `<template>` section with:

```vue
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
```

Also update the color maps in `<script setup>`:

```typescript
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
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/SpecificationDetailView.vue
git commit -m "feat(ui): glass specification detail with version cards and clause table"
```

---

### Task 4: Coverage Report Page

**Files:**
- Modify: `frontend/src/views/CoverageReportView.vue`

- [ ] **Step 1: Update template with glass styles**

Replace the `<template>` section with:

```vue
<template>
  <div class="max-w-6xl mx-auto">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-xl font-bold text-gray-900">Coverage Report</h1>
    </div>

    <!-- Error -->
    <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200/60 rounded-[14px] text-red-700 text-sm">
      {{ error }}
    </div>

    <!-- Loading -->
    <div v-if="loading" class="py-12 text-center text-gray-500">Loading...</div>

    <template v-else-if="coverageStore.report">
      <!-- Summary cards -->
      <div class="grid grid-cols-3 gap-3 mb-6">
        <div class="glass-card p-6 text-center">
          <div class="text-2xl font-bold text-gray-900">{{ coverageStore.report.total_clauses }}</div>
          <div class="text-xs text-gray-500 mt-1">Total Clauses</div>
        </div>
        <div class="glass-card p-6 text-center">
          <div class="text-2xl font-bold text-emerald-600">{{ coverageStore.report.covered_clauses }}</div>
          <div class="text-xs text-gray-500 mt-1">Covered</div>
        </div>
        <div class="glass-card p-6 text-center">
          <div class="text-2xl font-bold text-blue-600">{{ overallPct }}%</div>
          <div class="text-xs text-gray-500 mt-1">Overall Coverage</div>
        </div>
      </div>

      <!-- Progress bars by severity -->
      <div class="glass-card p-6 mb-6">
        <h2 class="text-sm font-bold text-gray-900 mb-5">Coverage by Severity</h2>
        <div class="space-y-5">
          <!-- MUST -->
          <div>
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-sm font-semibold text-gray-700">MUST</span>
              <span :class="['text-xs font-bold', mustTextColor(coverageStore.report.must_coverage_pct)]">
                {{ coverageStore.report.must_coverage_pct.toFixed(1) }}%
              </span>
            </div>
            <div class="w-full bg-gray-100 rounded-full h-2.5">
              <div :class="['h-2.5 rounded-full transition-all duration-700', mustBarColor(coverageStore.report.must_coverage_pct) === 'bg-green-500' ? 'bg-gradient-to-r from-emerald-400 to-emerald-500' : 'bg-gradient-to-r from-red-400 to-red-500']" :style="{ width: Math.max(coverageStore.report.must_coverage_pct, 0) + '%' }" />
            </div>
            <p class="text-[11px] text-gray-400 mt-1">100% required -- any gap is a risk</p>
          </div>
          <!-- SHOULD -->
          <div>
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-sm font-semibold text-gray-700">SHOULD</span>
              <span :class="['text-xs font-bold', shouldTextColor(coverageStore.report.should_coverage_pct)]">
                {{ coverageStore.report.should_coverage_pct.toFixed(1) }}%
              </span>
            </div>
            <div class="w-full bg-gray-100 rounded-full h-2.5">
              <div :class="['h-2.5 rounded-full transition-all duration-700', shouldBarColor(coverageStore.report.should_coverage_pct) === 'bg-green-500' ? 'bg-gradient-to-r from-emerald-400 to-emerald-500' : shouldBarColor(coverageStore.report.should_coverage_pct) === 'bg-yellow-500' ? 'bg-gradient-to-r from-amber-400 to-amber-500' : 'bg-gradient-to-r from-red-400 to-red-500']" :style="{ width: Math.max(coverageStore.report.should_coverage_pct, 0) + '%' }" />
            </div>
            <p class="text-[11px] text-gray-400 mt-1">Target >= 80%, warning below 50%</p>
          </div>
          <!-- MAY -->
          <div>
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-sm font-semibold text-gray-700">MAY</span>
              <span class="text-xs font-bold text-gray-400">{{ coverageStore.report.may_coverage_pct.toFixed(1) }}%</span>
            </div>
            <div class="w-full bg-gray-100 rounded-full h-2.5">
              <div class="h-2.5 rounded-full bg-gradient-to-r from-gray-300 to-gray-400 transition-all duration-700" :style="{ width: Math.max(coverageStore.report.may_coverage_pct, 0) + '%' }" />
            </div>
            <p class="text-[11px] text-gray-400 mt-1">Not enforced -- informational only</p>
          </div>
        </div>
      </div>

      <!-- Uncovered clauses table -->
      <div class="glass-card overflow-hidden">
        <div class="px-5 py-3 border-b border-blue-500/8">
          <h2 class="text-sm font-bold text-gray-900">Uncovered Clauses ({{ coverageStore.report.uncovered_clauses.length }})</h2>
        </div>
        <EmptyState v-if="coverageStore.report.uncovered_clauses.length === 0" title="All clauses covered" description="Every specification clause has associated test coverage." />
        <table v-else class="w-full text-sm">
          <thead>
            <tr class="border-b border-blue-500/5">
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Clause ID</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Title</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Severity</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Category</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-blue-500/5">
            <tr v-for="clause in coverageStore.report.uncovered_clauses" :key="clause.id" class="hover:bg-blue-500/[0.01] transition-colors">
              <td class="px-5 py-3 font-mono text-xs text-gray-600">{{ clause.clause_id }}</td>
              <td class="px-5 py-3 text-gray-900">{{ clause.title }}</td>
              <td class="px-5 py-3">
                <span :class="['badge-base', severityColorMap[clause.severity] ?? 'bg-gray-50 text-gray-600 border-gray-200/60']">
                  {{ clause.severity.toUpperCase() }}
                </span>
              </td>
              <td class="px-5 py-3 text-gray-500">{{ clause.category }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
```

Also update the `severityColorMap` in `<script setup>`:

```typescript
const severityColorMap: Record<string, string> = {
  must: 'bg-gradient-to-br from-red-50 to-red-100/50 text-red-700 border-red-200/60',
  should: 'bg-gradient-to-br from-amber-50 to-amber-100/50 text-amber-700 border-amber-200/60',
  may: 'bg-gradient-to-br from-gray-50 to-gray-100/50 text-gray-600 border-gray-200/60',
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/CoverageReportView.vue
git commit -m "feat(ui): glass coverage report with gradient progress bars"
```

---

### Task 5: Teams & Organizations Page

**Files:**
- Modify: `frontend/src/views/TeamsView.vue`

- [ ] **Step 1: Update template with glass styles**

Replace the `<template>` section with:

```vue
<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Teams &amp; Organizations</h1>
        <p class="mt-1 text-sm text-gray-500">Manage organizations and their teams.</p>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-6">
      <div v-for="i in 2" :key="i" class="glass-card p-5 animate-pulse">
        <div class="h-5 bg-gray-200/50 rounded w-1/3 mb-4" />
        <div class="h-4 bg-gray-100/50 rounded w-1/4 mb-3" />
        <div class="h-3 bg-gray-100/50 rounded w-1/2" />
      </div>
    </div>

    <!-- Empty state -->
    <EmptyState v-else-if="orgs.length === 0" title="No organizations yet" description="Create an organization to start managing teams." action-label="New Organization" @action="openNewOrgModal" />

    <!-- Org + teams list -->
    <div v-else class="space-y-4">
      <div v-for="org in orgs" :key="org.id" class="glass-card overflow-hidden">
        <!-- Org header -->
        <div class="flex items-center justify-between px-5 py-4 border-b border-blue-500/5">
          <div>
            <h2 class="text-sm font-bold text-gray-900">{{ org.name }}</h2>
            <p class="text-[11px] text-gray-400 mt-0.5">{{ org.slug }} &middot; Created {{ formatDate(org.created_at) }}</p>
          </div>
          <button class="btn-ghost px-3 py-1.5 text-xs" @click="openNewTeamModal(org.id)">+ Team</button>
        </div>

        <!-- Teams under this org -->
        <div class="divide-y divide-blue-500/5">
          <div v-for="team in teamsForOrg(org.id)" :key="team.id" class="px-5 py-3 flex items-center justify-between hover:bg-blue-500/[0.01] transition-colors">
            <div>
              <span class="text-sm font-medium text-gray-800">{{ team.name }}</span>
              <span class="text-xs text-gray-400 ml-2">{{ team.slug }}</span>
            </div>
            <span class="text-xs text-gray-400">{{ formatDate(team.created_at) }}</span>
          </div>
          <div v-if="teamsForOrg(org.id).length === 0" class="px-5 py-4 text-sm text-gray-400 text-center">
            No teams yet. Click "+ Team" to add one.
          </div>
        </div>
      </div>

      <!-- New org button at bottom -->
      <div class="flex justify-center">
        <button class="btn-secondary px-5 py-2.5 text-sm" @click="openNewOrgModal">New Organization</button>
      </div>
    </div>

    <!-- New Org Modal -->
    <Modal :show="showNewOrgModal" title="New Organization" @close="showNewOrgModal = false">
      <form @submit.prevent="handleCreateOrg" class="space-y-4">
        <div v-if="orgError" class="p-3 bg-red-50 border border-red-200/60 rounded-[10px] text-sm text-red-700">
          {{ orgError }}
        </div>
        <div>
          <label for="org-name" class="block text-xs font-semibold text-gray-600 mb-1.5">Name</label>
          <input id="org-name" v-model="orgForm.name" type="text" required class="input-glass" placeholder="Acme Inc." />
        </div>
        <div>
          <label for="org-slug" class="block text-xs font-semibold text-gray-600 mb-1.5">Slug</label>
          <input id="org-slug" v-model="orgForm.slug" type="text" class="input-glass" placeholder="auto-generated-from-name" />
          <p class="mt-1 text-[11px] text-gray-400">Leave empty to auto-generate from name.</p>
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button type="button" class="btn-secondary px-4 py-2 text-sm" @click="showNewOrgModal = false">Cancel</button>
          <button type="submit" :disabled="creatingOrg" class="btn-primary px-5 py-2 text-sm">
            {{ creatingOrg ? 'Creating...' : 'Create Organization' }}
          </button>
        </div>
      </form>
    </Modal>

    <!-- New Team Modal -->
    <Modal :show="showNewTeamModal" title="New Team" @close="showNewTeamModal = false">
      <form @submit.prevent="handleCreateTeam" class="space-y-4">
        <div v-if="teamError" class="p-3 bg-red-50 border border-red-200/60 rounded-[10px] text-sm text-red-700">
          {{ teamError }}
        </div>
        <div>
          <label for="team-org" class="block text-xs font-semibold text-gray-600 mb-1.5">Organization</label>
          <select id="team-org" v-model="teamForm.org_id" required class="select-glass">
            <option value="" disabled>Select an organization</option>
            <option v-for="org in orgs" :key="org.id" :value="org.id">{{ org.name }}</option>
          </select>
        </div>
        <div>
          <label for="team-name" class="block text-xs font-semibold text-gray-600 mb-1.5">Name</label>
          <input id="team-name" v-model="teamForm.name" type="text" required class="input-glass" placeholder="Backend Team" />
        </div>
        <div>
          <label for="team-slug" class="block text-xs font-semibold text-gray-600 mb-1.5">Slug</label>
          <input id="team-slug" v-model="teamForm.slug" type="text" class="input-glass" placeholder="auto-generated-from-name" />
          <p class="mt-1 text-[11px] text-gray-400">Leave empty to auto-generate from name.</p>
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button type="button" class="btn-secondary px-4 py-2 text-sm" @click="showNewTeamModal = false">Cancel</button>
          <button type="submit" :disabled="creatingTeam" class="btn-primary px-5 py-2 text-sm">
            {{ creatingTeam ? 'Creating...' : 'Create Team' }}
          </button>
        </div>
      </form>
    </Modal>
  </div>
</template>
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/TeamsView.vue
git commit -m "feat(ui): glass teams and organizations page"
```
