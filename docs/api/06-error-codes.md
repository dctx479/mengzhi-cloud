# 错误码文档

## 错误响应格式

所有API错误响应遵循统一格式：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述信息",
    "details": {}
  }
}
```

## 认证相关错误 (1xxx)

| 错误码 | HTTP状态码 | 说明 | 解决方案 |
|--------|-----------|------|---------|
| INVALID_CREDENTIALS | 401 | 用户名或密码错误 | 检查用户名和密码是否正确 |
| USER_EXISTS | 409 | 用户已存在 | 使用不同的用户名或邮箱 |
| INVALID_TOKEN | 401 | Token无效或已过期 | 重新登录获取新Token |
| TOKEN_EXPIRED | 401 | Token已过期 | 重新登录获取新Token |
| UNAUTHORIZED | 401 | 未授权访问 | 提供有效的认证Token |
| WEAK_PASSWORD | 400 | 密码强度不足 | 使用至少8个字符的强密码 |
| INVALID_EMAIL | 400 | 邮箱格式错误 | 检查邮箱格式 |
| VERIFICATION_FAILED | 400 | 验证码错误 | 检查验证码是否正确 |
| USER_NOT_FOUND | 404 | 用户不存在 | 检查用户ID是否正确 |
| ACCOUNT_DISABLED | 403 | 账户已被禁用 | 联系管理员 |
| PASSWORD_MISMATCH | 400 | 密码不匹配 | 确保新密码和确认密码一致 |

### 示例

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "用户名或密码错误"
  }
}
```

---

## 产品相关错误 (2xxx)

| 错误码 | HTTP状态码 | 说明 | 解决方案 |
|--------|-----------|------|---------|
| PRODUCT_NOT_FOUND | 404 | 产品不存在 | 检查产品ID是否正确 |
| INVALID_CATEGORY | 400 | 无效的分类 | 使用有效的分类ID |
| INVALID_PRICE_RANGE | 400 | 价格区间无效 | 确保最低价格小于最高价格 |
| REVIEW_EXISTS | 409 | 已评价过该产品 | 每个产品只能评价一次 |
| INVALID_RATING | 400 | 评分必须在1-5之间 | 提供1-5之间的评分 |
| INSUFFICIENT_STOCK | 400 | 库存不足 | 减少购买数量或选择其他产品 |
| PRODUCT_OUT_OF_STOCK | 400 | 产品已售罄 | 选择其他产品 |

### 示例

```json
{
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "产品不存在",
    "details": {
      "product_id": "prod_123"
    }
  }
}
```

---

## 对话相关错误 (3xxx)

| 错误码 | HTTP状态码 | 说明 | 解决方案 |
|--------|-----------|------|---------|
| CHAT_NOT_FOUND | 404 | 对话不存在 | 检查对话ID是否正确 |
| MESSAGE_NOT_FOUND | 404 | 消息不存在 | 检查消息ID是否正确 |
| QUOTA_EXCEEDED | 429 | 配额已用完 | 购买更多配额或等待配额重置 |
| FILE_TOO_LARGE | 413 | 文件过大 | 上传小于限制大小的文件 |
| UNSUPPORTED_FILE_TYPE | 400 | 不支持的文件类型 | 使用支持的文件格式 |
| STREAM_ERROR | 500 | 流式传输错误 | 重试请求或联系技术支持 |
| MESSAGE_TOO_LONG | 400 | 消息内容过长 | 缩短消息内容 |
| CHAT_LIMIT_EXCEEDED | 429 | 超过对话数量限制 | 删除旧对话或升级套餐 |

### 示例

```json
{
  "error": {
    "code": "QUOTA_EXCEEDED",
    "message": "对话配额已用完",
    "details": {
      "used": 1000,
      "total": 1000,
      "reset_at": "2024-02-01T00:00:00Z"
    }
  }
}
```

---

## 内容生成相关错误 (4xxx)

| 错误码 | HTTP状态码 | 说明 | 解决方案 |
|--------|-----------|------|---------|
| TEMPLATE_NOT_FOUND | 404 | 模板不存在 | 检查模板ID是否正确 |
| TASK_NOT_FOUND | 404 | 任务不存在 | 检查任务ID是否正确 |
| CONFIG_NOT_FOUND | 404 | 配置不存在 | 检查配置ID是否正确 |
| INVALID_PRODUCT_IDS | 400 | 无效的产品ID | 提供有效的产品ID列表 |
| INVALID_COUNT | 400 | 生成数量必须在1-10之间 | 调整生成数量 |
| INVALID_WORD_COUNT | 400 | 字数必须在50-1000之间 | 调整字数范围 |
| GENERATION_FAILED | 500 | 生成失败 | 重试或联系技术支持 |
| TASK_ALREADY_CANCELLED | 400 | 任务已取消 | 无法操作已取消的任务 |
| EXPORT_FAILED | 500 | 导出失败 | 重试或联系技术支持 |
| INVALID_TEMPLATE_CONFIG | 400 | 模板配置无效 | 检查模板配置参数 |

### 示例

```json
{
  "error": {
    "code": "INVALID_COUNT",
    "message": "生成数量必须在1-10之间",
    "details": {
      "provided": 15,
      "min": 1,
      "max": 10
    }
  }
}
```

---

## 订单相关错误 (5xxx)

| 错误码 | HTTP状态码 | 说明 | 解决方案 |
|--------|-----------|------|---------|
| ORDER_NOT_FOUND | 404 | 订单不存在 | 检查订单ID是否正确 |
| INVALID_ORDER_STATUS | 400 | 订单状态不允许此操作 | 检查订单当前状态 |
| ORDER_ALREADY_CANCELLED | 400 | 订单已取消 | 无法操作已取消的订单 |
| ORDER_ALREADY_COMPLETED | 400 | 订单已完成 | 无法修改已完成的订单 |
| INVALID_QUANTITIES | 400 | 数量无效 | 提供有效的产品数量 |
| EMPTY_ORDER | 400 | 订单为空 | 至少添加一个产品 |

### 示例

```json
{
  "error": {
    "code": "INVALID_ORDER_STATUS",
    "message": "订单状态不允许取消",
    "details": {
      "order_id": "order_123",
      "current_status": "shipped"
    }
  }
}
```

---

## 配额相关错误 (6xxx)

| 错误码 | HTTP状态码 | 说明 | 解决方案 |
|--------|-----------|------|---------|
| QUOTA_EXCEEDED | 429 | 配额已用完 | 购买更多配额 |
| INSUFFICIENT_BALANCE | 400 | 余额不足 | 充值账户余额 |
| INVALID_QUOTA_TYPE | 400 | 无效的配额类型 | 使用有效的配额类型 |
| INVALID_AMOUNT | 400 | 无效的数量 | 提供有效的购买数量 |

### 示例

```json
{
  "error": {
    "code": "QUOTA_EXCEEDED",
    "message": "内容生成配额已用完",
    "details": {
      "type": "content",
      "used": 500,
      "total": 500
    }
  }
}
```

---

## 安全相关错误 (7xxx)

| 错误码 | HTTP状态码 | 说明 | 解决方案 |
|--------|-----------|------|---------|
| INVALID_VERIFICATION_CODE | 400 | 验证码错误 | 检查验证码是否正确 |
| VERIFICATION_CODE_EXPIRED | 400 | 验证码已过期 | 重新发送验证码 |
| PHONE_ALREADY_BOUND | 409 | 手机号已被绑定 | 使用其他手机号 |
| EMAIL_ALREADY_BOUND | 409 | 邮箱已被绑定 | 使用其他邮箱 |
| DEVICE_NOT_FOUND | 404 | 设备不存在 | 检查设备ID是否正确 |
| TOO_MANY_REQUESTS | 429 | 请求过于频繁 | 稍后再试 |
| SUSPICIOUS_ACTIVITY | 403 | 检测到可疑活动 | 联系客服验证身份 |

### 示例

```json
{
  "error": {
    "code": "INVALID_VERIFICATION_CODE",
    "message": "验证码错误",
    "details": {
      "attempts_remaining": 2
    }
  }
}
```

---

## 系统错误 (9xxx)

| 错误码 | HTTP状态码 | 说明 | 解决方案 |
|--------|-----------|------|---------|
| INTERNAL_SERVER_ERROR | 500 | 服务器内部错误 | 联系技术支持 |
| SERVICE_UNAVAILABLE | 503 | 服务暂时不可用 | 稍后重试 |
| DATABASE_ERROR | 500 | 数据库错误 | 联系技术支持 |
| NETWORK_ERROR | 500 | 网络错误 | 检查网络连接 |
| TIMEOUT | 504 | 请求超时 | 重试请求 |
| MAINTENANCE_MODE | 503 | 系统维护中 | 等待维护完成 |

### 示例

```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "服务暂时不可用，请稍后重试",
    "details": {
      "retry_after": 300
    }
  }
}
```

---

## 通用错误

| 错误码 | HTTP状态码 | 说明 | 解决方案 |
|--------|-----------|------|---------|
| BAD_REQUEST | 400 | 请求参数错误 | 检查请求参数 |
| NOT_FOUND | 404 | 资源不存在 | 检查资源ID |
| METHOD_NOT_ALLOWED | 405 | 不支持的HTTP方法 | 使用正确的HTTP方法 |
| VALIDATION_ERROR | 400 | 数据验证失败 | 检查输入数据格式 |
| FORBIDDEN | 403 | 禁止访问 | 检查访问权限 |
| CONFLICT | 409 | 资源冲突 | 解决资源冲突 |

### 示例

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "数据验证失败",
    "details": {
      "fields": {
        "email": "邮箱格式不正确",
        "password": "密码长度至少8个字符"
      }
    }
  }
}
```

---

## 错误处理最佳实践

### 1. 客户端错误处理

```javascript
try {
  const response = await fetch('/api/v1/products', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })

  if (!response.ok) {
    const error = await response.json()

    // 根据错误码处理
    switch (error.error.code) {
      case 'INVALID_TOKEN':
        // 重新登录
        redirectToLogin()
        break
      case 'QUOTA_EXCEEDED':
        // 提示用户购买配额
        showQuotaDialog()
        break
      case 'PRODUCT_NOT_FOUND':
        // 显示404页面
        show404Page()
        break
      default:
        // 显示通用错误消息
        showError(error.error.message)
    }
  }

  const data = await response.json()
  return data
} catch (error) {
  // 处理网络错误
  console.error('Network error:', error)
  showNetworkError()
}
```

### 2. 重试策略

对于临时性错误（如503、504），建议实现指数退避重试：

```javascript
async function fetchWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options)

      if (response.ok) {
        return await response.json()
      }

      const error = await response.json()

      // 对于这些错误码，进行重试
      if (['SERVICE_UNAVAILABLE', 'TIMEOUT', 'NETWORK_ERROR'].includes(error.error.code)) {
        const delay = Math.pow(2, i) * 1000 // 指数退避
        await new Promise(resolve => setTimeout(resolve, delay))
        continue
      }

      // 其他错误直接抛出
      throw error
    } catch (error) {
      if (i === maxRetries - 1) throw error
    }
  }
}
```

### 3. 用户友好的错误消息

```javascript
const ERROR_MESSAGES = {
  'INVALID_CREDENTIALS': '用户名或密码错误，请重试',
  'QUOTA_EXCEEDED': '您的配额已用完，请购买更多配额',
  'PRODUCT_NOT_FOUND': '抱歉，该产品不存在或已下架',
  'FILE_TOO_LARGE': '文件太大，请上传小于10MB的文件',
  'NETWORK_ERROR': '网络连接失败，请检查您的网络'
}

function getUserFriendlyMessage(errorCode) {
  return ERROR_MESSAGES[errorCode] || '操作失败，请稍后重试'
}
```

---

## 速率限制

当超过API速率限制时，会返回429错误：

```json
{
  "error": {
    "code": "TOO_MANY_REQUESTS",
    "message": "请求过于频繁",
    "details": {
      "limit": 100,
      "remaining": 0,
      "reset_at": "2024-01-01T01:00:00Z"
    }
  }
}
```

响应头中也会包含速率限制信息：

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704067200
```

---

## 联系支持

如果遇到无法解决的错误，请联系技术支持：

- 邮箱: support@example.com
- 电话: 400-xxx-xxxx
- 在线客服: https://example.com/support

提供以下信息以便快速解决问题：
- 错误码
- 请求ID (从响应头 `X-Request-ID` 获取)
- 发生时间
- 请求详情
