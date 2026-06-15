/**
 * IP 智能对话 API 服务（IP 双人格：小数 / 小商）
 *
 * 后端路由（注册于 /api/v1/ip-chat）：
 *   POST   /message   → 发送消息（非流式，success_response 包装）
 *   GET    /ips       → 获取 IP 人格信息
 *   POST   /route     → 路由判断（content 为 query 参数）
 *   POST   /stream    → 发送消息（流式 SSE）
 */
import request from '@/utils/request'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

/** 从后端 success_response 包装中提取内层 data */
function unwrap<T>(res: unknown): T {
  const r = res as { data?: T }
  return r.data !== undefined ? r.data : (res as T)
}

export type IPType = 'xiaoshu' | 'xiaoshang'

export interface IPMessageRequest {
  content: string
  conversation_id?: number
  ip_type?: IPType
  temperature?: number
}

export interface IPMessageResponse {
  content: string
  ip_type: string
  ip_name: string
  conversation_id: number
  tokens: { input: number; output: number; total: number }
  cost: number
  metadata: { cultural_elements?: string[] }
}

export interface IPInfo {
  name: string
  description: string
  focus: string
}

export interface IPListResponse {
  xiaoshu: IPInfo
  xiaoshang: IPInfo
}

export interface RouteResponse {
  content: string
  routed_to: string
  explanation: string
}

export type IPStreamChunk =
  | { type: 'chunk'; content: string }
  | { type: 'done'; ip_type?: string; ip_name?: string }
  | { type: 'error'; message: string }

/**
 * 发送消息（非流式）— POST /message
 */
export const sendIPMessage = async (data: IPMessageRequest): Promise<IPMessageResponse> => {
  const res = await request.post<{ code: number; data: IPMessageResponse; message: string }>('/v1/ip-chat/message', data)
  return unwrap<IPMessageResponse>(res)
}

/**
 * 获取 IP 人格信息 — GET /ips
 */
export const getIPInfo = async (): Promise<IPListResponse> => {
  const res = await request.get<{ code: number; data: IPListResponse; message: string }>('/v1/ip-chat/ips')
  return unwrap<IPListResponse>(res)
}

/**
 * 路由判断 — POST /route?content=<urlencoded>
 */
export const routeIPMessage = async (content: string): Promise<RouteResponse> => {
  const res = await request.post<{ code: number; data: RouteResponse; message: string }>(`/v1/ip-chat/route?content=${encodeURIComponent(content)}`)
  return unwrap<RouteResponse>(res)
}

/**
 * 流式发送消息 — POST /stream（使用 fetch 支持 POST + Auth headers）
 */
export async function sendIPMessageStream(
  data: IPMessageRequest,
  onChunk: (chunk: IPStreamChunk) => void,
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
    response = await fetch(`${API_BASE}/v1/ip-chat/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        content: data.content,
        conversation_id: data.conversation_id,
        ip_type: data.ip_type,
        temperature: data.temperature,
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
          if (parsed.type === 'done') {
            onChunk({ type: 'done', ip_type: parsed.ip_type, ip_name: parsed.ip_name })
            doneCalled = true
            break outer
          } else if (parsed.type === 'error') {
            onChunk({ type: 'error', message: parsed.message || 'Stream error' })
          } else if (parsed.type === 'chunk') {
            if (typeof parsed.content === 'string' && parsed.content) {
              onChunk({ type: 'chunk', content: parsed.content })
            }
          }
        } catch {
          // Non-JSON frame — skip
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
