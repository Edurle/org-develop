<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await authStore.login(username.value, password.value)
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (err: any) {
    error.value = err?.response?.data?.detail || err?.message || t('auth.errorLoginFailed')
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

    <!-- Login card -->
    <div class="relative w-full max-w-[380px] rounded-[20px] p-8 border border-white/12"
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
        <p class="text-sm text-white/50 mt-1">{{ t('auth.signInToAccount') }}</p>
      </div>

      <!-- Error message -->
      <div
        v-if="error"
        class="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-[10px] text-sm text-red-300"
      >
        {{ error }}
      </div>

      <!-- Login form -->
      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label for="username" class="block text-xs font-semibold text-white/60 mb-1.5">
            {{ t('auth.username') }}
          </label>
          <input
            id="username"
            v-model="username"
            type="text"
            autocomplete="username"
            required
            class="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-[10px] text-sm text-white placeholder-white/25 outline-none focus:border-blue-400/40 focus:ring-2 focus:ring-blue-400/15 transition-all duration-150"
            :placeholder="t('auth.enterUsername')"
          />
        </div>

        <div>
          <label for="password" class="block text-xs font-semibold text-white/60 mb-1.5">
            {{ t('auth.password') }}
          </label>
          <input
            id="password"
            v-model="password"
            type="password"
            autocomplete="current-password"
            required
            class="w-full px-3.5 py-2.5 bg-white/5 border border-white/10 rounded-[10px] text-sm text-white placeholder-white/25 outline-none focus:border-blue-400/40 focus:ring-2 focus:ring-blue-400/15 transition-all duration-150"
            :placeholder="t('auth.enterPassword')"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
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
          {{ loading ? t('auth.signingIn') : t('auth.signIn') }}
        </button>
      </form>

      <!-- Link to register -->
      <p class="mt-6 text-center text-sm text-white/40">
        {{ t('auth.noAccount') }}
        <router-link to="/register" class="text-blue-400 hover:text-blue-300 transition-colors font-medium">
          {{ t('auth.createOne') }}
        </router-link>
      </p>
    </div>
  </div>
</template>
