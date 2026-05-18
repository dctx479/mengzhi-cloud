/**
 * 用户中心 API 服务
 *
 * 所有请求通过统一 http 实例（baseURL = /api），与后端路由保持一致：
 *   订单   → /v1/orders
 *   配额   → /v1/quotas
 *   密码   → /v1/auth/change-password
 *   验证码 → /v1/auth/send-code
 */
import http from '@/utils/http'
import type {
  Order,
  OrdersResponse,
  QuotaData,
  QuotaHistory,
  QuotaHistoryResponse,
  UserSettings,
  ChangePasswordRequest,
  SecurityLog,
} from '@/types/user'

/**
 * 标准 API 响应格式
 * 由响应拦截器返回给调用者
 */
interface ApiResponse<T> {
  code: number
  data: T
  message: string
}

/**
 * 安全提取 API 响应数据
 * 处理 http.get/post 返回的 {code, data, message} 格式
 */
function extractData<T>(response: ApiResponse<T>): T {
  return response.data
}

/**
 * 获取订单列表
 */
export async function getOrders(params: {
  page?: number
  page_size?: number
  status?: string
  start_date?: string
  end_date?: string
  keyword?: string
}): Promise<OrdersResponse> {
  const res = await http.get<ApiResponse<{ items: Order[]; total: number; page: number; size: number }>>(
    '/v1/orders',
    {
      params: {
        page: params.page,
        size: params.page_size, // 后端参数名为 size
        status: params.status,
        start_date: params.start_date,
        end_date: params.end_date,
        keyword: params.keyword,
      },
    }
  )
  const inner = extractData(res) ?? {}
  return {
    items: inner.items || [],
    total: inner.total || 0,
    page: inner.page || 1,
    page_size: params.page_size || 10,
  }
}

/**
 * 获取订单详情
 */
export async function getOrderDetail(orderId: string): Promise<Order> {
  const res = await http.get<ApiResponse<Order>>(`/v1/orders/${orderId}`)
  return extractData(res) ?? ({} as Order)
}

/**
 * 创建订单（从套餐购买）
 */
export async function createOrderFromPackage(packageId: number): Promise<Order> {
  const res = await http.post<ApiResponse<Order>>('/v1/orders', { package_id: packageId })
  return extractData(res) ?? ({} as Order)
}

/**
 * 取消订单
 */
export async function cancelOrder(orderId: string): Promise<void> {
  await http.post(`/v1/orders/${orderId}/cancel`)
}

/**
 * 获取配额信息（汇总）
 * 后端返回 by_resource_type: { message, generation, storage, ... }
 * 需要映射为前端 QuotaData 格式
 */
export async function getQuota(): Promise<QuotaData> {
  const res = await http.get<ApiResponse<{ by_resource_type: Record<string, { used: number; limit: number }> }>>(
    '/v1/quotas/statistics/summary'
  )
  const inner = extractData(res) ?? {}
  // 后端 resource_type: message→chat, generation→content, storage→storage
  const byType = inner?.by_resource_type || {}
  const message = byType.message || {}
  const generation = byType.generation || {}
  const storage = byType.storage || {}
  return {
    chat_used: message.used ?? 0,
    chat_total: message.limit ?? 100,
    content_used: generation.used ?? 0,
    content_total: generation.limit ?? 50,
    storage_used: storage.used ?? 0,
    storage_total: storage.limit ?? 1024 * 1024 * 1024,
  }
}

/**
 * 获取配额历史记录
 */
export async function getQuotaHistory(params: {
  page?: number
  page_size?: number
  type?: string
}): Promise<QuotaHistoryResponse> {
  const res = await http.get<ApiResponse<{ items: QuotaHistory[]; total: number; page: number; page_size: number }>>(
    '/v1/quotas',
    { params }
  )
  const inner = extractData(res) ?? {}
  return {
    items: inner.items || [],
    total: inner.total || 0,
    page: inner.page || 1,
    page_size: inner.page_size || params.page_size || 20,
  }
}

/**
 * 获取用户设置
 */
export async function getSettings(): Promise<UserSettings> {
  try {
    const res = await http.get<ApiResponse<UserSettings>>('/v1/users/settings')
    return extractData(res) ?? getDefaultSettings()
  } catch {
    return getDefaultSettings()
  }
}

/**
 * 更新用户设置
 */
export async function updateSettings(data: Partial<UserSettings>): Promise<UserSettings> {
  const res = await http.put<ApiResponse<UserSettings>>('/v1/users/settings', data)
  return extractData(res) ?? getDefaultSettings()
}

/**
 * 修改密码 — 对应 POST /api/v1/auth/change-password
 */
export async function changePassword(data: ChangePasswordRequest): Promise<void> {
  await http.post('/v1/auth/change-password', {
    old_password: data.old_password,
    new_password: data.new_password,
  })
}

/**
 * 获取登录日志
 * 注意：后端参数 page_size 的别名为 pageSize
 */
export async function getSecurityLogs(params: {
  page?: number
  page_size?: number
}): Promise<{ items: SecurityLog[]; total: number }> {
  const res = await http.get<ApiResponse<{ items: SecurityLog[]; total: number }>>('/v1/users/security/logs', {
    params: {
      page: params.page,
      pageSize: params.page_size, // 后端参数别名为 pageSize
    },
  })
  const inner = extractData(res) ?? {}
  return { items: inner.items || [], total: inner.total || 0 }
}

/**
 * 绑定手机号
 */
export async function bindPhone(data: { phone: string; verification_code: string }): Promise<void> {
  await http.post('/v1/users/security/bind-phone', data)
}

/**
 * 绑定邮箱
 */
export async function bindEmail(data: { email: string; verification_code: string }): Promise<void> {
  await http.post('/v1/users/security/bind-email', data)
}

/**
 * 发送验证码 — 对应 POST /api/v1/auth/send-code
 */
export async function sendVerificationCode(data: {
  type: 'email' | 'phone'
  target: string
}): Promise<void> {
  await http.post('/v1/auth/send-code', null, {
    params: {
      identifier: data.target,
      code_type: data.type === 'email' ? 'bind_email' : 'bind_phone',
    },
  })
}

/**
 * 获取设备列表
 */
export async function getDevices(): Promise<
  Array<{
    id: string
    device_name: string
    device_type: string
    ip_address: string
    last_login: string
    is_current: boolean
  }>
> {
  const res = await http.get<
    ApiResponse<
      Array<{
        id: string
        device_name: string
        device_type: string
        ip_address: string
        last_login: string
        is_current: boolean
      }>
    >
  >('/v1/users/security/devices')
  return extractData(res) ?? []
}

/**
 * 删除设备
 */
export async function removeDevice(deviceId: string): Promise<void> {
  await http.delete(`/v1/users/security/devices/${deviceId}`)
}

/**
 * 获取默认设置
 */
function getDefaultSettings(): UserSettings {
  return {
    email_notifications: true,
    sms_notifications: false,
    profile_public: false,
    language: 'zh-CN',
    theme: 'light',
  }
}
