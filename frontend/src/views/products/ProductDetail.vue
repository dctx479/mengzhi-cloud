<template>
  <div class="product-detail-page">
    <el-skeleton v-if="productStore.loading" :rows="5" animated />

    <div v-else-if="!productStore.currentProduct" class="not-found">
      <Empty
        title="产品不存在"
        description="您访问的产品已下架或不存在"
        type="error"
        :show-button="true"
        button-text="返回产品列表"
        @action="goToList"
      />
    </div>

    <div v-else class="product-detail">
      <el-breadcrumb class="breadcrumb">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item :to="{ path: '/products' }">产品</el-breadcrumb-item>
        <el-breadcrumb-item>{{ product.name }}</el-breadcrumb-item>
      </el-breadcrumb>

      <el-row :gutter="32">
        <!-- 左侧：图片展示 -->
        <el-col :xs="24" :md="12">
          <div class="product-images">
            <div class="main-image">
              <img :src="mainImage" :alt="product.name" />
            </div>
            <div class="thumbnail-list">
              <img
                v-for="(img, index) in product.images"
                :key="index"
                :src="img"
                :alt="`产品图${index}`"
                class="thumbnail"
                :class="{ active: mainImage === img }"
                @click="mainImage = img"
              />
            </div>
          </div>
        </el-col>

        <!-- 右侧：产品信息 -->
        <el-col :xs="24" :md="12">
          <div class="product-info">
            <h1 class="product-name">{{ product.name }}</h1>

            <div class="product-meta">
              <el-rate v-model="product.rating" disabled allow-half />
              <span class="review-count">({{ product.reviewCount }} 评价)</span>
            </div>

            <div class="product-prices">
              <span class="current-price">¥{{ product.price }}</span>
              <span v-if="product.originalPrice" class="original-price">
                ¥{{ product.originalPrice }}
              </span>
            </div>

            <el-divider />

            <div class="product-description">
              <p>{{ product.description }}</p>
            </div>

            <div v-if="product.specifications" class="product-specs">
              <h3>产品规格</h3>
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item
                  v-for="(value, key) in product.specifications"
                  :key="key"
                  :label="key"
                >
                  {{ value }}
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <div v-if="product.benefits" class="product-benefits">
              <h3>产品优势</h3>
              <ul>
                <li v-for="(benefit, index) in product.benefits" :key="index">
                  {{ benefit }}
                </li>
              </ul>
            </div>

            <div class="product-actions">
              <el-input-number
                v-model="quantity"
                :min="1"
                :max="product.stockCount || 999"
                controls-position="right"
                class="quantity-input"
              />
              <el-button
                type="primary"
                size="large"
                :disabled="!product.inStock"
                @click="handleAddToCart"
              >
                {{ product.inStock ? '加入购物车' : '缺货' }}
              </el-button>
              <el-button size="large" icon="Star" @click="handleAddToFavorite">
                收藏
              </el-button>
            </div>

            <el-alert
              v-if="!product.inStock"
              title="产品暂时缺货，您可以收藏此产品或联系客服"
              type="warning"
              :closable="false"
              class="stock-alert"
            />
          </div>
        </el-col>
      </el-row>

      <el-divider />

      <!-- 相关产品 -->
      <div v-if="product.relatedProducts && product.relatedProducts.length > 0" class="related-products">
        <h2>相关产品</h2>
        <el-row :gutter="20">
          <el-col
            v-for="item in product.relatedProducts"
            :key="item.id"
            :xs="24"
            :sm="12"
            :md="8"
            :lg="6"
          >
            <ProductCard :product="item" />
          </el-col>
        </el-row>
      </div>

      <!-- 评论区 -->
      <div class="reviews-section">
        <h2>用户评价</h2>
        <el-skeleton v-if="reviewsLoading" :rows="3" animated />
        <div v-else class="reviews-list">
          <div v-if="reviews.length === 0" class="no-reviews">
            <Empty title="暂无评价" description="还没有用户评价此产品" />
          </div>
          <div v-else>
            <div v-for="review in reviews" :key="review.id" class="review-item">
              <div class="review-header">
                <el-avatar :src="review.userAvatar" :size="32" />
                <div class="review-user-info">
                  <p class="review-user-name">{{ review.userName }}</p>
              <el-rate :model-value="review.rating" disabled allow-half size="small" />
                  <p class="review-time">{{ formatDate(review.createdAt) }}</p>
                </div>
              </div>
              <p class="review-comment">{{ review.comment }}</p>
            </div>

            <el-pagination
              v-if="reviewTotal > reviewPageSize"
              v-model:current-page="reviewPage"
              :page-size="reviewPageSize"
              :total="reviewTotal"
              layout="prev, pager, next"
              class="review-pagination"
              @current-change="handleReviewPageChange"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useProductStore } from '@/stores/product'
import * as productAPI from '@/api/products'
import ProductCard from '@/components/ProductCard.vue'
import Empty from '@/components/Empty.vue'

const route = useRoute()
const router = useRouter()
const productStore = useProductStore()

const mainImage = ref('')
const quantity = ref(1)
const reviews = ref<any[]>([])
const reviewTotal = ref(0)
const reviewsLoading = ref(false)
const reviewPage = ref(1)
const reviewPageSize = 10

const product = computed(() => productStore.currentProduct!)

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const handleAddToCart = () => {
  ElMessage.success(`已将 ${quantity.value} 件商品加入购物车`)
  quantity.value = 1
}

const handleAddToFavorite = () => {
  ElMessage.success('已加入收藏')
}

const goToList = () => {
  router.push('/products')
}

const loadReviews = async (page = reviewPage.value) => {
  reviewsLoading.value = true
  try {
    const response = await productAPI.getProductReviews(route.params.id as string, page, reviewPageSize)
    reviews.value = response.data
    reviewTotal.value = response.total
    reviewPage.value = page
  } catch (error) {
    ElMessage.error('加载评价失败')
  } finally {
    reviewsLoading.value = false
  }
}

const handleReviewPageChange = (page: number) => {
  loadReviews(page)
}

onMounted(async () => {
  try {
    await productStore.fetchProductDetail(route.params.id as string)
    if (productStore.currentProduct) {
      const p = productStore.currentProduct
      mainImage.value = p?.image || p?.images?.[0] || ''
      await loadReviews(1)
    }
  } catch (error) {
    ElMessage.error('加载产品信息失败')
  }
})

onUnmounted(() => {
  // 离开详情页时清除当前产品，避免下次进入时短暂显示旧数据
  productStore.currentProduct = null
})
</script>

<style scoped lang="scss">
.product-detail-page {
  background: white;
  padding: 20px;
  border-radius: 4px;

  .breadcrumb {
    margin-bottom: 24px;
  }

  .product-detail {
    .product-images {
      .main-image {
        width: 100%;
        aspect-ratio: 1;
        background: #f5f5f5;
        border-radius: 4px;
        margin-bottom: 16px;
        overflow: hidden;

        img {
          width: 100%;
          height: 100%;
          object-fit: contain;
        }
      }

      .thumbnail-list {
        display: flex;
        gap: 8px;
        overflow-x: auto;

        .thumbnail {
          width: 80px;
          height: 80px;
          background: #f5f5f5;
          border: 2px solid transparent;
          border-radius: 4px;
          cursor: pointer;
          flex-shrink: 0;
          object-fit: contain;
          transition: all 0.3s;

          &:hover,
          &.active {
            border-color: #409eff;
          }
        }
      }
    }

    .product-info {
      .product-name {
        font-size: 24px;
        font-weight: 600;
        color: #333;
        margin-bottom: 16px;
      }

      .product-meta {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 16px;

        .review-count {
          color: #999;
          font-size: 14px;
        }
      }

      .product-prices {
        font-size: 24px;
        margin-bottom: 16px;

        .current-price {
          color: #ff6b6b;
          font-weight: 600;
          margin-right: 12px;
        }

        .original-price {
          color: #999;
          font-size: 14px;
          text-decoration: line-through;
        }
      }

      .product-description {
        margin-bottom: 24px;
        color: #666;
        line-height: 1.6;
      }

      .product-specs {
        margin-bottom: 24px;

        h3 {
          font-size: 16px;
          font-weight: 600;
          margin-bottom: 12px;
        }
      }

      .product-benefits {
        margin-bottom: 24px;

        h3 {
          font-size: 16px;
          font-weight: 600;
          margin-bottom: 12px;
        }

        ul {
          list-style: none;
          padding: 0;
          margin: 0;

          li {
            padding: 8px 0;
            padding-left: 24px;
            position: relative;
            color: #666;

            &:before {
              content: '✓';
              position: absolute;
              left: 0;
              color: #67c23a;
              font-weight: 600;
            }
          }
        }
      }

      .product-actions {
        display: flex;
        gap: 12px;
        margin-bottom: 16px;
        flex-wrap: wrap;

        .quantity-input {
          width: 120px;
        }

        :deep(.el-button) {
          flex: 1;
          min-width: 120px;
        }
      }

      .stock-alert {
        margin-top: 16px;
      }
    }
  }

  .related-products {
    margin: 40px 0;

    h2 {
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 20px;
    }
  }

  .reviews-section {
    margin-top: 40px;

    h2 {
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 20px;
    }

    .reviews-list {
      .review-item {
        padding: 16px 0;
        border-bottom: 1px solid #f0f0f0;

        &:last-child {
          border-bottom: none;
        }

        .review-header {
          display: flex;
          gap: 12px;
          margin-bottom: 12px;

          .review-user-info {
            flex: 1;

            .review-user-name {
              font-weight: 500;
              margin: 0 0 4px 0;
            }

            .review-time {
              font-size: 12px;
              color: #999;
              margin: 0;
            }
          }
        }

        .review-comment {
          color: #666;
          margin: 0;
          line-height: 1.6;
        }
      }

      .review-pagination {
        margin-top: 20px;
        text-align: center;
      }
    }
  }
}

@media (max-width: 768px) {
  .product-detail-page {
    padding: 12px;

    .product-detail {
      .product-actions {
        :deep(.el-button) {
          min-width: auto;
          flex: 1;
        }
      }
    }
  }
}
</style>
