# 前端组件文档

**项目**: AI赋能云平台
**技术栈**: Vue 3 + TypeScript + Element Plus + Vite
**版本**: 1.0
**更新日期**: [项目完成日期]

## 目录

- [基础组件](#基础组件)
- [聊天组件](#聊天组件)
- [产品组件](#产品组件)
- [最佳实践](#最佳实践)
- [类型定义](#类型定义)

---

## 基础组件

### Header（页面头部）

**路径**: `Header.vue`

页面顶部导航栏组件，包含Logo、导航菜单、用户菜单等。

#### Props

无

#### Emits

- `logout`: 用户登出事件

#### 使用示例

```vue
<template>
  <Header />
</template>

<script setup lang="ts">
import Header from '@/components/Header.vue'
</script>
```

#### 样式说明

- 固定顶部，高度 60px
- 支持响应式，移动端自动折叠
- 包含Logo、菜单、用户下拉菜单

---

### Sidebar（侧边栏）

**路径**: `Sidebar.vue`

左侧导航菜单，展示应用的主要功能模块。

#### Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| collapsed | boolean | false | 是否折叠 |

#### Emits

- `toggle`: 切换折叠状态
- `navigate`: 导航到菜单项

#### 使用示例

```vue
<template>
  <Sidebar :collapsed="sidebarCollapsed" @navigate="handleNavigation" />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Sidebar from '@/components/Sidebar.vue'

const sidebarCollapsed = ref(false)

const handleNavigation = (path: string) => {
  router.push(path)
}
</script>
```

---

### Loading（加载指示器）

**路径**: `Loading.vue`

显示页面或内容加载中的状态。

#### Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| text | string | '加载中...' | 加载文案 |
| size | 'small' \| 'default' \| 'large' | 'default' | 加载器大小 |
| fullscreen | boolean | false | 是否全屏显示 |

#### 使用示例

```vue
<template>
  <div v-if="loading" class="page-content">
    <Loading text="正在加载产品列表..." />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Loading from '@/components/Loading.vue'

const loading = ref(true)
</script>
```

---

### Empty（空状态）

**路径**: `Empty.vue`

当列表、表格等内容为空时显示的占位符。

#### Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| description | string | '暂无数据' | 空状态描述文案 |
| image | string | - | 自定义空状态图片URL |

#### 使用示例

```vue
<template>
  <Empty
    v-if="products.length === 0"
    description="还没有添加任何产品"
  />
</template>

<script setup lang="ts">
import Empty from '@/components/Empty.vue'
</script>
```

---

## 聊天组件

### MessageBubble（消息气泡）

**路径**: `chat/MessageBubble.vue`

显示单条AI对话消息。

#### Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| message | Message | 必需 | 消息对象 |
| isLoading | boolean | false | 是否正在加载（显示思考动画） |
| showTime | boolean | true | 是否显示时间戳 |

#### Message 类型

```typescript
interface Message {
  id: string
  content: string
  role: 'user' | 'assistant' | 'system'  // 消息角色
  timestamp: string  // ISO 8601格式时间
  contentType?: 'text' | 'image' | 'file'  // 内容类型
}
```

#### 使用示例

```vue
<template>
  <MessageBubble
    :message="message"
    :is-loading="isLoading"
    :show-time="true"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import type { Message } from '@/types/chat'

const message = ref<Message>({
  id: '1',
  content: '你好，有什么我可以帮助的吗？',
  role: 'assistant',
  timestamp: new Date().toISOString()
})

const isLoading = ref(false)
</script>
```

#### 样式说明

- 用户消息：右对齐，蓝色背景
- AI消息：左对齐，灰色背景
- 加载状态：显示旋转的加载图标和文案
- 响应式：移动端消息气泡宽度调整为85%

---

### MessageInput（消息输入框）

**路径**: `chat/MessageInput.vue`

AI对话的消息输入框。

#### Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| placeholder | string | '输入您的问题...' | 占位符文案 |
| disabled | boolean | false | 是否禁用 |
| sending | boolean | false | 是否正在发送 |
| maxLength | number | 2000 | 最大输入长度 |

#### Emits

- `send(content: string)`: 发送消息
- `input(content: string)`: 输入内容变化

#### 使用示例

```vue
<template>
  <MessageInput
    :disabled="isLoading"
    :sending="isSending"
    @send="handleSendMessage"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import MessageInput from '@/components/chat/MessageInput.vue'

const isSending = ref(false)

const handleSendMessage = async (content: string) => {
  isSending.value = true
  try {
    await chatApi.sendMessage({
      conversationId: currentConversation.value.id,
      content
    })
  } finally {
    isSending.value = false
  }
}
</script>
```

#### 功能特性

- 自动高度调整（支持多行输入）
- 显示剩余字符数
- Shift+Enter换行，Enter发送
- 发送按钮禁用状态反馈
- 文本自动去除两端空白

---

### MessageList（消息列表）

**路径**: `chat/MessageList.vue`

显示对话历史的消息列表。

#### Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| messages | Message[] | [] | 消息数组 |
| loading | boolean | false | 是否加载中 |
| virtualScroll | boolean | true | 是否使用虚拟滚动 |

#### Emits

- `scroll-top`: 滚动到顶部事件

#### 使用示例

```vue
<template>
  <MessageList
    :messages="messages"
    :loading="isLoading"
    @scroll-top="handleLoadMore"
  />
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import MessageList from '@/components/chat/MessageList.vue'
import type { Message } from '@/types/chat'

const messages = ref<Message[]>([])
const isLoading = ref(false)

const handleLoadMore = async () => {
  isLoading.value = true
  try {
    const moreMessages = await chatApi.getMessages(currentConversation.value.id, {
      offset: messages.value.length,
      limit: 20
    })
    messages.value.unshift(...moreMessages)
  } finally {
    isLoading.value = false
  }
}
</script>
```

#### 功能特性

- 虚拟滚动优化大列表性能
- 自动滚动到最新消息
- 加载中状态显示
- 消息到达顶部自动触发加载更多

---

## 产品组件

### ProductCard（产品卡片）

**路径**: `ProductCard.vue`

展示单个产品信息的卡片。

#### Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| product | Product | 必需 | 产品对象 |

#### Product 类型

```typescript
interface Product {
  id: string | number
  uuid: string
  name: string
  image: string  // 封面图片
  description: string  // 简短描述
  price: number  // 当前价格
  originalPrice?: number  // 原价
  rating: number  // 评分 (0-5)
  reviewCount: number  // 评论数
  inStock: boolean  // 是否有货
  tags?: string[]  // 产品标签
  certifications?: string[]  // 认证标签
}
```

#### Emits

- `view-detail(id)`: 查看产品详情
- `add-to-cart(id)`: 加入购物车

#### 使用示例

```vue
<template>
  <el-row :gutter="20">
    <el-col v-for="product in products" :key="product.id" :xs="12" :sm="8" :md="6">
      <ProductCard
        :product="product"
        @view-detail="handleViewDetail"
        @add-to-cart="handleAddToCart"
      />
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import ProductCard from '@/components/ProductCard.vue'
import type { Product } from '@/types/product'

const router = useRouter()
const products = ref<Product[]>([])

const handleViewDetail = (id: string | number) => {
  router.push(`/products/${id}`)
}

const handleAddToCart = (id: string | number) => {
  // 添加到购物车逻辑
  ElMessage.success('已添加到购物车')
}
</script>
```

#### 功能特性

- 图片悬停显示"查看详情"按钮
- 显示优惠百分比徽章
- 库存状态标签
- 评分和评论数显示
- 自动计算折扣百分比
- 响应式栅格布局

#### 样式说明

- 卡片宽度：根据栅格列宽自适应
- 图片高度：200px
- 悬停效果：阴影和边框色变化

---

## 最佳实践

### 1. 类型安全

始终为props和events定义TypeScript类型：

```typescript
interface Props {
  title: string
  loading?: boolean
  items: Item[]
}

withDefaults(defineProps<Props>(), {
  loading: false
})
```

### 2. 事件命名

使用kebab-case事件名，避免与HTML事件冲突：

```typescript
// 好
defineEmits<{
  'update:modelValue': [value: string]
  'send-message': [content: string]
}>()

// 不好
defineEmits(['update', 'send'])
```

### 3. 响应式布局

使用Element Plus的响应式栅格系统：

```vue
<el-row :gutter="20">
  <el-col :xs="24" :sm="12" :md="8" :lg="6">
    <!-- 内容 -->
  </el-col>
</el-row>
```

### 4. 加载和错误状态

为用户操作提供完整的状态反馈：

```typescript
const loading = ref(false)
const error = ref<string | null>(null)

const handleAction = async () => {
  loading.value = true
  error.value = null
  try {
    await api.doSomething()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '操作失败'
  } finally {
    loading.value = false
  }
}
```

### 5. 条件渲染性能

对于大列表，使用 v-show 而非 v-if：

```vue
<!-- 频繁切换，使用 v-show -->
<div v-show="showDetail" class="detail">...</div>

<!-- 初始化时不渲染，使用 v-if -->
<dialog v-if="showModal">...</dialog>
```

### 6. 图片优化

使用懒加载和占位图：

```vue
<template>
  <img
    :src="imageSrc"
    :alt="altText"
    loading="lazy"
    @error="handleImageError"
  />
</template>
```

---

## 类型定义

### Chat 类型

```typescript
// src/types/chat.ts

export interface Message {
  id: string
  conversationId: string
  role: 'user' | 'assistant' | 'system'
  content: string
  contentType: 'text' | 'image' | 'file'
  attachments?: Attachment[]
  timestamp: string
  tokensUsed?: number
  responseTime?: number
}

export interface Attachment {
  id: string
  type: 'image' | 'file'
  url: string
  filename: string
  size: number
}

export interface Conversation {
  id: string
  uuid: string
  userId: string
  title: string
  agentType: 'marketing' | 'cultural' | 'data' | 'general'
  status: 'active' | 'archived' | 'deleted'
  messageCount: number
  totalTokens: number
  costUsd: number
  createdAt: string
  updatedAt: string
}
```

### Product 类型

```typescript
// src/types/product.ts

export interface Product {
  id: string | number
  uuid: string
  enterpriseId: string | number
  name: string
  category: string
  subCategory?: string
  description: string
  shortDescription: string
  coverImageUrl: string
  galleryImages: string[]
  originProvince: string
  originCity: string
  originDistrict?: string
  price?: number
  originalPrice?: number
  rating: number
  reviewCount: number
  inStock: boolean
  tags: string[]
  certifications: string[]
  status: 'draft' | 'pending' | 'published' | 'offline'
  viewCount: number
  generationCount: number
  favoriteCount: number
  createdAt: string
  updatedAt: string
}
```

---

## 开发指南

### 创建新组件

1. 在 `src/components` 下创建文件（.vue）
2. 定义Props和Emits类型
3. 实现模板、脚本、样式
4. 添加到此文档
5. 导出到 `src/components/index.ts`

### 导入组件

```typescript
// 方式1: 具名导入
import { ProductCard, MessageBubble } from '@/components'

// 方式2: 单文件导入
import ProductCard from '@/components/ProductCard.vue'
```

### 样式约定

- 使用 `scoped` 防止样式污染
- 使用 SCSS 变量和 mixin（如果需要）
- 遵循 BEM 命名规范
- 响应式设计优先考虑移动端

### 文档更新

添加或修改组件后，请更新本文档以包含：
- 新组件的Props、Emits定义
- 使用示例
- 功能特性说明
- 样式说明（如需要）

---

**维护者**: 前端团队
**最后更新**: [项目完成日期]
**下一个更新**: 添加新组件时
