<template>
  <div class="model-config-panel">
    <el-card class="header-card">
      <h2>AI模型配置</h2>
      <p class="subtitle">配置企业使用的AI模型和API密钥</p>
    </el-card>

    <el-tabs v-model="activeTab">
      <!-- DeepSeek -->
      <el-tab-pane label="DeepSeek" name="deepseek">
        <ModelConfigForm
          :model-config="configs.deepseek"
          model-name="DeepSeek"
          :default-base-url="'https://api.deepseek.com/v1'"
          @save="saveConfig('deepseek', $event)"
        />
      </el-tab-pane>

      <!-- 千问 -->
      <el-tab-pane label="千问" name="qwen">
        <ModelConfigForm
          :model-config="configs.qwen"
          model-name="千问"
          :default-base-url="'https://dashscope.aliyuncs.com/compatible-mode/v1'"
          @save="saveConfig('qwen', $event)"
        />
      </el-tab-pane>

      <!-- 智谱 -->
      <el-tab-pane label="智谱AI" name="zhipu">
        <ModelConfigForm
          :model-config="configs.zhipu"
          model-name="智谱AI"
          :default-base-url="'https://open.bigmodel.cn/api/paas/v4'"
          @save="saveConfig('zhipu', $event)"
        />
      </el-tab-pane>

      <!-- 自定义（仅企业版） -->
      <el-tab-pane label="自定义模型" name="custom" v-if="isEnterprise">
        <ModelConfigForm
          :model-config="configs.custom"
          model-name="自定义模型"
          :allow-custom-url="true"
          @save="saveConfig('custom', $event)"
        />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import ModelConfigForm from './components/ModelConfigForm.vue'
import { getModelConfigs, saveModelConfig } from '@/api/modelConfig'

const activeTab = ref('deepseek')
const isEnterprise = ref(false)
const configs = ref({
  deepseek: null,
  qwen: null,
  zhipu: null,
  custom: null
})

onMounted(async () => {
  await loadConfigs()
  checkEnterpriseStatus()
})

const loadConfigs = async () => {
  try {
    const res = await getModelConfigs()
    configs.value = res.data
  } catch (error) {
    ElMessage.error('加载配置失败')
  }
}

const checkEnterpriseStatus = () => {
  // 检查是否企业版
  const tier = localStorage.getItem('quota_tier')
  isEnterprise.value = tier === 'enterprise_tier'
}

const saveConfig = async (provider, config) => {
  try {
    await saveModelConfig(provider, config)
    ElMessage.success('保存成功')
    await loadConfigs()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}
</script>

<style scoped>
.model-config-panel {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.subtitle {
  color: #666;
  margin-top: 8px;
}
</style>
