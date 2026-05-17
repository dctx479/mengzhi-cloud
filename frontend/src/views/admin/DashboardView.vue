<template>
  <div class="dashboard" v-loading="loading">
    <el-row :gutter="20">
      <el-col :span="6" v-for="stat in stats" :key="stat.label">
        <el-card>
          <div class="stat-card">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="chart-card">
      <template #header>AI使用趋势</template>
      <div ref="chartRef" style="height: 300px"></div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { adminApi } from '@/api/admin'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import type { AdminStats, AIUsageData } from '@/types/admin'

const statsData = ref<AdminStats>()
const usageData = ref<AIUsageData[]>([])
const chartRef = ref<HTMLElement>()
const loading = ref(false)
let chartInstance: echarts.ECharts | null = null

const stats = computed(() => [
  { label: '总用户数', value: statsData.value?.totalUsers || 0 },
  { label: '总企业数', value: statsData.value?.totalEnterprises || 0 },
  { label: 'AI调用次数', value: statsData.value?.totalAIUsage || 0 },
  { label: '活跃用户', value: statsData.value?.activeUsers || 0 }
])

const loadData = async () => {
  loading.value = true
  try {
    const [statsRes, usageRes] = await Promise.all([
      adminApi.getStats(),
      adminApi.getAIUsage()
    ])
    statsData.value = statsRes
    usageData.value = Array.isArray(usageRes) ? usageRes : []
    if (usageData.value.length > 0) {
      renderChart()
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载数据失败')
    usageData.value = []
  } finally {
    loading.value = false
  }
}

const renderChart = () => {
  if (!chartRef.value || !Array.isArray(usageData.value) || usageData.value.length === 0) return
  // Dispose existing instance before re-initializing to prevent memory leak
  if (chartInstance) {
    chartInstance.dispose()
  }
  chartInstance = echarts.init(chartRef.value)
  chartInstance.setOption({
    xAxis: { type: 'category', data: usageData.value.map(d => d.date) },
    yAxis: { type: 'value' },
    series: [{ type: 'line', data: usageData.value.map(d => d.count) }]
  })
}

const handleResize = () => chartInstance?.resize()

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  margin-top: 8px;
  color: #909399;
}

.chart-card {
  margin-top: 20px;
}
</style>
