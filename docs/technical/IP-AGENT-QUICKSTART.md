# IP智能体快速开始指南
## Quick Start Guide for IP Agents

**版本**: v1.0  
**更新日期**: 2026-06-12

---

## 一、环境准备

### 1.1 依赖安装

```bash
# 后端依赖 (已包含在requirements.txt)
pip install fastapi sqlalchemy pydantic

# 开发依赖
pip install pytest pytest-asyncio
```

### 1.2 环境变量

确保 `.env` 文件包含：

```bash
DEEPSEEK_API_KEY=your_deepseek_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

---

## 二、快速测试

### 2.1 运行单元测试

```bash
cd backend
pytest tests/test_ip_agent.py -v
```

**预期输出**:
```
test_ip_agent.py::TestIPRouter::test_route_to_xiaoshu_product_inquiry PASSED
test_ip_agent.py::TestIPRouter::test_route_to_xiaoshang_marketing PASSED
test_ip_agent.py::TestXiaoshuAgent::test_xiaoshu_response_generation PASSED
...
```

### 2.2 启动后端服务

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2.3 测试API端点

**测试1: 自动路由 (产品咨询)**

```bash
curl -X POST "http://localhost:8000/api/v1/ip-chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "推荐一款羊肉",
    "temperature": 0.7
  }'
```

**预期响应** (路由到小数):
```json
{
  "code": 200,
  "data": {
    "content": "咱们草原上的羊肉啊，要是送礼的话...",
    "ip_type": "xiaoshu",
    "ip_name": "小数",
    "tokens": {"input": 150, "output": 200, "total": 350},
    "cost": 0.00175,
    "metadata": {
      "cultural_elements": ["草原", "羊肉"]
    }
  }
}
```

**测试2: 自动路由 (营销咨询)**

```bash
curl -X POST "http://localhost:8000/api/v1/ip-chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "怎么写直播脚本",
    "temperature": 0.7
  }'
```

**预期响应** (路由到小商):
```json
{
  "code": 200,
  "data": {
    "content": "根据我们的分析，羊肉直播脚本需要...",
    "ip_type": "xiaoshang",
    "ip_name": "小商",
    "metadata": {
      "marketing_intents": ["content_creation", "live_streaming"]
    }
  }
}
```

**测试3: 手动指定IP**

```bash
curl -X POST "http://localhost:8000/api/v1/ip-chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "你好",
    "ip_type": "xiaoshang"
  }'
```

**测试4: 流式响应**

```bash
curl -X POST "http://localhost:8000/api/v1/ip-chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "推荐羊肉"
  }'
```

**预期输出** (SSE流):
```
data: {"type": "chunk", "content": "咱们"}
data: {"type": "chunk", "content": "草原上"}
data: {"type": "chunk", "content": "的羊肉"}
...
data: {"type": "done", "ip_type": "xiaoshu", "ip_name": "小数"}
```

**测试5: 查看可用IP列表**

```bash
curl "http://localhost:8000/api/v1/ip-chat/ips"
```

**测试6: 测试路由算法**

```bash
curl -X POST "http://localhost:8000/api/v1/ip-chat/route?content=推荐羊肉"
```

**预期响应**:
```json
{
  "code": 200,
  "data": {
    "content": "推荐羊肉",
    "routed_to": "xiaoshu",
    "explanation": "匹配关键词: 推荐, 羊肉"
  }
}
```

---

## 三、集成到现有系统

### 3.1 注册路由

在 `app/api/v1/__init__.py` 中添加：

```python
from .ip_chat import router as ip_chat_router

# 注册IP对话路由
v1_router.include_router(ip_chat_router)
```

### 3.2 扩展ChatService (可选)

如果要将IP Agent集成到现有 `ChatService`:

```python
# app/services/chat_service.py

from .ip_agent import IPRouter, IPAgentFactory

class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.ip_router = IPRouter()
    
    async def send_message(
        self,
        user_id: int,
        content: str,
        use_ip_agent: bool = True,  # 新增开关
        ...
    ):
        if use_ip_agent:
            # 使用IP Agent
            ip_type = self.ip_router.route(content)
            agent = IPAgentFactory.create_agent(ip_type, self.db)
            response = await agent.generate_response(...)
            return response
        else:
            # 原有通用模式
            ...
```

---

## 四、前端集成示例

### 4.1 API调用封装

```typescript
// frontend/src/api/ipChat.ts

import http from '@/utils/http'

export interface IPChatRequest {
  content: string
  conversation_id?: number
  ip_type?: 'xiaoshu' | 'xiaoshang'
  temperature?: number
}

export interface IPChatResponse {
  content: string
  ip_type: string
  ip_name: string
  conversation_id: number
  tokens: { input: number; output: number; total: number }
  cost: number
  metadata: Record<string, any>
}

/**
 * 发送IP对话消息
 */
export const sendIPMessage = async (request: IPChatRequest): Promise<IPChatResponse> => {
  const res = await http.post<{ code: number; data: IPChatResponse }>('/v1/ip-chat/message', request)
  return (res as any).data
}

/**
 * 获取可用IP列表
 */
export const getAvailableIPs = async () => {
  const res = await http.get<{ code: number; data: Record<string, any> }>('/v1/ip-chat/ips')
  return (res as any).data
}
```

### 4.2 Vue组件示例

```vue
<!-- frontend/src/views/chat/IPChatPage.vue -->

<template>
  <div class="ip-chat-container">
    <!-- IP切换器 -->
    <el-tabs v-model="activeIP" @tab-click="handleIPSwitch">
      <el-tab-pane label="小数 (文化传承)" name="xiaoshu" />
      <el-tab-pane label="小商 (营销顾问)" name="xiaoshang" />
      <el-tab-pane label="自动识别" name="auto" />
    </el-tabs>

    <!-- 对话区域 -->
    <div class="chat-messages">
      <div v-for="msg in messages" :key="msg.id" :class="['message', msg.role]">
        <div class="message-header">
          <span class="ip-badge" v-if="msg.ip_type">{{ msg.ip_name }}</span>
          <span class="time">{{ msg.time }}</span>
        </div>
        <div class="message-content">{{ msg.content }}</div>
      </div>
    </div>

    <!-- 输入框 -->
    <div class="input-area">
      <el-input
        v-model="userInput"
        placeholder="输入消息..."
        @keyup.enter="sendMessage"
      />
      <el-button type="primary" @click="sendMessage">发送</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { sendIPMessage } from '@/api/ipChat'

const activeIP = ref('auto')
const userInput = ref('')
const messages = ref<any[]>([])

const sendMessage = async () => {
  if (!userInput.value.trim()) return

  // 添加用户消息
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: userInput.value,
    time: new Date().toLocaleTimeString()
  })

  const content = userInput.value
  userInput.value = ''

  try {
    // 调用API
    const response = await sendIPMessage({
      content,
      ip_type: activeIP.value === 'auto' ? undefined : activeIP.value
    })

    // 添加AI响应
    messages.value.push({
      id: Date.now(),
      role: 'assistant',
      content: response.content,
      ip_type: response.ip_type,
      ip_name: response.ip_name,
      time: new Date().toLocaleTimeString()
    })
  } catch (error) {
    console.error('发送消息失败:', error)
  }
}

const handleIPSwitch = (tab: any) => {
  console.log('切换到IP:', tab.name)
}
</script>

<style scoped>
.ip-chat-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.chat-messages {
  height: 500px;
  overflow-y: auto;
  border: 1px solid #eee;
  padding: 20px;
  margin: 20px 0;
}

.message {
  margin-bottom: 20px;
}

.message-header {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
}

.ip-badge {
  background: #409eff;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-right: 10px;
}

.input-area {
  display: flex;
  gap: 10px;
}
</style>
```

---

## 五、开发调试

### 5.1 查看日志

```bash
# 查看IP路由日志
tail -f logs/app.log | grep IPRouter

# 查看Agent执行日志
tail -f logs/app.log | grep "xiaoshu\|xiaoshang"
```

### 5.2 调试技巧

**技巧1: 测试路由算法**

```python
# 在Python REPL中测试
from app.services.ip_agent import IPRouter

router = IPRouter()
print(router.route("推荐羊肉"))  # 应输出: IPType.XIAOSHU
print(router.route("直播脚本"))  # 应输出: IPType.XIAOSHANG
```

**技巧2: 单独测试Agent**

```python
from app.services.ip_agent import XiaoshuAgent
from unittest.mock import Mock

db = Mock()
llm_client = Mock()
agent = XiaoshuAgent(db, llm_client)

# 查看系统提示词
print(agent._get_system_prompt())

# 查看示例
print(agent._get_few_shot_examples())
```

---

## 六、常见问题

### Q1: IP路由不准确怎么办？

**解决方案**:
1. 检查 `ip_router.py` 中的 `INTENT_KEYWORDS` 是否覆盖足够多的关键词
2. 调整关键词权重或添加新的关键词
3. 使用 `/route` 端点测试特定消息的路由结果

### Q2: Agent响应质量不佳？

**解决方案**:
1. 调整 `_get_system_prompt()` 中的人设描述
2. 增加或优化 `_get_few_shot_examples()` 示例
3. 调整 `temperature` 参数 (0.7 → 0.5 更保守)

### Q3: 如何添加新的IP？

**步骤**:
1. 在 `services/ip_agent/` 下创建新文件 (如 `xiaoyi_agent.py`)
2. 继承 `BaseIPAgent` 并实现 `_get_system_prompt()` 和 `_get_few_shot_examples()`
3. 在 `ip_router.py` 的 `IPType` 枚举中添加新类型
4. 在 `IPRouter.INTENT_KEYWORDS` 中添加关键词映射
5. 在 `IPAgentFactory.create_agent()` 中添加创建逻辑

### Q4: 如何监控IP使用情况？

**方案**:
1. 在 `conversations.metadata_info` 中记录 `ip_type`
2. 使用SQL查询统计:
   ```sql
   SELECT 
     metadata_info->>'ip_type' as ip_type,
     COUNT(*) as usage_count
   FROM conversations
   WHERE metadata_info->>'ip_type' IS NOT NULL
   GROUP BY metadata_info->>'ip_type';
   ```

---

## 七、下一步

- [ ] 完善Few-shot示例 (每个IP至少5个高质量示例)
- [ ] 集成RAG知识库 (产品知识、文化故事)
- [ ] 添加情绪识别 (根据用户情绪调整回复风格)
- [ ] 实现缓存机制 (相似问题缓存回答)
- [ ] 前端流式渲染优化
- [ ] A/B测试不同Prompt版本
- [ ] 监控Dashboard (路由准确率、响应质量)

---

**快速开始指南完成 | 版本 v1.0**
