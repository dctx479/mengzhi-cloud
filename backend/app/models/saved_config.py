"""
保存的内容生成配置模型

版本: 1.0
"""

from sqlalchemy import (
    Column, BIGINT, VARCHAR, JSON, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from typing import Dict, Any

from .base import BaseModel, generate_uuid


class SavedConfig(BaseModel):
    __tablename__ = "saved_configs"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    config_uuid = Column(VARCHAR(36), nullable=False, unique=True, index=True, default=generate_uuid)
    user_id = Column(BIGINT, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(VARCHAR(100), nullable=False)
    config = Column(JSON, nullable=False)

    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        UniqueConstraint("config_uuid", name="uk_saved_config_uuid"),
        Index("idx_saved_config_user_id", "user_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.config_uuid,
            "name": self.name,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
