<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getTickets,
  createTicket,
  updateTicket,
  type KefuTicket,
  type KefuTicketMessage,
} from '@/api/kefu'

// ============================================================
// State
// ============================================================
const tickets = ref<KefuTicket[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const dialogVisible = ref(false)
const createForm = ref({ title: '', description: '', category: 'inquiry', priority: 'normal' })
const detailTicket = ref<KefuTicket | null>(null)
const showDetail = computed({
  get: () => detailTicket.value !== null,
  set: (val: boolean) => { if (!val) detailTicket.value = null },
})
const filterStatus = ref('')

const statusMap: Record<string, string> = {
  pending: '待处理',
  processing: '处理中',
  resolved: '已解决',
  closed: '已关闭',
  reopened: '已重新打开',
}

const statusTypeMap: Record<string, string> = {
  pending: 'warning',
  processing: 'primary',
  resolved: 'success',
  closed: 'info',
  reopened: 'warning',
}

const categoryMap: Record<string, string> = {
  inquiry: '咨询',
  product: '产品咨询',
  refund: '退款',
  return: '退货',
  exchange: '换货',
  complaint: '投诉',
  quality: '质量反馈',
  delivery: '配送',
  other: '其他',
}

// ============================================================
// Methods
// ============================================================
async function loadTickets() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, page_size: pageSize.value }
    if (filterStatus.value) params.status = filterStatus.value
    const data = await getTickets(params as Parameters<typeof getTickets>[0])
    tickets.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    ElMessage.error('加载工单失败')
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!createForm.value.title.trim() || !createForm.value.description.trim()) {
    ElMessage.warning('请填写标题和描述')
    return
  }
  try {
    await createTicket(createForm.value)
    ElMessage.success('工单创建成功')
    dialogVisible.value = false
    createForm.value = { title: '', description: '', category: 'inquiry', priority: 'normal' }
    await loadTickets()
  } catch {
    ElMessage.error('创建工单失败')
  }
}

async function handleClose(ticket: KefuTicket) {
  try {
    await ElMessageBox.confirm('确定要关闭此工单吗？', '关闭工单', { type: 'warning' })
    await updateTicket(ticket.id, { status: 'closed' })
    ElMessage.success('工单已关闭')
    await loadTickets()
  } catch { /* cancel */ }
}

async function handleResolve(ticket: KefuTicket) {
  try {
    await updateTicket(ticket.id, { status: 'resolved' })
    ElMessage.success('工单已标记为已解决')
    await loadTickets()
  } catch {
    ElMessage.error('操作失败')
  }
}

function openDetail(ticket: KefuTicket) {
  detailTicket.value = ticket
}

// ============================================================
// Lifecycle
// ============================================================
onMounted(loadTickets)
</script>

<template>
  <div class="kefu-ticket-page">
    <div class="page-header">
      <h2>客服工单</h2>
      <div class="header-actions">
        <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 120px" @change="loadTickets">
          <el-option v-for="(label, key) in statusMap" :key="key" :label="label" :value="key" />
        </el-select>
        <el-button type="primary" @click="dialogVisible = true">创建工单</el-button>
      </div>
    </div>

    <!-- 工单列表 -->
    <el-table :data="tickets" v-loading="loading" stripe style="width: 100%">
      <el-table-column label="工单号" width="120">
        <template #default="{ row }">
          <span class="ticket-uuid">#{{ row.ticket_uuid?.slice(0, 8) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
      <el-table-column prop="category" label="类别" width="100">
        <template #default="{ row }">{{ categoryMap[row.category] || row.category }}</template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="80">
        <template #default="{ row }">
          <el-tag size="small" :type="row.priority === 'high' || row.priority === 'urgent' ? 'danger' : 'info'">
            {{ row.priority }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="statusTypeMap[row.status] || 'info'">
            {{ statusMap[row.status] || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="emotion" label="情绪" width="80">
        <template #default="{ row }">{{ row.emotion || '-' }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160">
        <template #default="{ row }">
          {{ row.created_at ? new Date(row.created_at).toLocaleString() : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button size="small" link @click="openDetail(row)">详情</el-button>
          <el-button
            v-if="row.status === 'pending' || row.status === 'processing'"
            size="small" link type="success"
            @click="handleResolve(row)"
          >解决</el-button>
          <el-button
            v-if="row.status !== 'closed' && row.status !== 'resolved'"
            size="small" link type="danger"
            @click="handleClose(row)"
          >关闭</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @change="loadTickets"
      />
    </div>

    <!-- 创建工单对话框 -->
    <el-dialog v-model="dialogVisible" title="创建工单" width="480px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="createForm.title" placeholder="简述您的问题" maxlength="200" />
        </el-form-item>
        <el-form-item label="描述" required>
          <el-input v-model="createForm.description" type="textarea" :rows="4" placeholder="详细描述您的问题" />
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="createForm.category" style="width: 100%">
            <el-option v-for="(label, key) in categoryMap" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="createForm.priority" style="width: 100%">
            <el-option label="低" value="low" />
            <el-option label="普通" value="normal" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 工单详情对话框 -->
    <el-dialog v-model="showDetail" :title="detailTicket?.title" width="560px" @close="detailTicket = null">
      <template #default>
        <div v-if="detailTicket">
          <div class="detail-meta">
            <el-tag :type="statusTypeMap[detailTicket.status] || 'info'">
              {{ statusMap[detailTicket.status] || detailTicket.status }}
            </el-tag>
            <el-tag size="small">{{ categoryMap[detailTicket.category] || detailTicket.category }}</el-tag>
            <el-tag size="small" :type="detailTicket.priority === 'high' || detailTicket.priority === 'urgent' ? 'danger' : 'info'">
              {{ detailTicket.priority }}
            </el-tag>
          </div>
          <el-divider />
          <div class="detail-desc">
            <h4>描述</h4>
            <p>{{ detailTicket.description }}</p>
          </div>
          <div v-if="detailTicket.messages && detailTicket.messages.length > 0" class="detail-messages">
            <h4>消息历史</h4>
            <div v-for="msg in detailTicket.messages" :key="msg.id" class="msg-item" :class="msg.role">
              <span class="msg-role">{{ msg.role === 'user' ? '用户' : '客服' }}</span>
              <span class="msg-content">{{ msg.content }}</span>
              <span class="msg-time">{{ new Date(msg.created_at).toLocaleString() }}</span>
            </div>
          </div>
        </div>
      </template>
      <template #footer>
        <el-button @click="detailTicket = null">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.kefu-ticket-page { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; }
.header-actions { display: flex; gap: 10px; align-items: center; }
.ticket-uuid { font-family: monospace; color: var(--el-text-color-secondary); font-size: 12px; }
.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
.detail-meta { display: flex; gap: 8px; }
.detail-desc h4 { margin: 0 0 8px; }
.detail-messages h4 { margin: 16px 0 8px; }
.msg-item { display: flex; gap: 8px; padding: 8px; border-radius: 6px; margin-bottom: 6px; background: var(--el-fill-color-light); }
.msg-role { font-weight: 600; min-width: 40px; }
.msg-content { flex: 1; }
.msg-time { font-size: 11px; color: var(--el-text-color-secondary); }
</style>