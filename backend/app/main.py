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

# P1-架构修复: 使用集中化路由管理
from app.api.v1.router import api_router
from app.api.admin_router import admin_router

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
# 注意: FastAPI 中间件后注册先执行（栈结构）
# 执行顺序: CORS → RateLimit → Performance → 路由处理器

# CORS配置 - 根据环境动态配置（最先注册，最后执行，包裹所有其他中间件）
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
        logger.warning("CORS_ORIGINS not configured, using default origins")
        cors_origins = [
            "http://localhost",
            "http://localhost:80",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8080",
        ]
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

# 频率限制中间件（在 CORS 之后注册，先于 CORS 执行）
from app.middleware.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# 性能监控中间件（最后注册，最先执行，紧贴路由处理器）
from app.middleware.performance import PerformanceMiddleware
app.add_middleware(PerformanceMiddleware)


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

# P1-架构修复: 使用集中化路由管理，统一 /api/v1 前缀
app.include_router(api_router, prefix="/api/v1")

# 管理员路由使用 /api/admin 前缀
app.include_router(admin_router, prefix="/api/admin")

# 挂载静态文件目录（用于访问上传的媒体文件）
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount(f"/{settings.UPLOAD_DIR}", StaticFiles(directory=str(upload_dir)), name="uploads")

# 初始化数据库
from app.database import init_db, SessionLocal

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

            # 种子系统企业 + 管理员用户
            from app.models.user import User, UserRole, UserStatus, UserType
            from app.models.enterprise import Enterprise, VerifyStatus, PlanType
            from app.models.base import generate_uuid
            from passlib.context import CryptContext

            sys_enterprise = db.query(Enterprise).filter(Enterprise.license_no == "SYSTEM-000000").first()
            if not sys_enterprise:
                sys_enterprise = Enterprise(
                    enterprise_uuid=generate_uuid(),
                    name="蒙智云平台",
                    license_no="SYSTEM-000000",
                    contact_name="系统管理员",
                    verify_status=VerifyStatus.VERIFIED,
                    plan_type=PlanType.ENTERPRISE,
                )
                db.add(sys_enterprise)
                db.flush()
                logger.info(f"系统默认企业已创建: id={sys_enterprise.id}")

            admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
            if not admin:
                pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
                admin = User(
                    user_uuid=generate_uuid(),
                    username="admin",
                    email="admin@mengzhi.cloud",
                    password_hash=pwd_ctx.hash("admin123"),
                    user_type=UserType.PERSONAL,
                    status=UserStatus.ACTIVE,
                    role=UserRole.ADMIN,
                    enterprise_id=sys_enterprise.id,
                )
                db.add(admin)
                db.commit()
                logger.info("默认管理员已创建: admin / admin123")
            else:
                if not admin.enterprise_id:
                    admin.enterprise_id = sys_enterprise.id
                    db.commit()
                    logger.info("管理员已绑定系统企业")
                else:
                    logger.info("管理员用户已存在，跳过种子")
        except Exception as e:
            logger.warning(f"RBAC初始化警告: {str(e)}")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")

    # 种子内容生成模板
    try:
        db = SessionLocal()
        try:
            from app.models.generation_template import GenerationTemplate, TemplateContentType, TemplatePlatform
            existing = db.query(GenerationTemplate).filter(GenerationTemplate.is_system == True).count()
            if existing == 0:
                seed_templates = [
                    GenerationTemplate(
                        name="产品营销文案",
                        description="为内蒙古特色农畜产品生成专业营销文案，突出产地优势和品质特点",
                        content_type=TemplateContentType.COPY,
                        platform=TemplatePlatform.GENERAL,
                        category="marketing",
                        system_prompt="你是一位专业的农畜产品营销文案专家。你擅长为内蒙古特色农畜产品撰写具有吸引力的营销文案，能够突出产品的产地优势、品质特点和文化底蕴。",
                        user_prompt_template='请为产品"{product_name}"撰写一段{word_count}字左右的营销文案。\n风格要求：{style}\n目标受众：{audience}',
                        variables=[
                            {"name": "product_name", "label": "产品名称", "required": True},
                            {"name": "word_count", "label": "字数", "required": True},
                            {"name": "style", "label": "风格", "required": False},
                            {"name": "audience", "label": "目标受众", "required": False},
                        ],
                        example_output="来自锡林郭勒大草原的天然牧场，每一口都是草原的馈赠。精选优质羊肉，肉质鲜嫩多汁，无膻味，富含蛋白质和多种微量元素。从牧场到餐桌，全程冷链配送，锁住新鲜与美味。",
                        model_config={"temperature": 0.7},
                        is_system=True,
                        is_active=True,
                    ),
                    GenerationTemplate(
                        name="直播带货脚本",
                        description="生成适合直播电商的产品介绍话术和互动脚本",
                        content_type=TemplateContentType.SCRIPT,
                        platform=TemplatePlatform.DOUYIN,
                        category="social",
                        system_prompt="你是一位经验丰富的直播电商脚本策划师。你擅长撰写带货直播话术，善于营造紧迫感和信任感，引导观众下单。",
                        user_prompt_template='请为产品"{product_name}"写一段直播带货脚本。\n时长约{word_count}字\n风格：{style}',
                        variables=[
                            {"name": "product_name", "label": "产品名称", "required": True},
                            {"name": "word_count", "label": "字数", "required": True},
                            {"name": "style", "label": "风格", "required": False},
                        ],
                        example_output="家人们看过来！这款正宗的科尔沁牛肉干，我们的粉丝专属价只要39.9！原价可是89啊！你们看这色泽，这纹理，咬一口满嘴都是牛肉的香气...",
                        model_config={"temperature": 0.8},
                        is_system=True,
                        is_active=True,
                    ),
                    GenerationTemplate(
                        name="短视频文案",
                        description="生成适合抖音、快手等短视频平台的产品展示文案",
                        content_type=TemplateContentType.VIDEO_COPY,
                        platform=TemplatePlatform.DOUYIN,
                        category="video",
                        system_prompt="你是一位短视频内容创作者，擅长用简洁有力的文案配合视觉画面，吸引用户停留和互动。",
                        user_prompt_template='请为产品"{product_name}"写一段短视频文案。\n字数约{word_count}字\n风格：{style}',
                        variables=[
                            {"name": "product_name", "label": "产品名称", "required": True},
                            {"name": "word_count", "label": "字数", "required": True},
                            {"name": "style", "label": "风格", "required": False},
                        ],
                        example_output="你以为内蒙古只有草原？不，还有藏在草原深处的这口鲜奶。0添加，0防腐剂，从牧场到你手里不超过48小时。喝过的都说回不去了...",
                        model_config={"temperature": 0.85},
                        is_system=True,
                        is_active=True,
                    ),
                    GenerationTemplate(
                        name="品牌故事",
                        description="为品牌或产品撰写有温度的品牌叙事内容",
                        content_type=TemplateContentType.STORY,
                        platform=TemplatePlatform.WECHAT,
                        category="marketing",
                        system_prompt="你是一位品牌叙事专家，擅长挖掘品牌背后的故事，用富有感染力的文字打动读者，建立品牌与消费者之间的情感连接。",
                        user_prompt_template='请为品牌/产品"{product_name}"撰写一段品牌故事。\n字数约{word_count}字\n风格：{style}\n目标受众：{audience}',
                        variables=[
                            {"name": "product_name", "label": "产品名称", "required": True},
                            {"name": "word_count", "label": "字数", "required": True},
                            {"name": "style", "label": "风格", "required": False},
                            {"name": "audience", "label": "目标受众", "required": False},
                        ],
                        example_output="在呼伦贝尔的深处，有一个叫巴尔虎的地方。这里的牧民世世代代逐水草而居，他们对草原的敬畏，融入了每一滴牛奶、每一块奶酪之中...",
                        model_config={"temperature": 0.75},
                        is_system=True,
                        is_active=True,
                    ),
                    GenerationTemplate(
                        name="广告标语",
                        description="生成简洁有力的广告语和品牌标语",
                        content_type=TemplateContentType.SLOGAN,
                        platform=TemplatePlatform.GENERAL,
                        category="marketing",
                        system_prompt="你是一位广告创意总监，擅长用最精炼的文字传递品牌价值，创作令人过目不忘的广告标语。",
                        user_prompt_template='请为产品"{product_name}"创作{word_count}条广告标语。\n风格：{style}',
                        variables=[
                            {"name": "product_name", "label": "产品名称", "required": True},
                            {"name": "word_count", "label": "数量", "required": True},
                            {"name": "style", "label": "风格", "required": False},
                        ],
                        example_output="1. 草原的味道，家的温度\n2. 天然牧场，自然好味\n3. 一口草原鲜，千里牧歌情",
                        model_config={"temperature": 0.9},
                        is_system=True,
                        is_active=True,
                    ),
                ]
                db.add_all(seed_templates)
                db.commit()
                logger.info(f"已种子化 {len(seed_templates)} 个系统内容生成模板")
            else:
                logger.info(f"内容生成模板已存在({existing}个)，跳过种子")
        except Exception as e:
            logger.warning(f"模板种子化失败: {str(e)}")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"模板种子化异常: {str(e)}")

    # 检查AI API
    try:
        from app.services.ai import get_deepseek_client
        client = await get_deepseek_client()
        is_healthy = await client.health_check()
        logger.info(f"DeepSeek API 状态: {'正常' if is_healthy else '异常'}")
    except Exception as e:
        logger.warning(f"DeepSeek API 初始化失败: {str(e)}")

    # 启动定时任务调度器（对账 + 淘宝 Session 自动刷新）
    try:
        from app.tasks.scheduler import reconciliation_scheduler
        reconciliation_scheduler.start()
    except Exception as e:
        logger.warning(f"定时任务调度器启动失败: {str(e)}")
