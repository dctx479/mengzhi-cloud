"""
多模态素材数据模型 - SQLAlchemy ORM

包含：
- 图片、视频、音频、文档等媒体文件管理
- 文件元数据（尺寸、时长、MIME类型）
- 分类和关联管理
- 存储路径和CDN URL

版本: 1.0
更新日期: 2026-01-17
"""

from sqlalchemy import (
    Column,
    BIGINT,
    VARCHAR,
    Enum,
    Integer,
    TIMESTAMP,
    Index,
    UniqueConstraint,
    Text,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any
import enum

from .base import BaseModel, generate_uuid


class MediaType(enum.Enum):
    """媒体类型枚举"""

    IMAGE = "image"  # 图片
    VIDEO = "video"  # 视频
    AUDIO = "audio"  # 音频
    DOCUMENT = "document"  # 文档


class MediaCategory(enum.Enum):
    """媒体分类枚举"""

    PRODUCT = "product"  # 产品图片/视频
    CULTURE = "culture"  # 文化素材
    CERTIFICATE = "certificate"  # 证书资质
    USER_AVATAR = "user_avatar"  # 用户头像
    OTHER = "other"  # 其他


class Media(BaseModel):
    """媒体素材模型

    支持多种媒体类型的上传、存储、管理。
    可关联到产品、用户等实体。
    支持本地存储和对象存储（OSS/COS/S3）。
    """

    __tablename__ = "media"

    # 主键
    id = Column(BIGINT, primary_key=True, autoincrement=True, comment="媒体ID")

    # UUID标识
    media_uuid = Column(VARCHAR(36), nullable=False, unique=True, index=True, default=generate_uuid, comment="媒体UUID")

    # 文件信息
    filename = Column(VARCHAR(255), nullable=False, comment="原始文件名")
    file_path = Column(VARCHAR(500), nullable=False, comment="存储路径（本地路径或OSS对象键）")
    file_url = Column(VARCHAR(500), nullable=False, comment="访问URL（CDN或本地静态路径）")
    file_size = Column(BIGINT, nullable=False, comment="文件大小（字节）")
    mime_type = Column(VARCHAR(100), nullable=False, comment="MIME类型（如image/jpeg）")

    # 分类
    media_type = Column(Enum(MediaType), nullable=False, index=True, comment="媒体类型：image/video/audio/document")
    category = Column(
        Enum(MediaCategory),
        nullable=False,
        index=True,
        comment="媒体分类：product/culture/certificate/user_avatar/other",
    )

    # 元数据（图片/视频专用）
    width = Column(Integer, nullable=True, comment="宽度（像素）")
    height = Column(Integer, nullable=True, comment="高度（像素）")
    duration = Column(Integer, nullable=True, comment="时长（秒，用于视频/音频）")

    # 缩略图（图片/视频封面）
    thumbnail_url = Column(VARCHAR(500), nullable=True, comment="缩略图URL")

    # 关联
    product_id = Column(
        BIGINT, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True, comment="关联产品ID"
    )
    user_id = Column(
        BIGINT, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="上传者用户ID"
    )

    # 描述信息
    title = Column(VARCHAR(200), nullable=True, comment="媒体标题")
    description = Column(Text, nullable=True, comment="媒体描述")
    alt_text = Column(VARCHAR(200), nullable=True, comment="图片alt属性（无障碍访问）")

    # 状态
    is_public = Column(Boolean, default=True, comment="是否公开")
    is_processed = Column(Boolean, default=False, comment="是否已处理（压缩、转码等）")

    # 关系
    user = relationship("User", foreign_keys=[user_id], back_populates="media")
    product = relationship("Product", foreign_keys=[product_id], back_populates="media")

    # 索引定义
    __table_args__ = (
        UniqueConstraint("media_uuid", name="uk_media_uuid"),
        Index("idx_media_type", "media_type"),
        Index("idx_media_category", "category"),
        Index("idx_media_user_id", "user_id"),
        Index("idx_media_product_id", "product_id"),
        Index("idx_media_created_at", "created_at"),
        Index("idx_media_deleted_at", "deleted_at"),
    )

    def __repr__(self) -> str:
        return f"<Media(id={self.id}, filename={self.filename}, type={self.media_type.value})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "media_uuid": self.media_uuid,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_url": self.file_url,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "media_type": self.media_type.value,
            "category": self.category.value,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "thumbnail_url": self.thumbnail_url,
            "product_id": self.product_id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "alt_text": self.alt_text,
            "is_public": self.is_public,
            "is_processed": self.is_processed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_image(self) -> bool:
        """检查是否为图片"""
        return self.media_type == MediaType.IMAGE

    def is_video(self) -> bool:
        """检查是否为视频"""
        return self.media_type == MediaType.VIDEO

    def get_file_size_mb(self) -> float:
        """获取文件大小（MB）"""
        return round(self.file_size / (1024 * 1024), 2)

    def get_dimensions(self) -> Optional[Dict[str, int]]:
        """获取媒体尺寸"""
        if self.width and self.height:
            return {"width": self.width, "height": self.height}
        return None

    @classmethod
    def get_by_uuid(cls, media_uuid: str) -> Optional["Media"]:
        """根据UUID获取媒体"""
        pass

    @classmethod
    def get_by_product(cls, product_id: int) -> list:
        """获取产品的所有媒体"""
        pass

    @classmethod
    def get_by_user(cls, user_id: int, media_type: MediaType = None) -> list:
        """获取用户上传的媒体"""
        pass
