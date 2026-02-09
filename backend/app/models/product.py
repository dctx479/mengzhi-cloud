"""
产品数据模型 - SQLAlchemy ORM

包含：
- 产品基本信息
- 产品定位信息
- 文化属性
- 认证信息
- 媒体资源

版本: 1.0
更新日期: 2026-01-17
"""

from sqlalchemy import (
    Column, BIGINT, VARCHAR, Enum, TIMESTAMP, Index,
    UniqueConstraint, Text, TEXT, Integer, DECIMAL, JSON, DATE,
    ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime, date
from typing import Optional, Dict, Any, List
import enum

from .base import BaseModel, generate_uuid


class ProductStatus(enum.Enum):
    """产品状态枚举"""
    DRAFT = "draft"  # 草稿
    PENDING = "pending"  # 待审核
    PUBLISHED = "published"  # 已发布
    OFFLINE = "offline"  # 已下架


class Product(BaseModel):
    """产品模型

    产品包含：
    - 基本信息（名称、分类等）
    - 产地信息（地理位置、经纬度）
    - 文化属性（标签、故事、历史）
    - 认证信息（地理标志、绿色、有机等）
    - 媒体资源（图片、视频）
    - 统计数据（浏览次数、生成次数）
    """

    __tablename__ = "products"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="产品ID"
    )

    # UUID标识
    product_uuid = Column(
        VARCHAR(36),
        nullable=False,
        unique=True,
        index=True,
        default=generate_uuid,
        comment="产品UUID"
    )

    # 基本信息
    name = Column(
        VARCHAR(200),
        nullable=False,
        index=True,
        comment="产品名称"
    )
    short_name = Column(
        VARCHAR(100),
        nullable=True,
        comment="产品简称"
    )
    category = Column(
        VARCHAR(100),
        nullable=False,
        index=True,
        comment="产品类别"
    )
    sub_category = Column(
        VARCHAR(100),
        nullable=True,
        comment="产品子类别"
    )

    # 产地信息
    origin_province = Column(
        VARCHAR(50),
        nullable=False,
        index=True,
        comment="产地省份"
    )
    origin_city = Column(
        VARCHAR(50),
        nullable=True,
        index=True,
        comment="产地城市"
    )
    origin_district = Column(
        VARCHAR(50),
        nullable=True,
        comment="产地区县"
    )
    origin_detail = Column(
        VARCHAR(500),
        nullable=True,
        comment="产地详情"
    )
    latitude = Column(
        DECIMAL(10, 7),
        nullable=True,
        comment="产地纬度"
    )
    longitude = Column(
        DECIMAL(10, 7),
        nullable=True,
        comment="产地经度"
    )

    # 产品详情
    description = Column(
        TEXT,
        nullable=True,
        comment="产品描述"
    )
    features = Column(
        JSON,
        nullable=True,
        comment="产品特点(JSON数组)"
    )
    specifications = Column(
        JSON,
        nullable=True,
        comment="规格参数(JSON对象)"
    )
    nutrition_facts = Column(
        JSON,
        nullable=True,
        comment="营养成分(JSON对象)"
    )

    # 认证信息
    certification_type = Column(
        VARCHAR(100),
        nullable=True,
        index=True,
        comment="认证类型：地理标志/绿色食品/有机认证"
    )
    certification_no = Column(
        VARCHAR(100),
        nullable=True,
        comment="认证编号"
    )
    certification_date = Column(
        DATE,
        nullable=True,
        comment="认证日期"
    )
    certification_expires = Column(
        DATE,
        nullable=True,
        comment="认证有效期"
    )

    # 文化属性
    cultural_tags = Column(
        JSON,
        nullable=True,
        comment="文化标签数组"
    )
    cultural_story = Column(
        TEXT,
        nullable=True,
        comment="文化故事"
    )
    historical_origin = Column(
        TEXT,
        nullable=True,
        comment="历史渊源"
    )

    # 媒体资源
    main_image_url = Column(
        VARCHAR(500),
        nullable=True,
        comment="主图URL"
    )
    image_urls = Column(
        JSON,
        nullable=True,
        comment="图片URL数组"
    )
    video_url = Column(
        VARCHAR(500),
        nullable=True,
        comment="视频URL"
    )

    # 状态与统计
    status = Column(
        Enum(ProductStatus),
        nullable=False,
        default=ProductStatus.DRAFT,
        index=True,
        comment="产品状态"
    )
    view_count = Column(
        Integer,
        default=0,
        comment="浏览次数"
    )
    generate_count = Column(
        Integer,
        default=0,
        comment="内容生成次数"
    )

    # 关联关系
    enterprise_id = Column(
        BIGINT,
        ForeignKey("enterprises.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="所属企业ID"
    )
    created_by = Column(
        BIGINT,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="创建人用户ID"
    )

    # 发布相关时间
    published_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="发布时间"
    )

    # 关系
    enterprise = relationship(
        "Enterprise",
        foreign_keys=[enterprise_id],
        back_populates="products"
    )
    creator = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="products"
    )
    content_records = relationship(
        "ContentRecord",
        back_populates="product",
        cascade="all, delete-orphan"
    )
    media = relationship(
        "Media",
        foreign_keys="Media.product_id",
        back_populates="product",
        cascade="all, delete-orphan"
    )
    tags = relationship(
        "CulturalTag",
        secondary="product_tags",
        back_populates="products"
    )

    # 索引定义
    __table_args__ = (
        UniqueConstraint("product_uuid", name="uk_product_uuid"),
        Index("idx_name", "name"),
        Index("idx_category", "category"),
        Index("idx_origin_province", "origin_province"),
        Index("idx_origin_city", "origin_city"),
        Index("idx_certification_type", "certification_type"),
        Index("idx_status", "status"),
        Index("idx_enterprise_id", "enterprise_id"),
        Index("idx_created_by", "created_by"),
        Index("idx_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name={self.name}, status={self.status.value})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "product_uuid": self.product_uuid,
            "name": self.name,
            "short_name": self.short_name,
            "category": self.category,
            "sub_category": self.sub_category,
            "origin_province": self.origin_province,
            "origin_city": self.origin_city,
            "origin_district": self.origin_district,
            "origin_detail": self.origin_detail,
            "latitude": float(self.latitude) if self.latitude else None,
            "longitude": float(self.longitude) if self.longitude else None,
            "description": self.description,
            "features": self.features,
            "specifications": self.specifications,
            "nutrition_facts": self.nutrition_facts,
            "certification_type": self.certification_type,
            "certification_no": self.certification_no,
            "certification_date": self.certification_date.isoformat() if self.certification_date else None,
            "certification_expires": self.certification_expires.isoformat() if self.certification_expires else None,
            "cultural_tags": self.cultural_tags,
            "cultural_story": self.cultural_story,
            "historical_origin": self.historical_origin,
            "main_image_url": self.main_image_url,
            "image_urls": self.image_urls,
            "video_url": self.video_url,
            "status": self.status.value if self.status else None,
            "view_count": self.view_count,
            "generate_count": self.generate_count,
            "enterprise_id": self.enterprise_id,
            "created_by": self.created_by,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_published(self) -> bool:
        """检查产品是否已发布"""
        return self.status == ProductStatus.PUBLISHED

    def is_certified(self) -> bool:
        """检查产品是否已认证"""
        if self.certification_type is None:
            return False
        if self.certification_expires is None:
            return False
        return date.today() <= self.certification_expires

    def get_location(self) -> Dict[str, Any]:
        """获取产品位置信息"""
        return {
            "province": self.origin_province,
            "city": self.origin_city,
            "district": self.origin_district,
            "detail": self.origin_detail,
            "latitude": float(self.latitude) if self.latitude else None,
            "longitude": float(self.longitude) if self.longitude else None,
        }

    @classmethod
    def get_by_uuid(cls, product_uuid: str) -> Optional["Product"]:
        """根据UUID获取产品"""
        pass

    @classmethod
    def get_published_products(cls, category: str = None) -> List["Product"]:
        """获取已发布的产品"""
        pass

    @classmethod
    def search_by_origin(cls, province: str, city: str = None) -> List["Product"]:
        """按产地搜索产品"""
        pass

    @classmethod
    def search_by_certification(cls, certification_type: str) -> List["Product"]:
        """按认证类型搜索产品"""
        pass
