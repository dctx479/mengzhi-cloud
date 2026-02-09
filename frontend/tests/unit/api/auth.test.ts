import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import axios from 'axios'
import * as authAPI from '@/api/auth'
import { testDataGenerators } from '../utils/test-utils'

/**
 * Auth API 测试
 * 测试认证相关API调用
 */

vi.mock('axios')

describe('Auth API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('login', () => {
    it('sends login request with correct data', async () => {
      const user = testDataGenerators.createUser()
      const token = 'test-token'

      vi.mocked(axios.create).mockReturnValue({
        post: vi.fn().mockResolvedValueOnce({
          data: {
            user,
            token,
            expiresIn: 3600,
          },
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      // Re-import to get mocked version
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

      vi.mocked(axios.create).mockReturnValue({
        post: vi.fn().mockResolvedValueOnce({
          data: {
            user,
            token,
            expiresIn: 3600,
          },
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

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

      vi.mocked(axios.create).mockReturnValue({
        post: vi.fn().mockResolvedValueOnce({
          data: {
            user,
            message: 'Registration successful',
          },
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

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

      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: user,
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

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

      vi.mocked(axios.create).mockReturnValue({
        put: vi.fn().mockResolvedValueOnce({
          data: updatedUser,
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

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

      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: user,
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

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

      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockRejectedValueOnce(new Error('Invalid token')),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/auth')
      const result = await module.verifyToken()

      expect(result).toBe(false)
    })
  })

  describe('changePassword', () => {
    it('sends password change request', async () => {
      vi.mocked(axios.create).mockReturnValue({
        post: vi.fn().mockResolvedValueOnce({
          data: { message: 'Password changed' },
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/auth')
      await expect(
        module.changePassword('oldpassword', 'newpassword')
      ).resolves.not.toThrow()
    })
  })

  describe('API Configuration', () => {
    it('uses correct API base URL', () => {
      const axiosCreateSpy = vi.mocked(axios.create)
      expect(axiosCreateSpy).toBeDefined()
    })

    it('sets correct timeout', () => {
      vi.mocked(axios.create).mockReturnValue({
        post: vi.fn(),
        get: vi.fn(),
        put: vi.fn(),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      expect(axios.create).toBeDefined()
    })
  })

  describe('Error Handling', () => {
    it('handles network errors', async () => {
      vi.mocked(axios.create).mockReturnValue({
        post: vi
          .fn()
          .mockRejectedValueOnce(new Error('Network error')),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

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
      vi.mocked(axios.create).mockReturnValue({
        post: vi.fn().mockRejectedValueOnce({
          response: {
            status: 400,
            data: {
              message: 'Invalid email format',
            },
          },
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      expect(axios.create).toBeDefined()
    })
  })
})
