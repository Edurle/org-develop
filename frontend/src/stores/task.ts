import { defineStore } from 'pinia'
import { ref } from 'vue'
import { taskApi } from '@/api/endpoints'
import type { DevTask, TestTask } from '@/types'

export const useTaskStore = defineStore('task', () => {
  const devTasks = ref<DevTask[]>([])
  const testTasks = ref<TestTask[]>([])

  async function fetchDevTasks(projectId: string) {
    const res = await taskApi.listDevTasks(projectId)
    devTasks.value = res.data
  }

  async function fetchTestTasks(projectId: string) {
    const res = await taskApi.listTestTasks(projectId)
    testTasks.value = res.data
  }

  async function createDevTask(
    reqId: string,
    data: {
      spec_version_id: string
      iteration_id: string
      title: string
      estimate_hours?: number
    },
  ) {
    const res = await taskApi.createDevTask(reqId, data)
    devTasks.value.push(res.data)
    return res.data
  }

  async function claimDevTask(taskId: string) {
    const res = await taskApi.claimDevTask(taskId)
    const idx = devTasks.value.findIndex((t) => t.id === taskId)
    if (idx !== -1) devTasks.value[idx] = res.data
    return res.data
  }

  async function updateDevTaskStatus(taskId: string, status: string) {
    const res = await taskApi.updateDevTaskStatus(taskId, status)
    const idx = devTasks.value.findIndex((t) => t.id === taskId)
    if (idx !== -1) devTasks.value[idx] = res.data
    return res.data
  }

  async function createTestTask(reqId: string, data: { iteration_id: string; title: string }) {
    const res = await taskApi.createTestTask(reqId, data)
    testTasks.value.push(res.data)
    return res.data
  }

  async function updateDevTask(id: string, data: {
    title?: string; estimate_hours?: number | null; assignee_id?: string | null
  }) {
    const res = await taskApi.updateDevTask(id, data)
    const idx = devTasks.value.findIndex((t) => t.id === id)
    if (idx !== -1) devTasks.value[idx] = res.data
    return res.data
  }

  async function removeDevTask(id: string) {
    await taskApi.deleteDevTask(id)
    devTasks.value = devTasks.value.filter((t) => t.id !== id)
  }

  return {
    devTasks,
    testTasks,
    fetchDevTasks,
    fetchTestTasks,
    createDevTask,
    claimDevTask,
    updateDevTaskStatus,
    createTestTask,
    updateDevTask,
    removeDevTask,
  }
})
