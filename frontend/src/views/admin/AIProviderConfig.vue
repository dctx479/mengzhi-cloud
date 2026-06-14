<!-- AI服务商配置管理面板 -->
<template>
  <div class="ai-config-panel">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>AI服务商配置</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加服务商
          </el-button>
        </div>
      </template>

      <el-table :data="providers" stripe>
        <el-table-column prop="provider" label="服务商" width="150">
          <template #default="{ row }">
            <el-tag :type="getProviderTagType(row.provider)">
              {{ getProviderName(row.provider) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="provider_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.provider_type }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="model_name" label="模型" width="180" />

        <el-table-column prop="api_endpoint" label="API端点" min-width="200" show-overflow-tooltip />

        <el-table-column prop="api_key_encrypted" label="API Key" width="150">
          <template #default="{ row }">
            <span class="masked-key">{{ maskApiKey(row.api_key_encrypted) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              @change="toggleActive(row)"
            />
          </template>
        </el-table-column>

        <el-table-column prop="priority" label="优先级" width="80" />

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="testConnection(row)">测试</el-button>
            <el-button size="small" @click="editProvider(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteProvider(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="服务商" prop="provider">
          <el-select v-model="form.provider" :disabled="isEdit" placeholder="选择服务商">
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="火山引擎(图像)" value="volcengine_image" />
            <el-option label="火山引擎(视频)" value="volcengine_video" />
            <el-option label="Claude" value="claude" />
          </el-select>
        </el-form-item>

        <el-form-item label="服务类型" prop="provider_type">
          <el-select v-model="form.provider_type">
            <el-option label="LLM" value="llm" />
            <el-option label="图像生成" value="image" />
            <el-option label="视频生成" value="video" />
          </el-select>
        </el-form-item>

        <el-form-item label="API端点" prop="api_endpoint">
          <el-input v-model="form.api_endpoint" placeholder="https://api.example.com" />
        </el-form-item>

        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="form.api_key"
            type="password"
            show-password
            placeholder="输入API Key（留空则不修改）"
          />
        </el-form-item>

        <el-form-item label="模型名称" prop="model_name">
          <el-input v-model="form.model_name" placeholder="deepseek-v4-flash" />
        </el-form-item>

        <el-form-item label="优先级" prop="priority">
          <el-input-number v-model="form.priority" :min="1" :max="10" />
          <span class="form-hint">数字越小优先级越高</span>
        </el-form-item>

        <el-form-item label="是否启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>

        <el-form-item label="高级配置">
          <el-input
            v-model="form.config_json"
            type="textarea"
            :rows="4"
            placeholder='{"temperature": 0.7, "max_tokens": 2000}'
          />
          <span class="form-hint">JSON格式配置参数</span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import * as api from '@/api/aiConfig'

interface Provider {
  id?: number
  provider: string
  provider_type: string
  api_endpoint: string
  api_key_encrypted?: string
  model_name: string
  is_active: boolean
  priority: number
  config_json?: string
}

const providers = ref<Provider[]>([])
const dialogVisible = ref(false)
const dialogTitle = ref('添加服务商')
const isEdit = ref(false)
const formRef = ref()

const form = reactive<Provider>({
  provider: '',
  provider_type: 'llm',
  api_endpoint: '',
  api_key: '',
  model_name: '',
  is_active: true,
  priority: 1,
  config_json: ''
})

const rules = {
  provider: [{ required: true, message: '请选择服务商', trigger: 'change' }],
  provider_type: [{ required: true, message: '请选择服务类型', trigger: 'change' }],
  api_endpoint: [{ required: true, message: '请输入API端点', trigger: 'blur' }],
  model_name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }]
}

onMounted(() => {
  loadProviders()
})

const loadProviders = async () => {
  const res = await api.getAIConfigs()
  providers.value = res
}

const getProviderName = (provider: string) => {
  const names = {
    deepseek: 'DeepSeek',
    volcengine_image: '火山引擎(图)',
    volcengine_video: '火山引擎(视频)',
    claude: 'Claude'
  }
  return names[provider] || provider
}

const getProviderTagType = (provider: string) => {
  const types = {
    deepseek: 'success',
    volcengine_image: 'warning',
    volcengine_video: 'warning',
    claude: 'info'
  }
  return types[provider] || ''
}

const maskApiKey = (key: string) => {
  if (!key || key.length < 8) return '****'
  return key.substring(0, 6) + '****' + key.substring(key.length - 4)
}

const showAddDialog = () => {
  dialogTitle.value = '添加服务商'
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const editProvider = (row: Provider) => {
  dialogTitle.value = '编辑服务商'
  isEdit.value = true
  Object.assign(form, {
    ...row,
    api_key: '' // 不回显密钥
  })
  dialogVisible.value = true
}

const resetForm = () => {
  Object.assign(form, {
    provider: '',
    provider_type: 'llm',
    api_endpoint: '',
    api_key: '',
    model_name: '',
    is_active: true,
    priority: 1,
    config_json: ''
  })
}

const submitForm = async () => {
  await formRef.value.validate()

  try {
    if (isEdit.value) {
      await api.updateAIConfig(form.provider, form)
      ElMessage.success('更新成功')
    } else {
      await api.createAIConfig(form)
      ElMessage.success('添加成功')
    }

    dialogVisible.value = false
    loadProviders()
  } catch (error) {
    ElMessage.error(error.message || '操作失败')
  }
}

const toggleActive = async (row: Provider) => {
  try {
    await api.updateAIConfig(row.provider, { is_active: row.is_active })
    ElMessage.success(row.is_active ? '已启用' : '已禁用')
  } catch (error) {
    row.is_active = !row.is_active
    ElMessage.error('状态切换失败')
  }
}

const testConnection = async (row: Provider) => {
  try {
    const res = await api.testAIConfig(row.provider)
    if (res.success) {
      ElMessage.success(`连接成功！模型: ${res.model || 'N/A'}`)
    } else {
      ElMessage.error(`连接失败: ${res.message}`)
    }
  } catch (error) {
    ElMessage.error('测试失败')
  }
}

const deleteProvider = async (row: Provider) => {
  await ElMessageBox.confirm('确认删除该服务商配置？', '警告', {
    type: 'warning'
  })

  try {
    await api.deleteAIConfig(row.provider)
    ElMessage.success('删除成功')
    loadProviders()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.masked-key {
  font-family: monospace;
  color: #999;
}

.form-hint {
  font-size: 12px;
  color: #999;
  margin-left: 10px;
}
</style>
