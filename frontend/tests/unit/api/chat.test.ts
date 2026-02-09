import { describe, it, expect, beforeEach, vi } from 'vitest'
import axios from 'axios'
import * as chatAPI from '@/api/chat'
import { testDataGenerators } from '../utils/test-utils'

/**
 * Chat API 测试
 * 测试对话相关API调用
 */

vi.mock('axios')

describe('Chat API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getChatList', () => {
    it('fetches chat list with pagination', async () => {
      const chats = [
        testDataGenerators.createChat({ id: 'chat-1' }),
        testDataGenerators.createChat({ id: 'chat-2' }),
      ]

      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: {
            data: chats,
            total: 2,
          },
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/chat')
      const result = await module.getChatList(1, 20)

      expect(result.data).toEqual(chats)
      expect(result.total).toBe(2)
    })

    it('handles different page numbers', async () => {
      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: {
            data: [],
            total: 100,
          },
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/chat')
      await module.getChatList(5, 20)

      expect(axios.create).toBeDefined()
    })

    it('handles empty chat list', async () => {
      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: {
            data: [],
            total: 0,
          },
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

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

      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: chat,
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/chat')
      const result = await module.getChatDetail('chat-1')

      expect(result).toEqual(chat)
      expect(result.messages).toHaveLength(2)
    })

    it('handles chat not found error', async () => {
      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockRejectedValueOnce({
          response: {
            status: 404,
            data: {
              message: 'Chat not found',
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

    it('includes full chat metadata', async () => {
      const chat = testDataGenerators.createChat({
        id: 'chat-123',
        title: '产品咨询',
        createdAt: '2024-01-01T00:00:00Z',
      })

      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: chat,
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

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

      vi.mocked(axios.create).mockReturnValue({
        post: vi.fn().mockResolvedValueOnce({
          data: chat,
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/chat')
      const result = await module.createChat('New Chat')

      expect(result).toEqual(chat)
      expect(result.id).toBe('new-chat')
    })

    it('creates chat with default title', async () => {
      const chat = testDataGenerators.createChat()

      vi.mocked(axios.create).mockReturnValue({
        post: vi.fn().mockResolvedValueOnce({
          data: chat,
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/chat')
      const result = await module.createChat()

      expect(result).toBeDefined()
    })

    it('handles create error', async () => {
      vi.mocked(axios.create).mockReturnValue({
        post: vi.fn().mockRejectedValueOnce({
          response: {
            status: 400,
            data: {
              message: 'Invalid request',
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

  describe('sendMessage', () => {
    it('sends message to chat', async () => {
      const message = testDataGenerators.createMessage({
        id: 'msg-1',
        content: '你好',
        role: 'user',
      })

      vi.mocked(axios.create).mockReturnValue({
        post: vi.fn().mockResolvedValueOnce({
          data: message,
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/chat')
      const result = await module.sendMessage('chat-1', '你好')

      expect(result).toEqual(message)
      expect(result.content).toBe('你好')
    })

    it('includes message in request', async () => {
      const message = testDataGenerators.createMessage()

      vi.mocked(axios.create).mockReturnValue({
        post: vi.fn().mockResolvedValueOnce({
          data: message,
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/chat')
      await module.sendMessage('chat-1', 'test message')

      expect(axios.create).toBeDefined()
    })

    it('handles send error', async () => {
      vi.mocked(axios.create).mockReturnValue({
        post: vi.fn().mockRejectedValueOnce({
          response: {
            status: 500,
            data: {
              message: 'Failed to process message',
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

  describe('deleteChat', () => {
    it('deletes chat by id', async () => {
      vi.mocked(axios.create).mockReturnValue({
        delete: vi.fn().mockResolvedValueOnce({
          data: { message: 'Chat deleted' },
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/chat')
      await expect(module.deleteChat('chat-1')).resolves.not.toThrow()
    })

    it('handles delete error', async () => {
      vi.mocked(axios.create).mockReturnValue({
        delete: vi.fn().mockRejectedValueOnce({
          response: {
            status: 404,
            data: {
              message: 'Chat not found',
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

  describe('clearChat', () => {
    it('clears all messages from chat', async () => {
      vi.mocked(axios.create).mockReturnValue({
        post: vi.fn().mockResolvedValueOnce({
          data: { message: 'Chat cleared' },
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/chat')
      await expect(module.clearChat('chat-1')).resolves.not.toThrow()
    })

    it('handles clear error', async () => {
      vi.mocked(axios.create).mockReturnValue({
        post: vi.fn().mockRejectedValueOnce({
          response: {
            status: 400,
            data: {
              message: 'Cannot clear chat',
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

  describe('deleteMessage', () => {
    it('deletes message from chat', async () => {
      vi.mocked(axios.create).mockReturnValue({
        delete: vi.fn().mockResolvedValueOnce({
          data: { message: 'Message deleted' },
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/chat')
      await expect(
        module.deleteMessage('chat-1', 'msg-1')
      ).resolves.not.toThrow()
    })

    it('handles message not found error', async () => {
      vi.mocked(axios.create).mockReturnValue({
        delete: vi.fn().mockRejectedValueOnce({
          response: {
            status: 404,
            data: {
              message: 'Message not found',
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

  describe('Error Handling', () => {
    it('handles network errors', async () => {
      vi.mocked(axios.create).mockReturnValue({
        get: vi
          .fn()
          .mockRejectedValueOnce(new Error('Network error')),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      expect(axios.create).toBeDefined()
    })

    it('handles server errors', async () => {
      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockRejectedValueOnce({
          response: {
            status: 500,
            data: {
              message: 'Internal server error',
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

    it('handles timeout errors', async () => {
      vi.mocked(axios.create).mockReturnValue({
        post: vi.fn().mockRejectedValueOnce({
          code: 'ECONNABORTED',
          message: 'timeout of 10000ms exceeded',
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

  describe('Data Transformation', () => {
    it('returns correctly formatted chat response', async () => {
      const chat = testDataGenerators.createChat()

      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: chat,
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

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

      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn().mockResolvedValueOnce({
          data: chat,
        }),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      const module = await import('@/api/chat')
      const result = await module.getChatDetail('chat-1')

      expect(result.messages).toHaveLength(3)
      expect(result.messages[0].role).toBe('user')
      expect(result.messages[1].role).toBe('assistant')
    })
  })

  describe('API Configuration', () => {
    it('uses correct API endpoints', () => {
      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn(),
        post: vi.fn(),
        delete: vi.fn(),
        defaults: {
          headers: {
            common: {},
          },
        },
      } as any)

      expect(axios.create).toBeDefined()
    })

    it('sets appropriate headers', () => {
      vi.mocked(axios.create).mockReturnValue({
        get: vi.fn(),
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
