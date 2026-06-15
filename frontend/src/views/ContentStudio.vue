<template>
  <div class="content-studio-page">
    <!-- Page Header -->
    <div class="page-header">
      <h1>智能内容生成工作台</h1>
      <p class="subtitle">使用 AI 快速生成产品文案、广告语、营销方案等内容</p>
    </div>

    <!-- Tabs Navigation -->
    <el-tabs v-model="activeTab" class="content-tabs">
      <!-- Generation Tab -->
      <el-tab-pane name="generation" label="内容生成">
        <div class="generation-container">
          <!-- Left Sidebar - Template Selector -->
          <div class="sidebar">
            <h2>模板库</h2>
            <TemplateSelector />
          </div>

          <!-- Middle Panel - Configuration -->
          <div class="config-area">
            <h2>生成配置</h2>
            <ConfigPanel @batch-created="onBatchCreated" />
          </div>

          <!-- Right Panel - Results -->
          <div class="results-area">
            <h2>生成结果</h2>
            <ResultsPanel />
          </div>
        </div>
      </el-tab-pane>

      <!-- Batch Tasks Tab -->
      <el-tab-pane name="tasks" label="批量任务">
       <BatchTaskManager />
      </el-tab-pane>

      <!-- History Tab -->
      <el-tab-pane name="history" label="历史记录">
        <HistoryPanel />
      </el-tab-pane>

      <!-- Statistics Tab -->
      <el-tab-pane name="statistics" label="统计分析">
        <StatisticsPanel />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useContentGenerationStore } from '@/stores/content-generation'
import { useProductStore } from '@/stores/product'
import TemplateSelector from '@/components/TemplateSelector.vue'
import ConfigPanel from '@/components/ConfigPanel.vue'
import ResultsPanel from '@/components/ResultsPanel.vue'
import BatchTaskManager from '@/components/BatchTaskManager.vue'
    import HistoryPanel from '@/components/HistoryPanel.vue'
import StatisticsPanel from '@/components/StatisticsPanel.vue'

const contentStore = useContentGenerationStore()
const productStore = useProductStore()

const activeTab = ref('generation')

  const onBatchCreated = () => {
    activeTab.value = 'tasks'
  }

onMounted(async () => {
  try {
    await Promise.all([
      contentStore.fetchTemplates().catch((err) => {
        console.error('Failed to fetch templates:', err)
      }),
      contentStore.fetchSavedConfigs().catch((err) => {
        console.error('Failed to fetch saved configs:', err)
      }),
      productStore.fetchProducts().catch((err) => {
        console.error('Failed to fetch products:', err)
      }),
    ])
  } catch (err) {
    console.error('Error during component initialization:', err)
  }
})
</script>

<style scoped lang="scss">
.content-studio-page {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100vh;

  .page-header {
    margin-bottom: 24px;
    text-align: center;

    h1 {
      margin: 0 0 8px 0;
      font-size: 28px;
      font-weight: 600;
      color: #333;
    }

    .subtitle {
      margin: 0;
      font-size: 14px;
      color: #666;
    }
  }

  .content-tabs {
    :deep(.el-tabs__header) {
      background: #fff;
      margin-bottom: 0;
      border-bottom: 2px solid #eee;
    }

    :deep(.el-tabs__content) {
      padding: 16px;
      background: #fff;
    }
  }

  .generation-container {
    display: grid;
    grid-template-columns: 280px 1fr 1fr;
    gap: 16px;
    min-height: calc(100vh - 300px);
    max-height: calc(100vh - 200px);

    @media (max-width: 1400px) {
      grid-template-columns: 250px 1fr 1fr;
      gap: 12px;
    }

    @media (max-width: 1024px) {
      grid-template-columns: 1fr;
      max-height: none;

      .sidebar {
        display: none;
      }
    }

    .sidebar {
      background: #fff;
      border-radius: 8px;
      padding: 16px;
      overflow-y: auto;
      min-width: 0;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);

      h2 {
        margin: 0 0 16px 0;
        font-size: 16px;
        font-weight: 600;
      }
    }

    .config-area {
      background: #fff;
      border-radius: 8px;
      padding: 16px;
      overflow-y: auto;
      min-width: 0;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);

      h2 {
        margin: 0 0 16px 0;
        font-size: 16px;
        font-weight: 600;
      }
    }

    .results-area {
      background: #fff;
      border-radius: 8px;
      padding: 16px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      min-width: 0;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);

      h2 {
        margin: 0 0 16px 0;
        font-size: 16px;
        font-weight: 600;
      }
    }
  }
}
</style>
