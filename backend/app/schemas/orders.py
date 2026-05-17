"""
订单Schema (Pydantic)

版本: 1.0
创建日期: 2026-01-23
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


# ============ 请求Schema ============

class OrderCreateRequest(BaseModel):
    """订单创建请求"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "package_id": 1
        }
    })

    package_id: int = Field(..., description="套餐ID")


# ============ 响应Schema ============

class OrderDetailResponse(BaseModel):
    """订单详情响应"""
    model_config = ConfigDict(from_attributes=True, json_schema_extra={
        "example": {
            "id": 1,
            "order_no": "ORD20260123001",
            "user_id": 1,
            "package_id": 1,
            "package_name": "标准版-月付",
            "package_type": "standard",
            "amount": 99.00,
            "original_amount": 129.00,
            "discount_amount": 30.00,
            "quotas": {
                "chat": 500,
                "generation": 200,
                "token": 200000,
                "storage_mb": 2000
            },
            "validity_days": 30,
            "status": "pending",
            "remark": None,
            "paid_at": None,
            "completed_at": None,
            "cancelled_at": None,
            "expired_at": "2026-01-24T10:00:00",
            "created_at": "2026-01-23T10:00:00",
            "updated_at": "2026-01-23T10:00:00"
        }
    })

    id: int = Field(..., description="订单ID")
    order_no: str = Field(..., description="订单号")
    user_id: int = Field(..., description="用户ID")
    package_id: Optional[int] = Field(None, description="套餐ID")
    package_name: str = Field(..., description="套餐名称")
    package_type: str = Field(..., description="套餐类型")

    # 价格信息
    amount: float = Field(..., description="订单金额(元)")
    original_amount: Optional[float] = Field(None, description="原价")
    discount_amount: Optional[float] = Field(None, description="优惠金额")

    # 配额信息
    quotas: Dict[str, int] = Field(..., description="配额详情")
    validity_days: int = Field(..., description="有效期(天)")

    # 状态
    status: str = Field(..., description="订单状态")
    remark: Optional[str] = Field(None, description="订单备注")

    # 时间信息
    paid_at: Optional[datetime] = Field(None, description="支付时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    cancelled_at: Optional[datetime] = Field(None, description="取消时间")
    expired_at: Optional[datetime] = Field(None, description="过期时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class OrderListItemResponse(BaseModel):
    """订单列表项响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="订单ID")
    order_no: str = Field(..., description="订单号")
    package_name: str = Field(..., description="套餐名称")
    amount: float = Field(..., description="订单金额(元)")
    status: str = Field(..., description="订单状态")
    created_at: datetime = Field(..., description="创建时间")
