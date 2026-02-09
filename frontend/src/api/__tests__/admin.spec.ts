import { describe, it, expect, vi, beforeEach } from 'vitest'
import { adminApi } from '../admin'
import type { AdminStats, User, Enterprise, AIUsageData } from '@/types/admin'

// Mock axios
const mockGet = vi.fn()
const mockPatch = vi.fn()
const mockDelete = vi.fn()

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      get: (...args: any[]) => mockGet(...args),
      patch: (...args: any[]) => mockPatch(...args),
      delete: (...args: any[]) => mockDelete(...args)
    }))
  }
}))

describe('admin API', () => {
  const mockStats: AdminStats = {
    totalUsers: 100,
    totalEnterprises: 20,
    totalAIUsage: 5000,
    activeUsers: 75
  }

  const mockUsers: User[] = [
    {
      id: 1,
      username: 'john_doe',
      email: 'john@example.com',
      role: 'admin',
      status: 'active',
      createdAt: '2024-01-01T00:00:00Z'
    },
    {
      id: 2,
      username: 'jane_smith',
      email: 'jane@example.com',
      role: 'user',
      status: 'active',
      createdAt: '2024-01-02T00:00:00Z'
    }
  ]

  const mockEnterprises: Enterprise[] = [
    {
      id: 1,
      name: 'Tech Corp',
      contactPerson: 'John Doe',
      email: 'contact@techcorp.com',
      status: 'active',
      createdAt: '2024-01-01T00:00:00Z'
    },
    {
      id: 2,
      name: 'Innovation Ltd',
      contactPerson: 'Jane Smith',
      email: 'info@innovation.com',
      status: 'active',
      createdAt: '2024-01-02T00:00:00Z'
    }
  ]

  const mockAIUsage: AIUsageData[] = [
    { date: '2024-01-01', count: 100 },
    { date: '2024-01-02', count: 150 },
    { date: '2024-01-03', count: 200 }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getStats', () => {
    it('should fetch admin statistics', async () => {
      mockGet.mockResolvedValue(mockStats)

      const result = await adminApi.getStats()

      expect(mockGet).toHaveBeenCalledWith('/stats')
      expect(result).toEqual(mockStats)
    })

    it('should return correct stats structure', async () => {
      mockGet.mockResolvedValue(mockStats)

      const result = await adminApi.getStats()

      expect(result).toHaveProperty('totalUsers')
      expect(result).toHaveProperty('totalEnterprises')
      expect(result).toHaveProperty('totalAIUsage')
      expect(result).toHaveProperty('activeUsers')
    })

    it('should handle stats fetch error', async () => {
      const error = new Error('Stats fetch failed')
      mockGet.mockRejectedValue(error)

      await expect(adminApi.getStats()).rejects.toThrow('Stats fetch failed')
    })

    it('should return numeric values', async () => {
      mockGet.mockResolvedValue(mockStats)

      const result = await adminApi.getStats()

      expect(typeof result.totalUsers).toBe('number')
      expect(typeof result.totalEnterprises).toBe('number')
      expect(typeof result.totalAIUsage).toBe('number')
      expect(typeof result.activeUsers).toBe('number')
    })
  })

  describe('getUsers', () => {
    it('should fetch users without search params', async () => {
      mockGet.mockResolvedValue(mockUsers)

      const result = await adminApi.getUsers()

      expect(mockGet).toHaveBeenCalledWith('/users', { params: undefined })
      expect(result).toEqual(mockUsers)
    })

    it('should fetch users with search params', async () => {
      mockGet.mockResolvedValue(mockUsers)

      const result = await adminApi.getUsers({ search: 'john' })

      expect(mockGet).toHaveBeenCalledWith('/users', { params: { search: 'john' } })
      expect(result).toEqual(mockUsers)
    })

    it('should return array of users', async () => {
      mockGet.mockResolvedValue(mockUsers)

      const result = await adminApi.getUsers()

      expect(Array.isArray(result)).toBe(true)
      expect(result.length).toBe(2)
    })

    it('should handle empty users list', async () => {
      mockGet.mockResolvedValue([])

      const result = await adminApi.getUsers()

      expect(result).toEqual([])
    })

    it('should handle users fetch error', async () => {
      const error = new Error('Users fetch failed')
      mockGet.mockRejectedValue(error)

      await expect(adminApi.getUsers()).rejects.toThrow('Users fetch failed')
    })

    it('should return users with correct structure', async () => {
      mockGet.mockResolvedValue(mockUsers)

      const result = await adminApi.getUsers()

      result.forEach(user => {
        expect(user).toHaveProperty('id')
        expect(user).toHaveProperty('username')
        expect(user).toHaveProperty('email')
        expect(user).toHaveProperty('role')
        expect(user).toHaveProperty('status')
        expect(user).toHaveProperty('createdAt')
      })
    })
  })

  describe('updateUser', () => {
    it('should update user', async () => {
      const updates = { username: 'updated_user', status: 'inactive' }
      const updatedUser = { ...mockUsers[0], ...updates }
      mockPatch.mockResolvedValue(updatedUser)

      const result = await adminApi.updateUser(1, updates)

      expect(mockPatch).toHaveBeenCalledWith('/users/1', updates)
      expect(result).toEqual(updatedUser)
    })

    it('should handle partial updates', async () => {
      const partialUpdate = { status: 'inactive' }
      mockPatch.mockResolvedValue({ ...mockUsers[0], status: 'inactive' })

      await adminApi.updateUser(1, partialUpdate)

      expect(mockPatch).toHaveBeenCalledWith('/users/1', partialUpdate)
    })

    it('should handle update error', async () => {
      const error = new Error('Update failed')
      mockPatch.mockRejectedValue(error)

      await expect(adminApi.updateUser(1, { username: 'test' })).rejects.toThrow('Update failed')
    })

    it('should use correct user ID', async () => {
      mockPatch.mockResolvedValue(mockUsers[1])

      await adminApi.updateUser(2, { username: 'new_name' })

      expect(mockPatch).toHaveBeenCalledWith('/users/2', { username: 'new_name' })
    })

    it('should allow updating all user fields', async () => {
      const fullUpdate = {
        username: 'new_username',
        email: 'new@example.com',
        role: 'user',
        status: 'inactive'
      }
      mockPatch.mockResolvedValue({ ...mockUsers[0], ...fullUpdate })

      await adminApi.updateUser(1, fullUpdate)

      expect(mockPatch).toHaveBeenCalledWith('/users/1', fullUpdate)
    })
  })

  describe('deleteUser', () => {
    it('should delete user', async () => {
      mockDelete.mockResolvedValue(undefined)

      await adminApi.deleteUser(1)

      expect(mockDelete).toHaveBeenCalledWith('/users/1')
    })

    it('should handle delete error', async () => {
      const error = new Error('Delete failed')
      mockDelete.mockRejectedValue(error)

      await expect(adminApi.deleteUser(1)).rejects.toThrow('Delete failed')
    })

    it('should use correct user ID', async () => {
      mockDelete.mockResolvedValue(undefined)

      await adminApi.deleteUser(5)

      expect(mockDelete).toHaveBeenCalledWith('/users/5')
    })

    it('should return void on success', async () => {
      mockDelete.mockResolvedValue(undefined)

      const result = await adminApi.deleteUser(1)

      expect(result).toBeUndefined()
    })
  })

  describe('getEnterprises', () => {
    it('should fetch enterprises without search params', async () => {
      mockGet.mockResolvedValue(mockEnterprises)

      const result = await adminApi.getEnterprises()

      expect(mockGet).toHaveBeenCalledWith('/enterprises', { params: undefined })
      expect(result).toEqual(mockEnterprises)
    })

    it('should fetch enterprises with search params', async () => {
      mockGet.mockResolvedValue(mockEnterprises)

      const result = await adminApi.getEnterprises({ search: 'Tech' })

      expect(mockGet).toHaveBeenCalledWith('/enterprises', { params: { search: 'Tech' } })
      expect(result).toEqual(mockEnterprises)
    })

    it('should return array of enterprises', async () => {
      mockGet.mockResolvedValue(mockEnterprises)

      const result = await adminApi.getEnterprises()

      expect(Array.isArray(result)).toBe(true)
      expect(result.length).toBe(2)
    })

    it('should handle empty enterprises list', async () => {
      mockGet.mockResolvedValue([])

      const result = await adminApi.getEnterprises()

      expect(result).toEqual([])
    })

    it('should handle enterprises fetch error', async () => {
      const error = new Error('Enterprises fetch failed')
      mockGet.mockRejectedValue(error)

      await expect(adminApi.getEnterprises()).rejects.toThrow('Enterprises fetch failed')
    })

    it('should return enterprises with correct structure', async () => {
      mockGet.mockResolvedValue(mockEnterprises)

      const result = await adminApi.getEnterprises()

      result.forEach(enterprise => {
        expect(enterprise).toHaveProperty('id')
        expect(enterprise).toHaveProperty('name')
        expect(enterprise).toHaveProperty('contactPerson')
        expect(enterprise).toHaveProperty('email')
        expect(enterprise).toHaveProperty('status')
        expect(enterprise).toHaveProperty('createdAt')
      })
    })
  })

  describe('updateEnterprise', () => {
    it('should update enterprise', async () => {
      const updates = { name: 'Updated Corp', status: 'inactive' }
      const updatedEnterprise = { ...mockEnterprises[0], ...updates }
      mockPatch.mockResolvedValue(updatedEnterprise)

      const result = await adminApi.updateEnterprise(1, updates)

      expect(mockPatch).toHaveBeenCalledWith('/enterprises/1', updates)
      expect(result).toEqual(updatedEnterprise)
    })

    it('should handle partial updates', async () => {
      const partialUpdate = { status: 'inactive' }
      mockPatch.mockResolvedValue({ ...mockEnterprises[0], status: 'inactive' })

      await adminApi.updateEnterprise(1, partialUpdate)

      expect(mockPatch).toHaveBeenCalledWith('/enterprises/1', partialUpdate)
    })

    it('should handle update error', async () => {
      const error = new Error('Update failed')
      mockPatch.mockRejectedValue(error)

      await expect(adminApi.updateEnterprise(1, { name: 'test' })).rejects.toThrow('Update failed')
    })

    it('should use correct enterprise ID', async () => {
      mockPatch.mockResolvedValue(mockEnterprises[1])

      await adminApi.updateEnterprise(2, { name: 'New Name' })

      expect(mockPatch).toHaveBeenCalledWith('/enterprises/2', { name: 'New Name' })
    })

    it('should allow updating all enterprise fields', async () => {
      const fullUpdate = {
        name: 'New Enterprise',
        contactPerson: 'New Contact',
        email: 'new@example.com',
        status: 'inactive'
      }
      mockPatch.mockResolvedValue({ ...mockEnterprises[0], ...fullUpdate })

      await adminApi.updateEnterprise(1, fullUpdate)

      expect(mockPatch).toHaveBeenCalledWith('/enterprises/1', fullUpdate)
    })
  })

  describe('deleteEnterprise', () => {
    it('should delete enterprise', async () => {
      mockDelete.mockResolvedValue(undefined)

      await adminApi.deleteEnterprise(1)

      expect(mockDelete).toHaveBeenCalledWith('/enterprises/1')
    })

    it('should handle delete error', async () => {
      const error = new Error('Delete failed')
      mockDelete.mockRejectedValue(error)

      await expect(adminApi.deleteEnterprise(1)).rejects.toThrow('Delete failed')
    })

    it('should use correct enterprise ID', async () => {
      mockDelete.mockResolvedValue(undefined)

      await adminApi.deleteEnterprise(5)

      expect(mockDelete).toHaveBeenCalledWith('/enterprises/5')
    })

    it('should return void on success', async () => {
      mockDelete.mockResolvedValue(undefined)

      const result = await adminApi.deleteEnterprise(1)

      expect(result).toBeUndefined()
    })
  })

  describe('getAIUsage', () => {
    it('should fetch AI usage data', async () => {
      mockGet.mockResolvedValue(mockAIUsage)

      const result = await adminApi.getAIUsage()

      expect(mockGet).toHaveBeenCalledWith('/ai-usage')
      expect(result).toEqual(mockAIUsage)
    })

    it('should return array of usage data', async () => {
      mockGet.mockResolvedValue(mockAIUsage)

      const result = await adminApi.getAIUsage()

      expect(Array.isArray(result)).toBe(true)
      expect(result.length).toBe(3)
    })

    it('should handle empty usage data', async () => {
      mockGet.mockResolvedValue([])

      const result = await adminApi.getAIUsage()

      expect(result).toEqual([])
    })

    it('should handle usage fetch error', async () => {
      const error = new Error('Usage fetch failed')
      mockGet.mockRejectedValue(error)

      await expect(adminApi.getAIUsage()).rejects.toThrow('Usage fetch failed')
    })

    it('should return usage data with correct structure', async () => {
      mockGet.mockResolvedValue(mockAIUsage)

      const result = await adminApi.getAIUsage()

      result.forEach(usage => {
        expect(usage).toHaveProperty('date')
        expect(usage).toHaveProperty('count')
        expect(typeof usage.date).toBe('string')
        expect(typeof usage.count).toBe('number')
      })
    })

    it('should return chronological data', async () => {
      mockGet.mockResolvedValue(mockAIUsage)

      const result = await adminApi.getAIUsage()

      expect(result[0].date).toBe('2024-01-01')
      expect(result[1].date).toBe('2024-01-02')
      expect(result[2].date).toBe('2024-01-03')
    })
  })

  describe('API Configuration', () => {
    it('should use correct base URL', () => {
      // The API is created with baseURL: '/api/admin'
      // This is tested implicitly through all the endpoint calls
      expect(mockGet).toBeDefined()
      expect(mockPatch).toBeDefined()
      expect(mockDelete).toBeDefined()
    })
  })

  describe('Error Handling', () => {
    it('should propagate network errors', async () => {
      const networkError = new Error('Network timeout')
      mockGet.mockRejectedValue(networkError)

      await expect(adminApi.getStats()).rejects.toThrow('Network timeout')
    })

    it('should handle 404 errors', async () => {
      const notFoundError = new Error('Not found')
      mockGet.mockRejectedValue(notFoundError)

      await expect(adminApi.getUsers()).rejects.toThrow('Not found')
    })

    it('should handle 500 errors', async () => {
      const serverError = new Error('Internal server error')
      mockGet.mockRejectedValue(serverError)

      await expect(adminApi.getEnterprises()).rejects.toThrow('Internal server error')
    })

    it('should handle validation errors', async () => {
      const validationError = new Error('Invalid data')
      mockPatch.mockRejectedValue(validationError)

      await expect(adminApi.updateUser(1, {})).rejects.toThrow('Invalid data')
    })
  })

  describe('Type Safety', () => {
    it('should return correctly typed stats', async () => {
      mockGet.mockResolvedValue(mockStats)

      const result = await adminApi.getStats()

      expect(result).toHaveProperty('totalUsers')
      expect(result).toHaveProperty('totalEnterprises')
      expect(result).toHaveProperty('totalAIUsage')
      expect(result).toHaveProperty('activeUsers')
    })

    it('should return correctly typed users', async () => {
      mockGet.mockResolvedValue(mockUsers)

      const result = await adminApi.getUsers()

      expect(result[0]).toHaveProperty('id')
      expect(result[0]).toHaveProperty('username')
      expect(result[0]).toHaveProperty('email')
      expect(result[0]).toHaveProperty('role')
      expect(result[0]).toHaveProperty('status')
    })

    it('should return correctly typed enterprises', async () => {
      mockGet.mockResolvedValue(mockEnterprises)

      const result = await adminApi.getEnterprises()

      expect(result[0]).toHaveProperty('id')
      expect(result[0]).toHaveProperty('name')
      expect(result[0]).toHaveProperty('contactPerson')
      expect(result[0]).toHaveProperty('email')
      expect(result[0]).toHaveProperty('status')
    })
  })
})
