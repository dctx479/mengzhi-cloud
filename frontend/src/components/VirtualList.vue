<!--
虚拟滚动列表组件 - BUG-033修复

支持大量数据的高性能渲染
只渲染可见区域的元素

版本: 1.0
创建日期: 2026-01-17
-->

<template>
  <div 
    ref="containerRef" 
    class="virtual-list" 
    @scroll="handleScroll"
    :style="{ height: containerHeight + 'px', overflow: 'auto' }"
  >
    <div 
      class="virtual-list-phantom"
      :style="{ height: totalHeight + 'px', position: 'relative' }"
    >
      <div
        class="virtual-list-content"
        :style="{ transform: `translateY(${offsetY}px)` }"
      >
        <div
          v-for="item in visibleItems"
          :key="getItemKey(item)"
          class="virtual-list-item"
          :style="{ height: itemHeight + 'px' }"
        >
          <slot :item="item" :index="item._index"></slot>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

// 定义Props
interface Props {
  items: any[]  // 数据列表
  itemHeight: number  // 每项的高度（px）
  containerHeight?: number  // 容器高度（px）,默认500px
  buffer?: number  // 缓冲区项数，默认5
  itemKey?: string  // item的唯一标识字段，默认'id'
}

const props = withDefaults(defineProps<Props>(), {
  containerHeight: 500,
  buffer: 5,
  itemKey: 'id'
})

// 引用
const containerRef = ref<HTMLElement>()
const scrollTop = ref(0)

// 计算总高度
const totalHeight = computed(() => {
  return props.items.length * props.itemHeight
})

// 计算可见项数量
const visibleCount = computed(() => {
  return Math.ceil(props.containerHeight / props.itemHeight)
})

// 计算起始索引
const startIndex = computed(() => {
  const index = Math.floor(scrollTop.value / props.itemHeight)
  return Math.max(0, index - props.buffer)
})

// 计算结束索引
const endIndex = computed(() => {
  const index = startIndex.value + visibleCount.value
  return Math.min(props.items.length, index + props.buffer)
})

// 计算偏移量
const offsetY = computed(() => {
  return startIndex.value * props.itemHeight
})

// 计算可见项
const visibleItems = computed(() => {
  return props.items.slice(startIndex.value, endIndex.value).map((item, index) => ({
    ...item,
    _index: startIndex.value + index
  }))
})

// 获取item的唯一key
const getItemKey = (item: any) => {
  return item[props.itemKey] || item._index
}

// 处理滚动
const handleScroll = (event: Event) => {
  const target = event.target as HTMLElement
  scrollTop.value = target.scrollTop
}

// 监听items变化，重置滚动位置
watch(() => props.items, () => {
  if (containerRef.value) {
    containerRef.value.scrollTop = 0
    scrollTop.value = 0
  }
}, { deep: true })

// 暴露方法：滚动到指定项
const scrollToIndex = (index: number) => {
  if (containerRef.value) {
    const targetScrollTop = index * props.itemHeight
    containerRef.value.scrollTop = targetScrollTop
    scrollTop.value = targetScrollTop
  }
}

// 暴露方法：滚动到顶部
const scrollToTop = () => {
  scrollToIndex(0)
}

// 暴露方法：滚动到底部
const scrollToBottom = () => {
  scrollToIndex(props.items.length - 1)
}

// 暴露给父组件
defineExpose({
  scrollToIndex,
  scrollToTop,
  scrollToBottom
})
</script>

<style scoped>
.virtual-list {
  position: relative;
  box-sizing: border-box;
}

.virtual-list-phantom {
  position: relative;
  width: 100%;
}

.virtual-list-content {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
}

.virtual-list-item {
  box-sizing: border-box;
}
</style>
