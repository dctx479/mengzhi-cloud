# AI对话API文档

**AI对话和会话管理相关API**

Base URL: `http://localhost:8000/api/v1/chat`

---

## 目录

- [1. 发送消息（非流式）](#1-发送消息非流式)
- [2. 发送消息（流式SSE）](#2-发送消息流式sse)
- [3. 获取对话列表](#3-获取对话列表)
- [4. 获取对话详情](#4-获取对话详情)
- [5. 删除对话](#5-删除对话)
- [6. 对话反馈](#6-对话反馈)

---

## 1. 发送消息（非流式）

发送对话消息，返回完整响应（非流式）。

### 端点信息

```
POST /api/v1/chat/message
```

### 请求Header

```
Authorization: Bearer {access_token}
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | 是 | 消息内容，1-10000字符 |
| conversation_id | integer | 否 | 对话ID（为空则创建新对话）|
| agent_type | string | 否 | 代理类型：xiaoshu/xiaoshang/assistant，默认assistant |

### 请求示例

#### curl

```bash
curl -X POST "http://localhost:8000/api/v1/chat/message" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "content": "请介绍一下内蒙古的特色农产品",
    "conversation_id": null,
    "agent_type": "assistant"
  }'
```

#### JavaScript

```javascript
const accessToken = localStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/api/v1/chat/message', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    content: '请介绍一下内蒙古的特色农产品',
    conversation_id: null,
    agent_type: 'assistant'
  })
});

const data = await response.json();
console.log(data.data.message.content);
```

#### Python

```python
import requests

url = 'http://localhost:8000/api/v1/chat/message'
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}
payload = {
    'content': '请介绍一下内蒙古的特色农产品',
    'conversation_id': None,
    'agent_type': 'assistant'
}

response = requests.post(url, headers=headers, json=payload)
data = response.json()
print(data['data']['message']['content'])
```

### 响应示例

#### 成功响应（200 OK）

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "conversation_id": 1,
    "message": {
      "id": "msg-uuid-123",
      "conversation_id": 1,
      "role": "assistant",
      "content": "内蒙古拥有丰富的特色农产品，主要包括：\n1. 草原牛羊肉：呼伦贝尔、锡林郭勒等地的牛羊肉品质优良\n2. 奶制品：伊利、蒙牛等知名品牌\n3. 杂粮：荞麦、燕麦、莜面等\n4. 羊绒制品：阿尔巴斯羊绒世界闻名...",
      "input_tokens": 15,
      "output_tokens": 120,
      "total_tokens": 135,
      "cost": 0.00027,
      "model": "deepseek-chat",
      "finish_reason": "stop",
      "created_at": "[项目完成日期]T10:00:00",
      "updated_at": "[项目完成日期]T10:00:00"
    },
    "usage": {
      "prompt_tokens": 15,
      "completion_tokens": 120,
      "total_tokens": 135
    }
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

### 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 10001 | 400 | 参数验证失败 |
| 20001 | 401 | Token缺失 |
| 20002 | 401 | Token无效 |
| 40010 | 404 | 对话不存在 |
| 50000 | 500 | 系统错误 |

### 注意事项

- conversation_id为空时自动创建新对话
- AI模型使用DeepSeek API
- Token消耗和费用会记录在响应中
- 支持上下文对话，需提供conversation_id

---

## 2. 发送消息（流式SSE）

发送对话消息，返回流式响应（Server-Sent Events）。

### 端点信息

```
POST /api/v1/chat/stream
```

### 请求Header

```
Authorization: Bearer {access_token}
```

### 请求参数

同"发送消息（非流式）"接口。

### 请求示例

#### curl

```bash
curl -N -X POST "http://localhost:8000/api/v1/chat/stream" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "content": "请介绍一下内蒙古的特色农产品",
    "conversation_id": 1
  }'
```

#### JavaScript（使用EventSource）

```javascript
const accessToken = localStorage.getItem('access_token');

// 注意：EventSource不支持自定义Header，需要使用fetch + ReadableStream
const response = await fetch('http://localhost:8000/api/v1/chat/stream', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    content: '请介绍一下内蒙古的特色农产品',
    conversation_id: 1
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

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
        break;
      }

      if (data.error) {
        console.error('Error:', data.message);
        break;
      }

      // 处理流式数据块
      console.log('Chunk:', data);
      // 通常包含：conversation_id, content, delta（增量内容）
    }
  }
}
```

#### Python（使用requests stream）

```python
import requests
import json

url = 'http://localhost:8000/api/v1/chat/stream'
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}
payload = {
    'content': '请介绍一下内蒙古的特色农产品',
    'conversation_id': 1
}

response = requests.post(url, headers=headers, json=payload, stream=True)

for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            data = json.loads(line_str[6:])

            if data.get('status') == 'completed':
                print('Stream completed')
                break

            if data.get('error'):
                print(f"Error: {data.get('message')}")
                break

            # 处理流式数据块
            print(f"Chunk: {data.get('delta', '')}")
```

### 响应格式

#### SSE数据块

```
data: {"conversation_id": 1, "delta": "内蒙古", "content": "内蒙古"}

data: {"conversation_id": 1, "delta": "拥有", "content": "内蒙古拥有"}

data: {"conversation_id": 1, "delta": "丰富的", "content": "内蒙古拥有丰富的"}

...

data: {"status": "completed"}
```

#### 错误响应

```
data: {"error": true, "code": 50000, "message": "Stream processing failed"}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| conversation_id | integer | 对话ID |
| delta | string | 增量内容（新增的文本）|
| content | string | 累积内容（从开始到现在的全部文本）|
| status | string | 状态：completed（完成）|
| error | boolean | 是否错误 |
| code | integer | 错误码 |
| message | string | 错误消息 |

### 注意事项

- SSE连接需要保持打开状态
- 浏览器需要支持EventSource或fetch ReadableStream
- 响应头：`Content-Type: text/event-stream`
- 响应头：`Cache-Control: no-cache`
- 流式响应适合实时展示AI生成内容
- 连接中断可能导致消息不完整

---

## 3. 获取对话列表

获取当前用户的对话列表，支持分页。

### 端点信息

```
GET /api/v1/chat/conversations
```

### 请求Header

```
Authorization: Bearer {access_token}
```

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码，≥1 |
| page_size | integer | 否 | 20 | 每页数量，1-100 |
| status | string | 否 | active | 状态筛选：active/archived/deleted |

### 请求示例

#### curl

```bash
curl -X GET "http://localhost:8000/api/v1/chat/conversations?page=1&page_size=20&status=active" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### JavaScript

```javascript
const accessToken = localStorage.getItem('access_token');

const params = new URLSearchParams({
  page: 1,
  page_size: 20,
  status: 'active'
});

const response = await fetch(`http://localhost:8000/api/v1/chat/conversations?${params}`, {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const data = await response.json();
console.log(data.data.items);
```

#### Python

```python
import requests

url = 'http://localhost:8000/api/v1/chat/conversations'
headers = {
    'Authorization': f'Bearer {access_token}'
}
params = {
    'page': 1,
    'page_size': 20,
    'status': 'active'
}

response = requests.get(url, headers=headers, params=params)
print(response.json())
```

### 响应示例

#### 成功响应（200 OK）

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 50,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "conversation_uuid": "conv-uuid-123",
        "user_id": 1,
        "title": "关于内蒙古特色农产品的讨论",
        "agent_type": "assistant",
        "context_product_id": null,
        "message_count": 5,
        "total_tokens": 1250,
        "status": "active",
        "last_message_at": "[项目完成日期]T10:00:00",
        "created_at": "[项目完成日期]T09:00:00",
        "updated_at": "[项目完成日期]T10:00:00"
      },
      {
        "id": 2,
        "conversation_uuid": "conv-uuid-456",
        "user_id": 1,
        "title": "草原牛肉产品咨询",
        "agent_type": "xiaoshu",
        "context_product_id": 1,
        "message_count": 3,
        "total_tokens": 680,
        "status": "active",
        "last_message_at": "[项目完成日期]T08:30:00",
        "created_at": "[项目完成日期]T08:00:00",
        "updated_at": "[项目完成日期]T08:30:00"
      }
    ]
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 对话ID |
| conversation_uuid | string | 对话UUID |
| user_id | integer | 用户ID |
| title | string | 对话标题 |
| agent_type | string | 代理类型 |
| context_product_id | integer | 关联产品ID |
| message_count | integer | 消息数量 |
| total_tokens | integer | 总Token消耗 |
| status | string | 状态：active/archived/deleted |
| last_message_at | datetime | 最后消息时间 |

---

## 4. 获取对话详情

获取对话详情，包含所有消息。

### 端点信息

```
GET /api/v1/chat/conversations/{conversation_id}
```

### 请求Header

```
Authorization: Bearer {access_token}
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| conversation_id | string | 是 | 对话ID或UUID |

### 请求示例

#### curl

```bash
curl -X GET "http://localhost:8000/api/v1/chat/conversations/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### JavaScript

```javascript
const accessToken = localStorage.getItem('access_token');
const conversationId = 1;

const response = await fetch(`http://localhost:8000/api/v1/chat/conversations/${conversationId}`, {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const data = await response.json();
console.log(data.data.messages);
```

#### Python

```python
import requests

conversation_id = 1
url = f'http://localhost:8000/api/v1/chat/conversations/{conversation_id}'
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
    "id": 1,
    "conversation_uuid": "conv-uuid-123",
    "user_id": 1,
    "title": "关于内蒙古特色农产品的讨论",
    "agent_type": "assistant",
    "message_count": 3,
    "total_tokens": 450,
    "status": "active",
    "created_at": "[项目完成日期]T09:00:00",
    "updated_at": "[项目完成日期]T10:00:00",
    "messages": [
      {
        "id": 1,
        "message_uuid": "msg-uuid-1",
        "conversation_id": 1,
        "role": "user",
        "content": "请介绍一下内蒙古的特色农产品",
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "cost": 0.0,
        "created_at": "[项目完成日期]T09:00:00"
      },
      {
        "id": 2,
        "message_uuid": "msg-uuid-2",
        "conversation_id": 1,
        "role": "assistant",
        "content": "内蒙古拥有丰富的特色农产品...",
        "input_tokens": 15,
        "output_tokens": 120,
        "total_tokens": 135,
        "cost": 0.00027,
        "model": "deepseek-chat",
        "created_at": "[项目完成日期]T09:00:30"
      },
      {
        "id": 3,
        "message_uuid": "msg-uuid-3",
        "conversation_id": 1,
        "role": "user",
        "content": "草原牛肉有什么特点？",
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "cost": 0.0,
        "created_at": "[项目完成日期]T09:01:00"
      }
    ]
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

### 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 20001 | 401 | Token缺失 |
| 20002 | 401 | Token无效 |
| 40010 | 404 | 对话不存在 |
| 50000 | 500 | 系统错误 |

---

## 5. 删除对话

删除指定对话。

### 端点信息

```
DELETE /api/v1/chat/conversations/{conversation_id}
```

### 请求Header

```
Authorization: Bearer {access_token}
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| conversation_id | string | 是 | 对话ID或UUID |

### 请求示例

#### curl

```bash
curl -X DELETE "http://localhost:8000/api/v1/chat/conversations/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### JavaScript

```javascript
const accessToken = localStorage.getItem('access_token');
const conversationId = 1;

const response = await fetch(`http://localhost:8000/api/v1/chat/conversations/${conversationId}`, {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const data = await response.json();
console.log(data);
```

#### Python

```python
import requests

conversation_id = 1
url = f'http://localhost:8000/api/v1/chat/conversations/{conversation_id}'
headers = {
    'Authorization': f'Bearer {access_token}'
}

response = requests.delete(url, headers=headers)
print(response.json())
```

### 响应示例

#### 成功响应（200 OK）

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "message": "Conversation deleted successfully"
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

### 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 20001 | 401 | Token缺失 |
| 40010 | 404 | 对话不存在 |
| 50000 | 500 | 系统错误 |

### 注意事项

- 删除操作是软删除，数据不会真正删除
- 删除后对话状态变为"deleted"，不会在列表中显示

---

## 6. 对话反馈

对AI回复进行评分和反馈。

### 端点信息

```
POST /api/v1/chat/feedback
```

### 请求Header

```
Authorization: Bearer {access_token}
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| message_id | integer | 是 | 消息ID |
| rating | integer | 是 | 评分，1-5 |
| feedback | string | 否 | 反馈内容，最长1000字符 |
| feedback_type | string | 否 | 反馈类型：helpful/unhelpful/incorrect |

### 请求示例

#### curl

```bash
curl -X POST "http://localhost:8000/api/v1/chat/feedback" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": 2,
    "rating": 5,
    "feedback": "回答很详细，很有帮助",
    "feedback_type": "helpful"
  }'
```

#### JavaScript

```javascript
const accessToken = localStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/api/v1/chat/feedback', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message_id: 2,
    rating: 5,
    feedback: '回答很详细，很有帮助',
    feedback_type: 'helpful'
  })
});

const data = await response.json();
console.log(data);
```

#### Python

```python
import requests

url = 'http://localhost:8000/api/v1/chat/feedback'
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}
payload = {
    'message_id': 2,
    'rating': 5,
    'feedback': '回答很详细，很有帮助',
    'feedback_type': 'helpful'
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

### 响应示例

#### 成功响应（200 OK）

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "message_id": 2,
    "rating": 5,
    "feedback": "回答很详细，很有帮助",
    "feedback_type": "helpful",
    "updated_at": "[项目完成日期]T10:00:00"
  },
  "timestamp": "[项目完成日期]T10:00:00"
}
```

### 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 10001 | 400 | 参数验证失败 |
| 20001 | 401 | Token缺失 |
| 40010 | 404 | 消息不存在 |
| 50000 | 500 | 系统错误 |

---

## Token消耗说明

### DeepSeek定价

- 输入Token：$0.14 / 1M tokens
- 输出Token：$0.28 / 1M tokens

### 计算方式

```
cost = (input_tokens * 0.14 + output_tokens * 0.28) / 1000000
```

### 示例

```json
{
  "input_tokens": 100,
  "output_tokens": 200,
  "total_tokens": 300,
  "cost": 0.00007  // (100 * 0.14 + 200 * 0.28) / 1000000 = 0.00007 USD
}
```

---

## 上下文管理

### 对话上下文

- 系统自动管理对话上下文
- 发送消息时提供conversation_id即可
- 上下文包含历史消息（默认最近10条）
- Token消耗会随上下文增加而增加

### 新建对话

```javascript
// conversation_id为null创建新对话
const response = await fetch('/api/v1/chat/message', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    content: '你好',
    conversation_id: null
  })
});
```

### 继续对话

```javascript
// 使用返回的conversation_id继续对话
const conversationId = data.data.conversation_id;

const response = await fetch('/api/v1/chat/message', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    content: '继续',
    conversation_id: conversationId
  })
});
```

---

## 常见问题

### Q: 流式响应和非流式响应有什么区别？

A:
- 非流式：等待AI完全生成后返回完整响应，适合对实时性要求不高的场景
- 流式：实时返回AI生成的内容，适合聊天界面实时展示

### Q: 如何实现打字机效果？

A: 使用流式响应接口，接收delta字段逐字追加到界面：

```javascript
let fullContent = '';
const reader = response.body.getReader();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  // 解析SSE数据
  const data = parseSSE(chunk);

  // 追加增量内容
  fullContent += data.delta;
  // 更新界面显示
  updateUI(fullContent);
}
```

### Q: 对话上下文如何清除？

A: 创建新对话（conversation_id为null），或删除旧对话。

### Q: Token消耗如何优化？

A:
- 定期清理旧对话
- 限制上下文长度
- 使用更精简的提示词
- 避免重复发送相同内容

---

**文档版本**: v1.0
**最后更新**: [项目完成日期]
