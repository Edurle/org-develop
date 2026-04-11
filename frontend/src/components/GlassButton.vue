<script setup lang="ts">
import { computed, useSlots } from 'vue'

const props = withDefaults(defineProps<{
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success' | 'warning' | 'auth'
  size?: 'small' | 'default' | 'large'
  disabled?: boolean
  loading?: boolean
}>(), {
  variant: 'primary',
  size: 'default',
  disabled: false,
  loading: false,
})

defineEmits<{
  click: [event: MouseEvent]
}>()

const slots = useSlots()

const isIconOnly = computed(() => {
  const defaultSlot = slots.default?.()
  if (!defaultSlot) return false
  const text = defaultSlot
    .map((vnode) => {
      if (typeof vnode.children === 'string') return vnode.children
      return ''
    })
    .join('')
    .trim()
  return text.length === 0
})

const sizeClasses = computed(() => {
  if (isIconOnly.value) {
    switch (props.size) {
      case 'small': return 'p-1'
      case 'large': return 'p-2.5'
      default: return 'p-1.5'
    }
  }
  switch (props.size) {
    case 'small': return 'px-3 py-1.5 text-xs'
    case 'large': return 'px-5 py-2.5 text-sm'
    default: return 'px-4 py-2 text-sm'
  }
})

const variantClasses = computed(() => {
  const variants: Record<string, string> = {
    primary: 'bg-white/60 backdrop-blur-md text-blue-600 border border-white/40 font-semibold shadow-glass-sm hover:bg-white/80 hover:shadow-glass-md hover:-translate-y-px',
    secondary: 'bg-white/50 backdrop-blur-sm text-gray-600 border border-white/30 font-medium hover:bg-white/70 hover:border-white/50',
    ghost: 'bg-transparent text-blue-600 border border-transparent font-medium hover:bg-white/40 hover:border-white/30',
    danger: 'bg-red-500/15 backdrop-blur-sm text-red-600 border border-red-500/20 font-semibold hover:bg-red-500/25 hover:border-red-500/40 hover:-translate-y-px',
    success: 'bg-green-500/15 backdrop-blur-sm text-green-600 border border-green-500/20 font-semibold hover:bg-green-500/25 hover:border-green-500/40 hover:-translate-y-px',
    warning: 'bg-amber-500/15 backdrop-blur-sm text-amber-700 border border-amber-500/20 font-semibold hover:bg-amber-500/25 hover:border-amber-500/40 hover:-translate-y-px',
    auth: 'bg-gradient-to-br from-blue-600 to-blue-700 text-white border-none font-semibold shadow-[0_2px_12px_rgba(37,99,235,0.4)] hover:shadow-[0_4px_20px_rgba(37,99,235,0.5)] hover:-translate-y-px',
  }
  return variants[props.variant]
})

const baseClasses = 'rounded-full transition-all duration-150 cursor-pointer inline-flex items-center justify-center gap-1.5'
const disabledClasses = 'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:transform-none'
</script>

<template>
  <button
    :class="[baseClasses, disabledClasses, sizeClasses, variantClasses]"
    :disabled="disabled || loading"
    @click="$emit('click', $event)"
  >
    <svg
      v-if="loading"
      class="animate-spin w-4 h-4"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
    </svg>
    <slot />
  </button>
</template>
