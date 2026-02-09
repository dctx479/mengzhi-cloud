"""
媒体素材 Schema - Pydantic 数据验证

包含：
- 媒体创建/更新/响应Schema
- 分页响应
- 文件上传表单

版本: 1.0
更新日期: 2026-01-17
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MediaType(str, Enum):
    """媒体类型枚举"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


class MediaCategory(str, Enum):
    """媒体分类枚举"""
    PRODUCT = "product"
    CULTURE = "culture"
    CERTIFICATE = "certificate"
    USER_AVATAR = "user_avatar"
    OTHER = "other"


class MediaBase(BaseModel):
    """媒体基础Schema"""
    title: Optional[str] = Field(None, max_length=200, description="媒体标题")
    description: Optional[str] = Field(None, description="媒体描述")
    alt_text: Optional[str] = Field(None, max_length=200, description="图片alt属性")
    is_public: bool = Field(True, description="是否公开")


class MediaCreate(MediaBase):
    """媒体创建Schema（用于表单数据）"""
    category: MediaCategory = Field(..., description="媒体分类")
    product_id: Optional[int] = Field(None, description="关联产品ID")

    @field_validator('product_id')
    @classmethod
    def validate_product_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError("产品ID必须大于0")
        return v


class MediaUpdate(BaseModel):
    """媒体更新Schema"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    alt_text: Optional[str] = Field(None, max_length=200)
    is_public: Optional[bool] = None
    product_id: Optional[int] = None


class MediaResponse(MediaBase):
    """媒体响应Schema"""
    id: int
    media_uuid: str
    filename: str
    file_url: str
    file_size: int = Field(..., description="文件大小（字节）")
    mime_type: str
    media_type: MediaType
    category: MediaCategory
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None
    user_id: int
    product_id: Optional[int] = None
    is_processed: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @property
    def file_size_mb(self) -> float:
        """文件大小（MB）"""
        return round(self.file_size / (1024 * 1024), 2)

    @property
    def dimensions(self) -> Optional[str]:
        """尺寸字符串"""
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return None


class MediaListResponse(BaseModel):
    """媒体列表响应Schema"""
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    items: List[MediaResponse] = Field(..., description="媒体列表")


class MediaUploadResponse(BaseModel):
    """媒体上传响应Schema"""
    success: bool = True
    message: str = "文件上传成功"
    data: MediaResponse


class MediaBatchDeleteRequest(BaseModel):
    """批量删除请求Schema"""
    media_ids: List[int] = Field(..., min_length=1, max_length=100, description="媒体ID列表")

    @field_validator('media_ids')
    @classmethod
    def validate_media_ids(cls, v):
        if not v:
            raise ValueError("媒体ID列表不能为空")
        if len(v) > 100:
            raise ValueError("一次最多删除100个媒体")
        return v


class MediaStatsResponse(BaseModel):
    """媒体统计响应Schema"""
    total_count: int = Field(..., description="总媒体数")
    total_size: int = Field(..., description="总大小（字节）")
    image_count: int = Field(..., description="图片数量")
    video_count: int = Field(..., description="视频数量")
    by_category: dict = Field(..., description="按分类统计")

    @property
    def total_size_mb(self) -> float:
        """总大小（MB）"""
        return round(self.total_size / (1024 * 1024), 2)
