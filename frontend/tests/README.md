# 前端测试说明文档

## 概述

本项目使用 **Vitest** 和 **Vue Test Utils** 进行单元测试和组件测试，目标覆盖率达到 **60%+**。

## 快速开始

### 安装依赖

```bash
npm install
```

### 运行测试

```bash
# 运行所有测试
npm test

# 运行测试并显示UI
npm run test:ui

# 生成覆盖率报告
npm run test:coverage
```

## 测试结构

```
frontend/tests/
├── setup.ts                          # Vitest全局设置
├── utils/
│   └── test-utils.ts                # 测试工具函数和数据生成器
├── mocks/
│   └── index.ts                     # Mock模块和函数
└── unit/
    ├── components/                  # 组件测试
    │   ├── ProductCard.test.ts
    │   ├── MessageBubble.test.ts
    │   └── Header.test.ts
    ├── views/                       # 页面测试（未来扩展）
    ├── stores/                      # Store测试
    │   ├── user.test.ts
    │   ├── product.test.ts
    │   └── chat.test.ts
    └── api/                         # API测试
        ├── auth.test.ts
        ├── products.test.ts
        └── chat.test.ts
```

## 测试覆盖

### 1. 组件测试

#### ProductCard (frontend/tests/unit/components/ProductCard.test.ts)

测试内容：
- Props渲染正确
- 产品名称、价格、描述显示
- 折扣徽章计算
- 库存状态显示
- 路由跳转
- 图片加载

测试用例数：12个

```typescript
// 示例：测试产品信息渲染
it('renders product information correctly', () => {
  const product = testDataGenerators.createProduct({
    name: '乌兰察布马铃薯',
    price: 5.99,
  })
  const wrapper = mount(ProductCard, { props: { product } })
  expect(wrapper.text()).toContain('乌兰察布马铃薯')
})
```

#### MessageBubble (frontend/tests/unit/components/MessageBubble.test.ts)

测试内容：
- 用户/AI消息样式区分
- 时间戳格式化
- 加载状态显示
- 长文本处理
- 特殊字符处理

测试用例数：15个

```typescript
// 示例：测试用户消息样式
it('renders user message correctly', () => {
  const message = testDataGenerators.createMessage({
    role: 'user',
    content: '你好',
  })
  const wrapper = mount(MessageBubble, { props: { message } })
  expect(wrapper.classes()).toContain('user-message')
})
```

#### Header (frontend/tests/unit/components/Header.test.ts)

测试内容：
- Logo和导航显示
- 登录/注册按钮（未登录）
- 用户菜单（已登录）
- 搜索功能
- 登出处理
- 响应式布局

测试用例数：14个

```typescript
// 示例：测试搜索功能
it('navigates to products page with search keyword', async () => {
  const wrapper = mount(Header, { ... })
  const input = wrapper.find('.el-input')
  await input.setValue('马铃薯')
  await input.trigger('keyup.enter')
  expect(mockRouter.push).toHaveBeenCalled()
})
```

### 2. Store测试

#### User Store (frontend/tests/unit/stores/user.test.ts)

测试内容：
- 登录/登出/注册
- Token管理
- 用户信息更新
- localStorage持久化
- 认证检查

测试用例数：25个

```typescript
// 示例：测试登录
it('sets user and token on successful login', async () => {
  const store = useUserStore()
  vi.mocked(authAPI.login).mockResolvedValueOnce({
    user: testDataGenerators.createUser(),
    token: 'test-token',
    expiresIn: 3600,
  })
  await store.login('test@example.com', 'password')
  expect(store.isLoggedIn).toBe(true)
})
```

#### Product Store (frontend/tests/unit/stores/product.test.ts)

测试内容：
- 产品列表获取
- 分类管理
- 搜索筛选
- 分页功能
- 筛选状态重置

测试用例数：23个

```typescript
// 示例：测试分类过滤
it('filteredProducts filters by category', () => {
  const store = useProductStore()
  store.products.value = [
    testDataGenerators.createProduct({ categoryId: 'cat-1' }),
    testDataGenerators.createProduct({ categoryId: 'cat-2' }),
  ]
  store.selectedCategory.value = 'cat-1'
  expect(store.filteredProducts).toHaveLength(1)
})
```

#### Chat Store (frontend/tests/unit/stores/chat.test.ts)

测试内容：
- 对话列表管理
- 消息发送/接收
- 对话创建/删除
- 消息状态管理
- 消息排序

测试用例数：28个

```typescript
// 示例：测试消息发送
it('sends message and updates state', async () => {
  const store = useChatStore()
  store.currentChat.value = testDataGenerators.createChat()
  vi.mocked(chatAPI.sendMessage).mockResolvedValueOnce(
    testDataGenerators.createMessage()
  )
  await store.sendMessage('你好')
  expect(store.messages).toHaveLength(2)
})
```

### 3. API测试

#### Auth API (frontend/tests/unit/api/auth.test.ts)

测试内容：
- 登录请求
- 注册请求
- Token验证
- 用户信息获取
- 错误处理

测试用例数：14个

#### Products API (frontend/tests/unit/api/products.test.ts)

测试内容：
- 产品列表获取
- 产品详情获取
- 分类列表获取
- 参数传递
- 错误处理

测试用例数：16个

#### Chat API (frontend/tests/unit/api/chat.test.ts)

测试内容：
- 对话列表获取
- 对话详情获取
- 消息发送
- 对话管理（创建/删除/清空）
- 错误处理

测试用例数：19个

## 测试工具函数

### 组件挂载辅助函数

```typescript
import { mountComponent } from '../utils/test-utils'

// 挂载组件（自动配置路由和Pinia）
const wrapper = mountComponent(MyComponent, {
  props: { /* ... */ },
  router: true,     // 启用路由
  pinia: true,      // 启用Pinia Store
})
```

### 数据生成器

```typescript
import { testDataGenerators } from '../utils/test-utils'

// 生成测试用户
const user = testDataGenerators.createUser({
  username: 'testuser',
  email: 'test@example.com',
})

// 生成测试产品
const product = testDataGenerators.createProduct({
  name: '乌兰察布马铃薯',
  price: 5.99,
})

// 生成测试消息
const message = testDataGenerators.createMessage({
  content: '你好',
  role: 'user',
})

// 生成测试对话
const chat = testDataGenerators.createChat({
  title: '产品咨询',
})

// 生成测试分类
const category = testDataGenerators.createCategory({
  name: '农产品',
})
```

### 异步操作辅助函数

```typescript
import {
  flushPromises,
  waitForComponent,
  triggerEvent,
  setInputValue,
} from '../utils/test-utils'

// 等待异步操作完成
await flushPromises()

// 等待组件更新
await waitForComponent(wrapper)

// 触发事件
await triggerEvent(wrapper, '.button', 'click')

// 设置输入框值
await setInputValue(wrapper, '.input', 'value')
```

### Mock辅助函数

```typescript
import { mockRouter, mockElMessage, resetAllMocks } from '../mocks/index'

// 使用Mock路由
expect(mockRouter.push).toHaveBeenCalledWith('/products')

// 使用Mock消息
expect(mockElMessage.success).toHaveBeenCalled()

// 重置所有Mock
resetAllMocks()
```

## 覆盖率报告

运行测试覆盖率命令后会生成HTML报告：

```bash
npm run test:coverage
```

报告位置：`frontend/coverage/index.html`

### 覆盖率目标

| 指标 | 目标 |
|------|------|
| 行覆盖率 | 60%+ |
| 分支覆盖率 | 60%+ |
| 函数覆盖率 | 60%+ |
| 语句覆盖率 | 60%+ |

## 编写测试的最佳实践

### 1. 测试命名

```typescript
// 好的实践
describe('ProductCard Component', () => {
  it('renders product name correctly', () => { ... })
  it('displays discount badge when originalPrice is provided', () => { ... })
})

// 避免
describe('Test', () => {
  it('works', () => { ... })
})
```

### 2. 测试结构 (AAA模式)

```typescript
it('should do something', () => {
  // Arrange - 准备
  const product = testDataGenerators.createProduct()
  const wrapper = mount(ProductCard, { props: { product } })

  // Act - 执行
  await wrapper.find('button').trigger('click')

  // Assert - 断言
  expect(wrapper.emitted('selected')).toBeTruthy()
})
```

### 3. Mock外部依赖

```typescript
// Mock API
vi.mock('@/api/products', () => ({
  getProductList: vi.fn(),
}))

// Mock路由
const mockRouter = {
  push: vi.fn(),
}

// Mock Pinia Store
setActivePinia(createPinia())
```

### 4. 测试隔离

```typescript
beforeEach(() => {
  // 清理状态
  vi.clearAllMocks()
  localStorage.clear()
  setActivePinia(createPinia())
})
```

### 5. 异步操作测试

```typescript
it('handles async operations', async () => {
  vi.mocked(someAPI).mockResolvedValueOnce(data)

  const promise = store.action()
  expect(store.loading).toBe(true)

  await promise
  expect(store.loading).toBe(false)
})
```

## 常见问题

### 1. Component不渲染

**问题**：组件测试时找不到元素

**解决方案**：
```typescript
// 确保有正确的stubs
const wrapper = mount(Component, {
  global: {
    stubs: {
      'el-button': { template: '<button><slot /></button>' },
    },
  },
})
```

### 2. Store状态未初始化

**问题**：Store测试失败

**解决方案**：
```typescript
beforeEach(() => {
  setActivePinia(createPinia())  // 必须在每个测试前重置
})
```

### 3. Mock函数未被调用

**问题**：Mock验证失败

**解决方案**：
```typescript
// 确保在beforeEach中清理Mock
beforeEach(() => {
  vi.clearAllMocks()
})
```

### 4. 时间相关测试

**问题**：时间戳格式化测试不稳定

**解决方案**：
```typescript
// 使用固定时间戳
const timestamp = '2024-01-15T14:30:00Z'
const message = testDataGenerators.createMessage({ timestamp })
```

## CI/CD集成

### GitHub Actions示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: npm test
      - run: npm run test:coverage
```

## 扩展测试

### 添加新的组件测试

1. 在 `frontend/tests/unit/components/` 目录下创建 `YourComponent.test.ts`
2. 使用test-utils中的工具函数
3. 运行 `npm test YourComponent.test.ts` 验证

### 添加新的Store测试

1. 在 `frontend/tests/unit/stores/` 目录下创建 `yourStore.test.ts`
2. Mock相关API
3. 测试所有action和computed

### 添加新的API测试

1. 在 `frontend/tests/unit/api/` 目录下创建 `yourApi.test.ts`
2. Mock axios
3. 测试所有API函数和错误处理

## 性能考虑

- 使用 `vi.mock()` 而不是 `vi.doMock()` 以获得更好的性能
- 合理使用 `beforeEach` 和 `afterEach` 避免重复设置
- 使用 `describe.skip()` 临时跳过测试而不是删除

## 调试

### 打印调试信息

```typescript
import { describe, it, expect } from 'vitest'

it('debug test', () => {
  const wrapper = mount(Component)
  console.log(wrapper.html())  // 打印HTML
  console.log(wrapper.vm)      // 打印组件实例
})
```

### 在浏览器中调试

```bash
npm run test:ui
```

会启动一个交互式UI，支持实时查看测试结果。

## 相关文档

- [Vitest官方文档](https://vitest.dev/)
- [Vue Test Utils文档](https://test-utils.vuejs.org/)
- [Pinia测试指南](https://pinia.vuejs.org/cookbook/testing.html)

## 统计信息

| 项目 | 数量 |
|------|------|
| 组件测试 | 3个 |
| 组件测试用例 | 41个 |
| Store测试 | 3个 |
| Store测试用例 | 76个 |
| API测试 | 3个 |
| API测试用例 | 49个 |
| **总测试用例** | **166个** |
| 预期覆盖率 | 60%+ |

## 贡献指南

编写新测试时请：
1. 遵循AAA模式（Arrange-Act-Assert）
2. 使用描述性的测试名称
3. 使用test-utils中的辅助函数
4. 保持测试独立和快速
5. 为复杂逻辑添加注释

---

**最后更新**：2024年1月
**维护者**：前端团队
