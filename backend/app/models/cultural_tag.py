"""
文化标签数据模型 - SQLAlchemy ORM

包含：
- 文化标签基本信息
- 标签分类体系
- 标签层级关系（可选）
- 使用统计信息
- 产品关联关系

版本: 1.0
更新日期: 2026-01-17
"""

from sqlalchemy import (
    Column, BIGINT, VARCHAR, TEXT, Integer, Boolean, TIMESTAMP,
    ForeignKey, Table, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List, Dict, Any

from .base import BaseModel


# 产品-标签关联表（多对多关系）
product_tags = Table(
    'product_tags',
    BaseModel.metadata,
    Column('product_id', BIGINT, ForeignKey('products.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', BIGINT, ForeignKey('cultural_tags.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', TIMESTAMP, default=datetime.utcnow, nullable=False, comment="关联创建时间"),
    Index('idx_product_tags_product_id', 'product_id'),
    Index('idx_product_tags_tag_id', 'tag_id'),
)


class CulturalTag(BaseModel):
    """文化标签模型

    文化标签用于标注内蒙古农畜产品的文化属性，包括：
    - 地理标志（锡林郭勒羊肉、科尔沁牛肉等）
    - 民族文化（蒙古族传统、游牧文化等）
    - 历史传承（马背民族、草原文化等）
    - 工艺特色（传统奶制品工艺、风干肉制作等）
    - 节日习俗（那达慕、祭敖包等）
    - 营养价值（高蛋白、富含微量元素等）
    - 文化故事（产品背后的故事和传说）
    """

    __tablename__ = "cultural_tags"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="标签ID"
    )

    # 标签基本信息
    name = Column(
        VARCHAR(50),
        nullable=False,
        unique=True,
        index=True,
        comment="标签名称"
    )
    category = Column(
        VARCHAR(30),
        nullable=False,
        index=True,
        comment="标签分类：geo/ethnicity/history/craft/festival/nutrition/story"
    )
    description = Column(
        TEXT,
        nullable=True,
        comment="标签详细描述"
    )
    keywords = Column(
        VARCHAR(200),
        nullable=True,
        comment="关键词（逗号分隔，用于搜索和推荐）"
    )

    # 层级关系（可选，支持标签树形结构）
    parent_id = Column(
        BIGINT,
        ForeignKey('cultural_tags.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="父标签ID"
    )

    # 统计信息
    usage_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="使用次数（有多少个产品使用了此标签）"
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="是否启用"
    )

    # 关系定义
    parent = relationship(
        "CulturalTag",
        remote_side=[id],
        back_populates="children",
        foreign_keys=[parent_id]
    )
    children = relationship(
        "CulturalTag",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    products = relationship(
        "Product",
        secondary=product_tags,
        back_populates="tags"
    )

    # 索引和约束
    __table_args__ = (
        UniqueConstraint("name", name="uk_cultural_tag_name"),
        Index("idx_cultural_tag_name", "name"),
        Index("idx_cultural_tag_category", "category"),
        Index("idx_cultural_tag_parent_id", "parent_id"),
        Index("idx_cultural_tag_is_active", "is_active"),
        Index("idx_cultural_tag_usage_count", "usage_count"),
        Index("idx_cultural_tag_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<CulturalTag(id={self.id}, name={self.name}, category={self.category})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "keywords": self.keywords,
            "parent_id": self.parent_id,
            "usage_count": self.usage_count,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def increment_usage(self) -> None:
        """增加使用次数"""
        self.usage_count += 1

    def decrement_usage(self) -> None:
        """减少使用次数"""
        if self.usage_count > 0:
            self.usage_count -= 1

    def get_keywords_list(self) -> List[str]:
        """获取关键词列表"""
        if not self.keywords:
            return []
        return [k.strip() for k in self.keywords.split(',') if k.strip()]

    @classmethod
    def get_by_category(cls, category: str, is_active: bool = True) -> List["CulturalTag"]:
        """根据分类获取标签列表"""
        pass

    @classmethod
    def search_by_keyword(cls, keyword: str, is_active: bool = True) -> List["CulturalTag"]:
        """根据关键词搜索标签"""
        pass

    @classmethod
    def get_popular_tags(cls, limit: int = 10) -> List["CulturalTag"]:
        """获取热门标签（按使用次数排序）"""
        pass
