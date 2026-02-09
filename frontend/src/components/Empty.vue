<template>
  <div class="empty-state">
    <div class="empty-icon">
      <el-icon :size="60"><component :is="icon" /></el-icon>
    </div>
    <p class="empty-text">{{ title }}</p>
    <p class="empty-description">{{ description }}</p>
    <slot name="actions">
      <el-button v-if="showButton" type="primary" @click="handleClick">
        {{ buttonText }}
      </el-button>
    </slot>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { DataAnalysis, Search, FolderOpened, ShoppingCart } from '@element-plus/icons-vue'

interface Props {
  title?: string
  description?: string
  type?: 'empty' | 'search' | 'error' | 'cart'
  showButton?: boolean
  buttonText?: string
}

interface Emits {
  (e: 'action'): void
}

const props = withDefaults(defineProps<Props>(), {
  title: '暂无数据',
  description: '没有找到相关内容',
  type: 'empty',
  showButton: false,
  buttonText: '返回首页',
})

const emit = defineEmits<Emits>()

const icon = computed(() => {
  const icons: Record<string, any> = {
    empty: NoData,
    search: Search,
    error: DataAnalysis,
    cart: ShoppingCart,
  }
  return icons[props.type] || NoData
})

const handleClick = () => {
  emit('action')
}
</script>

<style scoped lang="scss">
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: #909399;

  .empty-icon {
    margin-bottom: 16px;
    color: #c0c4cc;
  }

  .empty-text {
    font-size: 16px;
    font-weight: 500;
    color: #606266;
    margin: 0 0 8px 0;
  }

  .empty-description {
    font-size: 14px;
    color: #909399;
    margin: 0 0 24px 0;
  }
}
</style>
