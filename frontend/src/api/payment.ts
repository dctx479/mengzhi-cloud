/**
 * 支付 API 服务
 */
import axios from 'axios'

// P1-8: 强制从环境变量读取API基础URL，未配置时抛出错误
const API_BASE = import.meta.env.VITE_API_BASE
if (!API_BASE) {
  throw new Error(
    'VITE_API_BASE 环境变量未配置！\n' +
    '请在 .env 文件中配置:\n' +
    '  VITE_API_BASE=http://localhost:8000\n' +
    '或在 .env.production 中配置生产环境地址'
  )
}

// 验证URL格式
try {
  new URL(API_BASE)
} catch (error) {
  throw new Error(
    `VITE_API_BASE 配置格式错误: ${API_BASE}\n` +
    '请确保配置的是完整的URL，例如:\n' +
    '  VITE_API_BASE=http://localhost:8000'
  )
}

// 创建 axios 实例
const paymentAPI = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  timeout: 30000,
})

// 请求拦截器 - 添加 token
paymentAPI.interceptors.request.use(
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

// 响应拦截器 - 统一处理响应
paymentAPI.interceptors.response.use(
  (response) => {
    // 如果响应包含 data 字段，返回 data
    if (response.data && response.data.data !== undefined) {
      return response.data.data
    }
    return response.data
  },
  (error) => {
    // 统一错误处理
    if (error.response) {
      const { data } = error.response
      throw new Error(data.message || '请求失败')
    }
    throw error
  }
)

/**
 * 支付相关类型定义
 */
export interface Payment {
  id: number
  payment_no: string
  order_id: number
  amount: number
  payment_method: string
  status: string
  transaction_id?: string
  paid_at?: string
  failed_at?: string
  failure_reason?: string
  created_at: string
  qr_code?: string
  pay_url?: string
}

export interface PaymentStatus {
  order_id: number
  order_status: string
  payment_id?: number
  payment_no?: string
  payment_method?: string
  payment_status?: string
  amount?: number
  paid: boolean
  paid_at?: string
  transaction_id?: string
}

/**
 * 创建支付
 */
export async function createPayment(data: {
  order_id: number
  payment_method: string
}): Promise<Payment> {
  return await paymentAPI.post(`/orders/${data.order_id}/pay`, {
    payment_method: data.payment_method,
  })
}

/**
 * 查询支付状态
 */
export async function getPaymentStatus(orderId: number): Promise<PaymentStatus> {
  return await paymentAPI.get(`/orders/${orderId}/payment-status`)
}

/**
 * 支付回调（仅供测试）
 */
export async function paymentCallback(data: {
  order_id: number
  payment_no: string
  transaction_id?: string
  callback_data: Record<string, any>
}): Promise<{ processed: boolean }> {
  return await paymentAPI.post(`/orders/${data.order_id}/payment-callback`, {
    payment_no: data.payment_no,
    transaction_id: data.transaction_id,
    callback_data: data.callback_data,
  })
}

export default paymentAPI
