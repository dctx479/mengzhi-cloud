"""
效果监测服务

提供:
- track_event(): 单次事件记录 (高吞吐, fire-and-forget)
- batch_track_events(): 批量事件记录
- get_dashboard_summary(): Dashboard 聚合查询
- aggregate_daily_snapshot(): 每日聚合任务入口 (cron)

版本: 1.0
创建日期: 2026-06-17
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models import (
    EffectEvent,
    EffectMetricSnapshot,
    EffectType,
)

logger = logging.getLogger(__name__)


class EffectTrackingService:
    """效果追踪服务"""

    def __init__(self, db: Session):
        self.db = db

    def track_event(
        self,
        event_type: EffectType,
        user_id: Optional[int] = None,
        product_id: Optional[int] = None,
        content_record_id: Optional[int] = None,
        publish_record_id: Optional[int] = None,
        platform: Optional[str] = None,
        channel: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        event_time: Optional[datetime] = None,
    ) -> EffectEvent:
        """记录单个事件

        fire-and-forget: 失败仅 logger.error, 不抛异常 (避免影响主业务)
        """
        try:
            event = EffectEvent(
                event_type=event_type,
                user_id=user_id,
                product_id=product_id,
                content_record_id=content_record_id,
                publish_record_id=publish_record_id,
                platform=platform,
                channel=channel,
                event_time=event_time or datetime.utcnow(),
                extra_data=extra_data,
            )
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            return event
        except Exception as e:
            logger.error(f"⚠️ WARNING: track_event failed: {e}")
            self.db.rollback()
            raise

    def batch_track_events(self, events: List[Dict[str, Any]]) -> int:
        """批量记录事件

        Args:
            events: 事件字典列表, 每个字典包含 track_event 的参数

        Returns:
            成功插入的数量
        """
        if not events:
            return 0
        try:
            objects = []
            for evt in events:
                objects.append(
                    EffectEvent(
                        event_type=EffectType(evt["event_type"]) if isinstance(evt.get("event_type"), str) else evt["event_type"],
                        user_id=evt.get("user_id"),
                        product_id=evt.get("product_id"),
                        content_record_id=evt.get("content_record_id"),
                        publish_record_id=evt.get("publish_record_id"),
                        platform=evt.get("platform"),
                        channel=evt.get("channel"),
                        event_time=evt.get("event_time") or datetime.utcnow(),
                        extra_data=evt.get("extra_data"),
                    )
                )
            self.db.bulk_save_objects(objects)
            self.db.commit()
            return len(objects)
        except Exception as e:
            logger.error(f"⚠️ WARNING: batch_track_events failed: {e}")
            self.db.rollback()
            return 0

    def get_dashboard_summary(
        self,
        user_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Dashboard 聚合数据 (基于 EffectEvent 实时聚合, 适合中小数据量)

        返回:
        - overview: 总览 (PV/UV/事件数/转化数)
        - by_event_type: 按事件类型分组的统计
        - by_platform: 按平台分组的统计
        - trend: 按日期的趋势
        """
        query = self.db.query(EffectEvent).filter(EffectEvent.deleted_at.is_(None))

        if user_id is not None:
            query = query.filter(EffectEvent.user_id == user_id)
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(EffectEvent.event_time >= start_dt)
            except ValueError:
                logger.warning(f"⚠️ WARNING: invalid start_date format: {start_date}")
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(EffectEvent.event_time < end_dt)
            except ValueError:
                logger.warning(f"⚠️ WARNING: invalid end_date format: {end_date}")

        events = query.all()

        # 概览
        overview = {
            "total_events": len(events),
            "total_pv": 0,
            "total_uv": 0,
            "total_conversions": 0,
            "total_ai_calls": 0,
        }
        # unique users
        unique_users = set()
        unique_products = set()

        # by_event_type
        by_event_type: Dict[str, Dict[str, int]] = defaultdict(lambda: {"count": 0, "users": set()})
        # by_platform
        by_platform: Dict[str, Dict[str, int]] = defaultdict(lambda: {"count": 0, "users": set()})
        # trend by date
        by_date: Dict[str, int] = defaultdict(int)

        for e in events:
            et = e.event_type.value if e.event_type else "unknown"
            plat = e.platform or "unknown"
            date_key = e.event_time.strftime("%Y-%m-%d") if e.event_time else "unknown"

            by_event_type[et]["count"] += 1
            if e.user_id:
                by_event_type[et]["users"].add(e.user_id)
            by_platform[plat]["count"] += 1
            if e.user_id:
                by_platform[plat]["users"].add(e.user_id)
            by_date[date_key] += 1

            overview["total_pv"] += 1
            if e.user_id:
                unique_users.add(e.user_id)
                overview["total_uv"] += 1
            if e.product_id:
                unique_products.add(e.product_id)
            if et == EffectType.CONVERSION.value:
                overview["total_conversions"] += 1
            if et in (
                EffectType.CHAT_MESSAGE.value,
                EffectType.GENERATION_CALL.value,
                EffectType.AI_RESPONSE.value,
            ):
                overview["total_ai_calls"] += 1

        # 转换 set 为 count
        for d in by_event_type.values():
            d["unique_users"] = len(d.pop("users", set()))
        for d in by_platform.values():
            d["unique_users"] = len(d.pop("users", set()))

        return {
            "overview": {
                **overview,
                "total_uv": len(unique_users),  # 真正的 UV
                "unique_products": len(unique_products),
            },
            "by_event_type": dict(by_event_type),
            "by_platform": dict(by_platform),
            "by_date": dict(sorted(by_date.items())),
            "filter": {
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        }

    def aggregate_daily_snapshot(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """聚合某日的事件数据到 EffectMetricSnapshot

        供定时任务调用: 每日凌晨聚合前一日数据
        维度: total / platform / product
        """
        if target_date is None:
            target_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

        try:
            start_dt = datetime.strptime(target_date, "%Y-%m-%d")
            end_dt = start_dt + timedelta(days=1)
        except ValueError:
            raise ValueError(f"无效日期格式: {target_date}, 应为 YYYY-MM-DD")

        events = (
            self.db.query(EffectEvent)
            .filter(
                EffectEvent.event_time >= start_dt,
                EffectEvent.event_time < end_dt,
                EffectEvent.deleted_at.is_(None),
            )
            .all()
        )

        # 按维度聚合
        # 1. total
        total_count = len(events)
        total_uv = len({e.user_id for e in events if e.user_id})
        total_conv = sum(1 for e in events if e.event_type == EffectType.CONVERSION)
        total_ai = sum(
            1
            for e in events
            if e.event_type
            in (
                EffectType.CHAT_MESSAGE,
                EffectType.GENERATION_CALL,
                EffectType.AI_RESPONSE,
            )
        )
        # 2. by_platform
        by_platform: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "users": set(), "conversions": 0, "ai_calls": 0}
        )
        # 3. by_product
        by_product: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "users": set(), "conversions": 0}
        )

        for e in events:
            plat = e.platform or "unknown"
            by_platform[plat]["count"] += 1
            if e.user_id:
                by_platform[plat]["users"].add(e.user_id)
            if e.event_type == EffectType.CONVERSION:
                by_platform[plat]["conversions"] += 1
            if e.event_type in (
                EffectType.CHAT_MESSAGE,
                EffectType.GENERATION_CALL,
                EffectType.AI_RESPONSE,
            ):
                by_platform[plat]["ai_calls"] += 1

            if e.product_id:
                prod_key = str(e.product_id)
                by_product[prod_key]["count"] += 1
                if e.user_id:
                    by_product[prod_key]["users"].add(e.user_id)
                if e.event_type == EffectType.CONVERSION:
                    by_product[prod_key]["conversions"] += 1

        # upsert to EffectMetricSnapshot
        upserted = 0

        def _upsert(date, dim_type, dim_key, count, uv, conv, ai, extra=None):
            existing = (
                self.db.query(EffectMetricSnapshot)
                .filter(
                    EffectMetricSnapshot.metric_date == date,
                    EffectMetricSnapshot.dimension_type == dim_type,
                    EffectMetricSnapshot.dimension_key == dim_key,
                )
                .first()
            )
            if existing:
                existing.pv = count
                existing.uv = uv
                existing.event_count = count
                existing.conversion_count = conv
                existing.ai_call_count = ai
                existing.extra_data = extra
            else:
                self.db.add(
                    EffectMetricSnapshot(
                        metric_date=date,
                        dimension_type=dim_type,
                        dimension_key=dim_key,
                        pv=count,
                        uv=uv,
                        event_count=count,
                        conversion_count=conv,
                        ai_call_count=ai,
                        extra_data=extra,
                    )
                )
            return 1

        # total
        upserted += _upsert(target_date, "total", "all", total_count, total_uv, total_conv, total_ai)

        # by platform
        for plat, data in by_platform.items():
            upserted += _upsert(
                target_date,
                "platform",
                plat,
                data["count"],
                len(data["users"]),
                data["conversions"],
                data["ai_calls"],
            )

        # by product
        for prod, data in by_product.items():
            upserted += _upsert(
                target_date,
                "product",
                prod,
                data["count"],
                len(data["users"]),
                data["conversions"],
                0,
            )

        self.db.commit()
        return {
            "date": target_date,
            "snapshots_upserted": upserted,
            "total_events": total_count,
        }

    def get_snapshot_summary(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        dimension_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """从 EffectMetricSnapshot 读聚合数据 (快速路径)"""
        query = self.db.query(EffectMetricSnapshot).filter(EffectMetricSnapshot.deleted_at.is_(None))

        if start_date:
            query = query.filter(EffectMetricSnapshot.metric_date >= start_date)
        if end_date:
            query = query.filter(EffectMetricSnapshot.metric_date <= end_date)
        if dimension_type:
            query = query.filter(EffectMetricSnapshot.dimension_type == dimension_type)

        rows = query.order_by(EffectMetricSnapshot.metric_date.asc()).all()
        return {
            "items": [r.to_dict() for r in rows],
            "count": len(rows),
        }
