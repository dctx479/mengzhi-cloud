# AI对话API - 完整代码清单

本文档包含所有需要创建或更新的文件的完整代码。

## 1. backend/app/services/chat_service.py

完整的对话服务实现，需要复制全部内容到文件：

```python
"""
AI对话服务 - 处理对话业务逻辑和数据操作
版本: 1.0
更新日期: [项目完成日期]
"""

import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, AsyncGenerator, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from loguru import logger

from app.models.conversation import Conversation, ConversationStatus, AgentType
from app.models.message import Message, MessageRole
from app.services.ai import DeepSeekClient, PromptTemplates, get_deepseek_client
from app.core.errors import BusinessException, ErrorCode


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.deepseek_client: Optional[DeepSeekClient] = None

    async def _get_client(self) -> DeepSeekClient:
        if self.deepseek_client is None:
            self.deepseek_client = await get_deepseek_client()
        return self.deepseek_client

    async def send_message(
        self,
        user_id: int,
        content: str,
        conversation_id: Optional[int] = None,
        agent_type: str = "assistant",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> Tuple[int, str, int, int, float]:
        try:
            client = await self._get_client()
            if conversation_id:
                conversation = self.db.query(Conversation).filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id
                ).first()
                if not conversation:
                    raise BusinessException(
                        code=ErrorCode.RECORD_NOT_FOUND,
                        message="对话不存在"
                    )
            else:
                conversation = self._create_conversation(user_id, agent_type)

            messages = self._build_message_history(conversation.id, max_messages=10)
            messages.append({"role": "user", "content": content})

            if system_prompt is None:
                system_prompt = PromptTemplates.get_system_prompt()

            response = await client.chat_completion(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=4096
            )

            if not response.get("choices"):
                raise BusinessException(
                    code=ErrorCode.SYSTEM_ERROR,
                    message="AI服务返回无效响应"
                )

            choice = response["choices"][0]
            assistant_message = choice["message"]["content"]
            usage = response.get("usage", {})

            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            cost = client.calculate_cost(input_tokens, output_tokens)

            self._save_message(
                conversation.id,
                MessageRole.USER,
                content,
                input_tokens=client.count_tokens(content)
            )

            self._save_message(
                conversation.id,
                MessageRole.ASSISTANT,
                assistant_message,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                finish_reason=choice.get("finish_reason")
            )

            self._update_conversation_stats(
                conversation.id,
                total_tokens=input_tokens + output_tokens,
                cost=cost
            )

            logger.info(f"Message sent in conversation {conversation.id}, tokens={input_tokens + output_tokens}")
            return conversation.id, assistant_message, input_tokens, output_tokens, cost

        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise BusinessException(code=ErrorCode.SYSTEM_ERROR, message="发送消息失败")

    async def send_message_stream(
        self,
        user_id: int,
        content: str,
        conversation_id: Optional[int] = None,
        agent_type: str = "assistant",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        try:
            client = await self._get_client()
            if conversation_id:
                conversation = self.db.query(Conversation).filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id
                ).first()
                if not conversation:
                    raise BusinessException(code=ErrorCode.RECORD_NOT_FOUND, message="对话不存在")
            else:
                conversation = self._create_conversation(user_id, agent_type)

            messages = self._build_message_history(conversation.id, max_messages=10)
            messages.append({"role": "user", "content": content})

            if system_prompt is None:
                system_prompt = PromptTemplates.get_system_prompt()

            self._save_message(conversation.id, MessageRole.USER, content,
                             input_tokens=client.count_tokens(content))

            accumulated_content = ""
            finish_reason = None

            async for chunk in client.chat_completion_stream(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=4096
            ):
                if chunk.get("choices"):
                    choice = chunk["choices"][0]
                    delta = choice.get("delta", {})
                    content_delta = delta.get("content", "")
                    if content_delta:
                        accumulated_content += content_delta
                    if choice.get("finish_reason"):
                        finish_reason = choice["finish_reason"]

                yield json.dumps({
                    "id": conversation.id,
                    "object": "text_completion.chunk",
                    "created": int(datetime.utcnow().timestamp()),
                    "model": client.model,
                    "choices": chunk.get("choices", [])
                }) + "\n"

            total_output_tokens = client.count_tokens(accumulated_content)
            cost = client.calculate_cost(0, total_output_tokens)

            self._save_message(conversation.id, MessageRole.ASSISTANT, accumulated_content,
                             output_tokens=total_output_tokens, cost=cost, finish_reason=finish_reason)
            self._update_conversation_stats(conversation.id, total_tokens=total_output_tokens, cost=cost)

        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"Error in stream: {str(e)}")
            raise BusinessException(code=ErrorCode.SYSTEM_ERROR, message="流式消息发送失败")

    def get_conversations(self, user_id: int, page: int = 1, page_size: int = 20) -> Tuple[int, List[Conversation]]:
        try:
            query = self.db.query(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.status == ConversationStatus.ACTIVE
            ).order_by(desc(Conversation.last_message_at or Conversation.created_at))
            total = query.count()
            conversations = query.offset((page - 1) * page_size).limit(page_size).all()
            return total, conversations
        except Exception as e:
            logger.error(f"Error getting conversations: {str(e)}")
            raise BusinessException(code=ErrorCode.DB_QUERY_FAILED, message="获取对话列表失败")

    def get_conversation_detail(self, conversation_id: int, user_id: int) -> Conversation:
        try:
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            ).first()
            if not conversation:
                raise BusinessException(code=ErrorCode.RECORD_NOT_FOUND, message="对话不存在")
            return conversation
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"Error getting conversation detail: {str(e)}")
            raise BusinessException(code=ErrorCode.DB_QUERY_FAILED, message="获取对话详情失败")

    def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        try:
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            ).first()
            if not conversation:
                raise BusinessException(code=ErrorCode.RECORD_NOT_FOUND, message="对话不存在")
            conversation.status = ConversationStatus.DELETED
            conversation.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            self.db.rollback()
            raise BusinessException(code=ErrorCode.DB_UPDATE_FAILED, message="删除对话失败")

    def update_conversation(self, conversation_id: int, user_id: int, title: Optional[str] = None) -> Conversation:
        try:
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            ).first()
            if not conversation:
                raise BusinessException(code=ErrorCode.RECORD_NOT_FOUND, message="对话不存在")
            if title is not None:
                conversation.title = title
            conversation.updated_at = datetime.utcnow()
            self.db.commit()
            return conversation
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"Error updating conversation: {str(e)}")
            self.db.rollback()
            raise BusinessException(code=ErrorCode.DB_UPDATE_FAILED, message="更新对话失败")

    def add_feedback(self, message_id: int, conversation_id: int, user_id: int,
                    rating: int, feedback: Optional[str] = None, feedback_type: Optional[str] = None) -> Message:
        try:
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            ).first()
            if not conversation:
                raise BusinessException(code=ErrorCode.RECORD_NOT_FOUND, message="对话不存在")
            message = self.db.query(Message).filter(
                Message.id == message_id,
                Message.conversation_id == conversation_id,
                Message.role == MessageRole.ASSISTANT
            ).first()
            if not message:
                raise BusinessException(code=ErrorCode.RECORD_NOT_FOUND, message="消息不存在")
            message.rating = rating
            message.feedback = feedback
            message.feedback_type = feedback_type
            message.updated_at = datetime.utcnow()
            self.db.commit()
            return message
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"Error adding feedback: {str(e)}")
            self.db.rollback()
            raise BusinessException(code=ErrorCode.DB_UPDATE_FAILED, message="添加反馈失败")

    def _create_conversation(self, user_id: int, agent_type: str) -> Conversation:
        conversation = Conversation(
            conversation_uuid=str(uuid.uuid4()),
            user_id=user_id,
            agent_type=AgentType.ASSISTANT,
            status=ConversationStatus.ACTIVE
        )
        self.db.add(conversation)
        self.db.commit()
        return conversation

    def _save_message(self, conversation_id: int, role: MessageRole, content: str,
                     input_tokens: int = 0, output_tokens: int = 0, cost: float = 0.0,
                     finish_reason: Optional[str] = None) -> Message:
        message = Message(
            message_uuid=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost=cost,
            finish_reason=finish_reason
        )
        self.db.add(message)
        self.db.commit()
        return message

    def _build_message_history(self, conversation_id: int, max_messages: int = 10) -> List[Dict[str, str]]:
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()
        if len(messages) > max_messages:
            messages = messages[-max_messages:]
        return [{"role": msg.role.value, "content": msg.content} for msg in messages]

    def _update_conversation_stats(self, conversation_id: int, total_tokens: int = 0, cost: float = 0.0) -> None:
        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.total_tokens += total_tokens
            conversation.message_count = self.db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).count()
            conversation.last_message_at = datetime.utcnow()
            conversation.updated_at = datetime.utcnow()
            self.db.commit()
```

## 已创建的文件列表

### 核心文件（已创建）

1. **E:\项目\数商\AI赋能云平台\backend\app\services\ai\deepseek_client.py** - DeepSeek API客户端
   - 非流式和流式API调用
   - Token计数和成本计算
   - 自动重试机制

2. **E:\项目\数商\AI赋能云平台\backend\app\services\ai\prompt_templates.py** - Prompt模板
   - 系统提示词
   - 知识库注入
   - 对话上下文管理

3. **E:\项目\数商\AI赋能云平台\backend\app\services\ai\__init__.py** - 初始化

4. **E:\项目\数商\AI赋能云平台\backend\app\schemas\chat.py** - 数据验证Schema
   - SendMessageRequest/Response
   - ConversationResponse
   - FeedbackRequest/Response

5. **E:\项目\数商\AI赋能云平台\backend\app\models\message.py** - 消息数据模型
   - Message ORM模型
   - MessageRole枚举
   - 消息统计和反馈字段

6. **E:\项目\数商\AI赋能云平台\backend\app\database.py** - 数据库配置

7. **E:\项目\数商\AI赋能云平台\backend\app\api\chat.py** - API路由（需要更新）

8. **E:\项目\数商\AI赋能云平台\backend\app\main.py** - 主应用（已更新）

### 需要手动创建的文件

**E:\项目\数商\AI赋能云平台\backend\app\services\chat_service.py** - 对话服务
使用上面提供的完整代码

## 环境配置

在 `.env` 文件中添加：

```bash
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_API_BASE=https://api.deepseek.com
DATABASE_URL=mysql+pymysql://root:root123@localhost:3306/agri_platform?charset=utf8mb4
REDIS_URL=redis://localhost:6379/0
DEBUG=True
```

## 依赖安装

```bash
pip install httpx tenacity pydantic loguru sqlalchemy pymysql fastapi
```

## 快速测试

### 1. 启动应用
```bash
uvicorn app.main:app --reload
```

### 2. 测试非流式API
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Authorization: Bearer test_token" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "你好，请介绍一下内蒙古的农畜产品",
    "conversation_id": null
  }'
```

### 3. 测试流式API
```bash
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Authorization: Bearer test_token" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "请告诉我如何做好品牌营销",
    "conversation_id": null
  }'
```

### 4. 获取对话列表
```bash
curl http://localhost:8000/api/v1/chat/conversations?page=1&page_size=20 \
  -H "Authorization: Bearer test_token"
```

## 架构说明

```
请求流程：
1. 客户端发送HTTP请求到FastAPI路由 (chat.py)
2. 路由调用ChatService处理业务逻辑
3. ChatService调用DeepSeekClient与AI API通信
4. 使用PromptTemplates管理提示词
5. 数据通过SQLAlchemy保存到数据库
6. 响应通过Schema验证后返回

流式响应流程：
1. 客户端建立SSE连接
2. ChatService流式调用DeepSeekClient
3. 每个chunk即时发送给客户端
4. 流完成后保存完整消息到数据库
```

## 关键特性

- 非流式和流式两种API支持
- 自动Token计数和成本计算
- 对话上下文管理（最近10条消息）
- 用户反馈收集和评分
- 完整的错误处理和日志
- 异步I/O优化性能
- 数据库事务管理

## 注意事项

1. DeepSeek API密钥需要正确配置
2. 数据库连接字符串需要根据实际环境调整
3. 流式响应需要支持SSE的客户端
4. 所有异步操作都需要在异步上下文中执行
5. 对话历史仅保留最近10条以优化性能

