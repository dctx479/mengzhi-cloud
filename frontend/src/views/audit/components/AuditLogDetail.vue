<template>
  <el-dialog
    v-model="visible"
    title="审计日志详情"
    width="900px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div v-if="log" class="audit-log-detail">
      <!-- 基本信息 -->
      <el-descriptions :column="2" border>
        <el-descriptions-item label="日志ID">
          {{ log.id }}
        </el-descriptions-item>
        <el-descriptions-item label="操作时间">
          {{ log.createdAt }}
        </el-descriptions-item>
        <el-descriptions-item label="操作人">
          {{ log.username }} (ID: {{ log.userId }})
        </el-descriptions-item>
        <el-descriptions-item label="操作类型">
          <el-tag :type="getActionTagType(log.action)">
            {{ log.action }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="资源类型">
          {{ log.resourceType }}
        </el-descriptions-item>
        <el-descriptions-item label="资源ID">
          {{ log.resourceId }}
        </el-descriptions-item>
        <el-descriptions-item label="资源名称" :span="2">
          {{ log.resourceName || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="IP地址">
          {{ log.ipAddress }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="log.status === 'success' ? 'success' : 'danger'">
            {{ log.status === 'success' ? '成功' : '失败' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item v-if="log.errorMessage" label="错误信息" :span="2">
          <el-text type="danger">{{ log.errorMessage }}</el-text>
        </el-descriptions-item>
        <el-descriptions-item label="User Agent" :span="2">
          <el-text class="user-agent">{{ log.userAgent }}</el-text>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 元数据 -->
      <div v-if="log.metadata && Object.keys(log.metadata).length > 0" class="section">
        <div class="section-title">
          <el-icon><InfoFilled /></el-icon>
          <span>元数据</span>
        </div>
        <el-card shadow="never" class="metadata-card">
          <pre class="json-content">{{ JSON.stringify(log.metadata, null, 2) }}</pre>
        </el-card>
      </div>

      <!-- 数据对比 -->
      <div v-if="log.beforeData || log.afterData" class="section">
        <div class="section-title">
          <el-icon><DocumentCopy /></el-icon>
          <span>数据变更</span>
        </div>

        <el-tabs v-model="activeTab" class="diff-tabs">
          <!-- Diff视图 -->
          <el-tab-pane label="对比视图" name="diff">
            <div class="diff-view">
              <div v-if="diffResult.length === 0" class="no-changes">
                <el-empty description="无数据变更" />
              </div>
              <div v-else class="diff-list">
                <div
                  v-for="(item, index) in diffResult"
                  :key="index"
                  class="diff-item"
                  :class="item.type"
                >
                  <div class="diff-header">
                    <el-tag
                      :type="getDiffTagType(item.type)"
                      size="small"
                    >
                      {{ getDiffLabel(item.type) }}
                    </el-tag>
                    <span class="field-path">{{ item.path }}</span>
                  </div>
                  <div class="diff-content">
                    <div v-if="item.type !== 'added'" class="old-value">
                      <span class="label">旧值:</span>
                      <code>{{ formatValue(item.oldValue) }}</code>
                    </div>
                    <div v-if="item.type !== 'removed'" class="new-value">
                      <span class="label">新值:</span>
                      <code>{{ formatValue(item.newValue) }}</code>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 操作前数据 -->
          <el-tab-pane label="操作前" name="before">
            <el-card shadow="never" class="data-card">
              <pre v-if="log.beforeData" class="json-content">{{ JSON.stringify(log.beforeData, null, 2) }}</pre>
              <el-empty v-else description="无操作前数据" />
            </el-card>
          </el-tab-pane>

          <!-- 操作后数据 -->
          <el-tab-pane label="操作后" name="after">
            <el-card shadow="never" class="data-card">
              <pre v-if="log.afterData" class="json-content">{{ JSON.stringify(log.afterData, null, 2) }}</pre>
              <el-empty v-else description="无操作后数据" />
            </el-card>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 相关日志 -->
      <div v-if="relatedLogs.length > 0" class="section">
        <div class="section-title">
          <el-icon><Link /></el-icon>
          <span>相关日志</span>
        </div>
        <el-table :data="relatedLogs" size="small">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="action" label="操作" width="120">
            <template #default="{ row }">
              <el-tag :type="getActionTagType(row.action)" size="small">
                {{ row.action }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="resourceType" label="资源类型" width="120" />
          <el-table-column prop="createdAt" label="时间" />
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button
                type="primary"
                link
                size="small"
                @click="viewRelatedLog(row.id)"
              >
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { InfoFilled, DocumentCopy, Link } from '@element-plus/icons-vue'
import type { AuditLog } from '@/types/auditLog'

interface Props {
  modelValue: boolean
  log: AuditLog | null
  relatedLogs?: AuditLog[]
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'view-related', id: number): void
}

const props = withDefaults(defineProps<Props>(), {
  relatedLogs: () => []
})

const emit = defineEmits<Emits>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const activeTab = ref('diff')

interface DiffItem {
  type: 'added' | 'removed' | 'modified'
  path: string
  oldValue?: any
  newValue?: any
}

// 计算数据差异
const diffResult = computed<DiffItem[]>(() => {
  if (!props.log?.beforeData || !props.log?.afterData) {
    return []
  }

  const diffs: DiffItem[] = []
  const before = props.log.beforeData
  const after = props.log.afterData

  // 获取所有键
  const allKeys = new Set([
    ...Object.keys(before),
    ...Object.keys(after)
  ])

  allKeys.forEach(key => {
    const beforeValue = before[key]
    const afterValue = after[key]

    if (!(key in before)) {
      // 新增字段
      diffs.push({
        type: 'added',
        path: key,
        newValue: afterValue
      })
    } else if (!(key in after)) {
      // 删除字段
      diffs.push({
        type: 'removed',
        path: key,
        oldValue: beforeValue
      })
    } else if (JSON.stringify(beforeValue) !== JSON.stringify(afterValue)) {
      // 修改字段
      diffs.push({
        type: 'modified',
        path: key,
        oldValue: beforeValue,
        newValue: afterValue
      })
    }
  })

  return diffs
})

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

// 获取差异类型标签样式
const getDiffTagType = (type: string) => {
  const typeMap: Record<string, any> = {
    'added': 'success',
    'removed': 'danger',
    'modified': 'warning'
  }
  return typeMap[type] || ''
}

// 获取差异类型标签文本
const getDiffLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    'added': '新增',
    'removed': '删除',
    'modified': '修改'
  }
  return labelMap[type] || type
}

// 格式化值
const formatValue = (value: any) => {
  if (value === null) return 'null'
  if (value === undefined) return 'undefined'
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }
  return String(value)
}

// 查看相关日志
const viewRelatedLog = (id: number) => {
  emit('view-related', id)
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  activeTab.value = 'diff'
}

// 监听日志变化，重置tab
watch(() => props.log, () => {
  activeTab.value = 'diff'
})
</script>

<style scoped>
.audit-log-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.section {
  margin-top: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #303133;
}

.user-agent {
  font-size: 12px;
  word-break: break-all;
}

.metadata-card,
.data-card {
  background-color: #f5f7fa;
}

.json-content {
  margin: 0;
  padding: 12px;
  background-color: #282c34;
  color: #abb2bf;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.6;
  overflow-x: auto;
}

.diff-tabs {
  margin-top: 12px;
}

.diff-view {
  min-height: 200px;
}

.no-changes {
  padding: 40px 0;
}

.diff-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.diff-item {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 12px;
  transition: all 0.3s;
}

.diff-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.diff-item.added {
  background-color: #f0f9ff;
  border-color: #67c23a;
}

.diff-item.removed {
  background-color: #fef0f0;
  border-color: #f56c6c;
}

.diff-item.modified {
  background-color: #fdf6ec;
  border-color: #e6a23c;
}

.diff-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.field-path {
  font-weight: 600;
  color: #303133;
  font-family: 'Courier New', monospace;
}

.diff-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.old-value,
.new-value {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px;
  border-radius: 4px;
}

.old-value {
  background-color: rgba(245, 108, 108, 0.1);
}

.new-value {
  background-color: rgba(103, 194, 58, 0.1);
}

.old-value .label {
  color: #f56c6c;
  font-weight: 600;
  min-width: 50px;
}

.new-value .label {
  color: #67c23a;
  font-weight: 600;
  min-width: 50px;
}

.old-value code,
.new-value code {
  flex: 1;
  padding: 4px 8px;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  word-break: break-all;
  white-space: pre-wrap;
}
</style>
