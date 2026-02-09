## 前端项目完整代码生成汇总

本文档汇总了所有生成的 Vue 3 + TypeScript + Element Plus 组件代码。

### 项目结构

```
frontend/
├── src/
│   ├── api/                          # API 服务层
│   │   ├── auth.ts                   # 认证 API
│   │   ├── chat.ts                   # 对话 API
│   │   └── products.ts               # 产品 API
│   │
│   ├── components/                   # 通用组件
│   │   ├── Header.vue                # 顶部导航栏
│   │   ├── Sidebar.vue               # 侧边栏菜单
│   │   ├── Loading.vue               # 加载组件
│   │   ├── Empty.vue                 # 空状态组件
│   │   ├── ProductCard.vue           # 产品卡片组件
│   │   └── chat/                     # AI对话组件
│   │       ├── MessageBubble.vue     # 消息气泡
│   │       ├── MessageList.vue       # 消息列表
│   │       └── MessageInput.vue      # 消息输入
│   │
│   ├── layouts/                      # 布局组件
│   │   └── MainLayout.vue            # 主布局
│   │
│   ├── stores/                       # Pinia 状态管理
│   │   ├── user.ts                   # 用户状态管理
│   │   ├── product.ts                # 产品状态管理
│   │   └── chat.ts                   # 对话状态管理
│   │
│   ├── types/                        # TypeScript 类型定义
│   │   ├── user.ts                   # 用户类型
│   │   ├── product.ts                # 产品类型
│   │   └── chat.ts                   # 对话类型
│   │
│   ├── views/                        # 页面组件
│   │   ├── Home.vue                  # 首页
│   │   ├── NotFound.vue              # 404 页面
│   │   ├── auth/                     # 认证页面
│   │   │   ├── Login.vue             # 登录页面
│   │   │   └── Register.vue          # 注册页面
│   │   ├── products/                 # 产品页面
│   │   │   ├── ProductList.vue       # 产品列表
│   │   │   └── ProductDetail.vue     # 产品详情
│   │   ├── user/                     # 用户页面
│   │   │   └── Profile.vue           # 个人中心
│   │   └── chat/                     # 对话页面
│   │       └── ChatPage.vue          # AI对话页面
│   │
│   ├── router/
│   │   └── index.ts                  # 路由配置（已更新）
│   │
│   ├── App.vue                       # 根组件
│   └── main.ts                       # 入口文件
```

### 核心功能说明

#### 1. 认证模块 (auth)
- **Login.vue**: 完整的登录页面
  - 邮箱和密码输入
  - 表单验证
  - 错误提示
  - 渐变背景设计

- **Register.vue**: 完整的注册页面
  - 用户名、邮箱、密码输入
  - 密码确认验证
  - 服务条款同意
  - 美观的分步布局

#### 2. 产品模块 (products)
- **ProductList.vue**: 产品列表页面
  - 分类筛选
  - 搜索功能
  - 分页加载
  - 响应式网格布局

- **ProductDetail.vue**: 产品详情页面
  - 图片展示和缩略图
  - 产品规格详情
  - 用户评价展示
  - 相关产品推荐

- **ProductCard.vue**: 产品卡片组件
  - 图片、价格、评分展示
  - 优惠标签
  - 库存状态
  - 快速操作按钮

#### 3. AI对话模块 (chat)
- **ChatPage.vue**: 完整的AI对话页面
  - 对话列表管理
  - 实时消息同步
  - 对话搜索
  - 删除和清空功能

- **MessageList.vue**: 消息列表组件
  - 消息自动滚动
  - 消息删除功能
  - 消息复制功能
  - 加载状态显示

- **MessageInput.vue**: 消息输入组件
  - 多行文本输入
  - 快捷键支持 (Shift+Enter换行)
  - 字数限制
  - 附件和设置按钮

- **MessageBubble.vue**: 消息气泡组件
  - 用户消息和AI响应区分
  - 时间戳显示
  - 加载动画
  - 消息状态显示

#### 4. 用户模块 (user)
- **Profile.vue**: 用户个人中心
  - 头像和基本信息展示
  - 资料编辑功能
  - 统计数据展示
  - 账号设置入口

#### 5. 布局模块 (layouts)
- **MainLayout.vue**: 主布局
  - Header + Sidebar + Main 三部分
  - 响应式设计
  - 侧边栏折叠功能

- **Header.vue**: 顶部导航栏
  - Logo 和导航菜单
  - 搜索功能
  - 用户菜单
  - 认证按钮

- **Sidebar.vue**: 侧边栏菜单
  - 导航菜单
  - 权限管理（Admin菜单）
  - 可折叠设计

#### 6. 通用组件 (components)
- **Loading.vue**: 加载组件
  - 旋转动画
  - 自定义加载文本
  - 全屏模式

- **Empty.vue**: 空状态组件
  - 多种空状态类型
  - 自定义操作按钮
  - Icon 图标展示

### 状态管理 (Stores)

#### useUserStore
```typescript
// 状态
- user: 当前用户信息
- isLoggedIn: 登录状态
- loading: 加载中
- error: 错误信息

// 方法
- login(): 登录
- register(): 注册
- logout(): 登出
- fetchCurrentUser(): 获取当前用户
- updateProfile(): 更新个人资料
- checkAuth(): 检查认证
- restoreFromStorage(): 从存储恢复
```

#### useProductStore
```typescript
// 状态
- products: 产品列表
- categories: 分类列表
- currentProduct: 当前产品
- selectedCategory: 选中分类
- searchKeyword: 搜索关键词
- currentPage: 当前页码

// 方法
- fetchProducts(): 获取产品列表
- fetchProductDetail(): 获取产品详情
- fetchCategories(): 获取分类
- setCategory(): 设置分类过滤
- setSearchKeyword(): 设置搜索
- setPage(): 设置页码
```

#### useChatStore
```typescript
// 状态
- chats: 对话列表
- currentChat: 当前对话
- messages: 消息列表
- loading: 加载中
- messageLoading: 消息加载中

// 方法
- fetchChats(): 获取对话列表
- fetchChatDetail(): 获取对话详情
- createNewChat(): 创建新对话
- sendMessage(): 发送消息
- deleteChat(): 删除对话
- clearChat(): 清空对话
- deleteMessage(): 删除单条消息
```

### API 服务

#### auth.ts
- login()
- register()
- logout()
- getCurrentUser()
- updateProfile()
- changePassword()
- verifyToken()

#### products.ts
- getProductList()
- getProductDetail()
- getCategories()
- getProductReviews()
- addProductReview()
- searchProducts()
- getPopularProducts()

#### chat.ts
- getChatList()
- getChatDetail()
- createChat()
- sendMessage()
- getChatHistory()
- deleteChat()
- clearChat()
- deleteMessage()

### 类型定义

#### User Types
- User: 用户基本信息
- UserProfile: 扩展用户信息
- LoginRequest/Response
- RegisterRequest/Response
- UpdateProfileRequest

#### Product Types
- Product: 产品基本信息
- ProductDetail: 扩展产品信息
- ProductListRequest/Response
- Category: 产品分类
- Review: 产品评价

#### Chat Types
- Message: 消息
- Chat: 对话
- ChatListResponse
- SendMessageRequest/Response

### 路由配置

路由已在 `/src/router/index.ts` 中完整配置：

```
/login              - 登录页面
/register           - 注册页面
/                   - 首页
/products           - 产品列表
/products/:id       - 产品详情
/chat               - AI对话
/user/profile       - 个人中心
/user/settings      - 账号设置
/:pathMatch(.*)*    - 404 页面
```

### 路由守卫

- 自动检查本地存储中的用户信息
- 访问受保护路由时自动登录验证
- 登录用户试图访问登录页面时自动重定向

### 特性

✅ Vue 3 Composition API (`<script setup>`)
✅ TypeScript 完整类型支持
✅ Element Plus 组件库集成
✅ Pinia 状态管理
✅ 响应式设计（PC + 移动端）
✅ 路由守卫和认证
✅ SCSS 样式支持
✅ 错误处理和加载状态
✅ 表单验证
✅ 国际化文本（中文）

### 使用说明

1. 确保项目依赖已安装
```bash
npm install
```

2. 配置环境变量
```bash
# .env.development
VITE_API_BASE=http://localhost:3000/api
```

3. 运行开发服务器
```bash
npm run dev
```

4. 构建生产版本
```bash
npm run build
```

### 注意事项

- 所有 API 调用都需要后端支持
- 认证流程使用 localStorage 存储 token
- 组件已适配 PC 和移动端
- 所有样式使用 SCSS，需要 sass 依赖
- 消息输入支持 Shift+Enter 换行，Enter 发送

