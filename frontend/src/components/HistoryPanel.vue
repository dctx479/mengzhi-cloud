<template>
  <div class="history-panel">
    <div class="history-header">
      <h3>历史记录</h3>
      <div class="filter-actions">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索历史记录..."
          style="width: 200px"
          clearable
        />
        <el-button icon="Refresh" @click="refreshHistory">刷新</el-button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else-if="filteredHistory.length === 0" class="empty-state">
      <el-empty description="暂无历史记录" />
    </div>

    <div v-else class="history-list">
      <div
        v-for="record in filteredHistory"
        :key="record.id"
        class="history-item"
      >
        <div class="history-header-row">
          <div class="history-title">
            <span class="history-template">{{ record.config.template_id }}</span>
            <el-tag :type="getStatusType(record.status)" size="small">
              {{ getStatusLabel(record.status) }}
            </el-tag>
          </div>
          <div class="history-time">{{ formatDateTime(record.created_at) }}</div>
        </div>

        <div class="history-config">
          <span class="config-item">产品数: {{ record.config.product_ids.length }}</span>
          <span class="config-item">结果数: {{ record.results.length }}</span>
          <span class="config-item">风格: {{ record.config.style }}</span>
          <span class="config-item">字数: {{ record.config.word_count }}</span>
        </div>

        <div class="history-results">
          <div
            v-for="(result, idx) in record.results.slice(0, 2)"
            :key="result.id"
            class="result-preview"
          >
            <span class="result-number">#{{ idx + 1 }}</span>
            <span class="result-text">{{ result.content.substring(0, 100) }}...</span>
          </div>
          <div v-if="record.results.length > 2" class="more-results">
            +{{ record.results.length - 2 }} 更多结果
          </div>
        </div>

        <div class="history-actions">
          <el-button size="small" icon="View" @click="viewHistoryRecord(record)">
            查看详情
          </el-button>
          <el-button size="small" icon="DocumentCopy" @click="restoreFromHistory(record)">
            恢复配置
          </el-button>
        </div>
      </div>
    </div>

    <!-- Detail Dialog -->
    <el-dialog
      v-model="detailDialogVisible"
      title="历史记录详情"
      width="800px"
      max-height="600px"
    >
      <div v-if="selectedRecord" class="record-detail">
        <div class="detail-section">
          <h4>配置信息</h4>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="模板">
              {{ selectedRecord.config.template_id }}
            </el-descriptions-item>
            <el-descriptions-item label="文案风格">
              {{ selectedRecord.config.style }}
            </el-descriptions-item>
            <el-descriptions-item label="字数限制">
              {{ selectedRecord.config.word_count }}
            </el-descriptions-item>
            <el-descriptions-item label="创意温度">
              {{ selectedRecord.config.temperature }}
            </el-descriptions-item>
            <el-descriptions-item label="关键词">
              <div>
                <el-tag
                  v-for="keyword in selectedRecord.config.keywords"
                  :key="keyword"
                  size="small"
                  style="margin-right: 4px"
                >
                  {{ keyword }}
                </el-tag>
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="detail-section">
          <h4>生成结果 ({{ selectedRecord.results.length }})</h4>
          <div class="results-list">
            <div
              v-for="(result, idx) in selectedRecord.results"
              :key="result.id"
              class="result-item"
            >
              <div class="result-title">#{{ idx + 1 }}</div>
              <div class="result-content">{{ result.content }}</div>
              <div class="result-info">
                {{ result.word_count }} 字 | 评分: {{ result.rating || '-' }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useContentGenerationStore } from '@/stores/content-generation'

const contentStore = useContentGenerationStore()

const historyRecords = ref<any[]>([])
const loading = ref(false)
const searchKeyword = ref('')
const detailDialogVisible = ref(false)
const selectedRecord = ref<any>(null)

const filteredHistory = computed(() => {
  if (!searchKeyword.value) return historyRecords.value
  const keyword = searchKeyword.value.toLowerCase()
  return historyRecords.value.filter((record) =>
    record.config.template_id.toLowerCase().includes(keyword) ||
    record.results.some((r: any) => r.content.toLowerCase().includes(keyword))
  )
})

const refreshHistory = async () => {
  loading.value = true
  try {
    const response = await import('@/api/content-generation').then((mod) =>
      mod.getHistory(20, 0)
    )
    historyRecords.value = response.data || []
  } catch (err) {
    ElMessage.error('加载历史记录失败')
  } finally {
    loading.value = false
  }
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

const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

const viewHistoryRecord = (record: any) => {
  selectedRecord.value = record
  detailDialogVisible.value = true
}

const restoreFromHistory = (record: any) => {
  contentStore.updateConfig(record.config)
  ElMessage.success('配置已恢复')
}

onMounted(() => {
  refreshHistory()
})
</script>

<style scoped lang="scss">
.history-panel {
  .history-header {
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

    .filter-actions {
      display: flex;
      gap: 8px;
      align-items: center;
    }
  }

  .loading-state,
  .empty-state {
    padding: 40px;
    text-align: center;
  }

  .history-list {
    display: grid;
    gap: 12px;
    grid-template-columns: 1fr;
    max-height: 600px;
    overflow-y: auto;

    .history-item {
      border: 1px solid #eee;
      border-radius: 4px;
      padding: 12px;
      transition: all 0.3s ease;

      &:hover {
        border-color: #1890ff;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }

      .history-header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;

        .history-title {
          display: flex;
          gap: 8px;
          align-items: center;

          .history-template {
            font-weight: 500;
            color: #333;
          }
        }

        .history-time {
          font-size: 12px;
          color: #999;
        }
      }

      .history-config {
        display: flex;
        gap: 12px;
        margin-bottom: 12px;
        font-size: 12px;
        color: #666;
        flex-wrap: wrap;

        .config-item {
          padding: 4px 8px;
          background: #f5f5f5;
          border-radius: 3px;
        }
      }

      .history-results {
        margin-bottom: 12px;

        .result-preview {
          display: flex;
          gap: 8px;
          font-size: 12px;
          margin-bottom: 6px;
          color: #666;

          .result-number {
            font-weight: 500;
            color: #999;
            min-width: 20px;
          }

          .result-text {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            flex: 1;
          }
        }

        .more-results {
          font-size: 12px;
          color: #1890ff;
          cursor: pointer;

          &:hover {
            text-decoration: underline;
          }
        }
      }

      .history-actions {
        display: flex;
        gap: 8px;
      }
    }
  }

  .record-detail {
    .detail-section {
      margin-bottom: 16px;

      h4 {
        margin: 0 0 12px 0;
        font-size: 14px;
        font-weight: 600;
      }

      .results-list {
        max-height: 300px;
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
            font-size: 12px;
            margin-bottom: 8px;
            color: #333;
          }

          .result-content {
            font-size: 12px;
            color: #666;
            white-space: pre-wrap;
            word-break: break-word;
            margin-bottom: 8px;
            line-height: 1.6;
          }

          .result-info {
            font-size: 11px;
            color: #999;
          }
        }
      }
    }
  }
}
</style>
