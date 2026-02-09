import axios from 'axios'
import type {
  AuditLog,
  AuditLogQuery,
  AuditLogListResponse,
  AuditStats,
  ExportAuditLogsParams
} from '@/types/auditLog'

const api = axios.create({
  baseURL: '/api/audit-logs'
})

export const auditLogsApi = {
  /**
   * 获取审计日志列表
   */
  getAuditLogs: (params: AuditLogQuery) =>
    api.get<AuditLogListResponse>('/', { params }),

  /**
   * 获取审计日志详情
   */
  getAuditLogDetail: (id: number) =>
    api.get<AuditLog>(`/${id}`),

  /**
   * 获取审计统计数据
   */
  getAuditStats: (params?: { startTime?: string; endTime?: string }) =>
    api.get<AuditStats>('/stats', { params }),

  /**
   * 导出审计日志
   */
  exportAuditLogs: (params: ExportAuditLogsParams) =>
    api.post('/export', params, {
      responseType: 'blob'
    }),

  /**
   * 获取操作类型列表
   */
  getActionTypes: () =>
    api.get<string[]>('/action-types'),

  /**
   * 获取资源类型列表
   */
  getResourceTypes: () =>
    api.get<string[]>('/resource-types')
}
