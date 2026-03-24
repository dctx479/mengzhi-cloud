"""
API v1 路由聚合器

P1-架构修复: 集中化路由管理，统一前缀和标签配置

版本: 1.0
创建日期: 2026-02-10
"""

from fastapi import APIRouter

# 创建 v1 版本的主路由器
api_router = APIRouter()

# ==================== 认证模块 ====================
from app.api.auth import router as auth_router

api_router.include_router(auth_router, prefix="/auth", tags=["认证 - Authentication"])

# ==================== 用户模块 ====================
from app.api.users import router as users_router

api_router.include_router(users_router, prefix="/users", tags=["用户 - Users"])

# ==================== 产品模块 ====================
from app.api.products import router as products_router

api_router.include_router(products_router, tags=["产品 - Products"])

# ==================== AI对话模块 ====================
from app.api.chat import router as chat_router

api_router.include_router(chat_router, prefix="/chat", tags=["AI对话 - Chat"])

# ==================== 媒体素材模块 ====================
from app.api.media import router as media_router

api_router.include_router(media_router, tags=["媒体素材 - Media"])

# ==================== 文化标签模块 ====================
from app.api.cultural_tags import router as cultural_tags_router

api_router.include_router(cultural_tags_router, tags=["文化标签 - Cultural Tags"])

# ==================== RBAC 权限管理模块 ====================
from app.api.roles import router as roles_router
from app.api.permissions import router as permissions_router
from app.api.user_roles import router as user_roles_router

api_router.include_router(roles_router, prefix="/rbac", tags=["权限管理 - RBAC"])
api_router.include_router(permissions_router, prefix="/rbac", tags=["权限管理 - RBAC"])
api_router.include_router(user_roles_router, prefix="/rbac", tags=["权限管理 - RBAC"])

# ==================== 配额与订单模块 ====================
from app.api.quota_packages import router as quota_packages_router
from app.api.orders import router as orders_router
from app.api.quotas import router as quotas_router

api_router.include_router(quota_packages_router, tags=["配额套餐 - Quota Packages"])
api_router.include_router(orders_router, tags=["订单 - Orders"])
api_router.include_router(quotas_router, prefix="/quotas", tags=["配额管理 - Quotas"])

# ==================== 计费与对账模块 ====================
from app.api.billing import router as billing_router
from app.api.reconciliation import router as reconciliation_router

api_router.include_router(billing_router, prefix="/billing", tags=["计费管理 - Billing"])
api_router.include_router(reconciliation_router, prefix="/reconciliation", tags=["对账系统 - Reconciliation"])

# ==================== 风控模块 ====================
from app.api.risk_control import router as risk_control_router

api_router.include_router(risk_control_router, prefix="/risk", tags=["风控系统 - Risk Control"])

# ==================== SLA 保障模块 ====================
from app.api.sla import router as sla_router

api_router.include_router(sla_router, prefix="/sla", tags=["SLA保障 - SLA"])

# ==================== 租户管理模块 ====================
from app.api.tenant_management import router as tenant_router

api_router.include_router(tenant_router, prefix="/tenants", tags=["租户管理 - Tenant Management"])

# ==================== 导出模块 ====================
from app.api.exports import router as exports_router

api_router.include_router(exports_router, prefix="/export", tags=["导出 - Export"])

# ==================== AI 配置模块 ====================
from app.api.ai_configs import router as ai_configs_router

api_router.include_router(ai_configs_router, tags=["AI配置 - AI Configs"])

# ==================== 审计日志模块 ====================
from app.api.audit_logs import router as audit_logs_router

api_router.include_router(audit_logs_router, prefix="/audit-logs", tags=["审计日志 - Audit Logs"])

# ==================== 提示词模板模块 ====================
from app.api.v1.prompts import router as prompts_router

api_router.include_router(prompts_router, prefix="/prompts", tags=["提示词模板 - Prompts"])

# ==================== 优化内容生成模块 ====================
from app.api.optimized_content import router as optimized_content_router

api_router.include_router(optimized_content_router, prefix="/content-generation", tags=["内容生成 - Content Generation"])


__all__ = ["api_router"]
