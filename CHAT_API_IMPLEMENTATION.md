# AI对话API完整实现指南

## 项目概览

本文档总结了AI对话系统的完整实现，包括6个API端点、数据模型、服务层和业务逻辑。

## 已生成的文件结构

```
backend/app/
├── api/
│   ├── __init__.py                  # 路由初始化（已更新）
│   ├── auth.py                      # 认证路由（现有）
│   ├── chat.py                      # 对话路由（已更新）
│   ├── deps.py                      # 依赖注入（现有）
│   └── products.py                  # 产品路由（现有）
│
├── models/
│   ├── __init__.py                  # （现有）
│   ├── base.py                      # 基类（现有）
│   ├── conversation.py              # 对话模型（现有）
│   ├── message.py                   # 消息模型（新增）
│   ├── user.py                      # 用户模型（现有）
│   ├── product.py                   # 产品模型（现有）
│   └── enterprise.py                # 企业模型（现有）
│
├── schemas/
│   └── chat.py                      # 对话Schema（新增）
│
├── services/
│   ├── ai/
│   │   ├── __init__.py              # 初始化（新增）
│   │   ├── deepseek_client.py       # DeepSeek客户端（新增）
│   │   └── prompt_templates.py      # Prompt模板（新增）
│   ├── chat_service.py              # 对话服务（待创建）
│   └── ...其他服务
│
├── main.py                          # 主应用（已更新）
├── database.py                      # 数据库配置（新增）
└── core/
    ├── config.py                    # 配置（现有）
    ├── errors.py                    # 错误定义（现有）
    └── responses.py                 # 响应处理（现有）
```

## API端点汇总

### 1. POST /api/v1/chat/message - 发送消息（非流式）
发送消息并等待完整响应。

**请求体:**
```json
{
  "content": "用户消息内容",
  "conversation_id": 12345,  // 可选，为空则创建新对话
  "agent_type": "assistant"  // 可选，默认为assistant
}
```

**响应:**
```json
{
  "id": "响应ID",
  "conversation_id": 12345,
  "message": {
    "id": 67890,
    "message_uuid": "xxx",
    "conversation_id": 12345,
    "role": "assistant",
    "content": "AI响应内容",
    "input_tokens": 100,
    "output_tokens": 200,
    "total_tokens": 300,
    "cost": 0.0003,
    "model": "deepseek-chat",
    "created_at": "[项目完成日期]T10:00:00",
    "updated_at": "[项目完成日期]T10:00:00"
  },
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 200,
    "total_tokens": 300
  }
}
```

### 2. POST /api/v1/chat/stream - 发送消息（流式SSE）
发送消息并以流式方式返回响应。

**请求体:**
```json
{
  "content": "用户消息",
  "conversation_id": 12345,
  "agent_type": "assistant"
}
```

**响应:** Server-Sent Events (SSE) 流
```
data: {"id": 12345, "object": "text_completion.chunk", "choices": [{"delta": {"content": "第一段"}}]}

data: {"id": 12345, "object": "text_completion.chunk", "choices": [{"delta": {"content": "文本"}}]}

...

data: {"status": "completed"}
```

### 3. GET /api/v1/chat/conversations - 获取对话列表
获取当前用户的对话列表。

**查询参数:**
- `page`: 页码，默认为1
- `page_size`: 每页数量，默认为20

**响应:**
```json
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": 12345,
      "conversation_uuid": "xxx",
      "user_id": 1,
      "title": "对话标题",
      "agent_type": "assistant",
      "message_count": 5,
      "total_tokens": 1000,
      "status": "active",
      "last_message_at": "[项目完成日期]T10:00:00",
      "created_at": "[项目完成日期]T09:00:00",
      "updated_at": "[项目完成日期]T10:00:00"
    }
  ]
}
```

### 4. GET /api/v1/chat/conversations/{id} - 获取对话详情
获取指定对话的详情，包括所有消息。

**响应:**
```json
{
  "id": 12345,
  "conversation_uuid": "xxx",
  "user_id": 1,
  "title": "对话标题",
  "agent_type": "assistant",
  "message_count": 5,
  "total_tokens": 1000,
  "status": "active",
  "messages": [
    {
      "id": 1,
      "message_uuid": "xxx",
      "conversation_id": 12345,
      "role": "user",
      "content": "用户消息",
      "total_tokens": 10,
      "cost": 0.00001,
      "created_at": "[项目完成日期]T09:00:00",
      "updated_at": "[项目完成日期]T09:00:00"
    },
    {
      "id": 2,
      "message_uuid": "yyy",
      "conversation_id": 12345,
      "role": "assistant",
      "content": "AI响应",
      "total_tokens": 50,
      "cost": 0.00005,
      "created_at": "[项目完成日期]T09:01:00",
      "updated_at": "[项目完成日期]T09:01:00"
    }
  ]
}
```

### 5. DELETE /api/v1/chat/conversations/{id} - 删除对话
删除（软删除）指定的对话。

**响应:**
```json
{
  "success": true,
  "message": "Conversation deleted successfully"
}
```

### 6. POST /api/v1/chat/feedback - 添加反馈
为消息添加用户反馈。

**请求体:**
```json
{
  "message_id": 67890,
  "rating": 5,
  "feedback": "非常有帮助",
  "feedback_type": "helpful"
}
```

**响应:**
```json
{
  "message_id": 67890,
  "rating": 5,
  "feedback": "非常有帮助",
  "feedback_type": "helpful",
  "updated_at": "[项目完成日期]T10:00:00"
}
```

## 核心技术实现

### DeepSeek API客户端
文件：`backend/app/services/ai/deepseek_client.py`

**主要功能:**
- 非流式API调用
- 流式SSE支持
- 自动重试（tenacity）
- Token计数和成本计算
- API健康检查

**使用示例:**
```python
client = await get_deepseek_client()

# 非流式
response = await client.chat_completion(
    messages=[{"role": "user", "content": "你好"}],
    system_prompt="你是一个助手",
    temperature=0.7
)

# 流式
async for chunk in client.chat_completion_stream(
    messages=[{"role": "user", "content": "你好"}],
    system_prompt="你是一个助手"
):
    print(chunk)

# 成本计算
cost = client.calculate_cost(input_tokens=100, output_tokens=200)
```

### Prompt工程
文件：`backend/app/services/ai/prompt_templates.py`

**预定义模板:**
- 系统提示词（SYSTEM_PROMPT）
- 知识库注入（KNOWLEDGE_INJECT）
- 对话上下文（CONTEXT_TEMPLATE）
- 分析报告（ANALYSIS_PROMPT）
- 品牌定位（BRAND_POSITIONING）
- 渠道推荐（CHANNEL_RECOMMENDATION）
- 营销策略（MARKETING_STRATEGY）

**使用示例:**
```python
system_prompt = PromptTemplates.get_system_prompt()
context_prompt = PromptTemplates.build_context_aware_prompt(
    user_id="123",
    topic="品牌咨询"
)
```

### 对话服务
文件：`backend/app/services/chat_service.py`

**主要方法:**
- `send_message()` - 非流式消息
- `send_message_stream()` - 流式消息
- `get_conversations()` - 获取对话列表
- `get_conversation_detail()` - 获取对话详情
- `delete_conversation()` - 删除对话
- `update_conversation()` - 更新对话
- `add_feedback()` - 添加反馈

### 数据模型

**Conversation（对话）**
- id: 对话ID
- conversation_uuid: UUID标识
- user_id: 用户ID
- title: 对话标题
- agent_type: AI代理类型（xiaoshu/xiaoshang/assistant）
- context_product_id: 上下文产品ID
- message_count: 消息总数
- total_tokens: 总token消耗
- status: 状态（active/archived/deleted）
- last_message_at: 最后消息时间

**Message（消息）**
- id: 消息ID
- message_uuid: UUID标识
- conversation_id: 对话ID
- role: 角色（user/assistant/system）
- content: 消息内容
- input_tokens: 输入token数
- output_tokens: 输出token数
- total_tokens: 总token数
- cost: 消息成本
- rating: 用户评分（1-5）
- feedback: 反馈内容
- feedback_type: 反馈类型（helpful/unhelpful/incorrect）

## SSE流式响应实现

流式响应使用Server-Sent Events格式，允许服务器在连接保持打开的情况下多次向客户端发送数据。

**实现原理:**
1. 客户端发起SSE连接
2. 服务器开始调用DeepSeek API的stream接口
3. 每收到一个chunk，立即以`data: {json}\n\n`格式发送给客户端
4. 流结束后，发送完成信号

**客户端消费示例（JavaScript）:**
```javascript
const eventSource = new EventSource('/api/v1/chat/stream', {
  method: 'POST',
  body: JSON.stringify({
    content: '你好',
    conversation_id: 12345
  }),
  headers: {
    'Authorization': 'Bearer token',
    'Content-Type': 'application/json'
  }
});

eventSource.onmessage = (event) => {
  const chunk = JSON.parse(event.data);
  console.log(chunk.choices[0].delta.content);
};

eventSource.onerror = () => {
  eventSource.close();
};
```

## 配置和环境变量

**必需配置（.env）:**
```
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE=https://api.deepseek.com
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/db
REDIS_URL=redis://localhost:6379/0
```

## 错误处理

系统使用统一的错误响应格式：

```json
{
  "code": 40010,
  "message": "对话不存在",
  "errors": null,
  "request_id": "uuid"
}
```

**常见错误码:**
- 20001: 认证失败
- 40010: 对话不存在
- 40002: 消息不存在
- 50001: 系统错误

## 性能优化

1. **消息历史管理**: 仅保留最近10条消息用于上下文
2. **数据库索引**: 在常查询字段上建立索引
3. **异步处理**: 所有I/O操作都是异步的
4. **流式响应**: 长响应使用SSE流式处理，避免超时
5. **Token成本控制**: 实时计算和记录成本

## 下一步工作

1. 完成chat_service.py的创建
2. 更新chat.py路由实现
3. 添加认证中间件
4. 配置Redis缓存
5. 添加单元测试
6. 部署到生产环境

