<template>
  <div class="statistics-panel">
    <div class="stats-header">
      <h3>生成统计</h3>
      <el-button icon="Refresh" @click="refreshStatistics" :loading="loading">刷新</el-button>
    </div>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else class="stats-content">
      <!-- Key Metrics -->
      <el-row :gutter="20" class="metrics-row">
        <el-col :xs="24" :sm="12" :md="6">
          <div class="metric-card">
            <div class="metric-icon">📄</div>
            <el-statistic title="总生成数" :value="stats.total_generated" />
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="metric-card">
            <div class="metric-icon">✅</div>
            <el-statistic title="成功率" :value="`${stats.success_rate}%`" />
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="metric-card">
            <div class="metric-icon">⏱️</div>
            <el-statistic title="平均耗时" :value="`${stats.avg_time}s`" />
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="metric-card">
            <div class="metric-icon">⭐</div>
            <el-statistic title="平均评分" :value="stats.avg_rating.toFixed(1)" />
          </div>
        </el-col>
      </el-row>

      <!-- Charts -->
      <el-row :gutter="20" class="charts-row">
        <!-- Template Usage -->
        <el-col :xs="24" :md="12">
          <div class="chart-card">
            <h4>模板使用频率</h4>
            <div id="template-usage-chart" class="chart-container"></div>
          </div>
        </el-col>

        <!-- Content Style Distribution -->
        <el-col :xs="24" :md="12">
          <div class="chart-card">
            <h4>文案风格分布</h4>
            <div id="style-distribution-chart" class="chart-container"></div>
          </div>
        </el-col>
      </el-row>

      <!-- Generation Trend -->
      <el-row :gutter="20" class="trend-row">
        <el-col :xs="24">
          <div class="chart-card">
            <h4>生成趋势（最近7天）</h4>
            <div id="generation-trend-chart" class="chart-container" style="height: 300px"></div>
          </div>
        </el-col>
      </el-row>

      <!-- Top Templates -->
      <el-row :gutter="20" class="top-row">
        <el-col :xs="24" :md="12">
          <div class="top-card">
            <h4>热门模板</h4>
            <el-table :data="stats.top_templates" stripe size="small" style="width: 100%">
              <el-table-column prop="name" label="模板名称" />
              <el-table-column prop="count" label="使用次数" width="80" align="center" />
              <el-table-column prop="avg_rating" label="平均评分" width="80" align="center">
                <template #default="{ row }">
                  {{ row.avg_rating.toFixed(1) }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-col>

        <el-col :xs="24" :md="12">
          <div class="top-card">
            <h4>高评分结果</h4>
            <el-table :data="stats.top_results" stripe size="small" style="width: 100%">
              <el-table-column label="内容预览" min-width="120">
                <template #default="{ row }">
                  {{ row.content.substring(0, 30) }}...
                </template>
              </el-table-column>
              <el-table-column prop="rating" label="评分" width="50" align="center">
                <template #default="{ row }">
                  <el-rate :model-value="row.rating" disabled size="small" />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-col>
      </el-row>

      <!-- Daily Stats -->
      <el-row :gutter="20" class="daily-row">
        <el-col :xs="24">
          <div class="top-card">
            <h4>每日统计</h4>
            <el-table :data="stats.daily_stats" stripe size="small" style="width: 100%">
              <el-table-column prop="date" label="日期" width="120" />
              <el-table-column prop="count" label="生成数" width="80" align="center" />
              <el-table-column prop="success" label="成功数" width="80" align="center" />
              <el-table-column prop="avg_rating" label="平均评分" width="100" align="center">
                <template #default="{ row }">
                  {{ row.avg_rating.toFixed(1) }}
                </template>
              </el-table-column>
              <el-table-column prop="total_words" label="总字数" width="80" align="center" />
            </el-table>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

interface Statistics {
  total_generated: number
  success_rate: number
  avg_time: number
  avg_rating: number
  top_templates: Array<{
    name: string
    count: number
    avg_rating: number
  }>
  top_results: Array<{
    content: string
    rating: number
  }>
  daily_stats: Array<{
    date: string
    count: number
    success: number
    avg_rating: number
    total_words: number
  }>
}

const loading = ref(false)
const stats = ref<Statistics>({
  total_generated: 0,
  success_rate: 0,
  avg_time: 0,
  avg_rating: 0,
  top_templates: [],
  top_results: [],
  daily_stats: [],
})

const refreshStatistics = async () => {
  loading.value = true
  try {
    const response = await import('@/api/content-generation').then((mod) =>
      mod.getStatistics()
    )
    stats.value = response.data || response
    renderCharts()
  } catch (err) {
    ElMessage.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
}

const renderCharts = () => {
  // This is a placeholder for chart rendering
  // In a real implementation, you would use ECharts or similar
  console.log('Charts would be rendered here with stats:', stats.value)
}

onMounted(() => {
  refreshStatistics()
})
</script>

<style scoped lang="scss">
.statistics-panel {
  .stats-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid #eee;

    h3 {
      margin: 0;
      font-size: 16px;
    }
  }

  .loading-state {
    padding: 40px;
  }

  .stats-content {
    .metrics-row {
      margin-bottom: 24px;

      .metric-card {
        background: #fff;
        border-radius: 4px;
        padding: 20px;
        text-align: center;
        border: 1px solid #eee;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        align-items: center;

        &:hover {
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          border-color: #1890ff;
        }

        .metric-icon {
          font-size: 24px;
          margin-bottom: 12px;
        }

        :deep(.el-statistic) {
          width: 100%;

          .el-statistic__content {
            font-size: 20px;
          }
        }
      }
    }

    .charts-row {
      margin-bottom: 24px;

      .chart-card {
        background: #fff;
        border-radius: 4px;
        padding: 20px;
        border: 1px solid #eee;

        h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
          font-weight: 600;
        }

        .chart-container {
          height: 300px;
          min-height: 200px;
        }
      }
    }

    .trend-row {
      margin-bottom: 24px;

      .chart-card {
        background: #fff;
        border-radius: 4px;
        padding: 20px;
        border: 1px solid #eee;

        h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
          font-weight: 600;
        }
      }
    }

    .top-row,
    .daily-row {
      margin-bottom: 24px;

      .top-card {
        background: #fff;
        border-radius: 4px;
        padding: 20px;
        border: 1px solid #eee;

        h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
          font-weight: 600;
        }

        :deep(.el-table) {
          font-size: 12px;
        }
      }
    }
  }
}
</style>
