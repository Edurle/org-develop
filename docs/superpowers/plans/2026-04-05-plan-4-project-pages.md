# Plan 4: Project Pages Redesign

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign all project-related pages: project list (card grid), project overview, project settings, project members, and project tasks.

**Architecture:** All pages adopt glass-card containers, the new btn-primary/btn-secondary shortcuts, input-glass/select-glass for forms, and glass-wrapped tables with gradient headers.

**Tech Stack:** UnoCSS shortcuts (from Plan 1), Vue 3 SFC

**Depends on:** Plan 1 (theme tokens), Plan 2 (components)

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/src/views/ProjectsView.vue` | Rewrite | 3-column card grid + glass modal |
| `frontend/src/views/ProjectOverviewView.vue` | Modify | Glass stats, glass tables |
| `frontend/src/views/ProjectSettingsView.vue` | Modify | Glass forms, glass danger zone |
| `frontend/src/views/ProjectMembersView.vue` | Modify | Glass table + glass modal |
| `frontend/src/views/ProjectTasksView.vue` | Modify | Glass tables + glass tabs |

---

### Task 1: Projects List Page

**Files:**
- Modify: `frontend/src/views/ProjectsView.vue`

- [ ] **Step 1: Rewrite ProjectsView.vue with glass card grid**

Replace the entire `<template>` section (lines 89-217) with the new template. Keep the `<script setup>` unchanged.

New template:

```vue
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
        <!-- Avatar + name -->
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-white font-bold text-sm shrink-0">
            {{ project.name.charAt(0).toUpperCase() }}
          </div>
          <div class="min-w-0">
            <h3 class="text-sm font-bold text-gray-900 truncate">{{ project.name }}</h3>
            <p class="text-[11px] text-gray-400">{{ formatDate(project.created_at) }}</p>
          </div>
        </div>

        <!-- Description -->
        <p v-if="project.description" class="text-xs text-gray-500 mb-3 line-clamp-2 leading-relaxed">
          {{ project.description }}
        </p>

        <!-- Footer -->
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
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/ProjectsView.vue
git commit -m "feat(ui): glass project card grid with gradient avatars"
```

---

### Task 2: Project Overview Page

**Files:**
- Modify: `frontend/src/views/ProjectOverviewView.vue`

- [ ] **Step 1: Update template with glass styles**

Replace the `<template>` section (lines 93-268) with:

```vue
<template>
  <div class="space-y-6">
    <!-- Error banner -->
    <div v-if="error" class="p-3 bg-red-50 border border-red-200/60 rounded-[14px] text-sm text-red-700">
      {{ error }}
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="space-y-6">
      <div class="animate-pulse">
        <div class="h-7 bg-gray-200/50 rounded w-1/3 mb-2" />
        <div class="h-4 bg-gray-100/50 rounded w-2/3" />
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div v-for="i in 3" :key="i" class="glass-card p-5 animate-pulse">
          <div class="h-4 bg-gray-200/50 rounded w-20 mb-3" />
          <div class="h-6 bg-gray-100/50 rounded w-12" />
        </div>
      </div>
    </div>

    <template v-else-if="project">
      <!-- Project header -->
      <div>
        <div class="flex items-center gap-2">
          <h1 v-if="!editingName" class="text-xl font-bold text-gray-900">
            {{ project.name }}
          </h1>
          <div v-else class="flex items-center gap-2">
            <input v-model="editName" type="text" class="input-glass max-w-xs" @keyup.enter="saveName" @keyup.escape="editingName = false" />
            <button class="btn-primary px-3 py-1.5 text-xs" :disabled="saving" @click="saveName">Save</button>
            <button class="btn-secondary px-3 py-1.5 text-xs" @click="editingName = false">Cancel</button>
          </div>
          <button v-if="!editingName" class="p-1 text-gray-400 hover:text-gray-600 transition-colors" title="Edit name" @click="startEditName">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
          </button>
        </div>

        <div class="mt-2 flex items-center gap-2">
          <p v-if="!editingDesc" class="text-sm text-gray-500">
            {{ project.description || 'No description. Click edit to add one.' }}
          </p>
          <div v-else class="flex items-start gap-2 flex-1">
            <textarea v-model="editDesc" rows="2" class="input-glass resize-none flex-1" @keyup.escape="editingDesc = false" />
            <button class="btn-primary px-3 py-1.5 text-xs" :disabled="saving" @click="saveDesc">Save</button>
            <button class="btn-secondary px-3 py-1.5 text-xs" @click="editingDesc = false">Cancel</button>
          </div>
          <button v-if="!editingDesc" class="p-1 text-gray-400 hover:text-gray-600 transition-colors" title="Edit description" @click="startEditDesc">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Quick stats -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div class="glass-card p-5">
          <span class="text-xs font-semibold text-gray-500">Requirements</span>
          <p class="mt-1 text-2xl font-bold text-gray-900">{{ requirementStore.requirements.length }}</p>
        </div>
        <div class="glass-card p-5">
          <span class="text-xs font-semibold text-gray-500">Iterations</span>
          <p class="mt-1 text-2xl font-bold text-gray-900">{{ iterationStore.iterations.length }}</p>
        </div>
        <div class="glass-card p-5">
          <span class="text-xs font-semibold text-gray-500">Members</span>
          <p class="mt-1 text-2xl font-bold text-gray-900">--</p>
        </div>
      </div>

      <!-- Active iterations -->
      <div class="glass-card overflow-hidden">
        <div class="px-5 py-4 border-b border-blue-500/8">
          <h2 class="text-sm font-bold text-gray-900">Active Iterations</h2>
        </div>
        <div v-if="activeIterations.length === 0" class="px-5 py-8 text-center text-sm text-gray-400">
          No active iterations.
        </div>
        <div v-else class="divide-y divide-blue-500/5">
          <div v-for="iter in activeIterations" :key="iter.id" class="px-5 py-3 flex items-center justify-between">
            <div>
              <span class="text-sm font-medium text-gray-800">{{ iter.name }}</span>
              <span v-if="iter.start_date" class="text-xs text-gray-400 ml-2">
                {{ formatDate(iter.start_date) }}
                <span v-if="iter.end_date"> - {{ formatDate(iter.end_date) }}</span>
              </span>
            </div>
            <StatusBadge :status="iter.status" size="sm" />
          </div>
        </div>
      </div>

      <!-- Recent requirements table -->
      <div class="glass-card overflow-hidden">
        <div class="px-5 py-4 border-b border-blue-500/8">
          <h2 class="text-sm font-bold text-gray-900">Recent Requirements</h2>
        </div>
        <div v-if="recentRequirements.length === 0" class="px-5 py-8 text-center text-sm text-gray-400">
          No requirements yet.
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-blue-500/5 bg-blue-500/[0.02]">
                <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">Title</th>
                <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">Priority</th>
                <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">Status</th>
                <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">Created</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-blue-500/5">
              <tr v-for="req in recentRequirements" :key="req.id" class="hover:bg-blue-500/[0.01] transition-colors">
                <td class="px-5 py-3 text-gray-900 font-medium">{{ req.title }}</td>
                <td class="px-5 py-3 capitalize text-gray-600">{{ req.priority }}</td>
                <td class="px-5 py-3"><StatusBadge :status="req.status" size="sm" /></td>
                <td class="px-5 py-3 text-gray-400">{{ formatDate(req.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/ProjectOverviewView.vue
git commit -m "feat(ui): glass project overview with stats cards and tables"
```

---

### Task 3: Project Settings Page

**Files:**
- Modify: `frontend/src/views/ProjectSettingsView.vue`

- [ ] **Step 1: Update template with glass styles**

Replace the `<template>` section (lines 99-245) with:

```vue
<template>
  <div class="space-y-6 max-w-2xl">
    <!-- Error -->
    <div v-if="error" class="p-3 bg-red-50 border border-red-200/60 rounded-[14px] text-sm text-red-700">
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
          <div v-if="saveError" class="p-3 bg-red-50 border border-red-200/60 rounded-[10px] text-sm text-red-700">
            {{ saveError }}
          </div>
          <div v-if="saveSuccess" class="p-3 bg-green-50 border border-green-200/60 rounded-[10px] text-sm text-green-700">
            Settings saved successfully.
          </div>

          <div>
            <label for="settings-name" class="block text-xs font-semibold text-gray-600 mb-1.5">Project Name</label>
            <input id="settings-name" v-model="formName" type="text" required class="input-glass" />
          </div>

          <div>
            <label for="settings-slug" class="block text-xs font-semibold text-gray-600 mb-1.5">Slug</label>
            <input id="settings-slug" v-model="formSlug" type="text" required class="input-glass" />
          </div>

          <div>
            <label for="settings-desc" class="block text-xs font-semibold text-gray-600 mb-1.5">Description</label>
            <textarea id="settings-desc" v-model="formDesc" rows="4" class="input-glass resize-none" placeholder="Describe your project..." />
          </div>

          <div class="flex justify-end">
            <button type="submit" :disabled="saving" class="btn-primary px-5 py-2.5 text-sm">
              {{ saving ? 'Saving...' : 'Save Changes' }}
            </button>
          </div>
        </form>
      </div>

      <!-- Danger zone -->
      <div class="bg-white/70 backdrop-blur-xl border border-red-200/60 rounded-[14px] shadow-glass-sm">
        <div class="px-6 py-4 border-b border-red-200/40">
          <h2 class="text-sm font-bold text-red-700">Danger Zone</h2>
          <p class="text-xs text-gray-500 mt-0.5">Irreversible actions for this project.</p>
        </div>
        <div class="px-6 py-5 flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-900">Delete this project</p>
            <p class="text-xs text-gray-500">Once deleted, there is no going back.</p>
          </div>
          <button class="btn-danger px-4 py-2 text-sm" @click="openDeleteModal">
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
          <input id="delete-confirm" v-model="deleteConfirm" type="text" class="input-glass" :placeholder="project?.name" />
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button type="button" class="btn-secondary px-4 py-2 text-sm" @click="showDeleteModal = false">Cancel</button>
          <button type="button" :disabled="deleting || deleteConfirm !== project?.name" class="btn-danger px-4 py-2 text-sm" @click="handleDelete">
            {{ deleting ? 'Deleting...' : 'Delete Project' }}
          </button>
        </div>
      </div>
    </Modal>
  </div>
</template>
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/ProjectSettingsView.vue
git commit -m "feat(ui): glass project settings with danger zone"
```

---

### Task 4: Project Members Page

**Files:**
- Modify: `frontend/src/views/ProjectMembersView.vue`

- [ ] **Step 1: Update template with glass styles**

Replace the `<template>` section (lines 82-202) with:

```vue
<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Members</h1>
        <p class="mt-1 text-sm text-gray-500">Manage who has access to this project.</p>
      </div>
      <button class="btn-primary px-5 py-2.5 text-sm" @click="openAddModal">
        Add Member
      </button>
    </div>

    <!-- Error -->
    <div v-if="error" class="p-3 bg-red-50 border border-red-200/60 rounded-[14px] text-sm text-red-700">
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
    <div v-else-if="members.length === 0" class="glass-card px-5 py-12 text-center">
      <p class="text-sm text-gray-500">No members found. Add someone to get started.</p>
    </div>

    <!-- Members table -->
    <div v-else class="glass-card overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-blue-500/5 bg-blue-500/[0.02]">
            <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">User ID</th>
            <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">Role</th>
            <th class="px-5 py-3 text-left text-xs font-semibold text-gray-500">Joined</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-blue-500/5">
          <tr v-for="member in members" :key="member.id" class="hover:bg-blue-500/[0.01] transition-colors">
            <td class="px-5 py-3">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-xs font-bold text-white">
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
    <Modal :show="showAddModal" title="Add Member" @close="showAddModal = false">
      <form @submit.prevent="handleAddMember" class="space-y-4">
        <div v-if="addError" class="p-3 bg-red-50 border border-red-200/60 rounded-[10px] text-sm text-red-700">
          {{ addError }}
        </div>
        <div>
          <label for="member-user-id" class="block text-xs font-semibold text-gray-600 mb-1.5">User ID</label>
          <input id="member-user-id" v-model="addForm.user_id" type="text" required class="input-glass" placeholder="Enter user ID" />
        </div>
        <div>
          <label for="member-role" class="block text-xs font-semibold text-gray-600 mb-1.5">Role</label>
          <select id="member-role" v-model="addForm.roles" class="select-glass">
            <option value="admin">Admin</option>
            <option value="member">Member</option>
            <option value="viewer">Viewer</option>
          </select>
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button type="button" class="btn-secondary px-4 py-2 text-sm" @click="showAddModal = false">Cancel</button>
          <button type="submit" :disabled="adding" class="btn-primary px-5 py-2 text-sm">
            {{ adding ? 'Adding...' : 'Add Member' }}
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
git add frontend/src/views/ProjectMembersView.vue
git commit -m "feat(ui): glass members table with gradient avatars"
```

---

### Task 5: Project Tasks Page

**Files:**
- Modify: `frontend/src/views/ProjectTasksView.vue`

- [ ] **Step 1: Update template with glass styles**

Replace the `<template>` section (lines 57-204) with:

```vue
<template>
  <div class="max-w-6xl mx-auto">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-xl font-bold text-gray-900">Project Tasks</h1>
    </div>

    <!-- Error -->
    <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200/60 rounded-[14px] text-red-700 text-sm">
      {{ error }}
    </div>

    <!-- Tabs -->
    <div class="flex gap-1 border-b border-blue-500/8 mb-6">
      <button
        :class="[
          'pb-2.5 text-sm font-medium border-b-2 transition-all duration-200 -mb-px',
          activeTab === 'dev'
            ? 'border-blue-600 text-blue-600'
            : 'border-transparent text-gray-500 hover:text-gray-700',
        ]"
        @click="activeTab = 'dev'"
      >
        Dev Tasks ({{ taskStore.devTasks.length }})
      </button>
      <button
        :class="[
          'pb-2.5 text-sm font-medium border-b-2 transition-all duration-200 -mb-px',
          activeTab === 'test'
            ? 'border-blue-600 text-blue-600'
            : 'border-transparent text-gray-500 hover:text-gray-700',
        ]"
        @click="activeTab = 'test'"
      >
        Test Tasks ({{ taskStore.testTasks.length }})
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="py-12 text-center text-gray-500">Loading...</div>

    <!-- Dev Tasks Tab -->
    <template v-else-if="activeTab === 'dev'">
      <EmptyState
        v-if="taskStore.devTasks.length === 0"
        title="No dev tasks"
        description="Development tasks will appear here once created from requirements."
      />
      <div v-else class="glass-card overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-blue-500/5 bg-blue-500/[0.02]">
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Title</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Status</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Assignee</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Est. Hours</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Created</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-blue-500/5">
            <tr v-for="task in taskStore.devTasks" :key="task.id" class="hover:bg-blue-500/[0.01] transition-colors">
              <td class="px-5 py-3 font-medium text-gray-900">{{ task.title }}</td>
              <td class="px-5 py-3"><StatusBadge :status="task.status" size="sm" /></td>
              <td class="px-5 py-3 text-gray-500">{{ task.assignee_id ?? 'Unassigned' }}</td>
              <td class="px-5 py-3 text-gray-500">{{ task.estimate_hours ?? '-' }}</td>
              <td class="px-5 py-3 text-gray-400">{{ formatDate(task.created_at) }}</td>
              <td class="px-5 py-3">
                <div class="flex items-center gap-2">
                  <button v-if="task.status === 'open'" class="btn-primary px-3 py-1.5 text-xs" @click="handleClaim(task.id)">Claim</button>
                  <select
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
        title="No test tasks"
        description="Test tasks will appear here once created from requirements."
      />
      <div v-else class="glass-card overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-blue-500/5 bg-blue-500/[0.02]">
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Title</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Status</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Requirement</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">Created</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-blue-500/5">
            <tr v-for="task in taskStore.testTasks" :key="task.id" class="hover:bg-blue-500/[0.01] transition-colors">
              <td class="px-5 py-3 font-medium text-gray-900">{{ task.title }}</td>
              <td class="px-5 py-3"><StatusBadge :status="task.status" size="sm" /></td>
              <td class="px-5 py-3">
                <router-link :to="`/projects/${projectId}/requirements/${task.requirement_id}`" class="text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors">
                  {{ task.requirement_id }}
                </router-link>
              </td>
              <td class="px-5 py-3 text-gray-400">{{ formatDate(task.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
```

Also remove `class="p-6"` from the outer div since the layout now provides padding.

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/ProjectTasksView.vue
git commit -m "feat(ui): glass task tables with tab navigation"
```
