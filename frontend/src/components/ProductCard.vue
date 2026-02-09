<template>
  <el-card class="product-card" :body-style="{ padding: '0' }">
    <div class="card-image">
      <img :src="product.image" :alt="product.name" class="product-image" />

      <!-- 徽章 -->
      <div class="badges">
        <el-tag v-if="product.hasOrganic" type="success" size="small" class="badge">
          🌿 有机
        </el-tag>
        <el-tag v-if="product.hasGeo" type="warning" size="small" class="badge">
          🗺️ 地标
        </el-tag>
        <el-tag v-if="discountRate" type="danger" size="small" class="discount-badge">
          {{ discountRate }}% 优惠
        </el-tag>
      </div>

      <!-- 悬停操作 -->
      <div class="card-overlay">
        <div class="overlay-buttons">
          <el-button icon="View" circle @click="handleQuickView" />
          <el-button icon="ShoppingCart" circle @click="handleAddToCart" />
          <el-button
            :icon="isInCompare ? 'Check' : 'Scale'"
            circle
            :type="isInCompare ? 'primary' : 'default'"
            @click="handleToggleCompare"
          />
        </div>
      </div>
    </div>

    <div class="card-content">
      <h3 class="product-name" @click="handleViewDetail">{{ product.name }}</h3>

      <!-- 文化标签 -->
      <div v-if="product.culturalTags && product.culturalTags.length > 0" class="cultural-tags">
        <el-tag
          v-for="tag in product.culturalTags.slice(0, 2)"
          :key="tag.id"
          size="small"
          type="info"
        >
          {{ tag.icon }} {{ tag.name }}
        </el-tag>
      </div>

      <!-- 产地 -->
      <div v-if="product.origin" class="product-origin">
        <el-icon><MapLocation /></el-icon>
        <span>{{ product.origin }}</span>
      </div>

      <div class="product-rating">
        <el-rate v-model="product.rating" disabled allow-half size="small" />
        <span class="rating-count">({{ product.reviewCount }})</span>
      </div>

      <p class="product-description">{{ product.description }}</p>

      <div class="product-price">
        <span class="current-price">¥{{ product.price }}</span>
        <span v-if="product.originalPrice" class="original-price">
          ¥{{ product.originalPrice }}
        </span>
      </div>

      <div class="product-footer">
        <el-tag :type="product.inStock ? 'success' : 'danger'" size="small">
          {{ product.inStock ? '有货' : '缺货' }}
        </el-tag>
        <el-button
          type="primary"
          text
          size="small"
          @click="handleViewDetail"
        >
          查看详情
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MapLocation } from '@element-plus/icons-vue'
import type { Product } from '@/types/product'

interface Props {
  product: Product
  isInCompare?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isInCompare: false,
})

const emit = defineEmits<{
  'quick-view': []
  'add-to-cart': []
  'toggle-compare': []
}>()

const router = useRouter()

const discountRate = computed(() => {
  if (!props.product.originalPrice) return null
  return Math.round(
    ((props.product.originalPrice - props.product.price) / props.product.originalPrice) * 100
  )
})

const handleViewDetail = () => {
  router.push(`/products/${props.product.id}`)
}

const handleQuickView = () => {
  emit('quick-view')
}

const handleAddToCart = () => {
  emit('add-to-cart')
  ElMessage.success('已添加到购物车')
}

const handleToggleCompare = () => {
  emit('toggle-compare')
}
</script>

<style scoped lang="scss">
.product-card {
  height: 100%;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;

  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    border-color: #409eff;

    .card-overlay {
      display: flex;
    }

    .product-image {
      transform: scale(1.05);
    }
  }

  .card-image {
    position: relative;
    width: 100%;
    height: 200px;
    background: #f5f5f5;
    overflow: hidden;

    .product-image {
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.3s;
    }

    .card-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.4);
      display: none;
      align-items: center;
      justify-content: center;
      transition: all 0.3s;

      .overlay-buttons {
        display: flex;
        gap: 8px;

        :deep(.el-button) {
          background: white;

          &:hover {
            background: #f0f0f0;
          }
        }
      }
    }

    .badges {
      position: absolute;
      top: 8px;
      left: 8px;
      display: flex;
      flex-direction: column;
      gap: 4px;

      .badge {
        font-size: 12px;
      }
    }

    .discount-badge {
      position: absolute;
      top: 8px;
      right: 8px;
      background: #ff6b6b;
      color: white;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 600;
      border: none;
    }
  }

  .card-content {
    padding: 12px;

    .product-name {
      font-size: 14px;
      font-weight: 600;
      color: #333;
      margin: 0 0 8px 0;
      display: -webkit-box;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 2;
      overflow: hidden;
      cursor: pointer;
      transition: color 0.3s;

      &:hover {
        color: #409eff;
      }
    }

    .cultural-tags {
      display: flex;
      gap: 4px;
      margin-bottom: 6px;
      flex-wrap: wrap;

      :deep(.el-tag) {
        height: auto;
        padding: 2px 4px;
        font-size: 11px;
        line-height: 1.4;
      }
    }

    .product-origin {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      color: #909399;
      margin-bottom: 6px;

      :deep(.el-icon) {
        font-size: 14px;
      }
    }

    .product-rating {
      display: flex;
      align-items: center;
      gap: 4px;
      margin-bottom: 8px;

      .rating-count {
        font-size: 12px;
        color: #999;
      }
    }

    .product-description {
      font-size: 12px;
      color: #999;
      margin: 0 0 10px 0;
      display: -webkit-box;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 1;
      overflow: hidden;
    }

    .product-price {
      margin-bottom: 10px;

      .current-price {
        font-size: 18px;
        font-weight: 600;
        color: #ff6b6b;
        margin-right: 8px;
      }

      .original-price {
        font-size: 12px;
        color: #999;
        text-decoration: line-through;
      }
    }

    .product-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;

      :deep(.el-button) {
        flex: 1;
        padding: 0 6px;
      }
    }
  }
}

@media (max-width: 768px) {
  .product-card {
    .card-image {
      height: 150px;
    }

    .card-content {
      padding: 10px;
    }
  }
}
</style>
