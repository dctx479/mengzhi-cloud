"""
租户管理API

版本: 1.0
更新日期: 2026-01-22

功能：
- 创建租户（含数据库）
- 删除租户（含数据库）
- 迁移租户数据
- 备份租户数据
- 查询租户信息
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_current_user
from app.models.enterprise import Enterprise, IsolationMode, PlanType
from app.services.tenant_db_manager import get_tenant_db_manager
from app.core.tenant_database import get_tenant_router

router = APIRouter(tags=["租户管理"])


# ==================== Schemas ====================

class TenantCreateRequest(BaseModel):
    """创建租户请求"""
    enterprise_id: int = Field(..., description="企业ID")
    isolation_mode: str = Field("shared", description="隔离模式：shared/isolated")
    initialize_schema: bool = Field(True, description="是否初始化表结构")


class TenantCreateResponse(BaseModel):
    """创建租户响应"""
    success: bool
    enterprise_id: int
    database_name: Optional[str] = None
    isolation_mode: str
    created_at: Optional[str] = None


class TenantDeleteRequest(BaseModel):
    """删除租户请求"""
    backup_first: bool = Field(True, description="是否先备份")


class TenantDeleteResponse(BaseModel):
    """删除租户响应"""
    success: bool
    enterprise_id: int
    backup_file: Optional[str] = None


class TenantMigrateRequest(BaseModel):
    """迁移租户请求"""
    target_mode: str = Field(..., description="目标模式：shared/isolated")


class TenantMigrateResponse(BaseModel):
    """迁移租户响应"""
    success: bool
    enterprise_id: int
    from_mode: str
    to_mode: str
    database_name: Optional[str] = None
    migrated_tables: List[str]


class TenantBackupRequest(BaseModel):
    """备份租户请求"""
    output_dir: Optional[str] = Field(None, description="输出目录")


class TenantBackupResponse(BaseModel):
    """备份租户响应"""
    success: bool
    enterprise_id: int
    database_name: str
    backup_file: str
    backup_size: int
    created_at: str


class TenantInfoResponse(BaseModel):
    """租户信息响应"""
    enterprise_id: int
    enterprise_name: str
    isolation_mode: str
    database_name: Optional[str] = None
    database_created_at: Optional[str] = None
    plan_type: str
    verify_status: str


class TenantStatsResponse(BaseModel):
    """租户统计响应"""
    total_tenants: int
    isolated_tenants: int
    shared_tenants: int
    total_databases: int
    connection_stats: dict


# ==================== API Endpoints ====================

@router.post("/", response_model=TenantCreateResponse)
async def create_tenant(
    request: TenantCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    创建租户（含数据库）

    权限：系统管理员
    """
    # 验证权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统管理员权限"
        )

    # 获取企业信息
    enterprise = db.query(Enterprise).filter(
        Enterprise.id == request.enterprise_id
    ).first()

    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="企业不存在"
        )

    # 验证隔离模式
    if request.isolation_mode not in ["shared", "isolated"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的隔离模式"
        )

    # 更新企业隔离模式
    enterprise.isolation_mode = IsolationMode(request.isolation_mode)
    db.commit()

    # 如果是独立模式，创建数据库
    if request.isolation_mode == "isolated":
        manager = get_tenant_db_manager()
        result = manager.create_tenant_database(
            request.enterprise_id,
            db,
            initialize_schema=request.initialize_schema
        )

        return TenantCreateResponse(
            success=result["success"],
            enterprise_id=result["enterprise_id"],
            database_name=result["database_name"],
            isolation_mode=request.isolation_mode,
            created_at=result["created_at"]
        )
    else:
        return TenantCreateResponse(
            success=True,
            enterprise_id=request.enterprise_id,
            database_name=None,
            isolation_mode=request.isolation_mode,
            created_at=None
        )


@router.delete("/{enterprise_id}", response_model=TenantDeleteResponse)
async def delete_tenant(
    enterprise_id: int,
    request: TenantDeleteRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    删除租户（含数据库）

    权限：系统管理员
    """
    # 验证权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统管理员权限"
        )

    # 获取企业信息
    enterprise = db.query(Enterprise).filter(
        Enterprise.id == enterprise_id
    ).first()

    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="企业不存在"
        )

    # 如果有独立数据库，删除数据库
    if enterprise.database_name:
        manager = get_tenant_db_manager()
        result = manager.drop_tenant_database(
            enterprise_id,
            db,
            backup_first=request.backup_first
        )

        return TenantDeleteResponse(
            success=result["success"],
            enterprise_id=result["enterprise_id"],
            backup_file=result.get("backup_file")
        )
    else:
        return TenantDeleteResponse(
            success=True,
            enterprise_id=enterprise_id,
            backup_file=None
        )


@router.post("/{enterprise_id}/migrate", response_model=TenantMigrateResponse)
async def migrate_tenant(
    enterprise_id: int,
    request: TenantMigrateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    迁移租户数据

    权限：系统管理员
    """
    # 验证权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统管理员权限"
        )

    # 获取企业信息
    enterprise = db.query(Enterprise).filter(
        Enterprise.id == enterprise_id
    ).first()

    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="企业不存在"
        )

    # 验证目标模式
    if request.target_mode not in ["shared", "isolated"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的目标模式"
        )

    from_mode = enterprise.isolation_mode.value
    to_mode = request.target_mode

    if from_mode == to_mode:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="目标模式与当前模式相同"
        )

    # 执行迁移
    manager = get_tenant_db_manager()

    if to_mode == "isolated":
        result = manager.migrate_to_isolated(enterprise_id, db)
    else:
        result = manager.migrate_to_shared(enterprise_id, db)

    return TenantMigrateResponse(
        success=result["success"],
        enterprise_id=result["enterprise_id"],
        from_mode=from_mode,
        to_mode=to_mode,
        database_name=result.get("database_name"),
        migrated_tables=result["migrated_tables"]
    )


@router.post("/{enterprise_id}/backup", response_model=TenantBackupResponse)
async def backup_tenant(
    enterprise_id: int,
    request: TenantBackupRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    备份租户数据

    权限：系统管理员或企业管理员
    """
    # 验证权限
    if current_user.get("role") != "admin":
        # 检查是否为企业管理员
        from app.models import User
        user = db.query(User).filter(
            User.user_uuid == current_user["user_id"]
        ).first()

        if not user or user.enterprise_id != enterprise_id or user.role not in ["enterprise_admin", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要系统管理员或企业管理员权限"
            )

    # 获取企业信息
    enterprise = db.query(Enterprise).filter(
        Enterprise.id == enterprise_id
    ).first()

    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="企业不存在"
        )

    if not enterprise.database_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该企业没有独立数据库"
        )

    # 执行备份
    manager = get_tenant_db_manager()
    result = manager.backup_tenant_database(
        enterprise_id,
        db,
        output_dir=request.output_dir
    )

    return TenantBackupResponse(
        success=result["success"],
        enterprise_id=result["enterprise_id"],
        database_name=result["database_name"],
        backup_file=result["backup_file"],
        backup_size=result["backup_size"],
        created_at=result["created_at"]
    )


@router.get("/stats", response_model=TenantStatsResponse)
async def get_tenant_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取租户统计信息

    权限：系统管理员
    """
    # 验证权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统管理员权限"
        )

    # 统计租户数量
    total_tenants = db.query(Enterprise).count()
    isolated_tenants = db.query(Enterprise).filter(
        Enterprise.isolation_mode == IsolationMode.ISOLATED
    ).count()
    shared_tenants = total_tenants - isolated_tenants

    # 统计数据库数量
    total_databases = db.query(Enterprise).filter(
        Enterprise.database_name.isnot(None)
    ).count()

    # 获取连接统计
    router = get_tenant_router()
    connection_stats = router.get_connection_stats()

    return TenantStatsResponse(
        total_tenants=total_tenants,
        isolated_tenants=isolated_tenants,
        shared_tenants=shared_tenants,
        total_databases=total_databases,
        connection_stats=connection_stats
    )


@router.get("/", response_model=List[TenantInfoResponse])
async def list_tenants(
    isolation_mode: Optional[str] = Query(None, description="过滤隔离模式"),
    plan_type: Optional[str] = Query(None, description="过滤套餐类型"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取租户列表

    权限：系统管理员
    """
    # 验证权限
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统管理员权限"
        )

    # 构建查询
    query = db.query(Enterprise)

    if isolation_mode:
        query = query.filter(Enterprise.isolation_mode == IsolationMode(isolation_mode))

    if plan_type:
        query = query.filter(Enterprise.plan_type == PlanType(plan_type))

    # 分页
    enterprises = query.offset(skip).limit(limit).all()

    return [
        TenantInfoResponse(
            enterprise_id=e.id,
            enterprise_name=e.name,
            isolation_mode=e.isolation_mode.value,
            database_name=e.database_name,
            database_created_at=e.database_created_at.isoformat() if e.database_created_at else None,
            plan_type=e.plan_type.value,
            verify_status=e.verify_status.value
        )
        for e in enterprises
    ]


@router.get("/{enterprise_id}", response_model=TenantInfoResponse)
async def get_tenant_info(
    enterprise_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取租户信息

    权限：系统管理员或企业管理员
    """
    # 验证权限
    if current_user.get("role") != "admin":
        # 检查是否为企业管理员
        from app.models import User
        user = db.query(User).filter(
            User.user_uuid == current_user["user_id"]
        ).first()

        if not user or user.enterprise_id != enterprise_id or user.role not in ["enterprise_admin", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要系统管理员或企业管理员权限"
            )

    # 获取企业信息
    enterprise = db.query(Enterprise).filter(
        Enterprise.id == enterprise_id
    ).first()

    if not enterprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="企业不存在"
        )

    return TenantInfoResponse(
        enterprise_id=enterprise.id,
        enterprise_name=enterprise.name,
        isolation_mode=enterprise.isolation_mode.value,
        database_name=enterprise.database_name,
        database_created_at=enterprise.database_created_at.isoformat() if enterprise.database_created_at else None,
        plan_type=enterprise.plan_type.value,
        verify_status=enterprise.verify_status.value
    )


__all__ = ["router"]
