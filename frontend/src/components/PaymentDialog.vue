<template>
  <el-dialog
    v-model="visible"
    title="支付订单"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="payment-dialog">
      <!-- 订单信息 -->
      <div class="order-info">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="订单号">{{ order?.order_no }}</el-descriptions-item>
          <el-descriptions-item label="套餐名称">{{ order?.package_name }}</el-descriptions-item>
          <el-descriptions-item label="订单金额">
            <span class="amount">¥{{ order?.amount }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 支付方式选择 -->
      <div v-if="!isPaymentCreated" class="payment-methods">
        <h4>选择支付方式</h4>
        <el-radio-group v-model="selectedMethod" class="method-group">
          <el-radio label="alipay" class="method-item">
            <div class="method-content">
              <el-icon :size="24"><CreditCard /></el-icon>
              <span>支付宝</span>
            </div>
          </el-radio>
          <el-radio label="wechat" class="method-item">
            <div class="method-content">
              <el-icon :size="24"><Wallet /></el-icon>
              <span>微信支付</span>
            </div>
          </el-radio>
          <el-radio label="balance" class="method-item" disabled>
            <div class="method-content">
              <el-icon :size="24"><Coin /></el-icon>
              <span>余额支付（暂未开放）</span>
            </div>
          </el-radio>
        </el-radio-group>
      </div>

      <!-- 支付状态 -->
      <div v-if="isPaymentCreated" class="payment-status">
        <el-result
          v-if="isPaymentSuccess"
          icon="success"
          title="支付成功"
          sub-title="配额已发放，请刷新页面查看"
        >
          <template #extra>
            <el-button type="primary" @click="handleSuccess">确定</el-button>
          </template>
        </el-result>

        <el-result
          v-else-if="isPaymentFailed"
          icon="error"
          title="支付失败"
          :sub-title="failureReason || '支付过程中出现错误'"
        >
          <template #extra>
            <el-button type="primary" @click="handleRetry">重新支付</el-button>
          </template>
        </el-result>

        <div v-else class="payment-waiting">
          <el-icon class="is-loading" :size="48"><Loading /></el-icon>
          <p class="waiting-text">等待支付中...</p>
          <p class="waiting-hint">
            {{ devMode ? '开发模式：支付将自动完成' : '请使用' + getMethodName() + '扫码支付' }}
          </p>
          <div v-if="payment?.qr_code" class="qr-code">
            <img :src="payment.qr_code" alt="支付二维码" />
          </div>
          <el-button type="text" @click="handleCheckStatus">手动刷新状态</el-button>
        </div>
      </div>
    </div>

    <template #footer>
      <div v-if="!isPaymentCreated" class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="loading"
          :disabled="!selectedMethod"
          @click="handlePay"
        >
          立即支付
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { CreditCard, Wallet, Coin, Loading } from '@element-plus/icons-vue'
import type { Order } from '@/types/user'
import { usePayment } from '@/composables/usePayment'

// P2-13: 定义常量
const DIALOG_RESET_DELAY = 300 // 对话框关闭后重置状态的延迟时间（毫秒）

interface Props {
  modelValue: boolean
  order: Order | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

// P2-12: 使用usePayment composable
const {
  loading,
  payment,
  paymentStatus,
  failureReason,
  selectedMethod,
  isPaymentCreated,
  isPaymentSuccess,
  isPaymentFailed,
  isPaymentPending,
  getMethodName,
  createPaymentRequest,
  checkPaymentStatus,
  stopStatusCheck,
  reset,
  retry,
} = usePayment({
  devMode: true,
  onSuccess: () => {
    emit('success')
  },
})

// 开发模式标识
const devMode = true

const handlePay = async () => {
  if (!props.order) return
  await createPaymentRequest(props.order)
}

const handleCheckStatus = async () => {
  if (!props.order) return
  await checkPaymentStatus(props.order.id)
}

const handleSuccess = () => {
  emit('success')
  handleClose()
}

const handleRetry = () => {
  retry()
}

const handleClose = () => {
  stopStatusCheck()
  visible.value = false
  // P2-13: 使用常量替换魔法数字
  setTimeout(() => {
    reset()
  }, DIALOG_RESET_DELAY)
}

// 监听对话框关闭
watch(visible, (newVal) => {
  if (!newVal) {
    stopStatusCheck()
  }
})
</script>

<style scoped lang="scss">
.payment-dialog {
  .order-info {
    margin-bottom: 24px;

    .amount {
      color: #f56c6c;
      font-size: 20px;
      font-weight: bold;
    }
  }

  .payment-methods {
    h4 {
      margin-bottom: 16px;
      font-size: 16px;
      color: #303133;
    }

    .method-group {
      width: 100%;

      .method-item {
        display: block;
        width: 100%;
        margin-bottom: 12px;
        padding: 16px;
        border: 1px solid #dcdfe6;
        border-radius: 4px;
        transition: all 0.3s;

        &:hover {
          border-color: #409eff;
          background-color: #f0f9ff;
        }

        :deep(.el-radio__label) {
          width: 100%;
        }

        .method-content {
          display: flex;
          align-items: center;
          gap: 12px;

          span {
            font-size: 16px;
          }
        }
      }

      :deep(.el-radio.is-checked) {
        .method-item {
          border-color: #409eff;
          background-color: #f0f9ff;
        }
      }
    }
  }

  .payment-status {
    .payment-waiting {
      text-align: center;
      padding: 32px 0;

      .is-loading {
        color: #409eff;
        margin-bottom: 16px;
      }

      .waiting-text {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 8px;
      }

      .waiting-hint {
        color: #909399;
        margin-bottom: 24px;
      }

      .qr-code {
        margin: 24px 0;

        img {
          width: 200px;
          height: 200px;
        }
      }
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
