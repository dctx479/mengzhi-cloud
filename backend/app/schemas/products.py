"""
产品Schema (Pydantic)

版本: 2.0
更新日期: 2026-01-23
修复: 字段映射与Product模型一致
"""

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ProductStatus(str, Enum):
    """产品状态枚举"""
    DRAFT = "draft"
    PENDING = "pending"
    PUBLISHED = "published"
    OFFLINE = "offline"


# ============ 请求Schema ============

class ProductCreateRequest(BaseModel):
    """产品创建请求"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "草原牛肉",
            "short_name": "牛肉",
            "description": "来自内蒙古草原的优质牛肉",
            "category": "肉类",
            "sub_category": "牛肉制品",
            "origin_province": "内蒙古",
            "origin_city": "呼伦贝尔",
            "origin_district": "陈巴尔虎旗",
            "origin_detail": "呼伦贝尔大草原核心区域",
            "cultural_tags": ["草原", "有机", "绿色"],
            "cultural_story": "传统草原养殖文化",
            "historical_origin": "草原牛自由放牧...",
            "certification_type": "地理标志",
            "certification_no": "GI-2024-001",
            "status": "draft"
        }
    })

    name: str = Field(..., min_length=1, max_length=200, description="产品名称")
    short_name: Optional[str] = Field(None, max_length=100, description="产品简称")
    description: Optional[str] = Field(None, description="产品描述")
    category: str = Field(..., min_length=1, max_length=100, description="产品类别")
    sub_category: Optional[str] = Field(None, max_length=100, description="产品子类别")

    # 产地信息
    origin_province: str = Field(..., min_length=1, max_length=50, description="产地省份")
    origin_city: Optional[str] = Field(None, max_length=50, description="产地城市")
    origin_district: Optional[str] = Field(None, max_length=50, description="产地区县")
    origin_detail: Optional[str] = Field(None, max_length=500, description="产地详情")
    latitude: Optional[float] = Field(None, description="纬度")
    longitude: Optional[float] = Field(None, description="经度")

    # 产品详情
    features: Optional[List[str]] = Field(None, description="产品特点列表")
    specifications: Optional[dict] = Field(None, description="规格参数")
    nutrition_facts: Optional[dict] = Field(None, description="营养成分")

    # 文化属性
    cultural_tags: Optional[List[str]] = Field(None, description="文化标签列表")
    cultural_story: Optional[str] = Field(None, description="文化故事")
    historical_origin: Optional[str] = Field(None, description="历史渊源")

    # 认证信息
    certification_type: Optional[str] = Field(None, max_length=100, description="认证类型")
    certification_no: Optional[str] = Field(None, max_length=100, description="认证编号")

    status: ProductStatus = Field(default=ProductStatus.DRAFT, description="产品状态")


class ProductUpdateRequest(BaseModel):
    """产品更新请求"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "高级草原牛肉",
            "description": "更新后的描述",
            "status": "published"
        }
    })

    name: Optional[str] = Field(None, min_length=1, max_length=200, description="产品名称")
    short_name: Optional[str] = Field(None, max_length=100, description="产品简称")
    description: Optional[str] = Field(None, description="产品描述")
    category: Optional[str] = Field(None, min_length=1, max_length=100, description="产品类别")
    sub_category: Optional[str] = Field(None, max_length=100, description="产品子类别")

    # 产地信息
    origin_province: Optional[str] = Field(None, min_length=1, max_length=50, description="产地省份")
    origin_city: Optional[str] = Field(None, max_length=50, description="产地城市")
    origin_district: Optional[str] = Field(None, max_length=50, description="产地区县")
    origin_detail: Optional[str] = Field(None, max_length=500, description="产地详情")
    latitude: Optional[float] = Field(None, description="纬度")
    longitude: Optional[float] = Field(None, description="经度")

    # 产品详情
    features: Optional[List[str]] = Field(None, description="产品特点列表")
    specifications: Optional[dict] = Field(None, description="规格参数")
    nutrition_facts: Optional[dict] = Field(None, description="营养成分")

    # 文化属性
    cultural_tags: Optional[List[str]] = Field(None, description="文化标签列表")
    cultural_story: Optional[str] = Field(None, description="文化故事")
    historical_origin: Optional[str] = Field(None, description="历史渊源")

    # 认证信息
    certification_type: Optional[str] = Field(None, max_length=100, description="认证类型")
    certification_no: Optional[str] = Field(None, max_length=100, description="认证编号")

    status: Optional[ProductStatus] = Field(None, description="产品状态")


# ============ 响应Schema ============

class CulturalInfoResponse(BaseModel):
    """文化信息响应"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "cultural_tags": ["草原", "有机", "绿色"],
            "cultural_story": "传统草原养殖文化",
            "historical_origin": "草原牛自由放牧...",
            "origin_province": "内蒙古",
            "origin_city": "呼伦贝尔",
            "origin_district": "陈巴尔虎旗"
        }
    })

    cultural_tags: Optional[List[str]] = Field(default=None, description="文化标签列表")
    cultural_story: Optional[str] = Field(default=None, description="文化故事")
    historical_origin: Optional[str] = Field(default=None, description="历史渊源")
    origin_province: str = Field(..., description="产地省份")
    origin_city: Optional[str] = Field(default=None, description="产地城市")
    origin_district: Optional[str] = Field(default=None, description="产地区县")


class ProductDetailResponse(BaseModel):
    """产品详情响应"""
    model_config = ConfigDict(from_attributes=True, json_schema_extra={
        "example": {
            "id": 1,
            "product_uuid": "550e8400-e29b-41d4-a716-446655440000",
            "name": "草原牛肉",
            "short_name": "牛肉",
            "description": "来自内蒙古草原的优质牛肉",
            "category": "肉类",
            "sub_category": "牛肉制品",
            "origin_province": "内蒙古",
            "origin_city": "呼伦贝尔",
            "origin_district": "陈巴尔虎旗",
            "origin_detail": "呼伦贝尔大草原核心区域",
            "latitude": 49.2,
            "longitude": 119.7,
            "cultural_tags": ["草原", "有机", "绿色"],
            "cultural_story": "传统草原养殖文化",
            "historical_origin": "草原牛自由放牧...",
            "certification_type": "地理标志",
            "certification_no": "GI-2024-001",
            "main_image_url": "/uploads/products/1/main.jpg",
            "image_urls": ["/uploads/products/1/1.jpg", "/uploads/products/1/2.jpg"],
            "video_url": "/uploads/products/1/video.mp4",
            "status": "draft",
            "view_count": 100,
            "generate_count": 10,
            "created_at": "2026-01-17T10:00:00",
            "updated_at": "2026-01-17T10:00:00",
            "created_by": 1,
            "published_at": None
        }
    })

    id: int = Field(..., description="产品ID")
    product_uuid: str = Field(..., description="产品UUID")
    name: str = Field(..., description="产品名称")
    short_name: Optional[str] = Field(default=None, description="产品简称")
    description: Optional[str] = Field(default=None, description="产品描述")
    category: str = Field(..., description="产品类别")
    sub_category: Optional[str] = Field(default=None, description="产品子类别")

    # 产地信息
    origin_province: str = Field(..., description="产地省份")
    origin_city: Optional[str] = Field(default=None, description="产地城市")
    origin_district: Optional[str] = Field(default=None, description="产地区县")
    origin_detail: Optional[str] = Field(default=None, description="产地详情")
    latitude: Optional[float] = Field(default=None, description="纬度")
    longitude: Optional[float] = Field(default=None, description="经度")

    # 文化属性
    cultural_tags: Optional[List[str]] = Field(default=None, description="文化标签列表")
    cultural_story: Optional[str] = Field(default=None, description="文化故事")
    historical_origin: Optional[str] = Field(default=None, description="历史渊源")

    # 认证信息
    certification_type: Optional[str] = Field(default=None, description="认证类型")
    certification_no: Optional[str] = Field(default=None, description="认证编号")

    # 产品详情
    features: Optional[List[str]] = Field(default=None, description="产品特点列表")
    specifications: Optional[dict] = Field(default=None, description="规格参数")
    nutrition_facts: Optional[dict] = Field(default=None, description="营养成分")

    # 媒体资源
    main_image_url: Optional[str] = Field(default=None, description="主图URL")
    image_urls: Optional[List[str]] = Field(default=None, description="图片URL列表")
    video_url: Optional[str] = Field(default=None, description="视频URL")

    # 状态与统计
    status: str = Field(..., description="产品状态")
    view_count: int = Field(default=0, description="浏览次数")
    generate_count: int = Field(default=0, description="生成次数")

    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: int = Field(..., description="创建者ID")
    published_at: Optional[datetime] = Field(default=None, description="发布时间")
    price: float = Field(default=0, description="价格")

    @field_validator('status', mode='before')
    @classmethod
    def convert_status_enum(cls, v):
        """将枚举转换为字符串"""
        if hasattr(v, 'value'):
            return v.value
        return v


class ProductListItemResponse(BaseModel):
    """产品列表项响应（简化版）"""
    model_config = ConfigDict(from_attributes=True, json_schema_extra={
        "example": {
            "id": 1,
            "product_uuid": "550e8400-e29b-41d4-a716-446655440000",
            "name": "草原牛肉",
            "category": "肉类",
            "sub_category": "牛肉制品",
            "origin_province": "内蒙古",
            "origin_city": "呼伦贝尔",
            "main_image_url": "/uploads/products/1/main.jpg",
            "image_urls": ["/uploads/products/1/1.jpg"],
            "status": "draft",
            "view_count": 100,
            "price": 59.99,
            "created_at": "2026-01-17T10:00:00"
        }
    })

    id: int = Field(..., description="产品ID")
    product_uuid: str = Field(..., description="产品UUID")
    name: str = Field(..., description="产品名称")
    description: Optional[str] = Field(default=None, description="产品描述")
    category: str = Field(..., description="产品类别")
    sub_category: Optional[str] = Field(default=None, description="产品子类别")
    origin_province: str = Field(..., description="产地省份")
    origin_city: Optional[str] = Field(default=None, description="产地城市")
    main_image_url: Optional[str] = Field(default=None, description="主图URL")
    image_urls: Optional[List[str]] = Field(default=None, description="图片URL列表")
    status: str = Field(..., description="产品状态")
    view_count: int = Field(default=0, description="浏览次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")
    specifications: Optional[dict] = Field(default=None, description="规格参数")
    price: float = Field(default=0, description="价格")

    @field_validator('status', mode='before')
    @classmethod
    def convert_status_enum(cls, v):
        """将枚举转换为字符串"""
        if hasattr(v, 'value'):
            return v.value
        return v


# ============ 查询参数Schema ============

class ProductListQuery(BaseModel):
    """产品列表查询参数"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "page": 1,
            "size": 10,
            "search": "牛肉",
            "category": "肉类",
            "region": "内蒙古",
            "status": "published",
            "sort_by": "created_at",
            "sort_order": "desc"
        }
    })

    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=10, ge=1, le=100, description="每页数量")

    search: Optional[str] = Field(None, max_length=100, description="搜索关键词（名称）")
    category: Optional[str] = Field(None, max_length=100, description="产品类别")
    region: Optional[str] = Field(None, max_length=100, description="产地区域（省份）")
    status: Optional[ProductStatus] = Field(None, description="产品状态")
    is_featured: Optional[bool] = Field(None, description="是否精选产品")

    sort_by: Optional[str] = Field(default="created_at", description="排序字段：created_at, name")
    sort_order: Optional[str] = Field(default="desc", description="排序顺序：asc, desc")

    @field_validator('sort_by')
    @classmethod
    def validate_sort_by(cls, v):
        """验证排序字段"""
        allowed_fields = ['created_at', 'name', 'updated_at', 'view_count']
        if v not in allowed_fields:
            raise ValueError(f'排序字段必须为: {", ".join(allowed_fields)}')
        return v

    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v):
        """验证排序顺序"""
        if v not in ['asc', 'desc']:
            raise ValueError('排序顺序必须为: asc 或 desc')
        return v
