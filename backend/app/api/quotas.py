"""
配额管理API - Quota Management API

提供配额管理的HTTP接口：
- 查询配额
- 设置配额（管理员）
- 使用统计
- 手动重置（管理员）

版本: 1.0
更新日期: 2026-01-22
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import date

from app.api.deps import get_db, get_current_user, require_admin, require_enterprise_admin
from app.services.quota_service import QuotaService
from app.models.quota import QuotaResourceType, QuotaPeriodType, QuotaAlertLevel
from app.models.user import User
from app.core.errors import BusinessException


router = APIRouter(tags=["配额管理"])


# ==================== Pydantic模型 ====================

class QuotaResponse(BaseModel):
    """配额响应模型"""
    id: int
    enterprise_id: Optional[int]
    user_id: Optional[int]
    resource_type: str
    period_type: str
    quota_limit: int
    quota_used: int
    quota_remaining: int
    usage_percentage: float
    period: dict
    thresholds: dict
    alert: dict
    is_active: bool
    description: Optional[str]
    created_at: str
    updated_at: str


class QuotaCreateRequest(BaseModel):
    """创建配额请求模型"""
    enterprise_id: Optional[int] = Field(None, description="企业ID（企业配额）")
    user_id: Optional[int] = Field(None, description="用户ID（个人配额）")
    resource_type: str = Field(..., description="资源类型: token, message, api_call, generation, storage")
    period_type: str = Field(..., description="周期类型: daily, monthly, yearly, total")
    quota_limit: int = Field(..., gt=0, description="配额限制")
    start_date: Optional[str] = Field(None, description="开始日期 (YYYY-MM-DD)")
    warning_threshold: int = Field(80, ge=0, le=100, description="预警阈值（百分比）")
    critical_threshold: int = Field(90, ge=0, le=100, description="严重预警阈值（百分比）")
    description: Optional[str] = Field(None, description="配额描述")


class QuotaUpdateRequest(BaseModel):
    """更新配额请求模型"""
    quota_limit: Optional[int] = Field(None, gt=0, description="配额限制")
    warning_threshold: Optional[int] = Field(None, ge=0, le=100, description="预警阈值")
    critical_threshold: Optional[int] = Field(None, ge=0, le=100, description="严重预警阈值")
    is_active: Optional[bool] = Field(None, description="是否启用")
    description: Optional[str] = Field(None, description="配额描述")


class QuotaUsageResponse(BaseModel):
    """配额使用记录响应模型"""
    id: int
    quota_id: int
    amount: int
    operation: Optional[str]
    resource_id: Optional[str]
    resource_type: Optional[str]
    metadata: Optional[str]
    used_at: str
    created_at: str


class QuotaStatisticsResponse(BaseModel):
    """配额统计响应模型"""
    total_quotas: int
    by_resource_type: dict
    by_period_type: dict
    alerts: dict
    total_usage: int
    total_limit: int


# ==================== API端点 ====================

@router.get("/", response_model=dict)
async def list_quotas(
    enterprise_id: Optional[int] = Query(None, description="企业ID"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    period_type: Optional[str] = Query(None, description="周期类型"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    查询配额列表

    权限：
    - 管理员：可查询所有配额
    - 企业管理员：可查询本企业配额
    - 普通用户：只能查询自己的配额
    """
    service = QuotaService(db)

    # 权限检查
    if current_user["role"] != "admin":
        # 非管理员只能查询自己的配额
        user = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        if current_user["role"] == "enterprise_admin":
            # 企业管理员查询企业配额
            if not user.enterprise_id:
                raise HTTPException(status_code=403, detail="非企业用户")
            enterprise_id = user.enterprise_id
            user_id = None
        else:
            # 普通用户查询个人配额
            enterprise_id = None
            user_id = user.id

    # 转换枚举
    resource_type_enum = None
    if resource_type:
        try:
            resource_type_enum = QuotaResourceType(resource_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的资源类型")

    period_type_enum = None
    if period_type:
        try:
            period_type_enum = QuotaPeriodType(period_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的周期类型")

    # 查询配额
    quotas, total = service.list_quotas(
        enterprise_id=enterprise_id,
        user_id=user_id,
        resource_type=resource_type_enum,
        period_type=period_type_enum,
        is_active=is_active,
        page=page,
        page_size=page_size
    )

    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "items": [quota.to_dict() for quota in quotas],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/statistics/summary", response_model=dict)
async def get_quota_statistics(
    enterprise_id: Optional[int] = Query(None, description="企业ID"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取配额统计信息

    权限：
    - 管理员：可查询所有统计
    - 企业管理员：可查询本企业统计
    - 普通用户：只能查询自己的统计
    """
    service = QuotaService(db)

    # 权限检查
    if current_user["role"] != "admin":
        user = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        if current_user["role"] == "enterprise_admin":
            if not user.enterprise_id:
                raise HTTPException(status_code=403, detail="非企业用户")
            enterprise_id = user.enterprise_id
            user_id = None
        else:
            enterprise_id = None
            user_id = user.id

    # 获取统计信息
    statistics = service.get_quota_statistics(
        enterprise_id=enterprise_id,
        user_id=user_id
    )

    return {
        "code": 200,
        "message": "查询成功",
        "data": statistics
    }


@router.post("/batch-reset", response_model=dict)
async def batch_reset_expired_quotas(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    批量重置过期配额（管理员）

    权限：仅管理员
    说明：用于定时任务或手动触发
    """
    service = QuotaService(db)

    count = service.reset_expired_quotas()

    return {
        "code": 200,
        "message": f"批量重置成功，共重置 {count} 个配额",
        "data": {"count": count}
    }


@router.get("/{quota_id}", response_model=dict)
async def get_quota(
    quota_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取配额详情

    权限：
    - 管理员：可查询所有配额
    - 企业管理员：可查询本企业配额
    - 普通用户：只能查询自己的配额
    """
    service = QuotaService(db)
    quota = service.get_quota(quota_id)

    if not quota:
        raise HTTPException(status_code=404, detail="配额不存在")

    # 权限检查
    if current_user["role"] != "admin":
        user = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        if current_user["role"] == "enterprise_admin":
            # 企业管理员只能查询本企业配额
            if quota.enterprise_id != user.enterprise_id:
                raise HTTPException(status_code=403, detail="权限不足")
        else:
            # 普通用户只能查询自己的配额
            if quota.user_id != user.id:
                raise HTTPException(status_code=403, detail="权限不足")

    return {
        "code": 200,
        "message": "查询成功",
        "data": quota.to_dict()
    }


@router.post("/", response_model=dict)
async def create_quota(
    request: QuotaCreateRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    创建配额（管理员）

    权限：仅管理员
    """
    service = QuotaService(db)

    # 验证参数
    if not request.enterprise_id and not request.user_id:
        raise HTTPException(status_code=400, detail="必须指定 enterprise_id 或 user_id")

    if request.enterprise_id and request.user_id:
        raise HTTPException(status_code=400, detail="不能同时指定 enterprise_id 和 user_id")

    # 转换枚举
    try:
        resource_type = QuotaResourceType(request.resource_type)
        period_type = QuotaPeriodType(request.period_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"无效的参数: {e}")

    # 解析日期
    start_date = None
    if request.start_date:
        try:
            start_date = date.fromisoformat(request.start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的日期格式")

    # 创建配额
    try:
        quota = service.create_quota(
            resource_type=resource_type,
            period_type=period_type,
            quota_limit=request.quota_limit,
            enterprise_id=request.enterprise_id,
            user_id=request.user_id,
            start_date=start_date,
            warning_threshold=request.warning_threshold,
            critical_threshold=request.critical_threshold,
            description=request.description
        )

        return {
            "code": 200,
            "message": "创建成功",
            "data": quota.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建失败")


@router.put("/{quota_id}", response_model=dict)
async def update_quota(
    quota_id: int,
    request: QuotaUpdateRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    更新配额（管理员）

    权限：仅管理员
    """
    service = QuotaService(db)

    quota = service.update_quota(
        quota_id=quota_id,
        quota_limit=request.quota_limit,
        warning_threshold=request.warning_threshold,
        critical_threshold=request.critical_threshold,
        is_active=request.is_active,
        description=request.description
    )

    if not quota:
        raise HTTPException(status_code=404, detail="配额不存在")

    return {
        "code": 200,
        "message": "更新成功",
        "data": quota.to_dict()
    }


@router.delete("/{quota_id}", response_model=dict)
async def delete_quota(
    quota_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    删除配额（管理员）

    权限：仅管理员
    """
    service = QuotaService(db)

    success = service.delete_quota(quota_id)

    if not success:
        raise HTTPException(status_code=404, detail="配额不存在")

    return {
        "code": 200,
        "message": "删除成功",
        "data": None
    }


@router.post("/{quota_id}/reset", response_model=dict)
async def reset_quota(
    quota_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    手动重置配额（管理员）

    权限：仅管理员
    """
    service = QuotaService(db)

    success = service.reset_quota(quota_id)

    if not success:
        raise HTTPException(status_code=404, detail="配额不存在")

    return {
        "code": 200,
        "message": "重置成功"
    }


@router.get("/{quota_id}/usage", response_model=dict)
async def get_quota_usage(
    quota_id: int,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    operation: Optional[str] = Query(None, description="操作类型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取配额使用记录

    权限：
    - 管理员：可查询所有配额
    - 企业管理员：可查询本企业配额
    - 普通用户：只能查询自己的配额
    """
    service = QuotaService(db)

    # 获取配额并检查权限
    quota = service.get_quota(quota_id)
    if not quota:
        raise HTTPException(status_code=404, detail="配额不存在")

    # 权限检查
    if current_user["role"] != "admin":
        user = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        if current_user["role"] == "enterprise_admin":
            if quota.enterprise_id != user.enterprise_id:
                raise HTTPException(status_code=403, detail="权限不足")
        else:
            if quota.user_id != user.id:
                raise HTTPException(status_code=403, detail="权限不足")

    # 解析日期
    start_date_obj = None
    end_date_obj = None
    if start_date:
        try:
            start_date_obj = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的开始日期格式")
    if end_date:
        try:
            end_date_obj = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的结束日期格式")

    # 查询使用记录
    records, total = service.get_quota_usage_records(
        quota_id=quota_id,
        start_date=start_date_obj,
        end_date=end_date_obj,
        operation=operation,
        page=page,
        page_size=page_size
    )

    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "items": [record.to_dict() for record in records],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }
