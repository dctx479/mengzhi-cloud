/**
 * 对话状态管理 Store
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Chat, Message, FileUploadResponse } from '@/types/chat'
import * as chatAPI from '@/api/chat'

export const useChatStore = defineStore('chat', () => {
  // State
  const chats = ref<Chat[]>([])
  const currentChat = ref<Chat | null>(null)
  const messages = ref<Message[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const messageLoading = ref(false)
  const streamingMessageId = ref<string | null>(null)

  const currentPage = ref(1)
  const pageSize = ref(20)
  const totalChats = ref(0)

  // Computed
  const hasMoreChats = computed(() => currentPage.value * pageSize.value < totalChats.value)
  const sortedMessages = computed(() =>
    [...messages.value].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
  )
  const lastMessage = computed(() => sortedMessages.value[sortedMessages.value.length - 1] || null)

  // Actions
  const fetchChats = async (page = 1) => {
    loading.value = true
    error.value = null
    try {
      const response = await chatAPI.getChatList(page, pageSize.value)
      if (page === 1) {
        chats.value = response.data
      } else {
        chats.value.push(...response.data)
      }
      totalChats.value = response.total
      currentPage.value = page
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch chats'
    } finally {
      loading.value = false
    }
  }

  const fetchChatDetail = async (chatId: string) => {
    loading.value = true
    error.value = null
    try {
      const chat = await chatAPI.getChatDetail(chatId)
      currentChat.value = chat
      messages.value = chat.messages || []
      return chat
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch chat'
      throw err
    } finally {
      loading.value = false
    }
  }

  const createNewChat = async (title?: string) => {
    loading.value = true
    error.value = null
    try {
      const chat = await chatAPI.createChat(title)
      chats.value.unshift(chat)
      currentChat.value = chat
      messages.value = []
      totalChats.value++
      return chat
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create chat'
      throw err
    } finally {
      loading.value = false
    }
  }

  const sendMessage = async (
    content: string,
    files?: FileUploadResponse[],
    useStream?: boolean
  ) => {
    if (!currentChat.value) {
      error.value = 'No chat selected'
      return
    }

    messageLoading.value = true
    error.value = null

    try {
      // Add user message immediately
      const userMessage: Message = {
        id: `temp-${Date.now()}`,
        content,
        role: 'user',
        timestamp: new Date().toISOString(),
        status: 'sending',
        files: files,
      }
      messages.value.push(userMessage)

      // Create AI message for streaming or regular response
      const aiMessage: Message = {
        id: `ai-${Date.now()}`,
        content: '',
        role: 'assistant',
        timestamp: new Date().toISOString(),
        status: 'sending',
        isStreaming: useStream || false,
      }
      messages.value.push(aiMessage)
      streamingMessageId.value = aiMessage.id

      // Send to API with or without streaming
      if (useStream) {
        // Stream response
        await chatAPI.sendMessageStream(
          currentChat.value.id,
          content,
          (chunk) => {
            if (chunk.type === 'chunk' && chunk.content) {
              aiMessage.content += chunk.content
            } else if (chunk.type === 'done') {
              aiMessage.status = 'sent'
              aiMessage.isStreaming = false
              streamingMessageId.value = null
            } else if (chunk.type === 'error') {
              aiMessage.status = 'failed'
              aiMessage.content = `错误: ${chunk.error || 'Unknown error'}`
              aiMessage.isStreaming = false
              streamingMessageId.value = null
            }
          }
        )
      } else {
        // Regular response
        const response = await chatAPI.sendMessage(currentChat.value.id, content)
        aiMessage.content = response.content
        aiMessage.status = 'sent'
        aiMessage.isStreaming = false
        streamingMessageId.value = null
      }

      // Update user message
      const userIndex = messages.value.findIndex((m) => m.id === userMessage.id)
      if (userIndex !== -1) {
        messages.value[userIndex].status = 'sent'
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to send message'
      // Mark messages as failed
      const failedUserIndex = messages.value.findIndex(
        (m) => m.status === 'sending' && m.role === 'user'
      )
      if (failedUserIndex !== -1) {
        messages.value[failedUserIndex].status = 'failed'
      }

      const failedAiIndex = messages.value.findIndex(
        (m) => m.status === 'sending' && m.role === 'assistant'
      )
      if (failedAiIndex !== -1) {
        messages.value[failedAiIndex].status = 'failed'
      }
      streamingMessageId.value = null
      throw err
    } finally {
      messageLoading.value = false
    }
  }

  const deleteChat = async (chatId: string) => {
    error.value = null
    try {
      await chatAPI.deleteChat(chatId)
      chats.value = chats.value.filter((c) => c.id !== chatId)
      totalChats.value--
      if (currentChat.value?.id === chatId) {
        currentChat.value = null
        messages.value = []
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete chat'
      throw err
    }
  }

  const clearChat = async () => {
    if (!currentChat.value) {
      error.value = 'No chat selected'
      return
    }
    error.value = null
    try {
      await chatAPI.clearChat(currentChat.value.id)
      messages.value = []
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to clear chat'
      throw err
    }
  }

  const deleteMessage = async (messageId: string) => {
    if (!currentChat.value) {
      error.value = 'No chat selected'
      return
    }
    error.value = null
    try {
      await chatAPI.deleteMessage(currentChat.value.id, messageId)
      messages.value = messages.value.filter((m) => m.id !== messageId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete message'
      throw err
    }
  }

  const regenerateMessage = async (messageId: string) => {
    if (!currentChat.value) {
      error.value = 'No chat selected'
      return
    }
    error.value = null
    try {
      const response = await chatAPI.regenerateMessage(currentChat.value.id, messageId)
      const index = messages.value.findIndex((m) => m.id === messageId)
      if (index !== -1) {
        messages.value[index] = response
      }
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to regenerate message'
      throw err
    }
  }

  const exportConversation = async (format: 'json' | 'markdown' = 'json') => {
    if (!currentChat.value) {
      error.value = 'No chat selected'
      return
    }
    error.value = null
    try {
      if (format === 'json') {
        return await chatAPI.exportConversation(currentChat.value.id)
      } else {
        return await chatAPI.exportConversationMarkdown(currentChat.value.id)
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to export conversation'
      throw err
    }
  }

  const toggleMessageFavorite = async (messageId: string) => {
    if (!currentChat.value) {
      error.value = 'No chat selected'
      return
    }
    error.value = null
    try {
      const response = await chatAPI.toggleMessageFavorite(currentChat.value.id, messageId)
      const index = messages.value.findIndex((m) => m.id === messageId)
      if (index !== -1) {
        messages.value[index] = response
      }
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to toggle favorite'
      throw err
    }
  }

  const renameChat = async (chatId: string, title: string) => {
    error.value = null
    try {
      const response = await chatAPI.renameChat(chatId, title)
      const index = chats.value.findIndex((c) => c.id === chatId)
      if (index !== -1) {
        chats.value[index] = response
      }
      if (currentChat.value?.id === chatId) {
        currentChat.value = response
      }
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to rename chat'
      throw err
    }
  }

  const resetState = () => {
    chats.value = []
    currentChat.value = null
    messages.value = []
    currentPage.value = 1
    totalChats.value = 0
    error.value = null
    streamingMessageId.value = null
  }

  return {
    // State
    chats,
    currentChat,
    messages,
    loading,
    error,
    messageLoading,
    streamingMessageId,
    currentPage,
    pageSize,
    totalChats,
    // Computed
    hasMoreChats,
    sortedMessages,
    lastMessage,
    // Actions
    fetchChats,
    fetchChatDetail,
    createNewChat,
    sendMessage,
    deleteChat,
    clearChat,
    deleteMessage,
    regenerateMessage,
    exportConversation,
    toggleMessageFavorite,
    renameChat,
    resetState,
  }
})

