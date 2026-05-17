import { describe, it, expect, vi, beforeEach } from 'vitest'
import { getAIConfigs, createAIConfig, updateAIConfig, deleteAIConfig, testAIConfig } from '../aiConfig'
import type { AIConfig, AIConfigForm } from '@/types/aiConfig'

// Mock the request module
const mockGet = vi.fn()
const mockPost = vi.fn()
const mockPatch = vi.fn()
const mockDelete = vi.fn()

vi.mock('@/utils/request', () => ({
  default: {
    get: (...args: any[]) => mockGet(...args),
    post: (...args: any[]) => mockPost(...args),
    patch: (...args: any[]) => mockPatch(...args),
    delete: (...args: any[]) => mockDelete(...args)
  }
}))

describe('aiConfig API', () => {
  const enterpriseId = 'test-enterprise-id'

  const mockConfig: AIConfig = {
    id: '1',
    name: 'Test Config',
    provider: 'openai',
    apiKey: 'sk-test-key',
    model: 'gpt-4',
    isActive: true,
    createdAt: '2024-01-01T00:00:00Z'
  }

  const mockConfigForm: AIConfigForm = {
    name: 'New Config',
    provider: 'anthropic',
    apiKey: 'sk-new-key',
    model: 'claude-3-opus',
    isActive: true
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getAIConfigs', () => {
    it('should fetch AI configs for an enterprise', async () => {
      const mockConfigs = [mockConfig]
      mockGet.mockResolvedValue(mockConfigs)

      const result = await getAIConfigs(enterpriseId)

      expect(mockGet).toHaveBeenCalledWith(`/v1/enterprises/${enterpriseId}/ai-configs`)
      expect(result).toEqual(mockConfigs)
    })

    it('should handle empty configs list', async () => {
      mockGet.mockResolvedValue([])

      const result = await getAIConfigs(enterpriseId)

      expect(result).toEqual([])
    })

    it('should handle API errors', async () => {
      const error = new Error('Network error')
      mockGet.mockRejectedValue(error)

      await expect(getAIConfigs(enterpriseId)).rejects.toThrow('Network error')
    })

    it('should use correct URL format', async () => {
      mockGet.mockResolvedValue([])

      await getAIConfigs('enterprise-123')

      expect(mockGet).toHaveBeenCalledWith('/v1/enterprises/enterprise-123/ai-configs')
    })
  })

  describe('createAIConfig', () => {
    it('should create a new AI config', async () => {
      mockPost.mockResolvedValue(mockConfig)

      const result = await createAIConfig(enterpriseId, mockConfigForm)

      expect(mockPost).toHaveBeenCalledWith(
        `/v1/enterprises/${enterpriseId}/ai-configs`,
        mockConfigForm
      )
      expect(result).toEqual(mockConfig)
    })

    it('should send all form fields', async () => {
      mockPost.mockResolvedValue(mockConfig)

      await createAIConfig(enterpriseId, mockConfigForm)

      const callArgs = mockPost.mock.calls[0]
      expect(callArgs[1]).toHaveProperty('name')
      expect(callArgs[1]).toHaveProperty('provider')
      expect(callArgs[1]).toHaveProperty('apiKey')
      expect(callArgs[1]).toHaveProperty('model')
      expect(callArgs[1]).toHaveProperty('isActive')
    })

    it('should handle creation errors', async () => {
      const error = new Error('Creation failed')
      mockPost.mockRejectedValue(error)

      await expect(createAIConfig(enterpriseId, mockConfigForm)).rejects.toThrow('Creation failed')
    })

    it('should handle config with endpoint', async () => {
      const configWithEndpoint: AIConfigForm = {
        ...mockConfigForm,
        provider: 'azure',
        endpoint: 'https://azure.openai.com'
      }
      mockPost.mockResolvedValue({ ...mockConfig, ...configWithEndpoint })

      await createAIConfig(enterpriseId, configWithEndpoint)

      expect(mockPost.mock.calls[0][1]).toHaveProperty('endpoint')
      expect(mockPost.mock.calls[0][1].endpoint).toBe('https://azure.openai.com')
    })
  })

  describe('updateAIConfig', () => {
    const configId = 'config-123'

    it('should update an existing AI config', async () => {
      const updates: Partial<AIConfigForm> = {
        name: 'Updated Config',
        isActive: false
      }
      mockPatch.mockResolvedValue({ ...mockConfig, ...updates })

      const result = await updateAIConfig(enterpriseId, configId, updates)

      expect(mockPatch).toHaveBeenCalledWith(
        `/v1/enterprises/${enterpriseId}/ai-configs/${configId}`,
        updates
      )
      expect(result.name).toBe('Updated Config')
    })

    it('should handle partial updates', async () => {
      const partialUpdate = { isActive: false }
      mockPatch.mockResolvedValue({ ...mockConfig, isActive: false })

      await updateAIConfig(enterpriseId, configId, partialUpdate)

      expect(mockPatch.mock.calls[0][1]).toEqual(partialUpdate)
    })

    it('should handle update errors', async () => {
      const error = new Error('Update failed')
      mockPatch.mockRejectedValue(error)

      await expect(
        updateAIConfig(enterpriseId, configId, { name: 'New Name' })
      ).rejects.toThrow('Update failed')
    })

    it('should use correct URL with both IDs', async () => {
      mockPatch.mockResolvedValue(mockConfig)

      await updateAIConfig('ent-456', 'cfg-789', { name: 'Test' })

      expect(mockPatch).toHaveBeenCalledWith(
        '/v1/enterprises/ent-456/ai-configs/cfg-789',
        { name: 'Test' }
      )
    })

    it('should allow updating all fields', async () => {
      const fullUpdate: Partial<AIConfigForm> = {
        name: 'Full Update',
        provider: 'azure',
        apiKey: 'new-key',
        endpoint: 'https://new-endpoint.com',
        model: 'gpt-4-turbo',
        isActive: false
      }
      mockPatch.mockResolvedValue({ ...mockConfig, ...fullUpdate })

      await updateAIConfig(enterpriseId, configId, fullUpdate)

      expect(mockPatch.mock.calls[0][1]).toEqual(fullUpdate)
    })
  })

  describe('deleteAIConfig', () => {
    const configId = 'config-123'

    it('should delete an AI config', async () => {
      mockDelete.mockResolvedValue(undefined)

      await deleteAIConfig(enterpriseId, configId)

      expect(mockDelete).toHaveBeenCalledWith(
        `/v1/enterprises/${enterpriseId}/ai-configs/${configId}`
      )
    })

    it('should handle deletion errors', async () => {
      const error = new Error('Deletion failed')
      mockDelete.mockRejectedValue(error)

      await expect(deleteAIConfig(enterpriseId, configId)).rejects.toThrow('Deletion failed')
    })

    it('should use correct URL format', async () => {
      mockDelete.mockResolvedValue(undefined)

      await deleteAIConfig('ent-999', 'cfg-888')

      expect(mockDelete).toHaveBeenCalledWith('/v1/enterprises/ent-999/ai-configs/cfg-888')
    })

    it('should return void on successful deletion', async () => {
      mockDelete.mockResolvedValue(undefined)

      const result = await deleteAIConfig(enterpriseId, configId)

      expect(result).toBeUndefined()
    })
  })

  describe('testAIConfig', () => {
    const configId = 'config-123'

    it('should test AI config connection', async () => {
      const mockResponse = { success: true, message: '连接成功' }
      mockPost.mockResolvedValue(mockResponse)

      const result = await testAIConfig(enterpriseId, configId)

      expect(mockPost).toHaveBeenCalledWith(
        `/v1/enterprises/${enterpriseId}/ai-configs/${configId}/test`
      )
      expect(result).toEqual(mockResponse)
    })

    it('should return success status', async () => {
      mockPost.mockResolvedValue({ success: true, message: 'Connection successful' })

      const result = await testAIConfig(enterpriseId, configId)

      expect(result.success).toBe(true)
      expect(result.message).toBeTruthy()
    })

    it('should handle test failures', async () => {
      const error = new Error('Connection failed')
      mockPost.mockRejectedValue(error)

      await expect(testAIConfig(enterpriseId, configId)).rejects.toThrow('Connection failed')
    })

    it('should return failure status on API error', async () => {
      mockPost.mockResolvedValue({ success: false, message: 'Invalid API key' })

      const result = await testAIConfig(enterpriseId, configId)

      expect(result.success).toBe(false)
      expect(result.message).toBe('Invalid API key')
    })

    it('should use correct test endpoint', async () => {
      mockPost.mockResolvedValue({ success: true, message: 'OK' })

      await testAIConfig('ent-111', 'cfg-222')

      expect(mockPost).toHaveBeenCalledWith('/v1/enterprises/ent-111/ai-configs/cfg-222/test')
    })
  })

  describe('Error Handling', () => {
    it('should propagate network errors', async () => {
      const networkError = new Error('Network timeout')
      mockGet.mockRejectedValue(networkError)

      await expect(getAIConfigs(enterpriseId)).rejects.toThrow('Network timeout')
    })

    it('should handle 404 errors', async () => {
      const notFoundError = new Error('Not found')
      mockGet.mockRejectedValue(notFoundError)

      await expect(getAIConfigs('non-existent')).rejects.toThrow('Not found')
    })

    it('should handle 500 errors', async () => {
      const serverError = new Error('Internal server error')
      mockPost.mockRejectedValue(serverError)

      await expect(createAIConfig(enterpriseId, mockConfigForm)).rejects.toThrow(
        'Internal server error'
      )
    })

    it('should handle validation errors', async () => {
      const validationError = new Error('Invalid data')
      mockPost.mockRejectedValue(validationError)

      await expect(createAIConfig(enterpriseId, mockConfigForm)).rejects.toThrow('Invalid data')
    })
  })

  describe('Type Safety', () => {
    it('should return correctly typed config', async () => {
      mockGet.mockResolvedValue([mockConfig])

      const result = await getAIConfigs(enterpriseId)

      expect(result[0]).toHaveProperty('id')
      expect(result[0]).toHaveProperty('name')
      expect(result[0]).toHaveProperty('provider')
      expect(result[0]).toHaveProperty('apiKey')
      expect(result[0]).toHaveProperty('model')
      expect(result[0]).toHaveProperty('isActive')
      expect(result[0]).toHaveProperty('createdAt')
    })

    it('should accept valid provider types', async () => {
      mockPost.mockResolvedValue(mockConfig)

      const providers: Array<'openai' | 'azure' | 'anthropic' | 'custom'> = [
        'openai',
        'azure',
        'anthropic',
        'custom'
      ]

      for (const provider of providers) {
        await createAIConfig(enterpriseId, { ...mockConfigForm, provider })
        expect(mockPost).toHaveBeenCalled()
      }
    })
  })
})
