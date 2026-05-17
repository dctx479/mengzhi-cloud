<template>
  <div class="orders-page">
    <el-card class="page-header">
      <template #header>
        <div class="card-header">
          <span>订单历史</span>
        </div>
      </template>

      <!-- 筛选器 -->
      <div class="filters">
        <el-row :gutter="16">
          <el-col :xs="24" :sm="6">
            <el-select v-model="filterStatus" placeholder="订单状态" clearable class="w-full">
              <el-option label="全部" value=""></el-option>
              <el-option label="待支付" value="pending"></el-option>
              <el-option label="已完成" value="completed"></el-option>
              <el-option label="已发货" value="shipped"></el-option>
              <el-option label="已取消" value="cancelled"></el-option>
            </el-select>
          </el-col>

          <el-col :xs="24" :sm="12">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              class="w-full"
            />
          </el-col>

          <el-col :xs="24" :sm="6">
            <el-button type="primary" @click="loadOrders" class="w-full">
              <el-icon><Search /></el-icon>
              查询
            </el-button>
          </el-col>
        </el-row>

        <el-row :gutter="16" class="mt-3">
          <el-col :xs="24">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索订单号或产品名"
              clearable
              @change="loadOrders"
              class="w-full"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 订单列表 -->
    <div v-if="loading" class="text-center">
      <el-empty description="加载中..."></el-empty>
    </div>

    <div v-else-if="orders.length === 0" class="text-center">
      <el-empty description="暂无订单"></el-empty>
    </div>

    <div v-else class="order-list">
      <el-card
        v-for="order in orders"
        :key="order.id"
        class="order-card"
        :body-style="{ padding: '20px' }"
      >
        <div class="order-header">
          <div class="order-info-left">
            <span class="order-no">订单号: {{ order.order_no }}</span>
            <el-divider direction="vertical"></el-divider>
            <span class="order-date">{{ formatDate(order.created_at) }}</span>
          </div>
          <el-tag :type="getStatusType(order.status)" class="order-status">
            {{ getStatusText(order.status) }}
          </el-tag>
        </div>

        <!-- 订单商品 -->
        <div class="order-items">
          <div v-for="item in order.items" :key="item.id" class="order-item">
            <img
              :src="item.product?.image || 'https://via.placeholder.com/80'"
              alt=""
              class="item-image"
            />
            <div class="item-info">
              <div class="item-name">{{ item.product?.name || '未知商品' }}</div>
              <div class="item-spec">
                {{ item.quantity }} × ¥{{ (item.price || 0).toFixed(2) }}
              </div>
            </div>
            <div class="item-subtotal">
              ¥{{ ((item.subtotal || item.quantity * item.price) || 0).toFixed(2) }}
            </div>
          </div>
        </div>

        <!-- 订单总计 -->
        <div class="order-footer">
          <div class="order-total">
            <span class="label">合计:</span>
            <span class="amount">¥{{ (order.total_amount || 0).toFixed(2) }}</span>
          </div>

          <div class="order-actions">
            <el-button
              link
              @click="viewDetail(order)"
              type="primary"
              :icon="View"
              class="action-btn"
            >
              查看详情
            </el-button>
            <el-button
              v-if="order.status === 'pending'"
              link
              type="primary"
              class="action-btn"
              @click="handlePayment(order)"
              :icon="CreditCard"
            >
              立即支付
            </el-button>
            <el-button
              v-if="order.status !== 'completed' && order.status !== 'cancelled' && order.status !== 'shipped'"
              link
              type="danger"
              class="action-btn"
              @click="handleCancel(order)"
              :icon="Delete"
            >
              取消订单
            </el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 分页 -->
    <div v-if="total > 0" class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[5, 10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 订单详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="订单详情"
      width="600px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedOrder" class="order-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="订单号">
            {{ selectedOrder.order_no }}
          </el-descriptions-item>
          <el-descriptions-item label="订单状态">
            <el-tag :type="getStatusType(selectedOrder.status)">
              {{ getStatusText(selectedOrder.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDateTime(selectedOrder.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDateTime(selectedOrder.updated_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="订单金额">
            <span class="font-bold text-primary">
              ¥{{ (selectedOrder.total_amount || 0).toFixed(2) }}
            </span>
          </el-descriptions-item>
        </el-descriptions>

        <div class="detail-items mt-4">
          <h4 class="mb-3">订单商品</h4>
          <el-table :data="selectedOrder.items" style="width: 100%">
            <el-table-column prop="product.name" label="产品名称" width="150" />
            <el-table-column prop="quantity" label="数量" width="80" />
            <el-table-column prop="price" label="单价" width="100">
              <template #default="{ row }">
                ¥{{ (row.price || 0).toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="subtotal" label="小计" width="100">
              <template #default="{ row }">
                ¥{{ ((row.subtotal || row.quantity * row.price) || 0).toFixed(2) }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="detailDialogVisible = false">关闭</el-button>
          <el-button
            v-if="selectedOrder?.status === 'pending'"
            type="primary"
            @click="handlePayment(selectedOrder!)"
          >
            立即支付
          </el-button>
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
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, View, CreditCard, Delete } from '@element-plus/icons-vue'
import { getOrders, cancelOrder } from '@/api/user'
import PaymentDialog from '@/components/PaymentDialog.vue'
import type { Order } from '@/types/user'

const orders = ref<Order[]>([])
const filterStatus = ref('')
const dateRange = ref<[Date, Date] | null>(null)
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const loading = ref(false)
const detailDialogVisible = ref(false)
const selectedOrder = ref<Order | null>(null)
const paymentDialogVisible = ref(false)
const orderToPay = ref<Order | null>(null)

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const getStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    pending: '待支付',
    completed: '已完成',
    shipped: '已发货',
    cancelled: '已取消',
  }
  return statusMap[status] || '未知'
}

const getStatusType = (status: string): string => {
  const typeMap: Record<string, string> = {
    pending: 'warning',
    completed: 'success',
    shipped: 'info',
    cancelled: 'danger',
  }
  return typeMap[status] || 'info'
}

const loadOrders = async () => {
  try {
    loading.value = true
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value,
    }

    if (filterStatus.value) {
      params.status = filterStatus.value
    }

    if (dateRange.value) {
      params.start_date = dateRange.value[0].toISOString().split('T')[0]
      params.end_date = dateRange.value[1].toISOString().split('T')[0]
    }

    if (searchKeyword.value) {
      params.keyword = searchKeyword.value
    }

    const response = await getOrders(params)
    orders.value = response.items
    total.value = response.total
  } catch (error) {
    ElMessage.error('加载订单失败，请重试')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleSizeChange = () => {
  currentPage.value = 1
  loadOrders()
}

const handlePageChange = () => {
  loadOrders()
}

const viewDetail = (order: Order) => {
  selectedOrder.value = order
  detailDialogVisible.value = true
}

const handlePayment = async (order: Order) => {
  orderToPay.value = order
  paymentDialogVisible.value = true
}

const handlePaymentSuccess = async () => {
  ElMessage.success('支付成功')
  await loadOrders()
}

const handleCancel = async (order: Order) => {
  try {
    await ElMessageBox.confirm(
      '确定要取消这个订单吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await cancelOrder(String(order.id))
    ElMessage.success('订单已取消')
    await loadOrders()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('取消订单失败，请重试')
    }
  }
}

onMounted(() => {
  loadOrders()
})
</script>

<style scoped lang="scss">
.orders-page {
  max-width: 1200px;

  .page-header {
    margin-bottom: 24px;

    .card-header {
      font-size: 18px;
      font-weight: 600;
    }
  }

  .filters {
    display: flex;
    flex-direction: column;
    gap: 12px;

    .mt-3 {
      margin-top: 12px;
    }

    .w-full {
      width: 100%;
    }
  }

  .order-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-bottom: 24px;

    .order-card {
      border: 1px solid #ebeef5;
      transition: all 0.3s ease;

      &:hover {
        box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
      }

      .order-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        padding-bottom: 16px;
        border-bottom: 1px solid #f0f0f0;

        .order-info-left {
          display: flex;
          align-items: center;
          gap: 8px;

          .order-no {
            font-weight: 600;
            color: #333;
          }

          .order-date {
            color: #909399;
            font-size: 14px;
          }
        }

        .order-status {
          margin-left: 16px;
        }
      }

      .order-items {
        margin-bottom: 16px;

        .order-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 0;
          border-bottom: 1px solid #f5f7fa;

          &:last-child {
            border-bottom: none;
          }

          .item-image {
            width: 80px;
            height: 80px;
            border-radius: 4px;
            object-fit: cover;
          }

          .item-info {
            flex: 1;

            .item-name {
              font-weight: 500;
              color: #333;
              margin-bottom: 4px;
            }

            .item-spec {
              font-size: 14px;
              color: #909399;
            }
          }

          .item-subtotal {
            font-weight: 600;
            color: #f56c6c;
            min-width: 80px;
            text-align: right;
          }
        }
      }

      .order-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-top: 16px;
        border-top: 1px solid #f0f0f0;

        .order-total {
          display: flex;
          align-items: center;
          gap: 8px;

          .label {
            font-size: 14px;
            color: #909399;
          }

          .amount {
            font-size: 18px;
            font-weight: 600;
            color: #f56c6c;
          }
        }

        .order-actions {
          display: flex;
          gap: 8px;

          .action-btn {
            font-size: 14px;
          }
        }
      }
    }
  }

  .pagination-container {
    display: flex;
    justify-content: center;
    padding: 20px 0;
  }

  .order-detail {
    .detail-items {
      margin-top: 16px;

      h4 {
        font-size: 14px;
        font-weight: 600;
        color: #333;
      }
    }
  }

  .text-center {
    padding: 40px 20px;
    text-align: center;
  }

  .font-bold {
    font-weight: 600;
  }

  .text-primary {
    color: #409eff;
  }

  .mt-4 {
    margin-top: 16px;
  }

  .mb-3 {
    margin-bottom: 12px;
  }
}

@media (max-width: 768px) {
  .orders-page {
    .order-list {
      .order-card {
        .order-header {
          flex-direction: column;
          align-items: flex-start;

          .order-status {
            margin-left: 0;
            margin-top: 8px;
          }
        }

        .order-footer {
          flex-direction: column;
          align-items: flex-start;
          gap: 12px;

          .order-total {
            width: 100%;
          }

          .order-actions {
            width: 100%;
            flex-wrap: wrap;
          }
        }
      }
    }
  }
}
</style>
