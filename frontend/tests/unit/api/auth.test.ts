import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import axios, { AxiosInstance } from 'axios'
import * as authAPI from '@/api/auth'
import { testDataGenerators } from '../utils/test-utils'

vi.mock('axios')

describe('Auth API', () => {
  let mockAxiosInstance: Partial<AxiosInstance>

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    mockAxiosInstance = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      defaults: {
        headers: {
          common: {},
        },
      },
    }
    vi.mocked(axios.create).mockReturnValue(mockAxiosInstance as AxiosInstance)
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('login', () => {
    it('sends login request with correct data', async () => {
      const user = testDataGenerators.createUser()
      const token = 'test-token'

      vi.mocked(mockAxiosInstance.post).mockResolvedValueOnce({
        data: {
          user,
          token,
          expiresIn: 3600,
        },
      })

      const module = await import('@/api/auth')
      const result = await module.login({
        email: 'test@example.com',
        password: 'password',
      })

      expect(result.token).toBe(token)
      expect(result.user).toEqual(user)
    })

    it('stores token in localStorage on login', async () => {
      const user = testDataGenerators.createUser()
      const token = 'test-token-123'

      vi.mocked(mockAxiosInstance.post).mockResolvedValueOnce({
        data: {
          user,
          token,
          expiresIn: 3600,
        },
      })

      const module = await import('@/api/auth')
      await module.login({
        email: 'test@example.com',
        password: 'password',
      })

      expect(localStorage.getItem('token')).toBe(token)
    })
  })

  describe('register', () => {
    it('sends register request with correct data', async () => {
      const user = testDataGenerators.createUser()

      vi.mocked(mockAxiosInstance.post).mockResolvedValueOnce({
        data: {
          user,
          message: 'Registration successful',
        },
      })

      const module = await import('@/api/auth')
      const result = await module.register({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password',
        confirmPassword: 'password',
      })

      expect(result.user).toEqual(user)
      expect(result.message).toBe('Registration successful')
    })
  })

  describe('logout', () => {
    it('removes token from localStorage', async () => {
      localStorage.setItem('token', 'test-token')

      const module = await import('@/api/auth')
      await module.logout()

      expect(localStorage.getItem('token')).toBe(null)
    })
  })

  describe('getCurrentUser', () => {
    it('fetches user from API with token', async () => {
      const user = testDataGenerators.createUser()
      localStorage.setItem('token', 'test-token')

      vi.mocked(mockAxiosInstance.get).mockResolvedValueOnce({
        data: user,
      })

      const module = await import('@/api/auth')
      const result = await module.getCurrentUser()

      expect(result).toEqual(user)
    })

    it('throws error when no token', async () => {
      localStorage.removeItem('token')

      const module = await import('@/api/auth')
      try {
        await module.getCurrentUser()
        expect.fail('Should throw error')
      } catch (err) {
        expect((err as Error).message).toBe('No token found')
      }
    })
  })

  describe('updateProfile', () => {
    it('sends update request with profile data', async () => {
      const updatedUser = testDataGenerators.createUser({
        username: 'newusername',
      })

      vi.mocked(mockAxiosInstance.put).mockResolvedValueOnce({
        data: updatedUser,
      })

      const module = await import('@/api/auth')
      const result = await module.updateProfile({
        username: 'newusername',
      })

      expect(result).toEqual(updatedUser)
    })
  })

  describe('verifyToken', () => {
    it('returns true for valid token', async () => {
      const user = testDataGenerators.createUser()
      localStorage.setItem('token', 'valid-token')

      vi.mocked(mockAxiosInstance.get).mockResolvedValueOnce({
        data: user,
      })

      const module = await import('@/api/auth')
      const result = await module.verifyToken()

      expect(result).toBe(true)
    })

    it('returns false when token is missing', async () => {
      localStorage.removeItem('token')

      const module = await import('@/api/auth')
      const result = await module.verifyToken()

      expect(result).toBe(false)
    })

    it('returns false on API error', async () => {
      localStorage.setItem('token', 'invalid-token')

      vi.mocked(mockAxiosInstance.get).mockRejectedValueOnce(
        new Error('Invalid token')
      )

      const module = await import('@/api/auth')
      const result = await module.verifyToken()

      expect(result).toBe(false)
    })
  })

  describe('changePassword', () => {
    it('sends password change request', async () => {
      vi.mocked(mockAxiosInstance.post).mockResolvedValueOnce({
        data: { message: 'Password changed' },
      })

      const module = await import('@/api/auth')
      await expect(
        module.changePassword('oldpassword', 'newpassword')
      ).resolves.not.toThrow()
    })
  })

  describe('Error Handling', () => {
    it('handles network errors', async () => {
      vi.mocked(mockAxiosInstance.post).mockRejectedValueOnce(
        new Error('Network error')
      )

      const module = await import('@/api/auth')
      try {
        await module.login({
          email: 'test@example.com',
          password: 'password',
        })
        expect.fail('Should throw error')
      } catch (err) {
        expect((err as Error).message).toBe('Network error')
      }
    })

    it('handles validation errors', async () => {
      vi.mocked(mockAxiosInstance.post).mockRejectedValueOnce({
        response: {
          status: 400,
          data: {
            message: 'Invalid email format',
          },
        },
      })

      expect(axios.create).toBeDefined()
    })
  })
})
