/**
 * 用户中心 API 服务
 */
import axios from 'axios'
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

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3000/api'

// 创建 axios 实例
const userAPI = axios.create({
  baseURL: `${API_BASE}/user`,
  timeout: 10000,
})

// 请求拦截器 - 添加 token
userAPI.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

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
  const response = await userAPI.get<OrdersResponse>('/orders', { params })
  return response.data
}

/**
 * 获取订单详情
 */
export async function getOrderDetail(orderId: string): Promise<Order> {
  const response = await userAPI.get<Order>(`/orders/${orderId}`)
  return response.data
}

/**
 * 创建订单
 */
export async function createOrder(data: {
  product_ids: string[]
  quantities: number[]
}): Promise<Order> {
  const response = await userAPI.post<Order>('/orders', data)
  return response.data
}

/**
 * 取消订单
 */
export async function cancelOrder(orderId: string): Promise<void> {
  await userAPI.post(`/orders/${orderId}/cancel`)
}

/**
 * 获取配额信息
 */
export async function getQuota(): Promise<QuotaData> {
  const response = await userAPI.get<QuotaData>('/quota')
  return response.data
}

/**
 * 获取配额历史记录
 */
export async function getQuotaHistory(params: {
  page?: number
  page_size?: number
  type?: string
}): Promise<QuotaHistoryResponse> {
  const response = await userAPI.get<QuotaHistoryResponse>('/quota/history', { params })
  return response.data
}

/**
 * 购买配额
 */
export async function purchaseQuota(data: {
  type: string
  amount: number
  price: number
}): Promise<void> {
  await userAPI.post('/quota/purchase', data)
}

/**
 * 获取用户设置
 */
export async function getSettings(): Promise<UserSettings> {
  const response = await userAPI.get<UserSettings>('/settings')
  return response.data
}

/**
 * 更新用户设置
 */
export async function updateSettings(data: Partial<UserSettings>): Promise<UserSettings> {
  const response = await userAPI.put<UserSettings>('/settings', data)
  return response.data
}

/**
 * 修改密码
 */
export async function changePassword(data: ChangePasswordRequest): Promise<void> {
  await userAPI.post('/security/change-password', data)
}

/**
 * 获取登录日志
 */
export async function getSecurityLogs(params: {
  page?: number
  page_size?: number
}): Promise<{ items: SecurityLog[]; total: number }> {
  const response = await userAPI.get<{ items: SecurityLog[]; total: number }>('/security/logs', {
    params,
  })
  return response.data
}

/**
 * 绑定手机号
 */
export async function bindPhone(data: {
  phone: string
  verification_code: string
}): Promise<void> {
  await userAPI.post('/security/bind-phone', data)
}

/**
 * 绑定邮箱
 */
export async function bindEmail(data: {
  email: string
  verification_code: string
}): Promise<void> {
  await userAPI.post('/security/bind-email', data)
}

/**
 * 发送验证码
 */
export async function sendVerificationCode(data: {
  type: 'email' | 'phone'
  target: string
}): Promise<void> {
  await userAPI.post('/security/send-verification-code', data)
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
  const response = await userAPI.get('/security/devices')
  return response.data
}

/**
 * 删除设备
 */
export async function removeDevice(deviceId: string): Promise<void> {
  await userAPI.delete(`/security/devices/${deviceId}`)
}

/**
 * 创建订单（从套餐购买）
 */
export async function createOrderFromPackage(packageId: number): Promise<any> {
  const response = await axios.post(
    `${API_BASE}/v1/orders`,
    { package_id: packageId },
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
    }
  )
  return response.data.data
}

export default userAPI
