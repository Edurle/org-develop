# Plan 1: Theme Foundation & Layout Redesign

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the UnoCSS theme system (design tokens, shortcuts, animations) and migrate from sidebar to top navigation.

**Architecture:** Extend UnoCSS config with custom theme colors, glass-effect shadows, and reusable shortcuts. Create a global CSS file for `@keyframes` animations. Rewrite AppLayout from dark sidebar to sticky glass top-nav. Update ProjectLayout with new breadcrumb and tab styles.

**Tech Stack:** UnoCSS (shortcuts, theme), Vue 3 SFC, CSS @keyframes

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/uno.config.ts` | Modify | Theme colors, shadows, shortcuts |
| `frontend/src/assets/animations.css` | Create | @keyframes definitions |
| `frontend/src/main.ts` | Modify | Import animations.css |
| `frontend/src/components/AppLayout.vue` | Rewrite | Top nav bar |
| `frontend/src/components/ProjectLayout.vue` | Modify | New breadcrumb + tabs |
| `frontend/src/App.vue` | Modify | Page background |

---

### Task 1: UnoCSS Theme Configuration

**Files:**
- Modify: `frontend/uno.config.ts`

- [ ] **Step 1: Update uno.config.ts with theme, shadows, and shortcuts**

Replace the entire file with:

```typescript
import { defineConfig, presetUno, presetAttributify } from 'unocss'

export default defineConfig({
  presets: [
    presetUno(),
    presetAttributify(),
  ],
  theme: {
    colors: {
      primary: { DEFAULT: '#2563eb', light: '#3b82f6', dark: '#1d4ed8' },
      accent: '#06b6d4',
      surface: '#f0f4f8',
    },
    boxShadow: {
      'glass-xs': '0 1px 3px rgba(37,99,235,0.04)',
      'glass-sm': '0 4px 12px rgba(37,99,235,0.06)',
      'glass-md': '0 8px 24px rgba(37,99,235,0.08)',
      'glass-lg': '0 16px 40px rgba(37,99,235,0.12)',
    },
  },
  shortcuts: {
    'glass-card': 'bg-white/70 backdrop-blur-xl border border-blue-500/8 rounded-[14px] shadow-glass-sm transition-all duration-200',
    'glass-nav': 'bg-white/85 backdrop-blur-2xl border-b border-blue-500/6',
    'btn-primary': 'bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-[10px] font-semibold shadow-[0_2px_8px_rgba(37,99,235,0.3)] hover:shadow-[0_4px_16px_rgba(37,99,235,0.4)] hover:-translate-y-px transition-all duration-150 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed',
    'btn-secondary': 'bg-white text-blue-600 border border-blue-500/20 rounded-[10px] font-medium hover:border-blue-500/40 transition-all duration-150 cursor-pointer',
    'btn-ghost': 'bg-blue-50 text-blue-600 rounded-[10px] font-medium hover:bg-blue-100 transition-all duration-150 cursor-pointer',
    'btn-danger': 'bg-gradient-to-br from-red-500 to-red-600 text-white rounded-[10px] font-semibold shadow-[0_2px_8px_rgba(239,68,68,0.3)] hover:shadow-[0_4px_16px_rgba(239,68,68,0.4)] hover:-translate-y-px transition-all duration-150 cursor-pointer',
    'badge-base': 'px-2.5 py-1 rounded-full text-xs font-semibold border inline-flex items-center',
    'input-glass': 'w-full px-3.5 py-2.5 bg-white/70 backdrop-blur-sm border border-blue-500/12 rounded-[10px] text-sm outline-none focus:border-blue-500/30 focus:ring-2 focus:ring-blue-500/10 transition-all duration-150',
    'select-glass': 'w-full px-3.5 py-2.5 bg-white/70 backdrop-blur-sm border border-blue-500/12 rounded-[10px] text-sm outline-none focus:border-blue-500/30 focus:ring-2 focus:ring-blue-500/10 transition-all duration-150 cursor-pointer',
  },
})
```

- [ ] **Step 2: Verify UnoCSS compiles**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/uno.config.ts
git commit -m "feat(ui): add glass theme tokens, shadows, and UnoCSS shortcuts"
```

---

### Task 2: Animation Keyframes

**Files:**
- Create: `frontend/src/assets/animations.css`
- Modify: `frontend/src/main.ts`

- [ ] **Step 1: Create animations.css**

```css
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes progressFill {
  from { width: 0%; }
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
```

- [ ] **Step 2: Import in main.ts**

Replace `frontend/src/main.ts` with:

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

import 'virtual:uno.css'
import './assets/animations.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/assets/animations.css frontend/src/main.ts
git commit -m "feat(ui): add global CSS animation keyframes"
```

---

### Task 3: Top Navigation Bar (AppLayout)

**Files:**
- Modify: `frontend/src/App.vue`
- Rewrite: `frontend/src/components/AppLayout.vue`

- [ ] **Step 1: Rewrite AppLayout.vue as top navigation**

Replace the entire file with:

```vue
<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const navItems = [
  { name: 'Dashboard', routeName: 'home', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1' },
  { name: 'Projects', routeName: 'projects', icon: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z' },
  { name: 'Teams', routeName: 'teams', icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197' },
]

function isActive(routeName: string): boolean {
  if (routeName === 'home' && route.name === 'home') return true
  if (routeName === 'projects' && String(route.name).startsWith('project')) return true
  if (routeName === 'teams' && route.name === 'teams') return true
  return false
}

async function handleLogout() {
  await authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="min-h-screen bg-surface">
    <!-- Top Navigation Bar -->
    <header class="glass-nav sticky top-0 z-40 h-[56px] flex items-center px-6">
      <!-- Left: Logo -->
      <div class="flex items-center gap-2 mr-8">
        <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center">
          <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
        </div>
        <span class="text-base font-bold tracking-wide text-gray-900">OrgDev</span>
      </div>

      <!-- Center: Capsule Nav Switcher -->
      <nav class="flex items-center gap-1 bg-blue-500/4 rounded-full px-1.5 py-1">
        <router-link
          v-for="item in navItems"
          :key="item.routeName"
          :to="{ name: item.routeName }"
          :class="[
            'flex items-center gap-2 px-4 py-1.5 rounded-full text-[13px] font-medium transition-all duration-200',
            isActive(item.routeName)
              ? 'bg-white text-gray-900 shadow-glass-sm'
              : 'text-gray-500 hover:text-gray-700'
          ]"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" :d="item.icon" />
          </svg>
          {{ item.name }}
        </router-link>
      </nav>

      <!-- Right: User -->
      <div class="ml-auto flex items-center gap-3">
        <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-white text-xs font-bold">
          {{ (authStore.username || 'U').charAt(0).toUpperCase() }}
        </div>
        <span class="text-sm text-gray-600">{{ authStore.username || 'User' }}</span>
        <button
          class="text-xs text-gray-400 hover:text-gray-600 transition-colors ml-2"
          @click="handleLogout"
        >
          Logout
        </button>
      </div>
    </header>

    <!-- Main content -->
    <main class="p-6">
      <slot />
    </main>
  </div>
</template>
```

- [ ] **Step 2: Update App.vue for new background**

Replace `frontend/src/App.vue` with:

```vue
<script setup lang="ts">
import AppLayout from '@/components/AppLayout.vue'
import { useRoute } from 'vue-router'
const route = useRoute()
</script>

<template>
  <AppLayout v-if="!route.meta.hideLayout">
    <router-view />
  </AppLayout>
  <router-view v-else />
</template>
```

(Note: App.vue stays the same — the background is now set by AppLayout's `bg-surface`.)

- [ ] **Step 3: Verify dev server**

Run: `cd frontend && npm run build`
Expected: Build succeeds. The layout should now show a top nav bar instead of sidebar.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/AppLayout.vue frontend/src/App.vue
git commit -m "feat(ui): migrate sidebar to glass top navigation bar"
```

---

### Task 4: ProjectLayout Breadcrumb & Tabs

**Files:**
- Modify: `frontend/src/components/ProjectLayout.vue`

- [ ] **Step 1: Rewrite ProjectLayout.vue with glass styles**

Replace the entire file with:

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { ref, onMounted } from 'vue'
import api from '@/api'

const route = useRoute()

const projectId = computed(() => route.params.id as string)
const projectName = ref('')

const tabs = [
  { name: 'Overview', routeName: 'project-overview' },
  { name: 'Requirements', routeName: 'project-requirements' },
  { name: 'Tasks', routeName: 'project-tasks' },
  { name: 'Members', routeName: 'project-members' },
  { name: 'Settings', routeName: 'project-settings' },
]

function isActiveTab(routeName: string): boolean {
  if (route.name === routeName) return true
  if (routeName === 'project-requirements' && String(route.name).startsWith('requirement')) return true
  return false
}

onMounted(async () => {
  try {
    const response = await api.get(`/projects/${projectId.value}`)
    projectName.value = response.data.name || response.data.title || ''
  } catch {
    projectName.value = `Project ${projectId.value}`
  }
})
</script>

<template>
  <div>
    <!-- Breadcrumb -->
    <nav class="flex items-center gap-2 text-sm text-gray-500 mb-5">
      <router-link
        :to="{ name: 'projects' }"
        class="hover:text-gray-700 transition-colors"
      >
        Projects
      </router-link>
      <svg class="w-4 h-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
      </svg>
      <span class="text-gray-800 font-semibold">{{ projectName }}</span>
    </nav>

    <!-- Tab navigation -->
    <div class="flex gap-1 border-b border-blue-500/8 mb-6">
      <router-link
        v-for="tab in tabs"
        :key="tab.routeName"
        :to="{ name: tab.routeName, params: { id: projectId } }"
        :class="[
          'px-4 py-2.5 text-sm font-medium border-b-2 transition-all duration-200 -mb-px',
          isActiveTab(tab.routeName)
            ? 'border-blue-600 text-blue-600'
            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
        ]"
      >
        {{ tab.name }}
      </router-link>
    </div>

    <!-- Nested view -->
    <router-view />
  </div>
</template>
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ProjectLayout.vue
git commit -m "feat(ui): update project layout with glass breadcrumb and tabs"
```
