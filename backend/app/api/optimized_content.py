"""
优化内容生成API路由集成 - AI-007

将优化的内容生成服务集成到FastAPI路由

版本: 2.0 (优化版)
更新日期: 2026-01-17
"""

import asyncio
import time

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from typing import Optional, List, Any, Dict
from loguru import logger

from app.core.responses import success_response
from app.services.optimized_content_generation import ContentGenerationServiceFactory
from app.models.content_record import ContentType, Style, Platform
from app.api.deps import get_db

# 生成任务超时（秒）
_GENERATE_TIMEOUT = 60

# 允许的枚举值白名单（用于输入校验错误提示）
_VALID_CONTENT_TYPES = {e.name.lower() for e in ContentType}
_VALID_STYLES = {e.name.lower() for e in Style}
_VALID_PLATFORMS = {e.name.lower() for e in Platform}

# 创建路由（prefix 由 v1/router.py 的 include_router 统一管理）
router = APIRouter(tags=["内容生成 - Content Generation"])


# ==================== 请求体 Schema ====================

class GenerationConfigBody(BaseModel):
    """生成配置（匹配前端 GenerationConfig 格式）"""
    product_ids: Optional[List[str]] = None
    template_id: Optional[str] = None
    count: int = 1
    style: str = "casual"
    word_count: int = 200
    target_audience: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    avoid_words: Optional[str] = None
    temperature: float = 0.7
    platform: str = "general"
    content_type: str = "copy"

    @field_validator("word_count")
    @classmethod
    def validate_word_count(cls, v: int) -> int:
        if v < 50 or v > 2000:
            raise ValueError("word_count 必须在 50~2000 之间")
        return v

    @field_validator("style")
    @classmethod
    def validate_style(cls, v: str) -> str:
        if v.upper() not in {e.name for e in Style}:
            raise ValueError(f"无效的风格，允许值: {', '.join(e.name.lower() for e in Style)}")
        return v

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        if v.upper() not in {e.name for e in Platform}:
            raise ValueError(f"无效的平台，允许值: {', '.join(e.name.lower() for e in Platform)}")
        return v

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        if v.upper() not in {e.name for e in ContentType}:
            raise ValueError(f"无效的内容类型，允许值: {', '.join(e.name.lower() for e in ContentType)}")
        return v


class GenerateContentBody(BaseModel):
    """生成内容请求体（匹配前端 GenerationRequest）"""
    config: Optional[GenerationConfigBody] = None
    batch_id: Optional[str] = None
    # 也支持直接字段（兼容 query param 格式）
    product_id: Optional[int] = None
    content_type: Optional[str] = None
    style: Optional[str] = None
    platform: Optional[str] = None
    word_count: Optional[int] = None


@router.post("/generate", response_model=dict)
async def generate_content(
    body: Optional[GenerateContentBody] = None,
    product_id: Optional[int] = Query(None, description="产品ID（可在query或body中传入）"),
    content_type: str = Query("copy", description="内容类型"),
    style: str = Query("casual", description="风格"),
    platform: str = Query("general", description="目标平台"),
    word_count: int = Query(200, ge=50, le=2000, description="目标字数（50~2000）"),
    db: Session = Depends(get_db)
):
    """
    生成优化的产品内容

    支持两种调用方式：
    1. Query params: ?product_id=1&content_type=copy&style=casual&platform=general&word_count=200
    2. JSON body: {"config": {"product_ids": ["1"], "style": "professional", ...}}

    返回：
    - 生成的内容
    - 质量评分
    """
    try:
        # 优先从 body 中提取参数
        if body:
            if body.config:
                cfg = body.config
                # 从 config.product_ids 获取第一个 product_id
                if cfg.product_ids and not product_id:
                    try:
                        product_id = int(cfg.product_ids[0])
                    except (ValueError, IndexError) as e:
                        logger.warning(f"无效的 product_id 值: {cfg.product_ids}, 错误: {e}")
                content_type = cfg.content_type or content_type
                style = cfg.style or style
                platform = cfg.platform or platform
                word_count = cfg.word_count or word_count
            elif body.product_id:
                product_id = body.product_id
                content_type = body.content_type or content_type
                style = body.style or style
                platform = body.platform or platform
                word_count = body.word_count or word_count

        if not product_id:
            raise HTTPException(status_code=400, detail="缺少 product_id 参数")

        # word_count 范围校验（body 路径可能绕过 Query 约束）
        if not (50 <= word_count <= 2000):
            raise HTTPException(status_code=400, detail="word_count 必须在 50~2000 之间")

        # 参数验证和转换（使用白名单，避免回显用户输入）
        try:
            content_type_enum = ContentType[content_type.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的内容类型，允许值: {', '.join(e.name.lower() for e in ContentType)}"
            )

        try:
            style_enum = Style[style.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的风格，允许值: {', '.join(e.name.lower() for e in Style)}"
            )

        try:
            platform_enum = Platform[platform.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的平台，允许值: {', '.join(e.name.lower() for e in Platform)}"
            )

        # 获取优化的生成服务
        service = await ContentGenerationServiceFactory.get_service(db)

        # 生成内容（带超时保护）
        try:
            generated_content = await asyncio.wait_for(
                service.generate_product_copy(
                    product_id=product_id,
                    content_type=content_type_enum,
                    style=style_enum,
                    platform=platform_enum,
                    word_count=word_count
                ),
                timeout=_GENERATE_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.error(f"内容生成超时 (product_id={product_id}, timeout={_GENERATE_TIMEOUT}s)")
            raise HTTPException(status_code=504, detail="内容生成超时，请稍后重试")

        return success_response(
            data={
                "content": generated_content,
                "length": len(generated_content),
                "content_type": content_type,
                "style": style,
                "platform": platform
            },
            message="内容生成成功"
        ).dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"内容生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail="内容生成失败")


@router.post("/generate-variants", response_model=dict)
async def generate_content_variants(
    product_id: int = Query(..., description="产品ID"),
    count: int = Query(3, ge=1, le=10, description="生成数量"),
    content_type: str = Query("copy", description="内容类型"),
    style: str = Query("casual", description="风格"),
    platform: str = Query("general", description="目标平台"),
    word_count: int = Query(200, ge=50, le=2000, description="目标字数（50~2000）"),
    db: Session = Depends(get_db)
):
    """
    生成多个内容变体（用于A/B测试）

    参数：
    - product_id: 产品ID
    - count: 生成数量 (1-10)
    - content_type: 内容类型
    - style: 风格
    - platform: 平台
    - word_count: 目标字数（50~2000）

    返回：
    - 内容变体列表
    """
    try:
        # 参数验证
        try:
            content_type_enum = ContentType[content_type.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的内容类型，允许值: {', '.join(e.name.lower() for e in ContentType)}"
            )

        try:
            style_enum = Style[style.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的风格，允许值: {', '.join(e.name.lower() for e in Style)}"
            )

        try:
            platform_enum = Platform[platform.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的平台，允许值: {', '.join(e.name.lower() for e in Platform)}"
            )

        # 获取服务
        service = await ContentGenerationServiceFactory.get_service(db)

        # 生成多个变体（带超时保护，变体数量越多超时越长）
        variant_timeout = _GENERATE_TIMEOUT * count
        try:
            variants = await asyncio.wait_for(
                service.generate_multiple_variants(
                    product_id=product_id,
                    count=count,
                    content_type=content_type_enum,
                    style=style_enum,
                    platform=platform_enum,
                    word_count=word_count
                ),
                timeout=variant_timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"变体生成超时 (product_id={product_id}, count={count}, timeout={variant_timeout}s)")
            raise HTTPException(status_code=504, detail="内容生成超时，请减少变体数量后重试")

        return success_response(
            data={
                "variants": variants,
                "count": len(variants),
                "content_type": content_type,
                "style": style,
                "platform": platform
            },
            message=f"成功生成 {len(variants)} 个内容变体"
        ).dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成变体失败: {str(e)}")
        raise HTTPException(status_code=500, detail="生成变体失败")


@router.get("/content-types")
async def get_content_types():
    """获取支持的内容类型"""
    return success_response(
        data={
            "content_types": [
                {"value": "copy", "label": "营销文案"},
                {"value": "script", "label": "直播脚本"},
                {"value": "video_copy", "label": "短视频文案"},
                {"value": "slogan", "label": "广告标语"},
                {"value": "story", "label": "品牌故事"}
            ]
        },
        message="获取内容类型成功"
    ).dict()


@router.get("/styles")
async def get_styles():
    """获取支持的风格"""
    return success_response(
        data={
            "styles": [
                {"value": "formal", "label": "正式"},
                {"value": "casual", "label": "轻松"},
                {"value": "humorous", "label": "幽默"},
                {"value": "emotional", "label": "情感"},
                {"value": "professional", "label": "专业"}
            ]
        },
        message="获取风格成功"
    ).dict()


@router.get("/history")
async def get_history(
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """
    获取内容生成历史记录

    返回 ContentRecord 列表
    """
    try:
        from app.models.content_record import ContentRecord
        query = db.query(ContentRecord).order_by(ContentRecord.created_at.desc())
        total = query.count()
        records = query.offset(offset).limit(limit).all()

        return success_response(
            data={
                "items": [r.to_dict() if hasattr(r, 'to_dict') else {
                    "id": r.id,
                    "content_type": r.content_type.value if hasattr(r.content_type, 'value') else str(r.content_type),
                    "status": r.status.value if hasattr(r.status, 'value') else str(r.status),
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                } for r in records],
                "total": total,
                "limit": limit,
                "offset": offset
            },
            message="获取历史记录成功"
        ).dict()
    except Exception as e:
        logger.error(f"获取历史记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取历史记录失败")


@router.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """
    获取内容生成统计数据
    """
    try:
        from app.models.content_record import ContentRecord
        from sqlalchemy import func

        total_count = db.query(func.count(ContentRecord.id)).scalar() or 0

        return success_response(
            data={
                "total_generations": total_count,
                "today_generations": 0,
                "total_tokens_used": 0,
                "by_type": {},
                "by_platform": {},
                "recent_trend": []
            },
            message="获取统计数据成功"
        ).dict()
    except Exception as e:
        logger.error(f"获取统计数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取统计数据失败")


@router.get("/platforms")
async def get_platforms():
    """获取支持的平台"""
    return success_response(
        data={
            "platforms": [
                {"value": "douyin", "label": "抖音"},
                {"value": "xiaohongshu", "label": "小红书"},
                {"value": "wechat", "label": "微信公众号"},
                {"value": "weibo", "label": "微博"},
                {"value": "kuaishou", "label": "快手"},
                {"value": "general", "label": "通用"}
            ]
        },
        message="获取平台成功"
    ).dict()


# ==================== Stub 端点（前端已调用，后端尚未完整实现） ====================


@router.get("/templates")
async def get_templates(category: Optional[str] = None):
    """获取内容模板列表（stub）"""
    templates = [
        {"id": "product-copy", "name": "产品文案", "category": "marketing", "description": "生成产品营销文案"},
        {"id": "live-script", "name": "直播脚本", "category": "live", "description": "生成直播间话术脚本"},
        {"id": "short-video", "name": "短视频文案", "category": "video", "description": "生成短视频拍摄文案"},
        {"id": "brand-story", "name": "品牌故事", "category": "brand", "description": "生成品牌叙事内容"},
        {"id": "ad-slogan", "name": "广告标语", "category": "marketing", "description": "生成广告语和标语"},
    ]
    if category:
        templates = [t for t in templates if t["category"] == category]
    return success_response(data=templates, message="获取模板列表成功").dict()


@router.get("/templates/{template_id}")
async def get_template_detail(template_id: str):
    """获取模板详情（stub）"""
    return success_response(
        data={"id": template_id, "name": template_id, "category": "general", "description": "", "fields": []},
        message="获取模板详情成功"
    ).dict()


@router.get("/tasks")
async def get_tasks():
    """获取批量任务列表（stub）"""
    return success_response(data=[], message="获取任务列表成功").dict()


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取批量任务状态（stub）"""
    raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """取消批量任务（stub）"""
    raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")


@router.get("/tasks/{task_id}/export/{fmt}")
async def export_task_result(task_id: str, fmt: str):
    """导出任务结果（stub）"""
    raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")


@router.get("/configs")
async def get_saved_configs():
    """获取已保存的配置列表（stub）"""
    return success_response(data=[], message="获取配置列表成功").dict()


@router.post("/configs")
async def save_config(body: Optional[Dict[str, Any]] = Body(None)):
    """保存配置（stub）"""
    config_id = f"config-{int(time.time() * 1000)}"
    return success_response(
        data={"id": config_id, "name": (body or {}).get("name", ""), "config": (body or {}).get("config", {})},
        message="配置已保存"
    ).dict()


@router.get("/configs/{config_id}")
async def get_saved_config(config_id: str):
    """获取单个配置（stub）"""
    raise HTTPException(status_code=404, detail=f"配置 {config_id} 不存在")


@router.delete("/configs/{config_id}")
async def delete_saved_config(config_id: str):
    """删除配置（stub）"""
    raise HTTPException(status_code=404, detail=f"配置 {config_id} 不存在")
