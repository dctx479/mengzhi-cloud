<template>
  <div class="ai-config-view">
    <!-- 管理员: 提供商管理面板 -->
    <el-card v-if="userStore.isAdmin" style="margin-bottom: 20px">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>提供商管理</span>
          <el-button type="primary" size="small" :loading="savingProviders" @click="saveProviderSettings">
            保存设置
          </el-button>
        </div>
      </template>
      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      >
        <template #default>
          管理员可以控制哪些AI提供商对普通用户可见。「自定义接入」始终对用户开放。
        </template>
      </el-alert>
      <div class="provider-groups">
        <div class="provider-group">
          <h4>国际</h4>
          <div class="provider-switches">
            <div v-for="p in providersByGroup.international" :key="p.id" class="provider-switch-item">
              <el-switch v-model="p.enabled" :disabled="p.id === 'custom'" />
              <span>{{ p.name }}</span>
            </div>
          </div>
        </div>
        <div class="provider-group">
          <h4>国产</h4>
          <div class="provider-switches">
            <div v-for="p in providersByGroup.national" :key="p.id" class="provider-switch-item">
              <el-switch v-model="p.enabled" />
              <span>{{ p.name }}</span>
            </div>
          </div>
        </div>
        <div class="provider-group">
          <h4>其他</h4>
          <div class="provider-switches">
            <div v-for="p in providersByGroup.other" :key="p.id" class="provider-switch-item">
              <el-switch v-model="p.enabled" :disabled="p.id === 'custom'" />
              <span>{{ p.name }}</span>
              <el-tag v-if="p.id === 'custom'" size="small" type="info" style="margin-left: 8px">始终启用</el-tag>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- AI配置列表 -->
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center">
          <span>AI配置管理</span>
          <el-button type="primary" @click="handleAdd">添加配置</el-button>
        </div>
      </template>

      <el-table :data="configs" v-loading="loading">
        <el-table-column prop="name" label="配置名称" />
        <el-table-column prop="provider" label="提供商" width="140">
          <template #default="{ row }">
            <el-tag>{{ providerMap[row.provider] || row.provider }}</el-tag>
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
import { ref, reactive, onMounted, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import AIConfigForm from '@/components/enterprise/AIConfigForm.vue';
import {
  getAIConfigs, createAIConfig, updateAIConfig, deleteAIConfig, testAIConfig,
  getProviderSettings, updateProviderSettings, type ProviderInfo
} from '@/api/aiConfig';
import type { AIConfig, AIConfigForm as AIConfigFormType } from '@/types/aiConfig';
import { useUserStore } from '@/stores/user';

const userStore = useUserStore();
const enterpriseId = computed(() => {
  // 优先使用enterprise_id，其次tenant_id，再次user.id
  const id = userStore.user?.enterprise_id || userStore.user?.tenant_id || userStore.user?.id
  return String(id ?? 'default')
});
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

// 提供商管理
const allProviders = ref<(ProviderInfo & { enabled: boolean })[]>([]);
const savingProviders = ref(false);

const providersByGroup = computed(() => {
  const groups: Record<string, (ProviderInfo & { enabled: boolean })[]> = {
    international: [],
    national: [],
    other: [],
  };
  for (const p of allProviders.value) {
    const g = p.group || 'other';
    if (groups[g]) groups[g].push(p);
    else groups.other.push(p);
  }
  return groups;
});

const providerMap: Record<string, string> = {
  openai: 'OpenAI',
  azure: 'Azure',
  anthropic: 'Anthropic',
  deepseek: 'DeepSeek',
  qwen: '通义千问',
  wenxin: '文心一言',
  glm: '智谱GLM',
  spark: '讯飞星火',
  moonshot: 'Moonshot',
  custom: '自定义'
};

const loadProviderSettings = async () => {
  if (!userStore.isAdmin) return;
  try {
    const result = await getProviderSettings();
    if (result?.providers) {
      allProviders.value = result.providers.map((p: ProviderInfo) => ({
        ...p,
        enabled: (p as any).enabled ?? true
      }));
    }
  } catch {
    // 加载失败不影响主功能
  }
};

const saveProviderSettings = async () => {
  savingProviders.value = true;
  try {
    const enabledIds = allProviders.value
      .filter(p => p.enabled)
      .map(p => p.id);
    await updateProviderSettings(enabledIds);
    ElMessage.success('提供商设置已保存');
  } catch (error: any) {
    ElMessage.error(error.message || '保存失败');
  } finally {
    savingProviders.value = false;
  }
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
  loadProviderSettings();
});
</script>

<style scoped>
.ai-config-view {
  padding: 20px;
}

.provider-groups {
  display: flex;
  gap: 32px;
  flex-wrap: wrap;
}

.provider-group {
  flex: 1;
  min-width: 200px;
}

.provider-group h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
  border-bottom: 1px solid #eee;
  padding-bottom: 8px;
}

.provider-switches {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.provider-switch-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}
</style>
