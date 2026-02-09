<template>
  <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
    <el-form-item label="配置名称" prop="name">
      <el-input v-model="form.name" placeholder="请输入配置名称" />
    </el-form-item>

    <el-form-item label="AI提供商" prop="provider">
      <el-select v-model="form.provider" placeholder="请选择提供商" style="width: 100%">
        <el-option label="OpenAI" value="openai" />
        <el-option label="Azure OpenAI" value="azure" />
        <el-option label="Anthropic" value="anthropic" />
        <el-option label="自定义" value="custom" />
      </el-select>
    </el-form-item>

    <el-form-item label="API密钥" prop="apiKey">
      <el-input v-model="form.apiKey" type="password" show-password placeholder="请输入API密钥" />
    </el-form-item>

    <el-form-item label="端点地址" prop="endpoint" v-if="form.provider === 'azure' || form.provider === 'custom'">
      <el-input v-model="form.endpoint" placeholder="请输入端点地址" />
    </el-form-item>

    <el-form-item label="模型" prop="model">
      <el-input v-model="form.model" placeholder="例如: gpt-4, claude-3-opus" />
    </el-form-item>

    <el-form-item label="启用状态">
      <el-switch v-model="form.isActive" />
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import type { AIConfigForm } from '@/types/aiConfig';

const props = defineProps<{
  modelValue?: AIConfigForm;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: AIConfigForm];
}>();

const formRef = ref<FormInstance>();

const form = reactive<AIConfigForm>({
  name: '',
  provider: 'openai',
  apiKey: '',
  endpoint: '',
  model: '',
  isActive: true
});

const rules: FormRules = {
  name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
  provider: [{ required: true, message: '请选择提供商', trigger: 'change' }],
  apiKey: [{ required: true, message: '请输入API密钥', trigger: 'blur' }],
  endpoint: [{ required: true, message: '请输入端点地址', trigger: 'blur' }],
  model: [{ required: true, message: '请输入模型', trigger: 'blur' }]
};

watch(() => props.modelValue, (val) => {
  if (val) Object.assign(form, val);
}, { immediate: true, deep: true });

watch(form, () => {
  emit('update:modelValue', { ...form });
}, { deep: true });

const validate = () => formRef.value?.validate();

defineExpose({ validate });
</script>
