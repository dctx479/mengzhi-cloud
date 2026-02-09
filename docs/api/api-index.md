# API总览和索引

**内蒙古农畜产品品牌营销AI赋能云平台 - API文档**

版本: v1.0
更新日期: [项目完成日期]
Base URL: `http://localhost:8000/api/v1`

---

## 目录

- [快速开始](#快速开始)
- [认证说明](#认证说明)
- [统一响应格式](#统一响应格式)
- [错误码体系](#错误码体系)
- [API端点索引](#api端点索引)
- [变更日志](#变更日志)

---

## 快速开始

### 环境要求

- Python 3.9+
- MySQL 8.0+
- Redis 5.0+
- FastAPI 0.104+

### 启动服务

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 在线文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 快速示例

```bash
# 1. 用户注册
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "password": "Password123",
    "user_type": "personal",
    "verification_code": "123456"
  }'

# 2. 用户登录
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "zhangsan",
    "password": "Password123"
  }'

# 3. 获取产品列表（使用返回的access_token）
curl -X GET "http://localhost:8000/api/v1/products?page=1&size=10" \
  -H "Authorization: Bearer {access_token}"

# 4. 发送AI对话消息
curl -X POST "http://localhost:8000/api/v1/chat/message" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "请介绍一下内蒙古的特色农产品"
  }'
```

---

## 认证说明

### JWT Token机制

本平台采用JWT（JSON Web Token）双Token机制：

#### Access Token（访问令牌）
- 有效期：30分钟
- 用途：访问受保护的API端点
- 放置位置：HTTP Header `Authorization: Bearer {access_token}`

#### Refresh Token（刷新令牌）
- 有效期：7天
- 用途：刷新过期的Access Token
- 存储建议：安全存储（LocalStorage/Cookie）

### 认证流程

```
1. 用户登录 → 获取 access_token + refresh_token
2. 使用 access_token 访问API
3. access_token 过期 → 使用 refresh_token 刷新
4. 获取新的 access_token + refresh_token
5. 继续访问API
```

### Header格式

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

### Token黑名单

用户登出后，Token会被加入黑名单（Redis存储），无法继续使用。

---

## 统一响应格式

### 成功响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    // 响应数据
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

### 错误响应

```json
{
  "code": 10001,
  "message": "参数验证失败",
  "data": null,
  "errors": [
    {
      "field": "email",
      "message": "邮箱格式不正确"
    }
  ],
  "timestamp": "[项目完成日期]T10:00:00",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 分页响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "size": 10,
      "total": 100,
      "pages": 10,
      "has_next": true,
      "has_prev": false
    }
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

---

## 错误码体系

### 错误码分类

| 范围 | 分类 | 说明 |
|------|------|------|
| 10xxx | 参数错误 | 请求参数验证失败 |
| 20xxx | 认证授权错误 | 身份验证或权限问题 |
| 40xxx | 数据库错误 | 数据库操作失败 |
| 50xxx | 系统错误 | 服务器内部错误 |

### 常见错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 200 | 200 | 成功 |
| 10000 | 400 | 参数错误 |
| 10001 | 400 | 参数验证失败 |
| 10002 | 400 | 缺少必要参数 |
| 20000 | 401 | 认证错误 |
| 20001 | 401 | Token缺失 |
| 20002 | 401 | Token无效 |
| 20003 | 401 | Token过期 |
| 20010 | 404 | 用户不存在 |
| 20011 | 401 | 密码错误 |
| 20012 | 403 | 账号已禁用 |
| 20013 | 403 | 账号已锁定 |
| 20020 | 403 | 权限不足 |
| 40010 | 404 | 记录不存在 |
| 40011 | 409 | 记录已存在 |
| 50000 | 500 | 系统错误 |
| 50002 | 503 | 服务不可用 |

详细错误码文档：[errors.md](./errors.md)

---

## API端点索引

### 认证API（8个端点）

详细文档：[authentication-api.md](./authentication-api.md)

| 方法 | 端点 | 功能描述 | 认证 |
|------|------|---------|------|
| POST | `/auth/register` | 用户注册 | 否 |
| POST | `/auth/login` | 用户登录 | 否 |
| POST | `/auth/refresh` | 刷新Token | 否 |
| POST | `/auth/logout` | 用户登出 | 是 |
| GET | `/auth/me` | 获取当前用户信息 | 是 |
| PUT | `/auth/me` | 更新用户信息 | 是 |
| POST | `/auth/change-password` | 修改密码 | 是 |
| POST | `/auth/reset-password` | 重置密码 | 否 |

### 产品API（9个端点）

详细文档：[products-api.md](./products-api.md)

| 方法 | 端点 | 功能描述 | 认证 |
|------|------|---------|------|
| GET | `/products` | 获取产品列表 | 否 |
| GET | `/products/{id}` | 获取产品详情 | 否 |
| POST | `/products` | 创建产品 | 是（管理员）|
| PUT | `/products/{id}` | 更新产品 | 是（管理员）|
| DELETE | `/products/{id}` | 删除产品 | 是（管理员）|
| GET | `/products/{id}/cultural-info` | 获取文化信息 | 否 |
| GET | `/products/categories/list` | 分类列表 | 否 |
| GET | `/products/regions/list` | 产地列表 | 否 |
| GET | `/products/statistics` | 统计信息 | 否 |

### AI对话API（6个端点）

详细文档：[chat-api.md](./chat-api.md)

| 方法 | 端点 | 功能描述 | 认证 |
|------|------|---------|------|
| POST | `/chat/message` | 发送消息（非流式）| 是 |
| POST | `/chat/stream` | 发送消息（流式SSE）| 是 |
| GET | `/chat/conversations` | 获取对话列表 | 是 |
| GET | `/chat/conversations/{id}` | 获取对话详情 | 是 |
| DELETE | `/chat/conversations/{id}` | 删除对话 | 是 |
| POST | `/chat/feedback` | 对话反馈 | 是 |

### 系统API

| 方法 | 端点 | 功能描述 | 认证 |
|------|------|---------|------|
| GET | `/health` | 健康检查 | 否 |
| GET | `/docs` | Swagger文档 | 否 |
| GET | `/redoc` | ReDoc文档 | 否 |

---

## 使用建议

### 1. 认证流程

```
注册账号 → 登录获取Token → 使用Token访问API → Token过期刷新
```

### 2. 错误处理

```javascript
// JavaScript示例
try {
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    }
  });

  const data = await response.json();

  if (data.code !== 200) {
    // 处理业务错误
    if (data.code === 20003) {
      // Token过期，刷新Token
      await refreshToken();
    } else {
      // 其他错误
      console.error(data.message);
    }
  }
} catch (error) {
  // 处理网络错误
  console.error('Network error:', error);
}
```

### 3. 分页查询

```javascript
// 获取第2页，每页20条
const params = new URLSearchParams({
  page: 2,
  size: 20,
  search: '牛肉',
  category: '肉类'
});

const response = await fetch(`/api/v1/products?${params}`);
```

### 4. 流式响应

```javascript
// 使用SSE接收流式响应
const eventSource = new EventSource('/api/v1/chat/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

eventSource.onerror = (error) => {
  console.error('SSE Error:', error);
  eventSource.close();
};
```

---

## 最佳实践

### 1. 安全建议

- ✅ 使用HTTPS（生产环境）
- ✅ 安全存储Token（避免XSS攻击）
- ✅ 不在URL中传递敏感信息
- ✅ 实现请求签名（高安全场景）
- ✅ 设置合理的请求超时时间

### 2. 性能优化

- ✅ 使用分页查询，避免一次性获取大量数据
- ✅ 合理使用缓存（Redis）
- ✅ 压缩请求和响应（Gzip）
- ✅ 实现请求防抖和节流

### 3. 错误处理

- ✅ 始终检查响应的`code`字段
- ✅ 为不同错误码实现对应处理逻辑
- ✅ 提供友好的错误提示给用户
- ✅ 记录错误日志用于调试

---

## 工具和资源

### Postman集合

导入 [postman-collection.json](./postman-collection.json) 快速测试所有API。

### 代码示例

- JavaScript/TypeScript: `examples/javascript/`
- Python: `examples/python/`
- curl: 各API文档中有完整示例

### 相关文档

- [认证API文档](./authentication-api.md)
- [产品API文档](./products-api.md)
- [AI对话API文档](./chat-api.md)
- [错误码文档](./errors.md)

---

## 变更日志

### v1.0 ([项目完成日期])

- 初始版本发布
- 实现8个认证API端点
- 实现9个产品API端点
- 实现6个AI对话API端点
- 支持JWT双Token认证
- 支持流式SSE响应
- 完整的错误处理机制

---

## 支持与反馈

### 遇到问题？

1. 查看在线文档：http://localhost:8000/docs
2. 检查错误码文档：[errors.md](./errors.md)
3. 查看示例代码：`examples/`

### 技术支持

- 项目仓库：`E:\项目\数商\AI赋能云平台`
- 技术文档：`docs/`
- 邮箱支持：support@example.com

---

**文档版本**: v1.0
**最后更新**: [项目完成日期]
**维护团队**: AI赋能云平台技术团队
