<template>
  <div class="compare-panel">
    <!-- 浮动对比按钮 -->
    <el-affix v-if="compareList.length > 0" position="bottom" :offset="20">
      <el-button
        type="primary"
        size="large"
        class="compare-btn-fixed"
        @click="showCompareDialog = true"
      >
        <el-icon><Scale /></el-icon>
        对比产品 ({{ compareList.length }})
      </el-button>
    </el-affix>

    <!-- 对比弹窗 -->
    <el-dialog
      v-model="showCompareDialog"
      title="产品对比"
      width="95%"
      class="compare-dialog"
      @close="handleDialogClose"
    >
      <div class="compare-container">
        <div v-if="compareList.length === 0" class="empty-state">
          <el-icon class="empty-icon"><Picture /></el-icon>
          <p>暂无产品对比，请选择产品进行对比</p>
        </div>

        <el-table v-else :data="compareTableData" class="compare-table">
          <!-- 对比项列 -->
          <el-table-column prop="attribute" label="对比项" width="120" fixed="left" />

          <!-- 产品列 -->
          <el-table-column
            v-for="product in compareList"
            :key="product.id"
            :label="`产品 ${compareList.indexOf(product) + 1}`"
            :width="300"
            align="center"
          >
            <template #header>
              <div class="product-column-header">
                <div class="product-image-wrapper">
                  <img :src="product.image" :alt="product.name" class="product-image" />
                </div>
                <div class="product-info">
                  <h4 class="product-name">{{ product.name }}</h4>
                  <p class="product-category">{{ product.category }}</p>
                </div>
                <el-button
                  type="danger"
                  size="small"
                  icon="Close"
                  circle
                  @click.stop="removeFromCompare(product)"
                />
              </div>
            </template>

            <template #default="{ row }">
              <div v-if="row.key === 'price'" class="price-cell">
                <span class="price">¥{{ product.price }}</span>
                <span v-if="product.originalPrice" class="original">
                  ¥{{ product.originalPrice }}
                </span>
              </div>

              <div v-else-if="row.key === 'rating'" class="rating-cell">
                <el-rate v-model="product.rating" disabled allow-half size="small" />
                <span class="count">({{ product.reviewCount }})</span>
              </div>

              <div v-else-if="row.key === 'stock'" class="stock-cell">
                <el-tag :type="product.inStock ? 'success' : 'danger'">
                  {{ product.inStock ? '有货' : '缺货' }}
                </el-tag>
              </div>

              <div v-else-if="row.key === 'origin'" class="origin-cell">
                <span>{{ product.origin || '未知' }}</span>
              </div>

              <div v-else-if="row.key === 'tags'" class="tags-cell">
                <el-tag
                  v-for="tag in product.culturalTags?.slice(0, 3)"
                  :key="tag.id"
                  size="small"
                  type="info"
                >
                  {{ tag.icon }} {{ tag.name }}
                </el-tag>
                <span v-if="(product.culturalTags?.length || 0) > 3" class="more-tags">
                  +{{ product.culturalTags!.length - 3 }}
                </span>
              </div>

              <div v-else-if="row.key === 'certifications'" class="cert-cell">
                <div class="certs">
                  <span v-if="product.hasOrganic" class="cert-badge organic">🌿</span>
                  <span v-if="product.hasGeo" class="cert-badge geo">🗺️</span>
                  <span v-if="product.hasQuality" class="cert-badge quality">⭐</span>
                  <span v-if="!hasAnyCertification(product)" class="no-cert">-</span>
                </div>
              </div>

              <div v-else-if="row.key === 'description'" class="description-cell">
                <el-tooltip :content="product.description" placement="top">
                  <span class="truncate">{{ product.description }}</span>
                </el-tooltip>
              </div>

              <div v-else :class="`${row.key}-cell`">
                {{ getProductValue(product, row.key) }}
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 操作栏 -->
        <div v-if="compareList.length > 0" class="actions-bar">
          <el-button @click="handleClearCompare">清空对比</el-button>
          <el-button @click="handleExportCompare">导出对比</el-button>
          <div class="action-tips">
            <el-icon><InfoFilled /></el-icon>
            <span>提示: 您最多可以对比 5 个产品</span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Operation, Picture, InfoFilled } from '@element-plus/icons-vue'
import type { Product } from '@/types/product'

interface Props {
  modelValue: Product[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: Product[]]
  'remove': [product: Product]
  'clear': []
}>()

const showCompareDialog = ref(false)

const compareList = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

// 对比表格数据
const compareTableData = computed(() => {
  return [
    { attribute: '价格', key: 'price' },
    { attribute: '评分', key: 'rating' },
    { attribute: '库存', key: 'stock' },
    { attribute: '产地', key: 'origin' },
    { attribute: '文化标签', key: 'tags' },
    { attribute: '认证', key: 'certifications' },
    { attribute: '描述', key: 'description' },
  ]
})

const removeFromCompare = (product: Product) => {
  const newList = compareList.value.filter((p: Product) => p.id !== product.id)
  emit('update:modelValue', newList)
  emit('remove', product)
  ElMessage.success('已从对比中移除')
}

const handleClearCompare = () => {
  emit('update:modelValue', [])
  emit('clear')
  showCompareDialog.value = false
  ElMessage.success('已清空对比')
}

const handleExportCompare = () => {
  // 导出为CSV格式
  const headers = ['对比项', ...compareList.value.map((p: Product) => p.name)]
  const rows = compareTableData.value.map((row: any) => {
    const rowData = [row.attribute]
    compareList.value.forEach((product: Product) => {
      rowData.push(getProductValue(product, row.key))
    })
    return rowData
  })

  const csvContent = [
    headers.join(','),
    ...rows.map((row: any[]) => row.map((cell: any) => `"${cell}"`).join(',')),
  ].join('\n')

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `产品对比-${new Date().getTime()}.csv`)
  link.click()

  ElMessage.success('对比结果已导出')
}

const handleDialogClose = () => {
  showCompareDialog.value = false
}

const hasAnyCertification = (product: Product) => {
  return product.hasOrganic || product.hasGeo || product.hasQuality
}

const getProductValue = (product: Product, key: string): string => {
  switch (key) {
    case 'price':
      return `¥${product.price}`
    case 'rating':
      return `${product.rating.toFixed(1)} (${product.reviewCount})`
    case 'stock':
      return product.inStock ? '有货' : '缺货'
    case 'origin':
      return product.origin || '未知'
    case 'description':
      return product.description
    case 'unit':
      return product.unit || '件'
    case 'supplier':
      return product.supplier || '-'
    default:
      return '-'
  }
}
</script>

<style scoped lang="scss">
.compare-panel {
  .compare-btn-fixed {
    width: 180px;
    height: 50px;
    font-size: 16px;
    font-weight: 600;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

    :deep(.el-icon) {
      margin-right: 8px;
    }
  }

  .compare-dialog {
    :deep(.el-dialog) {
      max-height: 90vh;
    }

    :deep(.el-dialog__body) {
      padding: 20px;
      max-height: 70vh;
      overflow-y: auto;
    }
  }

  .compare-container {
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 60px 20px;
      text-align: center;

      .empty-icon {
        font-size: 48px;
        color: #ccc;
        margin-bottom: 16px;
      }

      p {
        font-size: 16px;
        color: #909399;
        margin: 0;
      }
    }

    .compare-table {
      width: 100%;

      :deep(.el-table__header-wrapper) {
        overflow-x: auto;
      }

      :deep(.el-table__body-wrapper) {
        overflow-x: auto;
      }

      .product-column-header {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;

        .product-image-wrapper {
          width: 80px;
          height: 80px;
          border-radius: 4px;
          overflow: hidden;
          background: #f5f5f5;

          .product-image {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }
        }

        .product-info {
          text-align: center;
          flex: 1;

          .product-name {
            font-size: 14px;
            font-weight: 600;
            margin: 0 0 4px 0;
            color: #333;
            display: -webkit-box;
            -webkit-box-orient: vertical;
            -webkit-line-clamp: 2;
            overflow: hidden;
          }

          .product-category {
            font-size: 12px;
            color: #909399;
            margin: 0;
          }
        }
      }

      .price-cell {
        display: flex;
        flex-direction: column;
        gap: 4px;

        .price {
          font-size: 18px;
          font-weight: 600;
          color: #ff6b6b;
        }

        .original {
          font-size: 12px;
          color: #999;
          text-decoration: line-through;
        }
      }

      .rating-cell {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;

        .count {
          font-size: 12px;
          color: #909399;
        }
      }

      .tags-cell {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        justify-content: center;

        .more-tags {
          font-size: 12px;
          color: #909399;
        }
      }

      .cert-cell {
        .certs {
          display: flex;
          justify-content: center;
          gap: 8px;
          font-size: 16px;

          .no-cert {
            color: #ccc;
          }
        }
      }

      .description-cell {
        .truncate {
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 2;
          overflow: hidden;
          font-size: 12px;
          color: #909399;
          line-height: 1.4;
        }
      }
    }

    .actions-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 20px;
      padding-top: 20px;
      border-top: 1px solid #f0f0f0;

      .action-tips {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        color: #909399;

        :deep(.el-icon) {
          color: #ff9800;
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .compare-panel {
    .compare-dialog {
      :deep(.el-dialog) {
        width: 100% !important;
      }
    }

    .compare-container {
      .compare-table {
        font-size: 12px;
      }
    }

    .actions-bar {
      flex-direction: column;
      gap: 12px;

      button {
        width: 100%;
      }
    }
  }
}
</style>
