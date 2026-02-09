# 前端测试用例

**项目**: 内蒙古农畜产品品牌营销AI赋能云平台
**版本**: v1.0.0
**编写日期**: [项目完成日期]
**测试框架**: Vitest + React Testing Library

---

## 目录

- [1. 页面级测试用例](#1-页面级测试用例)
- [2. 组件级测试用例](#2-组件级测试用例)
- [3. 路由测试用例](#3-路由测试用例)
- [4. 状态管理测试用例](#4-状态管理测试用例)
- [5. API集成测试用例](#5-api集成测试用例)

---

## 1. 页面级测试用例

### 1.1 登录页面 (LoginPage)

#### TC-FE-LOGIN-001: 页面渲染 - 初始状态

**优先级**: P0
**文件**: `src/pages/LoginPage.tsx`

**测试步骤**:
1. 渲染登录页面组件
2. 验证初始元素存在

**预期结果**:
- 显示"登录"标题
- 显示用户名输入框
- 显示密码输入框
- 显示"登录"按钮
- 显示"还没有账号？立即注册"链接
- 所有输入框为空
- 登录按钮可点击

**测试代码示例**:
```typescript
import { render, screen } from '@testing-library/react'
import { LoginPage } from './LoginPage'

describe('LoginPage', () => {
  it('renders login form correctly', () => {
    render(<LoginPage />)

    expect(screen.getByRole('heading', { name: /登录/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/用户名/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/密码/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument()
    expect(screen.getByText(/还没有账号/i)).toBeInTheDocument()
  })
})
```

---

#### TC-FE-LOGIN-002: 表单验证 - 空字段

**优先级**: P0

**测试步骤**:
1. 不填写任何字段
2. 点击"登录"按钮

**预期结果**:
- 显示"请输入用户名"错误提示
- 显示"请输入密码"错误提示
- 不调用登录API
- 焦点移动到第一个错误字段

---

#### TC-FE-LOGIN-003: 表单验证 - 用户名太短

**优先级**: P1

**测试步骤**:
1. 输入用户名: "ab"（少于3个字符）
2. 输入有效密码
3. 点击"登录"按钮

**预期结果**:
- 显示"用户名至少3个字符"错误提示
- 不调用登录API

---

#### TC-FE-LOGIN-004: 表单提交 - 成功登录

**优先级**: P0

**测试步骤**:
1. 输入用户名: "test_user"
2. 输入密码: "Test123!"
3. 点击"登录"按钮
4. API返回成功响应

**预期结果**:
- 显示加载状态（按钮禁用，显示loading图标）
- 调用 POST /api/v1/auth/login
- 请求body包含正确的用户名和密码
- 成功后:
  - 保存Token到localStorage
  - 显示成功提示
  - 跳转到首页（/）

**测试代码示例**:
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LoginPage } from './LoginPage'
import { vi } from 'vitest'

describe('LoginPage - Login Flow', () => {
  it('handles successful login', async () => {
    const mockNavigate = vi.fn()
    vi.mock('react-router-dom', () => ({
      useNavigate: () => mockNavigate
    }))

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          code: 200,
          data: {
            tokens: {
              access_token: 'mock_token',
              refresh_token: 'mock_refresh'
            }
          }
        })
      })
    )

    render(<LoginPage />)

    await userEvent.type(screen.getByLabelText(/用户名/i), 'test_user')
    await userEvent.type(screen.getByLabelText(/密码/i), 'Test123!')
    await userEvent.click(screen.getByRole('button', { name: /登录/i }))

    await waitFor(() => {
      expect(localStorage.getItem('access_token')).toBe('mock_token')
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })
})
```

---

#### TC-FE-LOGIN-005: 表单提交 - 登录失败（密码错误）

**优先级**: P0

**测试步骤**:
1. 输入有效用户名
2. 输入错误密码
3. 点击"登录"按钮
4. API返回401错误

**预期结果**:
- 显示错误提示: "密码错误"
- 不保存Token
- 不跳转页面
- 密码输入框被清空
- 焦点回到密码输入框

---

#### TC-FE-LOGIN-006: 表单提交 - 网络错误

**优先级**: P1

**测试步骤**:
1. 输入有效凭据
2. 点击登录
3. 网络请求失败

**预期结果**:
- 显示错误提示: "网络连接失败，请检查网络"
- 登录按钮恢复可点击状态
- 用户可以重试

---

#### TC-FE-LOGIN-007: 记住我 - 功能测试

**优先级**: P2

**测试步骤**:
1. 勾选"记住我"复选框
2. 输入凭据并登录
3. 关闭浏览器
4. 重新打开

**预期结果**:
- 用户名输入框自动填充
- 密码输入框不填充（安全考虑）
- "记住我"复选框保持勾选状态

---

#### TC-FE-LOGIN-008: 注册链接 - 跳转

**优先级**: P0

**测试步骤**:
1. 点击"立即注册"链接

**预期结果**:
- 跳转到注册页面（/register）

---

### 1.2 注册页面 (RegisterPage)

#### TC-FE-REGISTER-001: 页面渲染 - 初始状态

**优先级**: P0
**文件**: `src/pages/RegisterPage.tsx`

**测试步骤**:
1. 渲染注册页面

**预期结果**:
- 显示"注册"标题
- 显示用户类型选择（个人/企业）
- 显示用户名输入框
- 显示邮箱输入框
- 显示密码输入框
- 显示确认密码输入框
- 显示验证码输入框
- 显示"发送验证码"按钮
- 显示"注册"按钮
- 显示"已有账号？立即登录"链接

---

#### TC-FE-REGISTER-002: 用户类型切换 - 个人/企业

**优先级**: P0

**测试步骤**:
1. 初始选择"个人用户"
2. 切换到"企业用户"
3. 再切换回"个人用户"

**预期结果**:
- 切换到企业用户时:
  - 显示"企业名称"输入框
  - 显示"营业执照号"输入框
- 切换回个人用户时:
  - 隐藏企业相关字段

---

#### TC-FE-REGISTER-003: 表单验证 - 邮箱格式

**优先级**: P0

**测试步骤**:
1. 输入无效邮箱: "invalid-email"
2. 离开邮箱输入框（blur事件）

**预期结果**:
- 显示"邮箱格式不正确"错误提示
- 邮箱输入框显示错误样式（红色边框）

---

#### TC-FE-REGISTER-004: 表单验证 - 密码强度

**优先级**: P0

**测试步骤**:
1. 输入弱密码: "12345678"（无字母）
2. 离开密码输入框

**预期结果**:
- 显示"密码必须包含字母和数字"错误提示
- 显示密码强度指示器（弱）

---

#### TC-FE-REGISTER-005: 表单验证 - 确认密码不一致

**优先级**: P0

**测试步骤**:
1. 输入密码: "Test123!"
2. 输入确认密码: "Test456!"
3. 离开确认密码输入框

**预期结果**:
- 显示"两次密码不一致"错误提示

---

#### TC-FE-REGISTER-006: 发送验证码 - 邮箱有效

**优先级**: P0

**测试步骤**:
1. 输入有效邮箱
2. 点击"发送验证码"按钮
3. API返回成功

**预期结果**:
- 按钮文字变为"60s后重新发送"
- 开始倒计时
- 按钮禁用60秒
- 显示成功提示: "验证码已发送"
- 60秒后按钮恢复可点击

---

#### TC-FE-REGISTER-007: 发送验证码 - 邮箱未填写

**优先级**: P1

**测试步骤**:
1. 不填写邮箱
2. 点击"发送验证码"按钮

**预期结果**:
- 显示错误提示: "请先输入邮箱"
- 焦点移动到邮箱输入框

---

#### TC-FE-REGISTER-008: 注册提交 - 成功注册

**优先级**: P0

**测试步骤**:
1. 填写所有必填字段
2. 输入验证码
3. 点击"注册"按钮
4. API返回成功

**预期结果**:
- 调用 POST /api/v1/auth/register
- 显示成功提示
- 3秒后自动跳转到登录页面
- 显示"注册成功，请登录"提示

---

#### TC-FE-REGISTER-009: 注册提交 - 用户名已存在

**优先级**: P0

**测试步骤**:
1. 输入已存在的用户名
2. 填写其他字段
3. 提交注册
4. API返回400错误

**预期结果**:
- 显示错误提示: "该用户名已被注册"
- 用户名输入框显示错误样式
- 焦点移动到用户名输入框

---

### 1.3 产品列表页面 (ProductsPage)

#### TC-FE-PRODUCTS-001: 页面渲染 - 加载状态

**优先级**: P0
**文件**: `src/pages/ProductsPage.tsx`

**测试步骤**:
1. 渲染产品列表页面
2. API请求进行中

**预期结果**:
- 显示加载骨架屏或Loading图标
- 不显示产品卡片
- 不显示错误消息

---

#### TC-FE-PRODUCTS-002: 页面渲染 - 数据加载成功

**优先级**: P0

**测试步骤**:
1. 渲染页面
2. API返回10个产品

**预期结果**:
- 显示10个产品卡片
- 每个卡片显示:
  - 产品图片（或占位图）
  - 产品名称
  - 产品类别
  - 价格
  - 产地
  - "查看详情"按钮
- 不显示加载状态

**测试代码示例**:
```typescript
import { render, screen, waitFor } from '@testing-library/react'
import { ProductsPage } from './ProductsPage'

describe('ProductsPage', () => {
  it('displays products after loading', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          code: 200,
          data: {
            items: [
              { id: 1, name: '草原牛肉', category: '肉类', price: 199.99, region: '呼伦贝尔' }
            ],
            pagination: { page: 1, total: 1 }
          }
        })
      })
    )

    render(<ProductsPage />)

    await waitFor(() => {
      expect(screen.getByText('草原牛肉')).toBeInTheDocument()
      expect(screen.getByText('¥199.99')).toBeInTheDocument()
      expect(screen.getByText('肉类')).toBeInTheDocument()
    })
  })
})
```

---

#### TC-FE-PRODUCTS-003: 页面渲染 - 空数据

**优先级**: P1

**测试步骤**:
1. 渲染页面
2. API返回空数组

**预期结果**:
- 显示空状态提示
- 提示文字: "暂无产品"
- 显示空状态图标
- 不显示产品卡片

---

#### TC-FE-PRODUCTS-004: 搜索功能 - 关键词搜索

**优先级**: P0

**测试步骤**:
1. 在搜索框输入"牛肉"
2. 点击搜索按钮或按Enter键
3. 等待结果

**预期结果**:
- 调用 GET /api/v1/products?search=牛肉
- URL参数更新: ?search=牛肉
- 显示搜索结果
- 搜索框保持输入的关键词

---

#### TC-FE-PRODUCTS-005: 筛选功能 - 类别筛选

**优先级**: P0

**测试步骤**:
1. 点击"肉类"类别标签
2. 等待结果

**预期结果**:
- 调用 GET /api/v1/products?category=肉类
- URL参数更新
- 只显示"肉类"产品
- "肉类"标签显示选中状态

---

#### TC-FE-PRODUCTS-006: 筛选功能 - 产地筛选

**优先级**: P1

**测试步骤**:
1. 在产地下拉框选择"内蒙古呼伦贝尔"

**预期结果**:
- 调用 GET /api/v1/products?region=内蒙古呼伦贝尔
- 只显示呼伦贝尔产品

---

#### TC-FE-PRODUCTS-007: 排序功能 - 按价格升序

**优先级**: P0

**测试步骤**:
1. 点击排序下拉框
2. 选择"价格从低到高"

**预期结果**:
- 调用 GET /api/v1/products?sort_by=price&sort_order=asc
- 产品按价格升序排列
- 最便宜的产品在最前面

---

#### TC-FE-PRODUCTS-008: 分页功能 - 下一页

**优先级**: P0

**测试步骤**:
1. 页面显示第1页（共3页）
2. 点击"下一页"按钮

**预期结果**:
- 调用 GET /api/v1/products?page=2
- URL参数更新: ?page=2
- 显示第2页产品
- "上一页"按钮变为可点击
- 页码显示"2 / 3"

---

#### TC-FE-PRODUCTS-009: 分页功能 - 首页禁用"上一页"

**优先级**: P1

**测试步骤**:
1. 在第1页

**预期结果**:
- "上一页"按钮禁用状态
- "下一页"按钮可点击（如有下一页）

---

#### TC-FE-PRODUCTS-010: 无限滚动 - 触底加载

**优先级**: P2（可选功能）

**测试步骤**:
1. 滚动到页面底部
2. 触发加载更多

**预期结果**:
- 调用下一页API
- 新产品追加到列表末尾
- 显示加载中状态
- 到达最后一页时不再加载

---

#### TC-FE-PRODUCTS-011: 点击产品卡片 - 跳转详情

**优先级**: P0

**测试步骤**:
1. 点击产品卡片或"查看详情"按钮

**预期结果**:
- 跳转到产品详情页: /products/1
- 携带产品ID

---

#### TC-FE-PRODUCTS-012: 错误处理 - API请求失败

**优先级**: P1

**测试步骤**:
1. API返回500错误

**预期结果**:
- 显示错误提示
- 提示文字: "加载失败，请稍后重试"
- 显示"重试"按钮
- 点击重试重新发起请求

---

### 1.4 产品详情页面 (ProductDetailPage)

#### TC-FE-PRODUCT-DETAIL-001: 页面渲染 - 加载状态

**优先级**: P0

**测试步骤**:
1. 访问 /products/1
2. API请求中

**预期结果**:
- 显示加载骨架屏

---

#### TC-FE-PRODUCT-DETAIL-002: 页面渲染 - 数据加载成功

**优先级**: P0

**测试步骤**:
1. API返回产品详情

**预期结果**:
- 显示产品图片轮播（如有多张）
- 显示产品基本信息:
  - 产品名称
  - SKU
  - 价格
  - 类别
  - 产地
  - 库存状态
- 显示产品描述
- 显示文化信息:
  - 文化标签
  - 文化介绍
  - 产品起源故事
  - 功效说明
  - 使用方法

---

#### TC-FE-PRODUCT-DETAIL-003: 产品不存在 - 404页面

**优先级**: P0

**测试步骤**:
1. 访问不存在的产品: /products/9999
2. API返回404

**预期结果**:
- 显示404提示
- 提示文字: "产品不存在"
- 显示"返回产品列表"按钮

---

#### TC-FE-PRODUCT-DETAIL-004: 图片轮播 - 切换功能

**优先级**: P1

**测试步骤**:
1. 产品有3张图片
2. 点击"下一张"按钮

**预期结果**:
- 显示第2张图片
- 指示器更新（2/3）
- 可循环切换

---

#### TC-FE-PRODUCT-DETAIL-005: 返回按钮 - 导航

**优先级**: P0

**测试步骤**:
1. 点击"返回"按钮

**预期结果**:
- 返回到产品列表页
- 保留之前的筛选和分页状态

---

### 1.5 AI对话页面 (ChatPage)

#### TC-FE-CHAT-001: 页面渲染 - 初始状态

**优先级**: P0
**文件**: `src/pages/ChatPage.tsx`

**测试步骤**:
1. 渲染AI对话页面

**预期结果**:
- 显示对话列表（左侧边栏）
- 显示空的聊天区域
- 显示消息输入框
- 显示"发送"按钮
- 显示"新建对话"按钮

---

#### TC-FE-CHAT-002: 发送消息 - 正常流程

**优先级**: P0

**测试步骤**:
1. 在输入框输入: "请介绍内蒙古特色产品"
2. 点击"发送"按钮
3. API返回成功

**预期结果**:
- 用户消息立即显示在聊天区域
- 输入框被清空
- 发送按钮禁用（等待回复）
- AI消息显示在聊天区域（带有打字机效果）
- 发送按钮恢复可点击

---

#### TC-FE-CHAT-003: 发送消息 - 流式响应

**优先级**: P0

**测试步骤**:
1. 发送消息
2. 接收SSE流式响应

**预期结果**:
- AI消息逐字显示（打字机效果）
- 每收到一个delta，追加到消息末尾
- 滚动条自动滚动到底部
- 收到"completed"后停止

**测试代码示例**:
```typescript
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatPage } from './ChatPage'

describe('ChatPage - Streaming', () => {
  it('handles streaming response', async () => {
    // Mock SSE
    const mockEventSource = {
      addEventListener: vi.fn(),
      close: vi.fn()
    }
    global.EventSource = vi.fn(() => mockEventSource) as any

    render(<ChatPage />)

    await userEvent.type(screen.getByPlaceholderText(/输入消息/i), '你好')
    await userEvent.click(screen.getByRole('button', { name: /发送/i }))

    // 模拟SSE事件
    const messageHandler = mockEventSource.addEventListener.mock.calls[0][1]
    messageHandler({ data: JSON.stringify({ delta: '你', content: '你' }) })
    messageHandler({ data: JSON.stringify({ delta: '好', content: '你好' }) })
    messageHandler({ data: JSON.stringify({ status: 'completed' }) })

    await waitFor(() => {
      expect(screen.getByText(/你好/)).toBeInTheDocument()
    })
  })
})
```

---

#### TC-FE-CHAT-004: 发送消息 - 输入为空

**优先级**: P1

**测试步骤**:
1. 不输入任何内容
2. 点击"发送"按钮

**预期结果**:
- 发送按钮禁用状态（或点击无效）
- 不调用API

---

#### TC-FE-CHAT-005: 发送消息 - 超长消息

**优先级**: P1

**测试步骤**:
1. 输入超过10000字符
2. 尝试发送

**预期结果**:
- 显示错误提示: "消息内容最长10000字符"
- 不发送消息

---

#### TC-FE-CHAT-006: 对话列表 - 显示历史对话

**优先级**: P0

**测试步骤**:
1. 用户有3个历史对话
2. 加载页面

**预期结果**:
- 左侧显示3个对话项
- 每个对话项显示:
  - 对话标题
  - 最后一条消息时间
  - 消息数量
- 按时间倒序排列

---

#### TC-FE-CHAT-007: 对话列表 - 切换对话

**优先级**: P0

**测试步骤**:
1. 点击第2个对话项

**预期结果**:
- 调用 GET /api/v1/chat/conversations/2
- 聊天区域显示该对话的所有消息
- 该对话项高亮显示
- URL更新: /chat/2

---

#### TC-FE-CHAT-008: 新建对话 - 功能

**优先级**: P0

**测试步骤**:
1. 点击"新建对话"按钮

**预期结果**:
- 聊天区域清空
- 输入框获得焦点
- URL更新: /chat
- 发送第一条消息时创建新对话

---

#### TC-FE-CHAT-009: 删除对话 - 确认删除

**优先级**: P1

**测试步骤**:
1. 鼠标悬停在对话项上
2. 点击"删除"图标
3. 确认删除

**预期结果**:
- 显示确认对话框
- 点击"确认"后:
  - 调用 DELETE /api/v1/chat/conversations/1
  - 对话项从列表中移除
  - 如删除的是当前对话，切换到新建对话状态

---

#### TC-FE-CHAT-010: 消息反馈 - 点赞/点踩

**优先级**: P2

**测试步骤**:
1. 鼠标悬停在AI消息上
2. 点击"点赞"按钮

**预期结果**:
- 调用 POST /api/v1/chat/feedback
- 按钮变为选中状态
- 显示"感谢反馈"提示

---

#### TC-FE-CHAT-011: 错误处理 - 网络中断

**优先级**: P1

**测试步骤**:
1. 发送消息
2. 网络中断（SSE连接断开）

**预期结果**:
- 显示错误提示: "连接中断，请重试"
- 显示"重新发送"按钮
- 点击重新发送消息

---

#### TC-FE-CHAT-012: 自动滚动 - 新消息

**优先级**: P1

**测试步骤**:
1. 聊天区域有很多消息
2. 发送新消息

**预期结果**:
- 滚动条自动滚动到最底部
- 新消息可见

---

#### TC-FE-CHAT-013: 代理类型切换 - 小书/小商

**优先级**: P2（可选功能）

**测试步骤**:
1. 点击"切换代理"按钮
2. 选择"小书"

**预期结果**:
- 下次发送消息时agent_type参数为"xiaoshu"
- 显示当前代理类型图标

---

### 1.6 用户中心页面 (UserProfilePage)

#### TC-FE-PROFILE-001: 页面渲染 - 显示用户信息

**优先级**: P0

**测试步骤**:
1. 已登录用户访问用户中心

**预期结果**:
- 显示用户头像（或默认头像）
- 显示用户名
- 显示邮箱（脱敏）
- 显示用户类型（个人/企业）
- 显示注册时间

---

#### TC-FE-PROFILE-002: 编辑个人信息 - 更新昵称

**优先级**: P0

**测试步骤**:
1. 点击"编辑"按钮
2. 修改昵称为"张三"
3. 点击"保存"
4. API返回成功

**预期结果**:
- 调用 PUT /api/v1/auth/me
- 显示成功提示
- 昵称立即更新显示

---

#### TC-FE-PROFILE-003: 修改密码 - 正常流程

**优先级**: P0

**测试步骤**:
1. 点击"修改密码"
2. 输入旧密码
3. 输入新密码
4. 确认新密码
5. 提交
6. API返回成功

**预期结果**:
- 调用 POST /api/v1/auth/change-password
- 显示成功提示
- 提示用户重新登录
- 3秒后自动登出并跳转登录页

---

#### TC-FE-PROFILE-004: 修改密码 - 旧密码错误

**优先级**: P0

**测试步骤**:
1. 输入错误的旧密码
2. 提交

**预期结果**:
- 显示错误提示: "旧密码错误"
- 不清空输入框
- 焦点移到旧密码输入框

---

#### TC-FE-PROFILE-005: 登出功能

**优先级**: P0

**测试步骤**:
1. 点击"退出登录"按钮
2. 确认登出

**预期结果**:
- 调用 POST /api/v1/auth/logout
- 清除localStorage中的Token
- 跳转到登录页
- 显示"已退出登录"提示

---

## 2. 组件级测试用例

### 2.1 ProductCard组件

#### TC-FE-COMP-001: ProductCard - 基本渲染

**优先级**: P0
**文件**: `src/components/ProductCard.tsx`

**测试步骤**:
1. 渲染ProductCard组件
2. 传入产品数据

**预期结果**:
- 显示产品图片
- 显示产品名称
- 显示价格（格式化为¥199.99）
- 显示类别标签
- 显示产地

**测试代码示例**:
```typescript
import { render, screen } from '@testing-library/react'
import { ProductCard } from './ProductCard'

describe('ProductCard', () => {
  const mockProduct = {
    id: 1,
    name: '草原牛肉',
    price: 199.99,
    category: '肉类',
    region: '呼伦贝尔',
    image: '/images/beef.jpg'
  }

  it('renders product information correctly', () => {
    render(<ProductCard product={mockProduct} />)

    expect(screen.getByText('草原牛肉')).toBeInTheDocument()
    expect(screen.getByText('¥199.99')).toBeInTheDocument()
    expect(screen.getByText('肉类')).toBeInTheDocument()
    expect(screen.getByText('呼伦贝尔')).toBeInTheDocument()
    expect(screen.getByRole('img')).toHaveAttribute('src', '/images/beef.jpg')
  })
})
```

---

#### TC-FE-COMP-002: ProductCard - 点击事件

**优先级**: P0

**测试步骤**:
1. 点击ProductCard

**预期结果**:
- 触发onClick回调
- 传递产品ID

---

#### TC-FE-COMP-003: ProductCard - 缺货状态

**优先级**: P1

**测试步骤**:
1. 传入stock: 0的产品

**预期结果**:
- 显示"缺货"标签
- 卡片半透明显示
- 不可点击

---

#### TC-FE-COMP-004: ProductCard - 精选标记

**优先级**: P1

**测试步骤**:
1. 传入is_featured: true

**预期结果**:
- 显示"精选"徽章（右上角）

---

### 2.2 MessageBubble组件

#### TC-FE-COMP-005: MessageBubble - 用户消息

**优先级**: P0
**文件**: `src/components/MessageBubble.tsx`

**测试步骤**:
1. 渲染用户消息气泡

**预期结果**:
- 气泡靠右对齐
- 背景色为主题色（蓝色）
- 显示消息内容
- 显示时间戳

---

#### TC-FE-COMP-006: MessageBubble - AI消息

**优先级**: P0

**测试步骤**:
1. 渲染AI消息气泡

**预期结果**:
- 气泡靠左对齐
- 背景色为灰色
- 显示AI头像
- 显示消息内容
- 显示时间戳

---

#### TC-FE-COMP-007: MessageBubble - Markdown渲染

**优先级**: P1

**测试步骤**:
1. 传入包含Markdown的消息

**预期结果**:
- 正确渲染Markdown格式:
  - **粗体**
  - *斜体*
  - 列表
  - 代码块

---

#### TC-FE-COMP-008: MessageBubble - 复制功能

**优先级**: P2

**测试步骤**:
1. 鼠标悬停在消息上
2. 点击"复制"按钮

**预期结果**:
- 消息内容复制到剪贴板
- 显示"已复制"提示

---

### 2.3 Pagination组件

#### TC-FE-COMP-009: Pagination - 基本渲染

**优先级**: P0
**文件**: `src/components/Pagination.tsx`

**测试步骤**:
1. 渲染分页组件
2. 传入总数100，每页10，当前第1页

**预期结果**:
- 显示"上一页"按钮（禁用）
- 显示"下一页"按钮
- 显示页码"1 / 10"
- 显示"共100条"

---

#### TC-FE-COMP-010: Pagination - 点击下一页

**优先级**: P0

**测试步骤**:
1. 点击"下一页"按钮

**预期结果**:
- 触发onPageChange回调
- 传递page: 2

---

#### TC-FE-COMP-011: Pagination - 最后一页

**优先级**: P1

**测试步骤**:
1. 当前在第10页（最后一页）

**预期结果**:
- "下一页"按钮禁用
- "上一页"按钮可点击

---

### 2.4 SearchBar组件

#### TC-FE-COMP-012: SearchBar - 基本渲染

**优先级**: P0
**文件**: `src/components/SearchBar.tsx`

**测试步骤**:
1. 渲染搜索栏组件

**预期结果**:
- 显示搜索输入框
- 显示搜索图标按钮
- 显示placeholder: "搜索产品..."

---

#### TC-FE-COMP-013: SearchBar - 输入搜索

**优先级**: P0

**测试步骤**:
1. 输入"牛肉"
2. 按Enter键

**预期结果**:
- 触发onSearch回调
- 传递关键词: "牛肉"

---

#### TC-FE-COMP-014: SearchBar - 清空搜索

**优先级**: P1

**测试步骤**:
1. 输入框有内容
2. 点击"清空"按钮

**预期结果**:
- 输入框内容清空
- 触发onSearch回调，传递空字符串
- 清空按钮隐藏

---

### 2.5 FilterPanel组件

#### TC-FE-COMP-015: FilterPanel - 类别筛选

**优先级**: P0
**文件**: `src/components/FilterPanel.tsx`

**测试步骤**:
1. 渲染筛选面板
2. 点击"肉类"标签

**预期结果**:
- "肉类"标签高亮
- 触发onFilterChange回调
- 传递{ category: '肉类' }

---

#### TC-FE-COMP-016: FilterPanel - 多条件筛选

**优先级**: P0

**测试步骤**:
1. 选择类别: "肉类"
2. 选择产地: "呼伦贝尔"

**预期结果**:
- 触发onFilterChange回调
- 传递{ category: '肉类', region: '呼伦贝尔' }

---

#### TC-FE-COMP-017: FilterPanel - 重置筛选

**优先级**: P1

**测试步骤**:
1. 选择多个筛选条件
2. 点击"重置"按钮

**预期结果**:
- 所有筛选条件清空
- 触发onFilterChange回调，传递{}
- 所有标签恢复未选中状态

---

## 3. 路由测试用例

### TC-FE-ROUTE-001: 路由配置 - 页面映射

**优先级**: P0

**测试步骤**:
1. 访问各个路由

**预期结果**:
- `/` → HomePage
- `/login` → LoginPage
- `/register` → RegisterPage
- `/products` → ProductsPage
- `/products/:id` → ProductDetailPage
- `/chat` → ChatPage
- `/profile` → UserProfilePage

---

### TC-FE-ROUTE-002: 路由守卫 - 未登录访问保护页面

**优先级**: P0

**测试步骤**:
1. 未登录状态
2. 访问 /profile

**预期结果**:
- 重定向到 /login
- URL参数包含redirect: /profile
- 登录成功后重定向回 /profile

---

### TC-FE-ROUTE-003: 路由守卫 - 已登录访问登录页

**优先级**: P1

**测试步骤**:
1. 已登录状态
2. 访问 /login

**预期结果**:
- 重定向到首页 /

---

### TC-FE-ROUTE-004: 404页面 - 不存在的路由

**优先级**: P1

**测试步骤**:
1. 访问 /non-existent-page

**预期结果**:
- 显示404页面
- 显示"页面不存在"提示
- 显示"返回首页"按钮

---

## 4. 状态管理测试用例

### TC-FE-STATE-001: 用户状态 - 登录后保存

**优先级**: P0

**测试步骤**:
1. 用户登录成功
2. 检查全局状态

**预期结果**:
- user state包含用户信息
- isAuthenticated为true
- token已保存

---

### TC-FE-STATE-002: 用户状态 - 登出后清除

**优先级**: P0

**测试步骤**:
1. 用户登出

**预期结果**:
- user state清空
- isAuthenticated为false
- token被移除

---

### TC-FE-STATE-003: Token自动刷新

**优先级**: P0

**测试步骤**:
1. Token即将过期（剩余5分钟）
2. 发起任意API请求

**预期结果**:
- 自动调用refresh接口
- 更新token
- 原始请求继续执行

---

## 5. API集成测试用例

### TC-FE-API-001: 请求拦截器 - 自动添加Token

**优先级**: P0

**测试步骤**:
1. 已登录状态
2. 发起API请求

**预期结果**:
- 请求Header自动包含Authorization
- 格式: Bearer <access_token>

---

### TC-FE-API-002: 响应拦截器 - Token过期处理

**优先级**: P0

**测试步骤**:
1. API返回401，code: 20003

**预期结果**:
- 自动调用refresh接口
- 刷新成功后重试原请求
- 刷新失败后跳转登录页

---

### TC-FE-API-003: 错误处理 - 网络错误

**优先级**: P1

**测试步骤**:
1. 网络断开
2. 发起请求

**预期结果**:
- 显示错误提示: "网络连接失败"
- 不抛出未捕获异常

---

### TC-FE-API-004: 错误处理 - 业务错误

**优先级**: P1

**测试步骤**:
1. API返回400，code: 10001

**预期结果**:
- 显示API返回的错误消息
- errors数组中的字段错误高亮显示

---

## 测试覆盖率目标

- 组件覆盖率: ≥80%
- 函数覆盖率: ≥70%
- 分支覆盖率: ≥60%
- 行覆盖率: ≥75%

---

**文档版本**: v1.0
**最后更新**: [项目完成日期]
**维护团队**: 前端开发团队
