<template>
  <div class="sla-dashboard">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>SLA保障系统</h1>
      <p class="subtitle">实时监控服务质量，确保系统稳定运行</p>
    </div>

    <!-- 概览卡片 -->
    <div class="overview-cards">
      <div class="card overview-card">
        <div class="card-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
          <i class="el-icon-document"></i>
        </div>
        <div class="card-content">
          <div class="card-value">{{ overview.total_agreements }}</div>
          <div class="card-label">SLA协议总数</div>
        </div>
      </div>

      <div class="card overview-card">
        <div class="card-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%)">
          <i class="el-icon-success"></i>
        </div>
        <div class="card-content">
          <div class="card-value">{{ overview.compliant_agreements }}</div>
          <div class="card-label">达标协议数</div>
        </div>
      </div>

      <div class="card overview-card">
        <div class="card-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)">
          <i class="el-icon-data-line"></i>
        </div>
        <div class="card-content">
          <div class="card-value">{{ overview.compliance_rate }}%</div>
          <div class="card-label">达标率</div>
        </div>
      </div>

      <div class="card overview-card">
        <div class="card-icon" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%)">
          <i class="el-icon-warning"></i>
        </div>
        <div class="card-content">
          <div class="card-value">{{ overview.violation_count }}</div>
          <div class="card-label">违约事件数</div>
        </div>
      </div>
    </div>

    <!-- SLA协议列表 -->
    <div class="card agreements-section">
      <div class="card-header">
        <h2>SLA协议列表</h2>
        <el-button type="primary" @click="showCreateDialog = true">
          <i class="el-icon-plus"></i> 创建协议
        </el-button>
      </div>

      <el-table :data="agreements" style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="协议名称" min-width="150" />
        <el-table-column prop="level" label="等级" width="100">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.level)">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="可用性目标" width="120">
          <template #default="{ row }">{{ row.availability_target }}%</template>
        </el-table-column>
        <el-table-column label="响应时间目标" width="140">
          <template #default="{ row }">{{ row.response_time_target }}ms</template>
        </el-table-column>
        <el-table-column label="错误率目标" width="120">
          <template #default="{ row }">{{ row.error_rate_target }}%</template>
        </el-table-column>
        <el-table-column prop="start_date" label="开始日期" width="120" />
        <el-table-column prop="end_date" label="结束日期" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '激活' : '未激活' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="text" @click="viewMetrics(row)">查看指标</el-button>
            <el-button type="text" @click="viewReport(row)">查看报告</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 实时指标 -->
    <div class="card metrics-section" v-if="selectedAgreement">
      <div class="card-header">
        <h2>实时指标 - {{ selectedAgreement.name }}</h2>
        <el-button @click="refreshMetrics">
          <i class="el-icon-refresh"></i> 刷新
        </el-button>
      </div>

      <div class="metrics-grid">
        <!-- 可用性 -->
        <div class="metric-card">
          <div class="metric-header">
            <h3>可用性</h3>
            <el-tag :type="metrics.availability?.is_compliant ? 'success' : 'danger'">
              {{ metrics.availability?.is_compliant ? '达标' : '未达标' }}
            </el-tag>
          </div>
          <div class="metric-value">
            {{ metrics.availability?.actual || 0 }}%
          </div>
          <div class="metric-target">
            目标: {{ selectedAgreement.availability_target }}%
          </div>
          <div class="metric-stats">
            <span>总请求: {{ metrics.availability?.total_requests || 0 }}</span>
            <span>成功: {{ metrics.availability?.successful_requests || 0 }}</span>
          </div>
        </div>

        <!-- 响应时间 -->
        <div class="metric-card">
          <div class="metric-header">
            <h3>响应时间</h3>
            <el-tag :type="metrics.response_time?.is_compliant ? 'success' : 'danger'">
              {{ metrics.response_time?.is_compliant ? '达标' : '未达标' }}
            </el-tag>
          </div>
          <div class="metric-value">
            {{ metrics.response_time?.avg || 0 }}ms
          </div>
          <div class="metric-target">
            目标: {{ selectedAgreement.response_time_target }}ms
          </div>
          <div class="metric-stats">
            <span>P50: {{ metrics.response_time?.p50 || 0 }}ms</span>
            <span>P95: {{ metrics.response_time?.p95 || 0 }}ms</span>
            <span>P99: {{ metrics.response_time?.p99 || 0 }}ms</span>
          </div>
        </div>

        <!-- 错误率 -->
        <div class="metric-card">
          <div class="metric-header">
            <h3>错误率</h3>
            <el-tag :type="metrics.error_rate?.is_compliant ? 'success' : 'danger'">
              {{ metrics.error_rate?.is_compliant ? '达标' : '未达标' }}
            </el-tag>
          </div>
          <div class="metric-value">
            {{ metrics.error_rate?.actual || 0 }}%
          </div>
          <div class="metric-target">
            目标: {{ selectedAgreement.error_rate_target }}%
          </div>
          <div class="metric-stats">
            <span>失败请求: {{ metrics.error_rate?.failed_requests || 0 }}</span>
          </div>
        </div>

        <!-- 吞吐量 -->
        <div class="metric-card">
          <div class="metric-header">
            <h3>吞吐量</h3>
            <el-tag :type="metrics.throughput?.is_compliant ? 'success' : 'danger'">
              {{ metrics.throughput?.is_compliant ? '达标' : '未达标' }}
            </el-tag>
          </div>
          <div class="metric-value">
            {{ metrics.throughput?.actual || 0 }} req/s
          </div>
          <div class="metric-target">
            目标: {{ selectedAgreement.throughput_target }} req/s
          </div>
          <div class="metric-stats">
            <span>总请求: {{ metrics.throughput?.total_requests || 0 }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 违约事件 -->
    <div class="card violations-section" v-if="selectedAgreement">
      <div class="card-header">
        <h2>违约事件</h2>
        <el-select v-model="violationFilter" placeholder="筛选严重程度" style="width: 150px">
          <el-option label="全部" value="" />
          <el-option label="低" value="LOW" />
          <el-option label="中" value="MEDIUM" />
          <el-option label="高" value="HIGH" />
          <el-option label="严重" value="CRITICAL" />
        </el-select>
      </div>

      <el-table :data="filteredViolations" style="width: 100%">
        <el-table-column prop="metric_type" label="指标类型" width="120" />
        <el-table-column label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="目标值" width="100">
          <template #default="{ row }">{{ row.target_value }}</template>
        </el-table-column>
        <el-table-column label="实际值" width="100">
          <template #default="{ row }">{{ row.actual_value }}</template>
        </el-table-column>
        <el-table-column label="偏差率" width="100">
          <template #default="{ row }">{{ row.deviation_rate }}%</template>
        </el-table-column>
        <el-table-column prop="violation_time" label="违约时间" width="180" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_resolved ? 'success' : 'warning'">
              {{ row.is_resolved ? '已解决' : '未解决' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" />
      </el-table>
    </div>

    <!-- 创建协议对话框 -->
    <el-dialog title="创建SLA协议" v-model="showCreateDialog" width="600px">
      <el-form :model="newAgreement" label-width="140px">
        <el-form-item label="协议名称">
          <el-input v-model="newAgreement.name" placeholder="请输入协议名称" />
        </el-form-item>
        <el-form-item label="SLA等级">
          <el-select v-model="newAgreement.level" placeholder="请选择等级">
            <el-option label="基础版 (99.0%)" value="BASIC" />
            <el-option label="标准版 (99.5%)" value="STANDARD" />
            <el-option label="高级版 (99.9%)" value="PREMIUM" />
            <el-option label="企业版 (99.95%)" value="ENTERPRISE" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="newAgreement.start_date" type="date" placeholder="选择日期" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="newAgreement.end_date" type="date" placeholder="选择日期" />
        </el-form-item>
        <el-form-item label="可用性目标(%)">
          <el-input-number v-model="newAgreement.availability_target" :min="90" :max="100" :step="0.1" />
        </el-form-item>
        <el-form-item label="响应时间目标(ms)">
          <el-input-number v-model="newAgreement.response_time_target" :min="100" :max="10000" :step="100" />
        </el-form-item>
        <el-form-item label="错误率目标(%)">
          <el-input-number v-model="newAgreement.error_rate_target" :min="0" :max="10" :step="0.1" />
        </el-form-item>
        <el-form-item label="吞吐量目标(req/s)">
          <el-input-number v-model="newAgreement.throughput_target" :min="10" :max="10000" :step="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createAgreement">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/utils/http'

interface SLAAgreement {
  id: string
  name: string
  level: string
  availability_target: number
  response_time_target: number
  error_rate_target: number
  throughput_target: number
  start_date: string
  end_date: string
  is_active: boolean
}

interface MetricDetail {
  actual?: number
  avg?: number
  is_compliant?: boolean
  total_requests?: number
  successful_requests?: number
  failed_requests?: number
  p50?: number
  p95?: number
  p99?: number
}

interface Violation {
  metric_type: string
  severity: string
  target_value: number
  actual_value: number
  deviation_rate: number
  violation_time: string
  is_resolved: boolean
  description: string
}

const loading = ref(false)
const showCreateDialog = ref(false)
const agreements = ref<SLAAgreement[]>([])
const selectedAgreement = ref<SLAAgreement | null>(null)
const metrics = ref<Record<string, MetricDetail>>({})
const violations = ref<Violation[]>([])
const violationFilter = ref('')
const overview = reactive({
  total_agreements: 0,
  compliant_agreements: 0,
  compliance_rate: 0,
  violation_count: 0
})

const newAgreement = reactive({
  name: '',
  level: 'STANDARD',
  start_date: '',
  end_date: '',
  availability_target: 99.5,
  response_time_target: 2000,
  error_rate_target: 0.1,
  throughput_target: 100
})

// 自动刷新定时器
let refreshTimer: ReturnType<typeof setInterval> | null = null

// 计算属性
const filteredViolations = computed(() => {
  if (!violationFilter.value) return violations.value
  return violations.value.filter((v: Violation) => v.severity === violationFilter.value)
})

// 方法
const loadOverview = async () => {
  try {
    const res = await http.get('/v1/sla/dashboard/overview')
    const data = (res as any).data ?? res
    Object.assign(overview, data)
  } catch (error) {
    console.error('Failed to load overview:', error)
  }
}

const loadAgreements = async () => {
  loading.value = true
  try {
    const res = await http.get('/v1/sla/agreements')
    const rawData = (res as any).data ?? res
    // 兼容分页格式 {items, total} 和裸数组两种响应
    agreements.value = Array.isArray(rawData)
      ? rawData
      : Array.isArray(rawData?.items)
        ? rawData.items
        : []
    if (agreements.value.length > 0 && !selectedAgreement.value) {
      selectedAgreement.value = agreements.value[0]
      await loadMetrics()
      await loadViolations()
    }
  } catch (error) {
    ElMessage.error('加载协议列表失败')
  } finally {
    loading.value = false
  }
}

const loadMetrics = async () => {
  if (!selectedAgreement.value) return
  try {
    const res = await http.get(`/v1/sla/metrics/realtime/${selectedAgreement.value.id}`)
    const data = (res as any).data ?? res
    metrics.value = data.metrics || {}
  } catch (error) {
    ElMessage.error('加载指标数据失败')
  }
}

const loadViolations = async () => {
  if (!selectedAgreement.value) return
  try {
    const res = await http.get(`/v1/sla/violations/${selectedAgreement.value.id}?days=7`)
    const rawViolations = (res as any).data ?? res
    violations.value = Array.isArray(rawViolations) ? rawViolations : []
  } catch (error) {
    ElMessage.error('加载违约记录失败')
  }
}

const viewMetrics = async (agreement: SLAAgreement) => {
  selectedAgreement.value = agreement
  await loadMetrics()
  await loadViolations()
  // 滚动到指标区域
  document.querySelector('.metrics-section')?.scrollIntoView({ behavior: 'smooth' })
}

const viewReport = async (agreement: SLAAgreement) => {
  try {
    const res = await http.get(`/v1/sla/reports/daily/${agreement.id}`)
    // TODO: 显示报告详情
    console.log('Report:', (res as any).data ?? res)
    ElMessage.success('报告生成成功')
  } catch (error) {
    ElMessage.error('生成报告失败')
  }
}

const refreshMetrics = async () => {
  await loadMetrics()
  await loadViolations()
  ElMessage.success('数据已刷新')
}

const resetNewAgreement = () => {
  Object.assign(newAgreement, {
    name: '',
    level: 'STANDARD',
    start_date: '',
    end_date: '',
    availability_target: 99.5,
    response_time_target: 2000,
    error_rate_target: 0.1,
    throughput_target: 100
  })
}

const createAgreement = async () => {
  try {
    const data = {
      ...newAgreement,
      start_date: newAgreement.start_date ? new Date(newAgreement.start_date).toISOString().split('T')[0] : '',
      end_date: newAgreement.end_date ? new Date(newAgreement.end_date).toISOString().split('T')[0] : ''
    }
    await http.post('/v1/sla/agreements', data)
    ElMessage.success('协议创建成功')
    showCreateDialog.value = false
    resetNewAgreement()
    await loadAgreements()
    await loadOverview()
  } catch (error) {
    ElMessage.error('创建协议失败')
  }
}

const getLevelType = (level: string) => {
  const types: Record<string, string> = {
    BASIC: 'info',
    STANDARD: '',
    PREMIUM: 'success',
    ENTERPRISE: 'warning'
  }
  return types[level] || ''
}

const getSeverityType = (severity: string) => {
  const types: Record<string, string> = {
    LOW: 'info',
    MEDIUM: 'warning',
    HIGH: 'danger',
    CRITICAL: 'danger'
  }
  return types[severity] || ''
}

// 生命周期
onMounted(async () => {
  await loadOverview()
  await loadAgreements()
  // 每60秒自动刷新指标
  refreshTimer = setInterval(async () => {
    if (selectedAgreement.value) {
      await loadMetrics()
    }
  }, 60000)
})

onUnmounted(() => {
  if (refreshTimer !== null) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.sla-dashboard {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.overview-card {
  display: flex;
  align-items: center;
  padding: 24px;
  transition: transform 0.3s, box-shadow 0.3s;
}

.overview-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: white;
  margin-right: 20px;
}

.card-content {
  flex: 1;
}

.card-value {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
  line-height: 1;
  margin-bottom: 8px;
}

.card-label {
  font-size: 14px;
  color: #909399;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.metric-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 24px;
  color: white;
}

.metric-card:nth-child(2) {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.metric-card:nth-child(3) {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.metric-card:nth-child(4) {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.metric-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.metric-value {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 8px;
}

.metric-target {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 12px;
}

.metric-stats {
  display: flex;
  gap: 16px;
  font-size: 13px;
  opacity: 0.85;
}

.agreements-section,
.metrics-section,
.violations-section {
  animation: fadeIn 0.5s;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
