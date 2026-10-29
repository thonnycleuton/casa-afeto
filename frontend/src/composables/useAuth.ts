import { computed, ref } from 'vue'
import type { UserProfile } from '../api/types'
import { login as apiLogin, logout as apiLogout, getMe as apiGetMe, refresh as apiRefresh } from '../api/auth'

const ACCESS_TOKEN_KEY = 'casa_afeto_access_token'
const REFRESH_TOKEN_KEY = 'casa_afeto_refresh_token'

export function useAuth() {
  const accessToken = ref<string | null>(
    localStorage.getItem(ACCESS_TOKEN_KEY)
  )
  const refreshToken = ref<string | null>(
    localStorage.getItem(REFRESH_TOKEN_KEY)
  )
  const user = ref<UserProfile | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => accessToken.value !== null)
  const isAdmin = computed(() => user.value?.role === 'admin')

  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    try {
      localStorage.setItem(ACCESS_TOKEN_KEY, access)
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
    } catch {
      // localStorage unavailable
    }
  }

  function clearTokens() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    try {
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
    } catch {
      // localStorage unavailable
    }
  }

  async function login(email: string, password: string) {
    loading.value = true
    error.value = null
    try {
      const tokens = await apiLogin({ email, password })
      setTokens(tokens.access_token, tokens.refresh_token)
      await fetchProfile()
      return true
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Erro ao fazer login'
      return false
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    if (refreshToken.value) {
      try {
        await apiLogout(refreshToken.value)
      } catch {
        // Ignore logout errors
      }
    }
    clearTokens()
  }

  async function fetchProfile() {
    if (!accessToken.value) return
    try {
      user.value = await apiGetMe()
    } catch {
      clearTokens()
    }
  }

  async function tryRefresh(): Promise<string | null> {
    if (!refreshToken.value) return null
    try {
      const tokens = await apiRefresh(refreshToken.value)
      setTokens(tokens.access_token, tokens.refresh_token)
      return tokens.access_token
    } catch {
      clearTokens()
      return null
    }
  }

  async function init() {
    if (accessToken.value) {
      await fetchProfile()
    }
  }

  return {
    accessToken,
    refreshToken,
    user,
    loading,
    error,
    isAuthenticated,
    isAdmin,
    login,
    logout,
    fetchProfile,
    tryRefresh,
    clearTokens,
    init,
  }
}
