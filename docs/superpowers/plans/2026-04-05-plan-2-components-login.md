# Plan 2: Core Components & Login Page

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign shared components (Modal, StatusBadge, EmptyState) with glass effects and gradient badges, then redesign the login page with a dark gradient background and glass card.

**Architecture:** Modal gets glass background + scale animation. StatusBadge switches to gradient pill badges with color-coded borders. EmptyState gets a softer visual treatment. Login page uses a full-screen dark gradient with decorative orbs and a glass login card.

**Tech Stack:** UnoCSS shortcuts (from Plan 1), Vue 3 SFC, CSS gradients

**Depends on:** Plan 1 (theme tokens and shortcuts)

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/src/components/Modal.vue` | Modify | Glass effect + animation |
| `frontend/src/components/StatusBadge.vue` | Modify | Gradient badges |
| `frontend/src/components/EmptyState.vue` | Modify | New visual style |
| `frontend/src/views/LoginView.vue` | Rewrite | Dark gradient + glass card |

---

### Task 1: Glass Modal with Animation

**Files:**
- Modify: `frontend/src/components/Modal.vue`

- [ ] **Step 1: Rewrite Modal.vue with glass effect**

Replace the entire file with:

```vue
<script setup lang="ts">
import { watch } from 'vue'

const props = defineProps<{
  show: boolean
  title: string
}>()

const emit = defineEmits<{
  close: []
}>()

function onBackdropClick() {
  emit('close')
}

watch(() => props.show, (value) => {
  document.body.style.overflow = value ? 'hidden' : ''
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center"
      >
        <!-- Backdrop -->
        <div
          class="absolute inset-0 bg-black/30 backdrop-blur-sm"
          @click="onBackdropClick"
        />

        <!-- Modal card -->
        <div class="relative bg-white/90 backdrop-blur-xl rounded-[20px] shadow-glass-lg border border-blue-500/8 w-full max-w-md mx-4">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-blue-500/8">
            <h2 class="text-base font-bold text-gray-900">{{ title }}</h2>
            <button
              class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors text-gray-400 hover:text-gray-600"
              @click="emit('close')"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="px-6 py-4">
            <slot />
          </div>

          <!-- Footer -->
          <div v-if="$slots.footer" class="px-6 py-4 border-t border-blue-500/8 flex justify-end gap-3">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active {
  transition: all 0.2s ease;
}
.modal-leave-active {
  transition: all 0.15s ease;
}
.modal-enter-from {
  opacity: 0;
}
.modal-enter-from > :last-child {
  transform: scale(0.95);
}
.modal-leave-to {
  opacity: 0;
}
.modal-leave-to > :last-child {
  transform: scale(0.95);
}
</style>
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/Modal.vue
git commit -m "feat(ui): glass modal with scale animation"
```

---

### Task 2: Gradient Status Badges

**Files:**
- Modify: `frontend/src/components/StatusBadge.vue`

- [ ] **Step 1: Rewrite StatusBadge.vue with gradient pills**

Replace the entire file with:

```vue
<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  status: string
  size?: 'sm' | 'md'
}>(), {
  size: 'md',
})

const badgeStyles: Record<string, { bg: string; text: string; border: string }> = {
  draft: { bg: 'bg-gradient-to-br from-gray-50 to-gray-100/50', text: 'text-gray-600', border: 'border-gray-200/60' },
  open: { bg: 'bg-gradient-to-br from-gray-50 to-gray-100/50', text: 'text-gray-600', border: 'border-gray-200/60' },
  spec_writing: { bg: 'bg-gradient-to-br from-blue-50 to-blue-100/50', text: 'text-blue-700', border: 'border-blue-200/60' },
  in_progress: { bg: 'bg-gradient-to-br from-blue-50 to-blue-100/50', text: 'text-blue-700', border: 'border-blue-300/70' },
  spec_review: { bg: 'bg-gradient-to-br from-amber-50 to-amber-100/50', text: 'text-amber-700', border: 'border-amber-200/60' },
  review: { bg: 'bg-gradient-to-br from-amber-50 to-amber-100/50', text: 'text-amber-700', border: 'border-amber-200/60' },
  reviewing: { bg: 'bg-gradient-to-br from-amber-50 to-amber-100/50', text: 'text-amber-700', border: 'border-amber-200/60' },
  spec_locked: { bg: 'bg-gradient-to-br from-emerald-50 to-emerald-100/50', text: 'text-emerald-700', border: 'border-emerald-200/60' },
  locked: { bg: 'bg-gradient-to-br from-emerald-50 to-emerald-100/50', text: 'text-emerald-700', border: 'border-emerald-200/60' },
  done: { bg: 'bg-gradient-to-br from-green-50 to-green-100/50', text: 'text-green-700', border: 'border-green-200/70' },
  passed: { bg: 'bg-gradient-to-br from-green-50 to-green-100/50', text: 'text-green-700', border: 'border-green-200/70' },
  testing: { bg: 'bg-gradient-to-br from-violet-50 to-violet-100/50', text: 'text-violet-700', border: 'border-violet-200/60' },
  running: { bg: 'bg-gradient-to-br from-violet-50 to-violet-100/50', text: 'text-violet-700', border: 'border-violet-200/60' },
  failed: { bg: 'bg-gradient-to-br from-red-50 to-red-100/50', text: 'text-red-700', border: 'border-red-200/60' },
  blocked: { bg: 'bg-gradient-to-br from-red-50 to-red-100/50', text: 'text-red-700', border: 'border-red-200/60' },
  cancelled: { bg: 'bg-gradient-to-br from-red-50 to-red-100/50', text: 'text-red-700', border: 'border-red-200/60' },
  rejected: { bg: 'bg-gradient-to-br from-red-50 to-red-100/50', text: 'text-red-700', border: 'border-red-200/60' },
  spec_rejected: { bg: 'bg-gradient-to-br from-red-50 to-red-100/50', text: 'text-red-700', border: 'border-red-200/60' },
}

const defaultStyle = { bg: 'bg-gradient-to-br from-gray-50 to-gray-100/50', text: 'text-gray-600', border: 'border-gray-200/60' }

const style = computed(() => badgeStyles[props.status] ?? defaultStyle)

const sizeClass = computed(() =>
  props.size === 'sm'
    ? 'px-2 py-0.5 text-[10px]'
    : 'px-2.5 py-1 text-[11px]'
)

function formatLabel(status: string): string {
  return status.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}
</script>

<template>
  <span
    :class="['inline-flex items-center rounded-full font-semibold border', style.bg, style.text, style.border, sizeClass]"
  >
    {{ formatLabel(status) }}
  </span>
</template>
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/StatusBadge.vue
git commit -m "feat(ui): gradient pill status badges"
```

---

### Task 3: EmptyState Component

**Files:**
- Modify: `frontend/src/components/EmptyState.vue`

- [ ] **Step 1: Update EmptyState.vue with new visual style**

Replace the entire file with:

```vue
<script setup lang="ts">
defineProps<{
  title: string
  description?: string
  actionLabel?: string
}>()

defineEmits<{
  action: []
}>()
</script>

<template>
  <div class="flex flex-col items-center justify-center py-16 text-center">
    <!-- Icon -->
    <div class="flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-100/60 mb-4">
      <svg class="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
      </svg>
    </div>

    <!-- Title -->
    <h3 class="text-sm font-bold text-gray-800 mb-1">{{ title }}</h3>

    <!-- Description -->
    <p v-if="description" class="text-xs text-gray-500 max-w-sm mb-4">
      {{ description }}
    </p>

    <!-- Action button -->
    <button
      v-if="actionLabel"
      class="mt-2 btn-primary px-5 py-2 text-sm"
      @click="$emit('action')"
    >
      {{ actionLabel }}
    </button>
  </div>
</template>
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/EmptyState.vue
git commit -m "feat(ui): update empty state with glass icon container"
```

---

### Task 4: Login Page Redesign

**Files:**
- Modify: `frontend/src/views/LoginView.vue`

- [ ] **Step 1: Rewrite LoginView.vue with dark gradient + glass card**

Replace the entire file with:

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await authStore.login(username.value, password.value)
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (err: any) {
    error.value = err?.response?.data?.detail || err?.message || 'Login failed. Please check your credentials.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-4 relative overflow-hidden"
    style="background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f4c75 100%);"
  >
    <!-- Decorative orbs -->
    <div class="absolute top-1/4 left-1/4 w-96 h-96 rounded-full opacity-20 pointer-events-none"
      style="background: radial-gradient(circle, #2563eb 0%, transparent 70%);"
    />
    <div class="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full opacity-15 pointer-events-none"
      style="background: radial-gradient(circle, #06b6d4 0%, transparent 70%);"
    />
    <div class="absolute top-1/2 right-1/3 w-64 h-64 rounded-full opacity-10 pointer-events-none"
      style="background: radial-gradient(circle, #8b5cf6 0%, transparent 70%);"
    />

    <!-- Login card -->
    <div class="relative w-full max-w-[380px] rounded-[20px] p-8 border border-white/12"
      style="background: rgba(255,255,255,0.08); backdrop-filter: blur(24px);"
    >
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 mb-3">
          <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
        </div>
        <h1 class="text-xl font-bold text-white">OrgDev</h1>
        <p class="text-sm text-white/50 mt-1">Sign in to your account</p>
      </div>

      <!-- Error message -->
      <div
        v-if="error"
        class="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-[10px] text-sm text-red-300"
      >
        {{ error }}
      </div>

      <!-- Login form -->
      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label for="username" class="block text-xs font-semibold text-white/60 mb-1.5">
            Username
          </label>
          <input
            id="username"
            v-model="username"
            type="text"
            autocomplete="username"
            required
            class="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-[10px] text-sm text-white placeholder-white/25 outline-none focus:border-blue-400/40 focus:ring-2 focus:ring-blue-400/15 transition-all duration-150"
            placeholder="Enter your username"
          />
        </div>

        <div>
          <label for="password" class="block text-xs font-semibold text-white/60 mb-1.5">
            Password
          </label>
          <input
            id="password"
            v-model="password"
            type="password"
            autocomplete="current-password"
            required
            class="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-[10px] text-sm text-white placeholder-white/25 outline-none focus:border-blue-400/40 focus:ring-2 focus:ring-blue-400/15 transition-all duration-150"
            placeholder="Enter your password"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full flex items-center justify-center px-4 py-2.5 text-sm font-semibold text-white bg-gradient-to-br from-blue-600 to-blue-700 rounded-[10px] shadow-[0_2px_12px_rgba(37,99,235,0.4)] hover:shadow-[0_4px_20px_rgba(37,99,235,0.5)] hover:-translate-y-px disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150 mt-2"
        >
          <svg
            v-if="loading"
            class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          {{ loading ? 'Signing in...' : 'Sign in' }}
        </button>
      </form>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Verify build and visual**

Run: `cd frontend && npm run build`
Expected: Build succeeds. Login page should show dark gradient background with glass card.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/LoginView.vue
git commit -m "feat(ui): dark gradient login page with glass card"
```
