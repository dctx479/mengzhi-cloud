<template>
  <div class="template-selector">
    <!-- Template Categories -->
    <div class="template-categories">
      <div
        v-for="category in contentStore.templateCategories"
        :key="category.id"
        class="category-item"
        :class="{ active: isActiveCategory(category.id) }"
        @click="selectCategory(category.id)"
      >
        <div class="category-icon">{{ getCategoryIcon(category.id) }}</div>
        <div class="category-name">{{ category.name }}</div>
        <div class="category-count">{{ category.count }}</div>
      </div>
    </div>

    <!-- Template List -->
    <div class="template-list">
      <el-empty v-if="contentStore.templates.length === 0" description="No templates available" />

      <div v-else class="template-cards">
        <div
          v-for="template in filteredTemplates"
          :key="template.id"
          class="template-card"
          :class="{ selected: template.id === contentStore.selectedTemplate?.id }"
          @click="selectTemplate(template)"
        >
          <div class="template-preview">
            <div class="template-title">{{ template.name }}</div>
            <div class="template-description">{{ template.description }}</div>
            <div class="template-sample">
              <span class="sample-label">示例：</span>
              <span class="sample-text">{{ template.sample }}</span>
            </div>
          </div>

          <div class="template-meta">
            <el-tag :type="getDifficultyType(template.difficulty)" size="small">
              {{ getDifficultyLabel(template.difficulty) }}
            </el-tag>
            <span class="template-uses">使用 {{ template.usage_count }} 次</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useContentGenerationStore } from '@/stores/content-generation'
import { ElEmpty } from 'element-plus'
import type { TemplateCategory } from '@/types/content-generation'

const contentStore = useContentGenerationStore()

const activeCategory = computed(() => contentStore.selectedTemplate?.category)

const filteredTemplates = computed(() => {
  if (!activeCategory.value) {
    return contentStore.templates
  }
  return contentStore.templates.filter((t) => t.category === activeCategory.value)
})

const isActiveCategory = (category: string) => {
  return activeCategory.value === category
}

const selectCategory = (category: string) => {
  contentStore.selectCategory(category as TemplateCategory)
}

const selectTemplate = (template: any) => {
  contentStore.selectTemplate(template)
}

const getCategoryIcon = (category: string): string => {
  const iconMap: Record<string, string> = {
    product: '📝',
    slogan: '💡',
    marketing: '📊',
    social: '📱',
    video: '🎬',
  }
  return iconMap[category] || '📄'
}

const getDifficultyType = (difficulty: string): string => {
  const typeMap: Record<string, string> = {
    easy: 'success',
    medium: 'warning',
    hard: 'danger',
  }
  return typeMap[difficulty] || 'info'
}

const getDifficultyLabel = (difficulty: string): string => {
  const labelMap: Record<string, string> = {
    easy: '简单',
    medium: '中等',
    hard: '困难',
  }
  return labelMap[difficulty] || '未知'
}
</script>

<style scoped lang="scss">
.template-selector {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  border-radius: 4px;

  .template-categories {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 12px;
    padding: 16px;
    border-bottom: 1px solid #eee;
    background: #f9f9f9;

    .category-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 12px;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.3s ease;
      border: 2px solid transparent;

      &:hover {
        background: #f0f0f0;
        transform: translateY(-2px);
      }

      &.active {
        background: #e6f7ff;
        border-color: #1890ff;
        color: #1890ff;

        .category-icon {
          transform: scale(1.2);
        }
      }

      .category-icon {
        font-size: 24px;
        margin-bottom: 8px;
        transition: transform 0.3s ease;
      }

      .category-name {
        font-size: 12px;
        font-weight: 500;
        text-align: center;
        margin-bottom: 4px;
      }

      .category-count {
        font-size: 11px;
        color: #999;
      }
    }
  }

  .template-list {
    flex: 1;
    overflow-y: auto;
    padding: 16px;

    .template-cards {
      display: grid;
      gap: 12px;
      grid-template-columns: 1fr;
    }

    .template-card {
      padding: 12px;
      border: 2px solid #eee;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.3s ease;
      display: flex;
      flex-direction: column;

      &:hover {
        border-color: #1890ff;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
      }

      &.selected {
        border-color: #1890ff;
        background: #e6f7ff;

        .template-title {
          color: #1890ff;
          font-weight: 600;
        }
      }

      .template-preview {
        flex: 1;
        margin-bottom: 8px;

        .template-title {
          font-size: 14px;
          font-weight: 500;
          margin-bottom: 6px;
          color: #333;
        }

        .template-description {
          font-size: 12px;
          color: #666;
          margin-bottom: 8px;
          max-height: 40px;
          overflow: hidden;
          text-overflow: ellipsis;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
        }

        .template-sample {
          font-size: 11px;
          color: #999;
          background: #f5f5f5;
          padding: 6px;
          border-radius: 3px;
          max-height: 40px;
          overflow: hidden;

          .sample-label {
            font-weight: 500;
            color: #666;
          }

          .sample-text {
            color: #999;
          }
        }
      }

      .template-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 12px;

        .template-uses {
          color: #999;
        }
      }
    }
  }
}
</style>
