# API测试用例

**项目**: 内蒙古农畜产品品牌营销AI赋能云平台
**版本**: v1.0.0
**编写日期**: [项目完成日期]
**更新日期**: [项目完成日期]

---

## 目录

- [1. 认证API测试用例（8个端点）](#1-认证api测试用例)
- [2. 产品API测试用例（9个端点）](#2-产品api测试用例)
- [3. AI对话API测试用例（6个端点）](#3-ai对话api测试用例)
- [4. 测试数据](#4-测试数据)

---

## 1. 认证API测试用例

### 1.1 用户注册 - POST /api/v1/auth/register

#### TC-AUTH-001: 个人用户注册 - 正常流程

**优先级**: P0
**前置条件**: 无
**测试数据**: 见附录A-1

**测试步骤**:
1. 调用 POST /api/v1/auth/register
2. 提供有效参数:
   ```json
   {
     "username": "test_user_001",
     "email": "test001@example.com",
     "password": "Test123!@#",
     "user_type": "personal",
     "verification_code": "123456"
   }
   ```

**预期结果**:
- HTTP状态码: 201
- 响应body:
  ```json
  {
    "code": 200,
    "message": "注册成功",
    "data": {
      "user_id": "<UUID>",
      "username": "test_user_001",
      "email": "test001@example.com",
      "user_type": "personal",
      "created_at": "<timestamp>"
    }
  }
  ```
- 数据库验证:
  - users表有新记录
  - password字段已加密（bcrypt）
  - created_at不为空
  - status为"active"

**测试执行**: ✅ 通过 | ❌ 失败 | ⏸️ 阻塞
**实际结果**:
**备注**:

---

#### TC-AUTH-002: 企业用户注册 - 正常流程

**优先级**: P0
**前置条件**: 无
**测试数据**: 见附录A-2

**测试步骤**:
1. 调用 POST /api/v1/auth/register
2. 提供企业用户参数:
   ```json
   {
     "username": "test_enterprise_001",
     "email": "ent001@example.com",
     "password": "Enterprise123!",
     "user_type": "enterprise",
     "verification_code": "123456",
     "enterprise_name": "测试企业有限公司",
     "enterprise_license": "91150100MA0N1234X5"
   }
   ```

**预期结果**:
- HTTP状态码: 201
- 响应code: 200
- data.user_type: "enterprise"
- 数据库users表有企业信息

---

#### TC-AUTH-003: 注册 - 用户名重复

**优先级**: P0
**前置条件**: 用户名"test_user_001"已存在
**测试数据**: 见附录A-1

**测试步骤**:
1. 使用已存在的用户名注册

**预期结果**:
- HTTP状态码: 400
- 响应:
  ```json
  {
    "code": 10001,
    "message": "参数验证失败",
    "errors": [
      {
        "field": "username",
        "message": "该用户名已被注册"
      }
    ]
  }
  ```

---

#### TC-AUTH-004: 注册 - 邮箱重复

**优先级**: P0
**前置条件**: 邮箱"test001@example.com"已存在

**测试步骤**:
1. 使用已存在的邮箱注册

**预期结果**:
- HTTP状态码: 400
- 响应code: 10001
- errors包含"该邮箱已被注册"

---

#### TC-AUTH-005: 注册 - 手机号重复

**优先级**: P0
**前置条件**: 手机号"13800138000"已存在

**测试步骤**:
1. 使用已存在的手机号注册

**预期结果**:
- HTTP状态码: 400
- 响应code: 10001
- errors包含"该手机号已被注册"

---

#### TC-AUTH-006: 注册 - 密码格式无效（太短）

**优先级**: P1
**前置条件**: 无

**测试步骤**:
1. 提供密码: "abc123"（少于8个字符）

**预期结果**:
- HTTP状态码: 422（FastAPI验证错误）
- 或 400 + code: 10001

---

#### TC-AUTH-007: 注册 - 密码格式无效（无数字）

**优先级**: P1
**前置条件**: 无

**测试步骤**:
1. 提供密码: "abcdefgh"（无数字）

**预期结果**:
- HTTP状态码: 400 或 422
- 错误消息: "密码必须包含字母和数字"

---

#### TC-AUTH-008: 注册 - 密码格式无效（无字母）

**优先级**: P1
**前置条件**: 无

**测试步骤**:
1. 提供密码: "12345678"（无字母）

**预期结果**:
- HTTP状态码: 400 或 422
- 错误消息: "密码必须包含字母和数字"

---

#### TC-AUTH-009: 注册 - 缺少邮箱和手机号

**优先级**: P0
**前置条件**: 无

**测试步骤**:
1. 不提供email和phone字段

**预期结果**:
- HTTP状态码: 400 或 422
- 错误消息: "邮箱和手机号至少提供一个"

---

#### TC-AUTH-010: 注册 - 邮箱格式无效

**优先级**: P1
**前置条件**: 无

**测试步骤**:
1. 提供邮箱: "invalid-email"

**预期结果**:
- HTTP状态码: 400 或 422
- 错误消息: "邮箱格式不正确"

---

#### TC-AUTH-011: 注册 - 手机号格式无效

**优先级**: P1
**前置条件**: 无

**测试步骤**:
1. 提供手机号: "123456"（少于11位）

**预期结果**:
- HTTP状态码: 400 或 422
- 错误消息: "手机号格式不正确"

---

#### TC-AUTH-012: 注册 - 验证码无效

**优先级**: P1
**前置条件**: 无

**测试步骤**:
1. 提供验证码: "000000"（错误的验证码）

**预期结果**:
- HTTP状态码: 400
- 响应code: 20015
- 错误消息: "验证码无效"

---

#### TC-AUTH-013: 注册 - 验证码已过期

**优先级**: P1
**前置条件**: 验证码已超过有效期（5分钟）

**测试步骤**:
1. 使用5分钟前的验证码

**预期结果**:
- HTTP状态码: 400
- 响应code: 20016
- 错误消息: "验证码已过期"

---

#### TC-AUTH-014: 注册 - 企业用户缺少企业信息

**优先级**: P0
**前置条件**: 无

**测试步骤**:
1. user_type: "enterprise"
2. 不提供enterprise_name或enterprise_license

**预期结果**:
- HTTP状态码: 400 或 422
- 错误消息: "企业用户必须提供企业名称和营业执照号"

---

#### TC-AUTH-015: 注册 - 用户名格式无效（包含特殊字符）

**优先级**: P2
**前置条件**: 无

**测试步骤**:
1. 提供用户名: "test@user"（包含@）

**预期结果**:
- HTTP状态码: 400 或 422
- 错误消息: "用户名只能包含字母、数字、下划线、连字符"

---

#### TC-AUTH-016: 注册 - 用户名太短

**优先级**: P2
**前置条件**: 无

**测试步骤**:
1. 提供用户名: "ab"（少于3个字符）

**预期结果**:
- HTTP状态码: 400 或 422
- 错误消息: "用户名长度必须在3-50字符之间"

---

### 1.2 用户登录 - POST /api/v1/auth/login

#### TC-AUTH-017: 登录 - 使用用户名（正常）

**优先级**: P0
**前置条件**: 用户"test_user_001"已注册
**测试数据**: 见附录A-1

**测试步骤**:
1. 调用 POST /api/v1/auth/login
2. 提供参数:
   ```json
   {
     "username": "test_user_001",
     "password": "Test123!@#"
   }
   ```

**预期结果**:
- HTTP状态码: 200
- 响应:
  ```json
  {
    "code": 200,
    "message": "登录成功",
    "data": {
      "user": {
        "user_id": "<UUID>",
        "username": "test_user_001",
        "email": "te***@example.com",  // 脱敏
        "user_type": "personal",
        "status": "active",
        "role": "user"
      },
      "tokens": {
        "access_token": "<JWT>",
        "refresh_token": "<JWT>",
        "token_type": "Bearer",
        "expires_in": 1800
      }
    }
  }
  ```
- Token验证:
  - access_token可解码，包含user_id
  - refresh_token可解码
  - expires_in = 1800（30分钟）

---

#### TC-AUTH-018: 登录 - 使用邮箱（正常）

**优先级**: P0
**前置条件**: 用户已注册

**测试步骤**:
1. 使用邮箱登录:
   ```json
   {
     "username": "test001@example.com",
     "password": "Test123!@#"
   }
   ```

**预期结果**:
- HTTP状态码: 200
- 响应code: 200
- 返回access_token和refresh_token

---

#### TC-AUTH-019: 登录 - 使用手机号（正常）

**优先级**: P0
**前置条件**: 用户已注册

**测试步骤**:
1. 使用手机号登录:
   ```json
   {
     "username": "13800138000",
     "password": "Test123!@#"
   }
   ```

**预期结果**:
- HTTP状态码: 200
- 响应code: 200
- 返回tokens

---

#### TC-AUTH-020: 登录 - 用户不存在

**优先级**: P0
**前置条件**: 无

**测试步骤**:
1. 使用不存在的用户名登录

**预期结果**:
- HTTP状态码: 404
- 响应:
  ```json
  {
    "code": 20010,
    "message": "用户不存在"
  }
  ```

---

#### TC-AUTH-021: 登录 - 密码错误

**优先级**: P0
**前置条件**: 用户已注册

**测试步骤**:
1. 使用错误密码登录

**预期结果**:
- HTTP状态码: 401
- 响应:
  ```json
  {
    "code": 20011,
    "message": "密码错误"
  }
  ```

---

#### TC-AUTH-022: 登录 - 密码错误5次锁定

**优先级**: P0
**前置条件**: 用户已注册

**测试步骤**:
1. 连续5次使用错误密码登录
2. 第6次使用正确密码登录

**预期结果**:
- 前5次: HTTP 401, code: 20011
- 第6次: HTTP 403, code: 20013
- 错误消息: "账号已锁定，请30分钟后再试"

---

#### TC-AUTH-023: 登录 - 账号已禁用

**优先级**: P1
**前置条件**: 用户状态为"disabled"

**测试步骤**:
1. 使用已禁用账号登录

**预期结果**:
- HTTP状态码: 403
- 响应code: 20012
- 错误消息: "账号已禁用"

---

#### TC-AUTH-024: 登录 - 缺少密码

**优先级**: P2
**前置条件**: 无

**测试步骤**:
1. 只提供username，不提供password

**预期结果**:
- HTTP状态码: 422（FastAPI验证错误）
- 或 400 + code: 10002

---

### 1.3 刷新Token - POST /api/v1/auth/refresh

#### TC-AUTH-025: 刷新Token - 正常流程

**优先级**: P0
**前置条件**: 用户已登录，有refresh_token

**测试步骤**:
1. 调用 POST /api/v1/auth/refresh
2. 提供参数:
   ```json
   {
     "refresh_token": "<valid_refresh_token>"
   }
   ```

**预期结果**:
- HTTP状态码: 200
- 响应:
  ```json
  {
    "code": 200,
    "message": "Token刷新成功",
    "data": {
      "access_token": "<new_jwt>",
      "refresh_token": "<new_jwt>",
      "token_type": "Bearer",
      "expires_in": 1800
    }
  }
  ```
- 验证:
  - 新token与旧token不同
  - 旧token立即失效
  - 新token可用于API调用

---

#### TC-AUTH-026: 刷新Token - Token无效

**优先级**: P0
**前置条件**: 无

**测试步骤**:
1. 提供无效的refresh_token: "invalid_token_string"

**预期结果**:
- HTTP状态码: 401
- 响应code: 20005
- 错误消息: "无效的刷新令牌"

---

#### TC-AUTH-027: 刷新Token - Token已过期

**优先级**: P1
**前置条件**: refresh_token已超过7天有效期

**测试步骤**:
1. 使用过期的refresh_token

**预期结果**:
- HTTP状态码: 401
- 响应code: 20006
- 错误消息: "刷新令牌已过期"

---

#### TC-AUTH-028: 刷新Token - 使用access_token刷新

**优先级**: P2
**前置条件**: 用户已登录

**测试步骤**:
1. 使用access_token作为refresh_token

**预期结果**:
- HTTP状态码: 401
- 响应code: 20005
- 错误消息: "无效的刷新令牌"

---

### 1.4 用户登出 - POST /api/v1/auth/logout

#### TC-AUTH-029: 登出 - 正常流程

**优先级**: P0
**前置条件**: 用户已登录

**测试步骤**:
1. 调用 POST /api/v1/auth/logout
2. Header: Authorization: Bearer <access_token>

**预期结果**:
- HTTP状态码: 200
- 响应:
  ```json
  {
    "code": 200,
    "message": "登出成功",
    "data": {
      "message": "已成功登出"
    }
  }
  ```
- 验证:
  - Token加入黑名单（Redis）
  - 使用该token访问其他API返回401

---

#### TC-AUTH-030: 登出 - 未提供Token

**优先级**: P0
**前置条件**: 无

**测试步骤**:
1. 不提供Authorization Header

**预期结果**:
- HTTP状态码: 401
- 响应code: 20001
- 错误消息: "未提供认证令牌"

---

#### TC-AUTH-031: 登出 - Token无效

**优先级**: P1
**前置条件**: 无

**测试步骤**:
1. 提供无效Token

**预期结果**:
- HTTP状态码: 401
- 响应code: 20002
- 错误消息: "认证令牌无效"

---

### 1.5 获取当前用户信息 - GET /api/v1/auth/me

#### TC-AUTH-032: 获取用户信息 - 正常流程

**优先级**: P0
**前置条件**: 用户已登录

**测试步骤**:
1. 调用 GET /api/v1/auth/me
2. Header: Authorization: Bearer <access_token>

**预期结果**:
- HTTP状态码: 200
- 响应:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "user_id": "<UUID>",
      "username": "test_user_001",
      "email": "te***@example.com",  // 脱敏
      "phone": "138****8000",         // 脱敏
      "nickname": null,
      "avatar_url": null,
      "gender": 0,
      "user_type": "personal",
      "status": "active",
      "role": "user",
      "created_at": "<timestamp>",
      "last_login_at": "<timestamp>"
    }
  }
  ```

---

#### TC-AUTH-033: 获取用户信息 - 未登录

**优先级**: P0
**前置条件**: 无

**测试步骤**:
1. 不提供Token

**预期结果**:
- HTTP状态码: 401
- 响应code: 20001

---

#### TC-AUTH-034: 获取用户信息 - Token过期

**优先级**: P0
**前置条件**: access_token已过期

**测试步骤**:
1. 使用过期Token

**预期结果**:
- HTTP状态码: 401
- 响应code: 20003
- 错误消息: "认证令牌已过期，请重新登录"

---

### 1.6 更新用户信息 - PUT /api/v1/auth/me

#### TC-AUTH-035: 更新用户信息 - 正常流程

**优先级**: P0
**前置条件**: 用户已登录

**测试步骤**:
1. 调用 PUT /api/v1/auth/me
2. Header: Authorization: Bearer <access_token>
3. Body:
   ```json
   {
     "nickname": "张三",
     "avatar_url": "https://example.com/avatar.jpg",
     "gender": 1
   }
   ```

**预期结果**:
- HTTP状态码: 200
- 响应:
  ```json
  {
    "code": 200,
    "message": "个人信息更新成功",
    "data": {
      "updated": true
    }
  }
  ```
- 数据库验证:
  - nickname已更新
  - avatar_url已更新
  - gender已更新
  - updated_at时间戳已更新

---

#### TC-AUTH-036: 更新用户信息 - 部分字段

**优先级**: P1
**前置条件**: 用户已登录

**测试步骤**:
1. 只更新nickname字段

**预期结果**:
- HTTP状态码: 200
- 只有nickname被更新
- 其他字段保持不变

---

#### TC-AUTH-037: 更新用户信息 - 昵称太长

**优先级**: P2
**前置条件**: 用户已登录

**测试步骤**:
1. 提供超过100字符的昵称

**预期结果**:
- HTTP状态码: 400 或 422
- 错误消息: "昵称最长100字符"

---

#### TC-AUTH-038: 更新用户信息 - 性别值无效

**优先级**: P2
**前置条件**: 用户已登录

**测试步骤**:
1. 提供gender: 5（无效值）

**预期结果**:
- HTTP状态码: 400 或 422
- 错误消息: "性别值必须为0/1/2"

---

### 1.7 修改密码 - POST /api/v1/auth/change-password

#### TC-AUTH-039: 修改密码 - 正常流程

**优先级**: P0
**前置条件**: 用户已登录

**测试步骤**:
1. 调用 POST /api/v1/auth/change-password
2. Header: Authorization: Bearer <access_token>
3. Body:
   ```json
   {
     "old_password": "Test123!@#",
     "new_password": "NewPass123!"
   }
   ```
4. 使用新密码登录验证

**预期结果**:
- HTTP状态码: 200
- 响应:
  ```json
  {
    "code": 200,
    "message": "密码修改成功",
    "data": {
      "message": "密码修改成功",
      "changed_at": "<timestamp>"
    }
  }
  ```
- 验证:
  - 使用旧密码登录失败
  - 使用新密码登录成功
  - 数据库password已更新

---

#### TC-AUTH-040: 修改密码 - 旧密码错误

**优先级**: P0
**前置条件**: 用户已登录

**测试步骤**:
1. 提供错误的旧密码

**预期结果**:
- HTTP状态码: 401
- 响应code: 20011
- 错误消息: "密码错误"

---

#### TC-AUTH-041: 修改密码 - 新密码与旧密码相同

**优先级**: P1
**前置条件**: 用户已登录

**测试步骤**:
1. 新密码与旧密码相同

**预期结果**:
- HTTP状态码: 400
- 响应code: 10001
- 错误消息: "新密码不能与旧密码相同"

---

#### TC-AUTH-042: 修改密码 - 新密码格式无效

**优先级**: P1
**前置条件**: 用户已登录

**测试步骤**:
1. 提供格式不符合要求的新密码

**预期结果**:
- HTTP状态码: 400 或 422
- 错误消息: "密码必须同时包含字母和数字"

---

### 1.8 重置密码 - POST /api/v1/auth/reset-password

#### TC-AUTH-043: 重置密码 - 正常流程

**优先级**: P0
**前置条件**: 已发送验证码到邮箱

**测试步骤**:
1. 调用 POST /api/v1/auth/reset-password
2. Body:
   ```json
   {
     "identifier": "test001@example.com",
     "verification_code": "123456",
     "new_password": "ResetPass123!"
   }
   ```
3. 使用新密码登录验证

**预期结果**:
- HTTP状态码: 200
- 响应:
  ```json
  {
    "code": 200,
    "message": "密码重置成功",
    "data": {
      "message": "密码重置成功",
      "reset_at": "<timestamp>"
    }
  }
  ```
- 验证:
  - 使用新密码可以登录

---

#### TC-AUTH-044: 重置密码 - 验证码错误

**优先级**: P0
**前置条件**: 无

**测试步骤**:
1. 提供错误的验证码

**预期结果**:
- HTTP状态码: 400
- 响应code: 10001
- 错误消息: "验证码无效或已过期"

---

#### TC-AUTH-045: 重置密码 - 用户不存在

**优先级**: P1
**前置条件**: 无

**测试步骤**:
1. 提供不存在的邮箱

**预期结果**:
- HTTP状态码: 404
- 响应code: 20010
- 错误消息: "用户不存在"

---

## 2. 产品API测试用例

### 2.1 获取产品列表 - GET /api/v1/products

#### TC-PRODUCT-001: 获取产品列表 - 默认分页

**优先级**: P0
**前置条件**: 数据库有10个测试产品

**测试步骤**:
1. 调用 GET /api/v1/products

**预期结果**:
- HTTP状态码: 200
- 响应:
  ```json
  {
    "code": 200,
    "message": "获取产品列表成功",
    "data": {
      "items": [
        {
          "id": 1,
          "sku": "PROD-001",
          "name": "草原牛肉",
          "category": "肉类",
          "price": 199.99,
          "stock": 100,
          "region": "内蒙古呼伦贝尔",
          "status": "active",
          "is_featured": true,
          "created_at": "<timestamp>"
        }
        // ... 更多产品
      ],
      "pagination": {
        "page": 1,
        "size": 10,
        "total": 10,
        "pages": 1,
        "has_next": false,
        "has_prev": false
      }
    }
  }
  ```

---

#### TC-PRODUCT-002: 获取产品列表 - 自定义分页

**优先级**: P0
**前置条件**: 数据库有10个测试产品

**测试步骤**:
1. 调用 GET /api/v1/products?page=2&size=5

**预期结果**:
- HTTP状态码: 200
- pagination.page: 2
- pagination.size: 5
- items数量: 5
- pagination.has_prev: true
- pagination.has_next: false

---

#### TC-PRODUCT-003: 获取产品列表 - 搜索功能

**优先级**: P0
**前置条件**: 数据库有产品"草原牛肉"

**测试步骤**:
1. 调用 GET /api/v1/products?search=牛肉

**预期结果**:
- HTTP状态码: 200
- items中所有产品名称包含"牛肉"
- 或SKU包含"牛肉"

---

#### TC-PRODUCT-004: 获取产品列表 - 类别筛选

**优先级**: P0
**前置条件**: 数据库有"肉类"产品

**测试步骤**:
1. 调用 GET /api/v1/products?category=肉类

**预期结果**:
- HTTP状态码: 200
- items中所有产品category为"肉类"

---

#### TC-PRODUCT-005: 获取产品列表 - 产地筛选

**优先级**: P1
**前置条件**: 数据库有内蒙古产品

**测试步骤**:
1. 调用 GET /api/v1/products?region=内蒙古呼伦贝尔

**预期结果**:
- HTTP状态码: 200
- items中所有产品region为"内蒙古呼伦贝尔"

---

#### TC-PRODUCT-006: 获取产品列表 - 状态筛选

**优先级**: P0
**前置条件**: 数据库有active产品

**测试步骤**:
1. 调用 GET /api/v1/products?status=active

**预期结果**:
- HTTP状态码: 200
- items中所有产品status为"active"

---

#### TC-PRODUCT-007: 获取产品列表 - 精选产品筛选

**优先级**: P1
**前置条件**: 数据库有精选产品

**测试步骤**:
1. 调用 GET /api/v1/products?is_featured=true

**预期结果**:
- HTTP状态码: 200
- items中所有产品is_featured为true

---

#### TC-PRODUCT-008: 获取产品列表 - 按价格升序排序

**优先级**: P1
**前置条件**: 数据库有多个不同价格产品

**测试步骤**:
1. 调用 GET /api/v1/products?sort_by=price&sort_order=asc

**预期结果**:
- HTTP状态码: 200
- items按price从低到高排序

---

#### TC-PRODUCT-009: 获取产品列表 - 按创建时间降序排序

**优先级**: P1
**前置条件**: 数据库有产品

**测试步骤**:
1. 调用 GET /api/v1/products?sort_by=created_at&sort_order=desc

**预期结果**:
- HTTP状态码: 200
- items按created_at从新到旧排序

---

#### TC-PRODUCT-010: 获取产品列表 - 组合条件

**优先级**: P0
**前置条件**: 数据库有测试数据

**测试步骤**:
1. 调用 GET /api/v1/products?category=肉类&region=内蒙古&is_featured=true&sort_by=price&sort_order=asc

**预期结果**:
- HTTP状态码: 200
- 结果同时满足所有筛选条件
- 按价格升序排序

---

#### TC-PRODUCT-011: 获取产品列表 - 无效排序字段

**优先级**: P2
**前置条件**: 无

**测试步骤**:
1. 调用 GET /api/v1/products?sort_by=invalid_field

**预期结果**:
- HTTP状态码: 400
- 响应code: 10005
- 错误消息: "排序字段必须为: created_at, price, name, updated_at"

---

#### TC-PRODUCT-012: 获取产品列表 - 页码超出范围

**优先级**: P2
**前置条件**: 总共1页

**测试步骤**:
1. 调用 GET /api/v1/products?page=999

**预期结果**:
- HTTP状态码: 200
- items: []（空数组）
- pagination.page: 999
- pagination.total: 总数

---

### 2.2 获取产品详情 - GET /api/v1/products/{id}

#### TC-PRODUCT-013: 获取产品详情 - 正常流程

**优先级**: P0
**前置条件**: 产品ID=1存在

**测试步骤**:
1. 调用 GET /api/v1/products/1

**预期结果**:
- HTTP状态码: 200
- 响应:
  ```json
  {
    "code": 200,
    "message": "获取产品详情成功",
    "data": {
      "id": 1,
      "sku": "PROD-001",
      "name": "草原牛肉",
      "description": "来自内蒙古草原的优质牛肉...",
      "category": "肉类",
      "price": 199.99,
      "cost": 100.0,
      "stock": 100,
      "region": "内蒙古呼伦贝尔",
      "region_code": "NMG-HLB",
      "cultural_tags": ["草原", "有机", "绿色"],
      "cultural_description": "传统草原养殖文化...",
      "origin_story": "草原牛自由放牧...",
      "efficacy": "营养丰富...",
      "usage": "适合烧烤、炖汤...",
      "status": "active",
      "is_featured": true,
      "created_at": "<timestamp>",
      "updated_at": "<timestamp>",
      "created_by": 1,
      "updated_by": 1
    }
  }
  ```

---

#### TC-PRODUCT-014: 获取产品详情 - 产品不存在

**优先级**: P0
**前置条件**: 产品ID=9999不存在

**测试步骤**:
1. 调用 GET /api/v1/products/9999

**预期结果**:
- HTTP状态码: 404
- 响应code: 40010
- 错误消息: "记录不存在"

---

#### TC-PRODUCT-015: 获取产品详情 - 产品ID无效

**优先级**: P2
**前置条件**: 无

**测试步骤**:
1. 调用 GET /api/v1/products/abc

**预期结果**:
- HTTP状态码: 422（FastAPI验证错误）
- 或 400

---

### 2.3 创建产品 - POST /api/v1/products

#### TC-PRODUCT-016: 创建产品 - 正常流程（管理员）

**优先级**: P0
**前置条件**: 已登录为管理员
**测试数据**: 见附录B-1

**测试步骤**:
1. 调用 POST /api/v1/products
2. Header: Authorization: Bearer <admin_access_token>
3. Body:
   ```json
   {
     "sku": "PROD-NEW-001",
     "name": "测试新产品",
     "description": "这是测试产品",
     "category": "肉类",
     "price": 299.99,
     "cost": 150.0,
     "stock": 50,
     "region": "内蒙古呼伦贝尔",
     "region_code": "NMG-HLB",
     "cultural_tags": ["测试", "新品"],
     "cultural_description": "测试文化介绍",
     "status": "active",
     "is_featured": false
   }
   ```

**预期结果**:
- HTTP状态码: 201
- 响应code: 200
- 响应message: "产品创建成功"
- data包含新产品完整信息
- 数据库验证:
  - products表有新记录
  - created_by为当前管理员ID

---

#### TC-PRODUCT-017: 创建产品 - 非管理员

**优先级**: P0
**前置条件**: 已登录为普通用户

**测试步骤**:
1. 普通用户Token调用创建产品接口

**预期结果**:
- HTTP状态码: 403
- 响应code: 20020
- 错误消息: "权限不足"

---

#### TC-PRODUCT-018: 创建产品 - 未登录

**优先级**: P0
**前置条件**: 无

**测试步骤**:
1. 不提供Token调用接口

**预期结果**:
- HTTP状态码: 401
- 响应code: 20001
- 错误消息: "未提供认证令牌"

---

#### TC-PRODUCT-019: 创建产品 - SKU重复

**优先级**: P0
**前置条件**: SKU"PROD-001"已存在

**测试步骤**:
1. 管理员创建产品，使用已存在SKU

**预期结果**:
- HTTP状态码: 409
- 响应code: 40011
- 错误消息包含"SKU已存在"

---

#### TC-PRODUCT-020: 创建产品 - 缺少必填字段（名称）

**优先级**: P1
**前置条件**: 管理员已登录

**测试步骤**:
1. 不提供name字段

**预期结果**:
- HTTP状态码: 422 或 400
- 错误消息: "缺少必要参数"

---

#### TC-PRODUCT-021: 创建产品 - 价格为负数

**优先级**: P1
**前置条件**: 管理员已登录

**测试步骤**:
1. 提供price: -100

**预期结果**:
- HTTP状态码: 422 或 400
- 错误消息: "价格必须大于0"

---

#### TC-PRODUCT-022: 创建产品 - 库存为负数

**优先级**: P1
**前置条件**: 管理员已登录

**测试步骤**:
1. 提供stock: -10

**预期结果**:
- HTTP状态码: 422 或 400
- 错误消息: "库存必须≥0"

---

#### TC-PRODUCT-023: 创建产品 - 文化标签超过限制

**优先级**: P2
**前置条件**: 管理员已登录

**测试步骤**:
1. 提供21个文化标签（超过20个限制）

**预期结果**:
- HTTP状态码: 400 或 422
- 错误消息: "文化标签最多20个"

---

### 2.4 更新产品 - PUT /api/v1/products/{id}

#### TC-PRODUCT-024: 更新产品 - 正常流程（管理员）

**优先级**: P0
**前置条件**:
- 管理员已登录
- 产品ID=1存在

**测试步骤**:
1. 调用 PUT /api/v1/products/1
2. Header: Authorization: Bearer <admin_access_token>
3. Body:
   ```json
   {
     "name": "更新后的产品名称",
     "price": 249.99,
     "stock": 200
   }
   ```

**预期结果**:
- HTTP状态码: 200
- 响应code: 200
- 响应message: "产品更新成功"
- data包含更新后的产品信息
- 数据库验证:
  - name已更新
  - price已更新
  - stock已更新
  - updated_at时间戳已更新
  - updated_by为当前管理员ID

---

#### TC-PRODUCT-025: 更新产品 - 非管理员

**优先级**: P0
**前置条件**: 普通用户已登录

**测试步骤**:
1. 普通用户Token调用更新接口

**预期结果**:
- HTTP状态码: 403
- 响应code: 20020
- 错误消息: "权限不足"

---

#### TC-PRODUCT-026: 更新产品 - 产品不存在

**优先级**: P0
**前置条件**: 管理员已登录

**测试步骤**:
1. 调用 PUT /api/v1/products/9999

**预期结果**:
- HTTP状态码: 404
- 响应code: 40010
- 错误消息: "产品不存在"

---

#### TC-PRODUCT-027: 更新产品 - 请求体为空

**优先级**: P1
**前置条件**: 管理员已登录

**测试步骤**:
1. 提供空的JSON对象: {}

**预期结果**:
- HTTP状态码: 400
- 响应code: 10000
- 错误消息: "请求体不能为空"

---

#### TC-PRODUCT-028: 更新产品 - 部分字段更新

**优先级**: P1
**前置条件**: 管理员已登录

**测试步骤**:
1. 只更新price字段

**预期结果**:
- HTTP状态码: 200
- 只有price被更新
- 其他字段保持不变

---

### 2.5 删除产品 - DELETE /api/v1/products/{id}

#### TC-PRODUCT-029: 删除产品 - 正常流程（管理员）

**优先级**: P0
**前置条件**:
- 管理员已登录
- 产品ID=1存在

**测试步骤**:
1. 调用 DELETE /api/v1/products/1
2. Header: Authorization: Bearer <admin_access_token>

**预期结果**:
- HTTP状态码: 200
- 响应:
  ```json
  {
    "code": 200,
    "message": "产品删除成功",
    "data": {
      "id": 1
    }
  }
  ```
- 数据库验证:
  - products表记录status变为"deleted"（软删除）
  - 记录仍存在，未物理删除
  - 产品列表不再显示该产品

---

#### TC-PRODUCT-030: 删除产品 - 非管理员

**优先级**: P0
**前置条件**: 普通用户已登录

**测试步骤**:
1. 普通用户Token调用删除接口

**预期结果**:
- HTTP状态码: 403
- 响应code: 20020
- 错误消息: "权限不足"

---

#### TC-PRODUCT-031: 删除产品 - 产品不存在

**优先级**: P0
**前置条件**: 管理员已登录

**测试步骤**:
1. 调用 DELETE /api/v1/products/9999

**预期结果**:
- HTTP状态码: 404
- 响应code: 40010
- 错误消息: "产品不存在"

---

### 2.6 获取文化信息 - GET /api/v1/products/{id}/cultural-info

#### TC-PRODUCT-032: 获取文化信息 - 正常流程

**优先级**: P1
**前置条件**: 产品ID=1存在且有文化信息

**测试步骤**:
1. 调用 GET /api/v1/products/1/cultural-info

**预期结果**:
- HTTP状态码: 200
- 响应:
  ```json
  {
    "code": 200,
    "message": "获取文化信息成功",
    "data": {
      "cultural_tags": ["草原", "有机", "绿色"],
      "cultural_description": "传统草原养殖文化...",
      "origin_story": "草原牛自由放牧...",
      "efficacy": "营养丰富...",
      "usage": "适合烧烤、炖汤...",
      "region": "内蒙古呼伦贝尔",
      "region_code": "NMG-HLB"
    }
  }
  ```

---

#### TC-PRODUCT-033: 获取文化信息 - 产品不存在

**优先级**: P1
**前置条件**: 无

**测试步骤**:
1. 调用 GET /api/v1/products/9999/cultural-info

**预期结果**:
- HTTP状态码: 404
- 响应code: 40010
- 错误消息: "产品不存在"

---

### 2.7 获取分类列表 - GET /api/v1/products/categories/list

#### TC-PRODUCT-034: 获取分类列表 - 正常流程

**优先级**: P1
**前置条件**: 数据库有产品数据

**测试步骤**:
1. 调用 GET /api/v1/products/categories/list

**预期结果**:
- HTTP状态码: 200
- 响应:
  ```json
  {
    "code": 200,
    "message": "获取类别列表成功",
    "data": {
      "categories": [
        "肉类",
        "奶制品",
        "粮食",
        "蔬菜",
        "水果",
        "特色食品"
      ]
    }
  }
  ```
- 返回的类别列表是唯一的（去重）

---

### 2.8 获取产地列表 - GET /api/v1/products/regions/list

#### TC-PRODUCT-035: 获取产地列表 - 正常流程

**优先级**: P1
**前置条件**: 数据库有产品数据

**测试步骤**:
1. 调用 GET /api/v1/products/regions/list

**预期结果**:
- HTTP状态码: 200
- 响应:
  ```json
  {
    "code": 200,
    "message": "获取地区列表成功",
    "data": {
      "regions": [
        "内蒙古呼和浩特",
        "内蒙古包头",
        "内蒙古呼伦贝尔",
        "内蒙古兴安盟",
        "内蒙古通辽",
        "内蒙古赤峰",
        "内蒙古锡林郭勒",
        "内蒙古乌兰察布",
        "内蒙古鄂尔多斯",
        "内蒙古巴彦淖尔",
        "内蒙古乌海",
        "内蒙古阿拉善"
      ]
    }
  }
  ```

---

### 2.9 获取统计信息 - GET /api/v1/products/statistics

#### TC-PRODUCT-036: 获取统计信息 - 正常流程

**优先级**: P1
**前置条件**: 数据库有产品数据

**测试步骤**:
1. 调用 GET /api/v1/products/statistics

**预期结果**:
- HTTP状态码: 200
- 响应:
  ```json
  {
    "code": 200,
    "message": "获取统计信息成功",
    "data": {
      "total_products": 150,
      "active_products": 120,
      "inactive_products": 20,
      "draft_products": 10,
      "featured_products": 30,
      "total_categories": 6,
      "total_regions": 12,
      "out_of_stock_products": 5,
      "low_stock_products": 15
    }
  }
  ```
- 统计数字与数据库实际数据一致

---

## 3. AI对话API测试用例

### 3.1 发送消息（非流式） - POST /api/v1/chat/message

#### TC-CHAT-001: 发送消息 - 新对话

**优先级**: P0
**前置条件**: 用户已登录

**测试步骤**:
1. 调用 POST /api/v1/chat/message
2. Header: Authorization: Bearer <access_token>
3. Body:
   ```json
   {
     "content": "请介绍一下内蒙古的特色农产品",
     "conversation_id": null,
     "agent_type": "assistant"
   }
   ```

**预期结果**:
- HTTP状态码: 200
- 响应:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "id": "<message_uuid>",
      "conversation_id": 1,
      "message": {
        "id": "<message_uuid>",
        "conversation_id": 1,
        "role": "assistant",
        "content": "内蒙古拥有丰富的特色农产品...",
        "input_tokens": 15,
        "output_tokens": 120,
        "total_tokens": 135,
        "cost": 0.00027,
        "model": "deepseek-chat",
        "finish_reason": "stop",
        "created_at": "<timestamp>"
      },
      "usage": {
        "prompt_tokens": 15,
        "completion_tokens": 120,
        "total_tokens": 135
      }
    }
  }
  ```
- 数据库验证:
  - conversations表有新记录
  - messages表有2条记录（用户+助手）
  - conversation_id已返回

---

#### TC-CHAT-002: 发送消息 - 继续对话

**优先级**: P0
**前置条件**:
- 用户已登录
- 对话ID=1已存在

**测试步骤**:
1. 调用 POST /api/v1/chat/message
2. Body:
   ```json
   {
     "content": "草原牛肉有什么特点？",
     "conversation_id": 1
   }
   ```

**预期结果**:
- HTTP状态码: 200
- conversation_id: 1（与请求一致）
- message.content包含对草原牛肉的回答
- 回答考虑了上下文（之前的对话）

---

#### TC-CHAT-003: 发送消息 - 未登录

**优先级**: P0
**前置条件**: 无

**测试步骤**:
1. 不提供Token调用接口

**预期结果**:
- HTTP状态码: 401
- 响应code: 20001
- 错误消息: "未提供认证令牌"

---

#### TC-CHAT-004: 发送消息 - 内容为空

**优先级**: P1
**前置条件**: 用户已登录

**测试步骤**:
1. 提供content: ""

**预期结果**:
- HTTP状态码: 400 或 422
- 错误消息: "消息内容不能为空"

---

#### TC-CHAT-005: 发送消息 - 内容超长

**优先级**: P1
**前置条件**: 用户已登录

**测试步骤**:
1. 提供超过10000字符的content

**预期结果**:
- HTTP状态码: 400 或 422
- 错误消息: "消息内容最长10000字符"

---

#### TC-CHAT-006: 发送消息 - 对话不存在

**优先级**: P0
**前置条件**: 用户已登录

**测试步骤**:
1. 提供conversation_id: 9999（不存在）

**预期结果**:
- HTTP状态码: 404
- 响应code: 40010
- 错误消息: "对话不存在"

---

#### TC-CHAT-007: 发送消息 - 访问他人对话

**优先级**: P0
**前置条件**:
- 用户A已登录
- 对话ID=1属于用户B

**测试步骤**:
1. 用户A尝试向用户B的对话发送消息

**预期结果**:
- HTTP状态码: 403
- 响应code: 20020 或 20021
- 错误消息: "权限不足"或"资源访问被拒绝"

---

#### TC-CHAT-008: 发送消息 - 无效agent_type

**优先级**: P2
**前置条件**: 用户已登录

**测试步骤**:
1. 提供agent_type: "invalid_agent"

**预期结果**:
- HTTP状态码: 400 或 422
- 错误消息: "agent_type必须为: xiaoshu/xiaoshang/assistant"

---

### 3.2 发送消息（流式） - POST /api/v1/chat/stream

#### TC-CHAT-009: 流式消息 - 新对话

**优先级**: P0
**前置条件**: 用户已登录

**测试步骤**:
1. 调用 POST /api/v1/chat/stream
2. Header: Authorization: Bearer <access_token>
3. Body:
   ```json
   {
     "content": "请介绍一下内蒙古的特色农产品",
     "conversation_id": null
   }
   ```
4. 接收SSE流

**预期结果**:
- HTTP状态码: 200
- Content-Type: text/event-stream
- SSE数据流:
  ```
  data: {"conversation_id": 1, "delta": "内蒙古", "content": "内蒙古"}
  data: {"conversation_id": 1, "delta": "拥有", "content": "内蒙古拥有"}
  ...
  data: {"status": "completed"}
  ```
- 流式数据正确:
  - delta为增量内容
  - content为累积内容
  - 最后收到completed状态

---

#### TC-CHAT-010: 流式消息 - 中断重连

**优先级**: P1
**前置条件**: 用户已登录

**测试步骤**:
1. 开始接收流式消息
2. 中途断开连接
3. 验证数据库状态

**预期结果**:
- 部分消息已保存到数据库
- conversation状态正常
- 可重新发送消息继续对话

---

#### TC-CHAT-011: 流式消息 - 错误处理

**优先级**: P1
**前置条件**: 用户已登录

**测试步骤**:
1. 发送流式消息
2. DeepSeek API返回错误

**预期结果**:
- 收到SSE错误消息:
  ```
  data: {"error": true, "code": 50000, "message": "Stream processing failed"}
  ```
- 数据库记录错误状态

---

### 3.3 获取对话列表 - GET /api/v1/chat/conversations

#### TC-CHAT-012: 获取对话列表 - 默认参数

**优先级**: P0
**前置条件**:
- 用户已登录
- 用户有3个对话

**测试步骤**:
1. 调用 GET /api/v1/chat/conversations
2. Header: Authorization: Bearer <access_token>

**预期结果**:
- HTTP状态码: 200
- 响应:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "total": 3,
      "page": 1,
      "page_size": 20,
      "items": [
        {
          "id": 1,
          "conversation_uuid": "<uuid>",
          "user_id": 1,
          "title": "关于内蒙古特色农产品的讨论",
          "agent_type": "assistant",
          "context_product_id": null,
          "message_count": 5,
          "total_tokens": 1250,
          "status": "active",
          "last_message_at": "<timestamp>",
          "created_at": "<timestamp>"
        }
        // ... 更多对话
      ]
    }
  }
  ```
- 只返回当前用户的对话

---

#### TC-CHAT-013: 获取对话列表 - 分页

**优先级**: P1
**前置条件**: 用户有30个对话

**测试步骤**:
1. 调用 GET /api/v1/chat/conversations?page=2&page_size=10

**预期结果**:
- HTTP状态码: 200
- page: 2
- page_size: 10
- items数量: 10
- total: 30

---

#### TC-CHAT-014: 获取对话列表 - 状态筛选

**优先级**: P1
**前置条件**: 用户有active和archived对话

**测试步骤**:
1. 调用 GET /api/v1/chat/conversations?status=active

**预期结果**:
- HTTP状态码: 200
- items中所有对话status为"active"

---

#### TC-CHAT-015: 获取对话列表 - 按时间排序

**优先级**: P1
**前置条件**: 用户有多个对话

**测试步骤**:
1. 调用接口

**预期结果**:
- HTTP状态码: 200
- items按last_message_at降序排序（最新对话在前）

---

### 3.4 获取对话详情 - GET /api/v1/chat/conversations/{id}

#### TC-CHAT-016: 获取对话详情 - 正常流程

**优先级**: P0
**前置条件**:
- 用户已登录
- 对话ID=1存在且属于当前用户

**测试步骤**:
1. 调用 GET /api/v1/chat/conversations/1
2. Header: Authorization: Bearer <access_token>

**预期结果**:
- HTTP状态码: 200
- 响应:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "id": 1,
      "conversation_uuid": "<uuid>",
      "user_id": 1,
      "title": "关于内蒙古特色农产品的讨论",
      "agent_type": "assistant",
      "message_count": 3,
      "total_tokens": 450,
      "status": "active",
      "created_at": "<timestamp>",
      "updated_at": "<timestamp>",
      "messages": [
        {
          "id": 1,
          "message_uuid": "<uuid>",
          "conversation_id": 1,
          "role": "user",
          "content": "请介绍一下内蒙古的特色农产品",
          "created_at": "<timestamp>"
        },
        {
          "id": 2,
          "message_uuid": "<uuid>",
          "conversation_id": 1,
          "role": "assistant",
          "content": "内蒙古拥有丰富的特色农产品...",
          "input_tokens": 15,
          "output_tokens": 120,
          "total_tokens": 135,
          "cost": 0.00027,
          "model": "deepseek-chat",
          "created_at": "<timestamp>"
        }
        // ... 更多消息
      ]
    }
  }
  ```
- messages按时间升序排序

---

#### TC-CHAT-017: 获取对话详情 - 对话不存在

**优先级**: P0
**前置条件**: 用户已登录

**测试步骤**:
1. 调用 GET /api/v1/chat/conversations/9999

**预期结果**:
- HTTP状态码: 404
- 响应code: 40010
- 错误消息: "对话不存在"

---

#### TC-CHAT-018: 获取对话详情 - 访问他人对话

**优先级**: P0
**前置条件**:
- 用户A已登录
- 对话ID=1属于用户B

**测试步骤**:
1. 用户A调用 GET /api/v1/chat/conversations/1

**预期结果**:
- HTTP状态码: 403 或 404
- 错误消息: "权限不足"或"对话不存在"

---

#### TC-CHAT-019: 获取对话详情 - 使用UUID

**优先级**: P1
**前置条件**:
- 用户已登录
- 对话UUID存在

**测试步骤**:
1. 调用 GET /api/v1/chat/conversations/{conversation_uuid}

**预期结果**:
- HTTP状态码: 200
- 返回对话详情（与使用ID一致）

---

### 3.5 删除对话 - DELETE /api/v1/chat/conversations/{id}

#### TC-CHAT-020: 删除对话 - 正常流程

**优先级**: P0
**前置条件**:
- 用户已登录
- 对话ID=1存在且属于当前用户

**测试步骤**:
1. 调用 DELETE /api/v1/chat/conversations/1
2. Header: Authorization: Bearer <access_token>

**预期结果**:
- HTTP状态码: 200
- 响应:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "success": true,
      "message": "Conversation deleted successfully"
    }
  }
  ```
- 数据库验证:
  - conversation状态变为"deleted"（软删除）
  - 对话列表不再显示该对话
  - 记录仍存在于数据库

---

#### TC-CHAT-021: 删除对话 - 对话不存在

**优先级**: P0
**前置条件**: 用户已登录

**测试步骤**:
1. 调用 DELETE /api/v1/chat/conversations/9999

**预期结果**:
- HTTP状态码: 404
- 响应code: 40010
- 错误消息: "对话不存在"

---

#### TC-CHAT-022: 删除对话 - 删除他人对话

**优先级**: P0
**前置条件**:
- 用户A已登录
- 对话ID=1属于用户B

**测试步骤**:
1. 用户A调用 DELETE /api/v1/chat/conversations/1

**预期结果**:
- HTTP状态码: 403 或 404
- 错误消息: "权限不足"或"对话不存在"

---

### 3.6 对话反馈 - POST /api/v1/chat/feedback

#### TC-CHAT-023: 对话反馈 - 正常流程

**优先级**: P1
**前置条件**:
- 用户已登录
- 消息ID=2存在且为assistant消息

**测试步骤**:
1. 调用 POST /api/v1/chat/feedback
2. Header: Authorization: Bearer <access_token>
3. Body:
   ```json
   {
     "message_id": 2,
     "rating": 5,
     "feedback": "回答很详细，很有帮助",
     "feedback_type": "helpful"
   }
   ```

**预期结果**:
- HTTP状态码: 200
- 响应:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "message_id": 2,
      "rating": 5,
      "feedback": "回答很详细，很有帮助",
      "feedback_type": "helpful",
      "updated_at": "<timestamp>"
    }
  }
  ```
- 数据库验证:
  - messages表对应记录已更新反馈信息

---

#### TC-CHAT-024: 对话反馈 - 评分超出范围

**优先级**: P1
**前置条件**: 用户已登录

**测试步骤**:
1. 提供rating: 6（超过1-5范围）

**预期结果**:
- HTTP状态码: 400 或 422
- 错误消息: "评分必须在1-5之间"

---

#### TC-CHAT-025: 对话反馈 - 消息不存在

**优先级**: P1
**前置条件**: 用户已登录

**测试步骤**:
1. 提供message_id: 9999

**预期结果**:
- HTTP状态码: 404
- 响应code: 40010
- 错误消息: "消息不存在"

---

#### TC-CHAT-026: 对话反馈 - 反馈内容超长

**优先级**: P2
**前置条件**: 用户已登录

**测试步骤**:
1. 提供超过1000字符的feedback

**预期结果**:
- HTTP状态码: 400 或 422
- 错误消息: "反馈内容最长1000字符"

---

#### TC-CHAT-027: 对话反馈 - 无效反馈类型

**优先级**: P2
**前置条件**: 用户已登录

**测试步骤**:
1. 提供feedback_type: "invalid_type"

**预期结果**:
- HTTP状态码: 400 或 422
- 错误消息: "反馈类型必须为: helpful/unhelpful/incorrect"

---

## 4. 测试数据

### 附录A: 认证测试数据

#### A-1: 个人用户数据
```json
{
  "username": "test_user_001",
  "email": "test001@example.com",
  "phone": "13800138000",
  "password": "Test123!@#",
  "user_type": "personal",
  "verification_code": "123456"
}
```

#### A-2: 企业用户数据
```json
{
  "username": "test_enterprise_001",
  "email": "ent001@example.com",
  "phone": "13800138001",
  "password": "Enterprise123!",
  "user_type": "enterprise",
  "verification_code": "123456",
  "enterprise_name": "测试企业有限公司",
  "enterprise_license": "91150100MA0N1234X5"
}
```

### 附录B: 产品测试数据

#### B-1: 新产品数据
```json
{
  "sku": "PROD-NEW-001",
  "name": "测试新产品",
  "description": "这是一个测试产品描述",
  "category": "肉类",
  "price": 299.99,
  "cost": 150.0,
  "stock": 50,
  "region": "内蒙古呼伦贝尔",
  "region_code": "NMG-HLB",
  "cultural_tags": ["测试", "新品", "优质"],
  "cultural_description": "测试文化介绍内容",
  "origin_story": "测试产品起源故事",
  "efficacy": "测试功效说明",
  "usage": "测试使用方法",
  "status": "active",
  "is_featured": false
}
```

### 附录C: AI对话测试数据

#### C-1: 对话消息数据
```json
{
  "content": "请介绍一下内蒙古的特色农产品",
  "conversation_id": null,
  "agent_type": "assistant"
}
```

---

## 测试用例统计

### 总览

| 模块 | 测试用例数 | P0 | P1 | P2 |
|------|----------|----|----|-----|
| 认证API | 45 | 28 | 14 | 3 |
| 产品API | 36 | 20 | 12 | 4 |
| AI对话API | 27 | 15 | 10 | 2 |
| **合计** | **108** | **63** | **36** | **9** |

### 覆盖率

- API端点覆盖率: 23/23 = **100%**
- 正常流程覆盖: **100%**
- 异常流程覆盖: **≥80%**

---

**文档版本**: v1.0
**最后更新**: [项目完成日期]
**维护团队**: QA团队
