<template>
  <el-dialog
    v-model="visible"
    :title="product?.name || '产品预览'"
    width="850px"
    class="quick-view-dialog"
    @close="handleClose"
  >
    <div v-if="product" class="quick-view-content">
      <!-- 产品图库 -->
      <div class="product-gallery">
        <div class="main-image-wrapper">
          <img :src="currentImage" :alt="product.name" class="main-image" />
          <div class="image-controls">
            <el-button circle icon="ZoomIn" @click="handleOpenImage" />
            <el-button circle icon="Download" @click="handleDownloadImage" />
          </div>
        </div>

        <div v-if="productImages.length > 1" class="thumbnail-list">
          <img
            v-for="(img, index) in productImages"
            :key="index"
            :src="img"
            class="thumbnail"
            :class="{ active: img === currentImage }"
            @click="currentImage = img"
          />
        </div>
      </div>

      <!-- 产品详情 -->
      <div class="product-details">
        <!-- 标题和评分 -->
        <div class="header-section">
          <h2 class="product-title">{{ product.name }}</h2>
          <div class="rating-section">
            <el-rate v-model="product.rating" disabled allow-half size="large" />
            <span class="rating-text">({{ product.reviewCount }} 条评价)</span>
          </div>
        </div>

        <!-- 价格信息 -->
        <div class="price-section">
          <div class="price-group">
            <span class="label">价格</span>
            <span class="current-price">¥{{ product.price }}</span>
            <span v-if="product.originalPrice" class="original-price">
              ¥{{ product.originalPrice }}
            </span>
            <el-tag v-if="discountRate" type="danger" size="small">
              限时优惠 {{ discountRate }}%
            </el-tag>
          </div>

          <div class="stock-status">
            <el-tag :type="product.inStock ? 'success' : 'danger'">
              {{ product.inStock ? `有货 (库存${product.stockCount || '充足'})` : '缺货' }}
            </el-tag>
          </div>
        </div>

        <!-- 基本信息 -->
        <div class="info-section">
          <div class="info-item">
            <span class="label">产地:</span>
            <span class="value">{{ product.origin || '未知' }}</span>
          </div>

          <div class="info-item">
            <span class="label">分类:</span>
            <span class="value">{{ product.category }}</span>
          </div>

          <div class="info-item">
            <span class="label">单位:</span>
            <span class="value">{{ product.unit || '件' }}</span>
          </div>

          <div v-if="product.supplier" class="info-item">
            <span class="label">供应商:</span>
            <span class="value">{{ product.supplier }}</span>
          </div>
        </div>

        <!-- 文化标签 -->
        <div v-if="product.culturalTags && product.culturalTags.length > 0" class="tags-section">
          <span class="label">文化标签:</span>
          <div class="tags">
            <el-tag
              v-for="tag in product.culturalTags"
              :key="tag.id"
              type="info"
              size="large"
            >
              {{ tag.icon }} {{ tag.name }}
            </el-tag>
          </div>
        </div>

        <!-- 认证信息 -->
        <div v-if="hasCertifications" class="certification-section">
          <span class="label">认证:</span>
          <div class="certifications">
            <el-tag v-if="product.hasOrganic" type="success">🌿 有机认证</el-tag>
            <el-tag v-if="product.hasGeo" type="warning">🗺️ 地理标志</el-tag>
            <el-tag v-if="product.hasQuality" type="info">⭐ 质量认证</el-tag>
          </div>
        </div>

        <!-- 描述 -->
        <div v-if="product.description" class="description-section">
          <span class="label">产品描述:</span>
          <p class="description-text">{{ product.description }}</p>
        </div>

        <!-- 操作按钮 -->
        <div class="actions-section">
          <el-button type="primary" size="large" class="action-btn" @click="handleViewFullDetail">
            <el-icon><DocumentCopy /></el-icon>
            查看完整详情
          </el-button>
          <el-button size="large" class="action-btn" @click="handleAddToCart">
            <el-icon><ShoppingCart /></el-icon>
            加入购物车
          </el-button>
          <el-button
            :type="isInCompare ? 'primary' : 'default'"
            size="large"
            class="action-btn"
            @click="handleAddToCompare"
          >
            <el-icon><Scale /></el-icon>
            {{ isInCompare ? '已对比' : '加入对比' }}
          </el-button>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import {
  DocumentCopy,
  ShoppingCart,
} from '@element-plus/icons-vue'
import type { Product } from '@/types/product'

interface Props {
  modelValue: boolean
  product?: Product
  isInCompare?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isInCompare: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'add-to-cart': []
  'add-to-compare': []
  'view-detail': [productId: string]
}>()

const router = useRouter()
const currentImage = ref('')

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const productImages = computed(() => {
  if (!props.product) return []
  return props.product.images || [props.product.image]
})

const discountRate = computed(() => {
  if (!props.product || !props.product.originalPrice) return null
  return Math.round(
    ((props.product.originalPrice - props.product.price) / props.product.originalPrice) * 100
  )
})

const hasCertifications = computed(() => {
  return props.product && (props.product.hasOrganic || props.product.hasGeo || props.product.hasQuality)
})

const handleClose = () => {
  visible.value = false
}

const handleOpenImage = () => {
  if (currentImage.value) {
    window.open(currentImage.value, '_blank', 'noopener,noreferrer')
  }
}

const handleDownloadImage = () => {
  if (currentImage.value) {
    const link = document.createElement('a')
    link.href = currentImage.value
    link.download = props.product?.name || 'image'
    link.click()
  }
}

const handleViewFullDetail = () => {
  if (props.product) {
    handleClose()
    emit('view-detail', props.product.id)
    router.push(`/products/${props.product.id}`)
  }
}

const handleAddToCart = () => {
  emit('add-to-cart')
  ElMessage.success('已添加到购物车')
  handleClose()
}

const handleAddToCompare = () => {
  emit('add-to-compare')
}

watch(
  () => props.product,
  (newProduct) => {
    if (newProduct) {
      currentImage.value = newProduct.image || (newProduct.images?.[0] || '')
    }
  },
  { immediate: true }
)
</script>

<style scoped lang="scss">
.quick-view-dialog {
  :deep(.el-dialog) {
    max-height: 90vh;
    overflow-y: auto;
  }

  :deep(.el-dialog__body) {
    padding: 20px;
  }
}

.quick-view-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  min-height: 500px;

  .product-gallery {
    display: flex;
    flex-direction: column;
    gap: 12px;

    .main-image-wrapper {
      position: relative;
      width: 100%;
      aspect-ratio: 1;
      background: #f5f5f5;
      border-radius: 8px;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;

      .main-image {
        width: 100%;
        height: 100%;
        object-fit: contain;
        transition: transform 0.3s;
      }

      .image-controls {
        position: absolute;
        top: 12px;
        right: 12px;
        display: flex;
        gap: 8px;
      }
    }

    .thumbnail-list {
      display: flex;
      gap: 8px;
      overflow-x: auto;
      padding-bottom: 4px;

      .thumbnail {
        flex-shrink: 0;
        width: 60px;
        height: 60px;
        border-radius: 4px;
        cursor: pointer;
        border: 2px solid transparent;
        transition: all 0.3s;
        object-fit: cover;

        &:hover {
          border-color: $color-primary;
        }

        &.active {
          border-color: $color-primary;
        }
      }
    }
  }

  .product-details {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 8px 0;

    .header-section {
      .product-title {
        font-size: 24px;
        font-weight: 600;
        margin: 0 0 12px 0;
        color: #333;
      }

      .rating-section {
        display: flex;
        align-items: center;
        gap: 8px;

        .rating-text {
          color: #909399;
          font-size: 14px;
        }
      }
    }

    .price-section {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      background: #f5f7fa;
      border-radius: 8px;

      .price-group {
        display: flex;
        align-items: center;
        gap: 12px;

        .label {
          font-weight: 500;
          color: #666;
        }

        .current-price {
          font-size: 28px;
          font-weight: 600;
          color: #ff6b6b;
        }

        .original-price {
          font-size: 14px;
          color: #999;
          text-decoration: line-through;
        }
      }

      .stock-status {
        flex-shrink: 0;
      }
    }

    .info-section {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;

      .info-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;

        .label {
          font-weight: 500;
          color: #666;
          white-space: nowrap;
        }

        .value {
          color: #333;
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }
    }

    .tags-section {
      .label {
        display: block;
        font-weight: 500;
        color: #666;
        margin-bottom: 8px;
      }

      .tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
    }

    .certification-section {
      .label {
        display: block;
        font-weight: 500;
        color: #666;
        margin-bottom: 8px;
      }

      .certifications {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
    }

    .description-section {
      .label {
        display: block;
        font-weight: 500;
        color: #666;
        margin-bottom: 8px;
      }

      .description-text {
        margin: 0;
        color: #999;
        font-size: 14px;
        line-height: 1.6;
      }
    }

    .actions-section {
      display: flex;
      gap: 12px;
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid #f0f0f0;

      .action-btn {
        flex: 1;
        height: 40px;
        font-weight: 500;
      }
    }
  }
}

@media (max-width: 768px) {
  .quick-view-content {
    grid-template-columns: 1fr;
    gap: 16px;

    .product-details {
      .actions-section {
        flex-direction: column;

        .action-btn {
          width: 100%;
        }
      }
    }
  }
}
</style>
