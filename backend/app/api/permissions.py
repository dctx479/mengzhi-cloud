"""
权限管理API

提供权限的CRUD操作

版本: 1.0
更新日期: 2026-01-17
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.api.deps import get_db, require_admin
from app.schemas.roles import (
    PermissionCreate, PermissionUpdate, PermissionResponse,
    PermissionListQuery
)
from app.schemas.common import PageInfo, PaginatedResponse
from app.services.permission_service import PermissionService
from app.core.errors import BusinessException, ErrorCode

router = APIRouter(prefix="/permissions", tags=["权限管理-权限"])
logger = logging.getLogger(__name__)


@router.get("", response_model=PaginatedResponse[PermissionResponse])
async def list_permissions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    resource: Optional[str] = Query(None, max_length=50, description="资源筛选"),
    action: Optional[str] = Query(None, max_length=20, description="操作筛选"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    获取权限列表（管理员）

    权限要求：管理员

    查询参数：
    - page: 页码（默认1）
    - page_size: 每页数量（默认20，最大100）
    - resource: 资源筛选（如：product、user、chat）
    - action: 操作筛选（如：create、read、update、delete）
    """
    try:
        service = PermissionService(db)
        permissions, total = service.list_permissions(
            page=page,
            page_size=page_size,
            resource=resource,
            action=action
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
            data=[PermissionResponse.from_orm(perm) for perm in permissions],
            pagination=pagination
        )

    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to list permissions: {str(e)}")
        raise HTTPException(status_code=500, detail="获取权限列表失败")


@router.post("", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionCreate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    创建权限（管理员）

    权限要求：管理员

    请求体：
    - resource: 资源名称（必填，小写字母和下划线）
    - action: 操作名称（必填，如：create、read、update、delete）
    - name: 权限显示名称（必填）
    - description: 权限描述（可选）

    注意：resource + action 组合必须唯一
    """
    try:
        service = PermissionService(db)
        permission = service.create_permission(
            resource=permission_data.resource,
            action=permission_data.action,
            name=permission_data.name,
            description=permission_data.description
        )

        return PermissionResponse.from_orm(permission)

    except BusinessException as e:
        if e.code == ErrorCode.RESOURCE_ALREADY_EXISTS:
            raise HTTPException(status_code=409, detail=e.message)
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to create permission: {str(e)}")
        raise HTTPException(status_code=500, detail="创建权限失败")


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    获取权限详情（管理员）

    权限要求：管理员

    路径参数：
    - permission_id: 权限ID
    """
    try:
        service = PermissionService(db)
        permission = service.get_permission(permission_id)

        if not permission:
            raise HTTPException(status_code=404, detail="权限不存在")

        return PermissionResponse.from_orm(permission)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get permission {permission_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="获取权限详情失败")


@router.get("/resources/list", response_model=List[str])
async def list_resources(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    获取所有资源列表（管理员）

    权限要求：管理员

    返回系统中所有不重复的资源名称
    """
    try:
        from app.models import Permission
        resources = db.query(Permission.resource).distinct().all()
        return [r[0] for r in resources]

    except Exception as e:
        logger.error(f"Failed to list resources: {str(e)}")
        raise HTTPException(status_code=500, detail="获取资源列表失败")


__all__ = ["router"]
