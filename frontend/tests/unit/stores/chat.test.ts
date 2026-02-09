import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '@/stores/chat'
import * as chatAPI from '@/api/chat'

vi.mock('@/api/chat')

describe('Chat Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes with correct state', () => {
    const store = useChatStore()

    expect(store.chats).toEqual([])
    expect(store.currentChat).toBeNull()
    expect(store.messages).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.messageLoading).toBe(false)
  })

  it('creates new chat', async () => {
    const store = useChatStore()

    const mockChat = {
      id: 'chat-1',
      title: 'New Chat',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      userId: 'user-1'
    }

    vi.mocked(chatAPI.createChat).mockResolvedValueOnce(mockChat)

    await store.createNewChat('New Chat')

    expect(store.currentChat).toEqual(mockChat)
    expect(store.chats[0]).toEqual(mockChat)
    expect(store.totalChats).toBe(1)
  })

  it('resets state', () => {
    const store = useChatStore()

    store.chats = [{ id: 'chat-1', title: '', messages: [], createdAt: '', updatedAt: '', userId: '' }]
    store.currentChat = store.chats[0]
    store.messages = [{ id: 'msg-1', content: 'test', role: 'user', timestamp: '' }]
    store.error = 'Some error'

    store.resetState()

    expect(store.chats).toEqual([])
    expect(store.currentChat).toBeNull()
    expect(store.messages).toEqual([])
    expect(store.error).toBeNull()
  })
})
