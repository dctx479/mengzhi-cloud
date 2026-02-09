# 快速参考指南 - 前端代码生成

## 最常用的命令

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 类型检查
npm run typecheck

# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

## 最常用的文件

### 添加新功能时需要编辑的文件

1. **新增 API** → `src/api/xxx.ts`
2. **新增类型** → `src/types/xxx.ts`
3. **新增 Store** → `src/stores/xxx.ts`
4. **新增页面** → `src/views/xxx.vue`
5. **新增组件** → `src/components/xxx.vue`
6. **更新路由** → `src/router/index.ts`

## 导入常用模块

```typescript
// Composition API
import { ref, reactive, computed, watch, onMounted } from 'vue'

// 路由
import { useRouter, useRoute } from 'vue-router'
import { RouterLink } from 'vue-router'

// Pinia Store
import { useUserStore } from '@/stores/user'
import { useProductStore } from '@/stores/product'
import { useChatStore } from '@/stores/chat'

// API 服务
import * as authAPI from '@/api/auth'
import * as productAPI from '@/api/products'
import * as chatAPI from '@/api/chat'

// Element Plus
import { ElMessage, ElMessageBox, ElForm } from 'element-plus'

// 图标
import { Search, Delete, Plus } from '@element-plus/icons-vue'
```

## 常用组件导入

```vue
<script setup>
import Header from '@/components/Header.vue'
import Sidebar from '@/components/Sidebar.vue'
import MainLayout from '@/layouts/MainLayout.vue'
import ProductCard from '@/components/ProductCard.vue'
import Loading from '@/components/Loading.vue'
import Empty from '@/components/Empty.vue'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import MessageList from '@/components/chat/MessageList.vue'
import MessageInput from '@/components/chat/MessageInput.vue'
</script>
```

## 常用代码片段

### 1. 获取路由参数
```typescript
import { useRoute } from 'vue-router'

const route = useRoute()
const id = route.params.id              // 路径参数
const search = route.query.search       // 查询参数
```

### 2. 调用 API
```typescript
import * as api from '@/api/products'

const data = await api.getProductList({
  page: 1,
  pageSize: 20
})
```

### 3. 使用 Store
```typescript
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const user = userStore.user
const isLoggedIn = userStore.isLoggedIn
await userStore.login(email, password)
```

### 4. 表单验证
```vue
<el-form ref="formRef" :model="form" :rules="rules">
  <el-form-item prop="email">
    <el-input v-model="form.email" />
  </el-form-item>
</el-form>

<script setup>
const formRef = ref()
const handleSubmit = async () => {
  await formRef.value?.validate()
  // 提交逻辑
}
</script>
```

### 5. 消息提示
```typescript
import { ElMessage, ElMessageBox } from 'element-plus'

// 简单消息
ElMessage.success('操作成功')
ElMessage.error('操作失败')
ElMessage.warning('请确认')
ElMessage.info('提示信息')

// 确认框
ElMessageBox.confirm('确定删除？', '提示', {
  confirmButtonText: '确定',
  cancelButtonText: '取消',
  type: 'warning'
})
```

### 6. 列表页面模板
```vue
<template>
  <!-- 筛选 -->
  <el-card>
    <el-input v-model="keyword" placeholder="搜索..." />
    <el-button @click="handleSearch">搜索</el-button>
  </el-card>

  <!-- 列表 -->
  <el-table :data="list" v-loading="loading">
    <el-table-column prop="id" label="ID" />
    <el-table-column prop="name" label="名称" />
  </el-table>

  <!-- 分页 -->
  <el-pagination
    v-model:current-page="page"
    v-model:page-size="pageSize"
    :total="total"
  />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as api from '@/api/products'

const list = ref([])
const keyword = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const loading = ref(false)

const fetchData = async () => {
  loading.value = true
  try {
    const res = await api.getList({
      keyword: keyword.value,
      page: page.value,
      pageSize: pageSize.value
    })
    list.value = res.data
    total.value = res.total
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  page.value = 1
  fetchData()
}

onMounted(() => {
  fetchData()
})
</script>
```

### 7. 详情页面模板
```vue
<template>
  <el-skeleton v-if="loading" />
  <Empty v-else-if="!item" />
  <div v-else>
    <h1>{{ item.title }}</h1>
    <p>{{ item.description }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import * as api from '@/api/products'

const route = useRoute()
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

onMounted(() => {
  fetchData()
})
</script>
```

## 文件位置速查

| 功能 | 位置 |
|------|------|
| 用户登录 | `/views/auth/Login.vue` |
| 产品列表 | `/views/products/ProductList.vue` |
| 产品详情 | `/views/products/ProductDetail.vue` |
| AI对话 | `/views/chat/ChatPage.vue` |
| 个人中心 | `/views/user/Profile.vue` |
| 用户 API | `/api/auth.ts` |
| 产品 API | `/api/products.ts` |
| 对话 API | `/api/chat.ts` |
| 用户 Store | `/stores/user.ts` |
| 产品 Store | `/stores/product.ts` |
| 对话 Store | `/stores/chat.ts` |
| 路由配置 | `/router/index.ts` |
| 用户类型 | `/types/user.ts` |
| 产品类型 | `/types/product.ts` |
| 对话类型 | `/types/chat.ts` |

## 调试技巧

### 在浏览器控制台访问
```javascript
// 访问 Pinia Store
$pinia

// 访问路由
$route
$router

// 访问 Vue 组件（在 Vue DevTools 中选中组件后）
$vm
```

### 常见错误解决

**错误**: `Module not found`
```
解决: 检查导入路径，使用 @/ 别名
```

**错误**: `Cannot read property 'xxx' of undefined`
```
解决: 检查数据是否已加载，使用 v-if 或可选链操作符
```

**错误**: `Type 'xxx' is not assignable to type 'yyy'`
```
解决: 检查类型定义，确保类型匹配
```

## 性能检查清单

- [ ] 使用 v-if 隐藏而非 v-show 频繁切换的元素
- [ ] 列表使用 key 属性
- [ ] 避免在模板中调用方法
- [ ] 使用计算属性代替复杂逻辑
- [ ] 及时清理事件监听器
- [ ] 路由使用懒加载

## 代码审查清单

- [ ] TypeScript 没有 any 类型
- [ ] 变量名清晰有意义
- [ ] 函数不超过 50 行
- [ ] 组件不超过 200 行
- [ ] 有错误处理
- [ ] 有加载状态
- [ ] 有空状态处理

## 常见业务逻辑

### 用户认证流程
```
1. 用户输入邮箱和密码
2. 点击登录按钮
3. 调用 userStore.login()
4. 保存 token 到 localStorage
5. 重定向到首页
6. 路由守卫检查认证状态
```

### 产品列表流程
```
1. 页面挂载时加载分类
2. 加载产品列表
3. 用户选择分类时过滤
4. 用户输入关键词搜索
5. 点击分页时加载新数据
6. 点击产品卡片进入详情
```

### 对话功能流程
```
1. 加载对话列表
2. 点击对话进入详情
3. 用户输入消息
4. 按 Enter 发送
5. 消息显示在列表中
6. 用户可删除消息或对话
```

## 文档链接

- **完整文档**: `COMPONENT_SUMMARY.md`
- **开发指南**: `DEVELOPMENT_GUIDE.md`
- **项目报告**: `PROJECT_REPORT.md`
- **生成总结**: `GENERATION_SUMMARY.md`

---

**提示**: 将此文件保存为书签，便于快速查阅！

