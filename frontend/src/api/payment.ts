/**
 * 支付 API 服务
 */
import http from '@/utils/http'

/** 从后端 {code, data, message} 包装中提取 data 字段 */
function unwrap<T>(res: unknown): T {
  const r = res as { data?: T }
  if (r.data !== undefined) return r.data
  throw new Error('Invalid response: missing data field')
}

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
  const res = await http.post<{ code: number; data: Payment; message: string }>(`/v1/orders/${data.order_id}/pay`, {
    payment_method: data.payment_method,
  })
  return unwrap<Payment>(res)
}

/**
 * 查询支付状态
 */
export async function getPaymentStatus(orderId: number): Promise<PaymentStatus> {
  const res = await http.get<{ code: number; data: PaymentStatus; message: string }>(`/v1/orders/${orderId}/payment-status`)
  return unwrap<PaymentStatus>(res)
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
  const res = await http.post<{ code: number; data: { processed: boolean }; message: string }>(`/v1/orders/${data.order_id}/payment-callback`, {
    payment_no: data.payment_no,
    transaction_id: data.transaction_id,
    callback_data: data.callback_data,
  })
  return unwrap<{ processed: boolean }>(res)
}
