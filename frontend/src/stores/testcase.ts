import { defineStore } from 'pinia'
import { ref } from 'vue'
import { tcApi } from '@/api/endpoints'
import type { TestCase } from '@/types'

export const useTestcaseStore = defineStore('testcase', () => {
  const testCases = ref<TestCase[]>([])

  async function fetchList(testTaskId: string) {
    const res = await tcApi.list(testTaskId)
    testCases.value = res.data
  }

  async function create(
    testTaskId: string,
    data: {
      title: string
      preconditions?: string
      steps: string
      expected_result: string
      clause_ids?: string[]
    },
  ) {
    const res = await tcApi.create(testTaskId, data)
    testCases.value.push(res.data)
    return res.data
  }

  async function updateStatus(tcId: string, status: string) {
    const res = await tcApi.updateStatus(tcId, status)
    const idx = testCases.value.findIndex((tc) => tc.id === tcId)
    if (idx !== -1) testCases.value[idx] = res.data
    return res.data
  }

  async function update(tcId: string, data: {
    title?: string; preconditions?: string; steps?: string
    expected_result?: string; actual_result?: string
  }) {
    const res = await tcApi.update(tcId, data)
    const idx = testCases.value.findIndex((tc) => tc.id === tcId)
    if (idx !== -1) testCases.value[idx] = res.data
    return res.data
  }

  async function remove(tcId: string) {
    await tcApi.delete(tcId)
    testCases.value = testCases.value.filter((tc) => tc.id !== tcId)
  }

  return { testCases, fetchList, create, updateStatus, update, remove }
})
