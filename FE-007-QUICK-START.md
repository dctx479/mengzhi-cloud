# 用户中心模块（FE-007）快速开始指南

## 快速导航

### 文件位置
```
E:\项目\数商\AI赋能云平台\frontend\src\
├── api/user.ts                    # API 服务层
├── types/user.ts                  # 类型定义
├── router/index.ts                # 路由配置
└── views/user/
    ├── UserCenter.vue             # 主布局
    ├── Profile.vue                # 个人资料
    ├── Orders.vue                 # 订单历史
    ├── Quota.vue                  # 配额管理
    ├── Settings.vue               # 偏好设置
    ├── Security.vue               # 安全中心
    └── *.test.ts                  # 测试文件
```

## 功能概览

### 1. 订单历史 (/user/orders)
- 查看所有订单记录
- 按状态、日期、关键词筛选
- 查看订单详情
- 支付或取消订单
- **关键 API**: getOrders, cancelOrder

### 2. 配额管理 (/user/quota)
- 查看 AI 对话、内容生成、文件存储配额
- 查看配额使用历史
- 升级到更高配额方案
- **关键 API**: getQuota, getQuotaHistory, purchaseQuota

### 3. 偏好设置 (/user/settings)
- 通知设置（邮件、短信）
- 隐私设置（资料公开）
- 语言和主题选择
- 数据导出和缓存管理
- **关键 API**: getSettings, updateSettings

### 4. 安全中心 (/user/security)
- 修改密码
- 绑定手机和邮箱
- 查看登录历史
- 设备管理（查看和登出）
- **关键 API**: changePassword, bindPhone, bindEmail, getSecurityLogs

### 5. 个人资料 (/user/profile)
- 查看和编辑个人信息
- 用户统计展示
- **保留原有功能**

## 运行项目

```bash
# 进入前端目录
cd E:\项目\数商\AI赋能云平台\frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 访问: http://localhost:5173/user/profile
```

## 测试

```bash
# 运行所有测试
npm run test

# 运行特定组件测试
npm run test Orders.test.ts

# 生成覆盖率报告
npm run test:coverage

# 启动 UI 测试查看器
npm run test:ui
```

## API 服务使用示例

### 获取订单列表
```typescript
import { getOrders } from '@/api/user'

const response = await getOrders({
  page: 1,
  page_size: 10,
  status: 'completed'
})
```

### 获取配额信息
```typescript
import { getQuota, getQuotaHistory } from '@/api/user'

const quota = await getQuota()
const history = await getQuotaHistory({
  page: 1,
  page_size: 10
})
```

### 修改密码
```typescript
import { changePassword } from '@/api/user'

await changePassword({
  old_password: '旧密码',
  new_password: '新密码',
  confirm_password: '新密码'
})
```

### 绑定手机
```typescript
import { bindPhone, sendVerificationCode } from '@/api/user'

// 先发送验证码
await sendVerificationCode({
  type: 'phone',
  target: '13800138000'
})

// 然后绑定
await bindPhone({
  phone: '13800138000',
  verification_code: '123456'
})
```

## 页面访问

| 页面 | 路由 | 说明 |
|------|------|------|
| 个人资料 | `/user/profile` | 查看和编辑个人信息 |
| 订单历史 | `/user/orders` | 查看所有订单 |
| 配额管理 | `/user/quota` | 查看和升级配额 |
| 偏好设置 | `/user/settings` | 自定义用户设置 |
| 安全中心 | `/user/security` | 账户安全管理 |

## 组件结构

### UserCenter.vue (主布局)
- 左侧导航菜单
- 面包屑导航
- 路由容器

### 子页面组件
- Orders.vue - 订单列表和详情
- Quota.vue - 配额显示和升级
- Settings.vue - 用户设置表单
- Security.vue - 安全管理功能
- Profile.vue - 个人资料（原有）

## 关键功能实现

### 筛选和搜索
Orders 页面支持：
- 按状态筛选
- 按日期范围筛选
- 按关键词搜索

### 配额展示
Quota 页面展示：
- 进度条可视化
- 使用百分比
- 升级建议
- 历史记录

### 表单验证
Security 页面表单：
- 密码强度验证
- 邮箱格式验证
- 手机号格式验证
- 验证码倒计时

### 响应式设计
所有页面支持：
- 桌面端 (1920px+)
- 平板端 (768px-1024px)
- 移动端 (<768px)

## 常见问题

### Q1: 如何扩展新的配额类型？
在 Quota.vue 中修改 quotaData 结构和 upgradePlans 数组

### Q2: 如何自定义升级方案价格？
在 Quota.vue 的 upgradePlans 数据中修改 price 字段

### Q3: 如何修改验证规则？
在各组件的 xxx.test.ts 中修改对应的 Rules 对象

### Q4: 如何添加新的菜单项？
在 UserCenter.vue 的菜单部分添加新的 el-menu-item

## 后续开发

### 需要实现的后端 API
1. GET /api/user/orders - 获取订单列表
2. GET /api/user/orders/:id - 获取订单详情
3. POST /api/user/orders/:id/cancel - 取消订单
4. GET /api/user/quota - 获取配额
5. GET /api/user/quota/history - 获取配额历史
6. POST /api/user/quota/purchase - 购买配额
7. GET/PUT /api/user/settings - 获取/更新设置
8. POST /api/user/security/change-password - 修改密码
9. POST /api/user/security/bind-phone - 绑定手机
10. POST /api/user/security/bind-email - 绑定邮箱
11. GET /api/user/security/logs - 获取登录日志
12. GET /api/user/security/devices - 获取设备列表

## 开发建议

1. **本地开发**: 使用 `npm run dev` 启动开发服务器
2. **实时测试**: 使用 `npm run test:ui` 查看测试结果
3. **类型检查**: 使用 `npm run typecheck` 检查 TypeScript
4. **代码格式**: 使用 `npm run lint` 格式化代码
5. **生产构建**: 使用 `npm run build` 生成生产版本

## 支持

如有问题，请查看：
- 详细实现报告: `FE-007-USERCENTER-DELIVERY-REPORT.md`
- API 文档: `api/user.ts` 中的注释
- 类型定义: `types/user.ts` 中的接口
- 测试用例: `*.test.ts` 文件中的测试
