"""
优化内容生成API路由集成 - AI-007

将优化的内容生成服务集成到FastAPI路由

版本: 2.0 (优化版)
更新日期: 2026-01-17
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from loguru import logger

from app.schemas.chat import ChatNonStreamResponse
from app.services.optimized_content_generation import ContentGenerationServiceFactory
from app.models.content_record import ContentType, Style, Platform
from app.database import get_db

# 创建路由
router = APIRouter(prefix="/api/v1/content", tags=["content_generation"])


@router.post("/generate", response_model=ChatNonStreamResponse)
async def generate_content(
    product_id: int = Query(..., description="产品ID"),
    content_type: str = Query("copy", description="内容类型"),
    style: str = Query("casual", description="风格"),
    platform: str = Query("general", description="目标平台"),
    word_count: int = Query(200, description="目标字数"),
    db: Session = Depends(get_db)
):
    """
    生成优化的产品内容

    参数：
    - product_id: 产品ID
    - content_type: 内容类型 (copy, script, video_copy, slogan, story)
    - style: 风格 (formal, casual, humorous, emotional, professional)
    - platform: 平台 (douyin, xiaohongshu, wechat, weibo, kuaishou, general)
    - word_count: 目标字数

    返回：
    - 生成的内容
    - 质量评分
    - 生成耗时等统计信息
    """
    try:
        # 参数验证和转换
        try:
            content_type_enum = ContentType[content_type.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"无效的内容类型: {content_type}")

        try:
            style_enum = Style[style.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"无效的风格: {style}")

        try:
            platform_enum = Platform[platform.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"无效的平台: {platform}")

        # 获取优化的生成服务
        service = await ContentGenerationServiceFactory.get_service(db)

        # 生成内容
        generated_content = await service.generate_product_copy(
            product_id=product_id,
            content_type=content_type_enum,
            style=style_enum,
            platform=platform_enum,
            word_count=word_count
        )

        return ChatNonStreamResponse(
            status="success",
            message="内容生成成功",
            data={
                "content": generated_content,
                "length": len(generated_content),
                "content_type": content_type,
                "style": style,
                "platform": platform
            }
        )

    except Exception as e:
        logger.error(f"内容生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"内容生成失败: {str(e)}")


@router.post("/generate-variants", response_model=ChatNonStreamResponse)
async def generate_content_variants(
    product_id: int = Query(..., description="产品ID"),
    count: int = Query(3, ge=1, le=10, description="生成数量"),
    content_type: str = Query("copy", description="内容类型"),
    style: str = Query("casual", description="风格"),
    platform: str = Query("general", description="目标平台"),
    word_count: int = Query(200, description="目标字数"),
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
    - word_count: 目标字数

    返回：
    - 内容变体列表
    """
    try:
        # 参数验证
        try:
            content_type_enum = ContentType[content_type.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"无效的内容类型: {content_type}")

        try:
            style_enum = Style[style.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"无效的风格: {style}")

        try:
            platform_enum = Platform[platform.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"无效的平台: {platform}")

        # 获取服务
        service = await ContentGenerationServiceFactory.get_service(db)

        # 生成多个变体
        variants = await service.generate_multiple_variants(
            product_id=product_id,
            count=count,
            content_type=content_type_enum,
            style=style_enum,
            platform=platform_enum,
            word_count=word_count
        )

        return ChatNonStreamResponse(
            status="success",
            message=f"成功生成 {len(variants)} 个内容变体",
            data={
                "variants": variants,
                "count": len(variants),
                "content_type": content_type,
                "style": style,
                "platform": platform
            }
        )

    except Exception as e:
        logger.error(f"生成变体失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成变体失败: {str(e)}")


@router.get("/content-types")
async def get_content_types():
    """获取支持的内容类型"""
    return {
        "content_types": [
            {"value": "copy", "label": "营销文案"},
            {"value": "script", "label": "直播脚本"},
            {"value": "video_copy", "label": "短视频文案"},
            {"value": "slogan", "label": "广告标语"},
            {"value": "story", "label": "品牌故事"}
        ]
    }


@router.get("/styles")
async def get_styles():
    """获取支持的风格"""
    return {
        "styles": [
            {"value": "formal", "label": "正式"},
            {"value": "casual", "label": "轻松"},
            {"value": "humorous", "label": "幽默"},
            {"value": "emotional", "label": "情感"},
            {"value": "professional", "label": "专业"}
        ]
    }


@router.get("/platforms")
async def get_platforms():
    """获取支持的平台"""
    return {
        "platforms": [
            {"value": "douyin", "label": "抖音"},
            {"value": "xiaohongshu", "label": "小红书"},
            {"value": "wechat", "label": "微信公众号"},
            {"value": "weibo", "label": "微博"},
            {"value": "kuaishou", "label": "快手"},
            {"value": "general", "label": "通用"}
        ]
    }
