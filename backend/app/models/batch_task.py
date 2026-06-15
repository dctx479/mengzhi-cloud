"""
批量内容生成任务模型

记录一次批量内容生成任务的配置快照、进度与结果。
状态机：pending → running → completed / failed / cancelled

版本: 1.0
创建日期: 2026-06-14
"""

from sqlalchemy import (
    Column, BIGINT, BigInteger, Integer, VARCHAR, Text, JSON, DateTime,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from typing import Dict, Any

from .base import BaseModel, generate_uuid


class BatchTask(BaseModel):
    __tablename__ = "batch_tasks"

    # SQLite BIGINT autoincrement does not auto-inc (only INTEGER PRIMARY KEY).
    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    task_uuid = Column(VARCHAR(36), nullable=False, unique=True, index=True, default=generate_uuid)
    user_id = Column(BIGINT, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(VARCHAR(200), nullable=False)
    template_id = Column(VARCHAR(36), nullable=True)
    template_name = Column(VARCHAR(200), nullable=True)

    # GenerationConfig 快照
    config = Column(JSON, nullable=False)

    total_count = Column(Integer, nullable=False, default=0)
    completed_count = Column(Integer, nullable=False, default=0)
    progress = Column(Integer, nullable=False, default=0)

    # pending / running / completed / failed / cancelled（对齐前端 TaskStatus）
    status = Column(VARCHAR(20), nullable=False, default="pending")

    results = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    retry_count = Column(Integer, nullable=False, default=0)
    last_heartbeat_at = Column(DateTime, nullable=True)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        UniqueConstraint("task_uuid", name="uk_batch_task_uuid"),
        Index("idx_batch_tasks_user_id", "user_id"),
        Index("idx_batch_tasks_status", "status"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """对齐前端 BatchTask 接口（types/content-generation.ts）"""
        return {
            "id": self.task_uuid,
            "name": self.name,
            "template": self.template_name or "",
            "template_id": self.template_id or "",
            "count": self.total_count,
            "progress": self.progress,
            "status": self.status,
            "results": self.results or [],
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
