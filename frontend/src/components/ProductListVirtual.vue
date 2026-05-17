<!--
产品列表（虚拟滚动版） - BUG-033修复示例

使用虚拟滚动优化大量产品列表的渲染性能

版本: 1.0
创建日期: 2026-01-17
-->

<template>
  <div class="product-list-virtual">
    <VirtualList
      :items="products"
      :item-height="120"
      :container-height="600"
      :buffer="3"
      item-key="id"
    >
      <template #default="{ item }">
        <div class="product-item">
          <div class="product-image">
            <img :src="item.images || '/default-product.jpg'" :alt="item.name" />
          </div>
          <div class="product-info">
            <h3 class="product-name">{{ item.name }}</h3>
            <p class="product-category">{{ item.category }}</p>
            <p class="product-price">¥{{ item.price }}</p>
            <p class="product-region">产地: {{ item.region }}</p>
          </div>
          <div class="product-actions">
            <button @click="viewDetail(item.id)">查看详情</button>
            <button @click="addToCart(item.id)">加入购物车</button>
          </div>
        </div>
      </template>
    </VirtualList>
  </div>
</template>

<script setup lang="ts">
import VirtualList from './VirtualList.vue'

// 定义Props
interface Props {
  products: any[]
}

const props = defineProps<Props>()

// 方法
const viewDetail = (productId: string) => {
  console.log('查看产品详情:', productId)
  // 导航到产品详情页
}

const addToCart = (productId: string) => {
  console.log('添加到购物车:', productId)
  // 添加到购物车逻辑
}
</script>

<style scoped>
.product-list-virtual {
  width: 100%;
  padding: 20px;
}

.product-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
  background-color: #fff;
  transition: background-color 0.2s;
}

.product-item:hover {
  background-color: #f5f5f5;
}

.product-image {
  flex-shrink: 0;
  width: 80px;
  height: 80px;
  border-radius: 8px;
  overflow: hidden;
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-info {
  flex: 1;
  min-width: 0;
}

.product-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-category {
  margin: 0 0 4px 0;
  font-size: 12px;
  color: #666;
}

.product-price {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: bold;
  color: #e74c3c;
}

.product-region {
  margin: 0;
  font-size: 12px;
  color: #999;
}

.product-actions {
  display: flex;
  gap: 8px;
  flex-direction: column;
}

.product-actions button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.product-actions button:first-child {
  background-color: #3498db;
  color: white;
}

.product-actions button:first-child:hover {
  background-color: #2980b9;
}

.product-actions button:last-child {
  background-color: #2ecc71;
  color: white;
}

.product-actions button:last-child:hover {
  background-color: #27ae60;
}
</style>
