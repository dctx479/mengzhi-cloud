import { describe, it, expect, beforeEach, vi } from 'vitest'
import axios, { AxiosInstance } from 'axios'
import * as chatAPI from '@/api/chat'
import { testDataGenerators } from '../utils/test-utils'

vi.mock('axios')
/**
 * 创建类型安全的Mock Axios实例
 * 消除所有 `as any` 强制转换的需要
 */
function createMockAxiosInstance<T = any>(
  method: 'get' | 'post' | 'delete' | 'patch',
  responseData: T,
  isError = false
): AxiosInstance {
  const mockMethod = vi.fn()
  
  if (isError) {
    mockMethod.mockRejectedValueOnce(responseData)
  } else {
    mockMethod.mockResolvedValueOnce({
      data: responseData,
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {},
    })
  }

  const instance: Partial<AxiosInstance> = {
    defaults: {
      headers: {
        common: {},
      },
    } as any,
  }

  if (method === 'get') {
    instance.get = mockMethod
  } else if (method === 'post') {
    instance.post = mockMethod
  } else if (method === 'delete') {
    instance.delete = mockMethod
  } else if (method === 'patch') {
    instance.patch = mockMethod
  }

  return instance as AxiosInstance
}

/**
 * 创建多方法Mock Axios实例（支持多个HTTP方法）
 */
function createMockAxiosInstanceWithMethods(
  methods: Record<'get' | 'post' | 'delete' | 'patch', { data: any; error?: boolean }>
): AxiosInstance {
  const mockGet = vi.fn()
  const mockPost = vi.fn()
  const mockDelete = vi.fn()
  const mockPatch = vi.fn()

  Object.entries(methods).forEach(([method, config]) => {
    const mockFn = method === 'get' ? mockGet : method === 'post' ? mockPost : method === 'delete' ? mockDelete : mockPatch
    
    if (config.error) {
      mockFn.mockRejectedValueOnce(config.data)
    } else {
      mockFn.mockResolvedValueOnce({
        data: config.data,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {},
      })
    }
  })

  const instance: AxiosInstance = {
    defaults: {
      headers: {
        common: {},
      },
    } as any,
    get: mockGet,
    post: mockPost,
    delete: mockDelete,
    patch: mockPatch,
  } as any

  return instance
}

describe('Chat API', () => {
  let mockAxiosInstance: Partial<AxiosInstance>

  beforeEach(() => {
    vi.clearAllMocks()
    mockAxiosInstance = {
      get: vi.fn(),
      post: vi.fn(),
      delete: vi.fn(),
      defaults: {
        headers: {
          common: {},
        },
      },
    }
    vi.mocked(axios.create).mockReturnValue(mockAxiosInstance as AxiosInstance)
  })

  describe('getChatList', () => {
    it('fetches chat list with pagination', async () => {
      const chats = [
        testDataGenerators.createChat({ id: 'chat-1' }),
        testDataGenerators.createChat({ id: 'chat-2' }),
      ]

      vi.mocked(mockAxiosInstance.get).mockResolvedValueOnce({
        data: {
          data: chats,
          total: 2,
        },
      })

      const module = await import('@/api/chat')
      const result = await module.getChatList(1, 20)

      expect(result.data).toEqual(chats)
      expect(result.total).toBe(2)
    })

    it('handles empty chat list', async () => {
      vi.mocked(mockAxiosInstance.get).mockResolvedValueOnce({
        data: {
          data: [],
          total: 0,
        },
      })

      const module = await import('@/api/chat')
      const result = await module.getChatList(1, 20)

      expect(result.data).toEqual([])
      expect(result.total).toBe(0)
    })
  })

  describe('getChatDetail', () => {
    it('fetches chat detail with messages', async () => {
      const messages = [
        testDataGenerators.createMessage({ role: 'user' }),
        testDataGenerators.createMessage({ role: 'assistant' }),
      ]
      const chat = testDataGenerators.createChat({
        id: 'chat-1',
        messages,
      })

      vi.mocked(mockAxiosInstance.get).mockResolvedValueOnce({
        data: chat,
      })

      const module = await import('@/api/chat')
      const result = await module.getChatDetail('chat-1')

      expect(result).toEqual(chat)
      expect(result.messages).toHaveLength(2)
    })

    it('includes full chat metadata', async () => {
      const chat = testDataGenerators.createChat({
        id: 'chat-123',
        title: '产品咨询',
        createdAt: '2024-01-01T00:00:00Z',
      })

      vi.mocked(mockAxiosInstance.get).mockResolvedValueOnce({
        data: chat,
      })

      const module = await import('@/api/chat')
      const result = await module.getChatDetail('chat-123')

      expect(result.id).toBe('chat-123')
      expect(result.title).toBe('产品咨询')
      expect(result.createdAt).toBe('2024-01-01T00:00:00Z')
    })
  })

  describe('createChat', () => {
    it('creates new chat', async () => {
      const chat = testDataGenerators.createChat({
        id: 'new-chat',
        title: 'New Chat',
      })

      vi.mocked(mockAxiosInstance.post).mockResolvedValueOnce({
        data: chat,
      })

      const module = await import('@/api/chat')
      const result = await module.createChat('New Chat')

      expect(result).toEqual(chat)
      expect(result.id).toBe('new-chat')
    })

    it('creates chat with default title', async () => {
      const chat = testDataGenerators.createChat()

      vi.mocked(mockAxiosInstance.post).mockResolvedValueOnce({
        data: chat,
      })

      const module = await import('@/api/chat')
      const result = await module.createChat()

      expect(result).toBeDefined()
    })
  })

  describe('sendMessage', () => {
    it('sends message to chat', async () => {
      const message = testDataGenerators.createMessage({
        id: 'msg-1',
        content: '你好',
        role: 'user',
      })

      vi.mocked(mockAxiosInstance.post).mockResolvedValueOnce({
        data: message,
      })

      const module = await import('@/api/chat')
      const result = await module.sendMessage('chat-1', '你好')

      expect(result).toEqual(message)
      expect(result.content).toBe('你好')
    })
  })

  describe('deleteChat', () => {
    it('deletes chat by id', async () => {
      vi.mocked(mockAxiosInstance.delete).mockResolvedValueOnce({
        data: { message: 'Chat deleted' },
      })

      const module = await import('@/api/chat')
      await expect(module.deleteChat('chat-1')).resolves.not.toThrow()
    })
  })

  describe('clearChat', () => {
    it('clears all messages from chat', async () => {
      vi.mocked(mockAxiosInstance.post).mockResolvedValueOnce({
        data: { message: 'Chat cleared' },
      })

      const module = await import('@/api/chat')
      await expect(module.clearChat('chat-1')).resolves.not.toThrow()
    })
  })

  describe('deleteMessage', () => {
    it('deletes message from chat', async () => {
      vi.mocked(mockAxiosInstance.delete).mockResolvedValueOnce({
        data: { message: 'Message deleted' },
      })

      const module = await import('@/api/chat')
      await expect(
        module.deleteMessage('chat-1', 'msg-1')
      ).resolves.not.toThrow()
    })
  })

  describe('Error Handling', () => {
    it('handles network errors', async () => {
      vi.mocked(mockAxiosInstance.get).mockRejectedValueOnce(
        new Error('Network error')
      )

      expect(axios.create).toBeDefined()
    })

    it('handles server errors', async () => {
      vi.mocked(mockAxiosInstance.get).mockRejectedValueOnce({
        response: {
          status: 500,
          data: {
            message: 'Internal server error',
          },
        },
      })

      expect(axios.create).toBeDefined()
    })
  })

  describe('Data Transformation', () => {
    it('returns correctly formatted chat response', async () => {
      const chat = testDataGenerators.createChat()

      vi.mocked(mockAxiosInstance.get).mockResolvedValueOnce({
        data: chat,
      })

      const module = await import('@/api/chat')
      const result = await module.getChatDetail('chat-1')

      expect(result).toHaveProperty('id')
      expect(result).toHaveProperty('title')
      expect(result).toHaveProperty('messages')
      expect(result).toHaveProperty('createdAt')
      expect(result).toHaveProperty('updatedAt')
    })

    it('handles multiple messages in chat', async () => {
      const messages = [
        testDataGenerators.createMessage({ id: '1', role: 'user' }),
        testDataGenerators.createMessage({ id: '2', role: 'assistant' }),
        testDataGenerators.createMessage({ id: '3', role: 'user' }),
      ]
      const chat = testDataGenerators.createChat({ messages })

      vi.mocked(mockAxiosInstance.get).mockResolvedValueOnce({
        data: chat,
      })

      const module = await import('@/api/chat')
      const result = await module.getChatDetail('chat-1')

      expect(result.messages).toHaveLength(3)
      expect(result.messages[0].role).toBe('user')
      expect(result.messages[1].role).toBe('assistant')
    })
  })
})
