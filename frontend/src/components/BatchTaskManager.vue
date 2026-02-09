<template>
  <div class="batch-tasks">
    <div class="tasks-header">
      <h3>批量任务管理</h3>
      <el-button icon="Refresh" circle @click="refreshTasks" :loading="contentStore.tasksLoading" />
    </div>

    <el-table :data="contentStore.batchTasks" stripe style="width: 100%">
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

      <el-table-column label="创建时间" width="160" :formatter="formatDateTime" />

      <el-table-column label="操作" width="180" fixed="right">
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
            @command="(cmd) => handleExport(row, cmd)"
          >
            <el-button size="small">
              导出
              <el-icon class="is-icon">
                <arrow-down />
              </el-icon>
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
            v-if="row.status === 'running'"
            size="small"
            type="danger"
            @click="handleCancel(row)"
          >
            取消
          </el-button>
          <el-button
            v-if="row.status === 'failed'"
            size="small"
            @click="viewError(row)"
          >
            查看错误
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Results Dialog -->
    <el-dialog v-model="resultsDialogVisible" title="任务结果" width="800px" max-height="600px">
      <div v-if="currentTask" class="results-content">
        <div class="task-info">
          <span><strong>任务：</strong> {{ currentTask.name }}</span>
          <span><strong>模板：</strong> {{ currentTask.template }}</span>
          <span><strong>数量：</strong> {{ currentTask.count }}</span>
          <span><strong>状态：</strong>
            <el-tag :type="getStatusType(currentTask.status)">
              {{ getStatusLabel(currentTask.status) }}
            </el-tag>
          </span>
        </div>

        <div class="results-list">
          <div
            v-for="(result, index) in currentTask.results"
            :key="result.id"
            class="result-item"
          >
            <div class="result-title">#{{ index + 1 }} - {{ result.product_id }}</div>
            <div class="result-text">{{ result.content }}</div>
            <div class="result-footer">
              {{ result.word_count }} 字 | 评分：{{ result.rating || '-' }}
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- Error Dialog -->
    <el-dialog v-model="errorDialogVisible" title="错误信息" width="600px">
      <el-alert
        v-if="currentTask?.error_message"
        :title="currentTask.error_message"
        type="error"
        :closable="false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useContentGenerationStore } from '@/stores/content-generation'
import type { BatchTask } from '@/types/content-generation'
import { ArrowDown } from '@element-plus/icons-vue'

const contentStore = useContentGenerationStore()

const resultsDialogVisible = ref(false)
const errorDialogVisible = ref(false)
const currentTask = ref<BatchTask | null>(null)

const refreshTasks = async () => {
  await contentStore.fetchBatchTasks()
  ElMessage.success('任务列表已刷新')
}

const getStatusType = (status: string): string => {
  const typeMap: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info',
  }
  return typeMap[status] || 'info'
}

const getStatusLabel = (status: string): string => {
  const labelMap: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }
  return labelMap[status] || '未知'
}

const getProgressStatus = (status: string): string => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return ''
}

const formatDateTime = (row: BatchTask): string => {
  const date = new Date(row.created_at)
  return date.toLocaleString('zh-CN')
}

const viewResults = async (task: BatchTask) => {
  currentTask.value = task
  resultsDialogVisible.value = true
}

const viewError = (task: BatchTask) => {
  currentTask.value = task
  errorDialogVisible.value = true
}

const handleCancel = async (task: BatchTask) => {
  ElMessageBox.confirm('确定要取消此任务吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      await contentStore.cancelBatchTask(task.id)
      ElMessage.success('任务已取消')
    })
    .catch(() => {
      ElMessage.info('操作已取消')
    })
}

const handleExport = async (task: BatchTask, format: 'txt' | 'docx' | 'pdf') => {
  try {
    await contentStore.exportResults(format, task.id)
    ElMessage.success('导出成功')
  } catch (err) {
    ElMessage.error('导出失败')
  }
}
</script>

<style scoped lang="scss">
.batch-tasks {
  background: #fff;
  border-radius: 4px;
  padding: 16px;

  .tasks-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #eee;

    h3 {
      margin: 0;
      font-size: 16px;
    }
  }

  :deep(.el-table) {
    font-size: 12px;
  }

  .results-content {
    .task-info {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 12px;
      margin-bottom: 16px;
      padding: 12px;
      background: #f5f5f5;
      border-radius: 4px;
      font-size: 12px;

      span {
        word-break: break-word;
      }
    }

    .results-list {
      max-height: 400px;
      overflow-y: auto;
      border: 1px solid #eee;
      border-radius: 4px;

      .result-item {
        padding: 12px;
        border-bottom: 1px solid #eee;

        &:last-child {
          border-bottom: none;
        }

        .result-title {
          font-weight: 500;
          margin-bottom: 8px;
          color: #333;
          font-size: 12px;
        }

        .result-text {
          font-size: 12px;
          color: #666;
          line-height: 1.6;
          margin-bottom: 8px;
          white-space: pre-wrap;
          word-break: break-word;
        }

        .result-footer {
          font-size: 11px;
          color: #999;
        }
      }
    }
  }
}
</style>
