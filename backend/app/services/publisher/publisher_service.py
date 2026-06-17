"""
多平台内容发布服务 (统一入口)

提供:
- publish(): 一键发布到多平台
- ingest_metrics(): 表现数据采集
- get_metrics_summary(): Dashboard 聚合查询
- 平台记录管理: list/详情/重试

版本: 1.0
创建日期: 2026-06-17
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models import (
    ContentRecord,
    PublishRecord,
    PublishMetric,
    PublishStatus,
    Platform,
)
from .base import PublishRequest
from .registry import PublisherRegistry

logger = logging.getLogger(__name__)


class ContentPublisherService:
    """内容发布服务 (统一入口)"""

    def __init__(self, db: Session):
        self.db = db
        self.registry = PublisherRegistry()

    async def publish(
        self,
        user_id: int,
        content_record_id: int,
        platforms: List[str],
    ) -> Dict[str, Any]:
        """发布内容到多平台

        Args:
            user_id: 用户ID (用于权限校验)
            content_record_id: 内容记录ID
            platforms: 平台列表, 如 ['douyin', 'xiaohongshu']

        Returns:
            {
                "content_record_id": int,
                "results": [
                    {"platform": str, "success": bool, "publish_uuid": str, "platform_url": str|None, "error": str|None}
                ],
                "summary": {"total": int, "succeeded": int, "failed": int}
            }
        """
        # 1. 校验 content_record 存在且属于 user
        record = (
            self.db.query(ContentRecord)
            .filter(ContentRecord.id == content_record_id, ContentRecord.user_id == user_id)
            .first()
        )
        if not record:
            raise ValueError(f"内容记录 {content_record_id} 不存在或无权访问")

        # 2. 平台去重 & 校验
        unique_platforms = list({p for p in platforms if p})
        if not unique_platforms:
            raise ValueError("至少需要指定 1 个平台")

        unsupported = [p for p in unique_platforms if not self.registry.is_supported(p)]
        if unsupported:
            raise ValueError(f"不支持的平台: {unsupported}")

        # 3. 构造 PublishRequest
        request = self._build_request(record)

        # 4. 并发分发
        tasks = []
        for platform_key in unique_platforms:
            tasks.append(self._publish_to_single_platform(user_id, record, request, platform_key))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 5. 整理结果
        formatted = []
        succeeded = 0
        failed = 0
        for platform_key, result in zip(unique_platforms, results):
            if isinstance(result, Exception):
                logger.error(f"⚠️ WARNING: platform {platform_key} raised exception: {result}")
                formatted.append(
                    {
                        "platform": platform_key,
                        "success": False,
                        "publish_uuid": None,
                        "platform_url": None,
                        "error": str(result),
                    }
                )
                failed += 1
            else:
                formatted.append(result)
                if result["success"]:
                    succeeded += 1
                else:
                    failed += 1

        return {
            "content_record_id": content_record_id,
            "results": formatted,
            "summary": {"total": len(unique_platforms), "succeeded": succeeded, "failed": failed},
        }

    async def _publish_to_single_platform(
        self,
        user_id: int,
        record: ContentRecord,
        request: PublishRequest,
        platform_key: str,
    ) -> Dict[str, Any]:
        """发布到单一平台 + 持久化记录"""
        # 先创建 PENDING 记录
        publish_record = PublishRecord(
            user_id=user_id,
            product_id=record.product_id,
            content_record_id=record.id,
            platform=Platform(platform_key),
            status=PublishStatus.PUBLISHING,
            is_mock=1 if self.registry.get(platform_key).config.get("mode", "mock") == "mock" else 0,
        )
        self.db.add(publish_record)
        self.db.commit()
        self.db.refresh(publish_record)

        try:
            publisher = self.registry.get(platform_key)
            if not publisher:
                raise ValueError(f"未找到平台 {platform_key} 的发布器")

            # adapt() 内容
            adapted = publisher.adapt(request)
            # validate() 检查
            validation_err = publisher.validate(adapted)
            if validation_err:
                publish_record.status = PublishStatus.FAILED
                publish_record.error_message = validation_err
                self.db.commit()
                return {
                    "platform": platform_key,
                    "success": False,
                    "publish_uuid": publish_record.publish_uuid,
                    "platform_url": None,
                    "error": validation_err,
                }

            # 持久化适配后内容
            publish_record.adapted_title = adapted.title
            publish_record.adapted_content = adapted.content
            publish_record.adapted_tags = adapted.tags
            publish_record.media_urls = adapted.images

            # 执行发布
            result = await publisher.publish(adapted)

            # 持久化结果
            if result.success:
                publish_record.status = PublishStatus.PUBLISHED
                publish_record.platform_post_id = result.platform_post_id
                publish_record.platform_url = result.platform_url
                publish_record.published_at = datetime.utcnow()
            else:
                publish_record.status = PublishStatus.FAILED
                publish_record.error_message = result.error_message

            self.db.commit()

            return {
                "platform": platform_key,
                "success": result.success,
                "publish_uuid": publish_record.publish_uuid,
                "platform_url": result.platform_url,
                "error": result.error_message,
            }

        except Exception as e:
            logger.error(f"⚠️ WARNING: platform {platform_key} publish failed: {e}")
            publish_record.status = PublishStatus.FAILED
            publish_record.error_message = str(e)
            self.db.commit()
            return {
                "platform": platform_key,
                "success": False,
                "publish_uuid": publish_record.publish_uuid,
                "platform_url": None,
                "error": str(e),
            }

    def _build_request(self, record: ContentRecord) -> PublishRequest:
        """从 ContentRecord 构造 PublishRequest"""
        tags = []
        if record.keywords and isinstance(record.keywords, list):
            tags.extend([str(k) for k in record.keywords if k])

        return PublishRequest(
            content=record.generated_content or "",
            title=record.input_params.get("title") if isinstance(record.input_params, dict) else None,
            images=[],
            tags=tags,
            extra={"content_type": record.content_type.value if record.content_type else None},
        )

    async def ingest_metrics(
        self,
        publish_record_id: int,
        metric_date: str,
        pv: int = 0,
        uv: int = 0,
        like_count: int = 0,
        share_count: int = 0,
        comment_count: int = 0,
        favorite_count: int = 0,
        conversion_count: int = 0,
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> PublishMetric:
        """表现数据采集 (upsert by publish_record_id + metric_date)"""
        # 校验
        publish_record = (
            self.db.query(PublishRecord).filter(PublishRecord.id == publish_record_id).first()
        )
        if not publish_record:
            raise ValueError(f"发布记录 {publish_record_id} 不存在")

        existing = (
            self.db.query(PublishMetric)
            .filter(
                PublishMetric.publish_record_id == publish_record_id,
                PublishMetric.metric_date == metric_date,
            )
            .first()
        )

        if existing:
            existing.pv = pv
            existing.uv = uv
            existing.like_count = like_count
            existing.share_count = share_count
            existing.comment_count = comment_count
            existing.favorite_count = favorite_count
            existing.conversion_count = conversion_count
            existing.raw_data = raw_data
            self.db.commit()
            self.db.refresh(existing)
            return existing

        metric = PublishMetric(
            publish_record_id=publish_record_id,
            metric_date=metric_date,
            pv=pv,
            uv=uv,
            like_count=like_count,
            share_count=share_count,
            comment_count=comment_count,
            favorite_count=favorite_count,
            conversion_count=conversion_count,
            raw_data=raw_data,
        )
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def get_metrics_summary(
        self,
        user_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        platform: Optional[str] = None,
        product_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """聚合表现数据 (按平台 / 按日期)"""
        # JOIN publish_metrics + publish_records
        query = (
            self.db.query(PublishMetric, PublishRecord)
            .join(PublishRecord, PublishMetric.publish_record_id == PublishRecord.id)
            .filter(PublishRecord.user_id == user_id)
        )

        if start_date:
            query = query.filter(PublishMetric.metric_date >= start_date)
        if end_date:
            query = query.filter(PublishMetric.metric_date <= end_date)
        if platform:
            query = query.filter(PublishRecord.platform == Platform(platform))
        if product_id:
            query = query.filter(PublishRecord.product_id == product_id)

        rows = query.all()

        # 按平台汇总
        by_platform: Dict[str, Dict[str, int]] = {}
        by_date: Dict[str, Dict[str, int]] = {}
        totals = {
            "pv": 0, "uv": 0, "like_count": 0, "share_count": 0,
            "comment_count": 0, "favorite_count": 0, "conversion_count": 0,
        }

        for metric, record in rows:
            plat_key = record.platform.value if record.platform else "unknown"
            by_platform.setdefault(plat_key, {**totals})
            for k in totals:
                by_platform[plat_key][k] += getattr(metric, k) or 0
                totals[k] += getattr(metric, k) or 0

            by_date.setdefault(metric.metric_date, {**totals})
            for k in totals:
                by_date[metric.metric_date][k] += getattr(metric, k) or 0

        return {
            "totals": totals,
            "by_platform": by_platform,
            "by_date": by_date,
            "filter": {
                "start_date": start_date,
                "end_date": end_date,
                "platform": platform,
                "product_id": product_id,
            },
        }

    def list_user_records(
        self,
        user_id: int,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """列出用户的发布记录"""
        query = self.db.query(PublishRecord).filter(PublishRecord.user_id == user_id)

        if platform:
            query = query.filter(PublishRecord.platform == Platform(platform))
        if status:
            query = query.filter(PublishRecord.status == PublishStatus(status))

        total = query.count()
        records = (
            query.order_by(PublishRecord.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "items": [r.to_dict() for r in records],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_record_detail(self, user_id: int, publish_uuid: str) -> Optional[Dict[str, Any]]:
        """获取发布详情 + 表现数据"""
        record = (
            self.db.query(PublishRecord)
            .filter(PublishRecord.publish_uuid == publish_uuid, PublishRecord.user_id == user_id)
            .first()
        )
        if not record:
            return None

        result = record.to_dict()
        # 附加表现数据
        metrics = (
            self.db.query(PublishMetric)
            .filter(PublishMetric.publish_record_id == record.id)
            .order_by(PublishMetric.metric_date.asc())
            .all()
        )
        result["metrics"] = [m.to_dict() for m in metrics]
        return result

    async def retry_failed(self, user_id: int, publish_uuid: str) -> Dict[str, Any]:
        """重试失败的发布"""
        record = (
            self.db.query(PublishRecord)
            .filter(
                PublishRecord.publish_uuid == publish_uuid,
                PublishRecord.user_id == user_id,
                PublishRecord.status == PublishStatus.FAILED,
            )
            .first()
        )
        if not record:
            raise ValueError(f"未找到可重试的发布记录 {publish_uuid}")

        # 找到原始 content_record
        content_record = (
            self.db.query(ContentRecord).filter(ContentRecord.id == record.content_record_id).first()
        )
        if not content_record:
            raise ValueError(f"关联的内容记录 {record.content_record_id} 不存在")

        platform_key = record.platform.value
        request = self._build_request(content_record)

        # 清空旧错误, 重置状态
        record.error_message = None
        record.retry_count = (record.retry_count or 0) + 1
        record.status = PublishStatus.PUBLISHING
        self.db.commit()

        try:
            publisher = self.registry.get(platform_key)
            if not publisher:
                raise ValueError(f"未找到平台 {platform_key} 的发布器")

            adapted = publisher.adapt(request)
            result = await publisher.publish(adapted)

            record.adapted_title = adapted.title
            record.adapted_content = adapted.content
            record.adapted_tags = adapted.tags
            record.media_urls = adapted.images

            if result.success:
                record.status = PublishStatus.PUBLISHED
                record.platform_post_id = result.platform_post_id
                record.platform_url = result.platform_url
                record.published_at = datetime.utcnow()
            else:
                record.status = PublishStatus.FAILED
                record.error_message = result.error_message
            self.db.commit()

            return {
                "publish_uuid": publish_uuid,
                "success": result.success,
                "platform_url": result.platform_url,
                "error": result.error_message,
                "retry_count": record.retry_count,
            }
        except Exception as e:
            record.status = PublishStatus.FAILED
            record.error_message = str(e)
            self.db.commit()
            return {
                "publish_uuid": publish_uuid,
                "success": False,
                "platform_url": None,
                "error": str(e),
                "retry_count": record.retry_count,
            }
