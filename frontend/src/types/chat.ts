/**
 * AI 对话相关类型定义
 */

export interface FileAttachment {
  id: string
  name: string
  size: number
  type: string
  url: string
  uploadedAt: string
}

export interface ImageAttachment {
  id: string
  url: string
  name: string
  size: number
  uploadedAt: string
}

export interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: string
  status?: 'sending' | 'sent' | 'failed'
  metadata?: Record<string, any>
  files?: FileAttachment[]
  images?: ImageAttachment[]
  isStreaming?: boolean
}

export interface Chat {
  id: string
  title: string
  messages: Message[]
  createdAt: string
  updatedAt: string
  userId: string
  tokenCount?: number
}

export interface ChatListResponse {
  data: Chat[]
  total: number
}

export interface SendMessageRequest {
  chatId: string
  content: string
  context?: Record<string, any>
  files?: FileAttachment[]
  images?: ImageAttachment[]
}

export interface SendMessageResponse {
  message: Message
  reply: Message
}

export interface ChatCreateRequest {
  title?: string
  initialMessage?: string
}

export interface ChatCreateResponse {
  chat: Chat
}

export interface MessageBubbleProps {
  message: Message
  isLoading?: boolean
  showTime?: boolean
}

export interface StreamMessage {
  type: 'start' | 'chunk' | 'done' | 'error'
  content?: string
  error?: string
  messageId?: string
}

export interface FileUploadResponse {
  id: string
  name: string
  size: number
  type: string
  url: string
  uploadedAt: string
}

export interface ConversationExport {
  id: string
  title: string
  createdAt: string
  messages: Message[]
}
