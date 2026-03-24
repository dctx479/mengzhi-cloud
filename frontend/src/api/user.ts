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
  const res = await http.get<{
    code: number
    data: { items: Order[]; total: number; page: number; size: number }
    message: string
  }>('/v1/orders', {
    params: {
      page: params.page,
      size: params.page_size,   // 后端参数名为 size
      status: params.status,
    },
  })
  const inner = (res as unknown as { data: { items: Order[]; total: number; page: number; size: number } }).data ?? {}
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
  return http.get<Order>(`/v1/orders/${orderId}`)
}

/**
 * 创建订单（从套餐购买）
 */
export async function createOrderFromPackage(packageId: number): Promise<Order> {
  const res = await http.post<{ code: number; data: Order }>('/v1/orders', { package_id: packageId })
  return (res as unknown as { data: Order }).data ?? (res as unknown as Order)
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
  const res = await http.get<{ code: number; data: any }>('/v1/quotas/statistics/summary')
  const inner = (res as unknown as { data: any }).data ?? {}
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
    storage_total: storage.limit ?? (1024 * 1024 * 1024),
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
  const res = await http.get<{
    code: number
    data: { items: QuotaHistory[]; total: number; page: number; page_size: number }
    message: string
  }>('/v1/quotas/', { params })
  const inner = (res as unknown as { data: { items: QuotaHistory[]; total: number; page: number; page_size: number } }).data ?? {}
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
    const res = await http.get<{ code: number; data: UserSettings; message: string }>('/v1/users/settings')
    return (res as unknown as { data: UserSettings }).data ?? (res as unknown as UserSettings)
  } catch {
    return {
      email_notifications: true,
      sms_notifications: false,
      profile_public: false,
      language: 'zh-CN',
      theme: 'light',
    }
  }
}

/**
 * 更新用户设置
 */
export async function updateSettings(data: Partial<UserSettings>): Promise<UserSettings> {
  const res = await http.put<{ code: number; data: UserSettings; message: string }>('/v1/users/settings', data)
  return (res as unknown as { data: UserSettings }).data ?? (res as unknown as UserSettings)
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
  const res = await http.get<{
    code: number
    data: { items: SecurityLog[]; total: number }
    message: string
  }>('/v1/users/security/logs', {
    params: {
      page: params.page,
      pageSize: params.page_size,   // 后端参数别名为 pageSize
    },
  })
  const inner = (res as unknown as { data: { items: SecurityLog[]; total: number } }).data ?? (res as unknown as { items: SecurityLog[]; total: number })
  return { items: inner.items || [], total: inner.total || 0 }
}

/**
 * 绑定手机号
 */
export async function bindPhone(data: {
  phone: string
  verification_code: string
}): Promise<void> {
  await http.post('/v1/users/security/bind-phone', data)
}

/**
 * 绑定邮箱
 */
export async function bindEmail(data: {
  email: string
  verification_code: string
}): Promise<void> {
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
export async function getDevices(): Promise<Array<{
  id: string
  device_name: string
  device_type: string
  ip_address: string
  last_login: string
  is_current: boolean
}>> {
  const res = await http.get<{ code: number; data: Array<unknown>; message: string }>('/v1/users/security/devices')
  return ((res as unknown as { data: Array<unknown> }).data ?? (res as unknown as Array<unknown>) ?? []) as Array<{
    id: string
    device_name: string
    device_type: string
    ip_address: string
    last_login: string
    is_current: boolean
  }>
}

/**
 * 删除设备
 */
export async function removeDevice(deviceId: string): Promise<void> {
  await http.delete(`/v1/users/security/devices/${deviceId}`)
}
