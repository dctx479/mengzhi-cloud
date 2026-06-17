"""
测试 app/services/effect_service.py - 效果监测服务

覆盖:
- track_event(): 单次事件
- batch_track_events(): 批量事件
- get_dashboard_summary(): 实时聚合 (基于 mock 数据)
- aggregate_daily_snapshot(): 每日聚合
- get_snapshot_summary(): 快照读

注: 由于 SQLite + BIGINT autoincrement 的 pre-existing 兼容性问题,
    测试用 MagicMock 模拟 db session 和 EffectEvent 实例。
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from app.services.effect_service import EffectTrackingService
from app.models import EffectEvent, EffectType
from app.models.base import generate_uuid


def _make_event(event_type, user_id=1, platform=None, product_id=None, event_time=None, **kw):
    """构造一个 EffectEvent mock 实例"""
    e = MagicMock(spec=EffectEvent)
    e.id = 1
    e.event_uuid = generate_uuid()
    e.event_type = event_type
    e.user_id = user_id
    e.product_id = product_id
    e.content_record_id = None
    e.publish_record_id = None
    e.platform = platform
    e.channel = None
    e.event_time = event_time or datetime.utcnow()
    e.deleted_at = None
    e.extra_data = None
    return e


# ==================== track_event ====================


class TestTrackEvent:
    def test_track_calls_add_and_commit(self):
        db = MagicMock()
        svc = EffectTrackingService(db)
        result = svc.track_event(event_type=EffectType.CONTENT_VIEW, user_id=1)
        # 验证 add/commit/refresh 都被调用
        assert db.add.called
        assert db.commit.called
        assert db.refresh.called

    def test_track_constructs_event(self):
        db = MagicMock()
        svc = EffectTrackingService(db)
        svc.track_event(
            event_type=EffectType.CONVERSION,
            user_id=42,
            product_id=10,
            platform="douyin",
        )
        # 验证传入 db.add 的 event 对象有正确的字段
        added_event = db.add.call_args[0][0]
        assert added_event.event_type == EffectType.CONVERSION
        assert added_event.user_id == 42
        assert added_event.product_id == 10
        assert added_event.platform == "douyin"

    def test_track_rolls_back_on_error(self):
        db = MagicMock()
        db.commit.side_effect = RuntimeError("DB error")
        svc = EffectTrackingService(db)
        with pytest.raises(RuntimeError, match="DB error"):
            svc.track_event(event_type=EffectType.AI_RESPONSE)
        # 验证 rollback 被调用
        assert db.rollback.called


# ==================== batch_track_events ====================


class TestBatchTrackEvents:
    def test_empty_list_returns_zero(self):
        db = MagicMock()
        svc = EffectTrackingService(db)
        assert svc.batch_track_events([]) == 0

    def test_batch_returns_count(self):
        db = MagicMock()
        svc = EffectTrackingService(db)
        events = [
            {"event_type": "content_view", "user_id": 1, "platform": "wechat"},
            {"event_type": "content_view", "user_id": 2, "platform": "wechat"},
            {"event_type": "chat_message", "user_id": 1, "platform": "wechat"},
        ]
        count = svc.batch_track_events(events)
        assert count == 3
        assert db.bulk_save_objects.called
        assert db.commit.called

    def test_batch_with_enum_objects(self):
        db = MagicMock()
        svc = EffectTrackingService(db)
        events = [{"event_type": EffectType.PRODUCT_CLICK, "user_id": 5}]
        count = svc.batch_track_events(events)
        assert count == 1

    def test_batch_event_time_default(self):
        db = MagicMock()
        svc = EffectTrackingService(db)
        events = [{"event_type": "ai_response"}]
        svc.batch_track_events(events)
        # 验证传入的对象有 event_time
        call_args = db.bulk_save_objects.call_args[0][0]
        assert all(e.event_time is not None for e in call_args)

    def test_batch_rollback_on_error(self):
        db = MagicMock()
        db.bulk_save_objects.side_effect = RuntimeError("DB error")
        svc = EffectTrackingService(db)
        count = svc.batch_track_events([{"event_type": "ai_response"}])
        assert count == 0
        assert db.rollback.called


# ==================== get_dashboard_summary ====================


class TestDashboardSummary:
    def _setup_db_with_events(self, events):
        db = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.all.return_value = events
        db.query.return_value = query
        return db

    def test_overview_counts(self):
        events = [
            _make_event(EffectType.CONTENT_VIEW, user_id=1, platform="douyin"),
            _make_event(EffectType.CONTENT_VIEW, user_id=1, platform="douyin"),
            _make_event(EffectType.CONVERSION, user_id=1, platform="douyin", product_id=10),
            _make_event(EffectType.CHAT_MESSAGE, user_id=2, platform="wechat"),
        ]
        db = self._setup_db_with_events(events)
        svc = EffectTrackingService(db)
        result = svc.get_dashboard_summary()
        assert result["overview"]["total_events"] == 4
        assert result["overview"]["total_uv"] == 2
        assert result["overview"]["total_conversions"] == 1
        assert result["overview"]["total_ai_calls"] == 1
        assert result["overview"]["unique_products"] == 1

    def test_by_event_type(self):
        events = [
            _make_event(EffectType.CONTENT_VIEW, platform="douyin"),
            _make_event(EffectType.CONVERSION, platform="douyin"),
            _make_event(EffectType.CHAT_MESSAGE, platform="wechat"),
        ]
        db = self._setup_db_with_events(events)
        svc = EffectTrackingService(db)
        result = svc.get_dashboard_summary()
        by = result["by_event_type"]
        assert by["content_view"]["count"] == 1
        assert by["conversion"]["count"] == 1
        assert by["chat_message"]["count"] == 1

    def test_by_platform(self):
        events = [
            _make_event(EffectType.CONTENT_VIEW, platform="douyin"),
            _make_event(EffectType.CONTENT_VIEW, platform="douyin"),
            _make_event(EffectType.CHAT_MESSAGE, platform="wechat"),
        ]
        db = self._setup_db_with_events(events)
        svc = EffectTrackingService(db)
        result = svc.get_dashboard_summary()
        plat = result["by_platform"]
        assert plat["douyin"]["count"] == 2
        assert plat["wechat"]["count"] == 1

    def test_by_date(self):
        today = datetime.utcnow()
        events = [
            _make_event(EffectType.CONTENT_VIEW, event_time=today),
            _make_event(EffectType.CONTENT_VIEW, event_time=today - timedelta(days=1)),
        ]
        db = self._setup_db_with_events(events)
        svc = EffectTrackingService(db)
        result = svc.get_dashboard_summary()
        assert len(result["by_date"]) == 2

    def test_user_scope(self):
        events = [
            _make_event(EffectType.CONTENT_VIEW, user_id=1),
            _make_event(EffectType.CONTENT_VIEW, user_id=2),
        ]
        db = self._setup_db_with_events(events)
        svc = EffectTrackingService(db)
        # 实际 service 多次调用 .filter(), 由于 mock 共享同一 query, 都返回 events
        # 这里仅验证调用 query 不会崩溃, 用户的过滤逻辑由 SQL 层负责
        result = svc.get_dashboard_summary(user_id=1)
        assert result["filter"]["user_id"] == 1

    def test_date_range_invalid_format_ignored(self):
        events = [_make_event(EffectType.CONTENT_VIEW)]
        db = self._setup_db_with_events(events)
        svc = EffectTrackingService(db)
        result = svc.get_dashboard_summary(start_date="not-a-date", end_date="also-bad")
        assert result["overview"]["total_events"] == 1

    def test_uv_count_with_repeated_user(self):
        """同一 user 多次出现, UV 应只计 1"""
        events = [
            _make_event(EffectType.CONTENT_VIEW, user_id=1),
            _make_event(EffectType.CONTENT_VIEW, user_id=1),
            _make_event(EffectType.CONTENT_VIEW, user_id=1),
        ]
        db = self._setup_db_with_events(events)
        svc = EffectTrackingService(db)
        result = svc.get_dashboard_summary()
        assert result["overview"]["total_uv"] == 1

    def test_ai_call_count_includes_chat_generation_response(self):
        events = [
            _make_event(EffectType.CHAT_MESSAGE),
            _make_event(EffectType.GENERATION_CALL),
            _make_event(EffectType.AI_RESPONSE),
            _make_event(EffectType.CONTENT_VIEW),  # 不算 AI 调用
        ]
        db = self._setup_db_with_events(events)
        svc = EffectTrackingService(db)
        result = svc.get_dashboard_summary()
        assert result["overview"]["total_ai_calls"] == 3


# ==================== aggregate_daily_snapshot ====================


class TestAggregateDailySnapshot:
    def test_aggregate_invalid_date_raises(self):
        db = MagicMock()
        svc = EffectTrackingService(db)
        with pytest.raises(ValueError, match="无效日期格式"):
            svc.aggregate_daily_snapshot(target_date="2026/06/17")

    def test_aggregate_empty_returns_zeros(self):
        db = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.all.return_value = []
        db.query.return_value = query
        svc = EffectTrackingService(db)
        result = svc.aggregate_daily_snapshot(target_date="2026-06-15")
        assert result["total_events"] == 0
        assert result["date"] == "2026-06-15"
        # 至少 1 个 snapshot: total
        assert result["snapshots_upserted"] >= 1

    def test_aggregate_with_events(self):
        events = [
            _make_event(EffectType.CONTENT_VIEW, user_id=1, platform="douyin", product_id=10),
            _make_event(EffectType.CONVERSION, user_id=1, platform="douyin", product_id=10),
            _make_event(EffectType.CHAT_MESSAGE, user_id=2, platform="wechat"),
        ]
        db = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.all.return_value = events
        db.query.return_value = query
        # existing snapshot
        existing_snap = MagicMock()
        existing_snap.dimension_type = "total"
        existing_snap.dimension_key = "all"
        # upsert query: 第一次返回 None (insert), 第二次返回 None
        # 让 query().filter().first() 返回 None
        db.query.side_effect = [
            # 第一次: query events
            self._events_query(events),
            # 后续: 多次 upsert (返回 None 表示需要 insert)
            *[self._upsert_query() for _ in range(10)],
        ]
        svc = EffectTrackingService(db)
        result = svc.aggregate_daily_snapshot(target_date="2026-06-15")
        assert result["date"] == "2026-06-15"
        assert result["total_events"] == 3

    def _events_query(self, events):
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = events
        return q

    def _upsert_query(self):
        q = MagicMock()
        f = MagicMock()
        f.first = MagicMock(return_value=None)
        q.filter = MagicMock(return_value=f)
        return q

    def test_aggregate_updates_existing_snapshot(self):
        events = [_make_event(EffectType.CONTENT_VIEW, user_id=1, platform="douyin")]
        existing_snap = MagicMock()
        existing_snap.pv = 0
        existing_snap.uv = 0
        existing_snap.event_count = 0
        existing_snap.conversion_count = 0
        existing_snap.ai_call_count = 0
        existing_snap.extra_data = None

        db = MagicMock()
        db.query.side_effect = [
            self._events_query(events),
            self._upsert_query_with_existing(existing_snap),
            self._upsert_query_with_existing(existing_snap),
            self._upsert_query_with_existing(existing_snap),
        ]
        svc = EffectTrackingService(db)
        result = svc.aggregate_daily_snapshot(target_date="2026-06-15")
        assert result["total_events"] == 1
        # existing snapshot 应被更新
        assert existing_snap.event_count == 1

    def _upsert_query_with_existing(self, existing):
        q = MagicMock()
        f = MagicMock()
        f.first = MagicMock(return_value=existing)
        q.filter = MagicMock(return_value=f)
        return q


# ==================== get_snapshot_summary ====================


class TestSnapshotSummary:
    def test_empty(self):
        db = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.order_by.return_value = query
        query.all.return_value = []
        db.query.return_value = query

        svc = EffectTrackingService(db)
        result = svc.get_snapshot_summary()
        assert result["items"] == []
        assert result["count"] == 0

    def test_with_data(self):
        snap1 = MagicMock()
        snap1.to_dict = MagicMock(return_value={"metric_date": "2026-06-15", "pv": 100})
        snap2 = MagicMock()
        snap2.to_dict = MagicMock(return_value={"metric_date": "2026-06-15", "pv": 50})

        db = MagicMock()
        query = MagicMock()
        query.filter.return_value = query
        query.order_by.return_value = query
        query.all.return_value = [snap1, snap2]
        db.query.return_value = query

        svc = EffectTrackingService(db)
        result = svc.get_snapshot_summary()
        assert result["count"] == 2
        assert len(result["items"]) == 2
