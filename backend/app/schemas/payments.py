"""
支付Schema (Pydantic)

版本: 1.0
创建日期: 2026-01-23
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


# ============ 请求Schema ============

class PaymentCreateRequest(BaseModel):
    """支付创建请求"""

    order_id: int = Field(..., description="订单ID")
    payment_method: str = Field(..., description="支付方式(alipay/wechat/balance)")

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": 1,
                "payment_method": "alipay"
            }
        }


class PaymentCallbackRequest(BaseModel):
    """支付回调请求"""

    payment_no: str = Field(..., description="支付单号")
    transaction_id: Optional[str] = Field(None, description="第三方交易号")
    callback_data: Dict[str, Any] = Field(..., description="回调数据")

    class Config:
        json_schema_extra = {
            "example": {
                "payment_no": "PAY20260123001",
                "transaction_id": "2026012322001234567890",
                "callback_data": {
                    "trade_status": "TRADE_SUCCESS",
                    "total_amount": "99.00"
                }
            }
        }


# ============ 响应Schema ============

class PaymentDetailResponse(BaseModel):
    """支付详情响应"""

    id: int = Field(..., description="支付ID")
    payment_no: str = Field(..., description="支付单号")
    order_id: int = Field(..., description="订单ID")
    amount: float = Field(..., description="支付金额(元)")
    payment_method: str = Field(..., description="支付方式")
    status: str = Field(..., description="支付状态")
    transaction_id: Optional[str] = Field(None, description="第三方交易号")
    paid_at: Optional[datetime] = Field(None, description="支付成功时间")
    failed_at: Optional[datetime] = Field(None, description="支付失败时间")
    failure_reason: Optional[str] = Field(None, description="失败原因")
    created_at: datetime = Field(..., description="创建时间")

    # 支付二维码或跳转URL（仅在创建时返回）
    qr_code: Optional[str] = Field(None, description="支付二维码")
    pay_url: Optional[str] = Field(None, description="支付跳转URL")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "payment_no": "PAY20260123001",
                "order_id": 1,
                "amount": 99.00,
                "payment_method": "alipay",
                "status": "pending",
                "transaction_id": None,
                "paid_at": None,
                "failed_at": None,
                "failure_reason": None,
                "created_at": "2026-01-23T10:00:00",
                "qr_code": "https://qr.alipay.com/xxx",
                "pay_url": "https://openapi.alipay.com/gateway.do?xxx"
            }
        }


class PaymentStatusResponse(BaseModel):
    """支付状态响应"""

    order_id: int = Field(..., description="订单ID")
    order_status: str = Field(..., description="订单状态")
    payment_id: Optional[int] = Field(None, description="支付ID")
    payment_no: Optional[str] = Field(None, description="支付单号")
    payment_method: Optional[str] = Field(None, description="支付方式")
    payment_status: Optional[str] = Field(None, description="支付状态")
    amount: Optional[float] = Field(None, description="支付金额")
    paid: bool = Field(..., description="是否已支付")
    paid_at: Optional[str] = Field(None, description="支付时间")
    transaction_id: Optional[str] = Field(None, description="第三方交易号")

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": 1,
                "order_status": "completed",
                "payment_id": 1,
                "payment_no": "PAY20260123001",
                "payment_method": "alipay",
                "payment_status": "success",
                "amount": 99.00,
                "paid": True,
                "paid_at": "2026-01-23T10:05:00",
                "transaction_id": "2026012322001234567890"
            }
        }
