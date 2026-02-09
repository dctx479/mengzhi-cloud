<template>
  <div class="ai-config-view">
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>AI配置管理</span>
          <el-button type="primary" @click="handleAdd">添加配置</el-button>
        </div>
      </template>

      <el-table :data="configs" v-loading="loading">
        <el-table-column prop="name" label="配置名称" />
        <el-table-column prop="provider" label="提供商" width="120">
          <template #default="{ row }">
            <el-tag>{{ providerMap[row.provider] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model" label="模型" />
        <el-table-column prop="isActive" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.isActive ? 'success' : 'info'">
              {{ row.isActive ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleTest(row)">测试</el-button>
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" @close="resetForm">
      <AIConfigForm ref="formRef" v-model="formData" />
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import AIConfigForm from '@/components/enterprise/AIConfigForm.vue';
import { getAIConfigs, createAIConfig, updateAIConfig, deleteAIConfig, testAIConfig } from '@/api/aiConfig';
import type { AIConfig, AIConfigForm as AIConfigFormType } from '@/types/aiConfig';

const enterpriseId = ref('1'); // TODO: 从路由或store获取
const configs = ref<AIConfig[]>([]);
const loading = ref(false);
const dialogVisible = ref(false);
const dialogTitle = ref('');
const formRef = ref();
const formData = ref<AIConfigFormType>({
  name: '',
  provider: 'openai',
  apiKey: '',
  endpoint: '',
  model: '',
  isActive: true
});
const submitting = ref(false);
const editingId = ref<string>();

const providerMap: Record<string, string> = {
  openai: 'OpenAI',
  azure: 'Azure',
  anthropic: 'Anthropic',
  custom: '自定义'
};

const loadConfigs = async () => {
  loading.value = true;
  try {
    configs.value = await getAIConfigs(enterpriseId.value);
  } catch (error: any) {
    ElMessage.error(error.message || '加载失败');
  } finally {
    loading.value = false;
  }
};

const handleAdd = () => {
  dialogTitle.value = '添加AI配置';
  editingId.value = undefined;
  dialogVisible.value = true;
};

const handleEdit = (row: AIConfig) => {
  dialogTitle.value = '编辑AI配置';
  editingId.value = row.id;
  formData.value = {
    name: row.name,
    provider: row.provider,
    apiKey: row.apiKey,
    endpoint: row.endpoint,
    model: row.model,
    isActive: row.isActive
  };
  dialogVisible.value = true;
};

const handleSubmit = async () => {
  try {
    await formRef.value?.validate();
    submitting.value = true;

    if (editingId.value) {
      await updateAIConfig(enterpriseId.value, editingId.value, formData.value);
      ElMessage.success('更新成功');
    } else {
      await createAIConfig(enterpriseId.value, formData.value);
      ElMessage.success('添加成功');
    }

    dialogVisible.value = false;
    loadConfigs();
  } catch (error: any) {
    if (error !== false) ElMessage.error(error.message || '操作失败');
  } finally {
    submitting.value = false;
  }
};

const handleDelete = async (row: AIConfig) => {
  try {
    await ElMessageBox.confirm('确定删除该配置吗？', '提示', { type: 'warning' });
    await deleteAIConfig(enterpriseId.value, row.id);
    ElMessage.success('删除成功');
    loadConfigs();
  } catch (error: any) {
    if (error !== 'cancel') ElMessage.error(error.message || '删除失败');
  }
};

const handleTest = async (row: AIConfig) => {
  const loadingMsg = ElMessage.info({ message: '测试中...', duration: 0 });
  try {
    const result = await testAIConfig(enterpriseId.value, row.id);
    loadingMsg.close();
    ElMessage.success(result.message || '连接成功');
  } catch (error: any) {
    loadingMsg.close();
    ElMessage.error(error.message || '连接失败');
  }
};

const resetForm = () => {
  formData.value = {
    name: '',
    provider: 'openai',
    apiKey: '',
    endpoint: '',
    model: '',
    isActive: true
  };
};

onMounted(() => {
  loadConfigs();
});
</script>

<style scoped>
.ai-config-view {
  padding: 20px;
}
</style>
