"""
管理员API路由

版本: 1.0
更新日期: 2026-01-22

包含端点:
1. GET /api/admin/users - 用户列表（分页、搜索）
2. PATCH /api/admin/users/{id} - 更新用户（状态、角色）
3. DELETE /api/admin/users/{id} - 删除用户
4. GET /api/admin/enterprises - 企业列表
5. PATCH /api/admin/enterprises/{id} - 更新企业（状态、套餐）
6. DELETE /api/admin/enterprises/{id} - 删除企业
7. GET /api/admin/stats - 平台统计
8. GET /api/admin/ai-usage - AI使用统计
"""

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import Optional
from datetime import datetime, timedelta

from app.core.responses import APIResponse
from app.core.errors import ErrorCode, ERROR_MESSAGES, BusinessException
from app.api.deps import get_db, require_admin
from app.models import User, Enterprise, Message, ContentRecord, SystemConfig

router = APIRouter()


# ==================== 1. 用户列表 ====================


@router.get("/users", response_model=APIResponse, summary="获取用户列表", tags=["管理员"])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    user_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
) -> APIResponse:
    """获取用户列表（分页、搜索、筛选）"""
    try:
        query = db.query(User).filter(User.deleted_at.is_(None))

        # 搜索（使用 contains 避免 SQL 注入）
        if search:
            safe_search = search.replace("%", "\\%").replace("_", "\\_")
            query = query.filter(
                (User.username.like(f"%{safe_search}%"))
                | (User.email.like(f"%{safe_search}%"))
                | (User.phone.like(f"%{safe_search}%"))
            )

        # 筛选
        if user_type:
            query = query.filter(User.user_type == user_type)
        if status:
            query = query.filter(User.status == status)

        # 总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()

        return APIResponse(
            code=200,
            message="success",
            data={"items": [u.to_dict() for u in users], "total": total, "page": page, "page_size": page_size},
        )
    except Exception as e:
        return APIResponse(code=ErrorCode.SYSTEM_ERROR, message=str(e), data=None)


# ==================== 2. 更新用户 ====================


@router.patch("/users/{user_id}", response_model=APIResponse, summary="更新用户", tags=["管理员"])
async def update_user(
    user_id: int,
    status: Optional[str] = None,
    role: Optional[str] = None,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
) -> APIResponse:
    """更新用户状态或角色"""
    try:
        user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        if not user:
            return APIResponse(code=404, message="用户不存在", data=None)

        if status:
            user.status = status
        if role:
            from app.models.user import UserRole
            valid_roles = [r.value for r in UserRole]
            if role not in valid_roles:
                return APIResponse(code=400, message=f"无效的角色值，允许的值: {', '.join(valid_roles)}", data=None)
            user.role = role

        user.updated_at = datetime.utcnow()
        db.commit()

        return APIResponse(code=200, message="更新成功", data=user.to_dict())
    except Exception as e:
        db.rollback()
        return APIResponse(code=ErrorCode.SYSTEM_ERROR, message=str(e), data=None)


# ==================== 3. 删除用户 ====================


@router.delete("/users/{user_id}", response_model=APIResponse, summary="删除用户", tags=["管理员"])
async def delete_user(
    user_id: int, current_user: dict = Depends(require_admin), db: Session = Depends(get_db)
) -> APIResponse:
    """软删除用户"""
    try:
        user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        if not user:
            return APIResponse(code=404, message="用户不存在", data=None)

        user.deleted_at = datetime.utcnow()
        db.commit()

        return APIResponse(code=200, message="删除成功", data={"id": user_id})
    except Exception as e:
        db.rollback()
        return APIResponse(code=ErrorCode.SYSTEM_ERROR, message=str(e), data=None)


# ==================== 4. 企业列表 ====================


@router.get("/enterprises", response_model=APIResponse, summary="获取企业列表", tags=["管理员"])
async def list_enterprises(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    verify_status: Optional[str] = None,
    plan_type: Optional[str] = None,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
) -> APIResponse:
    """获取企业列表（分页、搜索、筛选）"""
    try:
        query = db.query(Enterprise).filter(Enterprise.deleted_at.is_(None))

        # 搜索（转义 LIKE 特殊字符）
        if search:
            safe_search = search.replace("%", "\\%").replace("_", "\\_")
            query = query.filter(
                (Enterprise.name.like(f"%{safe_search}%")) | (Enterprise.license_no.like(f"%{safe_search}%"))
            )

        # 筛选
        if verify_status:
            query = query.filter(Enterprise.verify_status == verify_status)
        if plan_type:
            query = query.filter(Enterprise.plan_type == plan_type)

        # 总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        enterprises = query.order_by(Enterprise.created_at.desc()).offset(offset).limit(page_size).all()

        return APIResponse(
            code=200,
            message="success",
            data={"items": [e.to_dict() for e in enterprises], "total": total, "page": page, "page_size": page_size},
        )
    except Exception as e:
        return APIResponse(code=ErrorCode.SYSTEM_ERROR, message=str(e), data=None)


# ==================== 5. 更新企业 ====================


@router.patch("/enterprises/{enterprise_id}", response_model=APIResponse, summary="更新企业", tags=["管理员"])
async def update_enterprise(
    enterprise_id: int,
    verify_status: Optional[str] = None,
    plan_type: Optional[str] = None,
    reject_reason: Optional[str] = None,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
) -> APIResponse:
    """更新企业状态或套餐"""
    try:
        enterprise = (
            db.query(Enterprise).filter(Enterprise.id == enterprise_id, Enterprise.deleted_at.is_(None)).first()
        )

        if not enterprise:
            return APIResponse(code=404, message="企业不存在", data=None)

        if verify_status:
            enterprise.verify_status = verify_status
            if verify_status == "verified":
                enterprise.verified_at = datetime.utcnow()
        if plan_type:
            enterprise.plan_type = plan_type
        if reject_reason:
            enterprise.reject_reason = reject_reason

        enterprise.updated_at = datetime.utcnow()
        db.commit()

        return APIResponse(code=200, message="更新成功", data=enterprise.to_dict())
    except Exception as e:
        db.rollback()
        return APIResponse(code=ErrorCode.SYSTEM_ERROR, message=str(e), data=None)


# ==================== 6. 删除企业 ====================


@router.delete("/enterprises/{enterprise_id}", response_model=APIResponse, summary="删除企业", tags=["管理员"])
async def delete_enterprise(
    enterprise_id: int, current_user: dict = Depends(require_admin), db: Session = Depends(get_db)
) -> APIResponse:
    """软删除企业"""
    try:
        enterprise = (
            db.query(Enterprise).filter(Enterprise.id == enterprise_id, Enterprise.deleted_at.is_(None)).first()
        )

        if not enterprise:
            return APIResponse(code=404, message="企业不存在", data=None)

        enterprise.deleted_at = datetime.utcnow()
        db.commit()

        return APIResponse(code=200, message="删除成功", data={"id": enterprise_id})
    except Exception as e:
        db.rollback()
        return APIResponse(code=ErrorCode.SYSTEM_ERROR, message=str(e), data=None)


# ==================== 7. 平台统计 ====================


@router.get("/stats", response_model=APIResponse, summary="平台统计", tags=["管理员"])
async def get_stats(current_user: dict = Depends(require_admin), db: Session = Depends(get_db)) -> APIResponse:
    """获取平台统计数据"""
    try:
        # 用户统计
        total_users = db.query(func.count(User.id)).filter(User.deleted_at.is_(None)).scalar()
        active_users = db.query(func.count(User.id)).filter(User.deleted_at.is_(None), User.status == "active").scalar()

        # 企业统计
        total_enterprises = db.query(func.count(Enterprise.id)).filter(Enterprise.deleted_at.is_(None)).scalar()
        verified_enterprises = (
            db.query(func.count(Enterprise.id))
            .filter(Enterprise.deleted_at.is_(None), Enterprise.verify_status == "verified")
            .scalar()
        )

        # 今日新增
        today = datetime.utcnow().date()
        new_users_today = (
            db.query(func.count(User.id))
            .filter(User.deleted_at.is_(None), func.date(User.created_at) == today)
            .scalar()
        )

        return APIResponse(
            code=200,
            message="success",
            data={
                "users": {"total": total_users, "active": active_users, "new_today": new_users_today},
                "enterprises": {"total": total_enterprises, "verified": verified_enterprises},
            },
        )
    except Exception as e:
        return APIResponse(code=ErrorCode.SYSTEM_ERROR, message=str(e), data=None)


# ==================== 8. AI使用统计 ====================


@router.get("/ai-usage", response_model=APIResponse, summary="AI使用统计", tags=["管理员"])
async def get_ai_usage(
    days: int = Query(7, ge=1, le=90), current_user: dict = Depends(require_admin), db: Session = Depends(get_db)
) -> APIResponse:
    """获取AI使用统计"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        # 对话消息Token统计
        message_stats = (
            db.query(
                func.sum(Message.total_tokens).label("total_tokens"), func.count(Message.id).label("message_count")
            )
            .filter(Message.created_at >= start_date)
            .first()
        )

        # 内容生成Token统计
        content_stats = (
            db.query(
                func.sum(ContentRecord.total_tokens).label("total_tokens"),
                func.count(ContentRecord.id).label("record_count"),
            )
            .filter(ContentRecord.created_at >= start_date)
            .first()
        )

        total_tokens = (message_stats.total_tokens or 0) + (content_stats.total_tokens or 0)

        return APIResponse(
            code=200,
            message="success",
            data={
                "period_days": days,
                "chat": {
                    "message_count": message_stats.message_count or 0,
                    "total_tokens": message_stats.total_tokens or 0,
                },
                "content_generation": {
                    "record_count": content_stats.record_count or 0,
                    "total_tokens": content_stats.total_tokens or 0,
                },
                "total_tokens": total_tokens,
            },
        )
    except Exception as e:
        return APIResponse(code=ErrorCode.SYSTEM_ERROR, message=str(e), data=None)


# ==================== 9. 提供商设置 ====================

# 所有可用提供商的完整列表
ALL_PROVIDERS = [
    {"id": "openai", "name": "OpenAI", "group": "international"},
    {"id": "azure", "name": "Azure OpenAI", "group": "international"},
    {"id": "anthropic", "name": "Anthropic", "group": "international"},
    {"id": "deepseek", "name": "DeepSeek（深度求索）", "group": "national"},
    {"id": "qwen", "name": "通义千问（阿里）", "group": "national"},
    {"id": "wenxin", "name": "文心一言（百度）", "group": "national"},
    {"id": "glm", "name": "智谱GLM", "group": "national"},
    {"id": "spark", "name": "讯飞星火", "group": "national"},
    {"id": "moonshot", "name": "Moonshot（月之暗面）", "group": "national"},
    {"id": "custom", "name": "自定义接入", "group": "other"},
]

PROVIDER_SETTINGS_KEY = "enabled_providers"


def _get_enabled_providers(db: Session) -> list:
    """获取已启用的提供商列表"""
    config = db.query(SystemConfig).filter(SystemConfig.config_key == PROVIDER_SETTINGS_KEY).first()
    if config and config.config_value:
        return config.config_value
    # 默认全部启用
    return [p["id"] for p in ALL_PROVIDERS]


@router.get("/provider-settings", response_model=APIResponse, summary="获取提供商设置", tags=["管理员"])
async def get_provider_settings(
    current_user: dict = Depends(require_admin), db: Session = Depends(get_db)
) -> APIResponse:
    """获取提供商设置（管理员查看所有提供商及其启用状态）"""
    try:
        enabled = _get_enabled_providers(db)
        providers = []
        for p in ALL_PROVIDERS:
            providers.append({**p, "enabled": p["id"] in enabled})
        return APIResponse(code=200, message="success", data={"providers": providers, "enabled_ids": enabled})
    except Exception as e:
        return APIResponse(code=ErrorCode.SYSTEM_ERROR, message=str(e), data=None)


class UpdateProviderSettingsRequest(BaseModel):
    enabled_ids: list = None


@router.put("/provider-settings", response_model=APIResponse, summary="更新提供商设置", tags=["管理员"])
async def update_provider_settings(
    body: UpdateProviderSettingsRequest = None,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
) -> APIResponse:
    """更新启用的提供商列表"""
    try:
        enabled_ids = body.enabled_ids if body and body.enabled_ids else None
        if enabled_ids is None:
            enabled_ids = [p["id"] for p in ALL_PROVIDERS]

        # 验证ID合法性
        valid_ids = {p["id"] for p in ALL_PROVIDERS}
        enabled_ids = [pid for pid in enabled_ids if pid in valid_ids]

        # "custom" 始终保留 — 用户自主接入权利
        if "custom" not in enabled_ids:
            enabled_ids.append("custom")

        config = db.query(SystemConfig).filter(SystemConfig.config_key == PROVIDER_SETTINGS_KEY).first()

        if config:
            config.config_value = enabled_ids
            config.updated_at = datetime.utcnow()
        else:
            config = SystemConfig(
                config_key=PROVIDER_SETTINGS_KEY, config_value=enabled_ids, description="管理员配置的已启用AI提供商列表"
            )
            db.add(config)

        db.commit()

        return APIResponse(code=200, message="提供商设置已更新", data={"enabled_ids": enabled_ids})
    except Exception as e:
        db.rollback()
        return APIResponse(code=ErrorCode.SYSTEM_ERROR, message=str(e), data=None)


__all__ = ["router"]
