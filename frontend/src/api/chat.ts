/**
 * AI 对话 API 服务
 */
import axios from 'axios'
import type { Chat, Message, ChatListResponse, SendMessageRequest, SendMessageResponse, StreamMessage, FileUploadResponse, ConversationExport } from '@/types/chat'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3000/api'

const chatAPI = axios.create({
  baseURL: `${API_BASE}/chat`,
  timeout: 30000,
})

// 添加 token 拦截器
chatAPI.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/**
 * 获取对话列表
 */
export async function getChatList(page = 1, pageSize = 20): Promise<ChatListResponse> {
  const response = await chatAPI.get<ChatListResponse>('/', {
    params: { page, pageSize },
  })
  return response.data
}

/**
 * 获取对话详情
 */
export async function getChatDetail(chatId: string): Promise<Chat> {
  const response = await chatAPI.get<Chat>(`/${chatId}`)
  return response.data
}

/**
 * 创建新对话
 */
export async function createChat(title?: string): Promise<Chat> {
  const response = await chatAPI.post<Chat>('/', { title })
  return response.data
}

/**
 * 发送消息
 */
export async function sendMessage(chatId: string, content: string): Promise<Message> {
  const response = await chatAPI.post<Message>(`/${chatId}/messages`, {
    content,
  })
  return response.data
}

/**
 * 流式发送消息 (SSE)
 */
export async function sendMessageStream(
  chatId: string,
  content: string,
  onChunk: (chunk: StreamMessage) => void,
  onError?: (error: Error) => void
): Promise<void> {
  return new Promise((resolve, reject) => {
    const eventSource = new EventSource(
      `${API_BASE}/chat/${chatId}/messages/stream?message=${encodeURIComponent(content)}`,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      } as any
    )

    eventSource.addEventListener('chunk', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data) as StreamMessage
        onChunk(data)
      } catch (e) {
        console.error('Parse stream chunk error:', e)
      }
    })

    eventSource.addEventListener('done', () => {
      eventSource.close()
      resolve()
    })

    eventSource.addEventListener('error', (event: Event) => {
      eventSource.close()
      const error = new Error('Stream connection error')
      if (onError) onError(error)
      reject(error)
    })
  })
}

/**
 * 上传文件
 */
export async function uploadFile(chatId: string, file: File): Promise<FileUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await chatAPI.post<FileUploadResponse>(`/${chatId}/uploads`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

/**
 * 上传多个文件
 */
export async function uploadFiles(chatId: string, files: File[]): Promise<FileUploadResponse[]> {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))

  const response = await chatAPI.post<FileUploadResponse[]>(
    `/${chatId}/uploads/batch`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )
  return response.data
}

/**
 * 获取对话历史
 */
export async function getChatHistory(
  chatId: string,
  page = 1,
  pageSize = 50
): Promise<{ data: Message[]; total: number }> {
  const response = await chatAPI.get(`/${chatId}/messages`, {
    params: { page, pageSize },
  })
  return response.data
}

/**
 * 删除对话
 */
export async function deleteChat(chatId: string): Promise<void> {
  await chatAPI.delete(`/${chatId}`)
}

/**
 * 清空对话
 */
export async function clearChat(chatId: string): Promise<void> {
  await chatAPI.post(`/${chatId}/clear`)
}

/**
 * 删除单条消息
 */
export async function deleteMessage(chatId: string, messageId: string): Promise<void> {
  await chatAPI.delete(`/${chatId}/messages/${messageId}`)
}

/**
 * 重新生成消息
 */
export async function regenerateMessage(chatId: string, messageId: string): Promise<Message> {
  const response = await chatAPI.post<Message>(`/${chatId}/messages/${messageId}/regenerate`)
  return response.data
}

/**
 * 导出对话为JSON
 */
export async function exportConversation(chatId: string): Promise<ConversationExport> {
  const response = await chatAPI.get<ConversationExport>(`/${chatId}/export`)
  return response.data
}

/**
 * 导出对话为Markdown
 */
export async function exportConversationMarkdown(chatId: string): Promise<string> {
  const response = await chatAPI.get(`/${chatId}/export/markdown`, {
    responseType: 'text',
  })
  return response.data
}

/**
 * 收藏/取消收藏消息
 */
export async function toggleMessageFavorite(chatId: string, messageId: string): Promise<Message> {
  const response = await chatAPI.post<Message>(`/${chatId}/messages/${messageId}/favorite`)
  return response.data
}

/**
 * 重命名对话
 */
export async function renameChat(chatId: string, title: string): Promise<Chat> {
  const response = await chatAPI.patch<Chat>(`/${chatId}`, { title })
  return response.data
}

export default chatAPI
