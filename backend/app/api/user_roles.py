"""
用户角色管理API

提供用户角色分配和权限查询

版本: 1.0
更新日期: 2026-01-17
"""

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from typing import List
import logging

from app.api.deps import get_db, require_admin, get_current_user
from app.schemas.roles import (
    UserRoleAssignment, RoleResponse, PermissionResponse
)
from app.services.permission_service import PermissionService
from app.models import User
from app.core.errors import BusinessException, ErrorCode

router = APIRouter(prefix="/users", tags=["权限管理-用户角色"])
logger = logging.getLogger(__name__)


@router.post("/{user_id}/roles", response_model=dict)
async def assign_roles_to_user(
    user_id: int = Path(..., description="用户ID"),
    assignment: UserRoleAssignment = ...,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    为用户分配角色（管理员）

    权限要求：管理员

    路径参数：
    - user_id: 用户ID

    请求体：
    - role_ids: 角色ID列表（必填，至少1个）

    注意：这是覆盖式分配，会替换用户的所有角色
    """
    try:
        service = PermissionService(db)
        user = service.assign_roles_to_user(
            user_id=user_id,
            role_ids=assignment.role_ids
        )

        return {
            "message": "角色分配成功",
            "user_id": user.id,
            "username": user.username,
            "roles": [{"id": role.id, "name": role.name, "code": role.code} for role in user.roles]
        }

    except BusinessException as e:
        if e.code == ErrorCode.RESOURCE_NOT_FOUND:
            raise HTTPException(status_code=404, detail=e.message)
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to assign roles to user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="分配角色失败")


@router.get("/me/permissions", response_model=List[PermissionResponse])
async def get_my_permissions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的所有权限

    权限要求：已登录用户

    返回当前用户通过所有角色获得的权限列表（去重）
    """
    try:
        # 需要从user_uuid获取user_id
        user = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()

        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        service = PermissionService(db)
        permissions = service.get_user_permissions(user.id)

        return [PermissionResponse.from_orm(perm) for perm in permissions]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current user permissions: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户权限失败")


@router.get("/{user_id}/roles", response_model=List[RoleResponse])
async def get_user_roles(
    user_id: int = Path(..., description="用户ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的角色列表

    权限要求：用户本人或管理员

    路径参数：
    - user_id: 用户ID
    """
    # 检查权限：只能查看自己的角色，或者管理员可以查看所有人
    current_user_obj = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
    if not current_user_obj:
        raise HTTPException(status_code=404, detail="当前用户不存在")
    if current_user_obj.id != user_id and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="无权查看其他用户的角色")

    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        return [RoleResponse.from_orm(role) for role in user.roles]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get roles for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户角色失败")


@router.get("/{user_id}/permissions", response_model=List[PermissionResponse])
async def get_user_permissions(
    user_id: int = Path(..., description="用户ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的所有权限

    权限要求：用户本人或管理员

    路径参数：
    - user_id: 用户ID

    返回用户通过所有角色获得的权限列表（去重）
    """
    # 检查权限：只能查看自己的权限，或者管理员可以查看所有人
    current_user_obj = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()
    if not current_user_obj:
        raise HTTPException(status_code=404, detail="当前用户不存在")
    if current_user_obj.id != user_id and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="无权查看其他用户的权限")

    try:
        service = PermissionService(db)
        permissions = service.get_user_permissions(user_id)

        return [PermissionResponse.from_orm(perm) for perm in permissions]

    except Exception as e:
        logger.error(f"Failed to get permissions for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户权限失败")


__all__ = ["router"]
