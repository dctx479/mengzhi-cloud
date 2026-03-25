<template>
  <div class="quota-page">
    <!-- 配额概览卡片 -->
    <div class="quota-overview">
      <el-row :gutter="20" class="quota-cards">
        <!-- AI对话配额 -->
        <el-col :xs="24" :sm="8">
          <el-card class="quota-card" :body-style="{ padding: '20px' }">
            <div class="quota-header">
              <div class="quota-icon chat">💬</div>
              <div class="quota-title">AI对话次数</div>
            </div>
            <div class="quota-content">
              <el-progress
                :percentage="chatQuotaPercent"
                :stroke-width="8"
                :color="getProgressColor(chatQuotaPercent)"
                class="mb-3"
              />
              <div class="quota-stats">
                <div class="stat">
                  <span class="label">已用:</span>
                  <span class="value">{{ quotaData.chat_used }}</span>
                </div>
                <div class="stat">
                  <span class="label">总量:</span>
                  <span class="value">{{ quotaData.chat_total }}</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 内容生成配额 -->
        <el-col :xs="24" :sm="8">
          <el-card class="quota-card" :body-style="{ padding: '20px' }">
            <div class="quota-header">
              <div class="quota-icon content">✍️</div>
              <div class="quota-title">内容生成次数</div>
            </div>
            <div class="quota-content">
              <el-progress
                :percentage="contentQuotaPercent"
                :stroke-width="8"
                :color="getProgressColor(contentQuotaPercent)"
                class="mb-3"
              />
              <div class="quota-stats">
                <div class="stat">
                  <span class="label">已用:</span>
                  <span class="value">{{ quotaData.content_used }}</span>
                </div>
                <div class="stat">
                  <span class="label">总量:</span>
                  <span class="value">{{ quotaData.content_total }}</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 文件存储配额 -->
        <el-col :xs="24" :sm="8">
          <el-card class="quota-card" :body-style="{ padding: '20px' }">
            <div class="quota-header">
              <div class="quota-icon storage">📁</div>
              <div class="quota-title">文件存储</div>
            </div>
            <div class="quota-content">
              <el-progress
                :percentage="storageQuotaPercent"
                :stroke-width="8"
                :color="getProgressColor(storageQuotaPercent)"
                class="mb-3"
              />
              <div class="quota-stats">
                <div class="stat">
                  <span class="label">已用:</span>
                  <span class="value">{{ formatFileSize(quotaData.storage_used) }}</span>
                </div>
                <div class="stat">
                  <span class="label">总量:</span>
                  <span class="value">{{ formatFileSize(quotaData.storage_total) }}</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 配额升级建议 -->
    <el-alert
      v-if="shouldShowUpgradeHint"
      title="提示"
      type="warning"
      description="您的配额使用率较高，建议升级账户以获得更多资源"
      show-icon
      closable
      class="mb-4"
    />

    <!-- 升级按钮 -->
    <div class="upgrade-section">
      <el-button type="primary" size="large" @click="showUpgradeDialog">
        <el-icon><ShoppingCart /></el-icon>
        升级配额
      </el-button>
    </div>

    <!-- 配额历史 -->
    <el-card class="quota-history-card">
      <template #header>
        <div class="card-header">
          <span>配额使用记录</span>
          <el-select v-model="historyFilter" placeholder="筛选类型" size="small" style="width: 120px">
            <el-option label="全部" value=""></el-option>
            <el-option label="对话次数" value="chat"></el-option>
            <el-option label="内容生成" value="content"></el-option>
            <el-option label="文件存储" value="storage"></el-option>
          </el-select>
        </div>
      </template>

      <div v-if="loadingHistory" class="text-center">
        <el-empty description="加载中..."></el-empty>
      </div>

      <div v-else-if="quotaHistory.length === 0" class="text-center">
        <el-empty description="暂无使用记录"></el-empty>
      </div>

      <el-table v-else :data="quotaHistory" style="width: 100%">
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getQuotaTypeTag(row.type)">
              {{ getQuotaTypeText(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="消耗" width="100">
          <template #default="{ row }">
            {{ row.type === 'storage' ? formatFileSize(row.amount) : row.amount }}
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" />
      </el-table>

      <!-- 分页 -->
      <div v-if="historyTotal > 0" class="pagination-container">
        <el-pagination
          v-model:current-page="historyPage"
          v-model:page-size="historyPageSize"
          :total="historyTotal"
          :page-sizes="[5, 10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadQuotaHistory"
          @current-change="loadQuotaHistory"
        />
      </div>
    </el-card>

    <!-- 升级对话框 -->
    <el-dialog
      v-model="upgradeDialogVisible"
      title="升级配额"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="upgrade-dialog-content">
        <el-alert
          title="升级说明"
          description="升级后将获得更多的配额限制，升级包含以下内容："
          type="info"
          show-icon
          class="mb-4"
        />

        <div class="upgrade-plans">
          <el-radio-group v-model="selectedPlan" class="w-full">
            <el-card
              v-for="plan in upgradePlans"
              :key="plan.id"
              class="plan-card"
              :body-style="{ padding: '16px' }"
              @click="selectedPlan = plan.id"
            >
              <div class="plan-content">
                <el-radio :label="plan.id" class="mr-3"></el-radio>
                <div class="plan-info">
                  <div class="plan-name">{{ plan.name }}</div>
                  <div class="plan-desc">{{ plan.description }}</div>
                  <div class="plan-items mt-3">
                    <div v-for="item in plan.items" :key="item" class="plan-item">
                      <el-icon style="color: #67c23a"><Check /></el-icon>
                      {{ item }}
                    </div>
                  </div>
                </div>
                <div class="plan-price">
                  <div class="price">¥{{ plan.price }}</div>
                  <div class="price-desc">{{ plan.billing_cycle }}</div>
                </div>
              </div>
            </el-card>
          </el-radio-group>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="upgradeDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleUpgrade">确认升级</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 支付对话框 -->
    <PaymentDialog
      v-model="paymentDialogVisible"
      :order="orderToPay"
      @success="handlePaymentSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElLoading } from 'element-plus'
import { ShoppingCart, Check } from '@element-plus/icons-vue'
import { getQuota, getQuotaHistory, createOrderFromPackage } from '@/api/user'
import PaymentDialog from '@/components/PaymentDialog.vue'
import type { QuotaData, QuotaHistory, Order } from '@/types/user'

const quotaData = ref<QuotaData>({
  chat_used: 0,
  chat_total: 100,
  content_used: 0,
  content_total: 50,
  storage_used: 0,
  storage_total: 1024 * 1024 * 1024, // 1GB
})

const quotaHistory = ref<QuotaHistory[]>([])
const historyFilter = ref('')
const loadingHistory = ref(false)
const historyPage = ref(1)
const historyPageSize = ref(10)
const historyTotal = ref(0)
const upgradeDialogVisible = ref(false)
const selectedPlan = ref(1)
const paymentDialogVisible = ref(false)
const orderToPay = ref<Order | null>(null)

const upgradePlans = [
  {
    id: 1,
    name: '专业版',
    description: '适合个人开发者',
    price: 99,
    billing_cycle: '每月',
    items: [
      '1000次 AI 对话',
      '500次内容生成',
      '10GB 存储空间',
      '优先技术支持',
    ],
  },
  {
    id: 2,
    name: '商业版',
    description: '适合中小企业',
    price: 299,
    billing_cycle: '每月',
    items: [
      '5000次 AI 对话',
      '2000次内容生成',
      '100GB 存储空间',
      '24小时技术支持',
      'API 调用权限',
    ],
  },
  {
    id: 3,
    name: '企业版',
    description: '定制化解决方案',
    price: 999,
    billing_cycle: '每月',
    items: [
      '无限 AI 对话',
      '无限内容生成',
      '无限存储空间',
      '专属技术支持',
      '完整 API 权限',
      '自定义功能开发',
    ],
  },
]

const chatQuotaPercent = computed(() => {
  if (quotaData.value.chat_total <= 0) return 0
  return Math.round((quotaData.value.chat_used / quotaData.value.chat_total) * 100)
})

const contentQuotaPercent = computed(() => {
  if (quotaData.value.content_total <= 0) return 0
  return Math.round((quotaData.value.content_used / quotaData.value.content_total) * 100)
})

const storageQuotaPercent = computed(() => {
  if (quotaData.value.storage_total <= 0) return 0
  return Math.round((quotaData.value.storage_used / quotaData.value.storage_total) * 100)
})

const shouldShowUpgradeHint = computed(() => {
  return chatQuotaPercent.value > 80 || contentQuotaPercent.value > 80 || storageQuotaPercent.value > 80
})

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const getProgressColor = (percentage: number): string => {
  if (percentage > 80) return '#f56c6c'
  if (percentage > 50) return '#e6a23c'
  return '#67c23a'
}

const getQuotaTypeText = (type: string): string => {
  const typeMap: Record<string, string> = {
    chat: 'AI对话',
    content: '内容生成',
    storage: '文件存储',
  }
  return typeMap[type] || type
}

const getQuotaTypeTag = (type: string): string => {
  const tagMap: Record<string, string> = {
    chat: 'primary',
    content: 'success',
    storage: 'warning',
  }
  return tagMap[type] || 'info'
}

const formatDateTime = (dateStr: string): string => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadQuota = async () => {
  try {
    const data = await getQuota()
    if (data && typeof data === 'object' && data.chat_total !== undefined) {
      quotaData.value = data
    } else {
      ElMessage.warning('配额数据无效')
      // 保持默认值
    }
  } catch (error) {
    ElMessage.error('加载配额信息失败')
    console.error(error)
  }
}

const loadQuotaHistory = async () => {
  try {
    loadingHistory.value = true
    const params: any = {
      page: historyPage.value,
      page_size: historyPageSize.value,
    }
    if (historyFilter.value) {
      params.type = historyFilter.value
    }
    const response = await getQuotaHistory(params)
    quotaHistory.value = response.items
    historyTotal.value = response.total
  } catch (error) {
    ElMessage.error('加载历史记录失败')
    console.error(error)
  } finally {
    loadingHistory.value = false
  }
}

const showUpgradeDialog = () => {
  upgradeDialogVisible.value = true
}

const handleUpgrade = async () => {
  try {
    const loading = ElLoading.service({
      lock: true,
      text: '创建订单中...',
      background: 'rgba(0, 0,0, 0.7)',
    })

    // 创建订单
    const order = await createOrderFromPackage(selectedPlan.value)

    loading.close()

    // 关闭升级对话框
    upgradeDialogVisible.value = false

    // 打开支付对话框
    orderToPay.value = order
    paymentDialogVisible.value = true

    ElMessage.success('订单创建成功，请完成支付')
  } catch (error: any) {
    ElMessage.error(error.message || '创建订单失败，请重试')
    console.error(error)
  }
}

const handlePaymentSuccess = async () => {
  ElMessage.success('支付成功，配额已更新')
  await loadQuota()
}

onMounted(() => {
  loadQuota()
  loadQuotaHistory()
})
</script>

<style scoped lang="scss">
.quota-page {
  max-width: 1200px;

  .quota-overview {
    margin-bottom: 24px;

    .quota-cards {
      .quota-card {
        border: 1px solid #ebeef5;
        transition: all 0.3s ease;

        &:hover {
          box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
        }

        .quota-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 16px;

          .quota-icon {
            font-size: 32px;
            line-height: 1;

            &.chat {
              color: #409eff;
            }

            &.content {
              color: #67c23a;
            }

            &.storage {
              color: #e6a23c;
            }
          }

          .quota-title {
            font-size: 14px;
            font-weight: 500;
            color: #333;
          }
        }

        .quota-content {
          .quota-stats {
            display: flex;
            justify-content: space-around;

            .stat {
              display: flex;
              flex-direction: column;
              align-items: center;

              .label {
                font-size: 12px;
                color: #909399;
                margin-bottom: 4px;
              }

              .value {
                font-size: 18px;
                font-weight: 600;
                color: #333;
              }
            }
          }
        }
      }
    }
  }

  .upgrade-section {
    text-align: center;
    margin: 24px 0;
  }

  .quota-history-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;
    }

    .text-center {
      padding: 40px 20px;
      text-align: center;
    }

    .pagination-container {
      display: flex;
      justify-content: center;
      padding: 20px 0;
    }
  }

  .upgrade-dialog-content {
    .upgrade-plans {
      display: flex;
      flex-direction: column;
      gap: 12px;

      .plan-card {
        cursor: pointer;
        border: 2px solid #f0f0f0;
        transition: all 0.3s ease;

        &:hover {
          border-color: #409eff;
        }

        .plan-content {
          display: flex;
          align-items: center;
          gap: 16px;

          .plan-info {
            flex: 1;

            .plan-name {
              font-size: 16px;
              font-weight: 600;
              color: #333;
              margin-bottom: 4px;
            }

            .plan-desc {
              font-size: 12px;
              color: #909399;
              margin-bottom: 8px;
            }

            .plan-items {
              display: flex;
              flex-direction: column;
              gap: 6px;

              .plan-item {
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 12px;
                color: #606266;
              }
            }
          }

          .plan-price {
            text-align: right;
            min-width: 80px;

            .price {
              font-size: 24px;
              font-weight: 600;
              color: #f56c6c;
            }

            .price-desc {
              font-size: 12px;
              color: #909399;
            }
          }
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
  }

  .w-full {
    width: 100%;
  }

  .mr-3 {
    margin-right: 12px;
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
  }
}

@media (max-width: 768px) {
  .quota-page {
    .upgrade-dialog-content {
      .upgrade-plans {
        .plan-card {
          .plan-content {
            flex-direction: column;
            align-items: flex-start;

            .plan-price {
              width: 100%;
              text-align: left;
            }
          }
        }
      }
    }
  }
}
</style>
