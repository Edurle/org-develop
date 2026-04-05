import { defineStore } from 'pinia'
import { ref } from 'vue'
import { specApi } from '@/api/endpoints'
import type { Specification, SpecVersion, SpecClause } from '@/types'

export const useSpecificationStore = defineStore('specification', () => {
  const specs = ref<Specification[]>([])
  const currentSpec = ref<Specification | null>(null)
  const versions = ref<SpecVersion[]>([])
  const currentVersion = ref<SpecVersion | null>(null)
  const clauses = ref<SpecClause[]>([])

  async function fetchList(reqId: string) {
    const res = await specApi.list(reqId)
    specs.value = res.data
  }

  async function create(reqId: string, data: { spec_type: string; title: string }) {
    const res = await specApi.create(reqId, data)
    specs.value.push(res.data)
    return res.data
  }

  async function fetchVersions(specId: string) {
    const res = await specApi.listVersions(specId)
    versions.value = res.data
  }

  async function createVersion(specId: string, content: Record<string, unknown>) {
    const res = await specApi.createVersion(specId, content)
    versions.value.push(res.data)
    return res.data
  }

  async function submitForReview(versionId: string) {
    const res = await specApi.submitForReview(versionId)
    const idx = versions.value.findIndex((v) => v.id === versionId)
    if (idx !== -1) versions.value[idx] = res.data
    if (currentVersion.value?.id === versionId) currentVersion.value = res.data
    return res.data
  }

  async function lock(versionId: string) {
    const res = await specApi.lock(versionId)
    const idx = versions.value.findIndex((v) => v.id === versionId)
    if (idx !== -1) versions.value[idx] = res.data
    if (currentVersion.value?.id === versionId) currentVersion.value = res.data
    return res.data
  }

  async function reject(versionId: string) {
    const res = await specApi.reject(versionId)
    const idx = versions.value.findIndex((v) => v.id === versionId)
    if (idx !== -1) versions.value[idx] = res.data
    if (currentVersion.value?.id === versionId) currentVersion.value = res.data
    return res.data
  }

  async function fetchClauses(versionId: string) {
    const res = await specApi.listClauses(versionId)
    clauses.value = res.data
  }

  async function createClause(
    versionId: string,
    data: {
      clause_id: string
      title: string
      description: string
      category: string
      severity?: string
    },
  ) {
    const res = await specApi.createClause(versionId, data)
    clauses.value.push(res.data)
    return res.data
  }

  return {
    specs,
    currentSpec,
    versions,
    currentVersion,
    clauses,
    fetchList,
    create,
    fetchVersions,
    createVersion,
    submitForReview,
    lock,
    reject,
    fetchClauses,
    createClause,
  }
})
