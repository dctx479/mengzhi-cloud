# 对话API

## 获取对话列表

**GET** `/api/chat`

需要认证。

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | number | 否 | 1 | 页码 |
| pageSize | number | 否 | 20 | 每页数量 |

### 响应示例

```json
{
  "data": [
    {
      "id": "chat_123",
      "title": "关于有机苹果的咨询",
      "messages": [],
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:00:00Z",
      "userId": "user_123",
      "tokenCount": 1500
    }
  ],
  "total": 10
}
```

### cURL示例

```bash
curl -X GET "http://localhost:3000/api/chat?page=1&pageSize=20" \
  -H "Authorization: Bearer <your_token>"
```

---

## 获取对话详情

**GET** `/api/chat/:chatId`

需要认证。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chatId | string | 是 | 对话ID |

### 响应示例

```json
{
  "id": "chat_123",
  "title": "关于有机苹果的咨询",
  "messages": [
    {
      "id": "msg_001",
      "content": "请介绍一下有机苹果的特点",
      "role": "user",
      "timestamp": "2024-01-01T00:00:00Z",
      "status": "sent"
    },
    {
      "id": "msg_002",
      "content": "有机苹果是指在生产过程中不使用化学合成农药...",
      "role": "assistant",
      "timestamp": "2024-01-01T00:00:05Z",
      "status": "sent"
    }
  ],
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:00:05Z",
  "userId": "user_123",
  "tokenCount": 1500
}
```

### cURL示例

```bash
curl -X GET http://localhost:3000/api/chat/chat_123 \
  -H "Authorization: Bearer <your_token>"
```

---

## 创建新对话

**POST** `/api/chat`

需要认证。

### 请求参数

```json
{
  "title": "string"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 否 | 对话标题 (可选，系统会自动生成) |

### 响应示例

```json
{
  "id": "chat_123",
  "title": "新对话",
  "messages": [],
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:00:00Z",
  "userId": "user_123",
  "tokenCount": 0
}
```

### cURL示例

```bash
curl -X POST http://localhost:3000/api/chat \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "关于产品的咨询"
  }'
```

---

## 发送消息

**POST** `/api/chat/:chatId/messages`

需要认证。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chatId | string | 是 | 对话ID |

### 请求参数

```json
{
  "content": "string"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | 是 | 消息内容 |

### 响应示例

```json
{
  "id": "msg_001",
  "content": "请介绍一下有机苹果的特点",
  "role": "user",
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "sent"
}
```

### cURL示例

```bash
curl -X POST http://localhost:3000/api/chat/chat_123/messages \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "请介绍一下有机苹果的特点"
  }'
```

---

## 流式发送消息 (SSE)

**GET** `/api/chat/:chatId/messages/stream`

需要认证。使用Server-Sent Events (SSE)实现流式响应。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chatId | string | 是 | 对话ID |

### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| message | string | 是 | 消息内容 (URL编码) |

### SSE事件类型

| 事件 | 说明 | 数据格式 |
|------|------|---------|
| chunk | 消息片段 | `{"type":"chunk","content":"文本片段"}` |
| done | 完成 | `{"type":"done"}` |
| error | 错误 | `{"type":"error","error":"错误信息"}` |

### 使用示例 (JavaScript)

```javascript
const eventSource = new EventSource(
  `http://localhost:3000/api/chat/chat_123/messages/stream?message=${encodeURIComponent('你好')}`,
  {
    headers: {
      Authorization: `Bearer ${token}`
    }
  }
)

eventSource.addEventListener('chunk', (event) => {
  const data = JSON.parse(event.data)
  console.log('收到片段:', data.content)
})

eventSource.addEventListener('done', () => {
  console.log('完成')
  eventSource.close()
})

eventSource.addEventListener('error', (event) => {
  console.error('错误:', event)
  eventSource.close()
})
```

---

## 上传文件

**POST** `/api/chat/:chatId/uploads`

需要认证。支持上传图片、文档等文件。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chatId | string | 是 | 对话ID |

### 请求参数

使用 `multipart/form-data` 格式：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 文件对象 |

### 响应示例

```json
{
  "id": "file_001",
  "name": "document.pdf",
  "size": 1024000,
  "type": "application/pdf",
  "url": "https://example.com/files/document.pdf",
  "uploadedAt": "2024-01-01T00:00:00Z"
}
```

### cURL示例

```bash
curl -X POST http://localhost:3000/api/chat/chat_123/uploads \
  -H "Authorization: Bearer <your_token>" \
  -F "file=@/path/to/document.pdf"
```

---

## 批量上传文件

**POST** `/api/chat/:chatId/uploads/batch`

需要认证。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chatId | string | 是 | 对话ID |

### 请求参数

使用 `multipart/form-data` 格式：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| files | File[] | 是 | 文件数组 |

### 响应示例

```json
[
  {
    "id": "file_001",
    "name": "document1.pdf",
    "size": 1024000,
    "type": "application/pdf",
    "url": "https://example.com/files/document1.pdf",
    "uploadedAt": "2024-01-01T00:00:00Z"
  },
  {
    "id": "file_002",
    "name": "image.jpg",
    "size": 512000,
    "type": "image/jpeg",
    "url": "https://example.com/files/image.jpg",
    "uploadedAt": "2024-01-01T00:00:00Z"
  }
]
```

### cURL示例

```bash
curl -X POST http://localhost:3000/api/chat/chat_123/uploads/batch \
  -H "Authorization: Bearer <your_token>" \
  -F "files=@/path/to/document1.pdf" \
  -F "files=@/path/to/image.jpg"
```

---

## 获取对话历史

**GET** `/api/chat/:chatId/messages`

需要认证。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chatId | string | 是 | 对话ID |

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | number | 否 | 1 | 页码 |
| pageSize | number | 否 | 50 | 每页数量 |

### 响应示例

```json
{
  "data": [
    {
      "id": "msg_001",
      "content": "请介绍一下有机苹果的特点",
      "role": "user",
      "timestamp": "2024-01-01T00:00:00Z",
      "status": "sent"
    }
  ],
  "total": 20
}
```

### cURL示例

```bash
curl -X GET "http://localhost:3000/api/chat/chat_123/messages?page=1&pageSize=50" \
  -H "Authorization: Bearer <your_token>"
```

---

## 删除对话

**DELETE** `/api/chat/:chatId`

需要认证。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chatId | string | 是 | 对话ID |

### 响应示例

```json
{
  "message": "对话已删除"
}
```

### cURL示例

```bash
curl -X DELETE http://localhost:3000/api/chat/chat_123 \
  -H "Authorization: Bearer <your_token>"
```

---

## 清空对话

**POST** `/api/chat/:chatId/clear`

需要认证。清空对话中的所有消息，但保留对话本身。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chatId | string | 是 | 对话ID |

### 响应示例

```json
{
  "message": "对话已清空"
}
```

### cURL示例

```bash
curl -X POST http://localhost:3000/api/chat/chat_123/clear \
  -H "Authorization: Bearer <your_token>"
```

---

## 删除单条消息

**DELETE** `/api/chat/:chatId/messages/:messageId`

需要认证。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chatId | string | 是 | 对话ID |
| messageId | string | 是 | 消息ID |

### 响应示例

```json
{
  "message": "消息已删除"
}
```

### cURL示例

```bash
curl -X DELETE http://localhost:3000/api/chat/chat_123/messages/msg_001 \
  -H "Authorization: Bearer <your_token>"
```

---

## 重新生成消息

**POST** `/api/chat/:chatId/messages/:messageId/regenerate`

需要认证。重新生成AI的回复。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chatId | string | 是 | 对话ID |
| messageId | string | 是 | 消息ID |

### 响应示例

```json
{
  "id": "msg_003",
  "content": "重新生成的回复内容...",
  "role": "assistant",
  "timestamp": "2024-01-01T00:01:00Z",
  "status": "sent"
}
```

### cURL示例

```bash
curl -X POST http://localhost:3000/api/chat/chat_123/messages/msg_002/regenerate \
  -H "Authorization: Bearer <your_token>"
```

---

## 导出对话 (JSON)

**GET** `/api/chat/:chatId/export`

需要认证。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chatId | string | 是 | 对话ID |

### 响应示例

```json
{
  "id": "chat_123",
  "title": "关于有机苹果的咨询",
  "createdAt": "2024-01-01T00:00:00Z",
  "messages": [
    {
      "id": "msg_001",
      "content": "请介绍一下有机苹果的特点",
      "role": "user",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### cURL示例

```bash
curl -X GET http://localhost:3000/api/chat/chat_123/export \
  -H "Authorization: Bearer <your_token>" \
  -o conversation.json
```

---

## 导出对话 (Markdown)

**GET** `/api/chat/:chatId/export/markdown`

需要认证。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chatId | string | 是 | 对话ID |

### 响应示例

```markdown
# 关于有机苹果的咨询

创建时间: 2024-01-01 00:00:00

---

## 用户
请介绍一下有机苹果的特点

## AI助手
有机苹果是指在生产过程中不使用化学合成农药...
```

### cURL示例

```bash
curl -X GET http://localhost:3000/api/chat/chat_123/export/markdown \
  -H "Authorization: Bearer <your_token>" \
  -o conversation.md
```

---

## 收藏/取消收藏消息

**POST** `/api/chat/:chatId/messages/:messageId/favorite`

需要认证。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chatId | string | 是 | 对话ID |
| messageId | string | 是 | 消息ID |

### 响应示例

```json
{
  "id": "msg_001",
  "content": "请介绍一下有机苹果的特点",
  "role": "user",
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "sent",
  "metadata": {
    "favorite": true
  }
}
```

### cURL示例

```bash
curl -X POST http://localhost:3000/api/chat/chat_123/messages/msg_001/favorite \
  -H "Authorization: Bearer <your_token>"
```

---

## 重命名对话

**PATCH** `/api/chat/:chatId`

需要认证。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chatId | string | 是 | 对话ID |

### 请求参数

```json
{
  "title": "string"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 新标题 |

### 响应示例

```json
{
  "id": "chat_123",
  "title": "新标题",
  "messages": [],
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:05:00Z",
  "userId": "user_123",
  "tokenCount": 1500
}
```

### cURL示例

```bash
curl -X PATCH http://localhost:3000/api/chat/chat_123 \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "新标题"
  }'
```

---

## 错误处理

### 常见错误

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| CHAT_NOT_FOUND | 404 | 对话不存在 |
| MESSAGE_NOT_FOUND | 404 | 消息不存在 |
| QUOTA_EXCEEDED | 429 | 配额已用完 |
| FILE_TOO_LARGE | 413 | 文件过大 |
| UNSUPPORTED_FILE_TYPE | 400 | 不支持的文件类型 |
| STREAM_ERROR | 500 | 流式传输错误 |
