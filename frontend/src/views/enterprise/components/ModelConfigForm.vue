<template>
  <el-form :model="form" label-width="120px">
    <el-form-item label="启用状态">
      <el-switch v-model="form.enabled" />
    </el-form-item>

    <el-form-item label="API密钥" required>
      <el-input
        v-model="form.api_key"
        type="password"
        show-password
        placeholder="请输入API密钥"
      />
      <div class="help-text">密钥将加密存储，仅用于调用AI服务</div>
    </el-form-item>

    <el-form-item label="Base URL">
      <el-input
        v-model="form.base_url"
        :placeholder="defaultBaseUrl"
        :disabled="!allowCustomUrl"
      />
      <div class="help-text" v-if="!allowCustomUrl">
        默认地址：{{ defaultBaseUrl }}
      </div>
      <div class="help-text" v-else>
        自定义模型可配置Base URL
      </div>
    </el-form-item>

    <el-form-item label="模型名称" v-if="allowCustomUrl">
      <el-input
        v-model="form.model_name"
        placeholder="如：gpt-3.5-turbo"
      />
    </el-form-item>

    <el-form-item label="优先级">
      <el-input-number v-model="form.priority" :min="1" :max="10" />
      <div class="help-text">数字越小优先级越高</div>
    </el-form-item>

    <el-form-item>
      <el-button type="primary" @click="handleSave">保存配置</el-button>
      <el-button @click="handleTest">测试连接</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelConfig: Object,
  modelName: String,
  defaultBaseUrl: String,
  allowCustomUrl: Boolean
})

const emit = defineEmits(['save'])

const form = ref({
  enabled: false,
  api_key: '',
  base_url: '',
  model_name: '',
  priority: 5
})

watch(() => props.modelConfig, (config) => {
  if (config) {
    form.value = { ...config }
  }
}, { immediate: true })

const handleSave = () => {
  if (!form.value.api_key) {
    ElMessage.error('请输入API密钥')
    return
  }

  emit('save', form.value)
}

const handleTest = async () => {
  ElMessage.info('当前页面暂不支持测试连接，请前往企业AI配置页使用测试功能')
}
</script>

<style scoped>
.help-text {
  color: #999;
  font-size: 12px;
  margin-top: 4px;
}
</style>
