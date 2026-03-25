import axios, { type AxiosRequestConfig, type AxiosResponse } from 'axios'
import type { AdminStats, User, Enterprise, AIUsageData } from '@/types/admin'

interface TypedAdminApi {
  get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T>
  post<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>
  patch<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>
  delete<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T>
}

interface APIResponseWrapper<T = unknown> {
  code?: number
  data?: T
  message?: string
}

interface StatsInner {
  users?: { total?: number; active?: number }
  enterprises?: { total?: number }
  total_ai_usage?: number
}

interface AIUsageInner {
  chat?: { message_count?: number }
  content_generation?: { record_count?: number }
  items?: AIUsageData[]
}

const _api = axios.create({
  baseURL: '/api/admin',
})

// 请求拦截器 — 附加认证 token
_api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器 — 自动解包 response.data (HTTP body = APIResponse)
_api.interceptors.response.use(
  (response: AxiosResponse) => response.data,
  (error) => Promise.reject(error)
)

const api = _api as unknown as TypedAdminApi

/** 从后端 APIResponse 包装中提取 data 字段 */
function unwrapAdmin<T>(res: unknown): T {
  const r = res as APIResponseWrapper<T>
  return r.data !== undefined ? r.data : res as T
}

export const adminApi = {
  getStats: async (): Promise<AdminStats> => {
    const res = await api.get<APIResponseWrapper<StatsInner>>('/stats')
    const inner = unwrapAdmin<StatsInner>(res)
    // Also fetch AI usage total for the stats panel
    let totalAIUsage = 0
    try {
      const usageRes = await api.get<APIResponseWrapper<AIUsageInner>>('/ai-usage')
      const usageInner = unwrapAdmin<AIUsageInner>(usageRes)
      totalAIUsage = (usageInner?.chat?.message_count || 0) + (usageInner?.content_generation?.record_count || 0)
    } catch { /* ignore */ }
    return {
      totalUsers: inner?.users?.total || 0,
      totalEnterprises: inner?.enterprises?.total || 0,
      totalAIUsage,
      activeUsers: inner?.users?.active || 0,
    } as AdminStats
  },

  getUsers: async (params?: { search?: string }): Promise<User[]> => {
    const res = await api.get<APIResponseWrapper<{ items?: User[] } | User[]>>('/users', { params })
    const inner = unwrapAdmin<{ items?: User[] } | User[]>(res)
    return (Array.isArray(inner) ? inner : (inner as { items?: User[] })?.items || []) as User[]
  },
  updateUser: async (id: number, data: Partial<User>) => {
    const res = await api.patch<APIResponseWrapper<User>>(`/users/${id}`, data)
    return unwrapAdmin<User>(res)
  },
  deleteUser: (id: number) => api.delete(`/users/${id}`),

  getEnterprises: async (params?: { search?: string }): Promise<Enterprise[]> => {
    const res = await api.get<APIResponseWrapper<{ items?: Enterprise[] } | Enterprise[]>>('/enterprises', { params })
    const inner = unwrapAdmin<{ items?: Enterprise[] } | Enterprise[]>(res)
    return (Array.isArray(inner) ? inner : (inner as { items?: Enterprise[] })?.items || []) as Enterprise[]
  },
  updateEnterprise: async (id: number, data: Partial<Enterprise>) => {
    const res = await api.patch<APIResponseWrapper<Enterprise>>(`/enterprises/${id}`, data)
    return unwrapAdmin<Enterprise>(res)
  },
  deleteEnterprise: (id: number) => api.delete(`/enterprises/${id}`),

  getAIUsage: async (): Promise<AIUsageData[]> => {
    const res = await api.get<APIResponseWrapper<AIUsageInner | AIUsageData[]>>('/ai-usage')
    const inner = unwrapAdmin<AIUsageInner | AIUsageData[]>(res)
    // Backend returns array directly
    if (Array.isArray(inner)) return inner
    // Backend returns aggregate stats — synthesize a single chart point
    const typed = inner as AIUsageInner
    const items = typed?.items
    if (Array.isArray(items)) return items
    const today = new Date().toISOString().split('T')[0]
    const count = (typed?.chat?.message_count || 0) + (typed?.content_generation?.record_count || 0)
    return count > 0 ? [{ date: today, count }] : []
  },
}
