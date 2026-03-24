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
            <div class="metric-icon">📅</div>
            <el-statistic title="今日生成" :value="stats.today_generated" />
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="metric-card">
            <div class="metric-icon">🔤</div>
            <el-statistic title="消耗Token" :value="stats.total_tokens" />
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="metric-card">
            <div class="metric-icon">📊</div>
            <el-statistic title="内容类型" :value="stats.type_count" />
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

      <!-- Content Type Distribution -->
      <el-row :gutter="20" class="top-row">
        <el-col :xs="24" :md="12">
          <div class="top-card">
            <h4>按内容类型</h4>
            <el-empty v-if="Object.keys(stats.by_type).length === 0" description="暂无数据" :image-size="60" />
            <el-table v-else :data="typeTableData" stripe size="small" style="width: 100%">
              <el-table-column prop="name" label="类型" />
              <el-table-column prop="count" label="次数" width="80" align="center" />
            </el-table>
          </div>
        </el-col>

        <el-col :xs="24" :md="12">
          <div class="top-card">
            <h4>按平台</h4>
            <el-empty v-if="Object.keys(stats.by_platform).length === 0" description="暂无数据" :image-size="60" />
            <el-table v-else :data="platformTableData" stripe size="small" style="width: 100%">
              <el-table-column prop="name" label="平台" />
              <el-table-column prop="count" label="次数" width="80" align="center" />
            </el-table>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

interface Statistics {
  total_generated: number
  today_generated: number
  total_tokens: number
  type_count: number
  by_type: Record<string, number>
  by_platform: Record<string, number>
  recent_trend: Array<{ date: string; count: number }>
}

const loading = ref(false)
const stats = ref<Statistics>({
  total_generated: 0,
  today_generated: 0,
  total_tokens: 0,
  type_count: 0,
  by_type: {},
  by_platform: {},
  recent_trend: [],
})

const typeTableData = computed(() =>
  Object.entries(stats.value.by_type).map(([name, count]) => ({ name, count }))
)

const platformTableData = computed(() =>
  Object.entries(stats.value.by_platform).map(([name, count]) => ({ name, count }))
)

const refreshStatistics = async () => {
  loading.value = true
  try {
    const response = await import('@/api/content-generation').then((mod) =>
      mod.getStatistics()
    )
    // Backend returns success_response wrapper: {code, data: {...}, message}
    // contentAPI uses separate axios, response.data = HTTP body = {code, data, message}
    const raw = response?.data ?? response
    stats.value = {
      total_generated: raw.total_generations ?? 0,
      today_generated: raw.today_generations ?? 0,
      total_tokens: raw.total_tokens_used ?? 0,
      type_count: Object.keys(raw.by_type ?? {}).length,
      by_type: raw.by_type ?? {},
      by_platform: raw.by_platform ?? {},
      recent_trend: raw.recent_trend ?? [],
    }
  } catch (err) {
    ElMessage.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
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
