import axios from 'axios'
import type {
  AuditLog,
  AuditLogQuery,
  AuditLogListResponse,
  AuditStats,
  ExportAuditLogsParams
} from '@/types/auditLog'

// Backend response wrapper format
interface ApiResponse<T> {
  code?: number
  data?: T
  message?: string
}

// Backend list response format
interface BackendListResponse {
  logs?: AuditLog[]
  data?: AuditLog[]
  total?: number
  page?: number
  page_size?: number
}

const _api = axios.create({
  baseURL: '/api/v1/audit-logs',
  timeout: 15000,
})

_api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/** 从后端 success_response 包装中提取内层 data */
function unwrapInner<T>(res: { data: ApiResponse<T> }): T {
  const body = res.data  // HTTP body = {code, data: inner, message}
  if (body?.data !== undefined) {
    return body.data
  }
  // Fallback: if backend returns data without wrapper, return the body itself
  throw new Error(`Invalid response format: missing 'data' field in ${JSON.stringify(body)}`)
}

export const auditLogsApi = {
  /**
   * 获取审计日志列表
   * 返回 { data: AuditLogListResponse } 以供调用方 const { data } = await ... 使用
   */
  getAuditLogs: async (params: AuditLogQuery): Promise<{ data: AuditLogListResponse }> => {
    const res = await _api.get<ApiResponse<BackendListResponse>>('/', { params })
    const inner = unwrapInner<BackendListResponse>(res)
    return {
      data: {
        data: inner.logs || inner.data || [],
        total: inner.total || 0,
        page: inner.page || 1,
        pageSize: inner.page_size || params.pageSize || 20,
      } as AuditLogListResponse,
    }
  },

  /**
   * 获取审计日志详情
   * 返回 { data: AuditLog } 以供调用方 const { data } = await ... 使用
   */
  getAuditLogDetail: async (id: number): Promise<{ data: AuditLog }> => {
    const res = await _api.get<ApiResponse<AuditLog>>(`/${id}`)
    return { data: unwrapInner<AuditLog>(res) }
  },

  /**
   * 获取审计统计数据
   * 返回 { data: AuditStats } 以供调用方 const { data } = await ... 使用
   */
  getAuditStats: async (params?: { startTime?: string; endTime?: string }): Promise<{ data: AuditStats }> => {
    const res = await _api.get<ApiResponse<AuditStats>>('/stats', { params })
    return { data: unwrapInner<AuditStats>(res) }
  },

  /**
   * 导出审计日志（返回 AxiosResponse 以便调用方用 { data } 拿到 blob）
   * 后端为 GET /export，参数用 query string 传递
   */
  exportAuditLogs: (params: ExportAuditLogsParams) =>
    _api.get('/export', {
      params: {
        format: params.format === 'excel' ? 'csv' : params.format,
        user_id: params.userId,
        action: params.action,
        resource: params.resourceType,
        start_date: params.startTime,
        end_date: params.endTime,
      },
      responseType: 'blob',
    }),

  /**
   * 获取操作类型列表
   * 返回 { data: string[] } 以供调用方 actionsRes.data 使用
   * 注意: 后端该端点尚未实现（404），捕获错误后返回空数组
   */
  getActionTypes: async (): Promise<{ data: string[] }> => {
    try {
      const res = await _api.get<ApiResponse<Array<{ value: string; label: string }> | string[]>>('/action-types')
      const inner = unwrapInner<Array<{ value: string; label: string }> | string[]>(res)
      const arr = Array.isArray(inner) ? inner : []
      return { data: arr.map((item: { value: string } | string) => typeof item === 'string' ? item : item.value).filter(Boolean) as string[] }
    } catch {
      return { data: [] }
    }
  },

  /**
   * 获取资源类型列表
   * 返回 { data: string[] } 以供调用方 resourcesRes.data 使用
   * 注意: 后端该端点尚未实现（404），捕获错误后返回空数组
   */
  getResourceTypes: async (): Promise<{ data: string[] }> => {
    try {
      const res = await _api.get<ApiResponse<Array<{ value: string; label: string }> | string[]>>('/resource-types')
      const inner = unwrapInner<Array<{ value: string; label: string }> | string[]>(res)
      const arr = Array.isArray(inner) ? inner : []
      return { data: arr.map((item: { value: string } | string) => typeof item === 'string' ? item : item.value).filter(Boolean) as string[] }
    } catch {
      return { data: [] }
    }
  },
}
