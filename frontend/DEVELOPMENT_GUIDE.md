# 前端开发指南

## 快速开始

### 环境要求
- Node.js 16+
- npm 8+ 或 pnpm

### 安装依赖
```bash
cd frontend
npm install
```

### 开发环境配置
创建 `.env.development` 文件：
```
VITE_API_BASE=http://localhost:3000/api
```

### 启动开发服务器
```bash
npm run dev
```

访问 `http://localhost:5173` 查看应用

## 项目结构详解

### /src/api
API 服务层，封装所有后端接口调用

**使用示例：**
```typescript
import * as authAPI from '@/api/auth'
import * as productAPI from '@/api/products'
import * as chatAPI from '@/api/chat'

// 登录
const response = await authAPI.login({
  email: 'user@example.com',
  password: 'password123'
})

// 获取产品列表
const products = await productAPI.getProductList({
  page: 1,
  pageSize: 12,
  category: 'electronics'
})
```

### /src/stores
Pinia 状态管理，集中管理应用状态

**使用示例：**
```typescript
import { useUserStore } from '@/stores/user'
import { useProductStore } from '@/stores/product'
import { useChatStore } from '@/stores/chat'

// 在组件中使用
const userStore = useUserStore()
const productStore = useProductStore()
const chatStore = useChatStore()

// 调用 store 方法
await userStore.login(email, password)
await productStore.fetchProducts()
await chatStore.sendMessage(message)

// 访问 store 状态
console.log(userStore.user)
console.log(productStore.products)
console.log(chatStore.messages)
```

### /src/components
可复用的 UI 组件

**使用示例：**
```vue
<template>
  <!-- 加载组件 -->
  <Loading message="加载中..." />

  <!-- 空状态组件 -->
  <Empty
    title="暂无数据"
    type="search"
    :show-button="true"
    button-text="返回首页"
    @action="goHome"
  />

  <!-- 产品卡片 -->
  <ProductCard :product="product" />

  <!-- 聊天消息气泡 -->
  <MessageBubble
    :message="message"
    :is-loading="false"
    show-time
  />
</template>

<script setup>
import Loading from '@/components/Loading.vue'
import Empty from '@/components/Empty.vue'
import ProductCard from '@/components/ProductCard.vue'
import MessageBubble from '@/components/chat/MessageBubble.vue'
</script>
```

### /src/layouts
页面布局组件

**MainLayout 结构：**
```
┌─────────────────────────────┐
│         Header              │
├──────────┬──────────────────┤
│          │                  │
│ Sidebar  │   Main Content   │
│          │                  │
└──────────┴──────────────────┘
```

## 页面开发指南

### 创建新页面

1. **创建页面文件**
```vue
<!-- src/views/example/Example.vue -->
<template>
  <div class="example-page">
    <h1>示例页面</h1>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const data = ref('')
</script>

<style scoped lang="scss">
.example-page {
  // 样式
}
</style>
```

2. **在路由中注册**
```typescript
// src/router/index.ts
{
  path: 'example',
  name: 'Example',
  component: () => import('@/views/example/Example.vue'),
}
```

3. **在导航菜单中添加**
```vue
<!-- src/components/Sidebar.vue -->
<el-menu-item index="/example">
  <el-icon><House /></el-icon>
  <template #title>示例</template>
</el-menu-item>
```

## 常见开发模式

### 模式 1：列表页面

```vue
<template>
  <div class="list-page">
    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-input v-model="keyword" placeholder="搜索..." />
      <el-button @click="handleSearch">搜索</el-button>
    </el-card>

    <!-- 列表 -->
    <el-skeleton v-if="loading" :rows="5" />
    <Empty v-else-if="items.length === 0" />
    <el-table v-else :data="items" />

    <!-- 分页 -->
    <el-pagination
      :current-page="page"
      :page-size="pageSize"
      :total="total"
      @current-change="handlePageChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const items = ref([])
const keyword = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const loading = ref(false)

const fetchData = async () => {
  loading.value = true
  try {
    // 调用 API
    const response = await api.getList({
      keyword: keyword.value,
      page: page.value,
      pageSize: pageSize.value
    })
    items.value = response.data
    total.value = response.total
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  page.value = 1
  fetchData()
}

const handlePageChange = () => {
  fetchData()
}

onMounted(() => {
  fetchData()
})
</script>
```

### 模式 2：表单页面

```vue
<template>
  <el-card>
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="用户名" prop="username">
        <el-input v-model="formData.username" />
      </el-form-item>

      <el-form-item label="邮箱" prop="email">
        <el-input v-model="formData.email" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="handleSubmit">提交</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, ElForm } from 'element-plus'

const formRef = ref<InstanceType<typeof ElForm>>()
const loading = ref(false)

const formData = reactive({
  username: '',
  email: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ]
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true
    // 提交数据
    await api.submit(formData)
    ElMessage.success('提交成功')
  } catch (error) {
    ElMessage.error('提交失败')
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  formRef.value?.resetFields()
}
</script>
```

### 模式 3：详情页面

```vue
<template>
  <div class="detail-page">
    <el-skeleton v-if="loading" :rows="5" />
    <div v-else-if="!item">
      <Empty title="数据不存在" />
    </div>
    <div v-else>
      <h1>{{ item.title }}</h1>
      <p>{{ item.content }}</p>
      <el-button @click="handleEdit">编辑</el-button>
      <el-button type="danger" @click="handleDelete">删除</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const item = ref(null)
const loading = ref(false)

const fetchData = async () => {
  loading.value = true
  try {
    item.value = await api.getDetail(route.params.id)
  } finally {
    loading.value = false
  }
}

const handleEdit = () => {
  router.push(`/edit/${item.value.id}`)
}

const handleDelete = async () => {
  await api.delete(item.value.id)
  router.back()
}

onMounted(() => {
  fetchData()
})
</script>
```

## API 集成指南

### 添加新的 API 服务

1. **创建 API 文件**
```typescript
// src/api/example.ts
import axios from 'axios'
import type { ExampleData } from '@/types/example'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3000/api'

const exampleAPI = axios.create({
  baseURL: `${API_BASE}/example`,
  timeout: 10000,
})

// 添加 token 拦截器
exampleAPI.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export async function getExample(id: string): Promise<ExampleData> {
  const response = await exampleAPI.get<ExampleData>(`/${id}`)
  return response.data
}

export async function createExample(data: ExampleData): Promise<ExampleData> {
  const response = await exampleAPI.post<ExampleData>('/', data)
  return response.data
}
```

2. **创建类型定义**
```typescript
// src/types/example.ts
export interface ExampleData {
  id: string
  name: string
  description: string
  createdAt: string
}
```

3. **在组件中使用**
```typescript
import * as exampleAPI from '@/api/example'

const data = await exampleAPI.getExample('123')
```

## 状态管理最佳实践

### 何时使用 Store

✅ **使用 Store：**
- 多个组件共享的状态
- 需要持久化的数据
- 复杂的状态逻辑

❌ **不使用 Store：**
- 仅单个组件使用的状态
- 临时 UI 状态（如表单数据）
- Props 能够传递的数据

### Store 使用示例

```typescript
// 在组件中使用 Store
import { useUserStore } from '@/stores/user'

export default {
  setup() {
    const userStore = useUserStore()

    // 访问状态
    console.log(userStore.user)
    console.log(userStore.isLoggedIn)

    // 调用方法
    const login = async () => {
      await userStore.login(email, password)
    }

    // 计算属性
    console.log(userStore.isAdmin)

    return {
      userStore,
      login
    }
  }
}
```

## 样式最佳实践

### 响应式断点

```scss
// 手机：< 576px
// 平板：576px - 768px
// 桌面：768px - 992px
// 大屏：992px - 1200px
// 超大屏：>= 1200px

@media (max-width: 576px) {
  // 手机样式
}

@media (min-width: 576px) and (max-width: 768px) {
  // 平板样式
}

@media (min-width: 768px) {
  // 桌面及以上样式
}
```

### CSS 变量

```scss
// 使用 Element Plus 的 CSS 变量
$primary-color: var(--el-color-primary);
$text-color: var(--el-text-color-primary);
$border-color: var(--el-border-color);
```

## 调试技巧

### Vue DevTools
```javascript
// 在浏览器控制台中
// 访问 Store
console.log($pinia)

// 访问路由
console.log($route, $router)

// 访问组件实例（在 DevTools 选中组件后）
$vm
```

### 日志记录
```typescript
// 创建日志工具
// src/utils/logger.ts
export const logger = {
  log: (...args) => console.log('[APP]', ...args),
  error: (...args) => console.error('[ERROR]', ...args),
  warn: (...args) => console.warn('[WARN]', ...args),
}
```

## 性能优化

### 懒加载组件
```typescript
// 使用动态导入
const ProductDetail = () => import('@/views/products/ProductDetail.vue')

// 在路由中使用
{
  path: 'products/:id',
  component: () => import('@/views/products/ProductDetail.vue')
}
```

### 虚拟列表
```vue
<template>
  <!-- 对于大列表使用虚拟列表 -->
  <el-virtual-list
    :items="items"
    :item-size="50"
  >
    <template #default="{ item }">
      <div>{{ item.name }}</div>
    </template>
  </el-virtual-list>
</template>
```

## 测试

### 单元测试示例
```typescript
import { describe, it, expect } from 'vitest'
import { useUserStore } from '@/stores/user'

describe('useUserStore', () => {
  it('should login successfully', async () => {
    const store = useUserStore()
    await store.login('user@example.com', 'password')
    expect(store.isLoggedIn).toBe(true)
  })
})
```

## 常见问题解决

### Q: 如何在组件中访问路由参数？
A:
```typescript
import { useRoute } from 'vue-router'

const route = useRoute()
const id = route.params.id
const query = route.query.search
```

### Q: 如何处理 API 错误？
A:
```typescript
try {
  const data = await api.fetchData()
} catch (error) {
  if (error.response?.status === 401) {
    // 未授权，重定向到登录
  } else if (error.response?.status === 404) {
    // 资源不存在
  } else {
    ElMessage.error('请求失败，请稍后重试')
  }
}
```

### Q: 如何在路由切换前保存表单数据？
A:
```typescript
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'

const router = useRouter()

router.beforeEach(async (to, from) => {
  if (formHasChanges.value) {
    try {
      await ElMessageBox.confirm('有未保存的更改，是否离开？')
      return true
    } catch {
      return false
    }
  }
})
```

