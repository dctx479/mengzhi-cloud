from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from loguru import logger
from datetime import datetime
import uuid
from pathlib import Path
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.core.errors import BusinessException, ERROR_HTTP_STATUS, ERROR_MESSAGES
from app.core.responses import error_response
from app.api import auth_router

# 创建FastAPI应用
app = FastAPI(
    title="内蒙古农畜产品AI平台 API",
    description="基于AI技术的农畜产品品牌营销智能化平台",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ==================== 中间件配置 ====================

# CORS配置 - 根据环境动态配置
from app.core.config import settings

if settings.ENVIRONMENT == "development":
    # 开发环境：允许所有来源（不能同时设置credentials=True）
    cors_origins = ["*"]
    cors_allow_credentials = False
else:
    # 生产环境：使用白名单
    cors_origins = getattr(settings, 'CORS_ORIGINS', []).split(',') if isinstance(getattr(settings, 'CORS_ORIGINS', ''), str) else getattr(settings, 'CORS_ORIGINS', [])
    cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]
    if not cors_origins:
        logger.warning("CORS_ORIGINS not configured, using default localhost")
        cors_origins = ["http://localhost:5173"]
    cors_allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Type", "Authorization"],
    max_age=3600,  # 缓存预检请求结果1小时
)


# ==================== 异常处理 ====================

# P1-10: 使用统一异常处理系统
from app.core.exception_handlers import register_exception_handlers

register_exception_handlers(app)


# ==================== 健康检查和根路由 ====================

logger.info("内蒙古农畜产品AI平台 API启动")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用内蒙古农畜产品AI平台API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "agri-ai-platform",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/metrics")
async def metrics():
    """Prometheus指标端点"""
    from app.core.metrics import (
        active_users, active_enterprises,
        payment_pending_gauge, payment_processing_gauge
    )

    # 更新一些实时指标（这里可以从数据库获取实际数据）
    # 这是示例数据，实际应用中应该从数据库查询
    try:
        # 这里可以添加实际的数据库查询来更新指标
        # active_users.set(get_active_users_count())
        # active_enterprises.set(get_active_enterprises_count())
        pass
    except Exception as e:
        logger.warning(f"更新实时指标失败: {str(e)}")

    # 生成Prometheus格式的指标数据
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ==================== 路由注册 ====================

# 注册认证路由
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["认证 - Authentication"]
)

# 注册产品路由
from app.api import products
app.include_router(
    products.router,
    prefix="/api/v1",
    tags=["产品 - Products"]
)

# 注册AI对话路由
from app.api import chat
app.include_router(
    chat.router,
    prefix="/api/v1/chat",
    tags=["AI对话 - Chat"]
)

# 注册用户路由 (BUG-022: 头像上传)
from app.api import users
app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["用户 - Users"]
)

# 注册导出路由 (BUG-026: 导出功能)
from app.api import exports
app.include_router(
    exports.router,
    prefix="/api/v1/export",
    tags=["导出 - Export"]
)

# 注册配额套餐路由
from app.api.quota_packages import router as quota_packages_router
app.include_router(
    quota_packages_router,
    prefix="/api/v1",
    tags=["配额套餐 - Quota Packages"]
)

# 注册订单路由
from app.api.orders import router as orders_router
app.include_router(
    orders_router,
    prefix="/api/v1",
    tags=["订单 - Orders"]
)

# 注册AI配置路由
from app.api import ai_configs
app.include_router(
    ai_configs.router,
    prefix="/api",
    tags=["AI配置 - AI Configs"]
)

# 注册媒体路由 (BE-008: 多模态素材管理)
from app.api import media
app.include_router(
    media.router,
    prefix="/api/v1",
    tags=["媒体素材 - Media"]
)

# 注册文化标签路由 (BE-007: 文化标签管理)
from app.api import cultural_tags
app.include_router(
    cultural_tags.router,
    prefix="/api/v1",
    tags=["文化标签 - Cultural Tags"]
)

# 注册权限管理路由 (BE-005: RBAC权限系统)
from app.api import roles, permissions, user_roles
app.include_router(
    roles.router,
    prefix="/api/v1/rbac",
    tags=["权限管理 - RBAC"]
)

# 注册管理员路由
from app.api import admin
app.include_router(
    admin.router,
    prefix="/api/admin",
    tags=["管理员 - Admin"]
)

# 注册审计日志路由
from app.api import audit_logs
app.include_router(
    audit_logs.router,
    prefix="/api",
    tags=["审计日志 - Audit Logs"]
)

# 注册配额管理路由
from app.api import quotas
app.include_router(
    quotas.router,
    prefix="/api",
    tags=["配额管理 - Quotas"]
)

# 注册计费路由
from app.api import billing
app.include_router(
    billing.router,
    prefix="/api",
    tags=["计费管理 - Billing"]
)

# 注册风控路由
from app.api import risk_control
app.include_router(
    risk_control.router,
    prefix="/api/v1",
    tags=["风控系统 - Risk Control"]
)

# 注册对账路由
from app.api import reconciliation
app.include_router(
    reconciliation.router,
    prefix="/api/v1",
    tags=["对账系统 - Reconciliation"]
)

# 注册SLA路由
from app.api import sla
app.include_router(
    sla.router,
    prefix="/api/v1",
    tags=["SLA保障 - SLA"]
)

# 注册租户管理路由
from app.api import tenant_management
app.include_router(
    tenant_management.router,
    prefix="/api/v1",
    tags=["租户管理 - Tenant Management"]
)

app.include_router(
    permissions.router,
    prefix="/api/v1/rbac",
    tags=["权限管理 - RBAC"]
)
app.include_router(
    user_roles.router,
    prefix="/api/v1/rbac",
    tags=["权限管理 - RBAC"]
)

# 挂载静态文件目录（用于访问上传的媒体文件）
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount(f"/{settings.UPLOAD_DIR}", StaticFiles(directory=str(upload_dir)), name="uploads")

# 初始化数据库
from app.database import init_db

@app.on_event("startup")
async def startup():
    """应用启动事件"""
    try:
        init_db()
        logger.info("数据库表初始化成功")

        # 初始化RBAC默认角色和权限
        from app.services.permission_service import PermissionService
        from app.api.deps import get_db
        db = next(get_db())
        try:
            PermissionService.initialize_default_roles(db)
            logger.info("RBAC默认角色和权限初始化成功")
        except Exception as e:
            logger.warning(f"RBAC初始化警告: {str(e)}")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")

    # 检查AI API
    try:
        from app.services.ai import get_deepseek_client
        client = await get_deepseek_client()
        is_healthy = await client.health_check()
        logger.info(f"DeepSeek API 状态: {'正常' if is_healthy else '异常'}")
    except Exception as e:
        logger.warning(f"DeepSeek API 初始化失败: {str(e)}")
