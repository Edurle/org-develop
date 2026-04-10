<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const displayName = ref('')
const loading = ref(false)
const error = ref('')

const passwordMismatch = computed(() =>
  confirmPassword.value.length > 0 && password.value !== confirmPassword.value
)

async function handleRegister() {
  error.value = ''

  if (!username.value || !email.value || !password.value) {
    error.value = t('auth.errorAllFieldsRequired')
    return
  }
  if (password.value !== confirmPassword.value) {
    error.value = t('auth.errorPasswordMismatch')
    return
  }
  if (password.value.length < 6) {
    error.value = t('auth.errorPasswordMin')
    return
  }

  loading.value = true
  try {
    await authStore.register(
      username.value,
      email.value,
      password.value,
      displayName.value || undefined,
    )
    router.push('/')
  } catch (err: any) {
    const detail = err?.response?.data?.detail
    if (typeof detail === 'string' && detail.includes('already')) {
      error.value = t('auth.errorUserExists')
    } else {
      error.value = detail || err?.message || t('auth.errorRegisterFailed')
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-4 relative overflow-hidden"
    style="background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f4c75 100%);"
  >
    <!-- Decorative orbs -->
    <div class="absolute top-1/4 left-1/4 w-96 h-96 rounded-full opacity-20 pointer-events-none"
      style="background: radial-gradient(circle, #2563eb 0%, transparent 70%);"
    />
    <div class="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full opacity-15 pointer-events-none"
      style="background: radial-gradient(circle, #06b6d4 0%, transparent 70%);"
    />
    <div class="absolute top-1/2 right-1/3 w-64 h-64 rounded-full opacity-10 pointer-events-none"
      style="background: radial-gradient(circle, #8b5cf6 0%, transparent 70%);"
    />

    <!-- Register card -->
    <div class="relative w-full max-w-[400px] rounded-[20px] p-8 border border-white/12"
      style="background: rgba(255,255,255,0.08); backdrop-filter: blur(24px);"
    >
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 mb-3">
          <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
        </div>
        <h1 class="text-xl font-bold text-white">OrgDev</h1>
        <p class="text-sm text-white/50 mt-1">{{ t('auth.createYourAccount') }}</p>
      </div>

      <!-- Error message -->
      <div
        v-if="error"
        class="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-[10px] text-sm text-red-300"
      >
        {{ error }}
      </div>

      <!-- Register form -->
      <form @submit.prevent="handleRegister" class="space-y-4">
        <div>
          <label for="username" class="block text-xs font-semibold text-white/60 mb-1.5">
            {{ t('auth.username') }} <span class="text-red-400">*</span>
          </label>
          <input
            id="username"
            v-model="username"
            type="text"
            autocomplete="username"
            required
            class="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-[10px] text-sm text-white placeholder-white/25 outline-none focus:border-blue-400/40 focus:ring-2 focus:ring-blue-400/15 transition-all duration-150"
            :placeholder="t('auth.chooseUsername')"
          />
        </div>

        <div>
          <label for="email" class="block text-xs font-semibold text-white/60 mb-1.5">
            {{ t('auth.email') }} <span class="text-red-400">*</span>
          </label>
          <input
            id="email"
            v-model="email"
            type="email"
            autocomplete="email"
            required
            class="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-[10px] text-sm text-white placeholder-white/25 outline-none focus:border-blue-400/40 focus:ring-2 focus:ring-blue-400/15 transition-all duration-150"
            :placeholder="t('auth.emailPlaceholder')"
          />
        </div>

        <div>
          <label for="display-name" class="block text-xs font-semibold text-white/60 mb-1.5">
            {{ t('auth.displayName') }}
          </label>
          <input
            id="display-name"
            v-model="displayName"
            type="text"
            autocomplete="name"
            class="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-[10px] text-sm text-white placeholder-white/25 outline-none focus:border-blue-400/40 focus:ring-2 focus:ring-blue-400/15 transition-all duration-150"
            :placeholder="t('auth.displayNamePlaceholder')"
          />
        </div>

        <div>
          <label for="password" class="block text-xs font-semibold text-white/60 mb-1.5">
            {{ t('auth.password') }} <span class="text-red-400">*</span>
          </label>
          <input
            id="password"
            v-model="password"
            type="password"
            autocomplete="new-password"
            required
            class="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-[10px] text-sm text-white placeholder-white/25 outline-none focus:border-blue-400/40 focus:ring-2 focus:ring-blue-400/15 transition-all duration-150"
            :placeholder="t('auth.passwordMin')"
          />
        </div>

        <div>
          <label for="confirm-password" class="block text-xs font-semibold text-white/60 mb-1.5">
            {{ t('auth.confirmPassword') }} <span class="text-red-400">*</span>
          </label>
          <input
            id="confirm-password"
            v-model="confirmPassword"
            type="password"
            autocomplete="new-password"
            required
            class="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-[10px] text-sm text-white placeholder-white/25 outline-none focus:border-blue-400/40 focus:ring-2 focus:ring-blue-400/15 transition-all duration-150"
            :class="{ '!border-red-400/40': passwordMismatch }"
            :placeholder="t('auth.repeatPassword')"
          />
          <p v-if="passwordMismatch" class="mt-1 text-xs text-red-300">{{ t('auth.passwordMismatch') }}</p>
        </div>

        <button
          type="submit"
          :disabled="loading || passwordMismatch"
          class="w-full flex items-center justify-center px-4 py-2.5 text-sm font-semibold text-white bg-gradient-to-br from-blue-600 to-blue-700 rounded-full shadow-[0_2px_12px_rgba(37,99,235,0.4)] hover:shadow-[0_4px_20px_rgba(37,99,235,0.5)] hover:-translate-y-px disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150 mt-2"
        >
          <svg
            v-if="loading"
            class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          {{ loading ? t('auth.creatingAccount') : t('auth.createAccount') }}
        </button>
      </form>

      <!-- Link to login -->
      <p class="mt-6 text-center text-sm text-white/40">
        {{ t('auth.alreadyHaveAccount') }}
        <router-link to="/login" class="text-blue-400 hover:text-blue-300 transition-colors font-medium">
          {{ t('auth.signIn') }}
        </router-link>
      </p>
    </div>
  </div>
</template>
