<template>
  <div class="audit-stats">
    <el-row :gutter="20">
      <!-- 统计卡片 -->
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon total">
              <el-icon :size="32"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats?.totalLogs || 0 }}</div>
              <div class="stat-label">总日志数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon success">
              <el-icon :size="32"><SuccessFilled /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats ? stats.successRate.toFixed(1) : '0.0' }}%</div>
              <div class="stat-label">成功率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon failure">
              <el-icon :size="32"><CircleCloseFilled /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats ? stats.failureRate.toFixed(1) : '0.0' }}%</div>
              <div class="stat-label">失败率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon users">
              <el-icon :size="32"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats?.topUsers.length || 0 }}</div>
              <div class="stat-label">活跃用户</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 操作类型分布 - 饼图 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>操作类型分布</span>
            </div>
          </template>
          <div ref="actionPieChart" style="height: 300px"></div>
        </el-card>
      </el-col>

      <!-- 资源类型分布 - 饼图 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>资源类型分布</span>
            </div>
          </template>
          <div ref="resourcePieChart" style="height: 300px"></div>
        </el-card>
      </el-col>

      <!-- Top操作人 - 柱状图 -->
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>Top操作人</span>
            </div>
          </template>
          <div ref="topUsersChart" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 操作趋势 - 折线图 -->
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>操作趋势</span>
            </div>
          </template>
          <div ref="trendChart" style="height: 350px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { Document, SuccessFilled, CircleCloseFilled, User } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import type { AuditStats } from '@/types/auditLog'

interface Props {
  stats: AuditStats | null
}

const props = defineProps<Props>()

const actionPieChart = ref<HTMLElement>()
const resourcePieChart = ref<HTMLElement>()
const topUsersChart = ref<HTMLElement>()
const trendChart = ref<HTMLElement>()

let actionPieInstance: echarts.ECharts | null = null
let resourcePieInstance: echarts.ECharts | null = null
let topUsersInstance: echarts.ECharts | null = null
let trendInstance: echarts.ECharts | null = null

// 初始化操作类型分布饼图
const initActionPieChart = () => {
  if (!actionPieChart.value || !props.stats) return

  actionPieInstance = echarts.init(actionPieChart.value)
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: {
        fontSize: 12
      }
    },
    series: [
      {
        name: '操作类型',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: props.stats.actionDistribution.map(item => ({
          value: item.count,
          name: item.action
        }))
      }
    ]
  }
  actionPieInstance.setOption(option)
}

// 初始化资源类型分布饼图
const initResourcePieChart = () => {
  if (!resourcePieChart.value || !props.stats) return

  resourcePieInstance = echarts.init(resourcePieChart.value)
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: {
        fontSize: 12
      }
    },
    series: [
      {
        name: '资源类型',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: props.stats.resourceTypeDistribution.map(item => ({
          value: item.count,
          name: item.resourceType
        }))
      }
    ]
  }
  resourcePieInstance.setOption(option)
}

// 初始化Top操作人柱状图
const initTopUsersChart = () => {
  if (!topUsersChart.value || !props.stats) return

  topUsersInstance = echarts.init(topUsersChart.value)
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      boundaryGap: [0, 0.01]
    },
    yAxis: {
      type: 'category',
      data: props.stats.topUsers.map(item => item.username)
    },
    series: [
      {
        name: '操作次数',
        type: 'bar',
        data: props.stats.topUsers.map(item => item.count),
        itemStyle: {
          borderRadius: [0, 5, 5, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#83bff6' },
            { offset: 0.5, color: '#188df0' },
            { offset: 1, color: '#188df0' }
          ])
        }
      }
    ]
  }
  topUsersInstance.setOption(option)
}

// 初始化操作趋势折线图
const initTrendChart = () => {
  if (!trendChart.value || !props.stats) return

  trendInstance = echarts.init(trendChart.value)
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['总操作', '成功', '失败']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: props.stats.actionTrend.map(item => item.date)
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '总操作',
        type: 'line',
        smooth: true,
        data: props.stats.actionTrend.map(item => item.count),
        itemStyle: {
          color: '#409EFF'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
          ])
        }
      },
      {
        name: '成功',
        type: 'line',
        smooth: true,
        data: props.stats.actionTrend.map(item => item.successCount),
        itemStyle: {
          color: '#67C23A'
        }
      },
      {
        name: '失败',
        type: 'line',
        smooth: true,
        data: props.stats.actionTrend.map(item => item.failureCount),
        itemStyle: {
          color: '#F56C6C'
        }
      }
    ]
  }
  trendInstance.setOption(option)
}

// 初始化所有图表
const initCharts = async () => {
  await nextTick()
  initActionPieChart()
  initResourcePieChart()
  initTopUsersChart()
  initTrendChart()
}

// 监听窗口大小变化
const handleResize = () => {
  actionPieInstance?.resize()
  resourcePieInstance?.resize()
  topUsersInstance?.resize()
  trendInstance?.resize()
}

// 监听stats变化
watch(() => props.stats, (newStats) => {
  if (newStats) {
    initCharts()
  }
}, { deep: true })

onMounted(() => {
  if (props.stats) {
    initCharts()
  }
  window.addEventListener('resize', handleResize)
})

// 清理
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  actionPieInstance?.dispose()
  resourcePieInstance?.dispose()
  topUsersInstance?.dispose()
  trendInstance?.dispose()
})
</script>

<style scoped lang="scss">
.audit-stats {
  width: 100%;
}

.stat-card {
  cursor: pointer;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-icon.total {
  background: linear-gradient(135deg, $color-primary-dark 0%, $color-primary 100%);
}

.stat-icon.success {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
}

.stat-icon.failure {
  background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
}

.stat-icon.users {
  background: linear-gradient(135deg, $color-primary 0%, #3ab585 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.card-header {
  font-weight: 600;
  font-size: 16px;
}
</style>
