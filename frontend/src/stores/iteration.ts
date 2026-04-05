import { defineStore } from 'pinia'
import { ref } from 'vue'
import { iterationApi } from '@/api/endpoints'
import type { Iteration } from '@/types'

export const useIterationStore = defineStore('iteration', () => {
  const iterations = ref<Iteration[]>([])

  async function fetchList(projectId: string) {
    const res = await iterationApi.list(projectId)
    iterations.value = res.data
  }

  async function create(projectId: string, data: { name: string; start_date?: string; end_date?: string }) {
    const res = await iterationApi.create(projectId, data)
    iterations.value.push(res.data)
    return res.data
  }

  async function update(projectId: string, id: string, data: { name?: string; status?: string }) {
    const res = await iterationApi.update(projectId, id, data)
    const idx = iterations.value.findIndex((i) => i.id === id)
    if (idx !== -1) iterations.value[idx] = res.data
    return res.data
  }

  return { iterations, fetchList, create, update }
})
