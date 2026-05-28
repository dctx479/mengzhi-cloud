<template>
  <div class="map-view-container">
    <!-- 视图切换器 -->
    <div class="view-switcher">
      <el-radio-group v-model="viewMode" @change="handleViewModeChange">
        <el-radio-button label="list">
          <el-icon><List /></el-icon>
          列表视图
        </el-radio-button>
        <el-radio-button label="map">
          <el-icon><Location /></el-icon>
          地图视图
        </el-radio-button>
      </el-radio-group>

      <div class="map-controls">
        <el-select v-model="selectedRegion" placeholder="选择地区" clearable>
          <el-option label="全部地区" value="" />
          <el-option label="锡林郭勒盟" value="xilin" />
          <el-option label="呼伦贝尔市" value="hulun" />
          <el-option label="赤峰市" value="chifeng" />
          <el-option label="通辽市" value="tongliao" />
          <el-option label="乌兰察布市" value="wulanchabu" />
          <el-option label="包头市" value="baotou" />
          <el-option label="呼和浩特市" value="huhhot" />
        </el-select>

        <el-button v-if="viewMode === 'map'" type="primary" @click="handleRefreshMap">
          重置筛选
        </el-button>
      </div>
    </div>

    <!-- 地图容器 -->
    <div v-if="viewMode === 'map'" class="map-wrapper">
      <!-- 简化地图 (使用 CSS 地图或数据可视化) -->
      <div id="amap-container" class="amap-container">
        <div class="map-placeholder">
          <div class="map-message">
            <el-icon class="icon"><Location /></el-icon>
            <p>产地地图展示</p>
            <p class="text-sm">共有 {{ filteredProducts.length }} 个产品</p>
          </div>

          <!-- 区域产品分布卡片 -->
          <div class="region-cards">
            <div v-for="region in regionDistribution" :key="region.code" class="region-card">
              <div class="region-header">
                <span class="region-name">{{ region.name }}</span>
                <el-tag type="info">{{ region.count }} 个产品</el-tag>
              </div>
              <div class="region-products">
                <el-tag
                  v-for="product in region.products.slice(0, 3)"
                  :key="product.id"
                  size="small"
                >
                  {{ product.name }}
                </el-tag>
                <span v-if="region.count > 3" class="more">+{{ region.count - 3 }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 产品弹窗 -->
        <el-dialog
          v-model="showProductPopup"
          :title="`产品: ${selectedMapProduct?.name || ''}`"
          width="600px"
        >
          <div v-if="selectedMapProduct" class="popup-content">
            <div class="popup-image">
              <img :src="selectedMapProduct.image" :alt="selectedMapProduct.name" />
            </div>
            <div class="popup-info">
              <div class="info-item">
                <span class="label">产地:</span>
                <span>{{ selectedMapProduct.origin }}</span>
              </div>
              <div class="info-item">
                <span class="label">价格:</span>
                <span class="price">¥{{ selectedMapProduct.price }}</span>
              </div>
              <div class="info-item">
                <span class="label">分类:</span>
                <span>{{ selectedMapProduct.category }}</span>
              </div>
              <div class="info-item">
                <span class="label">描述:</span>
                <p>{{ selectedMapProduct.description }}</p>
              </div>
            </div>
          </div>
          <template #footer>
            <el-button type="primary" @click="handleViewMapProductDetail">
              查看详情
            </el-button>
            <el-button @click="showProductPopup = false">关闭</el-button>
          </template>
        </el-dialog>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { List, Location } from '@element-plus/icons-vue'
import type { Product } from '@/types/product'

interface Props {
  products: Product[]
  modelValue?: 'list' | 'map'
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: 'list',
})

const emit = defineEmits<{
  'update:modelValue': [value: 'list' | 'map']
  'region-change': [region: string]
}>()

const router = useRouter()
const viewMode = ref(props.modelValue)
const selectedRegion = ref('')
const showProductPopup = ref(false)
const selectedMapProduct = ref<Product | null>(null)

// 区域信息映射
const regionMap = {
  xilin: { name: '锡林郭勒盟', code: 'xilin', lat: 43.9, lng: 116.5 },
  hulun: { name: '呼伦贝尔市', code: 'hulun', lat: 49.2, lng: 119.8 },
  chifeng: { name: '赤峰市', code: 'chifeng', lat: 42.3, lng: 118.9 },
  tongliao: { name: '通辽市', code: 'tongliao', lat: 43.6, lng: 122.3 },
  wulanchabu: { name: '乌兰察布市', code: 'wulanchabu', lat: 41.0, lng: 113.8 },
  baotou: { name: '包头市', code: 'baotou', lat: 40.7, lng: 109.8 },
  huhhot: { name: '呼和浩特市', code: 'huhhot', lat: 40.8, lng: 111.6 },
}

// 过滤后的产品列表
const filteredProducts = computed(() => {
  if (!selectedRegion.value) {
    return props.products
  }
  return props.products.filter((p) => p.region === selectedRegion.value)
})

// 区域产品分布
const regionDistribution = computed(() => {
  const distribution = Object.values(regionMap).map((region) => {
    const products = props.products.filter((p) => p.region === region.code)
    return {
      ...region,
      count: products.length,
      products: products.slice(0, 5),
    }
  })
  return distribution.filter((r) => r.count > 0)
})

const handleViewModeChange = (newMode: string) => {
  viewMode.value = newMode as 'list' | 'map'
  emit('update:modelValue', viewMode.value)
}

const handleRefreshMap = () => {
  selectedRegion.value = ''
  emit('region-change', '')
}

const handleViewMapProductDetail = () => {
  if (selectedMapProduct.value) {
    showProductPopup.value = false
    router.push(`/products/${selectedMapProduct.value.id}`)
  }
}
</script>

<style scoped lang="scss">
.map-view-container {
  width: 100%;

  .view-switcher {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 12px;
    background: #f5f7fa;
    border-radius: 4px;

    :deep(.el-radio-group) {
      display: flex;
      gap: 0;
    }

    .map-controls {
      display: flex;
      gap: 12px;
      align-items: center;

      :deep(.el-select) {
        width: 200px;
      }
    }
  }

  .map-wrapper {
    width: 100%;
    height: 600px;
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    background: #f5f7fa;
    overflow: hidden;

    .amap-container {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      position: relative;

      .map-placeholder {
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 20px;

        .map-message {
          text-align: center;
          margin-bottom: 40px;

          .icon {
            font-size: 48px;
            color: $color-primary;
            margin-bottom: 12px;
          }

          p {
            margin: 8px 0;
            color: #606266;
            font-size: 14px;

            &.text-sm {
              font-size: 12px;
              color: #909399;
            }
          }
        }

        .region-cards {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 16px;
          width: 100%;
          max-width: 1200px;

          .region-card {
            background: white;
            border: 1px solid #ebeef5;
            border-radius: 8px;
            padding: 16px;
            transition: all 0.3s;
            cursor: pointer;

            &:hover {
              box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
              border-color: $color-primary;

              .region-header .region-name {
                color: $color-primary;
              }
            }

            .region-header {
              display: flex;
              justify-content: space-between;
              align-items: center;
              margin-bottom: 12px;

              .region-name {
                font-size: 16px;
                font-weight: 600;
                color: #333;
                transition: color 0.3s;
              }
            }

            .region-products {
              display: flex;
              flex-wrap: wrap;
              gap: 8px;

              :deep(.el-tag) {
                margin: 0;
                max-width: 100%;
                overflow: hidden;
                text-overflow: ellipsis;
              }

              .more {
                display: inline-block;
                padding: 4px 8px;
                background: #f0f0f0;
                border-radius: 4px;
                font-size: 12px;
                color: #909399;
              }
            }
          }
        }
      }
    }
  }

  .popup-content {
    display: flex;
    gap: 16px;

    .popup-image {
      flex-shrink: 0;
      width: 120px;
      height: 120px;
      border-radius: 4px;
      overflow: hidden;
      background: #f5f5f5;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }

    .popup-info {
      flex: 1;

      .info-item {
        display: flex;
        gap: 8px;
        margin-bottom: 8px;
        font-size: 14px;

        .label {
          font-weight: 500;
          color: #666;
          white-space: nowrap;
        }

        span {
          color: #333;
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .price {
          font-size: 16px;
          font-weight: 600;
          color: #ff6b6b;
        }

        p {
          margin: 0;
          color: #666;
          line-height: 1.4;
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .map-view-container {
    .view-switcher {
      flex-direction: column;
      gap: 12px;

      .map-controls {
        width: 100%;
        flex-direction: column;

        :deep(.el-select) {
          width: 100%;
        }

        button {
          width: 100%;
        }
      }
    }

    .map-wrapper {
      height: 400px;

      .region-cards {
        grid-template-columns: 1fr;
      }
    }
  }
}
</style>
