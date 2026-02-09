# 组件 API 文档

## 目录

1. [AdvancedFilters](#advancedfilters)
2. [QuickViewDialog](#quickviewdialog)
3. [ComparePanel](#comparepanel)
4. [MapView](#mapview)
5. [ProductCard（增强）](#productcard)

---

## AdvancedFilters

高级筛选面板组件，支持多维度产品筛选。

### 文件位置
`frontend/src/components/AdvancedFilters.vue`

### Props

| 属性 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| modelValue | `AdvancedFilters` | ✅ | - | 筛选条件对象 |
| categories | `Category[]` | ✅ | - | 分类列表 |
| culturalTags | `CulturalTag[]` | ❌ | 6个预设 | 文化标签列表 |

### Emits

| 事件 | 参数 | 说明 |
|------|------|------|
| update:modelValue | `filters: AdvancedFilters` | 筛选条件更新 |
| apply | `filters: AdvancedFilters` | 应用筛选按钮点击 |

### Data Structure

```typescript
interface AdvancedFilters {
  category?: string[]                    // 选中的分类ID
  priceRange?: [number, number]         // 价格范围 [min, max]
  regions?: string[]                     // 选中的地区代码
  culturalTags?: string[]               // 选中的文化标签ID
  certifications?: string[]              // 选中的认证类型
  sortBy?: 'recommend' | 'price_asc' | 'price_desc' | 'newest' | 'sales'
}
```

### 使用示例

```vue
<template>
  <AdvancedFilters
    v-model="filters"
    :categories="categoryList"
    :cultural-tags="tagList"
    @apply="handleApplyFilters"
  />
</template>

<script setup>
import { ref } from 'vue'
import AdvancedFilters from '@/components/AdvancedFilters.vue'

const filters = ref({})

const handleApplyFilters = (appliedFilters) => {
  console.log('Applied filters:', appliedFilters)
  // 调用 API 获取筛选后的产品
}
</script>
```

### 功能特性

- ✅ 可折叠式面板设计
- ✅ 分类树形选择
- ✅ 价格范围双输入
- ✅ 范围滑块调整
- ✅ 多地区选择
- ✅ 文化标签复选
- ✅ 认证标识筛选
- ✅ 排序方式设置
- ✅ 已选条件展示
- ✅ 单个条件删除

---

## QuickViewDialog

产品快速预览弹窗组件，展示产品关键信息。

### 文件位置
`frontend/src/components/QuickViewDialog.vue`

### Props

| 属性 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| modelValue | `boolean` | ✅ | false | 是否显示弹窗 |
| product | `Product` | ❌ | null | 产品信息 |
| isInCompare | `boolean` | ❌ | false | 是否已在对比中 |

### Emits

| 事件 | 参数 | 说明 |
|------|------|------|
| update:modelValue | `value: boolean` | 弹窗显示/隐藏 |
| add-to-cart | - | 加入购物车 |
| add-to-compare | - | 加入对比 |
| view-detail | `productId: string` | 查看详情 |

### 使用示例

```vue
<template>
  <QuickViewDialog
    v-model="showPreview"
    :product="selectedProduct"
    :is-in-compare="isProductInCompare"
    @add-to-cart="handleAddToCart"
    @add-to-compare="handleAddToCompare"
    @view-detail="handleViewDetail"
  />
</template>

<script setup>
import { ref } from 'vue'
import QuickViewDialog from '@/components/QuickViewDialog.vue'

const showPreview = ref(false)
const selectedProduct = ref(null)

const handleAddToCart = () => {
  console.log('Added to cart')
}

const handleAddToCompare = () => {
  console.log('Added to compare')
}

const handleViewDetail = (productId) => {
  console.log('View detail:', productId)
}
</script>
```

### 显示内容

- 产品图库（主图 + 缩略图）
- 产品标题和评分
- 当前价格和原价
- 优惠率计算
- 产地信息
- 分类信息
- 文化标签
- 认证标识
- 产品描述
- 库存状态

### 快捷操作

- 🔍 图片放大
- 📥 图片下载
- 📖 查看完整详情
- 🛒 加入购物车
- ⚖️ 加入对比

---

## ComparePanel

产品对比面板组件，支持多产品属性对比。

### 文件位置
`frontend/src/components/ComparePanel.vue`

### Props

| 属性 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| modelValue | `Product[]` | ✅ | [] | 对比产品列表 |

### Emits

| 事件 | 参数 | 说明 |
|------|------|------|
| update:modelValue | `products: Product[]` | 对比列表更新 |
| remove | `product: Product` | 移除单个产品 |
| clear | - | 清空所有对比 |

### 对比项目

- 价格（包括原价）
- 评分和评价数
- 库存状态
- 产地
- 文化标签
- 认证标识
- 产品描述

### 使用示例

```vue
<template>
  <ComparePanel
    v-model="compareList"
    @remove="handleRemoveProduct"
    @clear="handleClearCompare"
  />
</template>

<script setup>
import { ref } from 'vue'
import ComparePanel from '@/components/ComparePanel.vue'

const compareList = ref([])

const handleRemoveProduct = (product) => {
  console.log('Removed:', product.name)
}

const handleClearCompare = () => {
  console.log('Cleared all')
}

// 最多支持 5 个产品对比
const addToCompare = (product) => {
  if (compareList.value.length < 5) {
    compareList.value.push(product)
  }
}
</script>
```

### 功能特性

- ✅ 浮动对比按钮
- ✅ 显示对比数量
- ✅ 表格式对比展示
- ✅ 产品移除功能
- ✅ 清空所有功能
- ✅ CSV 导出功能
- ✅ 最多 5 个产品限制
- ✅ 移动端优化

### 导出功能

```typescript
// 自动生成的 CSV 文件格式
对比项,产品1,产品2,产品3,...
价格,¥99,¥120,¥150,...
评分,4.5 (120),4.0 (85),4.8 (200),...
库存,有货,有货,缺货,...
产地,锡林郭勒盟,呼伦贝尔市,赤峰市,...
...
```

---

## MapView

地图视图组件，展示产品产地分布。

### 文件位置
`frontend/src/components/MapView.vue`

### Props

| 属性 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| products | `Product[]` | ✅ | [] | 产品列表 |
| modelValue | `'list'\|'map'` | ❌ | 'list' | 当前视图模式 |

### Emits

| 事件 | 参数 | 说明 |
|------|------|------|
| update:modelValue | `mode: 'list'\|'map'` | 视图模式切换 |
| region-change | `region: string` | 地区选择变化 |

### 使用示例

```vue
<template>
  <MapView
    v-model="viewMode"
    :products="productList"
    @region-change="handleRegionChange"
  />
</template>

<script setup>
import { ref } from 'vue'
import MapView from '@/components/MapView.vue'

const viewMode = ref('list')

const handleRegionChange = (region) => {
  console.log('Selected region:', region)
  // 按地区筛选产品
}
</script>
```

### 支持地区

- 锡林郭勒盟
- 呼伦贝尔市
- 赤峰市
- 通辽市
- 乌兰察布市
- 包头市
- 呼和浩特市

### 视图模式

| 模式 | 说明 |
|------|------|
| list | 列表视图（默认） |
| map | 地图视图（区域卡片） |

### 地图视图特性

- 按地区分组展示产品
- 显示每个地区的产品数量
- 快速预览产品列表
- 点击产品查看详情
- 响应式网格布局

---

## ProductCard（增强）

增强的产品卡片组件。

### 文件位置
`frontend/src/components/ProductCard.vue`

### Props

| 属性 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| product | `Product` | ✅ | - | 产品信息 |
| isInCompare | `boolean` | ❌ | false | 是否在对比中 |

### Emits

| 事件 | 说明 |
|------|------|
| quick-view | 快速预览按钮点击 |
| add-to-cart | 加入购物车按钮点击 |
| toggle-compare | 对比按钮点击 |

### 使用示例

```vue
<template>
  <ProductCard
    :product="product"
    :is-in-compare="isInCompare"
    @quick-view="handleQuickView"
    @add-to-cart="handleAddToCart"
    @toggle-compare="handleToggleCompare"
  />
</template>

<script setup>
import ProductCard from '@/components/ProductCard.vue'

const handleQuickView = () => {
  console.log('Quick view clicked')
}

const handleAddToCart = () => {
  console.log('Add to cart clicked')
}

const handleToggleCompare = () => {
  console.log('Toggle compare clicked')
}
</script>
```

### 显示元素

- 产品图片（支持悬停缩放）
- 认证徽章（有机、地标）
- 优惠率显示
- 文化标签（最多 2 个）
- 产地显示
- 评分和评价数
- 产品名称
- 产品描述（单行省略）
- 当前价格和原价
- 库存状态标签

### 悬停操作

- 👁️ 快速预览
- 🛒 加入购物车
- ⚖️ 加入对比（显示对比状态）

---

## 类型定义

### Product 扩展字段

```typescript
interface Product {
  // 现有字段...

  // 新增农产品特定字段
  origin?: string                    // 产地名称
  region?: string                    // 地区代码
  location?: LocationCoord           // 地理位置坐标
  culturalTags?: CulturalTag[]      // 文化标签数组
  hasOrganic?: boolean              // 有机认证标志
  hasGeo?: boolean                  // 地理标志标志
  hasQuality?: boolean              // 质量认证标志
  unit?: string                     // 产品单位
  supplier?: string                 // 供应商名称
}

interface LocationCoord {
  latitude: number
  longitude: number
}

interface CulturalTag {
  id: string                    // 标签ID
  name: string                 // 标签名称
  icon: string                 // 图标符号 (emoji)
  description?: string         // 标签描述
}

interface AdvancedFilters {
  category?: string[]
  priceRange?: [number, number]
  regions?: string[]
  culturalTags?: string[]
  certifications?: string[]
  sortBy?: 'recommend' | 'price_asc' | 'price_desc' | 'newest' | 'sales'
}
```

---

## 最佳实践

### 1. 集成到页面中

```vue
<template>
  <div class="products-page">
    <!-- 筛选 -->
    <AdvancedFilters
      v-model="filters"
      :categories="categories"
      @apply="applyFilters"
    />

    <!-- 视图切换 -->
    <MapView v-model="viewMode" :products="products" />

    <!-- 产品列表 -->
    <div v-if="viewMode === 'list'" class="products-grid">
      <ProductCard
        v-for="product in products"
        :key="product.id"
        :product="product"
        :is-in-compare="isProductInCompare(product.id)"
        @quick-view="showQuickView"
        @add-to-cart="addToCart"
        @toggle-compare="toggleCompare"
      />
    </div>

    <!-- 预览 -->
    <QuickViewDialog v-model="showPreview" :product="currentProduct" />

    <!-- 对比 -->
    <ComparePanel v-model="compareList" />
  </div>
</template>
```

### 2. 状态管理

```typescript
// 使用 Pinia store
import { defineStore } from 'pinia'

export const useProductStore = defineStore('product', () => {
  const filters = ref({})
  const compareList = ref([])
  const viewMode = ref('list')

  const applyFilters = async (newFilters) => {
    filters.value = newFilters
    await fetchProducts()
  }

  return {
    filters,
    compareList,
    viewMode,
    applyFilters
  }
})
```

### 3. 响应式图片

```typescript
// 为产品添加多张图片
const product = {
  id: '1',
  name: '产品名',
  image: 'https://example.com/main.jpg',
  images: [
    'https://example.com/main.jpg',
    'https://example.com/detail1.jpg',
    'https://example.com/detail2.jpg',
  ]
}
```

---

## 性能建议

1. **虚拟滚动**: 大数据量时使用虚拟列表
2. **图片优化**: 使用 CDN 和适当的图片尺寸
3. **防抖处理**: 筛选条件变化时防抖
4. **组件懒加载**: 预览弹窗等非关键组件支持动态导入
5. **缓存策略**: 使用 LocalStorage 缓存用户偏好

---

## 常见问题

**Q: 如何限制对比产品数量？**
A: 组件已内置限制，最多 5 个产品。可在 ComparePanel 中的 `handleToggleCompare` 方法修改限制数量。

**Q: 如何自定义文化标签？**
A: 通过 `AdvancedFilters` 的 `cultural-tags` prop 传入自定义标签数组。

**Q: 如何集成真实地图？**
A: MapView 当前使用 CSS 卡片展示。可集成高德地图 API 或百度地图 API 实现真实坐标展示。

**Q: 如何支持更多排序方式？**
A: 修改 `ProductListRequest` 类型中的 `sortBy` 枚举，并在后端实现相应的排序逻辑。

---

**文档版本**: 1.0
**最后更新**: [项目完成日期]
