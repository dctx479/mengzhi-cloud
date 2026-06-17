"""
效果监测 API 路由

提供:
- POST /effect/track                  记录单个事件
- POST /effect/track/batch            批量记录事件
- GET  /effect/dashboard              Dashboard 聚合 (实时聚合 EffectEvent)
- POST /effect/aggregate              手动触发每日聚合
- GET  /effect/snapshots              读聚合快照

版本: 1.0
创建日期: 2026-06-17
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.responses import success_response
from app.api.deps import get_current_user
from app.models import EffectType
from app.services.effect_service import EffectTrackingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/effect", tags=["效果监测 - Effect Analytics"])


# ============ Request Models ============


class TrackEventBody(BaseModel):
    """单事件记录请求"""

    event_type: str = Field(..., description="事件类型")
    product_id: Optional[int] = Field(None, gt=0)
    content_record_id: Optional[int] = Field(None, gt=0)
    publish_record_id: Optional[int] = Field(None, gt=0)
    platform: Optional[str] = Field(None, max_length=32)
    channel: Optional[str] = Field(None, max_length=64)
    extra_data: Optional[Dict[str, Any]] = None
    event_time: Optional[datetime] = None

    @validator("event_type")
    def validate_event_type(cls, v):
        valid = {t.value for t in EffectType}
        if v not in valid:
            raise ValueError(f"event_type 必须是 {valid} 之一")
        return v


class BatchTrackBody(BaseModel):
    """批量事件记录请求"""

    events: List[TrackEventBody] = Field(..., min_items=1, max_items=500)


# ============ API Endpoints ============


@router.post("/track")
async def track_event(
    body: TrackEventBody,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """记录单个效果事件"""
    try:
        user_id = int(current_user["user_id"])
        service = EffectTrackingService(db)
        event = service.track_event(
            event_type=EffectType(body.event_type),
            user_id=user_id,
            product_id=body.product_id,
            content_record_id=body.content_record_id,
            publish_record_id=body.publish_record_id,
            platform=body.platform,
            channel=body.channel,
            extra_data=body.extra_data,
            event_time=body.event_time,
        )
        return success_response(data=event.to_dict())
    except Exception as e:
        logger.error(f"⚠️ WARNING: track event failed: {e}")
        raise HTTPException(status_code=500, detail=f"事件记录失败: {str(e)}")


@router.post("/track/batch")
async def track_events_batch(
    body: BatchTrackBody,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """批量记录事件 (最多 500 条/批)"""
    try:
        user_id = int(current_user["user_id"])
        service = EffectTrackingService(db)
        events_payload = []
        for evt in body.events:
            events_payload.append(
                {
                    "event_type": evt.event_type,
                    "user_id": user_id,
                    "product_id": evt.product_id,
                    "content_record_id": evt.content_record_id,
                    "publish_record_id": evt.publish_record_id,
                    "platform": evt.platform,
                    "channel": evt.channel,
                    "extra_data": evt.extra_data,
                    "event_time": evt.event_time,
                }
            )
        count = service.batch_track_events(events_payload)
        return success_response(data={"inserted": count})
    except Exception as e:
        logger.error(f"⚠️ WARNING: batch track failed: {e}")
        raise HTTPException(status_code=500, detail=f"批量事件记录失败: {str(e)}")


@router.get("/dashboard")
async def dashboard_summary(
    start_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    scope: str = Query("me", description="me=仅本人数据, all=所有数据 (需 admin)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Dashboard 聚合 (实时聚合 EffectEvent 表)

    - **scope=me**: 仅返回当前用户的事件
    - **scope=all**: 返回所有数据 (仅 admin)
    """
    if scope == "all":
        # 仅 admin 可访问
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="需要 admin 权限")
        user_id = None
    else:
        user_id = int(current_user["user_id"])

    service = EffectTrackingService(db)
    summary = service.get_dashboard_summary(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )
    return success_response(data=summary)


@router.post("/aggregate")
async def aggregate_snapshot(
    target_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """手动触发每日聚合 (将 EffectEvent 聚合并 upsert 到 EffectMetricSnapshot)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要 admin 权限")
    try:
        service = EffectTrackingService(db)
        result = service.aggregate_daily_snapshot(target_date)
        return success_response(data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"⚠️ WARNING: aggregate failed: {e}")
        raise HTTPException(status_code=500, detail=f"聚合失败: {str(e)}")


@router.get("/snapshots")
async def list_snapshots(
    start_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    dimension_type: Optional[str] = Query(None, description="维度: total / platform / product"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """读聚合快照 (快速路径, 基于 EffectMetricSnapshot 表)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要 admin 权限")
    service = EffectTrackingService(db)
    result = service.get_snapshot_summary(
        start_date=start_date,
        end_date=end_date,
        dimension_type=dimension_type,
    )
    return success_response(data=result)
