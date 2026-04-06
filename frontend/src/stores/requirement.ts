import { defineStore } from 'pinia'
import { ref } from 'vue'
import { reqApi } from '@/api/endpoints'
import type { Requirement } from '@/types'

export const useRequirementStore = defineStore('requirement', () => {
  const requirements = ref<Requirement[]>([])
  const currentRequirement = ref<Requirement | null>(null)

  async function fetchList(projectId: string, params?: { iteration_id?: string; status?: string }) {
    const res = await reqApi.list(projectId, params)
    requirements.value = res.data
  }

  async function fetchOne(id: string) {
    const res = await reqApi.get(id)
    currentRequirement.value = res.data
  }

  async function create(projectId: string, data: { iteration_id: string; title: string; priority?: string }) {
    const res = await reqApi.create(projectId, data)
    requirements.value.push(res.data)
    return res.data
  }

  async function updateStatus(id: string, status: string) {
    const res = await reqApi.updateStatus(id, status)
    const idx = requirements.value.findIndex((r) => r.id === id)
    if (idx !== -1) requirements.value[idx] = res.data
    if (currentRequirement.value?.id === id) currentRequirement.value = res.data
    return res.data
  }

  async function update(id: string, data: { title?: string; priority?: string }) {
    const res = await reqApi.update(id, data)
    const idx = requirements.value.findIndex((r) => r.id === id)
    if (idx !== -1) requirements.value[idx] = res.data
    if (currentRequirement.value?.id === id) currentRequirement.value = res.data
    return res.data
  }

  async function remove(id: string) {
    await reqApi.delete(id)
    requirements.value = requirements.value.filter((r) => r.id !== id)
    if (currentRequirement.value?.id === id) currentRequirement.value = null
  }

  return { requirements, currentRequirement, fetchList, fetchOne, create, updateStatus, update, remove }
})
