<template>
  <div class="invoices-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>账单管理</h2>
      <p class="subtitle">查看和管理您的账单</p>
    </div>

    <!-- 筛选条件 -->
    <el-card class="filter-card mb-4" shadow="never">
      <el-form :model="filters" :inline="true" size="default">
        <el-form-item label="账单状态">
          <el-select
            v-model="filters.status"
            placeholder="全部"
            clearable
            @change="loadInvoices"
          >
            <el-option label="待支付" value="pending" />
            <el-option label="已支付" value="paid" />
            <el-option label="已逾期" value="overdue" />
            <el-option label="已取消" value="cancelled" />
            <el-option label="已退款" value="refunded" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="loadInvoices">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards mb-4">
      <el-col :xs="24" :sm="6">
        <el-card shadow="hover" class="stat-card pending">
          <div class="stat-content">
            <div class="stat-icon">⏳</div>
            <div class="stat-info">
              <div class="stat-label">待支付</div>
              <div class="stat-value">{{ statusCounts.pending || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="6">
        <el-card shadow="hover" class="stat-card paid">
          <div class="stat-content">
            <div class="stat-icon">✅</div>
            <div class="stat-info">
              <div class="stat-label">已支付</div>
              <div class="stat-value">{{ statusCounts.paid || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="6">
        <el-card shadow="hover" class="stat-card overdue">
          <div class="stat-content">
            <div class="stat-icon">⚠️</div>
            <div class="stat-info">
              <div class="stat-label">已逾期</div>
              <div class="stat-value">{{ statusCounts.overdue || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="6">
        <el-card shadow="hover" class="stat-card total">
          <div class="stat-content">
            <div class="stat-icon">💰</div>
            <div class="stat-info">
              <div class="stat-label">总金额</div>
              <div class="stat-value">¥{{ totalAmount.toFixed(2) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 账单列表 -->
    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="invoices"
        border
        stripe
        style="width: 100%"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="invoice-detail">
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="账单UUID">
                  {{ row.invoice_uuid }}
                </el-descriptions-item>
                <el-descriptions-item label="账单编号">
                  {{ row.invoice_number }}
                </el-descriptions-item>
                <el-descriptions-item label="账单周期">
                  {{ row.billing_period?.start }} ~ {{ row.billing_period?.end }}
                </el-descriptions-item>
                <el-descriptions-item label="到期日期">
                  {{ row.due_date }}
                </el-descriptions-item>
                <el-descriptions-item label="小计">
                  ¥{{ parseFloat(row.amounts?.subtotal || 0).toFixed(2) }}
                </el-descriptions-item>
                <el-descriptions-item label="折扣">
                  ¥{{ parseFloat(row.amounts?.discount || 0).toFixed(2) }}
                </el-descriptions-item>
                <el-descriptions-item label="税费">
                  ¥{{ parseFloat(row.amounts?.tax || 0).toFixed(2) }}
                </el-descriptions-item>
                <el-descriptions-item label="总金额">
                  <span class="total-amount">
                    ¥{{ parseFloat(row.amounts?.total || 0).toFixed(2) }}
                  </span>
                </el-descriptions-item>
                <el-descriptions-item v-if="row.payment?.method" label="支付方式">
                  {{ getPaymentMethodText(row.payment.method) }}
                </el-descriptions-item>
                <el-descriptions-item v-if="row.payment?.paid_at" label="支付时间">
                  {{ formatDateTime(row.payment.paid_at) }}
                </el-descriptions-item>
                <el-descriptions-item v-if="row.payment?.transaction_id" label="交易ID">
                  {{ row.payment.transaction_id }}
                </el-descriptions-item>
                <el-descriptions-item v-if="row.notes" label="备注" :span="2">
                  {{ row.notes }}
                </el-descriptions-item>
              </el-descriptions>

              <!-- 使用量汇总 -->
              <div v-if="row.usage_summary" class="usage-summary mt-3">
                <h4>使用量汇总</h4>
                <el-row :gutter="20">
                  <el-col :span="8">
                    <div class="summary-item">
                      <span class="label">总Token数:</span>
                      <span class="value">{{ row.usage_summary.total_tokens || 0 }}</span>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="summary-item">
                      <span class="label">总消息数:</span>
                      <span class="value">{{ row.usage_summary.total_messages || 0 }}</span>
                    </div>
                  </el-col>
                  <el-col :span="8">
                    <div class="summary-item">
                      <span class="label">总API调用:</span>
                      <span class="value">{{ row.usage_summary.total_api_calls || 0 }}</span>
                    </div>
                  </el-col>
                </el-row>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="invoice_number" label="账单编号" width="180" />

        <el-table-column label="账单周期" width="200">
          <template #default="{ row }">
            {{ row.billing_period?.start }} ~ {{ row.billing_period?.end }}
          </template>
        </el-table-column>

        <el-table-column label="金额" width="120" sortable>
          <template #default="{ row }">
            <span class="amount">¥{{ parseFloat(row.amounts?.total || 0).toFixed(2) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getInvoiceStatusType(row.status)" size="small">
              {{ getInvoiceStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="到期日期" width="120">
          <template #default="{ row }">
            <span :class="{ 'overdue-date': isOverdue(row) }">
              {{ row.due_date }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" fixed="right" width="200">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              @click="viewInvoiceDetail(row.id)"
            >
              查看详情
            </el-button>
            <el-button
              v-if="row.status === 'pending'"
              type="primary"
              link
              size="small"
              @click="showPayDialog(row)"
            >
              支付
            </el-button>
            <el-button
              type="primary"
              link
              size="small"
              @click="downloadInvoice(row.id)"
            >
              下载
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadInvoices"
          @current-change="loadInvoices"
        />
      </div>
    </el-card>

    <!-- 支付对话框 -->
    <el-dialog
      v-model="showPaymentDialog"
      title="支付账单"
      width="500px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedInvoice" class="payment-dialog">
        <el-descriptions :column="1" border size="small" class="mb-3">
          <el-descriptions-item label="账单编号">
            {{ selectedInvoice.invoice_number }}
          </el-descriptions-item>
          <el-descriptions-item label="应付金额">
            <span class="payment-amount">
              ¥{{ parseFloat(selectedInvoice.amounts?.total || 0).toFixed(2) }}
            </span>
          </el-descriptions-item>
        </el-descriptions>

        <el-form :model="paymentForm" label-width="100px">
          <el-form-item label="支付方式" required>
            <el-radio-group v-model="paymentForm.payment_method">
              <el-radio label="wechat">
                <span class="payment-method">
                  <span class="icon">💚</span>
                  <span>微信支付</span>
                </span>
              </el-radio>
              <el-radio label="alipay">
                <span class="payment-method">
                  <span class="icon">💙</span>
                  <span>支付宝</span>
                </span>
              </el-radio>
              <el-radio label="balance">
                <span class="payment-method">
                  <span class="icon">💰</span>
                  <span>余额支付</span>
                </span>
              </el-radio>
              <el-radio label="bank">
                <span class="payment-method">
                  <span class="icon">🏦</span>
                  <span>银行转账</span>
                </span>
              </el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="交易ID" v-if="paymentForm.payment_method === 'bank'">
            <el-input
              v-model="paymentForm.transaction_id"
              placeholder="请输入银行转账交易ID"
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="showPaymentDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="paymentLoading"
          @click="confirmPayment"
        >
          确认支付
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, h } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import http from '@/utils/http'

const router = useRouter()

// 数据
const invoices = ref([])
const filters = reactive({
  status: null
})
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})
const statusCounts = reactive({
  pending: 0,
  paid: 0,
  overdue: 0,
  cancelled: 0,
  refunded: 0
})

// 支付相关
const showPaymentDialog = ref(false)
const selectedInvoice = ref(null)
const paymentForm = reactive({
  payment_method: 'wechat',
  transaction_id: ''
})
const paymentLoading = ref(false)

// 加载状态
const loading = ref(false)

// 计算属性
const totalAmount = computed(() => {
  return invoices.value.reduce((sum, invoice) => {
    return sum + parseFloat(invoice.amounts?.total || 0)
  }, 0)
})

// 状态映射
const invoiceStatusMap = {
  pending: '待支付',
  paid: '已支付',
  overdue: '已逾期',
  cancelled: '已取消',
  refunded: '已退款'
}

const invoiceStatusTypeMap = {
  pending: 'warning',
  paid: 'success',
  overdue: 'danger',
  cancelled: 'info',
  refunded: 'info'
}

const paymentMethodMap = {
  wechat: '微信支付',
  alipay: '支付宝',
  bank: '银行转账',
  balance: '余额支付',
  other: '其他'
}

// 方法
const getInvoiceStatusText = (status) => invoiceStatusMap[status] || status
const getInvoiceStatusType = (status) => invoiceStatusTypeMap[status] || 'info'
const getPaymentMethodText = (method) => paymentMethodMap[method] || method

const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

const isOverdue = (invoice) => {
  if (invoice.status === 'paid') return false
  return new Date(invoice.due_date) < new Date()
}

// 加载账单列表
const loadInvoices = async () => {
  try {
    loading.value = true

    const params = {
      page: pagination.page,
      page_size: pagination.page_size
    }

    if (filters.status) params.status = filters.status

    const res = await http.get('/v1/billing/invoices', { params })

    if (res.code === 200) {
      invoices.value = res.data?.invoices || []
      pagination.total = res.data?.pagination?.total || 0

      // 更新状态统计
      updateStatusCounts()
    }
  } catch (error) {
    console.error('加载账单失败:', error)
    ElMessage.error('加载账单失败')
  } finally {
    loading.value = false
  }
}

// 更新状态统计（基于当前页数据，仅供参考）
const updateStatusCounts = () => {
  const counts = {
    pending: 0,
    paid: 0,
    overdue: 0,
    cancelled: 0,
    refunded: 0
  }

  invoices.value.forEach(invoice => {
    const status = invoice.status
    if (Object.prototype.hasOwnProperty.call(counts, status)) {
      counts[status]++
    }
  })

  Object.assign(statusCounts, counts)
}

// 重置筛选条件
const resetFilters = () => {
  filters.status = null
  pagination.page = 1
  loadInvoices()
}

// 查看账单详情
const viewInvoiceDetail = async (invoiceId) => {
  try {
    const res = await http.get(`/v1/billing/invoices/${invoiceId}`)

    if (res.code === 200) {
      const invoice = res.data

      // 显示详情对话框
      ElMessageBox.alert(
        h('div', { style: 'max-height: 500px; overflow-y: auto;' }, [
          h('h3', '账单详情'),
          h('p', [h('strong', '账单编号:'), ` ${invoice.invoice_number || '-'}`]),
          h('p', [h('strong', '账单周期:'), ` ${invoice.billing_period?.start || '-'} ~ ${invoice.billing_period?.end || '-'}`]),
          h('p', [h('strong', '总金额:'), ` ¥${parseFloat(invoice.amounts?.total || 0).toFixed(2)}`]),
          h('p', [h('strong', '状态:'), ` ${getInvoiceStatusText(invoice.status)}`]),
          h('h4', `计费记录 (${invoice.records?.length || 0}条)`),
          ...(invoice.records?.map(record =>
            h('div', { style: 'border: 1px solid #eee; padding: 8px; margin: 4px 0; border-radius: 4px;' }, [
              h('p', [h('strong', '日期:'), ` ${record.billing_date || '-'}`]),
              h('p', [h('strong', '模式:'), ` ${getBillingModeText(record.billing_mode)}`]),
              h('p', [h('strong', '数量:'), ` ${record.quantity}`]),
              h('p', [h('strong', '金额:'), ` ¥${record.amount || '0.00'}`]),
            ])
          ) || [h('p', '暂无记录')]),
        ]),
        '账单详情',
        {
          confirmButtonText: '关闭'
        }
      )
    }
  } catch (error) {
    console.error('加载账单详情失败:', error)
    ElMessage.error('加载账单详情失败')
  }
}

// 显示支付对话框
const showPayDialog = (invoice) => {
  selectedInvoice.value = invoice
  paymentForm.payment_method = 'wechat'
  paymentForm.transaction_id = ''
  showPaymentDialog.value = true
}

// 确认支付
const confirmPayment = async () => {
  try {
    if (!paymentForm.payment_method) {
      ElMessage.warning('请选择支付方式')
      return
    }

    if (paymentForm.payment_method === 'bank' && !paymentForm.transaction_id) {
      ElMessage.warning('请输入银行转账交易ID')
      return
    }

    paymentLoading.value = true

    const res = await http.post(
      `/v1/billing/invoices/${selectedInvoice.value.id}/pay`,
      {
        payment_method: paymentForm.payment_method,
        transaction_id: paymentForm.transaction_id || undefined
      }
    )

    if (res.code === 200) {
      ElMessage.success('支付成功')
      showPaymentDialog.value = false
      loadInvoices()
    }
  } catch (error) {
    console.error('支付失败:', error)
    ElMessage.error(error.response?.data?.message || '支付失败')
  } finally {
    paymentLoading.value = false
  }
}

// 下载账单
const downloadInvoice = async (invoiceId) => {
  try {
    const res = await http.get(`/v1/billing/invoices/${invoiceId}/download`, {
      responseType: 'blob'
    })
    // http interceptor returns response.data; for blob responseType that is already the Blob
    const blob = res instanceof Blob ? res : new Blob([res as any], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `invoice-${invoiceId}.pdf`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载账单失败:', error)
    ElMessage.error('下载账单失败')
  }
}

const getBillingModeText = (mode) => {
  const map = {
    token: 'Token',
    message: '消息',
    api_call: 'API调用',
    monthly: '包月',
    tiered: '阶梯'
  }
  return map[mode] || mode
}

// 初始化
onMounted(() => {
  loadInvoices()
})
</script>

<style scoped lang="scss">
.invoices-page {
  padding: 20px;

  .page-header {
    margin-bottom: 24px;

    h2 {
      margin: 0 0 8px 0;
      font-size: 24px;
      font-weight: 600;
      color: #303133;
    }

    .subtitle {
      margin: 0;
      font-size: 14px;
      color: #909399;
    }
  }

  .filter-card {
    :deep(.el-card__body) {
      padding: 16px;
    }
  }

  .stat-cards {
    .stat-card {
      .stat-content {
        display: flex;
        align-items: center;
        gap: 16px;

        .stat-icon {
          font-size: 48px;
          width: 60px;
          height: 60px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 12px;
        }

        .stat-info {
          flex: 1;

          .stat-label {
            font-size: 14px;
            color: #909399;
            margin-bottom: 8px;
          }

          .stat-value {
            font-size: 24px;
            font-weight: 600;
            color: #303133;
          }
        }
      }

      &.pending .stat-icon {
        background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
      }

      &.paid .stat-icon {
        background: linear-gradient(135deg, #55efc4 0%, #00b894 100%);
      }

      &.overdue .stat-icon {
        background: linear-gradient(135deg, #ff7675 0%, #d63031 100%);
      }

      &.total .stat-icon {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      }
    }
  }

  .invoice-detail {
    padding: 16px;
    background: #f5f7fa;

    .total-amount {
      font-size: 18px;
      font-weight: 600;
      color: #f56c6c;
    }

    .usage-summary {
      margin-top: 16px;
      padding: 12px;
      background: #fff;
      border-radius: 4px;

      h4 {
        margin: 0 0 12px 0;
        font-size: 14px;
        font-weight: 600;
        color: #303133;
      }

      .summary-item {
        display: flex;
        justify-content: space-between;
        padding: 8px;
        background: #f5f7fa;
        border-radius: 4px;

        .label {
          font-size: 14px;
          color: #606266;
        }

        .value {
          font-size: 16px;
          font-weight: 600;
          color: #303133;
        }
      }
    }
  }

  .amount {
    font-size: 16px;
    font-weight: 600;
    color: #f56c6c;
  }

  .overdue-date {
    color: #f56c6c;
    font-weight: 600;
  }

  .pagination-container {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
  }

  .payment-dialog {
    .payment-amount {
      font-size: 24px;
      font-weight: 600;
      color: #f56c6c;
    }

    .payment-method {
      display: flex;
      align-items: center;
      gap: 8px;

      .icon {
        font-size: 20px;
      }
    }
  }

  .mb-3 {
    margin-bottom: 12px;
  }

  .mb-4 {
    margin-bottom: 16px;
  }

  .mt-3 {
    margin-top: 12px;
  }
}
</style>
