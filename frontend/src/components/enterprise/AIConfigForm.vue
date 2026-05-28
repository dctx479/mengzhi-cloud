<template>
  <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
    <el-form-item label="配置名称" prop="name">
      <el-input v-model="form.name" placeholder="请输入配置名称" />
    </el-form-item>

    <el-form-item label="AI提供商" prop="provider">
      <el-select v-model="form.provider" placeholder="请选择提供商" style="width: 100%" :loading="loadingProviders">
        <template v-if="groupedProviders.international.length > 0">
          <el-option-group label="国际">
            <el-option v-for="p in groupedProviders.international" :key="p.id" :label="p.name" :value="p.id" />
          </el-option-group>
        </template>
        <template v-if="groupedProviders.national.length > 0">
          <el-option-group label="国产">
            <el-option v-for="p in groupedProviders.national" :key="p.id" :label="p.name" :value="p.id" />
          </el-option-group>
        </template>
        <template v-if="groupedProviders.other.length > 0">
          <el-option-group label="其他">
            <el-option v-for="p in groupedProviders.other" :key="p.id" :label="p.name" :value="p.id" />
          </el-option-group>
        </template>
      </el-select>
    </el-form-item>

    <el-form-item label="API密钥" prop="apiKey">
      <el-input v-model="form.apiKey" type="password" show-password placeholder="请输入API密钥" />
    </el-form-item>

    <el-form-item label="端点地址" prop="endpoint" v-if="needsEndpoint">
      <el-input v-model="form.endpoint" placeholder="请输入端点地址" />
    </el-form-item>

    <el-form-item label="模型" prop="model">
      <el-select v-if="modelOptions.length > 0" v-model="form.model" filterable allow-create default-first-option placeholder="选择或直接输入模型 ID" style="width: 100%">
        <el-option v-for="m in modelOptions" :key="m.value" :label="m.label" :value="m.value" />
      </el-select>
      <el-input v-else v-model="form.model" placeholder="请输入模型名称，如 gpt-4o" />
      <div style="font-size: 12px; color: #909399; margin-top: 4px; line-height: 1.4">
        可从列表选择，也可直接输入任意模型 ID（如 <code style="background:#f5f7fa;padding:1px 4px;border-radius:3px">gpt-5.5</code>、<code style="background:#f5f7fa;padding:1px 4px;border-radius:3px">deepseek-v4-pro</code>）
      </div>
    </el-form-item>

    <el-form-item label="启用状态">
      <el-switch v-model="form.isActive" />
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import type { AIConfigForm } from '@/types/aiConfig';
import { getAvailableProviders, type ProviderInfo } from '@/api/aiConfig';

const props = defineProps<{
  modelValue?: AIConfigForm;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: AIConfigForm];
}>();

const formRef = ref<FormInstance>();
const loadingProviders = ref(false);
const availableProviders = ref<ProviderInfo[]>([]);

const form = reactive<AIConfigForm>({
  name: '',
  provider: 'openai',
  apiKey: '',
  endpoint: '',
  model: '',
  isActive: true
});

// 按分组整理提供商
const groupedProviders = computed(() => {
  const groups: Record<string, ProviderInfo[]> = {
    international: [],
    national: [],
    other: [],
  };
  for (const p of availableProviders.value) {
    const g = p.group || 'other';
    if (groups[g]) groups[g].push(p);
    else groups.other.push(p);
  }
  return groups;
});

// 需要自定义端点地址的提供商
const needsEndpoint = computed(() =>
  ['azure', 'custom', 'wenxin', 'spark'].includes(form.provider)
);

// 各提供商推荐模型列表
const providerModels: Record<string, Array<{ label: string; value: string }>> = {
  openai: [
    { label: 'GPT-5.5 (最新)', value: 'gpt-5.5' },
    { label: 'GPT-5.4 Nano', value: 'gpt-5.4-nano' },
    { label: 'GPT-4o', value: 'gpt-4o' },
    { label: 'GPT-4o Mini', value: 'gpt-4o-mini' },
    { label: 'GPT-4.1', value: 'gpt-4.1' },
    { label: 'GPT-4.1 Mini', value: 'gpt-4.1-mini' },
    { label: 'GPT-4.1 Nano', value: 'gpt-4.1-nano' },
    { label: 'o3', value: 'o3' },
    { label: 'o4-mini', value: 'o4-mini' },
  ],
  anthropic: [
    { label: 'Claude Opus 4.7 (最新)', value: 'claude-opus-4-7' },
    { label: 'Claude Sonnet 4.6', value: 'claude-sonnet-4-6' },
    { label: 'Claude Haiku 4.5', value: 'claude-haiku-4-5-20251001' },
    { label: 'Claude 3.5 Sonnet', value: 'claude-3-5-sonnet-20241022' },
    { label: 'Claude 3.5 Haiku', value: 'claude-3-5-haiku-20241022' },
  ],
  deepseek: [
    { label: 'DeepSeek V4 Pro (最新)', value: 'deepseek-v4-pro' },
    { label: 'DeepSeek V4 Flash', value: 'deepseek-v4-flash' },
    { label: 'DeepSeek V3-0324', value: 'deepseek-v3-0324' },
    { label: 'DeepSeek R1-0528', value: 'deepseek-r1-0528' },
    { label: 'DeepSeek V3 (兼容别名)', value: 'deepseek-chat' },
    { label: 'DeepSeek R1 (兼容别名)', value: 'deepseek-reasoner' },
  ],
  qwen: [
    { label: 'Qwen3.5 Plus (最新)', value: 'qwen3.5-plus' },
    { label: 'Qwen3.5 Flash', value: 'qwen3.5-flash' },
    { label: 'Qwen3-235B-A22B', value: 'qwen3-235b-a22b' },
    { label: 'Qwen3-32B', value: 'qwen3-32b' },
    { label: 'Qwen3-14B', value: 'qwen3-14b' },
    { label: 'Qwen-Max', value: 'qwen-max' },
    { label: 'Qwen-Plus', value: 'qwen-plus' },
    { label: 'Qwen-Turbo', value: 'qwen-turbo' },
    { label: 'Qwen-Long', value: 'qwen-long' },
  ],
  wenxin: [
    { label: 'ERNIE-4.5-300B (最新)', value: 'ernie-4.5-300b-a47b' },
    { label: 'ERNIE-4.5-21B', value: 'ernie-4.5-21b-a3b' },
    { label: 'ERNIE-4.0-8K', value: 'ernie-4.0-8k' },
    { label: 'ERNIE-3.5-8K', value: 'ernie-3.5-8k' },
    { label: 'ERNIE Speed', value: 'ernie-speed-128k' },
  ],
  glm: [
    { label: 'GLM-5.1 (最新)', value: 'glm-5.1' },
    { label: 'GLM-4.7', value: 'glm-4.7' },
    { label: 'GLM-4.6', value: 'glm-4.6' },
    { label: 'GLM-4.5', value: 'glm-4.5' },
    { label: 'GLM-4-Flash', value: 'glm-4-flash' },
  ],
  spark: [
    { label: 'Spark 4.0 Ultra (最新)', value: 'spark4.0Ultra' },
    { label: 'Spark Max', value: 'spark-max' },
    { label: 'Spark Pro', value: 'spark-pro' },
    { label: 'Spark Lite', value: 'spark-lite' },
  ],
  moonshot: [
    { label: 'Kimi K2.6 (最新)', value: 'kimi-k2.6' },
    { label: 'Kimi K2.6 Thinking', value: 'kimi-k2.6-thinking' },
    { label: 'Moonshot v1-128K', value: 'moonshot-v1-128k' },
    { label: 'Moonshot v1-32K', value: 'moonshot-v1-32k' },
    { label: 'Moonshot v1-8K', value: 'moonshot-v1-8k' },
  ],
};

const modelOptions = computed(() => {
  const builtin = providerModels[form.provider] ?? []
  try {
    const custom = JSON.parse(localStorage.getItem('admin_custom_models') || '{}')
    const customList: Array<{ label: string; value: string }> = (custom[form.provider] || []).map(
      (id: string) => ({ label: `${id} (自定义)`, value: id })
    )
    // 去重：自定义中已存在于内置列表的不重复添加
    const builtinValues = new Set(builtin.map((m) => m.value))
    const newCustom = customList.filter((m) => !builtinValues.has(m.value))
    return [...builtin, ...newCustom]
  } catch {
    return builtin
  }
});

// 默认提供商列表（API请求失败时的降级方案）
const defaultProviders: ProviderInfo[] = [
  { id: 'openai', name: 'OpenAI', group: 'international' },
  { id: 'azure', name: 'Azure OpenAI', group: 'international' },
  { id: 'anthropic', name: 'Anthropic', group: 'international' },
  { id: 'deepseek', name: 'DeepSeek（深度求索）', group: 'national' },
  { id: 'qwen', name: '通义千问（阿里）', group: 'national' },
  { id: 'wenxin', name: '文心一言（百度）', group: 'national' },
  { id: 'glm', name: '智谱GLM', group: 'national' },
  { id: 'spark', name: '讯飞星火', group: 'national' },
  { id: 'moonshot', name: 'Moonshot（月之暗面）', group: 'national' },
  { id: 'custom', name: '自定义接入', group: 'other' },
];

const loadProviders = async () => {
  loadingProviders.value = true;
  try {
    const providers = await getAvailableProviders();
    availableProviders.value = providers.length > 0 ? providers : defaultProviders;
  } catch {
    availableProviders.value = defaultProviders;
  } finally {
    loadingProviders.value = false;
  }
};

const rules = computed<FormRules>(() => ({
  name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
  provider: [{ required: true, message: '请选择提供商', trigger: 'change' }],
  apiKey: [{ required: true, message: '请输入API密钥', trigger: 'blur' }],
  // endpoint 仅在需要时才校验 required
  ...(needsEndpoint.value
    ? { endpoint: [{ required: true, message: '请输入端点地址', trigger: 'blur' }] }
    : {}),
  model: [{ required: true, message: '请输入模型', trigger: 'blur' }]
}));

watch(() => props.modelValue, (val) => {
  if (val) Object.assign(form, val);
}, { immediate: true, deep: true });

watch(form, () => {
  emit('update:modelValue', { ...form });
}, { deep: true });

onMounted(() => {
  loadProviders();
});

const validate = () => formRef.value?.validate();

defineExpose({ validate });
</script>
