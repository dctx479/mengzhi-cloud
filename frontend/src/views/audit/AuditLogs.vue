<template>
  <div class="audit-logs-view">
    <!-- 统计图表 -->
    <AuditStats :stats="stats" />

    <!-- 日志列表 -->
    <el-card shadow="hover" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span class="title">审计日志</span>
          <div class="header-actions">
            <el-button
              type="primary"
              :icon="Refresh"
              @click="loadLogs"
              :loading="loading"
            >
              刷新
            </el-button>
            <el-button
              type="success"
              :icon="Download"
              @click="showExportDialog = true"
            >
              导出
            </el-button>
          </div>
        </div>
      </template>

      <!-- 高级筛选 -->
      <el-form :model="queryForm" inline class="filter-form">
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            :shortcuts="dateShortcuts"
            style="width: 380px"
            @change="handleDateChange"
          />
        </el-form-item>

        <el-form-item label="操作类型">
          <el-select
            v-model="queryForm.action"
            placeholder="全部"
            clearable
            style="width: 150px"
            @change="handleFilterChange"
          >
            <el-option
              v-for="action in actionTypes"
              :key="action"
              :label="action"
              :value="action"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="资源类型">
          <el-select
            v-model="queryForm.resourceType"
            placeholder="全部"
            clearable
            style="width: 150px"
            @change="handleFilterChange"
          >
            <el-option
              v-for="type in resourceTypes"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="操作人">
          <el-input
            v-model="queryForm.username"
            placeholder="输入用户名"
            clearable
            style="width: 150px"
            @change="handleFilterChange"
          />
        </el-form-item>

        <el-form-item label="状态">
          <el-select
            v-model="queryForm.status"
            placeholder="全部"
            clearable
            style="width: 120px"
            @change="handleFilterChange"
          >
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failure" />
          </el-select>
        </el-form-item>

        <el-form-item label="搜索">
          <el-input
            v-model="queryForm.search"
            placeholder="搜索资源名称/ID"
            clearable
            style="width: 200px"
            @change="handleFilterChange"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 日志表格 -->
      <el-table
        :data="logs"
        v-loading="loading"
        stripe
        style="width: 100%"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="id" label="ID" width="80" sortable="custom" />

        <el-table-column prop="action" label="操作类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getActionTagType(row.action)" size="small">
              {{ row.action }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="username" label="操作人" width="120" />

        <el-table-column prop="resource" label="资源类型" width="120" />

        <el-table-column label="资源名称" min-width="150">
          <template #default="{ row }">
            <el-text truncated>{{ row.details || row.resource_id }}</el-text>
          </template>
        </el-table-column>

        <el-table-column prop="ip_address" label="IP地址" width="140" />

        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag
              :type="row.is_success ? 'success' : 'danger'"
              size="small"
            >
              {{ row.is_success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          prop="created_at"
          label="操作时间"
          width="180"
          sortable="custom"
        />

        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              @click="viewDetail(row)"
            >
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="queryForm.page"
          v-model:page-size="queryForm.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 日志详情对话框 -->
    <AuditLogDetail
      v-model="showDetailDialog"
      :log="currentLog"
      :related-logs="relatedLogs"
      @view-related="viewRelatedLog"
    />

    <!-- 导出对话框 -->
    <el-dialog
      v-model="showExportDialog"
      title="导出审计日志"
      width="500px"
    >
      <el-form :model="exportForm" label-width="100px">
        <el-form-item label="导出格式">
          <el-radio-group v-model="exportForm.format">
            <el-radio label="csv">CSV</el-radio>
            <el-radio label="json">JSON</el-radio>
            <el-radio label="excel">Excel</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="时间范围">
          <el-date-picker
            v-model="exportDateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            :shortcuts="dateShortcuts"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="操作类型">
          <el-select
            v-model="exportForm.action"
            placeholder="全部"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="action in actionTypes"
              :key="action"
              :label="action"
              :value="action"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="资源类型">
          <el-select
            v-model="exportForm.resourceType"
            placeholder="全部"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="type in resourceTypes"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-select
            v-model="exportForm.status"
            placeholder="全部"
            clearable
            style="width: 100%"
          >
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failure" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showExportDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="handleExport"
          :loading="exporting"
        >
          导出
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Download, Search } from '@element-plus/icons-vue'
import { auditLogsApi } from '@/api/auditLogs'
import AuditStats from './components/AuditStats.vue'
import AuditLogDetail from './components/AuditLogDetail.vue'
import type { AuditLog, AuditLogQuery, AuditStats as AuditStatsType } from '@/types/auditLog'

// 数据
const logs = ref<AuditLog[]>([])
const stats = ref<AuditStatsType | null>(null)
const actionTypes = ref<string[]>([])
const resourceTypes = ref<string[]>([])
const loading = ref(false)
const total = ref(0)

// 查询表单
const queryForm = reactive<AuditLogQuery>({
  page: 1,
  pageSize: 20,
  startTime: undefined,
  endTime: undefined,
  action: undefined,
  resourceType: undefined,
  userId: undefined,
  username: undefined,
  status: undefined,
  search: undefined
})

// 日期范围
const dateRange = ref<[string, string] | null>(null)

// 日期快捷选项
const dateShortcuts = [
  {
    text: '最近1小时',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000)
      return [start, end]
    }
  },
  {
    text: '今天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setHours(0, 0, 0, 0)
      return [start, end]
    }
  },
  {
    text: '最近7天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
      return [start, end]
    }
  },
  {
    text: '最近30天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
      return [start, end]
    }
  }
]

// 详情对话框
const showDetailDialog = ref(false)
const currentLog = ref<AuditLog | null>(null)
const relatedLogs = ref<AuditLog[]>([])

// 导出对话框
const showExportDialog = ref(false)
const exporting = ref(false)
const exportDateRange = ref<[string, string] | null>(null)
const exportForm = reactive({
  format: 'csv' as 'csv' | 'json' | 'excel',
  startTime: undefined as string | undefined,
  endTime: undefined as string | undefined,
  action: undefined as string | undefined,
  resourceType: undefined as string | undefined,
  status: undefined as 'success' | 'failure' | undefined
})

// 加载日志列表
const loadLogs = async () => {
  loading.value = true
  try {
    const { data } = await auditLogsApi.getAuditLogs(queryForm)
    logs.value = data.data
    total.value = data.total
  } catch (error) {
    ElMessage.error('加载日志失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 加载统计数据
const loadStats = async () => {
  try {
    const params = {
      startTime: queryForm.startTime,
      endTime: queryForm.endTime
    }
    const { data } = await auditLogsApi.getAuditStats(params)
    stats.value = data
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 加载操作类型和资源类型
const loadTypes = async () => {
  try {
    const [actionsRes, resourcesRes] = await Promise.all([
      auditLogsApi.getActionTypes(),
      auditLogsApi.getResourceTypes()
    ])
    actionTypes.value = actionsRes.data
    resourceTypes.value = resourcesRes.data
  } catch (error) {
    console.error('加载类型列表失败:', error)
  }
}

// 处理日期范围变化
const handleDateChange = (value: [string, string] | null) => {
  if (value) {
    queryForm.startTime = value[0]
    queryForm.endTime = value[1]
  } else {
    queryForm.startTime = undefined
    queryForm.endTime = undefined
  }
  handleSearch()
}

// 处理筛选变化
const handleFilterChange = () => {
  queryForm.page = 1
  loadLogs()
}

// 处理搜索
const handleSearch = () => {
  queryForm.page = 1
  loadLogs()
  loadStats()
}

// 处理重置
const handleReset = () => {
  Object.assign(queryForm, {
    page: 1,
    pageSize: 20,
    startTime: undefined,
    endTime: undefined,
    action: undefined,
    resourceType: undefined,
    userId: undefined,
    username: undefined,
    status: undefined,
    search: undefined
  })
  dateRange.value = null
  loadLogs()
  loadStats()
}

// 处理排序
const handleSortChange = ({ prop, order }: any) => {
  // 实现排序逻辑
  console.log('Sort:', prop, order)
}

// 处理分页大小变化
const handleSizeChange = (size: number) => {
  queryForm.pageSize = size
  queryForm.page = 1
  loadLogs()
}

// 处理页码变化
const handlePageChange = (page: number) => {
  queryForm.page = page
  loadLogs()
}

// 查看详情
const viewDetail = async (log: AuditLog) => {
  try {
    // 加载完整日志详情
    const { data } = await auditLogsApi.getAuditLogDetail(log.id)
    currentLog.value = data

    // 加载相关日志（同一资源的其他操作）
    const relatedRes = await auditLogsApi.getAuditLogs({
      resourceType: log.resourceType,
      resourceId: log.resourceId,
      pageSize: 10
    })
    relatedLogs.value = relatedRes.data.data.filter(item => item.id !== log.id)

    showDetailDialog.value = true
  } catch (error) {
    ElMessage.error('加载日志详情失败')
    console.error(error)
  }
}

// 查看相关日志
const viewRelatedLog = async (id: number) => {
  try {
    const { data } = await auditLogsApi.getAuditLogDetail(id)
    currentLog.value = data

    // 重新加载相关日志
    const relatedRes = await auditLogsApi.getAuditLogs({
      resourceType: data.resourceType,
      resourceId: data.resourceId,
      pageSize: 10
    })
    relatedLogs.value = relatedRes.data.data.filter(item => item.id !== id)
  } catch (error) {
    ElMessage.error('加载日志详情失败')
    console.error(error)
  }
}

// 导出日志
const handleExport = async () => {
  exporting.value = true
  try {
    // 设置导出时间范围
    if (exportDateRange.value) {
      exportForm.startTime = exportDateRange.value[0]
      exportForm.endTime = exportDateRange.value[1]
    }

    const { data } = await auditLogsApi.exportAuditLogs(exportForm)

    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([data]))
    const link = document.createElement('a')
    link.href = url

    // 设置文件名
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
    const extension = exportForm.format === 'excel' ? 'xlsx' : exportForm.format
    link.setAttribute('download', `audit-logs-${timestamp}.${extension}`)

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
    showExportDialog.value = false
  } catch (error) {
    ElMessage.error('导出失败')
    console.error(error)
  } finally {
    exporting.value = false
  }
}

// 获取操作类型标签样式
const getActionTagType = (action: string) => {
  const actionMap: Record<string, any> = {
    'CREATE': 'success',
    'UPDATE': 'warning',
    'DELETE': 'danger',
    'LOGIN': 'info',
    'LOGOUT': 'info',
    'VIEW': '',
    'EXPORT': 'warning'
  }
  return actionMap[action] || ''
}

// 初始化
onMounted(() => {
  loadLogs()
  loadStats()
  loadTypes()
})
</script>

<style scoped>
.audit-logs-view {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header .title {
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filter-form {
  margin-bottom: 20px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
