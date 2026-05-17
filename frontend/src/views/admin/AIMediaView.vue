<template>
  <div class="ai-media-view">
    <el-row :gutter="20" class="summary-row">
      <el-col :span="8">
        <el-card>
          <div class="stat-card">
            <div class="stat-value">{{ providers.length }}</div>
            <div class="stat-label">服务商数量</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <div class="stat-card">
            <div class="stat-value">{{ activeProviderCount }}</div>
            <div class="stat-label">启用服务商</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <div class="stat-card">
            <div class="stat-value">¥{{ costSummary.total_cost.toFixed(2) }}</div>
            <div class="stat-label">累计生成成本</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header>
        <div class="header">
          <span>AI 媒体服务商</span>
          <div class="header-actions">
            <el-select v-model="providerTypeFilter" clearable placeholder="媒体类型" style="width: 140px" @change="loadProviders">
              <el-option label="图片" value="image" />
              <el-option label="视频" value="video" />
            </el-select>
            <el-button type="primary" @click="openCreateDialog">新增服务商</el-button>
          </div>
        </div>
      </template>

      <el-table :data="providers" v-loading="providersLoading">
        <el-table-column prop="provider_name" label="服务商" min-width="140" />
        <el-table-column prop="provider_code" label="代码" min-width="150" />
        <el-table-column prop="provider_type" label="类型" width="90">
          <template #default="{ row }">
            <el-tag>{{ getProviderTypeLabel(row.provider_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="default_model" label="默认模型" min-width="120" show-overflow-tooltip />
        <el-table-column label="启用" width="90">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              :loading="switchingProviderIds.has(row.id)"
              @change="toggleProvider(row, 'isActive', Boolean($event))"
            />
          </template>
        </el-table-column>
        <el-table-column label="主服务商" width="100">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_primary"
              :loading="switchingProviderIds.has(row.id)"
              @change="toggleProvider(row, 'isPrimary', Boolean($event))"
            />
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="90" />
        <el-table-column prop="cost_per_unit" label="单价" width="90" />
        <el-table-column prop="health_status" label="健康状态" width="110">
          <template #default="{ row }">
            <el-tag :type="getHealthTagType(row.health_status)">{{ getHealthLabel(row.health_status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_check_time" label="最后检查" min-width="170" show-overflow-tooltip />
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button size="small" @click="testProvider(row)">测试</el-button>
            <el-button size="small" @click="healthCheckProvider(row)">健康检查</el-button>
            <el-button size="small" type="danger" @click="deleteProvider(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-row :gutter="20" class="content-row">
      <el-col :span="12">
        <el-card>
          <template #header>成本统计</template>
          <el-table :data="costSummary.by_provider">
            <el-table-column prop="provider_name" label="服务商" />
            <el-table-column prop="task_count" label="任务数" width="100" />
            <el-table-column label="成本" width="120">
              <template #default="{ row }">¥{{ row.total_cost.toFixed(2) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="header">
              <span>生成任务监控</span>
              <el-button size="small" @click="loadTasks">刷新</el-button>
            </div>
          </template>
          <el-table :data="tasks" v-loading="tasksLoading">
            <el-table-column prop="task_uuid" label="任务ID" min-width="160" show-overflow-tooltip />
            <el-table-column prop="media_type" label="类型" width="80">
              <template #default="{ row }">{{ getProviderTypeLabel(row.media_type) }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getTaskTagType(row.status)">{{ getTaskStatusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="provider.provider_name" label="服务商" min-width="120" show-overflow-tooltip />
            <el-table-column prop="cost_amount" label="成本" width="90" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" :title="editingProvider ? '编辑服务商' : '新增服务商'" width="720px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="120px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="服务商代码" prop="providerCode">
              <el-select v-model="form.providerCode" :disabled="Boolean(editingProvider)" placeholder="请选择服务商">
                <el-option label="通义万相" value="tongyi_wanxiang" />
                <el-option label="文心一格" value="wenxin_yige" />
                <el-option label="讯飞星火绘画" value="spark_drawing" />
                <el-option label="剪映开放平台" value="jianying" />
                <el-option label="腾讯智影" value="tencent_zhiying" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="服务商名称" prop="providerName">
              <el-input v-model="form.providerName" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="媒体类型" prop="providerType">
              <el-select v-model="form.providerType">
                <el-option label="图片" value="image" />
                <el-option label="视频" value="video" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="默认模型">
              <el-input v-model="form.defaultModel" placeholder="如 wanx-v1" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="API Key" prop="apiKey">
          <el-input v-model="form.apiKey" type="password" show-password :placeholder="editingProvider ? '留空则不修改' : '请输入服务商 API Key'" />
        </el-form-item>
        <el-form-item label="提交地址" prop="apiEndpoint">
          <el-input v-model="form.apiEndpoint" placeholder="服务商任务提交地址" />
        </el-form-item>
        <el-form-item label="查询地址">
          <el-input v-model="queryEndpoint" placeholder="服务商任务查询地址，使用 {task_id} 占位" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="优先级">
              <el-input-number v-model="form.priority" :min="0" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="单价">
              <el-input-number v-model="form.costPerUnit" :min="0" :precision="4" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="每分钟限流">
              <el-input-number v-model="form.rateLimitPerMinute" :min="1" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="状态">
          <el-checkbox v-model="form.isActive">启用</el-checkbox>
          <el-checkbox v-model="form.isPrimary">设为主服务商</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveProvider">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { aiMediaApi } from '@/api/aiMedia'
import type {
  AIMediaCostSummary,
  AIMediaProvider,
  AIMediaProviderForm,
  AIMediaTask,
  MediaProviderType,
  MediaTaskStatus,
} from '@/types/aiMedia'

const providers = ref<AIMediaProvider[]>([])
const tasks = ref<AIMediaTask[]>([])
const costSummary = ref<AIMediaCostSummary>({ total_cost: 0, total_tasks: 0, by_provider: [] })
const providersLoading = ref(false)
const tasksLoading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const editingProvider = ref<AIMediaProvider | null>(null)
const providerTypeFilter = ref<MediaProviderType | ''>('')
const queryEndpoint = ref('')
const formRef = ref<FormInstance>()
const switchingProviderIds = ref<Set<number>>(new Set())

const form = reactive<AIMediaProviderForm>({
  providerCode: 'tongyi_wanxiang',
  providerName: '通义万相',
  providerType: 'image',
  apiKey: '',
  appId: '',
  apiEndpoint: '',
  defaultModel: 'wanx-v1',
  isActive: true,
  isPrimary: false,
  priority: 100,
  costPerUnit: 0,
  rateLimitPerMinute: 60,
  config: {},
})

const activeProviderCount = computed(() => providers.value.filter((item) => item.is_active).length)

const formRules = computed<FormRules<AIMediaProviderForm>>(() => ({
  providerCode: [{ required: true, message: '请选择服务商', trigger: 'change' }],
  providerName: [{ required: true, message: '请输入服务商名称', trigger: 'blur' }],
  providerType: [{ required: true, message: '请选择媒体类型', trigger: 'change' }],
  apiKey: editingProvider.value ? [] : [{ required: true, message: '请输入 API Key', trigger: 'blur' }],
  apiEndpoint: [{ required: true, message: '请输入提交地址', trigger: 'blur' }],
}))

const setSwitchingProvider = (providerId: number, loading: boolean) => {
  const next = new Set(switchingProviderIds.value)
  if (loading) {
    next.add(providerId)
  } else {
    next.delete(providerId)
  }
  switchingProviderIds.value = next
}

const resetForm = () => {
  Object.assign(form, {
    providerCode: 'tongyi_wanxiang',
    providerName: '通义万相',
    providerType: 'image',
    apiKey: '',
    appId: '',
    apiEndpoint: '',
    defaultModel: 'wanx-v1',
    isActive: true,
    isPrimary: false,
    priority: 100,
    costPerUnit: 0,
    rateLimitPerMinute: 60,
    config: {},
  })
  queryEndpoint.value = ''
}

const loadProviders = async () => {
  providersLoading.value = true
  try {
    providers.value = await aiMediaApi.getProviders({
      providerType: providerTypeFilter.value || undefined,
      includeInactive: true,
    })
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '服务商加载失败')
  } finally {
    providersLoading.value = false
  }
}

const loadCosts = async () => {
  try {
    costSummary.value = await aiMediaApi.getCosts()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '成本统计加载失败')
  }
}

const loadTasks = async () => {
  tasksLoading.value = true
  try {
    const data = await aiMediaApi.getTasks({ page: 1, pageSize: 10 })
    tasks.value = data.items
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '生成任务加载失败')
  } finally {
    tasksLoading.value = false
  }
}

const loadData = async () => {
  await Promise.allSettled([loadProviders(), loadCosts(), loadTasks()])
}

const openCreateDialog = () => {
  editingProvider.value = null
  resetForm()
  dialogVisible.value = true
}

const openEditDialog = (provider: AIMediaProvider) => {
  editingProvider.value = provider
  Object.assign(form, {
    providerCode: provider.provider_code,
    providerName: provider.provider_name,
    providerType: provider.provider_type,
    apiKey: '',
    appId: provider.app_id || '',
    apiEndpoint: provider.api_endpoint || '',
    defaultModel: provider.default_model || '',
    isActive: provider.is_active,
    isPrimary: provider.is_primary,
    priority: provider.priority,
    costPerUnit: provider.cost_per_unit,
    rateLimitPerMinute: provider.rate_limit_per_minute,
    config: { ...(provider.config || {}) },
  })
  queryEndpoint.value = String(provider.config?.query_endpoint || '')
  dialogVisible.value = true
}

const buildSubmitData = () => {
  const data: AIMediaProviderForm = {
    ...form,
    config: {
      ...(form.config || {}),
      query_endpoint: queryEndpoint.value || undefined,
    },
  }
  if (!data.apiKey) {
    delete data.apiKey
  }
  return data
}

const saveProvider = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const data = buildSubmitData()
    if (editingProvider.value) {
      await aiMediaApi.updateProvider(editingProvider.value.id, data)
      ElMessage.success('服务商已更新')
    } else {
      await aiMediaApi.createProvider(data)
      ElMessage.success('服务商已创建')
    }
    dialogVisible.value = false
    await loadProviders()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '服务商保存失败')
  } finally {
    saving.value = false
  }
}

const toggleProvider = async (provider: AIMediaProvider, key: 'isActive' | 'isPrimary', value: boolean) => {
  setSwitchingProvider(provider.id, true)
  try {
    await aiMediaApi.updateProvider(provider.id, { [key]: value })
    ElMessage.success('状态已更新')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '状态更新失败')
  } finally {
    setSwitchingProvider(provider.id, false)
    await loadProviders()
  }
}

const testProvider = async (provider: AIMediaProvider) => {
  try {
    const result = await aiMediaApi.testProvider(provider.id)
    ElMessage[result.success ? 'success' : 'warning'](result.message)
    await loadProviders()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '服务商测试失败')
  }
}

const healthCheckProvider = async (provider: AIMediaProvider) => {
  try {
    const result = await aiMediaApi.healthCheckProvider(provider.id)
    ElMessage[result.success ? 'success' : 'warning'](result.message)
    await loadProviders()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '健康检查失败')
  }
}

const deleteProvider = async (provider: AIMediaProvider) => {
  try {
    await ElMessageBox.confirm(
      `确认删除服务商「${provider.provider_name}」？此操作不可恢复。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }
    )
    await aiMediaApi.deleteProvider(provider.id)
    ElMessage.success('服务商已删除')
    await loadProviders()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error instanceof Error ? error.message : '删除失败')
    }
  }
}

const getProviderTypeLabel = (type: MediaProviderType) => type === 'image' ? '图片' : '视频'

const getHealthLabel = (status: string) => {
  const labels: Record<string, string> = { healthy: '健康', degraded: '降级', unhealthy: '异常' }
  return labels[status] || status
}

const getHealthTagType = (status: string) => {
  if (status === 'healthy') return 'success'
  if (status === 'degraded') return 'warning'
  if (status === 'unhealthy') return 'danger'
  return 'info'
}

const getTaskStatusLabel = (status: MediaTaskStatus) => {
  const labels: Record<MediaTaskStatus, string> = {
    pending: '待提交',
    processing: '处理中',
    succeeded: '成功',
    failed: '失败',
    canceled: '已取消',
  }
  return labels[status]
}

const getTaskTagType = (status: MediaTaskStatus) => {
  if (status === 'succeeded') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'processing') return 'warning'
  return 'info'
}

onMounted(loadData)
</script>

<style scoped>
.ai-media-view {
  padding: 20px;
}

.summary-row,
.content-row {
  margin-bottom: 20px;
}

.header,
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 30px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  margin-top: 8px;
  color: #909399;
}
</style>
