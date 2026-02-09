"""
计费系统API路由

版本: 1.0
更新日期: 2026-01-22

包含端点:
1. GET /api/v1/billing/plans - 获取计费方案列表
2. POST /api/v1/billing/plans - 创建计费方案（管理员）
3. GET /api/v1/billing/plans/{plan_id} - 获取计费方案详情
4. PUT /api/v1/billing/plans/{plan_id} - 更新计费方案（管理员）
5. DELETE /api/v1/billing/plans/{plan_id} - 删除计费方案（管理员）
6. POST /api/v1/billing/plans/{plan_id}/set-default - 设置默认方案（管理员）
7. GET /api/v1/billing/records - 获取计费记录
8. GET /api/v1/billing/records/statistics - 获取计费统计
9. GET /api/v1/billing/invoices - 获取账单列表
10. GET /api/v1/billing/invoices/{invoice_id} - 获取账单详情
11. POST /api/v1/billing/invoices/{invoice_id}/pay - 支付账单
12. POST /api/v1/billing/invoices/generate - 生成账单（管理员）
"""

from fastapi import APIRouter, Depends, status, Query, Path
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.core.responses import APIResponse, success_response, error_response
from app.core.errors import BusinessException, ErrorCode
from app.api.deps import get_db, get_current_user, require_admin
from app.services.billing_engine import BillingEngine, BillingPlanManager
from app.models.billing import BillingMode, InvoiceStatus, PaymentMethod
from app.models.user import User
from pydantic import BaseModel, Field, validator


# ==================== Pydantic Schemas ====================

class BillingPlanCreate(BaseModel):
    """创建计费方案请求"""
    name: str = Field(..., description="方案名称")
    description: Optional[str] = Field(None, description="方案描述")
    billing_mode: str = Field(..., description="计费模式: token/message/api_call/monthly/tiered")
    pricing_type: str = Field(..., description="定价类型: fixed/unit/tiered")
    pricing_rules: dict = Field(..., description="定价规则配置")
    quota_limits: Optional[dict] = Field(None, description="配额限制配置")
    is_active: bool = Field(True, description="是否启用")
    is_default: bool = Field(False, description="是否为默认方案")
    applicable_to: Optional[str] = Field("all", description="适用对象: all/personal/enterprise")
    valid_from: Optional[date] = Field(None, description="生效日期")
    valid_until: Optional[date] = Field(None, description="失效日期")
    sort_order: int = Field(0, description="排序顺序")


class BillingPlanUpdate(BaseModel):
    """更新计费方案请求"""
    name: Optional[str] = Field(None, description="方案名称")
    description: Optional[str] = Field(None, description="方案描述")
    pricing_rules: Optional[dict] = Field(None, description="定价规则配置")
    quota_limits: Optional[dict] = Field(None, description="配额限制配置")
    is_active: Optional[bool] = Field(None, description="是否启用")
    applicable_to: Optional[str] = Field(None, description="适用对象")
    valid_from: Optional[date] = Field(None, description="生效日期")
    valid_until: Optional[date] = Field(None, description="失效日期")
    sort_order: Optional[int] = Field(None, description="排序顺序")


class PayInvoiceRequest(BaseModel):
    """支付账单请求"""
    payment_method: str = Field(..., description="支付方式: wechat/alipay/bank/balance/other")
    transaction_id: Optional[str] = Field(None, description="交易ID")


class GenerateInvoiceRequest(BaseModel):
    """生成账单请求"""
    user_id: int = Field(..., description="用户ID")
    period_start: date = Field(..., description="账单周期开始日期")
    period_end: date = Field(..., description="账单周期结束日期")
    due_days: int = Field(7, description="到期天数")


# 创建路由
router = APIRouter()


# ==================== 计费方案管理 ====================

@router.get(
    "/plans",
    response_model=APIResponse,
    summary="获取计费方案列表",
    description="获取所有可用的计费方案",
    tags=["计费系统"]
)
async def get_billing_plans(
    is_active: Optional[bool] = Query(None, description="是否启用"),
    billing_mode: Optional[str] = Query(None, description="计费模式"),
    applicable_to: Optional[str] = Query(None, description="适用对象"),
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    获取计费方案列表

    参数:
        is_active: 是否启用（可选）
        billing_mode: 计费模式（可选）
        applicable_to: 适用对象（可选）

    返回:
        计费方案列表
    """
    try:
        manager = BillingPlanManager(db)

        # 转换billing_mode为枚举
        mode_enum = None
        if billing_mode:
            try:
                mode_enum = BillingMode(billing_mode)
            except ValueError:
                return error_response(
                    code=ErrorCode.VALIDATION_ERROR,
                    message=f"无效的计费模式: {billing_mode}"
                )

        plans = manager.get_plans(
            is_active=is_active,
            billing_mode=mode_enum,
            applicable_to=applicable_to
        )

        return success_response(
            data=[plan.to_dict() for plan in plans],
            message="获取计费方案列表成功"
        )

    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取计费方案列表失败: {str(e)}"
        )


@router.post(
    "/plans",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建计费方案",
    description="创建新的计费方案（管理员）",
    tags=["计费系统"]
)
async def create_billing_plan(
    request: BillingPlanCreate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    创建计费方案（管理员）

    参数:
        request: 计费方案数据

    返回:
        创建的计费方案
    """
    try:
        manager = BillingPlanManager(db)

        # 转换枚举
        try:
            billing_mode = BillingMode(request.billing_mode)
        except ValueError:
            return error_response(
                code=ErrorCode.VALIDATION_ERROR,
                message=f"无效的计费模式: {request.billing_mode}"
            )

        # 准备数据
        plan_data = request.dict()
        plan_data["billing_mode"] = billing_mode

        # 创建方案
        plan = manager.create_plan(plan_data)

        return success_response(
            data=plan.to_dict(),
            message="创建计费方案成功"
        )

    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"创建计费方案失败: {str(e)}"
        )


@router.get(
    "/plans/{plan_id}",
    response_model=APIResponse,
    summary="获取计费方案详情",
    description="获取指定计费方案的详细信息",
    tags=["计费系统"]
)
async def get_billing_plan(
    plan_id: int = Path(..., description="方案ID"),
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    获取计费方案详情

    参数:
        plan_id: 方案ID

    返回:
        计费方案详情
    """
    try:
        manager = BillingPlanManager(db)
        plan = manager.get_plan(plan_id)

        if not plan:
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message=f"计费方案不存在: {plan_id}"
            )

        return success_response(
            data=plan.to_dict(),
            message="获取计费方案详情成功"
        )

    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取计费方案详情失败: {str(e)}"
        )


@router.put(
    "/plans/{plan_id}",
    response_model=APIResponse,
    summary="更新计费方案",
    description="更新指定计费方案（管理员）",
    tags=["计费系统"]
)
async def update_billing_plan(
    plan_id: int = Path(..., description="方案ID"),
    request: BillingPlanUpdate = ...,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    更新计费方案（管理员）

    参数:
        plan_id: 方案ID
        request: 更新数据

    返回:
        更新后的计费方案
    """
    try:
        manager = BillingPlanManager(db)

        # 准备更新数据（排除None值）
        update_data = {k: v for k, v in request.dict().items() if v is not None}

        # 更新方案
        plan = manager.update_plan(plan_id, update_data)

        return success_response(
            data=plan.to_dict(),
            message="更新计费方案成功"
        )

    except ValueError as e:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message=str(e)
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"更新计费方案失败: {str(e)}"
        )


@router.delete(
    "/plans/{plan_id}",
    response_model=APIResponse,
    summary="删除计费方案",
    description="删除指定计费方案（管理员）",
    tags=["计费系统"]
)
async def delete_billing_plan(
    plan_id: int = Path(..., description="方案ID"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    删除计费方案（管理员）

    参数:
        plan_id: 方案ID

    返回:
        删除结果
    """
    try:
        manager = BillingPlanManager(db)
        success = manager.delete_plan(plan_id)

        if not success:
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message=f"计费方案不存在: {plan_id}"
            )

        return success_response(
            data={"plan_id": plan_id},
            message="删除计费方案成功"
        )

    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"删除计费方案失败: {str(e)}"
        )


@router.post(
    "/plans/{plan_id}/set-default",
    response_model=APIResponse,
    summary="设置默认方案",
    description="设置指定方案为默认方案（管理员）",
    tags=["计费系统"]
)
async def set_default_plan(
    plan_id: int = Path(..., description="方案ID"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    设置默认方案（管理员）

    参数:
        plan_id: 方案ID

    返回:
        设置后的方案
    """
    try:
        manager = BillingPlanManager(db)
        plan = manager.set_default_plan(plan_id)

        return success_response(
            data=plan.to_dict(),
            message="设置默认方案成功"
        )

    except ValueError as e:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message=str(e)
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"设置默认方案失败: {str(e)}"
        )


# ==================== 计费记录查询 ====================

@router.get(
    "/records",
    response_model=APIResponse,
    summary="获取计费记录",
    description="获取当前用户的计费记录",
    tags=["计费系统"]
)
async def get_billing_records(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    billing_mode: Optional[str] = Query(None, description="计费模式"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    获取计费记录

    参数:
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
        billing_mode: 计费模式（可选）
        page: 页码
        page_size: 每页数量

    返回:
        计费记录列表
    """
    try:
        # 获取用户ID
        user = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
        if not user:
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message="用户不存在"
            )

        engine = BillingEngine(db)

        # 转换billing_mode为枚举
        mode_enum = None
        if billing_mode:
            try:
                mode_enum = BillingMode(billing_mode)
            except ValueError:
                return error_response(
                    code=ErrorCode.VALIDATION_ERROR,
                    message=f"无效的计费模式: {billing_mode}"
                )

        # 计算偏移量
        offset = (page - 1) * page_size

        # 获取记录
        records, total = engine.get_user_billing_records(
            user_id=user.id,
            start_date=start_date,
            end_date=end_date,
            billing_mode=mode_enum,
            limit=page_size,
            offset=offset
        )

        return success_response(
            data={
                "records": [record.to_dict() for record in records],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            },
            message="获取计费记录成功"
        )

    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取计费记录失败: {str(e)}"
        )


@router.get(
    "/records/statistics",
    response_model=APIResponse,
    summary="获取计费统计",
    description="获取当前用户的计费统计信息",
    tags=["计费系统"]
)
async def get_billing_statistics(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    获取计费统计

    参数:
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）

    返回:
        计费统计信息
    """
    try:
        # 获取用户ID
        user = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
        if not user:
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message="用户不存在"
            )

        engine = BillingEngine(db)

        # 获取统计信息
        statistics = engine.get_billing_statistics(
            user_id=user.id,
            start_date=start_date,
            end_date=end_date
        )

        return success_response(
            data=statistics,
            message="获取计费统计成功"
        )

    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取计费统计失败: {str(e)}"
        )


# ==================== 账单管理 ====================

@router.get(
    "/invoices",
    response_model=APIResponse,
    summary="获取账单列表",
    description="获取当前用户的账单列表",
    tags=["计费系统"]
)
async def get_invoices(
    status: Optional[str] = Query(None, description="账单状态: pending/paid/overdue/cancelled/refunded"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    获取账单列表

    参数:
        status: 账单状态（可选）
        page: 页码
        page_size: 每页数量

    返回:
        账单列表
    """
    try:
        # 获取用户ID
        user = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
        if not user:
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message="用户不存在"
            )

        engine = BillingEngine(db)

        # 转换status为枚举
        status_enum = None
        if status:
            try:
                status_enum = InvoiceStatus(status)
            except ValueError:
                return error_response(
                    code=ErrorCode.VALIDATION_ERROR,
                    message=f"无效的账单状态: {status}"
                )

        # 计算偏移量
        offset = (page - 1) * page_size

        # 获取账单
        invoices, total = engine.get_user_invoices(
            user_id=user.id,
            status=status_enum,
            limit=page_size,
            offset=offset
        )

        return success_response(
            data={
                "invoices": [invoice.to_dict() for invoice in invoices],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            },
            message="获取账单列表成功"
        )

    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取账单列表失败: {str(e)}"
        )


@router.get(
    "/invoices/{invoice_id}",
    response_model=APIResponse,
    summary="获取账单详情",
    description="获取指定账单的详细信息",
    tags=["计费系统"]
)
async def get_invoice(
    invoice_id: int = Path(..., description="账单ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    获取账单详情

    参数:
        invoice_id: 账单ID

    返回:
        账单详情
    """
    try:
        from app.models.billing import Invoice

        # 获取用户ID
        user = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
        if not user:
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message="用户不存在"
            )

        # 获取账单
        invoice = db.query(Invoice).filter(
            Invoice.id == invoice_id,
            Invoice.user_id == user.id
        ).first()

        if not invoice:
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message=f"账单不存在: {invoice_id}"
            )

        # 获取账单详情（包含计费记录）
        invoice_data = invoice.to_dict()
        invoice_data["records"] = [record.to_dict() for record in invoice.records]

        return success_response(
            data=invoice_data,
            message="获取账单详情成功"
        )

    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取账单详情失败: {str(e)}"
        )


@router.post(
    "/invoices/{invoice_id}/pay",
    response_model=APIResponse,
    summary="支付账单",
    description="支付指定账单",
    tags=["计费系统"]
)
async def pay_invoice(
    invoice_id: int = Path(..., description="账单ID"),
    request: PayInvoiceRequest = ...,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    支付账单

    参数:
        invoice_id: 账单ID
        request: 支付信息

    返回:
        支付后的账单
    """
    try:
        from app.models.billing import Invoice

        # 获取用户ID
        user = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
        if not user:
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message="用户不存在"
            )

        # 验证账单所有权
        invoice = db.query(Invoice).filter(
            Invoice.id == invoice_id,
            Invoice.user_id == user.id
        ).first()

        if not invoice:
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message=f"账单不存在: {invoice_id}"
            )

        # 转换支付方式为枚举
        try:
            payment_method = PaymentMethod(request.payment_method)
        except ValueError:
            return error_response(
                code=ErrorCode.VALIDATION_ERROR,
                message=f"无效的支付方式: {request.payment_method}"
            )

        # 支付账单
        engine = BillingEngine(db)
        invoice = engine.pay_invoice(
            invoice_id=invoice_id,
            payment_method=payment_method,
            transaction_id=request.transaction_id
        )

        return success_response(
            data=invoice.to_dict(),
            message="支付账单成功"
        )

    except ValueError as e:
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message=str(e)
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"支付账单失败: {str(e)}"
        )


@router.post(
    "/invoices/generate",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="生成账单",
    description="为指定用户生成账单（管理员）",
    tags=["计费系统"]
)
async def generate_invoice(
    request: GenerateInvoiceRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    生成账单（管理员）

    参数:
        request: 生成账单请求

    返回:
        生成的账单
    """
    try:
        engine = BillingEngine(db)

        # 生成账单
        invoice = engine.generate_invoice(
            user_id=request.user_id,
            period_start=request.period_start,
            period_end=request.period_end,
            due_days=request.due_days
        )

        return success_response(
            data=invoice.to_dict(),
            message="生成账单成功"
        )

    except ValueError as e:
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message=str(e)
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"生成账单失败: {str(e)}"
        )
