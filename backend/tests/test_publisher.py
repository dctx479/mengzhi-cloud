"""
测试 app/services/publisher/* - 多平台内容发布框架

覆盖:
- base.py: PublishRequest/PublishResult 数据类, PublisherBase 校验
- adapters.py: 4 大平台适配器 (抖音/小红书/微信/微博) 的 adapt/validate/publish
- registry.py: 注册表单例 + Mock/Real 模式切换
- publisher_service.py: 关键路径单元测试 (mocked DB)

注: 由于 SQLite + BIGINT autoincrement 的兼容性问题 (pre-existing),
    集成测试改用 MagicMock 模拟 db 会话来覆盖关键逻辑。
"""

import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from app.services.publisher.base import (
    PublishRequest,
    PublishResult,
    PublisherBase,
)
from app.services.publisher.adapters import (
    ADAPTER_RULES,
    DouyinPublisher,
    XiaohongshuPublisher,
    WechatPublisher,
    WeiboPublisher,
)
from app.services.publisher.registry import PublisherRegistry
from app.services.publisher.publisher_service import ContentPublisherService

# ==================== base.py: PublishRequest / PublishResult ====================


class TestPublishRequest:
    def test_default_construction(self):
        req = PublishRequest(content="hello")
        assert req.content == "hello"
        assert req.title is None
        assert req.images == []
        assert req.tags == []
        assert req.extra == {}

    def test_full_construction(self):
        req = PublishRequest(
            content="正文",
            title="标题",
            images=["a.jpg", "b.jpg"],
            tags=["美食", "内蒙"],
            extra={"k": 1},
        )
        assert req.title == "标题"
        assert req.images == ["a.jpg", "b.jpg"]
        assert req.tags == ["美食", "内蒙"]
        assert req.extra == {"k": 1}


class TestPublishResult:
    def test_success_result(self):
        r = PublishResult(success=True, platform="douyin", platform_url="https://x")
        assert r.success is True
        assert r.error_message is None

    def test_failure_result(self):
        r = PublishResult(success=False, platform="wechat", error_message="失败")
        assert r.error_message == "失败"


# ==================== base.py: format_tags ====================


class _DummyPublisher(PublisherBase):
    """最小可实例化子类, 用于测试基类方法"""

    platform = "test"

    def adapt(self, request):
        return request

    async def publish(self, request):
        return PublishResult(success=True, platform=self.platform)


class TestFormatTags:
    def setup_method(self):
        self.p = _DummyPublisher()

    def test_empty_list(self):
        assert self.p.format_tags([]) == []

    def test_add_hash_prefix(self):
        out = self.p.format_tags(["美食"])
        assert out == ["#美食"]

    def test_existing_prefix_kept(self):
        out = self.p.format_tags(["#美食"])
        assert out == ["#美食"]

    def test_dedup(self):
        out = self.p.format_tags(["美食", "#美食", "美食"])
        assert out == ["#美食"]

    def test_max_length_30(self):
        long_tag = "a" * 50
        out = self.p.format_tags([long_tag])
        assert len(out[0]) <= 30

    def test_skip_empty(self):
        out = self.p.format_tags(["", "美食", None])
        assert out == ["#美食"]

    def test_custom_prefix(self):
        out = self.p.format_tags(["美食"], prefix="@")
        assert out == ["@美食"]


class TestBaseValidate:
    def setup_method(self):
        self.p = _DummyPublisher()

    def test_valid(self):
        assert self.p.validate(PublishRequest(content="正文")) is None

    def test_empty_content_and_title_rejected(self):
        err = self.p.validate(PublishRequest(content=""))
        assert err is not None
        assert "内容" in err or "标题" in err

    def test_too_long_content_rejected(self):
        big = "x" * 50001
        err = self.p.validate(PublishRequest(content=big))
        assert err is not None
        assert "50000" in err


# ==================== adapters.py: 平台规则 ====================


class TestAdapterRules:
    def test_all_platforms_have_rules(self):
        for p in ["douyin", "xiaohongshu", "wechat", "weibo"]:
            assert p in ADAPTER_RULES
            r = ADAPTER_RULES[p]
            assert "title_max" in r
            assert "content_max" in r
            assert "require_media" in r
            assert "tag_prefix" in r

    def test_douyin_strictest_title(self):
        assert ADAPTER_RULES["douyin"]["title_max"] <= ADAPTER_RULES["wechat"]["title_max"]

    def test_douyin_and_xiaohongshu_require_media(self):
        assert ADAPTER_RULES["douyin"]["require_media"] is True
        assert ADAPTER_RULES["xiaohongshu"]["require_media"] is True
        assert ADAPTER_RULES["wechat"]["require_media"] is False
        assert ADAPTER_RULES["weibo"]["require_media"] is False


# ==================== adapters.py: DouyinPublisher ====================


class TestDouyinPublisher:
    def setup_method(self):
        with patch.dict(os.environ, {"PUBLISHER_MODE": "mock"}):
            self.p = DouyinPublisher({"mode": "mock", "platform": "douyin"})

    def test_adapt_truncate_long_title(self):
        req = PublishRequest(content="正文" * 100, title="a" * 50, tags=["美食"])
        out = self.p.adapt(req)
        assert len(out.title) <= 30
        assert out.tags == ["#美食"]

    def test_validate_rejects_without_media(self):
        req = PublishRequest(content="正文", images=[])
        err = self.p.validate(req)
        assert err is not None
        assert "媒体" in err or "图片" in err

    def test_validate_accepts_with_media(self):
        req = PublishRequest(content="正文", images=["a.jpg"])
        assert self.p.validate(req) is None

    @pytest.mark.asyncio
    async def test_publish_success(self):
        req = PublishRequest(content="短视频文案", title="标题", images=["a.jpg"])
        with patch("app.services.publisher.adapters.random.random", return_value=0.99):
            result = await self.p.publish(req)
        assert result.success is True
        assert result.platform == "douyin"
        assert result.platform_url is not None
        assert "mock.douyin.com" in result.platform_url

    @pytest.mark.asyncio
    async def test_publish_failure(self):
        """5% 概率失败 - 强制 random < 0.05 模拟失败"""
        req = PublishRequest(content="短视频文案", title="标题", images=["a.jpg"])
        with patch("app.services.publisher.adapters.random.random", return_value=0.01):
            result = await self.p.publish(req)
        assert result.success is False
        assert "限流" in result.error_message or "失败" in result.error_message


# ==================== adapters.py: XiaohongshuPublisher ====================


class TestXiaohongshuPublisher:
    def setup_method(self):
        self.p = XiaohongshuPublisher({"mode": "mock", "platform": "xiaohongshu"})

    def test_adapt_truncates_to_20_chars_title(self):
        req = PublishRequest(content="笔记", title="a" * 30, tags=["种草"])
        out = self.p.adapt(req)
        assert len(out.title) <= 20
        assert out.tags == ["#种草"]

    def test_validate_rejects_no_image(self):
        req = PublishRequest(content="笔记")
        err = self.p.validate(req)
        assert err is not None

    def test_validate_accepts_with_image(self):
        req = PublishRequest(content="笔记", images=["a.jpg"])
        assert self.p.validate(req) is None

    @pytest.mark.asyncio
    async def test_publish_success(self):
        req = PublishRequest(content="笔记", title="标题", images=["a.jpg"])
        with patch("app.services.publisher.adapters.random.random", return_value=0.99):
            result = await self.p.publish(req)
        assert result.success is True
        assert "mock.xiaohongshu.com" in result.platform_url


# ==================== adapters.py: WechatPublisher ====================


class TestWechatPublisher:
    def setup_method(self):
        self.p = WechatPublisher({"mode": "mock", "platform": "wechat"})

    def test_adapt_long_content_truncated(self):
        req = PublishRequest(content="x" * 30000, title="标题", tags=["推文"])
        out = self.p.adapt(req)
        assert len(out.content) <= 20000

    def test_validate_no_media_required(self):
        req = PublishRequest(content="公众号长文", title="标题")
        assert self.p.validate(req) is None

    @pytest.mark.asyncio
    async def test_publish_success(self):
        req = PublishRequest(content="公众号长文", title="标题")
        with patch("app.services.publisher.adapters.random.random", return_value=0.99):
            result = await self.p.publish(req)
        assert result.success is True
        assert "mock.weixin.qq.com" in result.platform_url


# ==================== adapters.py: WeiboPublisher ====================


class TestWeiboPublisher:
    def setup_method(self):
        self.p = WeiboPublisher({"mode": "mock", "platform": "weibo"})

    def test_adapt_truncate(self):
        req = PublishRequest(content="x" * 3000, tags=["话题"])
        out = self.p.adapt(req)
        assert len(out.content) <= 2000
        assert out.tags == ["#话题"]

    def test_validate_no_media(self):
        req = PublishRequest(content="微博")
        assert self.p.validate(req) is None

    @pytest.mark.asyncio
    async def test_publish_success(self):
        req = PublishRequest(content="微博", title=None)
        with patch("app.services.publisher.adapters.random.random", return_value=0.99):
            result = await self.p.publish(req)
        assert result.success is True
        assert "mock.weibo.com" in result.platform_url


# ==================== registry.py ====================


class TestPublisherRegistry:
    def setup_method(self):
        PublisherRegistry._instance = None

    def teardown_method(self):
        PublisherRegistry._instance = None

    def test_singleton(self):
        r1 = PublisherRegistry()
        r2 = PublisherRegistry()
        assert r1 is r2

    def test_get_douyin(self):
        r = PublisherRegistry()
        p = r.get("douyin")
        assert isinstance(p, DouyinPublisher)

    def test_get_unknown_returns_none(self):
        r = PublisherRegistry()
        assert r.get("tiktok") is None

    def test_list_platforms(self):
        r = PublisherRegistry()
        plats = r.list_platforms()
        assert "douyin" in plats
        assert "xiaohongshu" in plats
        assert "wechat" in plats
        assert "weibo" in plats

    def test_is_supported(self):
        r = PublisherRegistry()
        assert r.is_supported("douyin") is True
        assert r.is_supported("unknown") is False

    def test_real_mode_reads_env(self):
        with patch.dict(
            os.environ,
            {
                "PUBLISHER_MODE": "real",
                "PUBLISHER_DOUYIN_APP_KEY": "k",
                "PUBLISHER_DOUYIN_APP_SECRET": "s",
                "PUBLISHER_DOUYIN_ACCESS_TOKEN": "t",
            },
        ):
            r = PublisherRegistry()
            p = r.get("douyin")
            assert p.config.get("mode") == "real"
            assert p.config.get("app_key") == "k"


# ==================== publisher_service.py: 单元测试 (mocked DB) ====================


class TestBuildRequest:
    def _make_record(self):
        rec = MagicMock()
        rec.generated_content = "生成的正文"
        rec.input_params = {"title": "测试标题"}
        rec.keywords = ["美食", "内蒙"]
        rec.content_type.value = "copy"
        return rec

    def test_build_request_basic(self):
        svc = ContentPublisherService(MagicMock())
        req = svc._build_request(self._make_record())
        assert req.content == "生成的正文"
        assert req.title == "测试标题"
        assert "美食" in req.tags
        assert req.extra.get("content_type") == "copy"

    def test_build_request_no_title(self):
        rec = self._make_record()
        rec.input_params = {}
        svc = ContentPublisherService(MagicMock())
        req = svc._build_request(rec)
        assert req.title is None

    def test_build_request_no_keywords(self):
        rec = self._make_record()
        rec.keywords = None
        svc = ContentPublisherService(MagicMock())
        req = svc._build_request(rec)
        assert req.tags == []

    def test_build_request_empty_keywords(self):
        rec = self._make_record()
        rec.keywords = []
        svc = ContentPublisherService(MagicMock())
        req = svc._build_request(rec)
        assert req.tags == []


class TestPublishServiceUnit:
    """用 mock DB 测试 service 关键路径 (无 SQLite 依赖)"""

    def _make_mock_db_with_record(self, user_id=1, content_id=1):
        """构造 mock db: query(ContentRecord).filter().first() 返回一个 mock record"""
        db = MagicMock()
        # 模拟 record
        rec = MagicMock()
        rec.id = content_id
        rec.user_id = user_id
        rec.product_id = 10
        rec.generated_content = "正文"
        rec.input_params = {"title": "标题"}
        rec.keywords = ["tag1"]
        rec.content_type.value = "copy"

        # 让 query(ContentRecord).filter(...).first() 返回 rec
        rec_query = MagicMock()
        rec_query.filter.return_value.first.return_value = rec
        db.query.return_value = rec_query

        # add() 模拟
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        return db, rec

    @pytest.mark.asyncio
    async def test_publish_record_not_found(self):
        db = MagicMock()
        rec_query = MagicMock()
        rec_query.filter.return_value.first.return_value = None
        db.query.return_value = rec_query

        svc = ContentPublisherService(db)
        with pytest.raises(ValueError, match="不存在或无权访问"):
            await svc.publish(user_id=999, content_record_id=99999, platforms=["douyin"])

    @pytest.mark.asyncio
    async def test_publish_no_platforms(self):
        db, rec = self._make_mock_db_with_record()
        svc = ContentPublisherService(db)
        with pytest.raises(ValueError, match="至少需要指定"):
            await svc.publish(user_id=1, content_record_id=rec.id, platforms=[])

    @pytest.mark.asyncio
    async def test_publish_unsupported_platform(self):
        db, rec = self._make_mock_db_with_record()
        svc = ContentPublisherService(db)
        with pytest.raises(ValueError, match="不支持的平台"):
            await svc.publish(user_id=1, content_record_id=rec.id, platforms=["tiktok"])

    @pytest.mark.asyncio
    async def test_publish_single_platform_wechat(self):
        """微信无需图片, 最简单路径"""
        db, rec = self._make_mock_db_with_record()
        svc = ContentPublisherService(db)
        with patch("app.services.publisher.adapters.random.random", return_value=0.99):
            result = await svc.publish(user_id=1, content_record_id=rec.id, platforms=["wechat"])
        assert result["summary"]["total"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0]["platform"] == "wechat"

    @pytest.mark.asyncio
    async def test_publish_multi_platform_dedup(self):
        """重复平台应去重"""
        db, rec = self._make_mock_db_with_record()
        svc = ContentPublisherService(db)
        with patch("app.services.publisher.adapters.random.random", return_value=0.99):
            result = await svc.publish(user_id=1, content_record_id=rec.id, platforms=["wechat", "wechat", "weibo"])
        assert result["summary"]["total"] == 2

    @pytest.mark.asyncio
    async def test_publish_handles_platform_exception(self):
        """某个平台抛异常不应影响其他平台"""
        db, rec = self._make_mock_db_with_record()
        svc = ContentPublisherService(db)

        async def boom(*args, **kwargs):
            raise RuntimeError("平台挂了")

        # monkey-patch _publish_to_single_platform: 1个成功 + 1个抛异常
        call_count = {"n": 0}

        async def fake_publish_to_single(user_id, record, request, platform_key):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return {
                    "platform": platform_key,
                    "success": True,
                    "publish_uuid": "abc",
                    "platform_url": "https://x",
                    "error": None,
                }
            else:
                raise RuntimeError("平台挂了")

        svc._publish_to_single_platform = fake_publish_to_single
        result = await svc.publish(user_id=1, content_record_id=rec.id, platforms=["wechat", "weibo"])
        assert result["summary"]["total"] == 2
        assert result["summary"]["succeeded"] == 1
        assert result["summary"]["failed"] == 1
        # 失败的平台应在 results 中
        assert any(not r["success"] for r in result["results"])


class TestIngestMetrics:
    @pytest.mark.asyncio
    def _dummy_for_marker(self):
        pass

    def _make_query(self, *return_values):
        calls = {"n": 0}

        def make(*args, **kwargs):
            q = MagicMock()
            f = MagicMock()
            idx = min(calls["n"], len(return_values) - 1)
            f.first = MagicMock(return_value=return_values[idx])
            f.all = MagicMock(return_value=return_values[idx] if isinstance(return_values[idx], list) else [])
            f.count = MagicMock(return_value=len(return_values[idx]) if isinstance(return_values[idx], list) else 1)
            q.filter = MagicMock(return_value=f)
            q.join = MagicMock(return_value=q)
            q.order_by = MagicMock(return_value=q)
            q.offset = MagicMock(return_value=q)
            q.limit = MagicMock(return_value=q)
            calls["n"] += 1
            return q

        return make

    @pytest.mark.asyncio
    async def test_ingest_metrics_raises_when_record_not_found(self):
        db = MagicMock()
        db.query = MagicMock(side_effect=self._make_query(None))
        svc = ContentPublisherService(db)
        with pytest.raises(ValueError, match="发布记录"):
            await svc.ingest_metrics(publish_record_id=99999, metric_date="2026-06-17")

    @pytest.mark.asyncio
    async def test_ingest_metrics_inserts_new(self):
        rec = MagicMock(id=1)
        db = MagicMock()
        db.query = MagicMock(side_effect=self._make_query(rec, None))
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        svc = ContentPublisherService(db)
        await svc.ingest_metrics(
            publish_record_id=1, metric_date="2026-06-17", pv=100, uv=50, like_count=20
        )
        assert db.add.called
        assert db.commit.called

    @pytest.mark.asyncio
    async def test_ingest_metrics_updates_existing(self):
        rec = MagicMock(id=1)
        existing = MagicMock(id=10, pv=0)
        db = MagicMock()
        db.query = MagicMock(side_effect=self._make_query(rec, existing))
        db.commit = MagicMock()
        db.refresh = MagicMock()

        svc = ContentPublisherService(db)
        await svc.ingest_metrics(publish_record_id=1, metric_date="2026-06-17", pv=999)
        assert existing.pv == 999


class TestGetMetricsSummary:
    def test_summary_empty(self):
        db = MagicMock()
        # query 返回空
        join_query = MagicMock()
        join_query.filter.return_value = join_query
        join_query.all.return_value = []
        db.query.return_value = join_query

        svc = ContentPublisherService(db)
        result = svc.get_metrics_summary(user_id=1)
        assert result["totals"]["pv"] == 0
        assert result["by_platform"] == {}
        assert result["by_date"] == {}

    def test_summary_aggregates(self):
        db = MagicMock()
        # 模拟 1 行: metric + record
        metric = MagicMock()
        metric.metric_date = "2026-06-17"
        metric.pv = 100
        metric.uv = 50
        metric.like_count = 10
        metric.share_count = 5
        metric.comment_count = 3
        metric.favorite_count = 2
        metric.conversion_count = 1
        record = MagicMock()
        record.platform.value = "wechat"

        join_query = MagicMock()
        join_query.join.return_value = join_query
        join_query.filter.return_value = join_query
        join_query.all.return_value = [(metric, record)]
        db.query.return_value = join_query

        svc = ContentPublisherService(db)
        result = svc.get_metrics_summary(user_id=1)
        assert result["totals"]["pv"] == 100
        assert "wechat" in result["by_platform"]
        assert result["by_platform"]["wechat"]["pv"] == 100


class TestListUserRecords:
    def test_list_with_pagination(self):
        db = MagicMock()
        rec1 = MagicMock()
        rec1.to_dict = MagicMock(return_value={"id": 1, "platform": "wechat"})
        rec2 = MagicMock()
        rec2.to_dict = MagicMock(return_value={"id": 2, "platform": "weibo"})

        query = MagicMock()
        query.filter.return_value = query
        query.count.return_value = 2
        query.order_by.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = [rec1, rec2]
        db.query.return_value = query

        svc = ContentPublisherService(db)
        result = svc.list_user_records(user_id=1, page=1, page_size=10)
        assert result["total"] == 2
        assert len(result["items"]) == 2


class TestGetRecordDetail:
    def test_detail_with_metrics(self):
        db = MagicMock()
        rec = MagicMock()
        rec.publish_uuid = "abc-123"
        rec.platform.value = "wechat"
        rec.to_dict = MagicMock(return_value={"publish_uuid": "abc-123", "platform": "wechat"})

        metric = MagicMock()
        metric.to_dict = MagicMock(return_value={"pv": 100})

        # 第一次 query 返回 rec, 第二次 query 返回 metrics
        rec_query = MagicMock()
        rec_query.filter.return_value.first.return_value = rec
        metric_query = MagicMock()
        metric_query.filter.return_value.order_by.return_value.all.return_value = [metric]

        db.query.side_effect = [rec_query, metric_query]

        svc = ContentPublisherService(db)
        result = svc.get_record_detail(user_id=1, publish_uuid="abc-123")
        assert result is not None
        assert result["platform"] == "wechat"
        assert len(result["metrics"]) == 1

    def test_detail_not_found(self):
        db = MagicMock()
        rec_query = MagicMock()
        rec_query.filter.return_value.first.return_value = None
        db.query.return_value = rec_query

        svc = ContentPublisherService(db)
        assert svc.get_record_detail(user_id=1, publish_uuid="missing") is None


class TestRetryFailed:
    @pytest.mark.asyncio
    async def test_retry_record_not_found(self):
        db = MagicMock()
        rec_query = MagicMock()
        rec_query.filter.return_value.first.return_value = None
        db.query.return_value = rec_query

        svc = ContentPublisherService(db)
        with pytest.raises(ValueError, match="未找到可重试"):
            await svc.retry_failed(user_id=1, publish_uuid="missing")

    @pytest.mark.asyncio
    async def test_retry_content_record_not_found(self):
        db = MagicMock()
        rec = MagicMock()
        rec.publish_uuid = "abc"
        rec.platform.value = "wechat"
        rec_query = MagicMock()
        rec_query.filter.return_value.first.return_value = rec

        # 第二次 query (ContentRecord) 返回 None
        content_query = MagicMock()
        content_query.filter.return_value.first.return_value = None

        db.query.side_effect = [rec_query, content_query]
        db.commit = MagicMock()

        svc = ContentPublisherService(db)
        with pytest.raises(ValueError, match="关联的内容记录"):
            await svc.retry_failed(user_id=1, publish_uuid="abc")

    @pytest.mark.asyncio
    async def test_retry_success(self):
        db = MagicMock()
        rec = MagicMock()
        rec.id = 1
        rec.publish_uuid = "abc"
        rec.platform.value = "wechat"
        rec.retry_count = 0
        rec.content_record_id = 1

        rec_query = MagicMock()
        rec_query.filter.return_value.first.return_value = rec

        # 关联的 content_record
        content = MagicMock()
        content.id = 1
        content.product_id = 10
        content.generated_content = "正文"
        content.input_params = {}
        content.keywords = []
        content.content_type.value = "copy"
        content_query = MagicMock()
        content_query.filter.return_value.first.return_value = content

        db.query.side_effect = [rec_query, content_query]
        db.commit = MagicMock()

        svc = ContentPublisherService(db)
        with patch("app.services.publisher.adapters.random.random", return_value=0.99):
            result = await svc.retry_failed(user_id=1, publish_uuid="abc")
        assert result["retry_count"] == 1
        assert "success" in result
