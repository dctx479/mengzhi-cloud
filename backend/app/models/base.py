"""
数据模型基类 - 通用字段和功能

版本: 1.0
更新日期: 2026-01-17
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import BIGINT
from typing import Dict, Any

# 创建基类
Base = declarative_base()


class BaseModel(Base):
    """ORM基类模型 - 包含通用字段和方法"""

    __abstract__ = True

    # 时间戳字段（所有表都有）
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间"
    )
    deleted_at = Column(
        DateTime,
        nullable=True,
        comment="软删除时间"
    )

    def __repr__(self) -> str:
        """字符串表示 - 子类应该重写"""
        return f"<{self.__class__.__name__}(id={getattr(self, 'id', 'N/A')})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 - 子类应该重写"""
        return {
            col.name: getattr(self, col.name)
            for col in self.__table__.columns
        }

    def to_dict_exclude(self, exclude: list = None) -> Dict[str, Any]:
        """转换为字典（排除某些字段）"""
        if exclude is None:
            exclude = []

        result = {}
        for col in self.__table__.columns:
            if col.name not in exclude:
                value = getattr(self, col.name)
                # 处理时间戳
                if isinstance(value, datetime):
                    result[col.name] = value.isoformat()
                else:
                    result[col.name] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建实例"""
        return cls(**data)


def generate_uuid() -> str:
    """生成UUID"""
    return str(uuid.uuid4())
