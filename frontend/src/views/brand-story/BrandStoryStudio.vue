<template>
  <div class="brand-story-page">
    <div class="page-header">
      <h1>品牌故事工作台</h1>
      <p class="subtitle">使用 AI 结合文化元素，快速生成有温度的品牌故事</p>
    </div>

    <el-tabs v-model="activeTab" class="brand-story-tabs">
      <!-- 生成 -->
      <el-tab-pane name="generate" label="故事生成">
        <div class="generate-container">
          <!-- 左侧: 生成表单 -->
          <div class="form-area" v-loading="generating">
            <h2>生成表单</h2>
            <el-form
              ref="formRef"
              :model="form"
              :rules="rules"
              label-width="110px"
            >
              <el-form-item label="产品名称" prop="product_name">
                <el-input v-model="form.product_name" placeholder="请输入产品名称" maxlength="100" />
              </el-form-item>

              <el-form-item label="产地" prop="origin">
                <el-input v-model="form.origin" placeholder="请输入产地" maxlength="100" />
              </el-form-item>

              <el-form-item label="产品特点">
                <el-input
                  v-model="form.features"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入产品特点（可选）"
                />
              </el-form-item>

              <el-form-item label="用途">
                <el-input v-model="form.purpose" placeholder="电商详情页" />
              </el-form-item>

              <el-form-item label="风格">
                <el-select v-model="form.style" placeholder="选择风格">
                  <el-option label="现代简约" value="现代简约" />
                  <el-option label="传统深沉" value="传统深沉" />
                  <el-option label="情感共鸣" value="情感共鸣" />
                </el-select>
              </el-form-item>

              <el-form-item label="字数">
                <el-input v-model="form.word_count" placeholder="300字左右" />
              </el-form-item>

              <el-form-item label="类别">
                <el-input v-model="form.category" placeholder="请输入类别（可选）" />
              </el-form-item>

              <el-form-item label="关键词">
                <el-input v-model="keywordsInput" placeholder="多个关键词用逗号分隔" />
              </el-form-item>

              <el-form-item label="使用文化元素">
                <el-switch v-model="form.use_culture" />
              </el-form-item>

              <el-form-item label="保存记录">
                <el-switch v-model="form.save_record" />
              </el-form-item>

              <el-form-item label="自动生成封面图">
                <el-switch v-model="form.auto_generate_image" />
              </el-form-item>

              <el-form-item>
                <el-button type="primary" :loading="generating" @click="handleGenerate">
                  <el-icon v-if="!generating"><MagicStick /></el-icon>
                  生成
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 右侧: 结果展示 -->
          <div class="result-area">
            <div class="result-header">
              <h2>结果展示</h2>
              <el-button
                v-if="result"
                size="small"
                @click="copyStory"
              >
                <el-icon><CopyDocument /></el-icon>
                复制
              </el-button>
            </div>

            <el-empty v-if="!result" description="尚未生成，请填写左侧表单后点击生成" />

            <template v-else>
              <el-card class="story-card" shadow="never">
                <div class="story-text">{{ result.story }}</div>
              </el-card>

              <div v-if="result.cultural_elements && result.cultural_elements.length" class="culture-tags">
                <span class="block-label">匹配文化元素</span>
                <el-tag
                  v-for="(el, idx) in result.cultural_elements"
                  :key="idx"
                  type="success"
                  class="culture-tag"
                >
                  {{ el }}
                </el-tag>
              </div>

              <el-descriptions :column="2" border class="stat-desc">
                <el-descriptions-item label="输入 Token">
                  {{ result.tokens?.input ?? '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="输出 Token">
                  {{ result.tokens?.output ?? '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="总 Token">
                  {{ result.tokens?.total ?? '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="成本">
                  {{ formatCost(result.cost) }}
                </el-descriptions-item>
              </el-descriptions>

              <div v-if="result.image_url" class="cover-image">
                <span class="block-label">封面图</span>
                <el-image
                  :src="result.image_url"
                  :preview-src-list="[result.image_url]"
                  fit="cover"
                  class="cover"
                />
              </div>
            </template>
          </div>
        </div>
      </el-tab-pane>

      <!-- 历史记录 -->
      <el-tab-pane name="history" label="历史记录">
        <div class="history-area">
          <div class="history-header">
            <el-button size="small" :loading="historyLoading" @click="loadHistory">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>

          <el-table :data="records" v-loading="historyLoading" stripe>
            <el-table-column prop="product_name" label="产品名称" min-width="140" show-overflow-tooltip />
            <el-table-column prop="origin" label="产地" width="120" show-overflow-tooltip />
            <el-table-column prop="style" label="风格" width="110" />
            <el-table-column prop="tokens_used" label="字数/Tokens" width="120" />
            <el-table-column label="成本" width="110">
              <template #default="{ row }">{{ formatCost(row.cost) }}</template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" min-width="170" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.created_at ? new Date(row.created_at).toLocaleString('zh-CN') : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'completed' ? 'success' : 'danger'" size="small">
                  {{ row.status === 'completed' ? '已完成' : row.status === 'failed' ? '失败' : row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="viewRecord(row.id)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 历史详情对话框 -->
    <el-dialog v-model="detailVisible" title="故事详情" width="640px">
      <div v-loading="detailLoading">
        <template v-if="detailRecord">
          <el-descriptions :column="2" border class="detail-desc">
            <el-descriptions-item label="产品名称">{{ detailRecord.product_name }}</el-descriptions-item>
            <el-descriptions-item label="产地">{{ detailRecord.origin }}</el-descriptions-item>
            <el-descriptions-item label="风格">{{ detailRecord.style }}</el-descriptions-item>
            <el-descriptions-item label="字数/Tokens">{{ detailRecord.tokens_used }}</el-descriptions-item>
            <el-descriptions-item label="成本">{{ formatCost(detailRecord.cost) }}</el-descriptions-item>
            <el-descriptions-item label="状态">{{ detailRecord.status === 'completed' ? '已完成' : detailRecord.status === 'failed' ? '失败' : detailRecord.status }}</el-descriptions-item>
          </el-descriptions>

          <div
            v-if="detailRecord.cultural_elements && detailRecord.cultural_elements.length"
            class="culture-tags"
          >
            <span class="block-label">文化元素</span>
            <el-tag
              v-for="(el, idx) in detailRecord.cultural_elements"
              :key="idx"
              type="success"
              class="culture-tag"
            >
              {{ el }}
            </el-tag>
          </div>

          <el-card class="story-card" shadow="never">
            <div class="story-text">{{ detailRecord.story }}</div>
          </el-card>
        </template>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { MagicStick, CopyDocument, Refresh } from '@element-plus/icons-vue'
import {
  generateBrandStory,
  getBrandStoryRecords,
  getBrandStoryRecord,
  type BrandStoryRequest,
  type BrandStoryResponse,
  type BrandStoryRecord,
} from '@/api/brandStory'

const activeTab = ref('generate')

const formRef = ref<FormInstance>()
const generating = ref(false)
const keywordsInput = ref('')

const form = reactive<BrandStoryRequest>({
  product_name: '',
  origin: '',
  features: '',
  purpose: '电商详情页',
  style: '现代简约',
  word_count: '300字左右',
  category: '',
  keywords: [],
  use_culture: true,
  save_record: true,
  auto_generate_image: false,
})

const rules: FormRules = {
  product_name: [{ required: true, message: '请输入产品名称', trigger: 'blur' }],
  origin: [{ required: true, message: '请输入产地', trigger: 'blur' }],
}

const result = ref<BrandStoryResponse | null>(null)

const records = ref<BrandStoryRecord[]>([])
const historyLoading = ref(false)

const detailVisible = ref(false)
const detailLoading = ref(false)
const detailRecord = ref<BrandStoryRecord | null>(null)

const formatCost = (cost?: number): string => {
  if (cost === undefined || cost === null) return '-'
  return `¥${cost.toFixed(4)}`
}

const parseKeywords = (): string[] =>
  keywordsInput.value
    .split(/[,，]/)
    .map((k) => k.trim())
    .filter((k) => k.length > 0)

const handleGenerate = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  generating.value = true
  try {
    const payload: BrandStoryRequest = {
      ...form,
      keywords: parseKeywords(),
    }
    result.value = await generateBrandStory(payload)
    ElMessage.success('生成成功')
    if (form.save_record) {
      loadHistory()
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '生成失败')
  } finally {
    generating.value = false
  }
}

const copyStory = async () => {
  if (!result.value) return
  try {
    await navigator.clipboard.writeText(result.value.story)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

const loadHistory = async () => {
  historyLoading.value = true
  try {
    records.value = await getBrandStoryRecords(0, 20)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载历史记录失败')
  } finally {
    historyLoading.value = false
  }
}

const viewRecord = async (recordId: number) => {
  detailVisible.value = true
  detailLoading.value = true
  detailRecord.value = null
  try {
    detailRecord.value = await getBrandStoryRecord(recordId)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载记录详情失败')
  } finally {
    detailLoading.value = false
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.brand-story-page {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
  text-align: center;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: #333;
}

.page-header .subtitle {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.brand-story-tabs :deep(.el-tabs__content) {
  padding: 16px;
  background: #fff;
}

.generate-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  align-items: start;
}

@media (max-width: 1024px) {
  .generate-container {
    grid-template-columns: 1fr;
  }
}

.form-area,
.result-area {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.form-area h2,
.result-area h2 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.story-card {
  margin-bottom: 16px;
  background: #fafafa;
}

.story-text {
  white-space: pre-wrap;
  line-height: 1.8;
  font-size: 14px;
  color: #333;
}

.block-label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  color: #909399;
}

.culture-tags {
  margin-bottom: 16px;
}

.culture-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

.stat-desc {
  margin-bottom: 16px;
}

.cover-image .cover {
  width: 100%;
  max-width: 320px;
  border-radius: 8px;
}

.history-header {
  margin-bottom: 12px;
  display: flex;
  justify-content: flex-end;
}

.detail-desc {
  margin-bottom: 16px;
}
</style>
