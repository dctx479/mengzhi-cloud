"""
租户上下文管理

版本: 2.0
更新日期: 2026-01-22

功能：
- 租户身份识别
- 数据库路由
- 权限验证
"""

from dataclasses import dataclass
from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.tenant_database import get_tenant_db
from app.models.enterprise import IsolationMode


@dataclass
class TenantContext:
    """租户上下文数据类"""
    tenant_id: int
    user_id: str
    user_type: str
    role: str
    isolation_mode: str = "shared"
    database_name: Optional[str] = None


def get_current_tenant(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TenantContext:
    """
    获取当前租户上下文

    参数:
        current_user: 当前用户信息
        db: 数据库会话

    返回:
        TenantContext: 租户上下文
    """
    tenant_id = current_user.get("tenant_id")

    if not tenant_id and current_user.get("user_type") == "enterprise":
        from app.models import User
        user = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
        if user and user.enterprise_id:
            tenant_id = user.enterprise_id

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="该操作需要企业用户身份"
        )

    # 获取企业信息以确定隔离模式
    from app.models import Enterprise
    enterprise = db.query(Enterprise).filter(Enterprise.id == tenant_id).first()

    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="企业不存在"
        )

    return TenantContext(
        tenant_id=tenant_id,
        user_id=current_user["user_id"],
        user_type=current_user.get("user_type", ""),
        role=current_user.get("role", ""),
        isolation_mode=enterprise.isolation_mode.value if enterprise.isolation_mode else "shared",
        database_name=enterprise.database_name
    )


def get_tenant_database(
    tenant_context: TenantContext = Depends(get_current_tenant)
) -> Session:
    """
    获取租户数据库会话（根据隔离模式路由）

    参数:
        tenant_context: 租户上下文

    返回:
        Session: 数据库会话
    """
    if tenant_context.isolation_mode == IsolationMode.ISOLATED.value:
        # 独立数据库模式：路由到租户数据库
        db = get_tenant_db(tenant_context.tenant_id)
    else:
        # 共享数据库模式：使用主数据库
        from app.database import SessionLocal
        db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


__all__ = [
    "TenantContext",
    "get_current_tenant",
    "get_tenant_database",
]

