/**
 * 用户状态管理 Store
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, UserProfile, UpdateProfileRequest } from '@/types/user'
import * as authAPI from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  // State
  const user = ref<User | null>(null)
  const isLoggedIn = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const _restored = ref(false)  // Track if restoration was attempted

  // Computed
  const userProfile = computed(() => user.value as UserProfile | null)
  const userId = computed(() => user.value?.id)
  const username = computed(() => user.value?.username)
  const userRole = computed(() => user.value?.role)
  const isAdmin = computed(() => user.value?.role === 'admin')

  // Helper: Restore user from localStorage if not yet restored
  const _ensureRestored = () => {
    if (!_restored.value) {
      restoreFromStorage()
      _restored.value = true
    }
  }

  // Helper: strip sensitive fields before persisting to localStorage
  const _safeUserForStorage = (u: User): Partial<User> => {
    // Only persist non-sensitive identity fields
    const { id, username, email, role, avatar, nickname } = u as User & {
      avatar?: string
      nickname?: string
    }
    return { id, username, email, role, avatar, nickname }
  }

  // Actions
  const login = async (username: string, password: string) => {
    loading.value = true
    error.value = null
    try {
      const response = await authAPI.login({ username, password })
      user.value = response.user
      isLoggedIn.value = true
      localStorage.setItem('token', response.token)
      localStorage.setItem('user', JSON.stringify(_safeUserForStorage(response.user)))
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Login failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  const register = async (username: string, email: string, password: string) => {
    loading.value = true
    error.value = null
    try {
      const response = await authAPI.register({
        username,
        email,
        password,
        user_type: 'personal',
        verification_code: '',
      })
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Registration failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  const logout = async () => {
    try {
      await authAPI.logout()
    } catch (err) {
      // logout API failure should not block local cleanup
    } finally {
      user.value = null
      isLoggedIn.value = false
      _restored.value = false  // Reset restoration flag
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }

  const fetchCurrentUser = async () => {
    _ensureRestored()  // Auto-restore before API call
    loading.value = true
    error.value = null
    try {
      const userData = await authAPI.getCurrentUser()
      user.value = userData
      isLoggedIn.value = true
      localStorage.setItem('user', JSON.stringify(_safeUserForStorage(userData)))
    } catch (err) {
      // Clear all auth state on fetch failure (token likely expired/invalid)
      user.value = null
      isLoggedIn.value = false
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      error.value = err instanceof Error ? err.message : 'Failed to fetch user'
    } finally {
      loading.value = false
    }
  }

  const updateProfile = async (profileData: UpdateProfileRequest) => {
    loading.value = true
    error.value = null
    try {
      await authAPI.updateProfile(profileData)
      // Backend returns only {updated:true}; re-fetch to get fresh user data
      const userData = await authAPI.getCurrentUser()
      user.value = userData
      localStorage.setItem('user', JSON.stringify(_safeUserForStorage(userData)))
      return userData
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Update failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  const checkAuth = async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      isLoggedIn.value = false
      return false
    }
    try {
      const isValid = await authAPI.verifyToken()
      if (isValid) {
        await fetchCurrentUser()
        return true
      } else {
        user.value = null
        isLoggedIn.value = false
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        return false
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Token verification failed'
      user.value = null
      isLoggedIn.value = false
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      return false
    }
  }

  const restoreFromStorage = () => {
    const storedUser = localStorage.getItem('user')
    const token = localStorage.getItem('token')
    if (storedUser && token) {
      try {
        user.value = JSON.parse(storedUser)
        isLoggedIn.value = true
      } catch {
        localStorage.removeItem('user')
        localStorage.removeItem('token')
        isLoggedIn.value = false
      }
    }
  }

  return {
    // State
    user,
    isLoggedIn,
    loading,
    error,
    // Computed
    userProfile,
    userId,
    username,
    userRole,
    isAdmin,
    // Actions
    login,
    register,
    logout,
    fetchCurrentUser,
    updateProfile,
    checkAuth,
    restoreFromStorage,
  }
})
