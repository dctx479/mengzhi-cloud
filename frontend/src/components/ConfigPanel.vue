<template>
  <div class="config-panel">
    <el-form :model="contentStore.config" label-width="100px">
      <!-- Product Selection -->
      <el-form-item label="选择产品" required>
        <el-select
          v-model="contentStore.config.product_ids"
          multiple
          filterable
          placeholder="选择产品"
          style="width: 100%"
        >
          <el-option
            v-for="product in products"
            :key="product.id"
            :label="product.name"
            :value="product.id"
          >
            <div class="product-option">
              <img v-if="product.image" :src="product.image" class="product-thumb" alt="product" />
              <span>{{ product.name }}</span>
            </div>
          </el-option>
        </el-select>
        <span class="form-hint">已选择 {{ contentStore.config.product_ids.length }} 个产品</span>
      </el-form-item>

      <!-- Generation Count -->
      <el-form-item label="生成数量">
        <div style="display: flex; gap: 8px; align-items: center">
          <el-input-number
            v-model="contentStore.config.count"
            :min="1"
            :max="10"
            style="flex: 1"
          />
          <span class="form-hint">最多生成10个版本</span>
        </div>
      </el-form-item>

      <!-- Content Style -->
      <el-form-item label="文案风格">
        <el-radio-group v-model="contentStore.config.style" style="width: 100%">
          <el-radio label="professional">专业</el-radio>
          <el-radio label="casual">轻松</el-radio>
          <el-radio label="emotional">感性</el-radio>
          <el-radio label="creative">创意</el-radio>
        </el-radio-group>
      </el-form-item>

      <!-- Word Count -->
      <el-form-item label="字数">
        <el-slider
          v-model="contentStore.config.word_count"
          :min="50"
          :max="500"
          :step="50"
          show-stops
          style="margin-bottom: 8px"
        />
        <div class="range-label">{{ contentStore.config.word_count }} 字</div>
      </el-form-item>

      <!-- Target Audience -->
      <el-form-item label="目标受众">
        <el-checkbox-group v-model="contentStore.config.target_audience" style="width: 100%">
          <el-checkbox label="urban">城市白领</el-checkbox>
          <el-checkbox label="family">家庭主妇</el-checkbox>
          <el-checkbox label="health">健康人群</el-checkbox>
          <el-checkbox label="gourmet">美食爱好者</el-checkbox>
        </el-checkbox-group>
      </el-form-item>

      <!-- Keywords -->
      <el-form-item label="关键词">
        <div class="keyword-input-group">
          <div class="keyword-tags">
            <el-tag
              v-for="tag in contentStore.config.keywords"
              :key="tag"
              closable
              @close="contentStore.removeKeyword(tag)"
            >
              {{ tag }}
            </el-tag>
          </div>
          <div style="margin-top: 8px">
            <el-input
              v-if="keywordInputVisible"
              ref="keywordInputRef"
              v-model="keywordInput"
              size="small"
              placeholder="输入关键词，按Enter确认"
              style="width: 150px"
              @keyup.enter="handleKeywordConfirm"
              @blur="handleKeywordConfirm"
            />
            <el-button v-else size="small" @click="showKeywordInput"> + 新标签 </el-button>
          </div>
        </div>
      </el-form-item>

      <!-- Advanced Options -->
      <el-collapse v-model="advancedOpen" style="margin-bottom: 16px">
        <el-collapse-item title="高级选项" name="1">
          <!-- Avoid Words -->
          <el-form-item label="避免词汇" style="margin-bottom: 16px">
            <el-input
              v-model="contentStore.config.avoid_words"
              type="textarea"
              :rows="2"
              placeholder="用逗号分隔，如：销售，促销"
            />
          </el-form-item>

          <!-- Temperature -->
          <el-form-item label="创意温度">
            <div style="display: flex; gap: 12px; align-items: center; width: 100%">
              <el-slider
                v-model="contentStore.config.temperature"
                :min="0"
                :max="1"
                :step="0.1"
                :show-tooltip="true"
                style="flex: 1; min-width: 200px"
              />
              <el-input-number
                v-model="contentStore.config.temperature"
                :min="0"
                :max="1"
                :step="0.1"
                :precision="1"
                :controls="true"
                size="small"
                style="width: 120px"
              />
            </div>
            <span class="form-hint">数值越高，创意性越强；越低，越严谨</span>
          </el-form-item>
        </el-collapse-item>
      </el-collapse>

      <!-- Action Buttons -->
      <el-form-item>
        <div style="display: flex; gap: 8px">
          <el-button
            type="primary"
            size="large"
            icon="MagicStick"
            :loading="contentStore.generating"
            :disabled="contentStore.config.product_ids.length === 0 || !contentStore.selectedTemplate"
            @click="handleGenerate"
            style="flex: 1"
          >
            {{ contentStore.generating ? '正在生成...' : '生成内容' }}
          </el-button>
          <el-button
            size="large"
            icon="Delete"
            :disabled="contentStore.config.product_ids.length === 0"
            @click="resetConfig"
          >
            重置
          </el-button>
        </div>
      </el-form-item>

      <!-- Save Configuration -->
      <el-form-item v-if="contentStore.hasResults">
        <el-button style="width: 100%" @click="showSaveDialog">
          💾 保存当前配置
        </el-button>
      </el-form-item>

      <!-- Load Configuration -->
      <el-form-item v-if="contentStore.savedConfigs.length > 0">
        <el-select
          placeholder="加载已保存的配置"
          style="width: 100%"
          @change="handleLoadConfig"
        >
          <el-option
            v-for="config in contentStore.savedConfigs"
            :key="config.id"
            :label="config.name"
            :value="config.id"
          />
        </el-select>
      </el-form-item>
    </el-form>

    <!-- Save Dialog -->
    <el-dialog v-model="saveDialogVisible" title="保存配置" width="400px">
      <el-input
        v-model="configName"
        placeholder="请输入配置名称"
        @keyup.enter="handleSaveConfig"
      />
      <template #footer>
        <el-button @click="saveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveConfig">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useProductStore } from '@/stores/product'
import { useContentGenerationStore } from '@/stores/content-generation'

const contentStore = useContentGenerationStore()
const productStore = useProductStore()

const keywordInputVisible = ref(false)
const keywordInput = ref('')
const keywordInputRef = ref()
const advancedOpen = ref([])

const saveDialogVisible = ref(false)
const configName = ref('')

const products = computed(() => productStore.products)

const showKeywordInput = async () => {
  keywordInputVisible.value = true
  await nextTick()
  keywordInputRef.value?.focus()
}

const handleKeywordConfirm = () => {
  const trimmed = keywordInput.value.trim()
  if (trimmed) {
    contentStore.addKeyword(trimmed)
    keywordInput.value = ''
  }
  keywordInputVisible.value = false
}

const handleGenerate = async () => {
  if (!contentStore.selectedTemplate) {
    ElMessage.error('请先选择模板')
    return
  }

  if (contentStore.config.product_ids.length === 0) {
    ElMessage.error('请至少选择一个产品')
    return
  }

  await contentStore.generateContent()
  if (!contentStore.generationError) {
    ElMessage.success('内容生成成功')
  } else {
    ElMessage.error(contentStore.generationError)
  }
}

const resetConfig = () => {
  contentStore.resetConfig()
  ElMessage.info('配置已重置')
}

const showSaveDialog = () => {
  configName.value = ''
  saveDialogVisible.value = true
}

const handleSaveConfig = async () => {
  const name = configName.value.trim()
  if (!name) {
    ElMessage.error('请输入配置名称')
    return
  }

  await contentStore.saveConfiguration(name)
  saveDialogVisible.value = false
  ElMessage.success('配置保存成功')
}

const handleLoadConfig = async (configId: string) => {
  await contentStore.loadSavedConfig(configId)
  ElMessage.success('配置已加载')
}
</script>

<style scoped lang="scss">
.config-panel {
  background: #fff;
  padding: 16px;
  border-radius: 4px;

  .form-hint {
    font-size: 12px;
    color: #999;
    margin-left: 8px;
  }

  .range-label {
    font-size: 12px;
    color: #666;
    margin-top: 8px;
  }

  .keyword-input-group {
    .keyword-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      margin-bottom: 8px;

      :deep(.el-tag) {
        margin-right: 0;
      }
    }
  }

  :deep(.el-collapse) {
    border: 1px solid #eee;
  }

  :deep(.el-form-item) {
    margin-bottom: 16px;
  }
}
</style>
