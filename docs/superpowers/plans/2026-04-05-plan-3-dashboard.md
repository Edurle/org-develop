# Plan 3: Dashboard Redesign

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the dashboard homepage with emoji stat cards, activity feed, and project progress list using glass effects.

**Architecture:** Replace the current plain stats grid with animated glass cards featuring emoji icons and trend indicators. Activity feed gets colored dots and glass container. Add a project progress section with gradient progress bars.

**Tech Stack:** UnoCSS shortcuts, Vue 3 SFC, CSS animations

**Depends on:** Plan 1 (theme tokens), Plan 2 (components)

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/src/views/HomeView.vue` | Rewrite | Dashboard with glass cards, activity, progress |

---

### Task 1: Dashboard Redesign

**Files:**
- Modify: `frontend/src/views/HomeView.vue`

- [ ] **Step 1: Rewrite HomeView.vue**

Replace the entire file with:

```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useProjectStore } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'

const projectStore = useProjectStore()
const authStore = useAuthStore()
const loading = ref(true)
const now = new Date()
const hour = now.getHours()

const greeting = computed(() => {
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
})

onMounted(async () => {
  try {
    await projectStore.fetchList()
  } catch {
    // silently fail
  } finally {
    loading.value = false
  }
})

const stats = [
  { label: 'Active Projects', key: 'projects', emoji: '📊', gradient: 'from-blue-500 to-cyan-400', bg: 'bg-blue-50' },
  { label: 'Total Requirements', key: 'requirements', emoji: '📋', gradient: 'from-emerald-500 to-teal-400', bg: 'bg-emerald-50' },
  { label: 'Test Coverage', key: 'coverage', emoji: '🎯', gradient: 'from-violet-500 to-purple-400', bg: 'bg-violet-50' },
  { label: 'Team Members', key: 'members', emoji: '👥', gradient: 'from-amber-500 to-orange-400', bg: 'bg-amber-50' },
]

function getStatValue(key: string): string | number {
  switch (key) {
    case 'projects':
      return projectStore.projects.length
    case 'requirements':
      return '--'
    case 'coverage':
      return '--'
    case 'members':
      return '--'
    default:
      return 0
  }
}

const recentActivity = [
  { text: 'Project "Alpha" was created', time: '2 hours ago', color: 'bg-blue-500' },
  { text: 'New requirement added to Sprint 3', time: '4 hours ago', color: 'bg-emerald-500' },
  { text: 'Specification v2.1 was locked', time: '1 day ago', color: 'bg-amber-500' },
  { text: 'Test case "Login validation" passed', time: '1 day ago', color: 'bg-green-500' },
  { text: 'Member john@example.com joined Team Beta', time: '2 days ago', color: 'bg-violet-500' },
]

const projectProgress = computed(() =>
  projectStore.projects.slice(0, 4).map((p, i) => ({
    name: p.name,
    progress: [72, 45, 90, 30][i] ?? 50,
    color: ['from-blue-500 to-cyan-400', 'from-emerald-500 to-teal-400', 'from-violet-500 to-purple-400', 'from-amber-500 to-orange-400'][i] ?? 'from-blue-500 to-cyan-400',
  }))
)
</script>

<template>
  <div class="space-y-6">
    <!-- Welcome header -->
    <div>
      <h1 class="text-xl font-bold text-gray-900">
        {{ greeting }}{{ authStore.user?.username ? `, ${authStore.user.username}` : '' }}
      </h1>
      <p class="mt-1 text-sm text-gray-500">Here is an overview of your workspace.</p>
    </div>

    <!-- Stats cards -->
    <div v-if="loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      <div v-for="i in 4" :key="i" class="glass-card p-5 animate-pulse">
        <div class="h-4 bg-gray-200/50 rounded w-24 mb-3" />
        <div class="h-8 bg-gray-200/50 rounded w-16" />
      </div>
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      <div
        v-for="(stat, index) in stats"
        :key="stat.key"
        class="glass-card p-5 hover:shadow-glass-md hover:-translate-y-0.5 cursor-default"
        :style="{ animation: `fadeInUp 0.4s ease ${index * 80}ms both` }"
      >
        <div class="flex items-center gap-3 mb-3">
          <div :class="[stat.bg, 'w-9 h-9 rounded-xl flex items-center justify-center text-lg']">
            {{ stat.emoji }}
          </div>
          <span class="text-xs font-semibold text-gray-500">{{ stat.label }}</span>
        </div>
        <p class="text-2xl font-bold text-gray-900">{{ getStatValue(stat.key) }}</p>
      </div>
    </div>

    <!-- Bottom: Activity + Progress -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
      <!-- Recent activity -->
      <div class="glass-card overflow-hidden">
        <div class="px-5 py-4 border-b border-blue-500/8">
          <h2 class="text-sm font-bold text-gray-900">Recent Activity</h2>
        </div>
        <div class="divide-y divide-blue-500/5">
          <div
            v-for="(item, index) in recentActivity"
            :key="index"
            class="px-5 py-3 flex items-center gap-3"
            :style="{ animation: `fadeInUp 0.4s ease ${index * 80 + 200}ms both` }"
          >
            <div :class="[item.color, 'w-2 h-2 rounded-full shrink-0']" />
            <span class="text-sm text-gray-700 flex-1">{{ item.text }}</span>
            <span class="text-[11px] text-gray-400 whitespace-nowrap">{{ item.time }}</span>
          </div>
        </div>
      </div>

      <!-- Project progress -->
      <div class="glass-card overflow-hidden">
        <div class="px-5 py-4 border-b border-blue-500/8">
          <h2 class="text-sm font-bold text-gray-900">Project Progress</h2>
        </div>
        <div class="p-5 space-y-4">
          <div
            v-for="(project, index) in projectProgress"
            :key="project.name"
            :style="{ animation: `fadeInUp 0.4s ease ${index * 80 + 200}ms both` }"
          >
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-sm font-medium text-gray-800">{{ project.name }}</span>
              <span class="text-xs font-semibold text-gray-500">{{ project.progress }}%</span>
            </div>
            <div class="w-full bg-gray-100 rounded-full h-2">
              <div
                :class="['h-2 rounded-full bg-gradient-to-r transition-all duration-700', project.color]"
                :style="{ width: project.progress + '%', animation: 'progressFill 0.8s ease-out' }"
              />
            </div>
          </div>
          <div v-if="projectProgress.length === 0" class="text-sm text-gray-400 text-center py-4">
            No projects yet.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/HomeView.vue
git commit -m "feat(ui): glass dashboard with emoji stat cards, activity feed, and progress bars"
```
