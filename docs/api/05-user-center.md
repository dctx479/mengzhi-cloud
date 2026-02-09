# 用户中心API

## 订单管理

### 获取订单列表

**GET** `/api/user/orders`

需要认证。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | number | 否 | 1 | 页码 |
| page_size | number | 否 | 20 | 每页数量 |
| status | string | 否 | - | 订单状态: pending, completed, cancelled, shipped |
| start_date | string | 否 | - | 开始日期 (YYYY-MM-DD) |
| end_date | string | 否 | - | 结束日期 (YYYY-MM-DD) |
| keyword | string | 否 | - | 搜索关键词 |

#### 响应示例

```json
{
  "items": [
    {
      "id": "order_123",
      "order_no": "ORD20240101001",
      "user_id": "user_123",
      "items": [
        {
          "id": "item_001",
          "product_id": "prod_123",
          "product": {
            "id": "prod_123",
            "name": "有机苹果",
            "image": "https://example.com/apple.jpg",
            "price": 29.9
          },
          "quantity": 2,
          "price": 29.9,
          "subtotal": 59.8
        }
      ],
      "status": "completed",
      "total_amount": 59.8,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:10:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

#### cURL示例

```bash
# 获取所有订单
curl -X GET "http://localhost:3000/api/user/orders?page=1&page_size=20" \
  -H "Authorization: Bearer <your_token>"

# 按状态筛选
curl -X GET "http://localhost:3000/api/user/orders?status=completed" \
  -H "Authorization: Bearer <your_token>"

# 按日期范围筛选
curl -X GET "http://localhost:3000/api/user/orders?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer <your_token>"
```

---

### 获取订单详情

**GET** `/api/user/orders/:orderId`

需要认证。

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| orderId | string | 是 | 订单ID |

#### 响应示例

```json
{
  "id": "order_123",
  "order_no": "ORD20240101001",
  "user_id": "user_123",
  "items": [
    {
      "id": "item_001",
      "product_id": "prod_123",
      "product": {
        "id": "prod_123",
        "name": "有机苹果",
        "image": "https://example.com/apple.jpg",
        "price": 29.9
      },
      "quantity": 2,
      "price": 29.9,
      "subtotal": 59.8
    }
  ],
  "status": "completed",
  "total_amount": 59.8,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:10:00Z"
}
```

#### cURL示例

```bash
curl -X GET http://localhost:3000/api/user/orders/order_123 \
  -H "Authorization: Bearer <your_token>"
```

---

### 创建订单

**POST** `/api/user/orders`

需要认证。

#### 请求参数

```json
{
  "product_ids": ["prod_123", "prod_124"],
  "quantities": [2, 1]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| product_ids | string[] | 是 | 产品ID列表 |
| quantities | number[] | 是 | 对应的数量列表 |

#### 响应示例

```json
{
  "id": "order_123",
  "order_no": "ORD20240101001",
  "user_id": "user_123",
  "items": [
    {
      "id": "item_001",
      "product_id": "prod_123",
      "product": {
        "id": "prod_123",
        "name": "有机苹果",
        "image": "https://example.com/apple.jpg",
        "price": 29.9
      },
      "quantity": 2,
      "price": 29.9,
      "subtotal": 59.8
    }
  ],
  "status": "pending",
  "total_amount": 59.8,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### cURL示例

```bash
curl -X POST http://localhost:3000/api/user/orders \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "product_ids": ["prod_123", "prod_124"],
    "quantities": [2, 1]
  }'
```

---

### 取消订单

**POST** `/api/user/orders/:orderId/cancel`

需要认证。

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| orderId | string | 是 | 订单ID |

#### 响应示例

```json
{
  "message": "订单已取消"
}
```

#### cURL示例

```bash
curl -X POST http://localhost:3000/api/user/orders/order_123/cancel \
  -H "Authorization: Bearer <your_token>"
```

---

## 配额管理

### 获取配额信息

**GET** `/api/user/quota`

需要认证。

#### 响应示例

```json
{
  "chat_used": 150,
  "chat_total": 1000,
  "content_used": 50,
  "content_total": 500,
  "storage_used": 1024000,
  "storage_total": 10240000
}
```

#### cURL示例

```bash
curl -X GET http://localhost:3000/api/user/quota \
  -H "Authorization: Bearer <your_token>"
```

---

### 获取配额历史记录

**GET** `/api/user/quota/history`

需要认证。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | number | 否 | 1 | 页码 |
| page_size | number | 否 | 20 | 每页数量 |
| type | string | 否 | - | 类型: chat, content, storage |

#### 响应示例

```json
{
  "items": [
    {
      "id": "quota_001",
      "type": "chat",
      "amount": -10,
      "created_at": "2024-01-01T00:00:00Z",
      "description": "AI对话消耗"
    },
    {
      "id": "quota_002",
      "type": "content",
      "amount": -5,
      "created_at": "2024-01-01T00:05:00Z",
      "description": "内容生成消耗"
    },
    {
      "id": "quota_003",
      "type": "chat",
      "amount": 100,
      "created_at": "2024-01-01T00:10:00Z",
      "description": "购买配额"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

#### cURL示例

```bash
# 获取所有历史
curl -X GET "http://localhost:3000/api/user/quota/history?page=1&page_size=20" \
  -H "Authorization: Bearer <your_token>"

# 按类型筛选
curl -X GET "http://localhost:3000/api/user/quota/history?type=chat" \
  -H "Authorization: Bearer <your_token>"
```

---

### 购买配额

**POST** `/api/user/quota/purchase`

需要认证。

#### 请求参数

```json
{
  "type": "chat",
  "amount": 1000,
  "price": 99.0
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 配额类型: chat, content, storage |
| amount | number | 是 | 购买数量 |
| price | number | 是 | 价格 |

#### 响应示例

```json
{
  "message": "购买成功",
  "quota": {
    "chat_used": 150,
    "chat_total": 2000,
    "content_used": 50,
    "content_total": 500,
    "storage_used": 1024000,
    "storage_total": 10240000
  }
}
```

#### cURL示例

```bash
curl -X POST http://localhost:3000/api/user/quota/purchase \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "chat",
    "amount": 1000,
    "price": 99.0
  }'
```

---

## 用户设置

### 获取用户设置

**GET** `/api/user/settings`

需要认证。

#### 响应示例

```json
{
  "email_notifications": true,
  "sms_notifications": false,
  "profile_public": true,
  "language": "zh-CN",
  "theme": "light"
}
```

#### cURL示例

```bash
curl -X GET http://localhost:3000/api/user/settings \
  -H "Authorization: Bearer <your_token>"
```

---

### 更新用户设置

**PUT** `/api/user/settings`

需要认证。

#### 请求参数

```json
{
  "email_notifications": true,
  "sms_notifications": false,
  "profile_public": true,
  "language": "zh-CN",
  "theme": "dark"
}
```

所有字段均为可选。

| 字段 | 类型 | 说明 |
|------|------|------|
| email_notifications | boolean | 邮件通知 |
| sms_notifications | boolean | 短信通知 |
| profile_public | boolean | 公开个人资料 |
| language | string | 语言: zh-CN, en-US |
| theme | string | 主题: light, dark, auto |

#### 响应示例

```json
{
  "email_notifications": true,
  "sms_notifications": false,
  "profile_public": true,
  "language": "zh-CN",
  "theme": "dark"
}
```

#### cURL示例

```bash
curl -X PUT http://localhost:3000/api/user/settings \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "dark",
    "email_notifications": true
  }'
```

---

## 安全管理

### 修改密码

**POST** `/api/user/security/change-password`

需要认证。

#### 请求参数

```json
{
  "old_password": "string",
  "new_password": "string",
  "confirm_password": "string"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| old_password | string | 是 | 旧密码 |
| new_password | string | 是 | 新密码 (至少8字符) |
| confirm_password | string | 是 | 确认新密码 |

#### 响应示例

```json
{
  "message": "密码修改成功"
}
```

#### cURL示例

```bash
curl -X POST http://localhost:3000/api/user/security/change-password \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "oldpass123",
    "new_password": "newpass123",
    "confirm_password": "newpass123"
  }'
```

---

### 获取登录日志

**GET** `/api/user/security/logs`

需要认证。

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | number | 否 | 1 | 页码 |
| page_size | number | 否 | 20 | 每页数量 |

#### 响应示例

```json
{
  "items": [
    {
      "id": "log_001",
      "event_type": "login",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2024-01-01T00:00:00Z",
      "success": true
    },
    {
      "id": "log_002",
      "event_type": "login_failed",
      "ip_address": "192.168.1.2",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2024-01-01T00:05:00Z",
      "success": false
    }
  ],
  "total": 50
}
```

#### cURL示例

```bash
curl -X GET "http://localhost:3000/api/user/security/logs?page=1&page_size=20" \
  -H "Authorization: Bearer <your_token>"
```

---

### 绑定手机号

**POST** `/api/user/security/bind-phone`

需要认证。

#### 请求参数

```json
{
  "phone": "13800138000",
  "verification_code": "123456"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | string | 是 | 手机号 |
| verification_code | string | 是 | 验证码 |

#### 响应示例

```json
{
  "message": "手机号绑定成功"
}
```

#### cURL示例

```bash
curl -X POST http://localhost:3000/api/user/security/bind-phone \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138000",
    "verification_code": "123456"
  }'
```

---

### 绑定邮箱

**POST** `/api/user/security/bind-email`

需要认证。

#### 请求参数

```json
{
  "email": "user@example.com",
  "verification_code": "123456"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 邮箱地址 |
| verification_code | string | 是 | 验证码 |

#### 响应示例

```json
{
  "message": "邮箱绑定成功"
}
```

#### cURL示例

```bash
curl -X POST http://localhost:3000/api/user/security/bind-email \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "verification_code": "123456"
  }'
```

---

### 发送验证码

**POST** `/api/user/security/send-verification-code`

需要认证。

#### 请求参数

```json
{
  "type": "email",
  "target": "user@example.com"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 类型: email 或 phone |
| target | string | 是 | 目标邮箱或手机号 |

#### 响应示例

```json
{
  "message": "验证码已发送"
}
```

#### cURL示例

```bash
curl -X POST http://localhost:3000/api/user/security/send-verification-code \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "email",
    "target": "user@example.com"
  }'
```

---

### 获取设备列表

**GET** `/api/user/security/devices`

需要认证。

#### 响应示例

```json
[
  {
    "id": "device_001",
    "device_name": "Chrome on Windows",
    "device_type": "desktop",
    "ip_address": "192.168.1.1",
    "last_login": "2024-01-01T00:00:00Z",
    "is_current": true
  },
  {
    "id": "device_002",
    "device_name": "Safari on iPhone",
    "device_type": "mobile",
    "ip_address": "192.168.1.2",
    "last_login": "2024-01-01T00:05:00Z",
    "is_current": false
  }
]
```

#### cURL示例

```bash
curl -X GET http://localhost:3000/api/user/security/devices \
  -H "Authorization: Bearer <your_token>"
```

---

### 删除设备

**DELETE** `/api/user/security/devices/:deviceId`

需要认证。

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| deviceId | string | 是 | 设备ID |

#### 响应示例

```json
{
  "message": "设备已删除"
}
```

#### cURL示例

```bash
curl -X DELETE http://localhost:3000/api/user/security/devices/device_002 \
  -H "Authorization: Bearer <your_token>"
```

---

## 错误处理

### 常见错误

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| ORDER_NOT_FOUND | 404 | 订单不存在 |
| INSUFFICIENT_STOCK | 400 | 库存不足 |
| INVALID_ORDER_STATUS | 400 | 订单状态不允许此操作 |
| QUOTA_EXCEEDED | 429 | 配额已用完 |
| INSUFFICIENT_BALANCE | 400 | 余额不足 |
| INVALID_VERIFICATION_CODE | 400 | 验证码错误 |
| PHONE_ALREADY_BOUND | 409 | 手机号已被绑定 |
| EMAIL_ALREADY_BOUND | 409 | 邮箱已被绑定 |
| DEVICE_NOT_FOUND | 404 | 设备不存在 |
| PASSWORD_MISMATCH | 400 | 密码不匹配 |
