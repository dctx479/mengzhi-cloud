<template>
  <div class="products-page">
    <!-- 高级筛选 -->
    <AdvancedFilters
      v-model="advancedFilters"
      :categories="productStore.categories"
      :cultural-tags="culturalTags"
      @apply="handleApplyAdvancedFilters"
    />

    <!-- 地图视图 -->
    <MapView
      v-model="viewMode"
      :products="productStore.products"
      @region-change="handleRegionChange"
    />

    <!-- 产品列表/网格 -->
    <div v-if="viewMode === 'list'" class="products-list">
      <el-skeleton v-if="productStore.loading" :rows="5" animated />

      <Empty
        v-else-if="productStore.products.length === 0"
        title="暂无产品"
        type="search"
      />

      <el-scrollbar v-else height="calc(100vh - 300px)">
        <el-row :gutter="20">
          <el-col
            v-for="product in productStore.products"
            :key="product.id"
            :xs="24"
            :sm="12"
            :md="8"
            :lg="6"
          >
            <ProductCard
              :product="product"
              :is-in-compare="isProductInCompare(product.id)"
              @quick-view="handleQuickView(product)"
              @add-to-cart="handleAddToCart(product)"
              @toggle-compare="handleToggleCompare(product)"
            />
          </el-col>
        </el-row>
      </el-scrollbar>
    </div>

    <!-- 分页 -->
    <div v-if="productStore.products.length > 0 && viewMode === 'list'" class="pagination-container">
      <el-pagination
        v-model:current-page="productStore.currentPage"
        v-model:page-size="productStore.pageSize"
        :page-sizes="[12, 24, 36]"
        :total="productStore.total"
        layout="total, sizes, prev, pager, next, jumper"
        @change="handlePageChange"
      />
    </div>

    <!-- 快速预览弹窗 -->
    <QuickViewDialog
      v-model="showQuickView"
      :product="selectedQuickViewProduct"
      :is-in-compare="selectedQuickViewProduct ? isProductInCompare(selectedQuickViewProduct.id) : false"
      @add-to-cart="handleQuickViewAddToCart"
      @add-to-compare="handleQuickViewAddToCompare"
      @view-detail="handleQuickViewViewDetail"
    />

    <!-- 产品对比面板 -->
    <ComparePanel
      v-model="compareList"
      @remove="handleRemoveFromCompare"
      @clear="handleClearCompare"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProductStore } from '@/stores/product'
import { ElMessage } from 'element-plus'
import AdvancedFilters from '@/components/AdvancedFilters.vue'
import MapView from '@/components/MapView.vue'
import ProductCard from '@/components/ProductCard.vue'
import QuickViewDialog from '@/components/QuickViewDialog.vue'
import ComparePanel from '@/components/ComparePanel.vue'
import Empty from '@/components/Empty.vue'
import type { Product, AdvancedFilters as AdvancedFiltersType } from '@/types/product'

const route = useRoute()
const router = useRouter()
const productStore = useProductStore()

const viewMode = ref<'list' | 'map'>('list')
const advancedFilters = ref<AdvancedFiltersType>({})
const compareList = ref<Product[]>([])
const showQuickView = ref(false)
const selectedQuickViewProduct = ref<Product | undefined>(undefined)

// 文化标签数据
const culturalTags = [
  { id: 'mongolian', name: '蒙古族', icon: '🐴', description: '蒙古族文化产品' },
  { id: 'dairy', name: '乳文化', icon: '🥛', description: '奶制品与乳文化' },
  { id: 'grassland', name: '草原', icon: '🌾', description: '草原产品' },
  { id: 'nomadic', name: '游牧文化', icon: '🏕️', description: '游牧文化特色' },
  { id: 'traditional', name: '传统工艺', icon: '🎨', description: '传统手工艺' },
  { id: 'heritage', name: '非遗传承', icon: '👑', description: '非物质文化遗产' },
]

// 检查产品是否在对比列表中
const isProductInCompare = (productId: string) => {
  return compareList.value.some((p) => p.id === productId)
}

// 处理高级筛选应用
const handleApplyAdvancedFilters = (filters: AdvancedFiltersType) => {
  advancedFilters.value = filters
  productStore.currentPage = 1
  // 这里可以扩展 store 来处理高级筛选
  productStore.fetchProducts()
}

// 处理地区变化
const handleRegionChange = (region: string) => {
  console.log('Selected region:', region)
  // 可以在这里添加地区筛选逻辑
}

// 快速预览
const handleQuickView = (product: Product) => {
  selectedQuickViewProduct.value = product
  showQuickView.value = true
}

// 加入购物车
const handleAddToCart = (product: Product) => {
  ElMessage.success(`已将 ${product.name} 添加到购物车`)
}

const handleQuickViewAddToCart = () => {
  if (selectedQuickViewProduct.value) {
    ElMessage.success(`已将 ${selectedQuickViewProduct.value.name} 添加到购物车`)
  }
}

// 加入对比
const handleToggleCompare = (product: Product) => {
  if (isProductInCompare(product.id)) {
    compareList.value = compareList.value.filter((p) => p.id !== product.id)
    ElMessage.success('已移除对比')
  } else {
    if (compareList.value.length >= 5) {
      ElMessage.warning('最多只能对比5个产品')
      return
    }
    compareList.value.push(product)
    ElMessage.success('已添加到对比')
  }
}

const handleQuickViewAddToCompare = () => {
  if (selectedQuickViewProduct.value) {
    handleToggleCompare(selectedQuickViewProduct.value)
  }
}

const handleQuickViewViewDetail = (productId: string) => {
  router.push(`/products/${productId}`)
}

const handleRemoveFromCompare = (product: Product) => {
  compareList.value = compareList.value.filter((p) => p.id !== product.id)
}

const handleClearCompare = () => {
  compareList.value = []
}

const handlePageChange = async () => {
  await productStore.fetchProducts()
  window.scrollTo(0, 0)
}

onMounted(async () => {
  // 从路由查询参数中获取关键词
  const keyword = route.query.keyword as string
  if (keyword) {
    productStore.searchKeyword = keyword
  }

  // 初始化分类列表
  if (productStore.categories.length === 0) {
    await productStore.fetchCategories()
  }

  // 获取产品列表
  if (productStore.products.length === 0) {
    await productStore.fetchProducts()
  }
})

onUnmounted(() => {
  // 离开页面时重置快速预览状态，避免内存泄漏
  showQuickView.value = false
  selectedQuickViewProduct.value = undefined
})
</script>

<style scoped lang="scss">
.products-page {
  padding: 20px;

  .products-list {
    margin-bottom: 24px;

    :deep(.el-skeleton) {
      margin-bottom: 20px;
    }
  }

  .pagination-container {
    display: flex;
    justify-content: center;
    padding: 20px 0;
  }
}

@media (max-width: 768px) {
  .products-page {
    padding: 12px;
  }
}
</style>
