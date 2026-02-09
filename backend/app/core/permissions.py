"""
权限控制中间件

版本: 1.0
更新日期: 2026-01-22
"""

from functools import wraps
from typing import Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db


def require_permission(resource: str, action: str):
    """
    权限验证装饰器

    参数:
        resource: 资源名称
        action: 操作名称
    """
    async def permission_checker(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> dict:
        if current_user.get("role") == "admin":
            return current_user

        from app.models import User
        user = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()

        if not user or not user.has_permission(resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要 {resource}:{action} 权限"
            )

        return current_user

    return permission_checker


def require_admin():
    """管理员权限装饰器"""
    async def admin_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员权限"
            )
        return current_user

    return admin_checker


def require_enterprise_owner():
    """企业所有者权限装饰器"""
    async def owner_checker(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> dict:
        if current_user.get("role") == "admin":
            return current_user

        if current_user.get("role") != "enterprise_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要企业管理员权限"
            )

        return current_user

    return owner_checker


__all__ = [
    "require_permission",
    "require_admin",
    "require_enterprise_owner",
]
