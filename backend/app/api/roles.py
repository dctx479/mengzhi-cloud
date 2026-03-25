"""
角色管理API

提供角色的CRUD操作和权限分配

版本: 1.0
更新日期: 2026-01-17
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.api.deps import get_db, require_admin
from app.schemas.roles import (
    RoleCreate, RoleUpdate, RoleResponse, RoleWithPermissions,
    RolePermissionAssignment, RoleListQuery
)
from app.schemas.common import PageInfo, PaginatedResponse, IDResponse, OperationResponse
from app.services.permission_service import PermissionService
from app.core.errors import BusinessException, ErrorCode

router = APIRouter(prefix="/roles", tags=["权限管理-角色"])
logger = logging.getLogger(__name__)


@router.get("", response_model=PaginatedResponse[RoleResponse])
async def list_roles(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, max_length=50, description="搜索关键词"),
    is_system: Optional[bool] = Query(None, description="是否系统角色"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    获取角色列表（管理员）

    权限要求：管理员

    查询参数：
    - page: 页码（默认1）
    - page_size: 每页数量（默认20，最大100）
    - keyword: 搜索关键词，匹配角色名称或代码
    - is_system: 筛选系统角色或自定义角色
    """
    try:
        service = PermissionService(db)
        roles, total = service.list_roles(
            page=page,
            page_size=page_size,
            keyword=keyword,
            is_system=is_system
        )

        # 计算分页信息
        total_pages = (total + page_size - 1) // page_size
        pagination = PageInfo(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )

        return PaginatedResponse(
            data=[RoleResponse.from_orm(role) for role in roles],
            pagination=pagination
        )

    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to list roles: {str(e)}")
        raise HTTPException(status_code=500, detail="获取角色列表失败")


@router.post("", response_model=RoleWithPermissions, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    创建角色（管理员）

    权限要求：管理员

    请求体：
    - name: 角色名称（必填，2-50字符）
    - code: 角色代码（必填，大写字母和下划线）
    - description: 角色描述（可选）
    - permission_ids: 权限ID列表（可选）
    """
    try:
        service = PermissionService(db)
        role = service.create_role(
            name=role_data.name,
            code=role_data.code,
            description=role_data.description,
            permission_ids=role_data.permission_ids,
            is_system=False  # 用户创建的角色不是系统角色
        )

        return RoleWithPermissions.from_orm(role)

    except BusinessException as e:
        if e.code == ErrorCode.RESOURCE_ALREADY_EXISTS:
            raise HTTPException(status_code=409, detail=e.message)
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to create role: {str(e)}")
        raise HTTPException(status_code=500, detail="创建角色失败")


@router.get("/{role_id}", response_model=RoleWithPermissions)
async def get_role(
    role_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    获取角色详情（管理员）

    权限要求：管理员

    路径参数：
    - role_id: 角色ID
    """
    try:
        service = PermissionService(db)
        role = service.get_role(role_id)

        if not role:
            raise HTTPException(status_code=404, detail="角色不存在")

        return RoleWithPermissions.from_orm(role)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get role {role_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="获取角色详情失败")


@router.put("/{role_id}", response_model=RoleWithPermissions)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    更新角色（管理员）

    权限要求：管理员

    路径参数：
    - role_id: 角色ID

    请求体：
    - name: 角色名称（可选）
    - description: 角色描述（可选）

    注意：系统角色不可修改名称，角色代码不可修改
    """
    try:
        service = PermissionService(db)
        role = service.update_role(
            role_id=role_id,
            name=role_data.name,
            description=role_data.description
        )

        return RoleWithPermissions.from_orm(role)

    except BusinessException as e:
        if e.code == ErrorCode.RESOURCE_NOT_FOUND:
            raise HTTPException(status_code=404, detail=e.message)
        elif e.code == ErrorCode.OPERATION_FORBIDDEN:
            raise HTTPException(status_code=403, detail=e.message)
        elif e.code == ErrorCode.RESOURCE_ALREADY_EXISTS:
            raise HTTPException(status_code=409, detail=e.message)
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to update role {role_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="更新角色失败")


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    删除角色（管理员）

    权限要求：管理员

    路径参数：
    - role_id: 角色ID

    注意：
    - 系统角色不可删除
    - 仍有用户使用的角色不可删除
    """
    try:
        service = PermissionService(db)
        service.delete_role(role_id)
        return None

    except BusinessException as e:
        if e.code == ErrorCode.RESOURCE_NOT_FOUND:
            raise HTTPException(status_code=404, detail=e.message)
        elif e.code == ErrorCode.OPERATION_FORBIDDEN:
            raise HTTPException(status_code=403, detail=e.message)
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to delete role {role_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="删除角色失败")


@router.post("/{role_id}/permissions", response_model=RoleWithPermissions)
async def assign_permissions(
    role_id: int,
    assignment: RolePermissionAssignment,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    为角色分配权限（管理员）

    权限要求：管理员

    路径参数：
    - role_id: 角色ID

    请求体：
    - permission_ids: 权限ID列表（必填，至少1个）

    注意：这是覆盖式分配，会替换角色的所有权限
    """
    try:
        service = PermissionService(db)
        role = service.assign_permissions_to_role(
            role_id=role_id,
            permission_ids=assignment.permission_ids
        )

        return RoleWithPermissions.from_orm(role)

    except BusinessException as e:
        if e.code == ErrorCode.RESOURCE_NOT_FOUND:
            raise HTTPException(status_code=404, detail=e.message)
        elif e.code == ErrorCode.OPERATION_FORBIDDEN:
            raise HTTPException(status_code=403, detail=e.message)
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to assign permissions to role {role_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="分配权限失败")


__all__ = ["router"]
