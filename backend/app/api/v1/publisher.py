"""
多平台内容分发 API 路由

提供:
- POST /publisher/publish               一键发布到多平台
- GET  /publisher/records               发布记录列表
- GET  /publisher/records/{uuid}        发布详情 + 表现数据
- POST /publisher/records/{uuid}/retry  重试失败发布
- POST /publisher/metrics/ingest        表现数据采集
- GET  /publisher/metrics/summary       Dashboard 聚合
- GET  /publisher/platforms             支持的平台列表

版本: 1.0
创建日期: 2026-06-17
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from app.core.database import get_db
from app.core.responses import success_response
from app.api.deps import get_current_user
from app.services.publisher import ContentPublisherService
from app.services.publisher.registry import PublisherRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/publisher", tags=["内容分发 - Publisher"])


# ============ Request Models ============


class PublishRequestBody(BaseModel):
    """发布请求"""

    content_record_id: int = Field(..., description="内容记录ID", gt=0)
    platforms: List[str] = Field(
        ..., description="目标平台列表", min_items=1, max_items=4,
        example=["douyin", "xiaohongshu"]
    )


class IngestMetricBody(BaseModel):
    """表现数据采集请求"""

    publish_record_id: int = Field(..., gt=0, description="发布记录ID")
    metric_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="数据日期 YYYY-MM-DD")
    pv: int = Field(0, ge=0, description="浏览量")
    uv: int = Field(0, ge=0, description="独立访客")
    like_count: int = Field(0, ge=0, description="点赞数")
    share_count: int = Field(0, ge=0, description="分享数")
    comment_count: int = Field(0, ge=0, description="评论数")
    favorite_count: int = Field(0, ge=0, description="收藏数")
    conversion_count: int = Field(0, ge=0, description="转化数")


# ============ API Endpoints ============


@router.post("/publish")
async def publish_content(
    body: PublishRequestBody,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    一键发布到多平台 (Mock 模式)

    - **content_record_id**: 内容记录ID (需属于当前用户)
    - **platforms**: 平台列表, 如 ["douyin", "xiaohongshu"]
    """
    try:
        user_id = int(current_user["user_id"])
        service = ContentPublisherService(db)
        result = await service.publish(
            user_id=user_id,
            content_record_id=body.content_record_id,
            platforms=body.platforms,
        )
        return success_response(data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"⚠️ WARNING: publish failed: {e}")
        raise HTTPException(status_code=500, detail=f"发布失败: {str(e)}")


@router.get("/records")
async def list_records(
    platform: Optional[str] = Query(None, description="平台筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """列出当前用户的发布记录"""
    user_id = int(current_user["user_id"])
    service = ContentPublisherService(db)
    result = service.list_user_records(
        user_id=user_id,
        platform=platform,
        status=status,
        page=page,
        page_size=page_size,
    )
    return success_response(data=result)


@router.get("/records/{publish_uuid}")
async def get_record(
    publish_uuid: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取发布详情 + 表现数据"""
    user_id = int(current_user["user_id"])
    service = ContentPublisherService(db)
    detail = service.get_record_detail(user_id, publish_uuid)
    if not detail:
        raise HTTPException(status_code=404, detail="发布记录不存在")
    return success_response(data=detail)


@router.post("/records/{publish_uuid}/retry")
async def retry_record(
    publish_uuid: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """重试失败的发布"""
    try:
        user_id = int(current_user["user_id"])
        service = ContentPublisherService(db)
        result = await service.retry_failed(user_id, publish_uuid)
        return success_response(data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"⚠️ WARNING: retry failed: {e}")
        raise HTTPException(status_code=500, detail=f"重试失败: {str(e)}")


@router.post("/metrics/ingest")
async def ingest_metric(
    body: IngestMetricBody,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """表现数据采集 (同一 publish_record + date 唯一, upsert)"""
    try:
        # user_id 校验: 确保 publish_record 属于当前用户
        from app.models import PublishRecord

        record = (
            db.query(PublishRecord)
            .filter(PublishRecord.id == body.publish_record_id)
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="发布记录不存在")
        if record.user_id != int(current_user["user_id"]):
            raise HTTPException(status_code=403, detail="无权操作此发布记录")

        service = ContentPublisherService(db)
        metric = await service.ingest_metrics(
            publish_record_id=body.publish_record_id,
            metric_date=body.metric_date,
            pv=body.pv,
            uv=body.uv,
            like_count=body.like_count,
            share_count=body.share_count,
            comment_count=body.comment_count,
            favorite_count=body.favorite_count,
            conversion_count=body.conversion_count,
        )
        return success_response(data=metric.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"⚠️ WARNING: metric ingest failed: {e}")
        raise HTTPException(status_code=500, detail=f"采集失败: {str(e)}")


@router.get("/metrics/summary")
async def metrics_summary(
    start_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    platform: Optional[str] = Query(None),
    product_id: Optional[int] = Query(None, gt=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Dashboard 聚合数据 (按平台 + 按日期)"""
    user_id = int(current_user["user_id"])
    service = ContentPublisherService(db)
    summary = service.get_metrics_summary(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        platform=platform,
        product_id=product_id,
    )
    return success_response(data=summary)


@router.get("/platforms")
async def list_platforms():
    """列出支持的发布平台"""
    registry = PublisherRegistry()
    return success_response(
        data={
            "platforms": registry.list_platforms(),
            "mode": "mock",
            "note": "当前为 Mock 模式 (PUBLISHER_MODE=mock), URL 以 mock. 开头",
        }
    )
