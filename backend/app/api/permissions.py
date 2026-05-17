"""
权限管理API

提供权限的CRUD操作

版本: 1.0
更新日期: 2026-01-17
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.api.deps import get_db, require_admin
from app.schemas.roles import (
    PermissionCreate, PermissionUpdate, PermissionResponse
)
from app.schemas.common import PageInfo
from app.services.permission_service import PermissionService
from app.core.errors import BusinessException, ErrorCode
from app.core.responses import success_response

router = APIRouter(prefix="/permissions", tags=["权限管理-权限"])
logger = logging.getLogger(__name__)


@router.get("")
async def list_permissions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    resource: Optional[str] = Query(None, max_length=50, description="资源筛选"),
    action: Optional[str] = Query(None, max_length=20, description="操作筛选"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取权限列表（管理员）"""
    try:
        service = PermissionService(db)
        permissions, total = service.list_permissions(
            page=page,
            page_size=page_size,
            resource=resource,
            action=action
        )

        total_pages = (total + page_size - 1) // page_size
        pagination = PageInfo(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )

        return success_response(data={
            "items": [PermissionResponse.from_orm(perm).dict() for perm in permissions],
            "pagination": pagination.dict()
        }).dict()

    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to list permissions: {str(e)}")
        raise HTTPException(status_code=500, detail="获取权限列表失败")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionCreate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """创建权限（管理员）"""
    try:
        service = PermissionService(db)
        permission = service.create_permission(
            resource=permission_data.resource,
            action=permission_data.action,
            name=permission_data.name,
            description=permission_data.description
        )

        return success_response(data=PermissionResponse.from_orm(permission).dict(), message="创建权限成功").dict()

    except BusinessException as e:
        if e.code == ErrorCode.RESOURCE_ALREADY_EXISTS:
            raise HTTPException(status_code=409, detail=e.message)
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to create permission: {str(e)}")
        raise HTTPException(status_code=500, detail="创建权限失败")


@router.get("/resources/list")
async def list_resources(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取所有资源列表（管理员）"""
    try:
        from app.models import Permission
        resources = db.query(Permission.resource).distinct().all()
        return success_response(data={"resources": [r[0] for r in resources]}).dict()

    except Exception as e:
        logger.error(f"Failed to list resources: {str(e)}")
        raise HTTPException(status_code=500, detail="获取资源列表失败")


@router.get("/{permission_id}")
async def get_permission(
    permission_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取权限详情（管理员）"""
    try:
        service = PermissionService(db)
        permission = service.get_permission(permission_id)

        if not permission:
            raise HTTPException(status_code=404, detail="权限不存在")

        return success_response(data=PermissionResponse.from_orm(permission).dict()).dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get permission {permission_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="获取权限详情失败")


@router.put("/{permission_id}")
async def update_permission(
    permission_id: int,
    permission_data: PermissionUpdate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """更新权限（管理员）"""
    try:
        service = PermissionService(db)
        permission = service.get_permission(permission_id)

        if not permission:
            raise HTTPException(status_code=404, detail="权限不存在")

        update_fields = permission_data.dict(exclude_unset=True)
        if not update_fields:
            raise HTTPException(status_code=400, detail="请求体不能为空")

        for field, value in update_fields.items():
            setattr(permission, field, value)

        db.commit()
        db.refresh(permission)

        return success_response(data=PermissionResponse.from_orm(permission).dict(), message="更新权限成功").dict()

    except HTTPException:
        raise
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Failed to update permission {permission_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="更新权限失败")


__all__ = ["router"]
