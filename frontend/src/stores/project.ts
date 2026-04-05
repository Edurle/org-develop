import { defineStore } from 'pinia'
import { ref } from 'vue'
import { projectApi } from '@/api/endpoints'
import type { Project } from '@/types'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)

  async function fetchList(teamId?: string) {
    const res = await projectApi.list(teamId)
    projects.value = res.data
  }

  async function fetchOne(id: string) {
    const res = await projectApi.get(id)
    currentProject.value = res.data
  }

  async function create(data: { team_id: string; name: string; slug: string; description?: string }) {
    const res = await projectApi.create(data)
    projects.value.push(res.data)
    return res.data
  }

  async function update(id: string, data: { name?: string; slug?: string; description?: string }) {
    const res = await projectApi.update(id, data)
    const idx = projects.value.findIndex((p) => p.id === id)
    if (idx !== -1) projects.value[idx] = res.data
    if (currentProject.value?.id === id) currentProject.value = res.data
    return res.data
  }

  async function remove(id: string) {
    await projectApi.delete(id)
    projects.value = projects.value.filter((p) => p.id !== id)
    if (currentProject.value?.id === id) currentProject.value = null
  }

  return { projects, currentProject, fetchList, fetchOne, create, update, remove }
})
