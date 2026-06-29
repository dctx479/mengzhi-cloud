<template>
  <div class="batch-tasks">
    <div class="tasks-header">
      <h3>批量任务管理</h3>
      <div style="display: flex; gap: 12px; align-items: center">
        <el-select v-model="statusFilter" placeholder="筛选状态" style="width: 120px" clearable>
          <el-option label="全部" value="" />
          <el-option label="待处理" value="pending" />
          <el-option label="运行中" value="running" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
        <el-button
          type="success"
          :disabled="selectedTasks.length === 0"
          @click="showBulkExportDialog"
        >
          批量导出 ({{ selectedTasks.length }})
        </el-button>
        <el-button icon="Refresh" circle @click="refreshTasks" :loading="contentStore.tasksLoading" />
      </div>
    </div>

    <el-table
      :data="filteredTasks"
      stripe
      style="width: 100%"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" :selectable="(row: BatchTask) => row.status === 'completed'" />
      <el-table-column type="expand">
        <template #default="{ row }">
          <div style="padding: 12px">
            <h4>生成结果预览（前 5 条）</h4>
            <div v-if="row.results && row.results.length > 0">
              <div v-for="(result, idx) in row.results.slice(0, 5)" :key="result.id" style="margin-bottom: 12px; padding: 8px; background: #f5f5f5; border-radius: 4px">
                <div style="font-weight: bold; margin-bottom: 4px">结果 {{ idx + 1 }}（产品 ID: {{ result.product_id }}）</div>
                <div style="white-space: pre-wrap">{{ result.content }}</div>
              </div>
              <div v-if="row.results.length > 5" style="color: #999; font-size: 12px">
                共 {{ row.results.length }} 条结果，仅显示前 5 条
              </div>
            </div>
            <div v-else style="color: #999">暂无结果</div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="任务名称" min-width="150" />
      <el-table-column prop="template" label="模板" min-width="120" />
      <el-table-column prop="count" label="数量" width="80" align="center" />
      <el-table-column label="进度" min-width="200">
        <template #default="{ row }">
          <div style="display: flex; align-items: center; gap: 8px">
            <el-progress
              :percentage="row.progress"
              :status="getProgressStatus(row.status)"
              style="flex: 1"
            />
            <span style="font-size: 12px; color: #666">{{ row.progress }}%</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="160">
        <template #default="{ row }">
          {{ formatDateTime(row) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'completed'"
            size="small"
            type="primary"
            @click="viewResults(row)"
          >
            查看结果
          </el-button>
          <el-dropdown
            v-if="row.status === 'completed'"
            size="small"
            @command="(cmd: 'txt' | 'docx' | 'pdf') => handleExport(row, cmd)"
          >
            <el-button size="small">
              导出
              <el-icon><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="txt">TXT</el-dropdown-item>
                <el-dropdown-item command="docx">DOCX</el-dropdown-item>
                <el-dropdown-item command="pdf">PDF</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button
            v-if="row.status === 'failed'"
            size="small"
            type="warning"
            @click="handleRetry(row)"
          >
            重试
          </el-button>
          <el-button
            v-if="row.status === 'running'"
            size="small"
            type="danger"
            @click="handleCancel(row)"
          >
            取消
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="bulkExportVisible" title="批量导出" width="400px">
      <el-form>
        <el-form-item label="导出格式">
          <el-radio-group v-model="bulkExportFormat">
            <el-radio label="txt">TXT</el-radio>
            <el-radio label="docx">DOCX</el-radio>
            <el-radio label="pdf">PDF</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bulkExportVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBulkExport">确定导出</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { useContentGenerationStore } from '@/stores/content-generation'
import type { BatchTask } from '@/types/content-generation'

const contentStore = useContentGenerationStore()

const statusFilter = ref('')
const selectedTasks = ref<BatchTask[]>([])
const bulkExportVisible = ref(false)
const bulkExportFormat = ref<'txt' | 'docx' | 'pdf'>('txt')

let pollingTimer: ReturnType<typeof setInterval> | null = null

const filteredTasks = computed(() => {
  if (!statusFilter.value) return contentStore.batchTasks
  return contentStore.batchTasks.filter(t => t.status === statusFilter.value)
})

const hasActiveTask = computed(() => {
  return contentStore.batchTasks.some(t => t.status === 'pending' || t.status === 'running')
})

const refreshTasks = async () => {
  await contentStore.fetchBatchTasks()
}

const handleSelectionChange = (selection: BatchTask[]) => {
  selectedTasks.value = selection
}

const showBulkExportDialog = () => {
  bulkExportVisible.value = true
}

const handleBulkExport = async () => {
  try {
    const taskIds = selectedTasks.value.map(t => t.id)
    await contentStore.bulkExportTasks(taskIds, bulkExportFormat.value)
    ElMessage.success('批量导出成功')
    bulkExportVisible.value = false
  } catch (e: any) {
    ElMessage.error(e?.message || '批量导出失败')
  }
}

const handleRetry = async (task: BatchTask) => {
  try {
    await ElMessageBox.confirm(`确定重试任务"${task.name}"吗？`, '重试确认', {
      confirmButtonText: '重试',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await contentStore.retryBatchTask(task.id)
    ElMessage.success('任务已重新提交')
  } catch {
    // 用户取消
  }
}

const handleCancel = async (task: BatchTask) => {
  try {
    await ElMessageBox.confirm(`确定取消任务"${task.name}"吗？`, '取消确认', {
      confirmButtonText: '取消任务',
      cancelButtonText: '返回',
      type: 'warning',
    })
    await contentStore.cancelBatchTask(task.id)
    ElMessage.success('任务已取消')
  } catch {
    // 用户取消
  }
}

const handleExport = async (task: BatchTask, format: 'txt' | 'docx' | 'pdf') => {
  try {
    await contentStore.exportResults(format, task.id)
    ElMessage.success('导出成功')
  } catch (e: any) {
    ElMessage.error(e?.message || '导出失败')
  }
}

const viewResults = (task: BatchTask) => {
  ElMessageBox.alert(
    `任务 "${task.name}" 共生成 ${task.results?.length || 0} 条内容`,
    '任务结果',
    { confirmButtonText: '关闭' }
  )
}

const getStatusType = (status: string) => {
  const map: Record<string, any> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info',
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    pending: '待处理',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }
  return map[status] || status
}

const getProgressStatus = (status: string) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return undefined
}

const formatDateTime = (row: BatchTask) => {
  if (!row.created_at) return '-'
  return new Date(row.created_at).toLocaleString('zh-CN')
}

const startPolling = () => {
  refreshTasks()
  pollingTimer = setInterval(() => {
    if (hasActiveTask.value) {
      refreshTasks()
    }
  }, 4000)
}

const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

onMounted(() => {
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped lang="scss">
.batch-tasks {
  .tasks-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    h3 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
    }
  }
}
</style>
