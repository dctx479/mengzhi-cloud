# 认证API文档

**用户认证和授权相关API**

Base URL: `http://localhost:8000/api/v1/auth`

---

## 目录

- [1. 用户注册](#1-用户注册)
- [2. 用户登录](#2-用户登录)
- [3. 刷新Token](#3-刷新token)
- [4. 用户登出](#4-用户登出)
- [5. 获取当前用户信息](#5-获取当前用户信息)
- [6. 更新用户信息](#6-更新用户信息)
- [7. 修改密码](#7-修改密码)
- [8. 重置密码](#8-重置密码)

---

## 1. 用户注册

注册新用户账号，支持个人和企业用户类型。

### 端点信息

```
POST /api/v1/auth/register
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名，3-50字符，只能包含字母、数字、下划线、连字符 |
| email | string | 否* | 邮箱地址（与phone至少填一个）|
| phone | string | 否* | 手机号码（与email至少填一个）|
| password | string | 是 | 密码，8-32字符，必须包含字母和数字 |
| user_type | string | 是 | 用户类型：`personal`（个人）/ `enterprise`（企业）|
| verification_code | string | 是 | 验证码（邮箱或手机）|
| enterprise_name | string | 否** | 企业名称（企业用户必填）|
| enterprise_license | string | 否** | 营业执照号（企业用户必填）|

### 请求示例

#### curl

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "phone": "13800138000",
    "password": "Password123",
    "user_type": "enterprise",
    "verification_code": "123456",
    "enterprise_name": "内蒙古草原牧业有限公司",
    "enterprise_license": "91150100MA0N1234X5"
  }'
```

#### JavaScript

```javascript
const response = await fetch('http://localhost:8000/api/v1/auth/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'zhangsan',
    email: 'zhangsan@example.com',
    password: 'Password123',
    user_type: 'personal',
    verification_code: '123456'
  })
});

const data = await response.json();
console.log(data);
```

#### Python

```python
import requests

url = 'http://localhost:8000/api/v1/auth/register'
payload = {
    'username': 'zhangsan',
    'email': 'zhangsan@example.com',
    'password': 'Password123',
    'user_type': 'personal',
    'verification_code': '123456'
}

response = requests.post(url, json=payload)
print(response.json())
```

### 响应示例

#### 成功响应（201 Created）

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "phone": "13800138000",
    "user_type": "enterprise",
    "created_at": "[项目完成日期]T10:00:00"
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

#### 失败响应（400 Bad Request）

```json
{
  "code": 10001,
  "message": "参数验证失败",
  "data": null,
  "errors": [
    {
      "field": "username",
      "message": "该用户名已被注册"
    }
  ],
  "timestamp": "[项目完成日期]T10:00:00",
  "request_id": "uuid-v4"
}
```

### 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 10001 | 400 | 参数验证失败（用户名已存在/邮箱已存在/手机号已存在）|
| 10002 | 400 | 缺少必要参数 |
| 20015 | 400 | 验证码无效 |
| 20016 | 400 | 验证码已过期 |
| 50000 | 500 | 系统错误 |

### 注意事项

- email和phone至少填写一个
- 企业用户必须填写enterprise_name和enterprise_license
- 密码必须同时包含字母和数字
- 验证码通过发送短信或邮件获取（需先调用验证码发送接口）

---

## 2. 用户登录

使用用户名/邮箱/手机号和密码登录。

### 端点信息

```
POST /api/v1/auth/login
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名或邮箱或手机号 |
| password | string | 是 | 密码 |
| device_id | string | 否 | 设备ID（用于多设备登录控制）|

### 请求示例

#### curl

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "zhangsan",
    "password": "Password123"
  }'
```

#### JavaScript

```javascript
const response = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'zhangsan',
    password: 'Password123'
  })
});

const data = await response.json();
// 存储Token
localStorage.setItem('access_token', data.data.tokens.access_token);
localStorage.setItem('refresh_token', data.data.tokens.refresh_token);
```

#### Python

```python
import requests

url = 'http://localhost:8000/api/v1/auth/login'
payload = {
    'username': 'zhangsan',
    'password': 'Password123'
}

response = requests.post(url, json=payload)
data = response.json()

# 存储Token
access_token = data['data']['tokens']['access_token']
refresh_token = data['data']['tokens']['refresh_token']
```

### 响应示例

#### 成功响应（200 OK）

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "user": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "zhangsan",
      "email": "zh***@example.com",
      "phone": "138****8000",
      "user_type": "enterprise",
      "status": "active",
      "role": "user",
      "created_at": "[项目完成日期]T10:00:00",
      "last_login_at": "[项目完成日期]T09:00:00"
    },
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "Bearer",
      "expires_in": 1800
    }
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

#### 失败响应（401 Unauthorized）

```json
{
  "code": 20011,
  "message": "密码错误",
  "data": null,
  "timestamp": "[项目完成日期]T10:00:00",
  "request_id": "uuid-v4"
}
```

### 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 20010 | 404 | 用户不存在 |
| 20011 | 401 | 密码错误 |
| 20012 | 403 | 账号已禁用 |
| 20013 | 403 | 账号已锁定（密码错误5次后锁定30分钟）|
| 20014 | 429 | 登录过于频繁 |
| 50000 | 500 | 系统错误 |

### 注意事项

- username字段支持用户名、邮箱、手机号三种方式
- 密码错误5次后账号锁定30分钟
- access_token有效期30分钟，refresh_token有效期7天
- 敏感信息（邮箱、手机号）会脱敏显示

---

## 3. 刷新Token

使用Refresh Token刷新过期的Access Token。

### 端点信息

```
POST /api/v1/auth/refresh
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| refresh_token | string | 是 | 刷新令牌 |

### 请求示例

#### curl

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

#### JavaScript

```javascript
const refreshToken = localStorage.getItem('refresh_token');

const response = await fetch('http://localhost:8000/api/v1/auth/refresh', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    refresh_token: refreshToken
  })
});

const data = await response.json();
// 更新Token
localStorage.setItem('access_token', data.data.access_token);
localStorage.setItem('refresh_token', data.data.refresh_token);
```

#### Python

```python
import requests

url = 'http://localhost:8000/api/v1/auth/refresh'
payload = {
    'refresh_token': refresh_token
}

response = requests.post(url, json=payload)
data = response.json()

# 更新Token
access_token = data['data']['access_token']
refresh_token = data['data']['refresh_token']
```

### 响应示例

#### 成功响应（200 OK）

```json
{
  "code": 200,
  "message": "Token刷新成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 1800
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

#### 失败响应（401 Unauthorized）

```json
{
  "code": 20005,
  "message": "无效的刷新令牌",
  "data": null,
  "timestamp": "[项目完成日期]T10:00:00",
  "request_id": "uuid-v4"
}
```

### 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 20005 | 401 | Refresh Token无效 |
| 20006 | 401 | Refresh Token已过期 |
| 50000 | 500 | 系统错误 |

### 注意事项

- 刷新Token会同时返回新的access_token和refresh_token
- 旧的Token立即失效
- 建议在access_token过期前主动刷新

---

## 4. 用户登出

用户登出，Token加入黑名单。

### 端点信息

```
POST /api/v1/auth/logout
```

### 请求Header

```
Authorization: Bearer {access_token}
```

### 请求示例

#### curl

```bash
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### JavaScript

```javascript
const accessToken = localStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/api/v1/auth/logout', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const data = await response.json();
// 清除本地Token
localStorage.removeItem('access_token');
localStorage.removeItem('refresh_token');
```

#### Python

```python
import requests

url = 'http://localhost:8000/api/v1/auth/logout'
headers = {
    'Authorization': f'Bearer {access_token}'
}

response = requests.post(url, headers=headers)
print(response.json())
```

### 响应示例

#### 成功响应（200 OK）

```json
{
  "code": 200,
  "message": "登出成功",
  "data": {
    "message": "已成功登出"
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

### 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 20001 | 401 | Token缺失 |
| 20002 | 401 | Token无效 |
| 20003 | 401 | Token已过期 |

### 注意事项

- 登出后Token会加入黑名单，无法继续使用
- 即使请求失败，客户端也应清除本地Token
- 黑名单存储在Redis中，有效期30分钟

---

## 5. 获取当前用户信息

获取当前登录用户的详细信息。

### 端点信息

```
GET /api/v1/auth/me
```

### 请求Header

```
Authorization: Bearer {access_token}
```

### 请求示例

#### curl

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### JavaScript

```javascript
const accessToken = localStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/api/v1/auth/me', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const data = await response.json();
console.log(data.data);
```

#### Python

```python
import requests

url = 'http://localhost:8000/api/v1/auth/me'
headers = {
    'Authorization': f'Bearer {access_token}'
}

response = requests.get(url, headers=headers)
print(response.json())
```

### 响应示例

#### 成功响应（200 OK）

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "zhangsan",
    "email": "zh***@example.com",
    "phone": "138****8000",
    "nickname": "张三",
    "avatar_url": "https://example.com/avatar.jpg",
    "gender": 1,
    "user_type": "enterprise",
    "status": "active",
    "role": "user",
    "created_at": "[项目完成日期]T10:00:00",
    "last_login_at": "[项目完成日期]T09:00:00"
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

### 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 20001 | 401 | Token缺失 |
| 20002 | 401 | Token无效 |
| 20003 | 401 | Token已过期 |
| 20010 | 404 | 用户不存在 |

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户UUID |
| username | string | 用户名 |
| email | string | 邮箱（已脱敏）|
| phone | string | 手机号（已脱敏）|
| nickname | string | 昵称 |
| avatar_url | string | 头像URL |
| gender | integer | 性别：0未知/1男/2女 |
| user_type | string | 用户类型：personal/enterprise |
| status | string | 账号状态：active/disabled/locked |
| role | string | 用户角色：user/admin |

---

## 6. 更新用户信息

更新当前用户的个人信息（昵称、头像、性别）。

### 端点信息

```
PUT /api/v1/auth/me
```

### 请求Header

```
Authorization: Bearer {access_token}
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| nickname | string | 否 | 昵称，最长100字符 |
| avatar_url | string | 否 | 头像URL，最长500字符 |
| gender | integer | 否 | 性别：0未知/1男/2女 |

### 请求示例

#### curl

```bash
curl -X PUT "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "nickname": "张三",
    "avatar_url": "https://example.com/avatar.jpg",
    "gender": 1
  }'
```

#### JavaScript

```javascript
const accessToken = localStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/api/v1/auth/me', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    nickname: '张三',
    avatar_url: 'https://example.com/avatar.jpg',
    gender: 1
  })
});

const data = await response.json();
console.log(data);
```

#### Python

```python
import requests

url = 'http://localhost:8000/api/v1/auth/me'
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}
payload = {
    'nickname': '张三',
    'avatar_url': 'https://example.com/avatar.jpg',
    'gender': 1
}

response = requests.put(url, headers=headers, json=payload)
print(response.json())
```

### 响应示例

#### 成功响应（200 OK）

```json
{
  "code": 200,
  "message": "个人信息更新成功",
  "data": {
    "updated": true
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

### 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 20001 | 401 | Token缺失 |
| 20002 | 401 | Token无效 |
| 20003 | 401 | Token已过期 |
| 10001 | 400 | 参数验证失败 |
| 50000 | 500 | 系统错误 |

### 注意事项

- 所有字段都是可选的，只更新提供的字段
- 用户名、邮箱、手机号不支持通过此接口修改

---

## 7. 修改密码

用户修改自己的密码，需要提供旧密码验证。

### 端点信息

```
POST /api/v1/auth/change-password
```

### 请求Header

```
Authorization: Bearer {access_token}
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| old_password | string | 是 | 原密码 |
| new_password | string | 是 | 新密码，8-32字符，必须包含字母和数字 |

### 请求示例

#### curl

```bash
curl -X POST "http://localhost:8000/api/v1/auth/change-password" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "OldPassword123",
    "new_password": "NewPassword123"
  }'
```

#### JavaScript

```javascript
const accessToken = localStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/api/v1/auth/change-password', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    old_password: 'OldPassword123',
    new_password: 'NewPassword123'
  })
});

const data = await response.json();
console.log(data);
```

#### Python

```python
import requests

url = 'http://localhost:8000/api/v1/auth/change-password'
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}
payload = {
    'old_password': 'OldPassword123',
    'new_password': 'NewPassword123'
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

### 响应示例

#### 成功响应（200 OK）

```json
{
  "code": 200,
  "message": "密码修改成功",
  "data": {
    "message": "密码修改成功",
    "changed_at": "[项目完成日期]T10:00:00"
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

#### 失败响应（401 Unauthorized）

```json
{
  "code": 20011,
  "message": "密码错误",
  "data": null,
  "timestamp": "[项目完成日期]T10:00:00",
  "request_id": "uuid-v4"
}
```

### 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 20001 | 401 | Token缺失 |
| 20002 | 401 | Token无效 |
| 20003 | 401 | Token已过期 |
| 20011 | 401 | 旧密码错误 |
| 10001 | 400 | 新密码不能与旧密码相同 |
| 50000 | 500 | 系统错误 |

### 注意事项

- 修改密码需要验证旧密码
- 新密码必须同时包含字母和数字
- 新密码不能与旧密码相同
- 修改成功后建议重新登录

---

## 8. 重置密码

通过验证码重置忘记的密码。

### 端点信息

```
POST /api/v1/auth/reset-password
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| identifier | string | 是 | 邮箱或手机号 |
| verification_code | string | 是 | 验证码 |
| new_password | string | 是 | 新密码，8-32字符，必须包含字母和数字 |

### 请求示例

#### curl

```bash
curl -X POST "http://localhost:8000/api/v1/auth/reset-password" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "zhangsan@example.com",
    "verification_code": "123456",
    "new_password": "NewPassword123"
  }'
```

#### JavaScript

```javascript
const response = await fetch('http://localhost:8000/api/v1/auth/reset-password', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    identifier: 'zhangsan@example.com',
    verification_code: '123456',
    new_password: 'NewPassword123'
  })
});

const data = await response.json();
console.log(data);
```

#### Python

```python
import requests

url = 'http://localhost:8000/api/v1/auth/reset-password'
payload = {
    'identifier': 'zhangsan@example.com',
    'verification_code': '123456',
    'new_password': 'NewPassword123'
}

response = requests.post(url, json=payload)
print(response.json())
```

### 响应示例

#### 成功响应（200 OK）

```json
{
  "code": 200,
  "message": "密码重置成功",
  "data": {
    "message": "密码重置成功",
    "reset_at": "[项目完成日期]T10:00:00"
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

#### 失败响应（400 Bad Request）

```json
{
  "code": 10001,
  "message": "验证码无效或已过期",
  "data": null,
  "errors": [
    {
      "field": "verification_code",
      "message": "验证码无效或已过期"
    }
  ],
  "timestamp": "[项目完成日期]T10:00:00",
  "request_id": "uuid-v4"
}
```

### 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 10001 | 400 | 验证码无效或已过期 |
| 20010 | 404 | 用户不存在 |
| 50000 | 500 | 系统错误 |

### 注意事项

- 验证码通过邮箱或手机短信获取（需先调用验证码发送接口）
- 新密码必须同时包含字母和数字
- 重置成功后需要使用新密码重新登录

---

## 常见问题

### Q: Token过期了怎么办？

A: 使用refresh_token调用刷新Token接口获取新的access_token。

```javascript
// 自动刷新示例
async function fetchWithAuth(url, options = {}) {
  let accessToken = localStorage.getItem('access_token');

  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${accessToken}`
    }
  });

  const data = await response.json();

  // Token过期，自动刷新
  if (data.code === 20003) {
    const refreshToken = localStorage.getItem('refresh_token');
    const refreshResponse = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    });

    const refreshData = await refreshResponse.json();
    localStorage.setItem('access_token', refreshData.data.access_token);
    localStorage.setItem('refresh_token', refreshData.data.refresh_token);

    // 重新请求
    return fetchWithAuth(url, options);
  }

  return data;
}
```

### Q: 如何处理密码错误5次锁定？

A: 账号锁定30分钟后自动解锁，或联系管理员手动解锁。

### Q: 验证码在哪里获取？

A: 需要先调用验证码发送接口（暂未实现），验证码会发送到邮箱或手机。

### Q: 如何实现"记住我"功能？

A: 将refresh_token安全存储（建议HttpOnly Cookie），自动刷新access_token。

---

**文档版本**: v1.0
**最后更新**: [项目完成日期]
