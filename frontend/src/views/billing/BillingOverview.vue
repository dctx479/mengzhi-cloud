<template>
  <div class="billing-overview">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>计费概览</h2>
      <p class="subtitle">查看您的计费方案和使用情况</p>
    </div>

    <!-- 当前计费方案 -->
    <el-card class="current-plan-card mb-4" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">当前计费方案</span>
          <el-button type="primary" size="small" @click="showPlansDialog = true">
            更换方案
          </el-button>
        </div>
      </template>

      <div v-if="currentPlan" class="plan-details">
        <div class="plan-info">
          <div class="plan-name">
            <h3>{{ currentPlan.name }}</h3>
            <el-tag v-if="currentPlan.is_default" type="success" size="small">默认方案</el-tag>
          </div>
          <p class="plan-description">{{ currentPlan.description }}</p>
        </div>

        <el-divider />

        <div class="plan-pricing">
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="pricing-item">
                <div class="label">计费模式</div>
                <div class="value">{{ getBillingModeText(currentPlan.billing_mode) }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="pricing-item">
                <div class="label">定价类型</div>
                <div class="value">{{ getPricingTypeText(currentPlan.pricing_type) }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="pricing-item">
                <div class="label">货币单位</div>
                <div class="value">{{ currentPlan.pricing_rules?.currency || 'CNY' }}</div>
              </div>
            </el-col>
          </el-row>
        </div>

        <el-divider />

        <div class="plan-rules">
          <h4>定价规则</h4>
          <div v-if="currentPlan.billing_mode === 'tiered'" class="tiered-pricing">
            <el-table :data="currentPlan.pricing_rules?.tiers || []" border size="small">
              <el-table-column prop="min" label="最小量" width="120" />
              <el-table-column label="最大量" width="120">
                <template #default="{ row }">
                  {{ row.max || '无上限' }}
                </template>
              </el-table-column>
              <el-table-column label="单价">
                <template #default="{ row }">
                  {{ row.unit_price }} {{ currentPlan.pricing_rules?.currency || 'CNY' }}
                </template>
              </el-table-column>
            </el-table>
          </div>
          <div v-else class="simple-pricing">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item v-if="currentPlan.pricing_rules?.unit_price" label="单价">
                {{ currentPlan.pricing_rules.unit_price }} {{ currentPlan.pricing_rules?.currency || 'CNY' }}
              </el-descriptions-item>
              <el-descriptions-item v-if="currentPlan.pricing_rules?.monthly_fee" label="月费">
                {{ currentPlan.pricing_rules.monthly_fee }} {{ currentPlan.pricing_rules?.currency || 'CNY' }}
              </el-descriptions-item>
              <el-descriptions-item v-if="currentPlan.pricing_rules?.included_tokens" label="包含Token">
                {{ currentPlan.pricing_rules.included_tokens }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </div>

      <el-empty v-else description="暂无计费方案" />
    </el-card>

    <!-- 本月费用统计 -->
    <el-card class="statistics-card mb-4" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">本月费用统计</span>
          <el-date-picker
            v-model="selectedMonth"
            type="month"
            placeholder="选择月份"
            size="small"
            @change="loadStatistics"
          />
        </div>
      </template>

      <div v-loading="statisticsLoading" class="statistics-content">
        <el-row :gutter="20" class="stat-cards">
          <el-col :xs="24" :sm="8">
            <div class="stat-card total">
              <div class="stat-icon">💰</div>
              <div class="stat-info">
                <div class="stat-label">总费用</div>
                <div class="stat-value">¥{{ statistics.total_amount?.toFixed(2) || '0.00' }}</div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="8">
            <div class="stat-card records">
              <div class="stat-icon">📊</div>
              <div class="stat-info">
                <div class="stat-label">计费记录</div>
                <div class="stat-value">{{ statistics.total_records || 0 }}</div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="8">
            <div class="stat-card average">
              <div class="stat-icon">📈</div>
              <div class="stat-info">
                <div class="stat-label">日均费用</div>
                <div class="stat-value">
                  ¥{{ (statistics.total_amount / getDaysInMonth())?.toFixed(2) || '0.00' }}
                </div>
              </div>
            </div>
          </el-col>
        </el-row>

        <el-divider />

        <!-- 按计费模式统计 -->
        <div class="by-mode-stats">
          <h4>按计费模式统计</h4>
          <el-table :data="getModeStatsData()" border size="small">
            <el-table-column prop="mode" label="计费模式" width="150">
              <template #default="{ row }">
                {{ getBillingModeText(row.mode) }}
              </template>
            </el-table-column>
            <el-table-column prop="count" label="记录数" width="100" />
            <el-table-column prop="quantity" label="使用量" width="120" />
            <el-table-column label="费用">
              <template #default="{ row }">
                ¥{{ row.amount?.toFixed(2) || '0.00' }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>

    <!-- 最近账单 -->
    <el-card class="recent-invoices-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">最近账单</span>
          <el-button type="text" size="small" @click="$router.push('/billing/invoices')">
            查看全部
          </el-button>
        </div>
      </template>

      <el-table
        v-loading="invoicesLoading"
        :data="recentInvoices"
        border
        size="small"
      >
        <el-table-column prop="invoice_number" label="账单编号" width="180" />
        <el-table-column label="账单周期" width="200">
          <template #default="{ row }">
            {{ row.billing_period?.start }} ~ {{ row.billing_period?.end }}
          </template>
        </el-table-column>
        <el-table-column label="金额" width="120">
          <template #default="{ row }">
            ¥{{ row.amounts?.total?.toFixed(2) || '0.00' }}
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
            {{ row.due_date }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="150">
          <template #default="{ row }">
            <el-button
              type="text"
              size="small"
              @click="viewInvoiceDetail(row.id)"
            >
              查看详情
            </el-button>
            <el-button
              v-if="row.status === 'pending'"
              type="text"
              size="small"
              @click="payInvoice(row.id)"
            >
              支付
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 计费方案选择对话框 -->
    <el-dialog
      v-model="showPlansDialog"
      title="选择计费方案"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-loading="plansLoading" class="plans-list">
        <el-row :gutter="20">
          <el-col
            v-for="plan in availablePlans"
            :key="plan.id"
            :xs="24"
            :sm="12"
            class="mb-3"
          >
            <el-card
              :class="['plan-card', { active: currentPlan?.id === plan.id }]"
              shadow="hover"
            >
              <div class="plan-header">
                <h4>{{ plan.name }}</h4>
                <el-tag v-if="plan.is_default" type="success" size="small">推荐</el-tag>
              </div>
              <p class="plan-desc">{{ plan.description }}</p>
              <div class="plan-price">
                <span class="price-label">{{ getBillingModeText(plan.billing_mode) }}</span>
                <span class="price-value">
                  {{ getPlanPriceText(plan) }}
                </span>
              </div>
              <el-button
                v-if="currentPlan?.id !== plan.id"
                type="primary"
                size="small"
                class="mt-3"
                @click="selectPlan(plan)"
              >
                选择此方案
              </el-button>
              <el-tag v-else type="success" size="small" class="mt-3">当前方案</el-tag>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import http from '@/utils/http'

const router = useRouter()

// 数据
const currentPlan = ref(null)
const availablePlans = ref([])
const statistics = reactive({
  total_amount: 0,
  total_records: 0,
  by_mode: {}
})
const recentInvoices = ref([])
const selectedMonth = ref(new Date())

// 加载状态
const plansLoading = ref(false)
const statisticsLoading = ref(false)
const invoicesLoading = ref(false)

// 对话框
const showPlansDialog = ref(false)

// 计费模式文本映射
const billingModeMap = {
  token: '按Token计费',
  message: '按消息计费',
  api_call: '按API调用计费',
  monthly: '包月套餐',
  tiered: '阶梯定价'
}

// 定价类型文本映射
const pricingTypeMap = {
  fixed: '固定价格',
  unit: '单价',
  tiered: '阶梯价格'
}

// 账单状态文本映射
const invoiceStatusMap = {
  pending: '待支付',
  paid: '已支付',
  overdue: '已逾期',
  cancelled: '已取消',
  refunded: '已退款'
}

// 方法
const getBillingModeText = (mode) => billingModeMap[mode] || mode
const getPricingTypeText = (type) => pricingTypeMap[type] || type
const getInvoiceStatusText = (status) => invoiceStatusMap[status] || status

const getInvoiceStatusType = (status) => {
  const typeMap = {
    pending: 'warning',
    paid: 'success',
    overdue: 'danger',
    cancelled: 'info',
    refunded: 'info'
  }
  return typeMap[status] || 'info'
}

const getPlanPriceText = (plan) => {
  const rules = plan.pricing_rules
  if (!rules) return '-'

  if (rules.monthly_fee) {
    return `¥${rules.monthly_fee}/月`
  } else if (rules.unit_price) {
    return `¥${rules.unit_price}/单位`
  }
  return '阶梯定价'
}

const getDaysInMonth = () => {
  const date = new Date(selectedMonth.value)
  const days = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate()
  return Math.max(days, 1)  // 确保最小值为1，防止除以0
}

const getModeStatsData = () => {
  return Object.entries(statistics.by_mode).map(([mode, data]) => ({
    mode,
    ...data
  }))
}

// 加载当前计费方案
const loadCurrentPlan = async () => {
  try {
    plansLoading.value = true
    const res = await http.get('/v1/billing/plans', {
      params: { is_active: true }
    })

    if (res.code === 200) {
      const plans = res.data
      // 获取默认方案作为当前方案
      currentPlan.value = plans.find(p => p.is_default) || plans[0]
    }
  } catch (error) {
    console.error('加载计费方案失败:', error)
  } finally {
    plansLoading.value = false
  }
}

// 加载可用计费方案
const loadAvailablePlans = async () => {
  try {
    plansLoading.value = true
    const res = await http.get('/v1/billing/plans', {
      params: { is_active: true }
    })

    if (res.code === 200) {
      availablePlans.value = res.data
    }
  } catch (error) {
    console.error('加载计费方案失败:', error)
  } finally {
    plansLoading.value = false
  }
}

// 加载统计数据
const loadStatistics = async () => {
  try {
    statisticsLoading.value = true
    const date = new Date(selectedMonth.value)
    const startDate = new Date(date.getFullYear(), date.getMonth(), 1)
    const endDate = new Date(date.getFullYear(), date.getMonth() + 1, 0)

    const res = await http.get('/v1/billing/records/statistics', {
      params: {
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0]
      }
    })

    if (res.code === 200 && res.data) {
      Object.assign(statistics, res.data)
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  } finally {
    statisticsLoading.value = false
  }
}

// 加载最近账单
const loadRecentInvoices = async () => {
  try {
    invoicesLoading.value = true
    const res = await http.get('/v1/billing/invoices', {
      params: {
        page: 1,
        page_size: 5
      }
    })

    if (res.code === 200 && res.data) {
      recentInvoices.value = res.data.invoices || []
    }
  } catch (error) {
    console.error('加载账单失败:', error)
  } finally {
    invoicesLoading.value = false
  }
}

// 选择计费方案
const selectPlan = async (plan) => {
  try {
    await ElMessageBox.confirm(
      `确定要切换到 "${plan.name}" 方案吗？`,
      '确认切换',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // TODO: 实现切换方案的API
    ElMessage.success('切换方案成功')
    currentPlan.value = plan
    showPlansDialog.value = false
  } catch (error) {
    if (error !== 'cancel') {
      console.error('切换方案失败:', error)
      ElMessage.error('切换方案失败')
    }
  }
}

// 查看账单详情
const viewInvoiceDetail = (invoiceId) => {
  router.push(`/billing/invoices/${invoiceId}`)
}

// 支付账单
const payInvoice = async (invoiceId) => {
  router.push(`/billing/invoices/${invoiceId}/pay`)
}

// 初始化
onMounted(() => {
  loadCurrentPlan()
  loadAvailablePlans()
  loadStatistics()
  loadRecentInvoices()
})
</script>

<style scoped lang="scss">
.billing-overview {
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

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .card-title {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }

  .current-plan-card {
    .plan-details {
      .plan-info {
        .plan-name {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 8px;

          h3 {
            margin: 0;
            font-size: 20px;
            font-weight: 600;
            color: #303133;
          }
        }

        .plan-description {
          margin: 0;
          font-size: 14px;
          color: #606266;
        }
      }

      .plan-pricing {
        .pricing-item {
          text-align: center;

          .label {
            font-size: 14px;
            color: #909399;
            margin-bottom: 8px;
          }

          .value {
            font-size: 18px;
            font-weight: 600;
            color: #303133;
          }
        }
      }

      .plan-rules {
        h4 {
          margin: 0 0 16px 0;
          font-size: 16px;
          font-weight: 600;
          color: #303133;
        }
      }
    }
  }

  .statistics-card {
    .statistics-content {
      .stat-cards {
        .stat-card {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 20px;
          border-radius: 8px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;

          &.total {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          }

          &.records {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          }

          &.average {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
          }

          .stat-icon {
            font-size: 48px;
          }

          .stat-info {
            flex: 1;

            .stat-label {
              font-size: 14px;
              opacity: 0.9;
              margin-bottom: 8px;
            }

            .stat-value {
              font-size: 28px;
              font-weight: 600;
            }
          }
        }
      }

      .by-mode-stats {
        h4 {
          margin: 0 0 16px 0;
          font-size: 16px;
          font-weight: 600;
          color: #303133;
        }
      }
    }
  }

  .plans-list {
    .plan-card {
      height: 100%;
      transition: all 0.3s;

      &:hover {
        transform: translateY(-4px);
      }

      &.active {
        border-color: #409eff;
      }

      .plan-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;

        h4 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
          color: #303133;
        }
      }

      .plan-desc {
        margin: 0 0 16px 0;
        font-size: 14px;
        color: #606266;
        min-height: 40px;
      }

      .plan-price {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px;
        background: #f5f7fa;
        border-radius: 4px;

        .price-label {
          font-size: 14px;
          color: #909399;
        }

        .price-value {
          font-size: 20px;
          font-weight: 600;
          color: #409eff;
        }
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
    width: 100%;
  }
}
</style>
