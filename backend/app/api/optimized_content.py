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
from app.api.deps import get_db, get_current_user, require_admin

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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    生成优化的产品内容

    支持两种调用方式：
    1. Query params: ?product_id=1&content_type=copy&style=casual&platform=general&word_count=200
    2. JSON body: {"config": {"product_ids": ["1"], "style": "professional", ...}}

    生成成功后自动保存 ContentRecord 到数据库。
    """
    from app.models.content_record import ContentRecord, RecordStatus, LengthType
    from app.models.user import User

    # 获取当前用户整数 ID
    user_uuid = current_user.get("user_id")
    user_obj = db.query(User).filter(User.user_uuid == user_uuid).first()
    if not user_obj:
        raise HTTPException(status_code=401, detail="用户不存在")

    # 从 body.config 提取完整参数
    template_id = None
    count = 1
    keywords = None
    avoid_words = None
    target_audience = None
    temperature = None

    if body and body.config:
        cfg = body.config
        if cfg.product_ids and not product_id:
            try:
                product_id = int(cfg.product_ids[0])
            except (ValueError, IndexError) as e:
                logger.warning(f"无效的 product_id 值: {cfg.product_ids}, 错误: {e}")
        content_type = cfg.content_type or content_type
        style = cfg.style or style
        platform = cfg.platform or platform
        word_count = cfg.word_count if cfg.word_count is not None else word_count
        template_id = cfg.template_id or None
        count = cfg.count if cfg.count and cfg.count >= 1 else 1
        keywords = cfg.keywords or None
        avoid_words = cfg.avoid_words or None
        target_audience = cfg.target_audience or None
        temperature = cfg.temperature
    elif body and body.product_id:
        product_id = body.product_id
        content_type = body.content_type or content_type
        style = body.style or style
        platform = body.platform or platform
        word_count = body.word_count or word_count

    if not product_id:
        raise HTTPException(status_code=400, detail="缺少 product_id 参数")

    if not (50 <= word_count <= 2000):
        raise HTTPException(status_code=400, detail="word_count 必须在 50~2000 之间")

    # 枚举转换
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

    # 确定长度类型
    if word_count < 500:
        length_type = LengthType.SHORT
    elif word_count <= 1500:
        length_type = LengthType.MEDIUM
    else:
        length_type = LengthType.LONG

    input_params = {
        "word_count": word_count,
        "template_id": template_id,
        "keywords": keywords,
        "avoid_words": avoid_words,
        "target_audience": target_audience,
        "temperature": temperature,
        "count": count,
    }

    start_time = time.time()

    try:
        service = await ContentGenerationServiceFactory.get_service(db)

        if count > 1:
            variant_timeout = min(_GENERATE_TIMEOUT * count, 180)
            try:
                variants = await asyncio.wait_for(
                    service.generate_multiple_variants(
                        product_id=product_id,
                        count=count,
                        content_type=content_type_enum,
                        style=style_enum,
                        platform=platform_enum,
                        word_count=word_count,
                        keywords=keywords,
                        avoid_words=avoid_words,
                        target_audience=target_audience,
                        temperature=temperature,
                        template_id=template_id,
                    ),
                    timeout=variant_timeout
                )
            except asyncio.TimeoutError:
                raise HTTPException(status_code=504, detail="内容生成超时，请减少变体数量后重试")

            elapsed_ms = int((time.time() - start_time) * 1000)

            result_list = []
            for variant_content in variants:
                record = ContentRecord(
                    user_id=user_obj.id,
                    product_id=product_id,
                    content_type=content_type_enum,
                    platform=platform_enum,
                    style=style_enum,
                    length_type=length_type,
                    input_params=input_params,
                    keywords=keywords,
                    generated_content=variant_content,
                    model_name="deepseek-chat",
                    generation_time_ms=elapsed_ms,
                    status=RecordStatus.COMPLETED,
                )
                db.add(record)
                db.flush()
                result_list.append({
                    "id": record.record_uuid,
                    "content": variant_content,
                    "length": len(variant_content),
                    "content_type": content_type,
                    "style": style,
                    "platform": platform,
                })
            db.commit()

            return success_response(data=result_list, message=f"成功生成 {len(result_list)} 个内容变体").dict()

        else:
            try:
                generated_content = await asyncio.wait_for(
                    service.generate_product_copy(
                        product_id=product_id,
                        content_type=content_type_enum,
                        style=style_enum,
                        platform=platform_enum,
                        word_count=word_count,
                        keywords=keywords,
                        avoid_words=avoid_words,
                        target_audience=target_audience,
                        temperature=temperature,
                        template_id=template_id,
                    ),
                    timeout=_GENERATE_TIMEOUT
                )
            except asyncio.TimeoutError:
                raise HTTPException(status_code=504, detail="内容生成超时，请稍后重试")

            elapsed_ms = int((time.time() - start_time) * 1000)

            record = ContentRecord(
                user_id=user_obj.id,
                product_id=product_id,
                content_type=content_type_enum,
                platform=platform_enum,
                style=style_enum,
                length_type=length_type,
                input_params=input_params,
                keywords=keywords,
                generated_content=generated_content,
                model_name="deepseek-chat",
                generation_time_ms=elapsed_ms,
                status=RecordStatus.COMPLETED,
            )
            db.add(record)
            db.commit()

            return success_response(
                data={
                    "id": record.record_uuid,
                    "content": generated_content,
                    "length": len(generated_content),
                    "content_type": content_type,
                    "style": style,
                    "platform": platform,
                },
                message="内容生成成功"
            ).dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"内容生成失败: {str(e)}")
        try:
            fail_record = ContentRecord(
                user_id=user_obj.id,
                product_id=product_id,
                content_type=content_type_enum,
                platform=platform_enum,
                style=style_enum,
                length_type=length_type,
                input_params=input_params,
                keywords=keywords,
                generated_content="",
                status=RecordStatus.FAILED,
                error_message=str(e)[:500],
            )
            db.add(fail_record)
            db.commit()
        except Exception as save_err:
            logger.warning(f"保存失败记录异常: {save_err}")
        raise HTTPException(status_code=500, detail="内容生成失败")


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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取内容生成历史记录

    返回结构匹配前端 HistoryRecord 类型
    """
    try:
        from app.models.content_record import ContentRecord
        from app.models.user import User

        user_uuid = current_user.get("user_id")
        user_obj = db.query(User).filter(User.user_uuid == user_uuid).first()
        if not user_obj:
            raise HTTPException(status_code=401, detail="用户不存在")

        query = db.query(ContentRecord).filter(
            ContentRecord.user_id == user_obj.id
        ).order_by(ContentRecord.created_at.desc())
        total = query.count()
        records = query.offset(offset).limit(limit).all()

        items = []
        for r in records:
            input_p = r.input_params or {}
            items.append({
                "id": r.record_uuid,
                "task_id": r.record_uuid,
                "template_id": input_p.get("template_id", ""),
                "config": {
                    "product_ids": [str(r.product_id)] if r.product_id else [],
                    "template_id": input_p.get("template_id", ""),
                    "count": input_p.get("count", 1),
                    "style": r.style.value if r.style else "casual",
                    "word_count": input_p.get("word_count", 200),
                    "target_audience": input_p.get("target_audience", []),
                    "keywords": r.keywords or input_p.get("keywords", []),
                    "avoid_words": input_p.get("avoid_words", ""),
                    "temperature": input_p.get("temperature", 0.7),
                },
                "results": [{
                    "id": r.record_uuid,
                    "template_id": input_p.get("template_id", ""),
                    "product_id": str(r.product_id) if r.product_id else "",
                    "content": r.generated_content or "",
                    "word_count": len(r.generated_content.replace(" ", "").replace("\n", "")) if r.generated_content else 0,
                    "rating": r.user_rating or 0,
                    "edited": bool(r.edited_content),
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                }],
                "status": r.status.value if r.status else "completed",
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

        return success_response(
            data={"items": items, "total": total, "limit": limit, "offset": offset},
            message="获取历史记录成功"
        ).dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取历史记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取历史记录失败")


@router.get("/statistics")
async def get_statistics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取内容生成统计数据（真实查询）"""
    try:
        from app.models.content_record import ContentRecord
        from sqlalchemy import func, cast, Date
        from datetime import date, timedelta

        today = date.today()

        total_count = db.query(func.count(ContentRecord.id)).scalar() or 0
        today_count = db.query(func.count(ContentRecord.id)).filter(
            cast(ContentRecord.created_at, Date) == today
        ).scalar() or 0
        total_tokens = db.query(func.coalesce(func.sum(ContentRecord.total_tokens), 0)).scalar() or 0

        by_type_rows = db.query(
            ContentRecord.content_type, func.count(ContentRecord.id)
        ).group_by(ContentRecord.content_type).all()
        by_type = {(row[0].value if hasattr(row[0], 'value') else str(row[0])): row[1] for row in by_type_rows}

        by_platform_rows = db.query(
            ContentRecord.platform, func.count(ContentRecord.id)
        ).group_by(ContentRecord.platform).all()
        by_platform = {(row[0].value if hasattr(row[0], 'value') else str(row[0])): row[1] for row in by_platform_rows}

        recent_trend = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_count = db.query(func.count(ContentRecord.id)).filter(
                cast(ContentRecord.created_at, Date) == day
            ).scalar() or 0
            recent_trend.append({"date": day.isoformat(), "count": day_count})

        return success_response(
            data={
                "total_generations": total_count,
                "today_generations": today_count,
                "total_tokens_used": int(total_tokens),
                "by_type": by_type,
                "by_platform": by_platform,
                "recent_trend": recent_trend,
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


@router.get("/templates")
async def get_templates(
    category: Optional[str] = Query(None, description="按类别筛选"),
    db: Session = Depends(get_db),
):
    """获取内容模板列表（从数据库读取）"""
    from app.models.generation_template import GenerationTemplate

    query = db.query(GenerationTemplate).filter(GenerationTemplate.is_active == True)
    if category:
        query = query.filter(GenerationTemplate.category == category)
    templates = query.order_by(GenerationTemplate.use_count.desc()).all()

    data = []
    for t in templates:
        data.append({
            "id": t.template_uuid,
            "category": t.category or "marketing",
            "name": t.name,
            "description": t.description or "",
            "sample": t.example_output or "",
            "difficulty": "medium",
            "usage_count": t.use_count or 0,
            "parameters": t.variables,
            "prompt": t.user_prompt_template,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        })

    return success_response(data=data, message="获取模板列表成功").dict()


@router.get("/templates/{template_id}")
async def get_template_detail(template_id: str, db: Session = Depends(get_db)):
    """获取模板详情"""
    from app.models.generation_template import GenerationTemplate

    tmpl = db.query(GenerationTemplate).filter(
        GenerationTemplate.template_uuid == template_id,
        GenerationTemplate.is_active == True,
    ).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="模板不存在")

    return success_response(
        data={
            "id": tmpl.template_uuid,
            "category": tmpl.category or "marketing",
            "name": tmpl.name,
            "description": tmpl.description or "",
            "sample": tmpl.example_output or "",
            "difficulty": "medium",
            "usage_count": tmpl.use_count or 0,
            "parameters": tmpl.variables,
            "prompt": tmpl.user_prompt_template,
            "system_prompt": tmpl.system_prompt,
            "created_at": tmpl.created_at.isoformat() if tmpl.created_at else None,
            "updated_at": tmpl.updated_at.isoformat() if tmpl.updated_at else None,
        },
        message="获取模板详情成功"
    ).dict()


@router.get("/tasks")
async def get_tasks():
    """批量任务功能暂未开放"""
    raise HTTPException(status_code=501, detail="批量任务功能暂未开放")


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """批量任务功能暂未开放"""
    raise HTTPException(status_code=501, detail="批量任务功能暂未开放")


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """批量任务功能暂未开放"""
    raise HTTPException(status_code=501, detail="批量任务功能暂未开放")


@router.get("/tasks/{task_id}/export/{fmt}")
async def export_task_result(task_id: str, fmt: str):
    """批量任务功能暂未开放"""
    raise HTTPException(status_code=501, detail="批量任务功能暂未开放")


@router.get("/configs")
async def get_saved_configs(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取已保存的配置列表"""
    from app.models.saved_config import SavedConfig
    from app.models.user import User

    user_obj = db.query(User).filter(User.user_uuid == current_user.get("user_id")).first()
    if not user_obj:
        raise HTTPException(status_code=401, detail="用户不存在")

    configs = db.query(SavedConfig).filter(
        SavedConfig.user_id == user_obj.id
    ).order_by(SavedConfig.created_at.desc()).all()

    return success_response(
        data=[c.to_dict() for c in configs],
        message="获取配置列表成功"
    ).dict()


@router.post("/configs")
async def save_config(
    body: Optional[Dict[str, Any]] = Body(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存配置"""
    from app.models.saved_config import SavedConfig
    from app.models.user import User

    user_obj = db.query(User).filter(User.user_uuid == current_user.get("user_id")).first()
    if not user_obj:
        raise HTTPException(status_code=401, detail="用户不存在")

    name = (body or {}).get("name", "")
    config_data = (body or {}).get("config", {})
    if not name:
        raise HTTPException(status_code=400, detail="配置名称不能为空")

    saved = SavedConfig(
        user_id=user_obj.id,
        name=name[:100],
        config=config_data,
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)

    return success_response(data=saved.to_dict(), message="配置已保存").dict()


@router.get("/configs/{config_id}")
async def get_saved_config(
    config_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单个配置"""
    from app.models.saved_config import SavedConfig
    from app.models.user import User

    user_obj = db.query(User).filter(User.user_uuid == current_user.get("user_id")).first()
    if not user_obj:
        raise HTTPException(status_code=401, detail="用户不存在")

    saved = db.query(SavedConfig).filter(
        SavedConfig.config_uuid == config_id,
        SavedConfig.user_id == user_obj.id,
    ).first()
    if not saved:
        raise HTTPException(status_code=404, detail="配置不存在")

    return success_response(data=saved.to_dict(), message="获取配置成功").dict()


@router.delete("/configs/{config_id}")
async def delete_saved_config(
    config_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除配置"""
    from app.models.saved_config import SavedConfig
    from app.models.user import User

    user_obj = db.query(User).filter(User.user_uuid == current_user.get("user_id")).first()
    if not user_obj:
        raise HTTPException(status_code=401, detail="用户不存在")

    saved = db.query(SavedConfig).filter(
        SavedConfig.config_uuid == config_id,
        SavedConfig.user_id == user_obj.id,
    ).first()
    if not saved:
        raise HTTPException(status_code=404, detail="配置不存在")

    db.delete(saved)
    db.commit()

    return success_response(data=None, message="配置已删除").dict()


# ==================== 模板管理（管理员） ====================

class TemplateCreateBody(BaseModel):
    """创建模板请求体"""
    name: str
    description: Optional[str] = None
    category: str = "marketing"
    content_type: str = "copy"
    platform: str = "general"
    system_prompt: str
    user_prompt_template: str
    variables: Optional[List[Any]] = None
    example_output: Optional[str] = None
    max_tokens: int = 2000
    is_active: bool = True


class TemplateUpdateBody(BaseModel):
    """更新模板请求体（所有字段可选）"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    content_type: Optional[str] = None
    platform: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    variables: Optional[List[Any]] = None
    example_output: Optional[str] = None
    max_tokens: Optional[int] = None
    is_active: Optional[bool] = None


def _template_to_dict(t) -> dict:
    return {
        "id": t.template_uuid,
        "category": t.category or "marketing",
        "name": t.name,
        "description": t.description or "",
        "sample": t.example_output or "",
        "difficulty": "medium",
        "usage_count": t.use_count or 0,
        "parameters": t.variables,
        "prompt": t.user_prompt_template,
        "system_prompt": t.system_prompt,
        "content_type": t.content_type.value if t.content_type else "copy",
        "platform": t.platform.value if t.platform else "general",
        "is_system": t.is_system or False,
        "is_active": t.is_active,
        "max_tokens": t.max_tokens,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


@router.post("/templates")
async def create_template(
    body: TemplateCreateBody,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """创建内容模板（管理员）"""
    from app.models.generation_template import GenerationTemplate, TemplateContentType, TemplatePlatform
    from app.models.user import User

    user_obj = db.query(User).filter(User.user_uuid == current_user.get("user_id")).first()

    try:
        content_type_enum = TemplateContentType[body.content_type.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"无效的内容类型: {body.content_type}")
    try:
        platform_enum = TemplatePlatform[body.platform.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"无效的平台: {body.platform}")

    tmpl = GenerationTemplate(
        name=body.name[:100],
        description=body.description,
        category=body.category,
        content_type=content_type_enum,
        platform=platform_enum,
        system_prompt=body.system_prompt,
        user_prompt_template=body.user_prompt_template,
        variables=body.variables or [],
        example_output=body.example_output,
        max_tokens=body.max_tokens,
        is_active=body.is_active,
        is_system=False,
        created_by=user_obj.id if user_obj else None,
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)

    return success_response(data=_template_to_dict(tmpl), message="模板创建成功").dict()


@router.put("/templates/{template_id}")
async def update_template(
    template_id: str,
    body: TemplateUpdateBody,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """更新内容模板（管理员）"""
    from app.models.generation_template import GenerationTemplate, TemplateContentType, TemplatePlatform

    tmpl = db.query(GenerationTemplate).filter(
        GenerationTemplate.template_uuid == template_id
    ).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="模板不存在")
    if tmpl.is_system:
        raise HTTPException(status_code=403, detail="系统内置模板不可修改")

    if body.name is not None:
        tmpl.name = body.name[:100]
    if body.description is not None:
        tmpl.description = body.description
    if body.category is not None:
        tmpl.category = body.category
    if body.content_type is not None:
        try:
            tmpl.content_type = TemplateContentType[body.content_type.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"无效的内容类型: {body.content_type}")
    if body.platform is not None:
        try:
            tmpl.platform = TemplatePlatform[body.platform.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"无效的平台: {body.platform}")
    if body.system_prompt is not None:
        tmpl.system_prompt = body.system_prompt
    if body.user_prompt_template is not None:
        tmpl.user_prompt_template = body.user_prompt_template
    if body.variables is not None:
        tmpl.variables = body.variables
    if body.example_output is not None:
        tmpl.example_output = body.example_output
    if body.max_tokens is not None:
        tmpl.max_tokens = body.max_tokens
    if body.is_active is not None:
        tmpl.is_active = body.is_active

    db.commit()
    db.refresh(tmpl)

    return success_response(data=_template_to_dict(tmpl), message="模板更新成功").dict()


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """删除内容模板（管理员，系统模板不可删除）"""
    from app.models.generation_template import GenerationTemplate

    tmpl = db.query(GenerationTemplate).filter(
        GenerationTemplate.template_uuid == template_id
    ).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="模板不存在")
    if tmpl.is_system:
        raise HTTPException(status_code=403, detail="系统内置模板不可删除")

    db.delete(tmpl)
    db.commit()

    return success_response(data=None, message="模板已删除").dict()
