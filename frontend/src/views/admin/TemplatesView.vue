<template>
  <div class="templates-view">
    <div class="page-header">
      <h2>内容模板管理</h2>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon> 新建模板
      </el-button>
    </div>

    <el-card class="filter-card">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-select v-model="filterCategory" placeholder="按分类筛选" clearable style="width: 100%" @change="loadTemplates">
            <el-option label="产品文案" value="product" />
            <el-option label="广告语" value="slogan" />
            <el-option label="营销方案" value="marketing" />
            <el-option label="社交媒体" value="social" />
            <el-option label="短视频脚本" value="video" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button @click="loadTemplates">刷新</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-table :data="templates" v-loading="loading" stripe>
      <el-table-column prop="name" label="模板名称" min-width="160" />
      <el-table-column prop="category" label="分类" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ categoryLabel(row.category) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="content_type" label="内容类型" width="110" />
      <el-table-column prop="platform" label="平台" width="100" />
      <el-table-column prop="usage_count" label="使用次数" width="90" align="center" />
      <el-table-column prop="is_system" label="系统模板" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_system ? 'warning' : 'info'" size="small">
            {{ row.is_system ? '系统' : '自定义' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-switch
            v-model="row.is_active"
            :disabled="row.is_system"
            @change="toggleActive(row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button
            size="small"
            type="danger"
            :disabled="row.is_system"
            @click="confirmDelete(row)"
          >删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingTemplate ? '编辑模板' : '新建模板'"
      width="760px"
      :close-on-click-modal="false"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="110px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="模板名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入模板名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分类" prop="category">
              <el-select v-model="form.category" style="width: 100%">
                <el-option label="产品文案" value="product" />
                <el-option label="广告语" value="slogan" />
                <el-option label="营销方案" value="marketing" />
                <el-option label="社交媒体" value="social" />
                <el-option label="短视频脚本" value="video" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="内容类型" prop="content_type">
              <el-select v-model="form.content_type" style="width: 100%">
                <el-option label="营销文案" value="copy" />
                <el-option label="直播脚本" value="script" />
                <el-option label="短视频文案" value="video_copy" />
                <el-option label="广告标语" value="slogan" />
                <el-option label="品牌故事" value="story" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="适用平台" prop="platform">
              <el-select v-model="form.platform" style="width: 100%">
                <el-option label="通用" value="general" />
                <el-option label="抖音" value="douyin" />
                <el-option label="小红书" value="xiaohongshu" />
                <el-option label="微信公众号" value="wechat" />
                <el-option label="微博" value="weibo" />
                <el-option label="快手" value="kuaishou" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="模板描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="简要描述模板用途" />
        </el-form-item>
        <el-form-item label="系统提示词" prop="system_prompt">
          <el-input v-model="form.system_prompt" type="textarea" :rows="4" placeholder="输入系统提示词（System Prompt）" />
        </el-form-item>
        <el-form-item label="用户提示模板" prop="user_prompt_template">
          <el-input v-model="form.user_prompt_template" type="textarea" :rows="5" placeholder="输入用户提示词模板，用 {变量名} 表示变量" />
        </el-form-item>
        <el-form-item label="示例输出">
          <el-input v-model="form.example_output" type="textarea" :rows="3" placeholder="填写示例输出（可选）" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="最大 Token">
              <el-input-number v-model="form.max_tokens" :min="100" :max="8000" :step="100" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="启用状态">
              <el-switch v-model="form.is_active" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitForm">
          {{ editingTemplate ? '保存修改' : '创建模板' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import {
  getTemplates,
  createTemplate,
  updateTemplate,
  deleteTemplate,
} from '@/api/content-generation'

interface TemplateRow {
  id: string
  name: string
  description: string
  category: string
  content_type: string
  platform: string
  system_prompt: string
  user_prompt_template: string
  example_output: string
  max_tokens: number
  is_active: boolean
  is_system: boolean
  usage_count: number
}

const templates = ref<TemplateRow[]>([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const editingTemplate = ref<TemplateRow | null>(null)
const filterCategory = ref('')
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  description: '',
  category: 'marketing',
  content_type: 'copy',
  platform: 'general',
  system_prompt: '',
  user_prompt_template: '',
  example_output: '',
  max_tokens: 2000,
  is_active: true,
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  content_type: [{ required: true, message: '请选择内容类型', trigger: 'change' }],
  platform: [{ required: true, message: '请选择平台', trigger: 'change' }],
  system_prompt: [{ required: true, message: '请输入系统提示词', trigger: 'blur' }],
  user_prompt_template: [{ required: true, message: '请输入用户提示模板', trigger: 'blur' }],
}

const categoryLabel = (cat: string) => {
  const map: Record<string, string> = {
    product: '产品文案', slogan: '广告语', marketing: '营销方案',
    social: '社交媒体', video: '短视频脚本',
  }
  return map[cat] || cat
}

const loadTemplates = async () => {
  loading.value = true
  try {
    const data = await getTemplates()
    templates.value = (data as unknown as TemplateRow[]).filter(
      (t) => !filterCategory.value || t.category === filterCategory.value
    )
  } catch {
    ElMessage.error('加载模板失败')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  Object.assign(form, {
    name: '', description: '', category: 'marketing', content_type: 'copy',
    platform: 'general', system_prompt: '', user_prompt_template: '',
    example_output: '', max_tokens: 2000, is_active: true,
  })
}

const openCreateDialog = () => {
  editingTemplate.value = null
  resetForm()
  dialogVisible.value = true
}

const openEditDialog = (row: TemplateRow) => {
  editingTemplate.value = row
  Object.assign(form, {
    name: row.name,
    description: row.description || '',
    category: row.category,
    content_type: row.content_type,
    platform: row.platform,
    system_prompt: row.system_prompt || '',
    user_prompt_template: row.user_prompt_template || '',
    example_output: row.example_output || '',
    max_tokens: row.max_tokens || 2000,
    is_active: row.is_active,
  })
  dialogVisible.value = true
}

const submitForm = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    if (editingTemplate.value) {
      await updateTemplate(editingTemplate.value.id, { ...form })
      ElMessage.success('模板已更新')
    } else {
      await createTemplate({ ...form })
      ElMessage.success('模板已创建')
    }
    dialogVisible.value = false
    await loadTemplates()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '操作失败'
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}

const toggleActive = async (row: TemplateRow) => {
  try {
    await updateTemplate(row.id, { is_active: row.is_active })
    ElMessage.success(row.is_active ? '模板已启用' : '模板已禁用')
  } catch {
    row.is_active = !row.is_active
    ElMessage.error('状态更新失败')
  }
}

const confirmDelete = (row: TemplateRow) => {
  ElMessageBox.confirm(`确定删除模板「${row.name}」？此操作不可恢复。`, '删除确认', {
    type: 'warning',
    confirmButtonText: '删除',
    confirmButtonClass: 'el-button--danger',
  }).then(async () => {
    try {
      await deleteTemplate(row.id)
      ElMessage.success('模板已删除')
      await loadTemplates()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '删除失败'
      ElMessage.error(msg)
    }
  }).catch(() => {})
}

onMounted(loadTemplates)
</script>

<style scoped lang="scss">
.templates-view {
  padding: 24px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h2 {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
    }
  }

  .filter-card {
    margin-bottom: 16px;
  }
}
</style>
