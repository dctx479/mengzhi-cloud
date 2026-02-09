<template>
  <div class="dashboard">
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
import { ref, onMounted, computed } from 'vue'
import { adminApi } from '@/api/admin'
import * as echarts from 'echarts'
import type { AdminStats, AIUsageData } from '@/types/admin'

const statsData = ref<AdminStats>()
const usageData = ref<AIUsageData[]>([])
const chartRef = ref<HTMLElement>()

const stats = computed(() => [
  { label: '总用户数', value: statsData.value?.totalUsers || 0 },
  { label: '总企业数', value: statsData.value?.totalEnterprises || 0 },
  { label: 'AI调用次数', value: statsData.value?.totalAIUsage || 0 },
  { label: '活跃用户', value: statsData.value?.activeUsers || 0 }
])

const loadData = async () => {
  try {
    const [statsRes, usageRes] = await Promise.all([
      adminApi.getStats(),
      adminApi.getAIUsage()
    ])
    statsData.value = statsRes.data
    usageData.value = usageRes.data
    renderChart()
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

const renderChart = () => {
  if (!chartRef.value) return
  const chart = echarts.init(chartRef.value)
  chart.setOption({
    xAxis: { type: 'category', data: usageData.value.map(d => d.date) },
    yAxis: { type: 'value' },
    series: [{ type: 'line', data: usageData.value.map(d => d.count) }]
  })
}

onMounted(loadData)
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
