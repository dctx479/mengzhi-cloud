<template>
  <div class="results-panel">
    <!-- Generating Status -->
    <div v-if="contentStore.generating" class="generating-status">
      <el-progress :percentage="contentStore.progress" />
      <div class="status-text">正在生成... {{ contentStore.progress }}%</div>
    </div>

    <!-- Results Display -->
    <div v-else-if="contentStore.hasResults" class="results-list">
      <div class="results-header">
        <h3>生成结果 ({{ contentStore.results.length }})</h3>
        <div class="result-actions">
          <el-button type="primary" icon="Download" @click="handleExportTxt">导出 TXT</el-button>
          <el-button icon="Delete" @click="handleClearAll">清空</el-button>
        </div>
      </div>

      <div v-if="contentStore.generationError" class="error-message">
        <el-alert :title="contentStore.generationError" type="error" :closable="true" />
      </div>

      <div class="result-cards">
        <div
          v-for="(result, index) in contentStore.results"
          :key="result.id"
          class="result-card"
        >
          <div class="result-header">
            <span class="result-number">#{{ index + 1 }}</span>
            <div class="result-rating">
              <el-rate
                v-model="result.rating"
                size="small"
                @change="contentStore.rateResult(result.id, result.rating)"
              />
            </div>
          </div>

          <div class="result-content">
            <el-input
              v-model="result.content"
              type="textarea"
              :rows="6"
              @change="contentStore.updateResult(result.id, result.content)"
            />
          </div>

          <div class="result-meta">
            <span class="word-count">{{ result.word_count }} 字</span>
            <el-tag v-if="result.edited" type="warning" size="small">已编辑</el-tag>
            <span class="create-time">{{ formatTime(result.created_at) }}</span>
          </div>

          <div class="result-actions">
            <el-button size="small" icon="CopyDocument" @click="copyResult(result)">
              复制
            </el-button>
            <el-button size="small" icon="Refresh" @click="handleRegenerate(result)">
              重新生成
            </el-button>
            <el-button size="small" icon="Download" @click="handleExportSingleTxt(result)">
              导出
            </el-button>
            <el-button
              size="small"
              type="danger"
              icon="Delete"
              @click="contentStore.deleteResult(result.id)"
            >
              删除
            </el-button>
          </div>
        </div>
      </div>

      <div class="results-summary">
        <el-statistic title="总字数" :value="contentStore.totalWordCount" />
        <el-statistic title="生成数量" :value="contentStore.results.length" />
        <el-statistic
          title="平均评分"
          :value="(contentStore.results.reduce((sum, r) => sum + r.rating, 0) / contentStore.results.length || 0).toFixed(1)"
        />
      </div>
    </div>

    <!-- Empty State -->
    <el-empty v-else description="选择模板和配置参数后开始生成" />
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { useContentGenerationStore } from '@/stores/content-generation'
import type { GenerationResult } from '@/types/content-generation'

const contentStore = useContentGenerationStore()

const copyResult = (result: GenerationResult) => {
  navigator.clipboard.writeText(result.content).then(() => {
    ElMessage.success('已复制到剪贴板')
  })
}

const handleRegenerate = async (result: GenerationResult) => {
  ElMessageBox.confirm('确定要重新生成此内容吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      await contentStore.regenerateResult(result)
      ElMessage.success('内容已重新生成')
    })
    .catch(() => {})
}

const downloadBlob = (content: string, filename: string) => {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const handleExportTxt = () => {
  const allContent = contentStore.results.map((r, i) => `#${i + 1}\n${r.content}`).join('\n\n---\n\n')
  downloadBlob(allContent, `content-results-${Date.now()}.txt`)
  ElMessage.success('导出成功')
}

const handleExportSingleTxt = (result: GenerationResult) => {
  downloadBlob(result.content, `content-${result.id.substring(0, 8)}.txt`)
  ElMessage.success('导出成功')
}

const handleClearAll = async () => {
  ElMessageBox.confirm('确定要清空所有结果吗？此操作不可撤销。', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      contentStore.clearResults()
      ElMessage.success('已清空所有结果')
    })
    .catch(() => {
      ElMessage.info('操作已取消')
    })
}

const formatTime = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
</script>

<style scoped lang="scss">
.results-panel {
  background: #fff;
  border-radius: 4px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: 100%;

  .generating-status {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px;

    :deep(.el-progress) {
      width: 100%;
      margin-bottom: 16px;
    }

    .status-text {
      font-size: 14px;
      color: #666;
    }
  }

  .results-list {
    display: flex;
    flex-direction: column;
    height: 100%;

    .results-header {
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

      .result-actions {
        display: flex;
        gap: 8px;
      }
    }

    .error-message {
      margin-bottom: 16px;
    }

    .result-cards {
      flex: 1;
      overflow-y: auto;
      display: grid;
      gap: 12px;
      grid-template-columns: 1fr;
    }

    .result-card {
      border: 1px solid #eee;
      border-radius: 4px;
      padding: 12px;
      transition: all 0.3s ease;

      &:hover {
        border-color: #1890ff;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }

      .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;

        .result-number {
          font-weight: 500;
          color: #333;
        }

        .result-rating {
          :deep(.el-rate) {
            --el-rate-icon-size: 16px;
          }
        }
      }

      .result-content {
        margin-bottom: 12px;

        :deep(.el-textarea) {
          font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
        }
      }

      .result-meta {
        display: flex;
        gap: 12px;
        margin-bottom: 12px;
        font-size: 12px;

        .word-count {
          color: #666;
        }

        .create-time {
          color: #999;
        }
      }

      .result-actions {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
    }

    .results-summary {
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid #eee;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
      gap: 16px;

      :deep(.el-statistic) {
        text-align: center;
      }
    }
  }
}
</style>
