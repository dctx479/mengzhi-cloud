export interface AuditLog {
  id: number
  userId: number
  username: string
  action: string
  resourceType: string
  resourceId: string
  resourceName?: string
  ipAddress: string
  userAgent: string
  status: 'success' | 'failure'
  errorMessage?: string
  beforeData?: Record<string, any>
  afterData?: Record<string, any>
  metadata?: Record<string, any>
  createdAt: string
}

export interface AuditLogQuery {
  page?: number
  pageSize?: number
  startTime?: string
  endTime?: string
  action?: string
  resourceType?: string
  resourceId?: string
  userId?: number
  username?: string
  status?: 'success' | 'failure'
  search?: string
}

export interface AuditLogListResponse {
  data: AuditLog[]
  total: number
  page: number
  pageSize: number
}

export interface AuditStats {
  actionDistribution: {
    action: string
    count: number
    percentage: number
  }[]
  actionTrend: {
    date: string
    count: number
    successCount: number
    failureCount: number
  }[]
  topUsers: {
    userId: number
    username: string
    count: number
  }[]
  resourceTypeDistribution: {
    resourceType: string
    count: number
    percentage: number
  }[]
  totalLogs: number
  successRate: number
  failureRate: number
}

export interface ExportAuditLogsParams {
  format: 'csv' | 'json' | 'excel'
  startTime?: string
  endTime?: string
  action?: string
  resourceType?: string
  userId?: number
  status?: 'success' | 'failure'
}
