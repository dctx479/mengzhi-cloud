"""
Admin API 路由聚合器

P1-架构修复: 集中化管理员路由

版本: 1.0
创建日期: 2026-02-10
"""

from fastapi import APIRouter

# 创建 admin 版本的主路由器
admin_router = APIRouter()

# ==================== 管理员模块 ====================
from app.api.admin import router as admin_ops_router
admin_router.include_router(
    admin_ops_router,
    tags=["管理员 - Admin"]
)

# ==================== 监控模块 (如果存在) ====================
try:
    from app.api.monitoring import router as monitoring_router
    admin_router.include_router(
        monitoring_router,
        prefix="/monitoring",
        tags=["监控 - Monitoring"]
    )
except ImportError:
    pass


__all__ = ["admin_router"]
