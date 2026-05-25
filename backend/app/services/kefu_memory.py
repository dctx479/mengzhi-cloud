"""
客服对话记忆管理

功能：
- 内存中的 Session 窗口记忆
- 持久化到数据库 (kefu_conversations / kefu_messages)

版本: 1.0
更新日期: 2026-05-25
"""

from typing import Optional, List, Dict, Any
from collections import deque
from datetime import datetime, timedelta
from loguru import logger

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import KefuConversation, KefuMessage, KefuConversationStatus


class SimpleMemory:
    """简单内存记忆窗口"""

    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self._buffer: deque = deque(maxlen=window_size)

    def add(self, role: str, content: str):
        self._buffer.append({"role": role, "content": content})

    def get_messages(self) -> List[Dict[str, str]]:
        return list(self._buffer)

    def clear(self):
        self._buffer.clear()


class KefuMemory:
    """客服对话记忆管理器"""

    def __init__(self, db: Session, window_size: int = 5, timeout_minutes: int = 30):
        self.db = db
        self.window_size = window_size
        self.timeout_minutes = timeout_minutes
        self._memory_cache: Dict[str, SimpleMemory] = {}

    def _get_memory(self, session_id: str) -> SimpleMemory:
        """获取或创建内存记忆"""
        if session_id not in self._memory_cache:
            self._memory_cache[session_id] = SimpleMemory(self.window_size)
        return self._memory_cache[session_id]

    def save_message(
        self,
        session_id: str,
        user_id: int,
        role: str,
        content: str,
        emotion: str = None,
        intent: str = None,
        confidence: int = None,
        action: str = None,
        user_name: str = None,
        title: str = None,
    ):
        """保存消息到内存和数据库"""
        # 更新内存
        mem = self._get_memory(session_id)
        mem.add(role, content)

        # 持久化到数据库
        try:
            # 查找或创建会话
            conv = self.db.query(KefuConversation).filter(
                KefuConversation.session_id == session_id
            ).first()

            if not conv:
                conv = KefuConversation(
                    session_id=session_id,
                    user_id=user_id,
                    user_name=user_name or "",
                    title=title or "新会话",
                    status=KefuConversationStatus.ACTIVE,
                )
                self.db.add(conv)
                self.db.flush()

            # 保存消息
            msg = KefuMessage(
                conversation_id=conv.id,
                role=role,
                content=content,
                emotion=emotion,
                intent=intent,
                confidence=confidence,
                action=action,
            )
            self.db.add(msg)

            # 更新会话统计
            conv.message_count += 1
            if emotion:
                conv.emotion_type = emotion
            if intent:
                conv.intent_type = intent

            self.db.commit()
        except Exception as e:
            logger.error(f"保存客服消息失败: {e}")
            self.db.rollback()

    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """从数据库获取会话历史"""
        try:
            conv = self.db.query(KefuConversation).filter(
                KefuConversation.session_id == session_id
            ).first()

            if not conv:
                return []

            messages = (
                self.db.query(KefuMessage)
                .filter(KefuMessage.conversation_id == conv.id)
                .order_by(KefuMessage.created_at.desc())
                .limit(limit)
                .all()
            )

            return [m.to_dict() for m in reversed(messages)]
        except Exception as e:
            logger.error(f"获取会话历史失败: {e}")
            return []

    def get_or_create_conversation(
        self,
        session_id: str,
        user_id: int,
        user_name: str = None,
    ) -> KefuConversation:
        """获取或创建会话"""
        conv = self.db.query(KefuConversation).filter(
            KefuConversation.session_id == session_id
        ).first()

        if not conv:
            conv = KefuConversation(
                session_id=session_id,
                user_id=user_id,
                user_name=user_name or "",
                title="新会话",
                status=KefuConversationStatus.ACTIVE,
            )
            self.db.add(conv)
            self.db.commit()
            self.db.refresh(conv)

        return conv

    def list_user_conversations(
        self,
        user_id: int,
        limit: int = 20,
        include_deleted: bool = False
    ) -> List[KefuConversation]:
        """列出用户的所有会话"""
        query = self.db.query(KefuConversation).filter(
            KefuConversation.user_id == user_id
        )

        if not include_deleted:
            query = query.filter(
                KefuConversation.status != KefuConversationStatus.DELETED
            )

        return query.order_by(KefuConversation.updated_at.desc()).limit(limit).all()

    def delete_conversation(self, session_id: str) -> bool:
        """软删除会话"""
        try:
            conv = self.db.query(KefuConversation).filter(
                KefuConversation.session_id == session_id
            ).first()

            if conv:
                conv.status = KefuConversationStatus.DELETED
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False

    def clear_memory(self, session_id: str):
        """清理内存缓存"""
        if session_id in self._memory_cache:
            del self._memory_cache[session_id]