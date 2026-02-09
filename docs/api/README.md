# API文档使用指南

欢迎使用"内蒙古农畜产品品牌营销AI赋能云平台"API文档！

---

## 文档结构

本文档集包含以下文件：

```
docs/api/
├── api-index.md                # API总览和索引（从这里开始）
├── authentication-api.md       # 认证API详细文档（8个端点）
├── products-api.md            # 产品API详细文档（9个端点）
├── chat-api.md                # AI对话API详细文档（6个端点）
├── errors.md                  # 完整错误码文档
├── postman-collection.json    # Postman集合（可直接导入）
└── README.md                  # 本文件
```

---

## 快速开始

### 1. 查看API总览

首先阅读 [api-index.md](./api-index.md)，了解：
- API基础信息
- 认证机制
- 统一响应格式
- 错误码体系
- 所有API端点索引

### 2. 选择您需要的API模块

根据功能需求，查阅对应的详细文档：

**用户认证和授权**
- 文档：[authentication-api.md](./authentication-api.md)
- 包含：注册、登录、Token刷新、用户信息管理等

**产品管理**
- 文档：[products-api.md](./products-api.md)
- 包含：产品CRUD、搜索筛选、文化信息等

**AI对话**
- 文档：[chat-api.md](./chat-api.md)
- 包含：发送消息（流式/非流式）、对话管理、反馈等

### 3. 使用Postman快速测试

#### 导入步骤

1. 打开Postman
2. 点击 `Import` 按钮
3. 选择 `postman-collection.json` 文件
4. 导入成功后，会看到3个文件夹：
   - 认证API（8个请求）
   - 产品API（9个请求）
   - AI对话API（6个请求）

#### 配置环境变量

创建一个新的Environment，设置以下变量：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| base_url | http://localhost:8000/api/v1 | API基础URL |
| access_token | 空 | 访问令牌（登录后自动设置）|
| refresh_token | 空 | 刷新令牌（登录后自动设置）|
| user_id | 空 | 用户ID（登录后自动设置）|
| conversation_id | 空 | 对话ID（发送消息后自动设置）|
| product_id | 空 | 产品ID（查询列表后自动设置）|

#### 测试流程

1. **注册账号**
   - 请求：`认证API > 1. 用户注册`
   - 修改请求体中的用户信息
   - 点击 `Send`

2. **登录获取Token**
   - 请求：`认证API > 2. 用户登录`
   - 登录成功后，Token会自动保存到环境变量
   - 后续请求会自动使用该Token

3. **测试其他API**
   - 所有需要认证的请求会自动使用 `{{access_token}}`
   - 可以按顺序测试所有端点

---

## API调用示例

### 基础示例（curl）

```bash
# 1. 登录获取Token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"zhangsan","password":"Password123"}'

# 2. 使用Token访问受保护API
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# 3. 获取产品列表
curl -X GET "http://localhost:8000/api/v1/products?page=1&size=10"
```

### JavaScript示例

```javascript
// 1. 登录
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'zhangsan',
    password: 'Password123'
  })
});

const loginData = await loginResponse.json();
const accessToken = loginData.data.tokens.access_token;

// 2. 使用Token访问API
const response = await fetch('http://localhost:8000/api/v1/auth/me', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const userData = await response.json();
console.log(userData.data);
```

### Python示例

```python
import requests

# 1. 登录
login_url = 'http://localhost:8000/api/v1/auth/login'
login_data = {
    'username': 'zhangsan',
    'password': 'Password123'
}

response = requests.post(login_url, json=login_data)
data = response.json()
access_token = data['data']['tokens']['access_token']

# 2. 使用Token访问API
headers = {
    'Authorization': f'Bearer {access_token}'
}

response = requests.get('http://localhost:8000/api/v1/auth/me', headers=headers)
user_data = response.json()
print(user_data['data'])
```

---

## 错误处理

### 查看错误码

所有错误码都在 [errors.md](./errors.md) 中有详细说明。

### 常见错误

| 错误码 | 说明 | 解决方法 |
|--------|------|---------|
| 10001 | 参数验证失败 | 检查请求参数是否正确 |
| 20003 | Token过期 | 使用refresh_token刷新 |
| 20011 | 密码错误 | 检查密码是否正确 |
| 40010 | 记录不存在 | 检查ID是否有效 |
| 50000 | 系统错误 | 稍后重试或联系技术支持 |

### 错误处理示例

```javascript
async function callAPI(url, options) {
  try {
    const response = await fetch(url, options);
    const data = await response.json();

    if (data.code !== 200) {
      // Token过期，自动刷新
      if (data.code === 20003) {
        await refreshToken();
        return callAPI(url, options); // 重试
      }

      // 显示错误
      console.error(data.message);
      if (data.errors) {
        data.errors.forEach(err => {
          console.error(`${err.field}: ${err.message}`);
        });
      }

      throw new Error(data.message);
    }

    return data.data;
  } catch (error) {
    console.error('API调用失败:', error);
    throw error;
  }
}
```

---

## 认证流程

### 标准流程

```
1. 注册账号 (POST /auth/register)
   ↓
2. 登录获取Token (POST /auth/login)
   ↓
3. 使用access_token访问API
   ↓
4. Token过期时刷新 (POST /auth/refresh)
   ↓
5. 登出 (POST /auth/logout)
```

### Token管理

**Access Token**
- 有效期：30分钟
- 用途：访问受保护的API
- 存储：内存/LocalStorage

**Refresh Token**
- 有效期：7天
- 用途：刷新Access Token
- 存储：安全存储（建议HttpOnly Cookie）

### 自动刷新Token

```javascript
let isRefreshing = false;
let failedQueue = [];

async function refreshToken() {
  if (isRefreshing) {
    return new Promise((resolve, reject) => {
      failedQueue.push({ resolve, reject });
    });
  }

  isRefreshing = true;

  try {
    const refreshToken = localStorage.getItem('refresh_token');
    const response = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    });

    const data = await response.json();

    if (data.code === 200) {
      localStorage.setItem('access_token', data.data.access_token);
      localStorage.setItem('refresh_token', data.data.refresh_token);

      // 处理队列中的请求
      failedQueue.forEach(({ resolve }) => resolve(data.data.access_token));
      failedQueue = [];

      return data.data.access_token;
    } else {
      throw new Error('Refresh failed');
    }
  } catch (error) {
    // 处理队列中的请求
    failedQueue.forEach(({ reject }) => reject(error));
    failedQueue = [];

    // 跳转到登录页
    window.location.href = '/login';
    throw error;
  } finally {
    isRefreshing = false;
  }
}
```

---

## 分页查询

### 查询参数

```
GET /api/v1/products?page=1&size=10
```

### 响应格式

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
  }
}
```

### 无限滚动示例

```javascript
let page = 1;
let hasNext = true;
let isLoading = false;

async function loadMore() {
  if (!hasNext || isLoading) return;

  isLoading = true;

  try {
    const response = await fetch(`/api/v1/products?page=${page}&size=20`);
    const data = await response.json();

    if (data.code === 200) {
      // 追加数据
      products.push(...data.data.items);

      // 更新状态
      hasNext = data.data.pagination.has_next;
      page++;
    }
  } finally {
    isLoading = false;
  }
}

// 监听滚动
window.addEventListener('scroll', () => {
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 500) {
    loadMore();
  }
});
```

---

## 流式响应（SSE）

### 使用场景

AI对话接口支持流式响应，适合实时展示AI生成内容。

### 示例代码

```javascript
async function sendMessageStream(content, conversationId) {
  const response = await fetch('/api/v1/chat/stream', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      content: content,
      conversation_id: conversationId
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let fullContent = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.substring(6));

        if (data.status === 'completed') {
          console.log('Stream completed');
          return fullContent;
        }

        if (data.error) {
          throw new Error(data.message);
        }

        // 追加增量内容
        fullContent += data.delta;
        // 更新UI
        updateUI(fullContent);
      }
    }
  }
}
```

---

## 常见问题

### Q: 如何获取在线文档？

A: 启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Q: Token存储在哪里？

A:
- **开发环境**: LocalStorage
- **生产环境**: HttpOnly Cookie（更安全）

### Q: 如何处理并发请求中的Token刷新？

A: 使用队列机制，参考"自动刷新Token"示例。

### Q: 如何实现请求重试？

A: 参考 [errors.md](./errors.md) 中的"错误处理最佳实践"。

### Q: 如何测试流式响应？

A:
- Postman: 需要特殊设置
- 浏览器: 使用fetch + ReadableStream
- curl: 使用 `-N` 参数

### Q: 如何区分哪些API需要认证？

A: 参考 [api-index.md](./api-index.md) 中的端点索引表，"认证"列标注了是否需要。

---

## 版本信息

- **API版本**: v1.0
- **文档版本**: v1.0
- **最后更新**: [项目完成日期]
- **维护团队**: AI赋能云平台技术团队

---

## 技术支持

### 遇到问题？

1. 查看对应API的详细文档
2. 查看 [errors.md](./errors.md) 获取错误码说明
3. 使用Postman集合测试
4. 查看在线文档: http://localhost:8000/docs

### 反馈建议

如有文档问题或改进建议，请联系技术团队。

---

## 更新日志

### v1.0 ([项目完成日期])

- 初始版本发布
- 23个API端点完整文档
- Postman集合
- 完整错误码文档
- 使用示例和最佳实践

---

**祝您使用愉快！**
