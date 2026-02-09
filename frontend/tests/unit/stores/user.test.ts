import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '@/stores/user'
import * as authAPI from '@/api/auth'
import { testDataGenerators } from '../utils/test-utils'

/**
 * User Store 测试
 * 测试用户认证、状态管理和localStorage持久化
 */

vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  getCurrentUser: vi.fn(),
  updateProfile: vi.fn(),
  verifyToken: vi.fn(),
  changePassword: vi.fn(),
}))

describe('User Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('login', () => {
    it('sets user and token on successful login', async () => {
      const store = useUserStore()
      const user = testDataGenerators.createUser()
      const token = 'test-token-123'

      vi.mocked(authAPI.login).mockResolvedValueOnce({
        user,
        token,
        expiresIn: 3600,
      })

      await store.login('test@example.com', 'password')

      expect(store.user).toEqual(user)
      expect(store.isLoggedIn).toBe(true)
      expect(localStorage.getItem('token')).toBe(token)
      expect(localStorage.getItem('user')).toBe(JSON.stringify(user))
    })

    it('sets loading state during login', async () => {
      const store = useUserStore()
      const user = testDataGenerators.createUser()

      vi.mocked(authAPI.login).mockImplementation(
        () =>
          new Promise(resolve => {
            setTimeout(() => {
              resolve({
                user,
                token: 'token',
                expiresIn: 3600,
              })
            }, 100)
          })
      )

      expect(store.loading).toBe(false)
      const promise = store.login('test@example.com', 'password')
      expect(store.loading).toBe(true)
      await promise
      expect(store.loading).toBe(false)
    })

    it('handles login error', async () => {
      const store = useUserStore()
      const errorMessage = 'Invalid credentials'

      vi.mocked(authAPI.login).mockRejectedValueOnce(new Error(errorMessage))

      try {
        await store.login('test@example.com', 'wrongpassword')
      } catch (err) {
        // Expected error
      }

      expect(store.error).toBe(errorMessage)
      expect(store.isLoggedIn).toBe(false)
    })

    it('clears previous error on new login attempt', async () => {
      const store = useUserStore()
      store.error = 'Previous error'
      const user = testDataGenerators.createUser()

      vi.mocked(authAPI.login).mockResolvedValueOnce({
        user,
        token: 'token',
        expiresIn: 3600,
      })

      await store.login('test@example.com', 'password')

      expect(store.error).toBe(null)
    })
  })

  describe('register', () => {
    it('calls register API with correct data', async () => {
      const store = useUserStore()
      const user = testDataGenerators.createUser()

      vi.mocked(authAPI.register).mockResolvedValueOnce({
        user,
        message: 'Registration successful',
      })

      const result = await store.register('testuser', 'test@example.com', 'password')

      expect(authAPI.register).toHaveBeenCalledWith({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password',
        confirmPassword: 'password',
      })
      expect(result.user).toEqual(user)
    })

    it('handles registration error', async () => {
      const store = useUserStore()
      const errorMessage = 'Email already exists'

      vi.mocked(authAPI.register).mockRejectedValueOnce(new Error(errorMessage))

      try {
        await store.register('testuser', 'existing@example.com', 'password')
      } catch (err) {
        // Expected error
      }

      expect(store.error).toBe(errorMessage)
    })
  })

  describe('logout', () => {
    it('clears user data and localStorage on logout', async () => {
      const store = useUserStore()
      const user = testDataGenerators.createUser()

      // Set initial state
      store.user = user
      store.isLoggedIn = true
      localStorage.setItem('token', 'test-token')
      localStorage.setItem('user', JSON.stringify(user))

      await store.logout()

      expect(store.user).toBe(null)
      expect(store.isLoggedIn).toBe(false)
      expect(localStorage.getItem('token')).toBe(null)
      expect(localStorage.getItem('user')).toBe(null)
    })

    it('calls logout API', async () => {
      const store = useUserStore()

      await store.logout()

      expect(authAPI.logout).toHaveBeenCalled()
    })
  })

  describe('fetchCurrentUser', () => {
    it('fetches and stores current user', async () => {
      const store = useUserStore()
      const user = testDataGenerators.createUser()

      vi.mocked(authAPI.getCurrentUser).mockResolvedValueOnce(user)

      await store.fetchCurrentUser()

      expect(store.user).toEqual(user)
      expect(store.isLoggedIn).toBe(true)
      expect(localStorage.getItem('user')).toBe(JSON.stringify(user))
    })

    it('handles fetch user error', async () => {
      const store = useUserStore()

      vi.mocked(authAPI.getCurrentUser).mockRejectedValueOnce(
        new Error('No token found')
      )

      await store.fetchCurrentUser()

      expect(store.isLoggedIn).toBe(false)
      expect(localStorage.getItem('token')).toBe(null)
    })
  })

  describe('updateProfile', () => {
    it('updates user profile', async () => {
      const store = useUserStore()
      const updatedUser = testDataGenerators.createUser({
        username: 'newusername',
      })

      vi.mocked(authAPI.updateProfile).mockResolvedValueOnce(updatedUser)

      const result = await store.updateProfile({ username: 'newusername' })

      expect(store.user).toEqual(updatedUser)
      expect(result).toEqual(updatedUser)
      expect(localStorage.getItem('user')).toBe(JSON.stringify(updatedUser))
    })

    it('handles profile update error', async () => {
      const store = useUserStore()

      vi.mocked(authAPI.updateProfile).mockRejectedValueOnce(
        new Error('Update failed')
      )

      try {
        await store.updateProfile({ username: 'newusername' })
      } catch (err) {
        // Expected error
      }

      expect(store.error).toBe('Update failed')
    })
  })

  describe('checkAuth', () => {
    it('returns false when no token', async () => {
      const store = useUserStore()
      localStorage.clear()

      const result = await store.checkAuth()

      expect(result).toBe(false)
      expect(store.isLoggedIn).toBe(false)
    })

    it('verifies token and fetches user', async () => {
      const store = useUserStore()
      const user = testDataGenerators.createUser()

      localStorage.setItem('token', 'valid-token')
      vi.mocked(authAPI.verifyToken).mockResolvedValueOnce(true)
      vi.mocked(authAPI.getCurrentUser).mockResolvedValueOnce(user)

      const result = await store.checkAuth()

      expect(result).toBe(true)
      expect(store.isLoggedIn).toBe(true)
      expect(store.user).toEqual(user)
    })

    it('returns false for invalid token', async () => {
      const store = useUserStore()

      localStorage.setItem('token', 'invalid-token')
      vi.mocked(authAPI.verifyToken).mockResolvedValueOnce(false)

      const result = await store.checkAuth()

      expect(result).toBe(false)
      expect(store.isLoggedIn).toBe(false)
    })
  })

  describe('restoreFromStorage', () => {
    it('restores user from localStorage', () => {
      const store = useUserStore()
      const user = testDataGenerators.createUser()

      localStorage.setItem('user', JSON.stringify(user))
      localStorage.setItem('token', 'test-token')

      store.restoreFromStorage()

      expect(store.user).toEqual(user)
      expect(store.isLoggedIn).toBe(true)
    })

    it('does nothing when localStorage is empty', () => {
      const store = useUserStore()

      store.restoreFromStorage()

      expect(store.user).toBe(null)
      expect(store.isLoggedIn).toBe(false)
    })

    it('clears invalid stored data', () => {
      const store = useUserStore()

      localStorage.setItem('user', 'invalid-json')
      localStorage.setItem('token', 'test-token')

      store.restoreFromStorage()

      expect(store.user).toBe(null)
      expect(localStorage.getItem('user')).toBe(null)
      expect(localStorage.getItem('token')).toBe(null)
    })
  })

  describe('Computed Properties', () => {
    it('userId computed returns user id', () => {
      const store = useUserStore()
      const user = testDataGenerators.createUser({ id: 'user-123' })

      store.user = user

      expect(store.userId).toBe('user-123')
    })

    it('username computed returns username', () => {
      const store = useUserStore()
      const user = testDataGenerators.createUser({ username: 'testuser' })

      store.user = user

      expect(store.username).toBe('testuser')
    })

    it('userRole computed returns user role', () => {
      const store = useUserStore()
      const user = testDataGenerators.createUser({ role: 'admin' })

      store.user = user

      expect(store.userRole).toBe('admin')
    })

    it('isAdmin computed returns true for admin role', () => {
      const store = useUserStore()
      const user = testDataGenerators.createUser({ role: 'admin' })

      store.user = user

      expect(store.isAdmin).toBe(true)
    })

    it('isAdmin computed returns false for non-admin role', () => {
      const store = useUserStore()
      const user = testDataGenerators.createUser({ role: 'user' })

      store.user = user

      expect(store.isAdmin).toBe(false)
    })

    it('userProfile computed returns user as UserProfile', () => {
      const store = useUserStore()
      const user = testDataGenerators.createUser()

      store.user = user

      expect(store.userProfile).toEqual(user)
    })
  })

  describe('State Management', () => {
    it('initializes with correct default state', () => {
      const store = useUserStore()

      expect(store.user).toBe(null)
      expect(store.isLoggedIn).toBe(false)
      expect(store.loading).toBe(false)
      expect(store.error).toBe(null)
    })

    it('maintains state across actions', async () => {
      const store = useUserStore()
      const user = testDataGenerators.createUser()

      vi.mocked(authAPI.login).mockResolvedValueOnce({
        user,
        token: 'token',
        expiresIn: 3600,
      })

      await store.login('test@example.com', 'password')

      expect(store.isLoggedIn).toBe(true)

      await store.logout()

      expect(store.isLoggedIn).toBe(false)
    })
  })
})
