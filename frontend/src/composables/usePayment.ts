/**
 * 支付相关的Composable
 *
 * P2-12: 提取支付逻辑到可复用的Composable
 *
 * 功能:
 * - 创建支付
 * - 查询支付状态
 * - 轮询支付状态（指数退避策略）
 * - 支付状态管理
 */

import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { createPayment, getPaymentStatus, type Payment, type PaymentStatus } from '@/api/payment'
import type { Order } from '@/types/user'

// P2-13: 定义常量
const POLL_CONFIG = {
  MAX_ATTEMPTS: 15,        // 最多轮询15次
  INITIAL_INTERVAL: 1000,  // 初始间隔1秒
  MAX_INTERVAL: 5000,      // 最大间隔5秒
  TIMEOUT: 60000,          // 总超时时间60秒
} as const

const PAYMENT_METHOD_NAMES: Record<string, string> = {
  alipay: '支付宝',
  wechat: '微信',
  balance: '余额',
} as const

export interface UsePaymentOptions {
  /** 开发模式标识 */
  devMode?: boolean
  /** 支付成功回调 */
  onSuccess?: () => void
  /** 支付失败回调 */
  onFailed?: (reason: string) => void
}

export function usePayment(options: UsePaymentOptions = {}) {
  // 状态
  const loading = ref(false)
  const payment = ref<Payment | null>(null)
  const paymentStatus = ref<string>('pending')
  const failureReason = ref<string>('')
  const selectedMethod = ref<string>('alipay')

  // 轮询相关
  let statusCheckTimer: ReturnType<typeof setTimeout> | null = null
  let pollAttempts = 0

  // 计算属性
  const isPaymentCreated = computed(() => payment.value !== null)
  const isPaymentSuccess = computed(() => paymentStatus.value === 'success')
  const isPaymentFailed = computed(() => paymentStatus.value === 'failed')
  const isPaymentPending = computed(() => paymentStatus.value === 'pending')

  /**
   * 获取支付方式名称
   */
  const getMethodName = (method?: string): string => {
    const methodKey = method || selectedMethod.value
    return PAYMENT_METHOD_NAMES[methodKey] || '第三方支付'
  }

  /**
   * 创建支付
   */
  const createPaymentRequest = async (order: Order): Promise<void> => {
    if (!order) {
      ElMessage.error('订单信息不存在')
      return
    }

    loading.value = true
    try {
      // 创建支付
      const result = await createPayment({
        order_id: order.id,
        payment_method: selectedMethod.value,
      })

      payment.value = result
      paymentStatus.value = result.status

      // 开始轮询支付状态
      startStatusCheck(order.id)

      ElMessage.success('支付创建成功')
    } catch (error: any) {
      // P2-16: 改进错误提示
      const errorMessage = error.response?.data?.message || error.message || '创建支付失败'
      const errorDetail = error.response?.data?.detail

      if (errorDetail) {
        // 显示详细错误信息
        ElMessage.error(`${errorMessage}: ${errorDetail}`)
      } else {
        ElMessage.error(errorMessage)
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 查询支付状态
   */
  const checkPaymentStatus = async (orderId: number): Promise<void> => {
    try {
      const status = await getPaymentStatus(orderId)
      paymentStatus.value = status.payment_status || 'pending'

      if (status.paid) {
        // 支付成功
        paymentStatus.value = 'success'
        stopStatusCheck()
        options.onSuccess?.()
      } else if (status.payment_status === 'failed') {
        // 支付失败
        paymentStatus.value = 'failed'
        failureReason.value = '支付失败，请重试'
        stopStatusCheck()
        options.onFailed?.(failureReason.value)
      }
    } catch (error: any) {
      console.error('查询支付状态失败:', error)
      // P2-16: 改进错误提示
      const errorMessage = error.response?.data?.message || error.message
      if (errorMessage) {
        ElMessage.warning(`查询支付状态失败: ${errorMessage}`)
      }
    }
  }

  /**
   * 开始轮询支付状态（指数退避策略）
   */
  const startStatusCheck = (orderId: number): void => {
    pollAttempts = 0

    const scheduleNextCheck = () => {
      if (pollAttempts >= POLL_CONFIG.MAX_ATTEMPTS) {
        console.log('达到最大轮询次数，停止轮询')
        stopStatusCheck()
        return
      }

      // 计算下次轮询间隔：指数退避，但不超过最大间隔
      // 间隔序列: 1s, 2s, 3s, 4s, 5s, 5s, 5s...
      const interval = Math.min(
        POLL_CONFIG.INITIAL_INTERVAL * (pollAttempts + 1),
        POLL_CONFIG.MAX_INTERVAL
      )

      pollAttempts++
      console.log(`第 ${pollAttempts} 次轮询，间隔 ${interval}ms`)

      statusCheckTimer = setTimeout(async () => {
        await checkPaymentStatus(orderId)

        // 如果支付还在进行中，继续下一次轮询
        if (paymentStatus.value === 'pending') {
          scheduleNextCheck()
        }
      }, interval)
    }

    // 立即执行第一次检查
    checkPaymentStatus(orderId).then(() => {
      // 如果第一次检查后还是pending，开始轮询
      if (paymentStatus.value === 'pending') {
        scheduleNextCheck()
      }
    })
  }

  /**
   * 停止轮询
   */
  const stopStatusCheck = (): void => {
    if (statusCheckTimer) {
      clearTimeout(statusCheckTimer)
      statusCheckTimer = null
    }
    pollAttempts = 0
  }

  /**
   * 重置状态
   */
  const reset = (): void => {
    stopStatusCheck()
    payment.value = null
    paymentStatus.value = 'pending'
    failureReason.value = ''
    selectedMethod.value = 'alipay'
    pollAttempts = 0
  }

  /**
   * 重试支付
   */
  const retry = (): void => {
    payment.value = null
    paymentStatus.value = 'pending'
    failureReason.value = ''
  }

  return {
    // 状态
    loading,
    payment,
    paymentStatus,
    failureReason,
    selectedMethod,

    // 计算属性
    isPaymentCreated,
    isPaymentSuccess,
    isPaymentFailed,
    isPaymentPending,

    // 方法
    getMethodName,
    createPaymentRequest,
    checkPaymentStatus,
    startStatusCheck,
    stopStatusCheck,
    reset,
    retry,

    // 常量
    POLL_CONFIG,
  }
}
