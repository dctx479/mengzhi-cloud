/**
 * 智能客服 API 服务
 *
 * 后端路由（注册于 /api/v1/kefu）：
 *   POST   /chat              → 发送消息（非流式）
 *   POST   /chat/stream       → 发送消息（流式 SSE）
 *   GET    /sessions          → 会话列表
 *   POST   /sessions          → 创建会话
 *   GET    /sessions/{id}     → 会话详情
 *   DELETE /sessions/{id}     → 删除会话（自动蒸馏）
 *   POST   /sessions/{id}/distill → 手动蒸馏 Session Summary
 *   GET    /tickets           → 工单列表
 *   POST   /tickets           → 创建工单
 *   GET    /tickets/{id}      → 工单详情
 *   PATCH  /tickets/{id}      → 更新工单
 *   GET    /profile           → 用户画像（5层 Persona）
 *   POST   /profile/correction → 纠正记录
 *   GET    /stats             → 统计数据
 *   POST   /kb/rebuild        → 重建知识库
 *   GET    /mcp/tools         → MCP 工具列表
 */
import http from '@/utils/http'

const BASE = '/v1/kefu'

// ============================================================
// Types
// ============================================================

export interface KefuChatRequest {
  session_id?: string
  message: string
  user_name?: string
}

export interface KefuChatResponse {
  reply: string
  session_id: string
  emotion: string
  emotion_intensity: number
  emotion_should_escalate: boolean
  intent: string
  intent_confidence: number
  action: string
  priority: string
  ticket_id?: string
  confidence: number
  processing_time_ms: number
}

export interface KefuSession {
  id: number
  session_id: string
  user_id: number
  status: string
  title: string
  user_name: string
  message_count: number
  emotion_type?: string
  intent_type?: string
  created_at: string
  updated_at: string
}

export interface KefuMessage {
  id: number
  conversation_id: number
  role: string
  content: string
  emotion?: string
  emotion_intensity?: number
  intent?: string
  confidence?: number
  action?: string
  created_at: string
}

export interface KefuTicket {
  id: number
  ticket_uuid: string
  user_id: number
  category: string
  priority: string
  status: string
  title: string
  description: string
  user_name?: string
  assigned_to?: string
  emotion?: string
  emotion_intensity?: number
  intent?: string
  created_at: string
  updated_at: string
  resolved_at?: string
  closed_at?: string
  messages?: KefuTicketMessage[]
}

export interface KefuTicketMessage {
  id: number
  ticket_id: number
  role: string
  content: string
  created_at: string
}

export interface TicketCreateRequest {
  title: string
  description: string
  category?: string
  priority?: string
}

export interface TicketUpdateRequest {
  status?: string
  priority?: string
  assigned_to?: string
  add_message?: string
}

export interface KefuStats {
  total: number
  pending: number
  processing: number
  resolved: number
  closed: number
  by_category: Record<string, number>
}

// ============================================================
// API Functions
// ============================================================

// 聊天（/chat 使用 response_model=ChatResponse，FastAPI 直接返回，无 success_response 包装）
export async function sendChat(request: KefuChatRequest): Promise<KefuChatResponse> {
  const res = await http.post<KefuChatResponse>(`${BASE}/chat`, request)
  return res as unknown as KefuChatResponse
}

// 流式聊天
export async function sendChatStream(
  request: KefuChatRequest,
  onChunk: (content: string) => void,
  onMeta?: (meta: Record<string, unknown>) => void,
  onDone?: () => void
): Promise<void> {
  const token = localStorage.getItem('token')
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || '/api'}${BASE}/chat/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    let errorMessage = `Stream request failed: ${response.status}`
    try {
      const errorBody = await response.json()
      errorMessage = errorBody.message || errorBody.detail || errorMessage
    } catch { /* non-JSON body */ }
    throw new Error(errorMessage)
  }

  const reader = response.body?.getReader()
  if (!reader) return

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const data = JSON.parse(line.slice(6))
        if (data.type === 'meta') {
          onMeta?.(data)
        } else if (data.type === 'chunk') {
          onChunk(data.content)
        } else if (data.type === 'done') {
          onDone?.()
        }
      } catch {
        // ignore parse error
      }
    }
  }
}

// 会话管理
export async function getSessions(limit = 20) {
  const res = await http.get(`${BASE}/sessions`, { params: { limit } })
  const d = (res as unknown as { data: { sessions: KefuSession[]; total: number } })
  return d.data ?? res
}

export async function createSession(title?: string) {
  const res = await http.post(`${BASE}/sessions`, { title })
  return (res as unknown as { data: { session_id: string } }).data ?? res
}

export async function getSession(sessionId: string) {
  const res = await http.get(`${BASE}/sessions/${sessionId}`)
  return res
}

export async function deleteSession(sessionId: string) {
  const res = await http.delete(`${BASE}/sessions/${sessionId}`)
  return res
}

// 工单管理
export async function getTickets(params?: {
  status?: string
  category?: string
  page?: number
  page_size?: number
}) {
  const res = await http.get(`${BASE}/tickets`, { params })
  const d = (res as unknown as { data: { items: KefuTicket[]; total: number; page: number } })
  return d.data ?? res
}

export async function createTicket(request: TicketCreateRequest) {
  const res = await http.post(`${BASE}/tickets`, request)
  return (res as unknown as { data: KefuTicket }).data ?? res
}

export async function getTicket(ticketId: number) {
  const res = await http.get(`${BASE}/tickets/${ticketId}`)
  return (res as unknown as { data: KefuTicket }).data ?? res
}

export async function updateTicket(ticketId: number, request: TicketUpdateRequest) {
  const res = await http.patch(`${BASE}/tickets/${ticketId}`, request)
  return (res as unknown as { data: KefuTicket }).data ?? res
}

// 统计
export async function getKefuStats(): Promise<KefuStats> {
  const res = await http.get(`${BASE}/stats`)
  return (res as unknown as { data: KefuStats }).data as KefuStats
}

// 用户画像（5层 Persona 模型 v2.0）
export interface UserProfile {
  user_id: number
  persona_version: string
  generated_at: string
  layer_0_identity: {
    username: string
    email: string
    member_days: number
    member_since: string
    user_type: string
    role: string
    status: string
  }
  layer_1_purchase: {
    total_orders: number
    total_spent: number
    avg_order_value: number
    consumption_level: string
    purchase_frequency: string
    categories: Array<{ name: string; count: number }>
    last_purchase_days_ago: number | null
    recency: string
  }
  layer_2_communication: {
    message_count: number
    avg_message_length: number
    style: string
    active_hours: number[]
    topic_distribution: Array<{ topic: string; count: number; intent: string }>
  }
  layer_3_emotion: {
    dominant_emotion: string
    distribution: Record<string, { count: number; ratio: number }>
    escalation_tendency: string
    negative_ratio: number
    recent_emotions: string[]
    emotion_strategy: string
  }
  layer_4_service: {
    total_tickets: number
    open_tickets: number
    resolved_tickets: number
    resolution_rate: number
    escalated_count: number
    satisfaction: string
    common_issues: Array<{ category: string; count: number }>
  }
  engagement_score: {
    score: number
    level: string
    breakdown: Record<string, number>
  }
  strategy: {
    level_tone: string
    level_rules: string[]
    emotion_rule: string
    recency_rules: string[]
  }
  insights: string[]
}

export async function getUserProfile(): Promise<UserProfile> {
  const res = await http.get(`${BASE}/profile`)
  return (res as unknown as { data: UserProfile }).data as UserProfile
}

// Session Summary 蒸馏
export interface SessionSummary {
  session_id: string
  user_id: number
  distilled_at: string
  turn_count: number
  user_message_count: number
  topic_summary: string
  mood: string
  dominant_emotion: string
  dominant_intent: string
  discoveries: Array<{ type: string; text: string }>
  had_ticket: boolean
  had_escalation: boolean
  followup_topics: string[]
}

export async function distillSession(sessionId: string): Promise<SessionSummary> {
  const res = await http.post(`${BASE}/sessions/${sessionId}/distill`)
  return (res as unknown as { data: SessionSummary }).data as SessionSummary
}

// 纠正记录
export async function recordCorrection(params: {
  session_id: string
  correction_type: 'emotion' | 'intent' | 'answer' | 'profile'
  original: string
  corrected: string
}) {
  const res = await http.post(`${BASE}/profile/correction`, params)
  return (res as unknown as { data: { recorded: boolean } }).data ?? res
}

// MCP 工具
export async function getMcpTools() {
  const res = await http.get(`${BASE}/mcp/tools`)
  return res
}