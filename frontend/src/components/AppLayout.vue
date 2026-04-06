<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { currentLocale, toggleLocale } from '@/locales'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const navItems = computed(() => [
  { name: t('nav.dashboard'), routeName: 'home', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1' },
  { name: t('nav.projects'), routeName: 'projects', icon: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z' },
  { name: t('nav.teams'), routeName: 'teams', icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197' },
])

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
        <button
          class="text-xs text-gray-400 hover:text-gray-600 transition-colors px-2 py-1 rounded-md hover:bg-gray-100"
          @click="toggleLocale"
        >
          {{ currentLocale() === 'en' ? '中文' : 'EN' }}
        </button>
        <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-white text-xs font-bold">
          {{ (authStore.username || 'U').charAt(0).toUpperCase() }}
        </div>
        <span class="text-sm text-gray-600">{{ authStore.username || 'User' }}</span>
        <button
          class="text-xs text-gray-400 hover:text-gray-600 transition-colors ml-2"
          @click="handleLogout"
        >
          {{ $t('common.logout') }}
        </button>
      </div>
    </header>

    <!-- Main content -->
    <main class="p-6">
      <slot />
    </main>
  </div>
</template>
