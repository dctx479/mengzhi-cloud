/**
 * AI 对话 API 服务
 *
 * 后端路由（注册于 /api/v1/chat）：
 *   GET    /conversations             → 对话列表
 *   POST   /conversations             → 创建对话
 *   GET    /conversations/:id         → 对话详情（含消息）
 *   DELETE /conversations/:id         → 删除对话
 *   PATCH  /conversations/:id         → 更新对话（改名/收藏）
 *   POST   /message                   → 发送消息（非流式）
 *   POST   /stream                    → 发送消息（流式 SSE）
 */
import axios from 'axios'
import type { Chat, Message, ChatListResponse, StreamMessage, FileUploadResponse, ConversationExport } from '@/types/chat'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

const chatAPI = axios.create({
  baseURL: `${API_BASE}/v1/chat`,
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

// 添加响应拦截器 — 自动解包 {code, data, message} 结构
chatAPI.interceptors.response.use(
  (response) => {
    // 后端某些端点（如 /stream）返回 Pydantic 模型直接，不用 success_response 包装
    // 检查是否存在 code 和 data 字段（仅当两者都存在时才解包）
    const body = response.data
    if (body && typeof body === 'object' && 'code' in body && 'data' in body && body.code === 200) {
      return { ...response, data: body.data }
    }
    // 否则直接返回原始 response.data（已是最终数据或 Pydantic 序列化对象）
    return response
  },
  (error) => Promise.reject(error)
)

// ==================== 类型映射辅助 ====================

interface BackendConversation {
  id: number
  title: string
  status: string
  user_id: string
  message_count?: number
  created_at: string
  updated_at: string
  messages?: BackendMessage[]
}

interface BackendMessage {
  id: number
  role: string
  content: string
  created_at: string
  updated_at?: string
}

function mapConversation(conv: BackendConversation): Chat {
  return {
    id: String(conv.id),
    title: conv.title || '新对话',
    messages: (conv.messages || []).map(mapMessage),
    createdAt: conv.created_at,
    updatedAt: conv.updated_at,
    userId: conv.user_id,
  }
}

function mapMessage(m: BackendMessage): Message {
  return {
    id: String(m.id),
    content: m.content,
    role: m.role as 'user' | 'assistant',
    timestamp: m.created_at,
    status: 'sent',
  }
}

// ==================== API 函数 ====================

/**
 * 获取对话列表 — GET /conversations
 */
export async function getChatList(page = 1, pageSize = 20): Promise<ChatListResponse> {
  const response = await chatAPI.get<{
    total: number
    page: number
    page_size: number
    items: BackendConversation[]
  }>('/conversations', { params: { page, page_size: pageSize } })
  const body = response.data
  return {
    data: (body.items || []).map(mapConversation),
    total: body.total,
  }
}

/**
 * 获取对话详情（含消息历史）— GET /conversations/:id
 */
export async function getChatDetail(chatId: string): Promise<Chat> {
  const response = await chatAPI.get<BackendConversation>(`/conversations/${chatId}`)
  return mapConversation(response.data)
}

/**
 * 创建新对话 — POST /conversations
 */
export async function createChat(title?: string): Promise<Chat> {
  const response = await chatAPI.post<BackendConversation>('/conversations', { title })
  return mapConversation(response.data)
}

/**
 * 发送消息（非流式）— POST /message
 */
export async function sendMessage(chatId: string, content: string): Promise<Message> {
  const response = await chatAPI.post<{
    id: string
    conversation_id: number
    message: BackendMessage
    usage: Record<string, number>
  }>('/message', {
    content,
    conversation_id: chatId ? Number(chatId) : undefined,
  })
  return mapMessage(response.data.message)
}

/**
 * 流式发送消息 — POST /stream（使用 fetch 支持 POST + Auth headers）
 */
export async function sendMessageStream(
  chatId: string,
  content: string,
  onChunk: (chunk: StreamMessage) => void,
  onError?: (error: Error) => void,
  signal?: AbortSignal
): Promise<void> {
  const token = localStorage.getItem('token')
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  let response: Response
  try {
    response = await fetch(`${API_BASE}/v1/chat/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        content,
        conversation_id: chatId ? Number(chatId) : undefined,
      }),
      signal,
    })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') return
    const error = err instanceof Error ? err : new Error('Stream request failed')
    if (onError) onError(error)
    throw error
  }

  if (!response.ok) {
    // Attempt to read error details from response body
    let errorMessage = `Stream request failed: ${response.status}`
    try {
      const errorBody = await response.json()
      if (errorBody.message) {
        errorMessage = errorBody.message
      } else if (errorBody.detail) {
        errorMessage = errorBody.detail
      }
    } catch {
      // If response body is not JSON, keep HTTP status message
    }
    const error = new Error(errorMessage)
    if (onError) onError(error)
    throw error
  }

  const reader = response.body?.getReader()
  if (!reader) {
    const error = new Error('No response body')
    if (onError) onError(error)
    throw error
  }

  const decoder = new TextDecoder()
  let buffer = ''
  let doneCalled = false

  try {
    outer: while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const data = line.slice(6).trim()
        if (!data) continue

        try {
          const parsed = JSON.parse(data)
          if (parsed.type === 'done' || parsed.status === 'completed') {
            onChunk({ type: 'done' })
            doneCalled = true
            break outer
          } else if (parsed.error) {
            onChunk({ type: 'error', error: parsed.message || 'Stream error' })
          } else {
            // parsed is backend return JSON object, extract actual text content
            const text = parsed.content || parsed.text || parsed.delta?.content
            // Only emit if we have valid content text (avoid emitting raw SSE strings)
            if (typeof text === 'string' && text) {
              onChunk({ type: 'chunk', content: text })
            } else if (text) {
              onChunk({ type: 'chunk', content: JSON.stringify(text) })
            }
            // If no content field found, skip this frame (don't fall back to raw 'data')
          }
        } catch {
          // Non-JSON plain text chunk - only emit if line looks like raw content
          // Only emit if data doesn't look like a malformed JSON (avoid garbage data)
          if (data && !data.startsWith('{') && !data.startsWith('[')) {
            onChunk({ type: 'chunk', content: data })
          }
        }
      }
    }
    if (!doneCalled) onChunk({ type: 'done' })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') return
    const error = err instanceof Error ? err : new Error('Stream read error')
    if (onError) onError(error)
    throw error
  } finally {
    reader.releaseLock()
  }
}

/**
 * 上传文件
 */
export async function uploadFile(_chatId: string, file: File): Promise<FileUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  // Note: _chatId parameter kept for API compatibility but not used in path
  // Backend handles file association server-side
  const response = await chatAPI.post<FileUploadResponse>('/uploads', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

/**
 * 上传多个文件
 */
export async function uploadFiles(_chatId: string, files: File[]): Promise<FileUploadResponse[]> {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))
  // Note: _chatId parameter kept for API compatibility but not used in path
  // Backend handles file association server-side
  const response = await chatAPI.post<FileUploadResponse[]>('/uploads/batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

/**
 * 获取对话历史消息
 */
export async function getChatHistory(
  chatId: string,
  page = 1,
  pageSize = 50
): Promise<{ data: Message[]; total: number }> {
  const response = await chatAPI.get(`/conversations/${chatId}`, {
    params: { page, page_size: pageSize },
  })
  const conv = response.data as BackendConversation & { total?: number }
  const total = typeof conv.total === 'number' ? conv.total : (conv.messages?.length ?? 0)
  return { data: (conv.messages || []).map(mapMessage), total }
}

/**
 * 删除对话 — DELETE /conversations/:id
 */
export async function deleteChat(chatId: string): Promise<void> {
  await chatAPI.delete(`/conversations/${chatId}`)
}

/**
 * 清空对话消息（后端暂未实现，预留接口）
 */
export async function clearChat(chatId: string): Promise<void> {
  await chatAPI.post(`/conversations/${chatId}/clear`)
}

/**
 * 删除单条消息（后端暂未实现，预留接口）
 */
export async function deleteMessage(chatId: string, messageId: string): Promise<void> {
  await chatAPI.delete(`/conversations/${chatId}/messages/${messageId}`)
}

/**
 * 重新生成消息（后端暂未实现，预留接口）
 */
export async function regenerateMessage(chatId: string, messageId: string): Promise<Message> {
  const response = await chatAPI.post<BackendMessage>(
    `/conversations/${chatId}/messages/${messageId}/regenerate`
  )
  return mapMessage(response.data)
}

/**
 * 导出对话为JSON（后端暂未实现，预留接口）
 */
export async function exportConversation(chatId: string): Promise<ConversationExport> {
  const response = await chatAPI.get<ConversationExport>(`/conversations/${chatId}/export`)
  return response.data
}

/**
 * 导出对话为Markdown（后端暂未实现，预留接口）
 */
export async function exportConversationMarkdown(chatId: string): Promise<string> {
  const response = await chatAPI.get(`/conversations/${chatId}/export/markdown`, {
    responseType: 'text',
  })
  return response.data
}

/**
 * 收藏/取消收藏消息（后端暂未实现，预留接口）
 */
export async function toggleMessageFavorite(chatId: string, messageId: string): Promise<Message> {
  const response = await chatAPI.post<BackendMessage>(
    `/conversations/${chatId}/messages/${messageId}/favorite`
  )
  return mapMessage(response.data)
}

/**
 * 重命名对话 — PATCH /conversations/:id
 */
export async function renameChat(chatId: string, title: string): Promise<Chat> {
  const response = await chatAPI.patch<BackendConversation>(`/conversations/${chatId}`, { title })
  return mapConversation(response.data)
}

export default chatAPI
