<template>
  <div class="billing-records">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>计费记录</h2>
      <p class="subtitle">查看详细的计费记录和使用情况</p>
    </div>

    <!-- 筛选条件 -->
    <el-card class="filter-card mb-4" shadow="never">
      <el-form :model="filters" :inline="true" size="default">
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            @change="handleDateRangeChange"
          />
        </el-form-item>

        <el-form-item label="计费模式">
          <el-select
            v-model="filters.billing_mode"
            placeholder="全部"
            clearable
            @change="loadRecords"
          >
            <el-option label="按Token计费" value="token" />
            <el-option label="按消息计费" value="message" />
            <el-option label="按API调用计费" value="api_call" />
            <el-option label="包月套餐" value="monthly" />
            <el-option label="阶梯定价" value="tiered" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="loadRecords">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
          <el-button type="success" @click="exportRecords">导出</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards mb-4">
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon total">💰</div>
            <div class="stat-info">
              <div class="stat-label">总费用</div>
              <div class="stat-value">¥{{ totalAmount.toFixed(2) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon count">📊</div>
            <div class="stat-info">
              <div class="stat-label">记录数</div>
              <div class="stat-value">{{ totalRecords }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon average">📈</div>
            <div class="stat-info">
              <div class="stat-label">平均费用</div>
              <div class="stat-value">
                ¥{{ totalRecords > 0 ? (totalAmount / totalRecords).toFixed(2) : '0.00' }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 计费记录表格 -->
    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="records"
        border
        stripe
        style="width: 100%"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="record-detail">
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="记录UUID">
                  {{ row.record_uuid }}
                </el-descriptions-item>
                <el-descriptions-item label="计费方案ID">
                  {{ row.plan_id || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="资源类型">
                  {{ row.resource_type || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="资源ID">
                  {{ row.resource_id || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="账单ID">
                  {{ row.invoice_id || '未关联' }}
                </el-descriptions-item>
                <el-descriptions-item label="备注">
                  {{ row.notes || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="使用量数据" :span="2">
                  <pre>{{ JSON.stringify(row.usage_data, null, 2) }}</pre>
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="billing_date" label="计费日期" width="120" sortable>
          <template #default="{ row }">
            {{ row.billing_date ? new Date(row.billing_date).toLocaleDateString('zh-CN') : '-' }}
          </template>
        </el-table-column>

        <el-table-column label="计费模式" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="getBillingModeType(row.billing_mode)">
              {{ getBillingModeText(row.billing_mode) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="使用量" width="150">
          <template #default="{ row }">
            <div class="usage-info">
              <span class="quantity">{{ row.quantity }}</span>
              <span class="unit">{{ getUsageUnit(row.billing_mode) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="单价" width="120">
          <template #default="{ row }">
            ¥{{ parseFloat(row.unit_price || 0).toFixed(4) }}
          </template>
        </el-table-column>

        <el-table-column label="金额" width="120" sortable>
          <template #default="{ row }">
            <span class="amount">¥{{ parseFloat(row.amount || 0).toFixed(2) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="currency" label="货币" width="80" />

        <el-table-column label="账单状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.invoice_id" type="success" size="small">已关联</el-tag>
            <el-tag v-else type="info" size="small">未关联</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" fixed="right" width="120">
          <template #default="{ row }">
            <el-button
              v-if="row.invoice_id"
              type="primary"
              link
              size="small"
              @click="viewInvoice()"
            >
              查看账单
            </el-button>
            <span v-else class="text-muted">-</span>
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
          @size-change="loadRecords"
          @current-change="loadRecords"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import http from '@/utils/http'

interface BillingRecordItem {
  id: string
  record_uuid?: string
  plan_id?: string | null
  resource_type?: string | null
  resource_id?: string | null
  invoice_id?: string | null
  notes?: string | null
  usage_data?: Record<string, unknown> | null
  billing_date?: string
  billing_mode: 'token' | 'message' | 'api_call' | 'monthly' | 'tiered'
  quantity: number | string
  unit_price?: number | string
  amount?: number | string
  currency?: string
  created_at?: string
}

interface BillingRecordsResponse {
  records?: BillingRecordItem[]
  pagination?: {
    total?: number
  }
}

interface BillingApiResponse<T> {
  code?: number
  data?: T
  message?: string
}

type BillingMode = BillingRecordItem['billing_mode']
type DateRangeValue = [string, string] | null

const router = useRouter()

const records = ref<BillingRecordItem[]>([])
const dateRange = ref<DateRangeValue>(null)
const filters = reactive<{
  start_date: string | null
  end_date: string | null
  billing_mode: BillingMode | null
}>({
  start_date: null,
  end_date: null,
  billing_mode: null,
})
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})

const loading = ref(false)

const totalAmount = computed(() => {
  return records.value.reduce((sum, record) => sum + Number(record.amount || 0), 0)
})

const totalRecords = computed(() => {
  return pagination.total
})

const billingModeMap: Record<BillingMode, string> = {
  token: 'Token',
  message: '消息',
  api_call: 'API调用',
  monthly: '包月',
  tiered: '阶梯',
}

const billingModeTypeMap: Record<BillingMode, string> = {
  token: 'primary',
  message: 'success',
  api_call: 'warning',
  monthly: 'danger',
  tiered: 'info',
}

const getBillingModeText = (mode: BillingMode) => billingModeMap[mode] || mode
const getBillingModeType = (mode: BillingMode) => billingModeTypeMap[mode] || 'info'

const getUsageUnit = (mode: BillingMode) => {
  const unitMap: Record<BillingMode, string> = {
    token: 'tokens',
    message: '条',
    api_call: '次',
    monthly: '月',
    tiered: '单位',
  }
  return unitMap[mode] || ''
}

const formatDateTime = (dateTime?: string) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

const loadRecords = async () => {
  try {
    loading.value = true

    const params: {
      page: number
      page_size: number
      start_date?: string
      end_date?: string
      billing_mode?: BillingMode
    } = {
      page: pagination.page,
      page_size: pagination.page_size,
    }

    if (filters.start_date) params.start_date = filters.start_date
    if (filters.end_date) params.end_date = filters.end_date
    if (filters.billing_mode) params.billing_mode = filters.billing_mode

    const res = await http.get<BillingApiResponse<BillingRecordsResponse>>('/v1/billing/records', { params }) as BillingApiResponse<BillingRecordsResponse>

    if (res.code === 200) {
      records.value = res.data?.records || []
      pagination.total = res.data?.pagination?.total || 0
    }
  } catch (error) {
    console.error('加载计费记录失败:', error)
    ElMessage.error('加载计费记录失败')
  } finally {
    loading.value = false
  }
}

const handleDateRangeChange = (value: DateRangeValue) => {
  if (Array.isArray(value) && value.length === 2) {
    filters.start_date = value[0]
    filters.end_date = value[1]
  } else {
    filters.start_date = null
    filters.end_date = null
  }
  pagination.page = 1
  loadRecords()
}

const resetFilters = () => {
  dateRange.value = null
  filters.start_date = null
  filters.end_date = null
  filters.billing_mode = null
  pagination.page = 1
  loadRecords()
}

const exportRecords = async () => {
  router.push('/billing/invoices')
}

const viewInvoice = () => {
  router.push('/billing/invoices')
}

onMounted(() => {
  const endDate = new Date()
  const startDate = new Date()
  startDate.setDate(startDate.getDate() - 30)

  const initialRange: [string, string] = [
    startDate.toISOString().split('T')[0],
    endDate.toISOString().split('T')[0],
  ]

  dateRange.value = initialRange
  filters.start_date = initialRange[0]
  filters.end_date = initialRange[1]

  loadRecords()
})
</script>

<style scoped lang="scss">
.billing-records {
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

          &.total {
            background: linear-gradient(135deg, $color-primary-dark 0%, $color-primary 100%);
          }

          &.count {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          }

          &.average {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
          }
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
    }
  }

  .record-detail {
    padding: 16px;
    background: #f5f7fa;

    pre {
      margin: 0;
      padding: 8px;
      background: #fff;
      border-radius: 4px;
      font-size: 12px;
      overflow-x: auto;
    }
  }

  .usage-info {
    display: flex;
    align-items: baseline;
    gap: 4px;

    .quantity {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }

    .unit {
      font-size: 12px;
      color: #909399;
    }
  }

  .amount {
    font-size: 16px;
    font-weight: 600;
    color: #f56c6c;
  }

  .text-muted {
    color: #c0c4cc;
  }

  .pagination-container {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
  }

  .mb-4 {
    margin-bottom: 16px;
  }
}
</style>
