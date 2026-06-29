<template>
  <div class="cultural-elements">
    <el-tabs v-model="activeTab">
      <!-- Tab 1: 元素库 -->
      <el-tab-pane label="元素库" name="library">
        <el-card>
          <div class="filter-bar">
            <el-input
              v-model="filters.keyword"
              placeholder="搜索关键词/名称"
              clearable
              style="width: 220px"
              @keyup.enter="onSearch"
            />
            <el-select
              v-model="filters.type"
              placeholder="类型"
              clearable
              style="width: 160px"
            >
              <el-option label="非遗技艺" value="craft" />
              <el-option label="历史典故" value="story" />
              <el-option label="民俗文化" value="folklore" />
              <el-option label="地域特产" value="specialty" />
              <el-option label="艺术形式" value="art" />
            </el-select>
            <el-button type="primary" @click="onSearch">查询</el-button>
          </div>

          <el-table :data="elements" v-loading="listLoading" @row-click="openDetail">
            <el-table-column prop="name" label="名称" min-width="140" />
            <el-table-column prop="type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag size="small">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="origin_region" label="地域" width="140" />
            <el-table-column prop="story_preview" label="故事预览" min-width="220" show-overflow-tooltip />
            <el-table-column label="关键词" min-width="180">
              <template #default="{ row }">
                <el-tag
                  v-for="kw in row.keywords"
                  :key="kw"
                  size="small"
                  type="info"
                  class="kw-tag"
                >
                  {{ kw }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'approved' ? 'success' : 'warning'" size="small">
                  {{ row.status === 'approved' ? '已审核' : row.status === 'pending' ? '待审核' : '已拒绝' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click.stop="openDetail(row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            style="margin-top: 16px; display: flex; justify-content: flex-end"
            @change="loadElements"
          />
        </el-card>
      </el-tab-pane>

      <!-- Tab 2: 智能匹配 -->
      <el-tab-pane label="智能匹配" name="match">
        <el-card>
          <el-form :model="matchForm" label-width="120px" class="match-form">
            <el-form-item label="产品名称" required>
              <el-input v-model="matchForm.product_name" placeholder="例如：手工蜡染围巾" />
            </el-form-item>
            <el-form-item label="产地">
              <el-input v-model="matchForm.origin" placeholder="例如：贵州" />
            </el-form-item>
            <el-form-item label="类别">
              <el-input v-model="matchForm.category" placeholder="例如：服饰" />
            </el-form-item>
            <el-form-item label="关键词">
              <el-input v-model="keywordsInput" placeholder="逗号分隔，例如：蜡染,苗族,手工" />
            </el-form-item>
            <el-form-item label="使用知识图谱">
              <el-switch v-model="matchForm.use_knowledge_graph" />
            </el-form-item>
            <el-form-item label="返回数量">
              <el-input-number v-model="matchForm.top_k" :min="1" :max="20" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="matchLoading" @click="onMatch">匹配</el-button>
            </el-form-item>
          </el-form>

          <el-table v-if="matchResults.length" :data="matchResults" class="match-results">
            <el-table-column label="名称" min-width="140">
              <template #default="{ row }">{{ row.element.name }}</template>
            </el-table-column>
            <el-table-column label="类型" width="120">
              <template #default="{ row }">
                <el-tag size="small">{{ row.element.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="得分" width="100">
              <template #default="{ row }">{{ row.score.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="match_reason" label="匹配原因" min-width="200" show-overflow-tooltip />
            <el-table-column label="得分构成" min-width="180">
              <template #default="{ row }">
                精确: {{ row.score_breakdown.exact_match.toFixed(2) }} /
                图谱: {{ row.score_breakdown.knowledge_graph.toFixed(2) }}
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else-if="matched" description="无匹配结果" />
        </el-card>
      </el-tab-pane>

      <!-- Tab 3: 统计概览 -->
      <el-tab-pane label="统计概览" name="overview">
        <el-card v-loading="overviewLoading">
          <div v-if="overview" class="overview">
            <div class="stat-row">
              <el-statistic title="元素总数" :value="overview.elements.total" />
              <el-statistic title="已审核" :value="overview.elements.approved" />
              <el-statistic title="待审核" :value="overview.elements.pending" />
            </div>
            <div class="stat-row">
              <el-statistic title="任务总数" :value="overview.tasks.total" />
              <el-statistic title="已完成" :value="overview.tasks.completed" />
              <el-statistic title="成功率" :value="overview.tasks.success_rate" suffix="%" />
            </div>
            <div class="by-type">
              <h4>按类型分布</h4>
              <el-tag
                v-for="(count, type) in overview.by_type"
                :key="type"
                class="type-tag"
              >
                {{ type }}: {{ count }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" :title="detail?.name || '元素详情'" width="640px">
      <div v-if="detail" v-loading="detailLoading" class="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="类型">{{ detail.type }}</el-descriptions-item>
          <el-descriptions-item label="地域">{{ detail.origin_region }}</el-descriptions-item>
          <el-descriptions-item label="来源">{{ detail.source }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ detail.status === 'approved' ? '已审核' : detail.status === 'pending' ? '待审核' : '已拒绝' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ detail.created_at ? new Date(detail.created_at).toLocaleString('zh-CN') : '-' }}</el-descriptions-item>
          <el-descriptions-item label="审核时间">{{ detail.reviewed_at ? new Date(detail.reviewed_at).toLocaleString('zh-CN') : '未审核' }}</el-descriptions-item>
        </el-descriptions>
        <div class="detail-section">
          <h4>关键词</h4>
          <el-tag v-for="kw in detail.keywords" :key="kw" size="small" type="info" class="kw-tag">
            {{ kw }}
          </el-tag>
        </div>
        <div class="detail-section">
          <h4>故事</h4>
          <p class="story-text">{{ detail.story }}</p>
        </div>
        <div class="detail-section">
          <h4>元数据</h4>
          <pre class="metadata">{{ JSON.stringify(detail.metadata, null, 2) }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getElements,
  getElementDetail,
  matchElements,
  getStatisticsOverview,
  type CulturalElement,
  type CulturalElementDetail,
  type MatchedElement,
  type StatisticsOverview,
} from '@/api/cultural'

const activeTab = ref('library')

// 元素库
const elements = ref<CulturalElement[]>([])
const listLoading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filters = reactive<{ keyword: string; type: string }>({ keyword: '', type: '' })

const loadElements = async () => {
  listLoading.value = true
  try {
    const result = await getElements({
      keyword: filters.keyword || undefined,
      type: filters.type || undefined,
      page: currentPage.value,
      page_size: pageSize.value,
    })
    elements.value = result.elements
    total.value = result.pagination.total
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载失败')
  } finally {
    listLoading.value = false
  }
}

const onSearch = () => {
  currentPage.value = 1
  loadElements()
}

// 详情
const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref<CulturalElementDetail | null>(null)

const openDetail = async (row: CulturalElement) => {
  detailVisible.value = true
  detailLoading.value = true
  detail.value = null
  try {
    detail.value = await getElementDetail(row.id)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载失败')
  } finally {
    detailLoading.value = false
  }
}

// 智能匹配
const matchForm = reactive<{
  product_name: string
  origin: string
  category: string
  use_knowledge_graph: boolean
  top_k: number
}>({
  product_name: '',
  origin: '',
  category: '',
  use_knowledge_graph: true,
  top_k: 3,
})
const keywordsInput = ref('')
const matchResults = ref<MatchedElement[]>([])
const matchLoading = ref(false)
const matched = ref(false)

const onMatch = async () => {
  if (!matchForm.product_name) {
    ElMessage.warning('请填写产品名称')
    return
  }
  matchLoading.value = true
  try {
    const keywords = keywordsInput.value
      .split(',')
      .map((k) => k.trim())
      .filter((k) => k)
    const result = await matchElements({
      product_name: matchForm.product_name,
      origin: matchForm.origin || undefined,
      category: matchForm.category || undefined,
      keywords: keywords.length ? keywords : undefined,
      use_knowledge_graph: matchForm.use_knowledge_graph,
      top_k: matchForm.top_k,
    })
    matchResults.value = result.matched_elements
    matched.value = true
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '匹配失败')
  } finally {
    matchLoading.value = false
  }
}

// 统计概览
const overview = ref<StatisticsOverview | null>(null)
const overviewLoading = ref(false)

const loadOverview = async () => {
  overviewLoading.value = true
  try {
    overview.value = await getStatisticsOverview()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载失败')
  } finally {
    overviewLoading.value = false
  }
}

onMounted(() => {
  loadElements()
  loadOverview()
})
</script>

<style scoped>
.cultural-elements {
  padding: 20px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.kw-tag {
  margin-right: 4px;
  margin-bottom: 4px;
}

.match-form {
  max-width: 520px;
}

.match-results {
  margin-top: 16px;
}

.overview .stat-row {
  display: flex;
  gap: 48px;
  margin-bottom: 24px;
}

.by-type {
  margin-top: 16px;
}

.type-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

.detail-section {
  margin-top: 16px;
}

.detail-section h4 {
  margin: 8px 0;
}

.story-text {
  line-height: 1.6;
  white-space: pre-wrap;
}

.metadata {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
}
</style>
