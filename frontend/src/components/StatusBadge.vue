<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = withDefaults(defineProps<{
  status: string
  size?: 'sm' | 'md'
}>(), {
  size: 'md',
})

const badgeStyles: Record<string, { bg: string; text: string; border: string }> = {
  draft: { bg: 'bg-gradient-to-br from-gray-50 to-gray-100/50', text: 'text-gray-600', border: 'border-gray-200/60' },
  open: { bg: 'bg-gradient-to-br from-gray-50 to-gray-100/50', text: 'text-gray-600', border: 'border-gray-200/60' },
  spec_writing: { bg: 'bg-gradient-to-br from-blue-50 to-blue-100/50', text: 'text-blue-700', border: 'border-blue-200/60' },
  in_progress: { bg: 'bg-gradient-to-br from-blue-50 to-blue-100/50', text: 'text-blue-700', border: 'border-blue-300/70' },
  spec_review: { bg: 'bg-gradient-to-br from-amber-50 to-amber-100/50', text: 'text-amber-700', border: 'border-amber-200/60' },
  review: { bg: 'bg-gradient-to-br from-amber-50 to-amber-100/50', text: 'text-amber-700', border: 'border-amber-200/60' },
  reviewing: { bg: 'bg-gradient-to-br from-amber-50 to-amber-100/50', text: 'text-amber-700', border: 'border-amber-200/60' },
  spec_locked: { bg: 'bg-gradient-to-br from-emerald-50 to-emerald-100/50', text: 'text-emerald-700', border: 'border-emerald-200/60' },
  locked: { bg: 'bg-gradient-to-br from-emerald-50 to-emerald-100/50', text: 'text-emerald-700', border: 'border-emerald-200/60' },
  done: { bg: 'bg-gradient-to-br from-green-50 to-green-100/50', text: 'text-green-700', border: 'border-green-200/70' },
  passed: { bg: 'bg-gradient-to-br from-green-50 to-green-100/50', text: 'text-green-700', border: 'border-green-200/70' },
  testing: { bg: 'bg-gradient-to-br from-violet-50 to-violet-100/50', text: 'text-violet-700', border: 'border-violet-200/60' },
  running: { bg: 'bg-gradient-to-br from-violet-50 to-violet-100/50', text: 'text-violet-700', border: 'border-violet-200/60' },
  failed: { bg: 'bg-gradient-to-br from-red-50 to-red-100/50', text: 'text-red-700', border: 'border-red-200/60' },
  blocked: { bg: 'bg-gradient-to-br from-red-50 to-red-100/50', text: 'text-red-700', border: 'border-red-200/60' },
  cancelled: { bg: 'bg-gradient-to-br from-red-50 to-red-100/50', text: 'text-red-700', border: 'border-red-200/60' },
  rejected: { bg: 'bg-gradient-to-br from-red-50 to-red-100/50', text: 'text-red-700', border: 'border-red-200/60' },
  spec_rejected: { bg: 'bg-gradient-to-br from-red-50 to-red-100/50', text: 'text-red-700', border: 'border-red-200/60' },
}

const defaultStyle = { bg: 'bg-gradient-to-br from-gray-50 to-gray-100/50', text: 'text-gray-600', border: 'border-gray-200/60' }

const style = computed(() => badgeStyles[props.status] ?? defaultStyle)

const sizeClass = computed(() =>
  props.size === 'sm'
    ? 'px-2 py-0.5 text-[10px]'
    : 'px-2.5 py-1 text-[11px]'
)


</script>

<template>
  <span
    :class="['inline-flex items-center rounded-full font-semibold border', style.bg, style.text, style.border, sizeClass]"
  >
    {{ t(`status.${status}`) }}
  </span>
</template>
