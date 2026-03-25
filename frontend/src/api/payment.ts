/**
 * 支付 API 服务
 */
import http from '@/utils/http'

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
  // 后端响应格式: {code: 200, data: Payment, message: "..."}
  // http.get/post 已通过响应拦截器自动解包 response.data，返回 {code, data, message}
  const response = res as unknown as { code?: number; data?: Payment; message?: string }
  if (response.data) {
    return response.data
  }
  throw new Error(`Invalid payment response: missing data field`)
}

/**
 * 查询支付状态
 */
export async function getPaymentStatus(orderId: number): Promise<PaymentStatus> {
  const res = await http.get<{ code: number; data: PaymentStatus; message: string }>(`/v1/orders/${orderId}/payment-status`)
  // 后端响应格式: {code: 200, data: PaymentStatus, message: "..."}
  const response = res as unknown as { code?: number; data?: PaymentStatus; message?: string }
  if (response.data) {
    return response.data
  }
  throw new Error(`Invalid payment status response: missing data field`)
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
  // 后端响应格式: {code: 200, data: {processed: boolean}, message: "..."}
  const response = res as unknown as { code?: number; data?: { processed: boolean }; message?: string }
  if (response.data) {
    return response.data
  }
  throw new Error(`Invalid payment callback response: missing data field`)
}
