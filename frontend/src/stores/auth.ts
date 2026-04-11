import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

interface User {
  id: string
  username: string
  email: string
}

function decodeJwtPayload(token: string): Record<string, unknown> {
  try {
    const base64 = token.split('.')[1]
    if (!base64) return {}
    const json = atob(base64.replace(/-/g, '+').replace(/_/g, '/'))
    return JSON.parse(json)
  } catch {
    return {}
  }
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refreshToken'))

  const isAuthenticated = computed(() => !!token.value)
  const username = computed(() => {
    if (user.value) return user.value.username
    if (token.value) return (decodeJwtPayload(token.value).username as string) ?? ''
    return ''
  })

  // Restore user from token on init
  if (token.value && !user.value) {
    const payload = decodeJwtPayload(token.value)
    if (payload.sub && payload.username) {
      user.value = { id: payload.sub as string, username: payload.username as string, email: '' }
    }
  }

  async function login(loginUsername: string, password: string) {
    const response = await api.post('/auth/login', { username: loginUsername, password })
    const { access_token, refresh_token } = response.data

    token.value = access_token
    refreshToken.value = refresh_token

    const payload = decodeJwtPayload(access_token)
    user.value = {
      id: (payload.sub as string) ?? '',
      username: (payload.username as string) ?? '',
      email: '',
    }

    localStorage.setItem('token', access_token)
    localStorage.setItem('refreshToken', refresh_token)
  }

  async function register(username: string, email: string, password: string, displayName?: string) {
    const response = await api.post('/auth/register', {
      username,
      email,
      password,
      display_name: displayName || undefined,
    })
    const { access_token, refresh_token } = response.data

    token.value = access_token
    refreshToken.value = refresh_token

    const payload = decodeJwtPayload(access_token)
    user.value = {
      id: (payload.sub as string) ?? '',
      username: (payload.username as string) ?? '',
      email,
    }

    localStorage.setItem('token', access_token)
    localStorage.setItem('refreshToken', refresh_token)
  }

  async function logout() {
    token.value = null
    refreshToken.value = null
    user.value = null

    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
  }

  async function refresh() {
    if (!refreshToken.value) {
      throw new Error('No refresh token available')
    }

    const response = await api.post('/auth/refresh', {
      refresh_token: refreshToken.value,
    })
    const { access_token, refresh_token: newRefreshToken } = response.data

    token.value = access_token
    refreshToken.value = newRefreshToken

    localStorage.setItem('token', access_token)
    localStorage.setItem('refreshToken', newRefreshToken)
  }

  return {
    user,
    token,
    refreshToken,
    isAuthenticated,
    username,
    login,
    register,
    logout,
    refresh,
  }
})
