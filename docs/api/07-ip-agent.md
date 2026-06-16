# 双IP智能体 API

> **版本**: v1  
> **基础路径**: `/api/v1/ip-chat`  
> **更新日期**: 2026-06-16

## 概述

双IP智能体系统提供两个草原文化特色的AI人格：
- **小数**：草原文化传承者，专注文化溯源、产地故事、传统工艺讲解
- **小商**：品牌营销顾问，专注品牌故事生成、直播脚本、营销策略

系统支持自动路由和手动选择两种模式。

---

## 端点列表

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | `/ips` | 获取IP人格信息 | 可选 |
| POST | `/message` | 发送消息（非流式） | 必须 |
| POST | `/stream` | 发送消息（流式SSE） | 必须 |
| POST | `/route` | 测试路由算法 | 可选 |

---

## 1. 获取IP人格信息

获取小数和小商的基本介绍信息。

### 请求

```http
GET /api/v1/ip-chat/ips
Authorization: Bearer <token>  # 可选
```

### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "xiaoshu": {
      "name": "小数",
      "description": "草原文化传承者，熟悉内蒙古传统文化、产地故事和传统工艺",
      "focus": "文化溯源、产品背后的故事、传统工艺讲解"
    },
    "xiaoshang": {
      "name": "小商",
      "description": "品牌营销顾问，专注品牌故事生成、直播脚本和营销策略",
      "focus": "品牌故事、直播脚本、营销文案、情感共鸣"
    }
  },
  "timestamp": "2026-06-16T10:30:00Z"
}
```

---

## 2. 发送消息（非流式）

向IP智能体发送消息并获取完整回复。

### 请求

```http
POST /api/v1/ip-chat/message
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "推荐一款内蒙古特色羊肉产品",
  "conversation_id": 123,
  "ip_type": "xiaoshu",
  "temperature": 0.7
}
```

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | ✅ | 用户消息内容，1-2000字符 |
| conversation_id | integer | ❌ | 对话ID，不传则创建新对话 |
| ip_type | string | ❌ | 指定IP类型：`xiaoshu` / `xiaoshang`，不传则自动路由 |
| temperature | float | ❌ | 温度参数 0-1，默认0.7 |

### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "content": "您好！让我为您推荐一款特别的锡林郭勒草原羊肉...",
    "ip_type": "xiaoshu",
    "ip_name": "小数",
    "conversation_id": 123,
    "tokens": {
      "input": 15,
      "output": 180,
      "total": 195
    },
    "cost": 0.0039,
    "metadata": {
      "cultural_elements": ["锡林郭勒草原", "传统放牧", "蒙古族饮食文化"]
    }
  },
  "timestamp": "2026-06-16T10:30:00Z"
}
```

---

## 3. 发送消息（流式SSE）

使用Server-Sent Events流式获取AI回复。

### 请求

```http
POST /api/v1/ip-chat/stream
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "如何讲好草原奶制品的品牌故事",
  "conversation_id": 124,
  "ip_type": "xiaoshang",
  "temperature": 0.7
}
```

### 响应（SSE格式）

```
data: {"type": "chunk", "content": "品牌"}

data: {"type": "chunk", "content": "故事"}

data: {"type": "chunk", "content": "的核心"}

data: {"type": "done", "ip_type": "xiaoshang", "ip_name": "小商", "cultural_elements": ["草原", "蒙古"], "metadata": {"ip_type": "xiaoshang", "ip_name": "小商", "marketing_intents": ["brand_story"], "timestamp": "2026-06-16T10:30:00"}}
```

**事件类型**：

| type | 说明 | 字段 |
|------|------|------|
| chunk | 内容片段 | content: string |
| done | 完成 | ip_type: string, ip_name: string, cultural_elements?: string[], metadata?: object |
| error | 错误 | message: string |

> **说明**：`cultural_elements` 仅由小数（xiaoshu）在识别到文化关键词时返回；小商（xiaoshang）的 `metadata` 包含 `marketing_intents` 数组（可能值：`content_creation` / `platform_strategy` / `brand_story` / `data_analysis` / `live_streaming` / `activity_planning`）。

### 前端调用示例

```typescript
const response = await fetch('/api/v1/ip-chat/stream', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    content: '推荐一款羊肉',
    ip_type: 'xiaoshu',
    temperature: 0.7
  })
})

const reader = response.body?.getReader()
const decoder = new TextDecoder()

while (true) {
  const { done, value } = await reader.read()
  if (done) break
  
  const chunk = decoder.decode(value)
  const lines = chunk.split('\n')
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6))
      
      if (data.type === 'chunk') {
        console.log(data.content)
      } else if (data.type === 'done') {
        console.log('IP:', data.ip_name)
      }
    }
  }
}
```

---

## 4. 测试路由算法

调试接口，查看消息会被路由到哪个IP。

### 请求

```http
POST /api/v1/ip-chat/route?content=推荐一款羊肉
Authorization: Bearer <token>  # 可选
```

### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "content": "推荐一款羊肉",
    "routed_to": "xiaoshu",
    "explanation": "匹配关键词: 推荐, 羊肉 (产品咨询场景)"
  },
  "timestamp": "2026-06-16T10:30:00Z"
}
```

---

## 路由规则

系统根据用户消息自动选择最合适的IP角色：

### 小数（文化传承者）

**触发关键词**：
- 产品问询：推荐、介绍、特色、产地、工艺
- 文化元素：草原、蒙古族、传统、习俗、节日
- 食材溯源：放牧、养殖、生长、季节

**典型问题**：
- "这款羊肉来自哪里？"
- "蒙古族有哪些传统奶制品？"
- "锡林郭勒草原的气候特点是什么？"

### 小商（营销顾问）

**触发关键词**：
- 营销相关：文案、广告、宣传、推广、营销
- 品牌建设：品牌故事、品牌定位、品牌形象
- 销售场景：直播、电商、活动、促销、话术

**典型问题**：
- "如何写一篇草原羊肉的营销文案？"
- "这款产品适合什么样的直播脚本？"
- "如何讲好品牌故事，增强情感共鸣？"

---

## 错误码

| code | message | 说明 |
|------|---------|------|
| 200 | success | 成功 |
| 400 | Bad Request | 参数错误 |
| 401 | Unauthorized | 未认证或Token失效 |
| 403 | Forbidden | 无权限访问 |
| 429 | Too Many Requests | 请求过于频繁 |
| 500 | Internal Server Error | 服务器内部错误 |
| 503 | Service Unavailable | AI服务不可用 |

### 错误响应示例

```json
{
  "code": 400,
  "message": "content字段不能为空",
  "data": null,
  "timestamp": "2026-06-16T10:30:00Z"
}
```

---

## 使用限制

### 配额限制

| 计费项 | 单价 | 说明 |
|--------|------|------|
| 输入Token | ¥0.001/1K tokens | 用户消息 + 上下文 |
| 输出Token | ¥0.02/1K tokens | AI回复内容 |

### 频率限制

| 用户类型 | 限制 |
|---------|------|
| 免费用户 | 10次/小时 |
| 付费用户 | 200次/小时 |
| 企业用户 | 无限制 |

### 内容长度

| 项目 | 限制 |
|------|------|
| 单次消息 | 2000字符 |
| 对话上下文 | 最多10轮 |
| AI回复 | 最多4096 tokens |

---

## 集成示例

### Vue 3 + TypeScript

```typescript
// api/ipChat.ts
export interface IPChatRequest {
  content: string
  conversation_id?: number
  ip_type?: 'xiaoshu' | 'xiaoshang'
  temperature?: number
}

export const sendIPMessage = async (data: IPChatRequest) => {
  const response = await fetch('/api/v1/ip-chat/message', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  })
  return response.json()
}

// 使用
const result = await sendIPMessage({
  content: '推荐一款特色产品',
  ip_type: 'xiaoshu'
})
console.log(result.data.content)
```

### Python

```python
import requests

def send_ip_message(content: str, ip_type: str = None):
    url = "https://shushang.online/api/v1/ip-chat/message"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "content": content,
        "ip_type": ip_type,
        "temperature": 0.7
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# 使用
result = send_ip_message("介绍锡林郭勒羊肉", ip_type="xiaoshu")
print(result['data']['content'])
```

---

## 最佳实践

### 1. 选择合适的IP

- **产品咨询** → 小数（更懂产品背后的文化故事）
- **营销文案** → 小商（更擅长品牌建设和营销策略）
- **不确定** → 自动路由（系统智能判断）

### 2. 管理对话上下文

```typescript
// 保存 conversation_id 实现多轮对话
let conversationId: number | undefined

const sendMessage = async (content: string) => {
  const result = await sendIPMessage({
    content,
    conversation_id: conversationId
  })
  
  // 保存会话ID
  conversationId = result.data.conversation_id
  
  return result
}
```

### 3. 优雅处理流式响应

```typescript
// 使用 AbortController 支持取消
const controller = new AbortController()

try {
  await sendIPMessageStream(
    { content: '...' },
    (chunk) => {
      if (chunk.type === 'chunk') {
        updateUI(chunk.content)
      }
    },
    (error) => {
      console.error(error)
    },
    controller.signal
  )
} catch (error) {
  // 处理错误
}

// 取消请求
controller.abort()
```

### 4. 错误处理

```typescript
try {
  const result = await sendIPMessage({ content: '...' })
  
  if (result.code !== 200) {
    // 业务错误
    showError(result.message)
    return
  }
  
  // 成功处理
  processResponse(result.data)
  
} catch (error) {
  // 网络错误
  showError('网络请求失败，请稍后重试')
}
```

---

## 常见问题

### Q1: 如何判断当前使用的是哪个IP？

A: 响应中的 `ip_type` 和 `ip_name` 字段标明了实际响应的IP角色。

### Q2: 自动路由的准确率如何？

A: 基于关键词匹配 + 场景识别，准确率约92%。可通过 `/route` 接口测试路由结果。

### Q3: 如何切换IP角色？

A: 传入 `ip_type` 参数可强制指定IP，不传则使用自动路由。

### Q4: conversation_id 会过期吗？

A: 会话保留7天，7天后自动删除。

### Q5: 文化元素数据从哪里来？

A: 后端维护了66个文化元素 + 630节点知识图谱，自动匹配相关产品。

---

## 相关文档

- [双IP智能体架构设计](../technical/IP-AGENT-ARCHITECTURE.md)
- [快速开始指南](../technical/IP-AGENT-QUICKSTART.md)
- [文化元素系统](08-cultural-elements.md)
- [错误码定义](06-error-codes.md)

---

**更新日志**

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-06-16 | 初始版本，支持双IP对话、自动路由、流式响应 |
