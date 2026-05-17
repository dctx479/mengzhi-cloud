"""
订单API路由

版本: 1.0
创建日期: 2026-01-23

端点:
- POST /api/v1/orders - 创建订单
- GET /api/v1/orders - 获取用户订单列表
- GET /api/v1/orders/{order_id} - 获取订单详情
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from loguru import logger
from typing import Optional

from app.schemas.orders import OrderCreateRequest, OrderDetailResponse, OrderListItemResponse
from app.schemas.payments import (
    PaymentCreateRequest,
    PaymentDetailResponse,
    PaymentStatusResponse,
    PaymentCallbackRequest,
)
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.core.errors import BusinessException, ErrorCode
from app.core.responses import success_response, error_response
from app.api.deps import get_db, get_current_user
from app.core.security import get_client_ip, verify_callback_ip
from app.core.config import settings
from app.models.user import User

# 创建路由器
router = APIRouter()


@router.post("/orders", response_model=dict, tags=["订单"])
async def create_order(
    request: OrderCreateRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
) -> dict:
    """创建订单

    路径: POST /api/v1/orders

    参数:
        request: 订单创建请求
        current_user: 当前登录用户

    返回:
        创建的订单信息
    """
    # P1-10: 移除重复的异常处理，由全局异常处理器统一处理
    service = OrderService(db)
    current_user_obj = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
    if not current_user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    order = service.create_order(request, current_user_obj.id)

    # 转换为响应对象
    response_data = {
        "id": order.id,
        "order_no": order.order_no,
        "user_id": order.user_id,
        "package_id": order.package_id,
        "package_name": order.package_name,
        "package_type": order.package_type,
        "amount": str(order.amount) if order.amount is not None else "0",
        "original_amount": str(order.original_amount) if order.original_amount is not None else None,
        "discount_amount": str(order.discount_amount) if order.discount_amount is not None else None,
        "quotas": {
            "chat": order.chat_quota,
            "generation": order.generation_quota,
            "token": order.token_quota,
            "storage_mb": order.storage_quota_mb,
        },
        "validity_days": order.validity_days,
        "status": order.status.value if hasattr(order.status, "value") else order.status,
        "remark": order.remark,
        "paid_at": order.paid_at,
        "completed_at": order.completed_at,
        "cancelled_at": order.cancelled_at,
        "expired_at": order.expired_at,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }

    return success_response(data=response_data, message="订单创建成功").dict()


@router.get("/orders", response_model=dict, tags=["订单"])
async def list_orders(
    status_filter: Optional[str] = Query(None, alias="status", description="订单状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """获取用户订单列表

    路径: GET /api/v1/orders

    参数:
        status: 订单状态筛选(pending/paid/completed/cancelled/expired)
        page: 页码
        size: 每页数量
        current_user: 当前登录用户

    返回:
        订单列表和总数
    """
    # P1-10: 移除重复的异常处理
    service = OrderService(db)
    current_user_obj = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
    if not current_user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    orders, total = service.get_user_orders(user_id=current_user_obj.id, status=status_filter, page=page, size=size)

    # 转换为响应对象
    items = []
    for order in orders:
        item_dict = {
            "id": order.id,
            "order_no": order.order_no,
            "package_name": order.package_name,
            "amount": str(order.amount) if order.amount is not None else "0",
            "status": order.status.value if hasattr(order.status, "value") else order.status,
            "created_at": order.created_at,
        }
        items.append(item_dict)

    return success_response(
        data={"items": items, "total": total, "page": page, "size": size}, message="获取订单列表成功"
    ).dict()


@router.get("/orders/{order_id}", response_model=dict, tags=["订单"])
async def get_order(
    order_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
) -> dict:
    """获取订单详情

    路径: GET /api/v1/orders/{order_id}

    参数:
        order_id: 订单ID
        current_user: 当前登录用户

    返回:
        订单详细信息
    """
    # P1-10: 移除重复的异常处理
    service = OrderService(db)
    order = service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 验证订单所有权
    current_user_obj = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
    if not current_user_obj or order.user_id != current_user_obj.id:
        raise BusinessException(code=ErrorCode.PERMISSION_DENIED, message="无权访问此订单")

    # 转换为响应对象
    response_data = {
        "id": order.id,
        "order_no": order.order_no,
        "user_id": order.user_id,
        "package_id": order.package_id,
        "package_name": order.package_name,
        "package_type": order.package_type,
        "amount": str(order.amount) if order.amount is not None else "0",
        "original_amount": str(order.original_amount) if order.original_amount is not None else None,
        "discount_amount": str(order.discount_amount) if order.discount_amount is not None else None,
        "quotas": {
            "chat": order.chat_quota,
            "generation": order.generation_quota,
            "token": order.token_quota,
            "storage_mb": order.storage_quota_mb,
        },
        "validity_days": order.validity_days,
        "status": order.status.value if hasattr(order.status, "value") else order.status,
        "remark": order.remark,
        "paid_at": order.paid_at,
        "completed_at": order.completed_at,
        "cancelled_at": order.cancelled_at,
        "expired_at": order.expired_at,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }

    return success_response(data=response_data, message="获取订单详情成功").dict()


@router.post("/orders/{order_id}/pay", response_model=dict, tags=["支付"])
async def create_payment(
    order_id: int,
    request: PaymentCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """创建支付

    路径: POST /api/v1/orders/{order_id}/pay

    参数:
        order_id: 订单ID
        request: 支付创建请求
        current_user: 当前登录用户

    返回:
        支付信息（包含支付二维码或跳转URL）
    """
    # P1-10: 移除重复的异常处理
    service = PaymentService(db)
    current_user_obj = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
    if not current_user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    payment = service.create_payment(order_id=order_id, payment_method=request.payment_method, user_id=current_user_obj.id)

    # 转换为响应对象
    response_data = {
        "id": payment.id,
        "payment_no": payment.payment_no,
        "order_id": payment.order_id,
        "amount": str(payment.amount) if payment.amount is not None else "0",
        "payment_method": (
            payment.payment_method.value if hasattr(payment.payment_method, "value") else payment.payment_method
        ),
        "status": payment.status.value if hasattr(payment.status, "value") else payment.status,
        "transaction_id": payment.transaction_id,
        "paid_at": payment.paid_at,
        "failed_at": payment.failed_at,
        "failure_reason": payment.failure_reason,
        "created_at": payment.created_at,
        "qr_code": None,  # TODO: 生产环境返回真实二维码
        "pay_url": None,  # TODO: 生产环境返回真实跳转URL
    }

    return success_response(data=response_data, message="支付创建成功").dict()


@router.get("/orders/{order_id}/payment-status", response_model=dict, tags=["支付"])
async def get_payment_status(
    order_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
) -> dict:
    """查询支付状态

    路径: GET /api/v1/orders/{order_id}/payment-status

    参数:
        order_id: 订单ID
        current_user: 当前登录用户

    返回:
        支付状态信息
    """
    # P1-10: 移除重复的异常处理
    service = PaymentService(db)
    current_user_obj = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
    if not current_user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    payment_status = service.get_payment_status(order_id, current_user_obj.id)

    return success_response(data=payment_status, message="查询支付状态成功").dict()


@router.post("/orders/{order_id}/payment-callback", response_model=dict, tags=["支付"])
async def payment_callback(
    order_id: int, request: PaymentCallbackRequest, http_request: Request, db: Session = Depends(get_db)
) -> dict:
    """支付回调

    路径: POST /api/v1/orders/{order_id}/payment-callback

    参数:
        order_id: 订单ID
        request: 支付回调请求
        http_request: HTTP请求对象（用于IP验证）

    返回:
        处理结果

    注意:
        此接口由支付平台回调，不需要用户认证
        但需要验证回调来源IP是否在白名单中
    """
    # P0-2: 验证回调IP
    client_ip = get_client_ip(http_request)
    logger.info(f"收到支付回调: order_id={order_id}, payment_no={request.payment_no}, ip={client_ip}")

    # 根据支付方式选择IP白名单
    # 注意：这里简化处理，实际应该从payment_no查询支付方式
    # 为了安全，我们同时检查支付宝和微信的IP白名单
    allowed_ips = list(set(settings.ALIPAY_CALLBACK_IPS + settings.WECHAT_CALLBACK_IPS))

    if not verify_callback_ip(http_request, allowed_ips):
        logger.error(f"支付回调IP验证失败: ip={client_ip}, order_id={order_id}")
        raise BusinessException(code=ErrorCode.PERMISSION_DENIED, message="IP地址未授权")

    # 处理支付回调
    service = PaymentService(db)
    success = service.handle_payment_callback(payment_no=request.payment_no, callback_data=request.callback_data)

    if success:
        logger.info(f"支付回调处理成功: payment_no={request.payment_no}")
        return success_response(data={"processed": True}, message="回调处理成功").dict()
    else:
        logger.warning(f"支付回调处理失败: payment_no={request.payment_no}")
        raise BusinessException(code=ErrorCode.INVALID_OPERATION, message="回调处理失败")


@router.post("/orders/{order_id}/cancel", response_model=dict, tags=["订单"])
async def cancel_order(
    order_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
) -> dict:
    """取消订单

    路径: POST /api/v1/orders/{order_id}/cancel

    参数:
        order_id: 订单ID
        current_user: 当前登录用户

    返回:
        取消结果

    注意:
        只有待支付(pending)或支付失败(failed)状态的订单才能取消
    """
    from app.models.order import Order

    current_user_obj = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
    if not current_user_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user_obj.id, Order.deleted_at.is_(None))
        .first()
    )

    if not order:
        raise BusinessException(code=ErrorCode.RECORD_NOT_FOUND, message="订单不存在")

    if not order.can_cancel():
        raise BusinessException(code=ErrorCode.INVALID_OPERATION, message="只有待支付或支付失败的订单才能取消")

    order.mark_as_cancelled()
    db.commit()
    db.refresh(order)

    logger.info(f"订单已取消: order_id={order_id}, user_id={current_user_obj.id}")
    return success_response(data={"order_id": order_id, "status": "cancelled"}, message="订单已取消").dict()
