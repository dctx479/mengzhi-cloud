"""
配额套餐Schema (Pydantic)

版本: 1.0
创建日期: 2026-01-23
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============ 响应Schema ============

class QuotaPackageListItemResponse(BaseModel):
    """配额套餐列表项响应"""

    id: int = Field(..., description="套餐ID")
    name: str = Field(..., description="套餐名称")
    package_type: str = Field(..., description="套餐类型")
    period: str = Field(..., description="套餐周期")
    price: float = Field(..., description="套餐价格(元)")
    original_price: Optional[float] = Field(None, description="原价")
    discount_percentage: Optional[int] = Field(None, description="折扣百分比")

    # 配额信息
    chat_quota: int = Field(..., description="对话次数配额")
    generation_quota: int = Field(..., description="生成次数配额")
    token_quota: int = Field(..., description="Token配额")
    storage_quota_mb: int = Field(..., description="存储配额(MB)")
    validity_days: int = Field(..., description="有效期(天)")

    # 状态
    is_active: bool = Field(..., description="是否启用")
    is_recommended: bool = Field(..., description="是否推荐")
    sort_order: int = Field(..., description="排序顺序")

    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "标准版-月付",
                "package_type": "standard",
                "period": "monthly",
                "price": 99.00,
                "original_price": 129.00,
                "discount_percentage": 23,
                "chat_quota": 500,
                "generation_quota": 200,
                "token_quota": 200000,
                "storage_quota_mb": 2000,
                "validity_days": 30,
                "is_active": True,
                "is_recommended": True,
                "sort_order": 2,
                "created_at": "2026-01-23T10:00:00"
            }
        }


class QuotaPackageDetailResponse(BaseModel):
    """配额套餐详情响应"""

    id: int = Field(..., description="套餐ID")
    name: str = Field(..., description="套餐名称")
    package_type: str = Field(..., description="套餐类型")
    period: str = Field(..., description="套餐周期")
    price: float = Field(..., description="套餐价格(元)")
    original_price: Optional[float] = Field(None, description="原价")
    discount_percentage: Optional[int] = Field(None, description="折扣百分比")

    # 配额信息
    quotas: Dict[str, int] = Field(..., description="配额详情")
    validity_days: int = Field(..., description="有效期(天)")

    # 描述信息
    description: Optional[str] = Field(None, description="套餐描述")
    features: Optional[str] = Field(None, description="套餐特性(JSON)")

    # 状态
    is_active: bool = Field(..., description="是否启用")
    is_recommended: bool = Field(..., description="是否推荐")
    sort_order: int = Field(..., description="排序顺序")

    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "标准版-月付",
                "package_type": "standard",
                "period": "monthly",
                "price": 99.00,
                "original_price": 129.00,
                "discount_percentage": 23,
                "quotas": {
                    "chat": 500,
                    "generation": 200,
                    "token": 200000,
                    "storage_mb": 2000
                },
                "validity_days": 30,
                "description": "适合个人用户中度使用",
                "features": None,
                "is_active": True,
                "is_recommended": True,
                "sort_order": 2,
                "created_at": "2026-01-23T10:00:00",
                "updated_at": "2026-01-23T10:00:00"
            }
        }
