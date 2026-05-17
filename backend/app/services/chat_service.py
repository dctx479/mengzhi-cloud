"""
Chat Service - 对话服务层
"""
from typing import Tuple, List, Optional, Dict, Any, AsyncGenerator
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from datetime import datetime, date
from loguru import logger

from app.models.conversation import Conversation, ConversationStatus, AgentType
from app.models.message import Message, MessageRole
from app.models.user_quota import UserQuota, QuotaType
from app.services.ai.deepseek_client import get_deepseek_client
from app.core.errors import BusinessException

# 历史消息截断：最多保留最近 N 条消息，防止 token 超限
MAX_HISTORY_MESSAGES = 20


class ChatService:
    """对话服务"""

    def __init__(self, db: Session):
        self.db = db

    async def send_message(
        self,
        user_id: int,
        content: str,
        conversation_id: Optional[int] = None,
        temperature: float = 0.7
    ) -> Tuple[int, str, int, int, float]:
        """发送消息（非流式）"""
        # 检查配额
        quota = self._get_or_create_quota(user_id)
        if not quota.can_chat():
            raise BusinessException("对话次数已用完")

        # 获取或创建对话
        conv = self._get_or_create_conversation(user_id, conversation_id)

        # 保存用户消息
        user_msg = Message(
            conversation_id=conv.id,
            role=MessageRole.USER,
            content=content,
            model=conv.model
        )
        self.db.add(user_msg)
        self.db.flush()  # flush 而非 commit，保持事务完整性

        # 构建历史消息
        history = self._build_message_history(conv.id)

        # 调用AI（失败时整个事务回滚，用户消息不会孤立存在）
        try:
            client = await get_deepseek_client()
            response = await client.chat_completion(
                messages=history,
                system_prompt=self._get_system_prompt(conv.agent_type),
                temperature=temperature,
                max_tokens=conv.max_tokens
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"AI call failed, transaction rolled back: {str(e)}")
            raise BusinessException(f"AI服务调用失败: {str(e)}")

        # 解析响应
        choice = response["choices"][0]
        assistant_content = choice["message"]["content"]
        usage = response["usage"]
        input_tokens = usage["prompt_tokens"]
        output_tokens = usage["completion_tokens"]
        total_tokens = usage["total_tokens"]
        cost = client.calculate_cost(input_tokens, output_tokens)

        # 保存助手消息
        assistant_msg = Message(
            conversation_id=conv.id,
            role=MessageRole.ASSISTANT,
            content=assistant_content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost=cost,
            model=conv.model,
            finish_reason=choice.get("finish_reason")
        )
        self.db.add(assistant_msg)

        # 更新对话统计
        conv.message_count = (conv.message_count or 0) + 2
        conv.total_tokens = (conv.total_tokens or 0) + total_tokens
        conv.total_cost = (conv.total_cost or 0) + cost

        # 更新配额（先用后扣，AI 成功才扣减）
        quota.increment_chat_usage()
        quota.increment_token_usage(total_tokens)

        self.db.commit()

        return (conv.id, assistant_content, input_tokens, output_tokens, cost)

    async def send_message_stream(
        self,
        user_id: int,
        content: str,
        conversation_id: Optional[int] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """发送消息（流式）"""
        # 检查配额
        quota = self._get_or_create_quota(user_id)
        if not quota.can_chat():
            raise BusinessException("对话次数已用完")

        # 获取或创建对话
        conv = self._get_or_create_conversation(user_id, conversation_id)

        # 保存用户消息（flush 不 commit，保持事务）
        user_msg = Message(
            conversation_id=conv.id,
            role=MessageRole.USER,
            content=content,
            model=conv.model
        )
        self.db.add(user_msg)
        self.db.flush()

        # 构建历史消息
        history = self._build_message_history(conv.id)

        # 调用AI流式接口
        client = await get_deepseek_client()
        full_content = ""
        input_tokens = 0
        output_tokens = 0
        stream_error: Optional[Exception] = None

        try:
            async for chunk in client.chat_completion_stream(
                messages=history,
                system_prompt=self._get_system_prompt(conv.agent_type),
                temperature=temperature,
                max_tokens=conv.max_tokens
            ):
                if "choices" in chunk and len(chunk["choices"]) > 0:
                    delta = chunk["choices"][0].get("delta", {})
                    content_chunk = delta.get("content", "")
                    if content_chunk:
                        full_content += content_chunk
                        yield content_chunk

                    # 最后一个chunk包含usage信息
                    if "usage" in chunk:
                        usage = chunk["usage"]
                        input_tokens = usage.get("prompt_tokens", 0)
                        output_tokens = usage.get("completion_tokens", 0)
        except Exception as e:
            stream_error = e
            logger.error(f"Stream AI call failed: {str(e)}")

        if stream_error is not None:
            # 流中途失败：回滚事务，不保存任何消息
            self.db.rollback()
            raise BusinessException(f"AI流式服务调用失败: {str(stream_error)}")

        # 保存助手消息（AI 成功完成后才持久化）
        total_tokens = input_tokens + output_tokens
        cost = client.calculate_cost(input_tokens, output_tokens)

        assistant_msg = Message(
            conversation_id=conv.id,
            role=MessageRole.ASSISTANT,
            content=full_content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost=cost,
            model=conv.model,
            finish_reason="stop"
        )
        self.db.add(assistant_msg)

        # 更新对话统计
        conv.message_count = (conv.message_count or 0) + 2
        conv.total_tokens = (conv.total_tokens or 0) + total_tokens
        conv.total_cost = (conv.total_cost or 0) + cost

        # 更新配额（AI 成功才扣减）
        quota.increment_chat_usage()
        quota.increment_token_usage(total_tokens)

        self.db.commit()

    def get_conversations(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: str = "active"
    ) -> Tuple[int, List[Conversation]]:
        """获取对话列表"""
        query = self.db.query(Conversation).filter(
            Conversation.user_id == user_id
        )

        if status:
            try:
                query = query.filter(Conversation.status == ConversationStatus(status))
            except ValueError:
                # 非法 status 值忽略过滤，返回全部
                logger.warning(f"Invalid conversation status filter: {status!r}, ignoring")

        total = query.count()
        conversations = query.order_by(desc(Conversation.updated_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return (total, [conv for conv in conversations])

    def get_conversation_detail(
        self,
        conversation_id: str,
        user_id: int
    ) -> Conversation:
        """获取对话详情"""
        # 修复 N+1 查询：预加载消息关系
        conv = self.db.query(Conversation).options(
            joinedload(Conversation.messages)
        ).filter(
            Conversation.conversation_uuid == conversation_id,
            Conversation.user_id == user_id
        ).first()

        if not conv:
            raise BusinessException("对话不存在")

        return conv

    def delete_conversation(
        self,
        conversation_id: str,
        user_id: int
    ) -> None:
        """删除对话"""
        conv = self.db.query(Conversation).filter(
            Conversation.conversation_uuid == conversation_id,
            Conversation.user_id == user_id
        ).first()

        if not conv:
            raise BusinessException("对话不存在")

        conv.soft_delete()
        self.db.commit()

    def update_conversation(
        self,
        conversation_id: str,
        user_id: int,
        title: Optional[str] = None,
        is_favorited: Optional[bool] = None
    ) -> Dict[str, Any]:
        """更新对话"""
        conv = self.db.query(Conversation).filter(
            Conversation.conversation_uuid == conversation_id,
            Conversation.user_id == user_id
        ).first()

        if not conv:
            raise BusinessException("对话不存在")

        if title:
            conv.title = title
        if is_favorited is not None:
            conv.metadata_info = conv.metadata_info or {}
            conv.metadata_info["is_favorited"] = is_favorited

        self.db.commit()
        return conv.to_dict()

    def add_feedback(
        self,
        message_id: int,
        conversation_id: int,
        user_id: int,
        rating: int,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """添加反馈"""
        msg = self.db.query(Message).join(Conversation).filter(
            Message.id == message_id,
            Message.conversation_id == conversation_id,
            Conversation.user_id == user_id
        ).first()

        if not msg:
            raise BusinessException("消息不存在")

        msg.rating = rating
        msg.feedback = feedback
        if rating >= 4:
            msg.feedback_type = "helpful"
        elif rating <= 2:
            msg.feedback_type = "unhelpful"

        self.db.commit()
        return msg.to_dict()

    def _get_or_create_quota(self, user_id: int) -> UserQuota:
        """获取或创建用户配额"""
        today = date.today()
        quota = self.db.query(UserQuota).filter(
            UserQuota.user_id == user_id,
            UserQuota.quota_type == QuotaType.DAILY,
            UserQuota.period_start <= today,
            UserQuota.period_end >= today
        ).first()

        if not quota:
            quota = UserQuota.create_daily_quota(user_id, today)
            self.db.add(quota)
            self.db.commit()

        return quota

    def _get_or_create_conversation(self, user_id: int, conversation_id: Optional[int]) -> Conversation:
        """获取或创建对话"""
        if conversation_id:
            conv = self.db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            ).first()
            if not conv:
                raise BusinessException("对话不存在")
            return conv

        conv = Conversation(
            user_id=user_id,
            title="新对话",
            agent_type=AgentType.GENERAL,
            status=ConversationStatus.ACTIVE
        )
        self.db.add(conv)
        self.db.commit()
        return conv

    def _build_message_history(self, conversation_id: int) -> List[Dict[str, str]]:
        """构建消息历史（截断到最近 MAX_HISTORY_MESSAGES 条，防止 token 超限）"""
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()

        # 截断：保留最近 N 条，确保上下文不超限
        if len(messages) > MAX_HISTORY_MESSAGES:
            messages = messages[-MAX_HISTORY_MESSAGES:]

        return [{"role": msg.role.value, "content": msg.content} for msg in messages]

    def _get_system_prompt(self, agent_type: AgentType) -> str:
        """获取系统提示词"""
        prompts = {
            AgentType.MARKETING: "你是一位专业的营销顾问，擅长市场分析和营销策略。",
            AgentType.CULTURAL: "你是一位文化专家，精通传统文化和现代文化融合。",
            AgentType.DATA: "你是一位数据分析师，擅长数据分析和可视化。",
            AgentType.GENERAL: "你是一位智能助手，可以帮助用户解决各种问题。"
        }
        return prompts.get(agent_type, prompts[AgentType.GENERAL])
