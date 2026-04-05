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
