import { defineStore } from 'pinia'
import { ref } from 'vue'
import { coverageApi } from '@/api/endpoints'
import type { CoverageReport, CoverageCheck } from '@/types'

export const useCoverageStore = defineStore('coverage', () => {
  const report = ref<CoverageReport | null>(null)
  const check = ref<CoverageCheck | null>(null)

  async function fetchReport(reqId: string) {
    const res = await coverageApi.report(reqId)
    report.value = res.data
  }

  async function checkSufficient(reqId: string) {
    const res = await coverageApi.check(reqId)
    check.value = res.data
    return res.data
  }

  return { report, check, fetchReport, checkSufficient }
})
