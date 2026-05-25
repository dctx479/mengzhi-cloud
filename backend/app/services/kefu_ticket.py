"""
客服工单服务

功能：
- 工单 CRUD
- 工单消息管理
- 可见性：用户看自己的，Admin看全部

版本: 1.0
更新日期: 2026-05-25
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import (
    KefuTicket, KefuTicketMessage,
    TicketStatus, TicketPriority, TicketCategory
)


class KefuTicketService:
    """客服工单服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_ticket(
        self,
        user_id: int,
        title: str,
        description: str,
        category: TicketCategory = TicketCategory.INQUIRY,
        priority: TicketPriority = TicketPriority.NORMAL,
        emotion: str = None,
        emotion_intensity: int = None,
        intent: str = None,
        user_name: str = None,
    ) -> KefuTicket:
        """创建工单"""
        ticket = KefuTicket(
            ticket_uuid=str(uuid.uuid4()),
            user_id=user_id,
            title=title[:200],
            description=description,
            category=category,
            priority=priority,
            status=TicketStatus.PENDING,
            emotion=emotion,
            emotion_intensity=emotion_intensity,
            intent=intent,
            user_name=user_name,
        )
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        logger.info(f"创建工单: {ticket.ticket_uuid} by user:{user_id}")
        return ticket

    def get_ticket(self, ticket_id: int, user_id: int, role: str = "user") -> Optional[KefuTicket]:
        """获取工单（带权限过滤）"""
        query = self.db.query(KefuTicket).filter(KefuTicket.id == ticket_id)

        if role != "admin":
            # 普通用户只能看自己的
            query = query.filter(KefuTicket.user_id == user_id)

        return query.first()

    def get_ticket_by_uuid(self, ticket_uuid: str, user_id: int, role: str = "user") -> Optional[KefuTicket]:
        """根据 UUID 获取工单"""
        query = self.db.query(KefuTicket).filter(KefuTicket.ticket_uuid == ticket_uuid)

        if role != "admin":
            query = query.filter(KefuTicket.user_id == user_id)

        return query.first()

    def list_tickets(
        self,
        user_id: int,
        role: str = "user",
        status: TicketStatus = None,
        category: TicketCategory = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """列出工单（分页）"""
        query = self.db.query(KefuTicket)

        # 权限过滤
        if role != "admin":
            query = query.filter(KefuTicket.user_id == user_id)

        if status:
            query = query.filter(KefuTicket.status == status)
        if category:
            query = query.filter(KefuTicket.category == category)

        total = query.count()
        items = (
            query.order_by(KefuTicket.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "items": [t.to_dict() for t in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }

    def update_ticket(
        self,
        ticket_id: int,
        user_id: int,
        role: str,
        status: TicketStatus = None,
        priority: TicketPriority = None,
        assigned_to: str = None,
        add_message: str = None,
    ) -> Optional[KefuTicket]:
        """更新工单（状态、优先级、指派）"""
        ticket = self.get_ticket(ticket_id, user_id, role)
        if not ticket:
            return None

        if status:
            ticket.status = status
            if status == TicketStatus.RESOLVED:
                ticket.resolved_at = datetime.utcnow()
            elif status == TicketStatus.CLOSED:
                ticket.closed_at = datetime.utcnow()

        if priority:
            ticket.priority = priority

        if assigned_to:
            ticket.assigned_to = assigned_to

        if add_message:
            msg = KefuTicketMessage(
                ticket_id=ticket.id,
                role="agent",
                content=add_message,
            )
            self.db.add(msg)

        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def add_ticket_message(
        self,
        ticket_id: int,
        user_id: int,
        role: str,  # "user" or "agent"
        content: str,
    ) -> Optional[KefuTicketMessage]:
        """向工单添加消息"""
        # 验证权限
        ticket = self.get_ticket(ticket_id, user_id, role)
        if not ticket:
            return None

        msg = KefuTicketMessage(
            ticket_id=ticket.id,
            role=role,
            content=content,
        )
        self.db.add(msg)
        ticket.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_ticket_messages(self, ticket_id: int, user_id: int, role: str = "user") -> List[Dict]:
        """获取工单消息历史"""
        ticket = self.get_ticket(ticket_id, user_id, role)
        if not ticket:
            return []

        messages = (
            self.db.query(KefuTicketMessage)
            .filter(KefuTicketMessage.ticket_id == ticket.id)
            .order_by(KefuTicketMessage.created_at.asc())
            .all()
        )
        return [m.to_dict() for m in messages]

    def get_stats(self, user_id: int = None, role: str = "user") -> Dict[str, Any]:
        """获取工单统计（Admin 用）"""
        query = self.db.query(KefuTicket)
        if role != "admin" and user_id:
            query = query.filter(KefuTicket.user_id == user_id)

        total = query.count()
        pending = query.filter(KefuTicket.status == TicketStatus.PENDING).count()
        processing = query.filter(KefuTicket.status == TicketStatus.PROCESSING).count()
        resolved = query.filter(KefuTicket.status == TicketStatus.RESOLVED).count()
        closed = query.filter(KefuTicket.status == TicketStatus.CLOSED).count()

        # 按类别统计
        category_stats = {}
        for cat in TicketCategory:
            count = query.filter(KefuTicket.category == cat).count()
            if count > 0:
                category_stats[cat.value] = count

        return {
            "total": total,
            "pending": pending,
            "processing": processing,
            "resolved": resolved,
            "closed": closed,
            "by_category": category_stats,
        }

    def close_ticket(self, ticket_id: int, user_id: int, role: str) -> bool:
        """关闭工单"""
        ticket = self.update_ticket(ticket_id, user_id, role, status=TicketStatus.CLOSED)
        return ticket is not None

    def resolve_ticket(self, ticket_id: int, user_id: int, role: str) -> bool:
        """标记工单为已解决"""
        ticket = self.update_ticket(ticket_id, user_id, role, status=TicketStatus.RESOLVED)
        return ticket is not None