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

interface ListResponse<T> {
  items?: T[]
  total?: number
  page?: number
  page_size?: number
}

interface StatsInner {
  users?: { total?: number; active?: number; new_today?: number }
  enterprises?: { total?: number; verified?: number }
}

interface AIUsageInner {
  chat?: { message_count?: number; total_tokens?: number }
  content_generation?: { record_count?: number; total_tokens?: number }
  total_tokens?: number
  period_days?: number
}

const _api = axios.create({
  baseURL: '/api/admin',
  timeout: 15000,
})

// Request interceptor — attach auth token
_api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor — auto-unwrap response.data (HTTP body = APIResponse)
_api.interceptors.response.use(
  (response: AxiosResponse) => response.data,
  (error) => Promise.reject(error)
)

const api = _api as unknown as TypedAdminApi

/** Extract data field from backend APIResponse wrapper */
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
    } catch (e) {
      console.warn('⚠️ WARNING: Failed to fetch AI usage for stats panel', e)
    }
    return {
      totalUsers: inner?.users?.total || 0,
      totalEnterprises: inner?.enterprises?.total || 0,
      totalAIUsage,
      activeUsers: inner?.users?.active || 0,
    }
  },

  getUsers: async (params?: { search?: string; page?: number; page_size?: number }): Promise<{ items: User[]; total: number }> => {
    const res = await api.get<APIResponseWrapper<ListResponse<User>>>('/users', { params })
    const inner = unwrapAdmin<ListResponse<User>>(res)
    return { items: inner?.items || [], total: inner?.total || 0 }
  },
  updateUser: async (id: number, data: Partial<User>) => {
    const res = await api.patch<APIResponseWrapper<User>>(`/users/${id}`, data)
    return unwrapAdmin<User>(res)
  },
  deleteUser: (id: number) => api.delete(`/users/${id}`),

  getEnterprises: async (params?: { search?: string; page?: number; page_size?: number }): Promise<{ items: Enterprise[]; total: number }> => {
    const res = await api.get<APIResponseWrapper<ListResponse<Enterprise>>>('/enterprises', { params })
    const inner = unwrapAdmin<ListResponse<Enterprise>>(res)
    return { items: inner?.items || [], total: inner?.total || 0 }
  },
  updateEnterprise: async (id: number, data: Partial<Enterprise>) => {
    const res = await api.patch<APIResponseWrapper<Enterprise>>(`/enterprises/${id}`, data)
    return unwrapAdmin<Enterprise>(res)
  },
  deleteEnterprise: (id: number) => api.delete(`/enterprises/${id}`),

  getAIUsage: async (): Promise<AIUsageData[]> => {
    const res = await api.get<APIResponseWrapper<AIUsageInner>>('/ai-usage')
    const inner = unwrapAdmin<AIUsageInner>(res)
    // Backend returns aggregate stats — synthesize a single chart point
    const today = new Date().toISOString().split('T')[0]
    const count = (inner?.chat?.message_count || 0) + (inner?.content_generation?.record_count || 0)
    return count > 0 ? [{ date: today, count }] : []
  },
}
