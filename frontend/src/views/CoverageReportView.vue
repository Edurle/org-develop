<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useCoverageStore } from '@/stores/coverage'
import EmptyState from '@/components/EmptyState.vue'

const route = useRoute()
const { t } = useI18n()
const coverageStore = useCoverageStore()

const reqId = computed(() => route.params.reqId as string)

const loading = ref(false)
const error = ref('')

const severityColorMap: Record<string, string> = {
  must: 'bg-gradient-to-br from-red-50 to-red-100/50 text-red-700 border-red-200/60',
  should: 'bg-gradient-to-br from-amber-50 to-amber-100/50 text-amber-700 border-amber-200/60',
  may: 'bg-gradient-to-br from-gray-50 to-gray-100/50 text-gray-600 border-gray-200/60',
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    await coverageStore.fetchReport(reqId.value)
  } catch (e: any) {
    error.value = e?.message || t('coverage.loadFailed')
  } finally {
    loading.value = false
  }
}

const overallPct = computed(() => {
  const r = coverageStore.report
  if (!r || r.total_clauses === 0) return 0
  return Math.round((r.covered_clauses / r.total_clauses) * 100)
})

function mustBarColor(pct: number): string {
  return pct === 100 ? 'bg-green-500' : 'bg-red-500'
}

function mustTextColor(pct: number): string {
  return pct === 100 ? 'text-green-600' : 'text-red-600'
}

function shouldBarColor(pct: number): string {
  if (pct >= 80) return 'bg-green-500'
  if (pct >= 50) return 'bg-yellow-500'
  return 'bg-red-500'
}

function shouldTextColor(pct: number): string {
  if (pct >= 80) return 'text-green-600'
  if (pct >= 50) return 'text-yellow-600'
  return 'text-red-600'
}

onMounted(loadData)
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-xl font-bold text-gray-900">{{ t('coverage.reportTitle') }}</h1>
    </div>

    <!-- Error -->
    <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200/60 rounded-[14px] text-red-700 text-sm">
      {{ error }}
    </div>

    <!-- Loading -->
    <div v-if="loading" class="py-12 text-center text-gray-500">{{ t('coverage.loadingCoverage') }}</div>

    <template v-else-if="coverageStore.report">
      <!-- Summary cards -->
      <div class="grid grid-cols-3 gap-3 mb-6">
        <div class="glass-card p-6 text-center">
          <div class="text-2xl font-bold text-gray-900">{{ coverageStore.report.total_clauses }}</div>
          <div class="text-xs text-gray-500 mt-1">{{ t('coverage.totalClauses') }}</div>
        </div>
        <div class="glass-card p-6 text-center">
          <div class="text-2xl font-bold text-emerald-600">{{ coverageStore.report.covered_clauses }}</div>
          <div class="text-xs text-gray-500 mt-1">{{ t('coverage.covered') }}</div>
        </div>
        <div class="glass-card p-6 text-center">
          <div class="text-2xl font-bold text-blue-600">{{ overallPct }}%</div>
          <div class="text-xs text-gray-500 mt-1">{{ t('coverage.overallCoverage') }}</div>
        </div>
      </div>

      <!-- Progress bars by severity -->
      <div class="glass-card p-6 mb-6">
        <h2 class="text-sm font-bold text-gray-900 mb-5">{{ t('coverage.coverageBySeverity') }}</h2>
        <div class="space-y-5">
          <!-- MUST -->
          <div>
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-sm font-semibold text-gray-700">{{ t('severity.must') }}</span>
              <span :class="['text-xs font-bold', mustTextColor(coverageStore.report.must_coverage_pct)]">
                {{ coverageStore.report.must_coverage_pct.toFixed(1) }}%
              </span>
            </div>
            <div class="w-full bg-gray-100 rounded-full h-2.5">
              <div
                :class="['h-2.5 rounded-full transition-all duration-700', mustBarColor(coverageStore.report.must_coverage_pct) === 'bg-green-500' ? 'bg-gradient-to-r from-emerald-400 to-emerald-500' : 'bg-gradient-to-r from-red-400 to-red-500']"
                :style="{ width: Math.max(coverageStore.report.must_coverage_pct, 0) + '%' }"
              />
            </div>
            <p class="text-[11px] text-gray-400 mt-1">{{ t('coverage.mustRequired') }}</p>
          </div>

          <!-- SHOULD -->
          <div>
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-sm font-semibold text-gray-700">{{ t('severity.should') }}</span>
              <span :class="['text-xs font-bold', shouldTextColor(coverageStore.report.should_coverage_pct)]">
                {{ coverageStore.report.should_coverage_pct.toFixed(1) }}%
              </span>
            </div>
            <div class="w-full bg-gray-100 rounded-full h-2.5">
              <div
                :class="['h-2.5 rounded-full transition-all duration-700', shouldBarColor(coverageStore.report.should_coverage_pct) === 'bg-green-500' ? 'bg-gradient-to-r from-emerald-400 to-emerald-500' : shouldBarColor(coverageStore.report.should_coverage_pct) === 'bg-yellow-500' ? 'bg-gradient-to-r from-amber-400 to-amber-500' : 'bg-gradient-to-r from-red-400 to-red-500']"
                :style="{ width: Math.max(coverageStore.report.should_coverage_pct, 0) + '%' }"
              />
            </div>
            <p class="text-[11px] text-gray-400 mt-1">{{ t('coverage.shouldTarget') }}</p>
          </div>

          <!-- MAY -->
          <div>
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-sm font-semibold text-gray-700">{{ t('severity.may') }}</span>
              <span class="text-xs font-bold text-gray-400">{{ coverageStore.report.may_coverage_pct.toFixed(1) }}%</span>
            </div>
            <div class="w-full bg-gray-100 rounded-full h-2.5">
              <div
                class="h-2.5 rounded-full bg-gradient-to-r from-gray-300 to-gray-400 transition-all duration-700"
                :style="{ width: Math.max(coverageStore.report.may_coverage_pct, 0) + '%' }"
              />
            </div>
            <p class="text-[11px] text-gray-400 mt-1">{{ t('coverage.mayInfo') }}</p>
          </div>
        </div>
      </div>

      <!-- Uncovered clauses table -->
      <div class="glass-card overflow-hidden">
        <div class="px-5 py-3 border-b border-blue-500/8">
          <h2 class="text-sm font-bold text-gray-900">
            {{ t('coverage.uncoveredClauses') }} ({{ coverageStore.report.uncovered_clauses.length }})
          </h2>
        </div>

        <EmptyState
          v-if="coverageStore.report.uncovered_clauses.length === 0"
          :title="t('coverage.allClausesCovered')"
          :description="t('coverage.allClausesCoveredDesc')"
        />

        <table v-else class="w-full text-sm">
          <thead>
            <tr class="border-b border-blue-500/5">
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('coverage.clauseId') }}</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('common.title') }}</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('coverage.severity') }}</th>
              <th class="text-left px-5 py-3 text-xs font-semibold text-gray-500">{{ t('coverage.category') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-blue-500/5">
            <tr
              v-for="clause in coverageStore.report.uncovered_clauses"
              :key="clause.id"
              class="hover:bg-blue-500/[0.01] transition-colors"
            >
              <td class="px-5 py-3 font-mono text-xs text-gray-600">{{ clause.clause_id }}</td>
              <td class="px-5 py-3 text-gray-900">{{ clause.title }}</td>
              <td class="px-5 py-3">
                <span :class="['badge-base', severityColorMap[clause.severity] ?? 'bg-gray-50 text-gray-600 border-gray-200/60']">
                  {{ t(`severity.${clause.severity}`) }}
                </span>
              </td>
              <td class="px-5 py-3 text-gray-500">{{ clause.category }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
