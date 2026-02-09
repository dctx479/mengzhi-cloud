"""
文化标签Schema定义

包含：
- 标签创建请求
- 标签更新请求
- 标签响应
- 标签列表查询
- 标签推荐请求

版本: 1.0
更新日期: 2026-01-17
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

from app.core.constants import (
    TAG_CATEGORY_GEO, TAG_CATEGORY_ETHNICITY, TAG_CATEGORY_HISTORY,
    TAG_CATEGORY_CRAFT, TAG_CATEGORY_FESTIVAL, TAG_CATEGORY_NUTRITION,
    TAG_CATEGORY_STORY
)


# ==================== 基础Schema ====================

class CulturalTagBase(BaseModel):
    """文化标签基础Schema"""

    name: str = Field(..., min_length=1, max_length=50, description="标签名称")
    category: str = Field(..., description="标签分类")
    description: Optional[str] = Field(None, max_length=500, description="标签描述")
    keywords: Optional[str] = Field(None, max_length=200, description="关键词（逗号分隔）")
    parent_id: Optional[int] = Field(None, description="父标签ID")

    @validator('category')
    def validate_category(cls, v):
        """验证标签分类"""
        valid_categories = [
            TAG_CATEGORY_GEO, TAG_CATEGORY_ETHNICITY, TAG_CATEGORY_HISTORY,
            TAG_CATEGORY_CRAFT, TAG_CATEGORY_FESTIVAL, TAG_CATEGORY_NUTRITION,
            TAG_CATEGORY_STORY
        ]
        if v not in valid_categories:
            raise ValueError(f"标签分类必须是以下之一: {', '.join(valid_categories)}")
        return v


# ==================== 请求Schema ====================

class CulturalTagCreate(CulturalTagBase):
    """创建文化标签请求"""
    pass


class CulturalTagUpdate(BaseModel):
    """更新文化标签请求"""

    name: Optional[str] = Field(None, min_length=1, max_length=50, description="标签名称")
    category: Optional[str] = Field(None, description="标签分类")
    description: Optional[str] = Field(None, max_length=500, description="标签描述")
    keywords: Optional[str] = Field(None, max_length=200, description="关键词")
    parent_id: Optional[int] = Field(None, description="父标签ID")
    is_active: Optional[bool] = Field(None, description="是否启用")

    @validator('category')
    def validate_category(cls, v):
        """验证标签分类"""
        if v is None:
            return v
        valid_categories = [
            TAG_CATEGORY_GEO, TAG_CATEGORY_ETHNICITY, TAG_CATEGORY_HISTORY,
            TAG_CATEGORY_CRAFT, TAG_CATEGORY_FESTIVAL, TAG_CATEGORY_NUTRITION,
            TAG_CATEGORY_STORY
        ]
        if v not in valid_categories:
            raise ValueError(f"标签分类必须是以下之一: {', '.join(valid_categories)}")
        return v


# ==================== 响应Schema ====================

class CulturalTagResponse(CulturalTagBase):
    """文化标签响应"""

    id: int = Field(..., description="标签ID")
    usage_count: int = Field(default=0, description="使用次数")
    is_active: bool = Field(default=True, description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class CulturalTagListItemResponse(BaseModel):
    """文化标签列表项响应（简化版）"""

    id: int
    name: str
    category: str
    usage_count: int
    is_active: bool

    class Config:
        from_attributes = True


class CulturalTagWithProductsResponse(CulturalTagResponse):
    """带产品信息的标签响应"""

    product_count: int = Field(default=0, description="关联产品数量")


# ==================== 查询Schema ====================

class CulturalTagListQuery(BaseModel):
    """文化标签列表查询参数"""

    category: Optional[str] = Field(None, description="按分类筛选")
    keyword: Optional[str] = Field(None, max_length=100, description="关键词搜索")
    is_active: bool = Field(True, description="是否只显示启用的标签")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(50, ge=1, le=100, description="每页数量")

    @validator('category')
    def validate_category(cls, v):
        """验证标签分类"""
        if v is None:
            return v
        valid_categories = [
            TAG_CATEGORY_GEO, TAG_CATEGORY_ETHNICITY, TAG_CATEGORY_HISTORY,
            TAG_CATEGORY_CRAFT, TAG_CATEGORY_FESTIVAL, TAG_CATEGORY_NUTRITION,
            TAG_CATEGORY_STORY
        ]
        if v not in valid_categories:
            raise ValueError(f"标签分类必须是以下之一: {', '.join(valid_categories)}")
        return v


class CulturalTagRecommendQuery(BaseModel):
    """标签推荐查询参数"""

    product_id: Optional[int] = Field(None, description="基于产品推荐")
    keywords: Optional[str] = Field(None, max_length=200, description="基于关键词推荐")
    limit: int = Field(10, ge=1, le=50, description="推荐数量")


# ==================== 分类Schema ====================

class TagCategoryResponse(BaseModel):
    """标签分类响应"""

    code: str = Field(..., description="分类代码")
    name: str = Field(..., description="分类名称")
    icon: str = Field(..., description="分类图标")
    description: str = Field(..., description="分类描述")
    tag_count: int = Field(default=0, description="该分类下的标签数量")


# ==================== 产品标签关联Schema ====================

class ProductTagsAssignRequest(BaseModel):
    """产品标签分配请求"""

    tag_ids: List[int] = Field(..., min_items=1, description="标签ID列表")

    @validator('tag_ids')
    def validate_tag_ids(cls, v):
        """验证标签ID列表"""
        if len(v) != len(set(v)):
            raise ValueError("标签ID列表中存在重复")
        return v


class ProductTagsResponse(BaseModel):
    """产品标签响应"""

    product_id: int = Field(..., description="产品ID")
    tags: List[CulturalTagListItemResponse] = Field(default_factory=list, description="标签列表")


# ==================== 统计Schema ====================

class TagStatisticsResponse(BaseModel):
    """标签统计响应"""

    total_tags: int = Field(..., description="标签总数")
    active_tags: int = Field(..., description="启用标签数")
    category_distribution: dict = Field(..., description="分类分布")
    popular_tags: List[CulturalTagListItemResponse] = Field(..., description="热门标签")


__all__ = [
    "CulturalTagBase",
    "CulturalTagCreate",
    "CulturalTagUpdate",
    "CulturalTagResponse",
    "CulturalTagListItemResponse",
    "CulturalTagWithProductsResponse",
    "CulturalTagListQuery",
    "CulturalTagRecommendQuery",
    "TagCategoryResponse",
    "ProductTagsAssignRequest",
    "ProductTagsResponse",
    "TagStatisticsResponse",
]
