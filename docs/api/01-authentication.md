# 认证API

## 用户登录

**POST** `/v1/auth/login`

### 请求参数

```json
{
  "username": "string",
  "password": "string"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名或邮箱 |
| password | string | 是 | 密码 |

### 响应示例

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "user_123",
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "avatar": "https://example.com/avatar.jpg",
    "nickname": "张三",
    "status": "active",
    "role": "user",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z"
  },
  "expiresIn": 86400
}
```

### cURL示例

```bash
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "zhangsan",
    "password": "password123"
  }'
```

---

## 用户注册

**POST** `/v1/auth/register`

### 请求参数

```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "user_type": "string",
  "verification_code": "string"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 (3-20字符) |
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码 (至少8字符) |
| user_type | string | 是 | 用户类型 |
| verification_code | string | 是 | 邮箱验证码 |

### 响应示例

```json
{
  "user": {
    "id": "user_123",
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "status": "active",
    "role": "user",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z"
  },
  "message": "注册成功"
}
```

### cURL示例

```bash
curl -X POST http://localhost:3000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "password": "password123",
    "user_type": "individual",
    "verification_code": "123456"
  }'
```

---

## 获取当前用户信息

**GET** `/v1/auth/me`

需要认证。

### 响应示例

```json
{
  "id": "user_123",
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "avatar": "https://example.com/avatar.jpg",
  "phone": "13800138000",
  "nickname": "张三",
  "status": "active",
  "role": "user",
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:00:00Z"
}
```

### cURL示例

```bash
curl -X GET http://localhost:3000/api/v1/auth/me \
  -H "Authorization: Bearer <your_token>"
```

---

## 更新个人资料

**PUT** `/v1/auth/profile`

需要认证。

### 请求参数

```json
{
  "username": "string",
  "nickname": "string",
  "avatar": "string",
  "phone": "string",
  "bio": "string",
  "location": "string",
  "website": "string"
}
```

所有字段均为可选。

### 响应示例

```json
{
  "id": "user_123",
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "avatar": "https://example.com/new-avatar.jpg",
  "nickname": "张三",
  "bio": "热爱生活",
  "location": "北京",
  "website": "https://example.com",
  "status": "active",
  "role": "user",
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-02T00:00:00Z"
}
```

### cURL示例

```bash
curl -X PUT http://localhost:3000/api/v1/auth/profile \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "nickname": "张三",
    "bio": "热爱生活"
  }'
```

---

## 修改密码

**POST** `/v1/auth/change-password`

需要认证。

### 请求参数

```json
{
  "oldPassword": "string",
  "newPassword": "string"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| oldPassword | string | 是 | 旧密码 |
| newPassword | string | 是 | 新密码 (至少8字符) |

### 响应示例

```json
{
  "message": "密码修改成功"
}
```

### cURL示例

```bash
curl -X POST http://localhost:3000/api/v1/auth/change-password \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "oldPassword": "oldpass123",
    "newPassword": "newpass123"
  }'
```

---

## 检查用户名/邮箱可用性

**GET** `/v1/auth/check-availability`

### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| field | string | 是 | 检查字段: username 或 email |
| value | string | 是 | 要检查的值 |

### 响应示例

```json
{
  "available": true
}
```

### cURL示例

```bash
curl -X GET "http://localhost:3000/api/v1/auth/check-availability?field=username&value=zhangsan"
```

---

## 错误处理

### 常见错误

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| INVALID_CREDENTIALS | 401 | 用户名或密码错误 |
| USER_EXISTS | 409 | 用户已存在 |
| INVALID_TOKEN | 401 | Token无效或已过期 |
| WEAK_PASSWORD | 400 | 密码强度不足 |
| INVALID_EMAIL | 400 | 邮箱格式错误 |
| VERIFICATION_FAILED | 400 | 验证码错误 |

### 错误响应示例

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "用户名或密码错误"
  }
}
```
