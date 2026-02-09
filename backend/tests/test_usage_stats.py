"""
测试 app/services/usage_stats.py - 使用统计服务

覆盖所有统计记录和查询功能
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.usage_stats import UsageStatsService
from app.models.usage_stats import UsageStatistics, StatType


@pytest.fixture
def usage_stats_service(db: Session):
    """创建使用统计服务实例"""
    return UsageStatsService(db)


@pytest.fixture
def sample_enterprise_id():
    """示例企业ID"""
    return 1


@pytest.fixture
def sample_user_id():
    """示例用户ID"""
    return 100


class TestRecordChatUsage:
    """测试对话使用记录"""

    def test_record_chat_usage_success(self, usage_stats_service, sample_enterprise_id, sample_user_id, db):
        """测试成功记录对话使用"""
        stat = usage_stats_service.record_chat_usage(
            enterprise_id=sample_enterprise_id,
            user_id=sample_user_id,
            model="gpt-4",
            input_tokens=100,
            output_tokens=200,
            client_charge=Decimal("0.1"),
            backend_cost=Decimal("0.05")
        )

        assert stat is not None
        assert stat.enterprise_id == sample_enterprise_id
        assert stat.user_id == sample_user_id
        assert stat.stat_type == StatType.CHAT
        assert stat.model == "gpt-4"
        assert stat.request_count == 1
        assert stat.input_tokens == 100
        assert stat.output_tokens == 200
        assert stat.client_charge == Decimal("0.1")
        assert stat.backend_cost == Decimal("0.05")
        assert stat.profit == Decimal("0.05")
        assert stat.profit_margin == 50.0

    def test_record_chat_usage_persisted(self, usage_stats_service, sample_enterprise_id, sample_user_id, db):
        """测试记录已持久化到数据库"""
        usage_stats_service.record_chat_usage(
            enterprise_id=sample_enterprise_id,
            user_id=sample_user_id,
            model="gpt-3.5-turbo",
            input_tokens=50,
            output_tokens=100,
            client_charge=Decimal("0.1"),
            backend_cost=Decimal("0.02")
        )

        # 查询数据库验证
        stats = db.query(UsageStatistics).filter(
            UsageStatistics.enterprise_id == sample_enterprise_id
        ).all()

        assert len(stats) == 1
        assert stats[0].model == "gpt-3.5-turbo"


class TestRecordImageUsage:
    """测试图片生成使用记录"""

    def test_record_image_usage_success(self, usage_stats_service, sample_enterprise_id, sample_user_id):
        """测试成功记录图片生成使用"""
        stat = usage_stats_service.record_image_usage(
            enterprise_id=sample_enterprise_id,
            user_id=sample_user_id,
            resolution="1024x1024",
            client_charge=Decimal("0.5"),
            backend_cost=Decimal("0.3")
        )

        assert stat is not None
        assert stat.stat_type == StatType.IMAGE
        assert stat.resolution == "1024x1024"
        assert stat.request_count == 1
        assert stat.client_charge == Decimal("0.5")
        assert stat.backend_cost == Decimal("0.3")
        assert stat.profit == Decimal("0.2")
        assert stat.profit_margin == 40.0

    def test_record_image_usage_different_resolutions(self, usage_stats_service, sample_enterprise_id, sample_user_id, db):
        """测试记录不同分辨率的图片生成"""
        resolutions = ["512x512", "1024x1024", "2048x2048"]

        for resolution in resolutions:
            usage_stats_service.record_image_usage(
                enterprise_id=sample_enterprise_id,
                user_id=sample_user_id,
                resolution=resolution,
                client_charge=Decimal("0.5"),
                backend_cost=Decimal("0.3")
            )

        stats = db.query(UsageStatistics).filter(
            UsageStatistics.stat_type == StatType.IMAGE
        ).all()

        assert len(stats) == 3
        assert set(s.resolution for s in stats) == set(resolutions)


class TestRecordVideoUsage:
    """测试视频生成使用记录"""

    def test_record_video_usage_success(self, usage_stats_service, sample_enterprise_id, sample_user_id):
        """测试成功记录视频生成使用"""
        stat = usage_stats_service.record_video_usage(
            enterprise_id=sample_enterprise_id,
            user_id=sample_user_id,
            resolution="1920x1080",
            duration=30,
            client_charge=Decimal("2.0"),
            backend_cost=Decimal("1.5")
        )

        assert stat is not None
        assert stat.stat_type == StatType.VIDEO
        assert stat.resolution == "1920x1080"
        assert stat.duration == 30
        assert stat.request_count == 1
        assert stat.client_charge == Decimal("2.0")
        assert stat.backend_cost == Decimal("1.5")
        assert stat.profit == Decimal("0.5")
        assert stat.profit_margin == 25.0

    def test_record_video_usage_various_durations(self, usage_stats_service, sample_enterprise_id, sample_user_id, db):
        """测试记录不同时长的视频生成"""
        durations = [10, 30, 60]

        for duration in durations:
            usage_stats_service.record_video_usage(
                enterprise_id=sample_enterprise_id,
                user_id=sample_user_id,
                resolution="1920x1080",
                duration=duration,
                client_charge=Decimal("2.0"),
                backend_cost=Decimal("1.0")
            )

        stats = db.query(UsageStatistics).filter(
            UsageStatistics.stat_type == StatType.VIDEO
        ).all()

        assert len(stats) == 3
        assert set(s.duration for s in stats) == set(durations)


class TestGetDailyStats:
    """测试获取每日统计"""

    def test_get_daily_stats_empty(self, usage_stats_service, sample_enterprise_id):
        """测试空统计"""
        stats = usage_stats_service.get_daily_stats(sample_enterprise_id)

        assert stats['total_requests'] == 0
        assert stats['total_revenue'] == 0
        assert stats['total_cost'] == 0
        assert stats['total_profit'] == 0
        assert stats['profit_margin'] == 0
        assert stats['total_input_tokens'] == 0
        assert stats['total_output_tokens'] == 0

    def test_get_daily_stats_with_data(self, usage_stats_service, sample_enterprise_id, sample_user_id):
        """测试有数据的统计"""
        # 记录多次使用
        for i in range(3):
            usage_stats_service.record_chat_usage(
                enterprise_id=sample_enterprise_id,
                user_id=sample_user_id,
                model="gpt-4",
                input_tokens=100,
                output_tokens=200,
                client_charge=Decimal("0.1"),
                backend_cost=Decimal("0.05")
            )

        stats = usage_stats_service.get_daily_stats(sample_enterprise_id)

        assert stats['total_requests'] == 3
        assert stats['total_revenue'] == 0.3
        assert stats['total_cost'] == 0.15
        assert stats['total_profit'] == 0.15
        assert stats['profit_margin'] == 50.0
        assert stats['total_input_tokens'] == 300
        assert stats['total_output_tokens'] == 600

    def test_get_daily_stats_specific_date(self, usage_stats_service, sample_enterprise_id, sample_user_id, db):
        """测试指定日期的统计"""
        # 记录今天的数据
        usage_stats_service.record_chat_usage(
            enterprise_id=sample_enterprise_id,
            user_id=sample_user_id,
            model="gpt-4",
            input_tokens=100,
            output_tokens=200,
            client_charge=Decimal("0.1"),
            backend_cost=Decimal("0.05")
        )

        # 记录昨天的数据
        yesterday = datetime.utcnow() - timedelta(days=1)
        stat = UsageStatistics(
            enterprise_id=sample_enterprise_id,
            user_id=sample_user_id,
            stat_type=StatType.CHAT,
            model="gpt-4",
            request_count=1,
            input_tokens=50,
            output_tokens=100,
            client_charge=Decimal("0.1"),
            backend_cost=Decimal("0.05"),
            profit=Decimal("0.05"),
            profit_margin=50.0,
            created_at=yesterday
        )
        db.add(stat)
        db.commit()

        # 查询今天的统计
        today_stats = usage_stats_service.get_daily_stats(sample_enterprise_id)
        assert today_stats['total_requests'] == 1
        assert today_stats['total_input_tokens'] == 100

        # 查询昨天的统计
        yesterday_stats = usage_stats_service.get_daily_stats(sample_enterprise_id, yesterday)
        assert yesterday_stats['total_requests'] == 1
        assert yesterday_stats['total_input_tokens'] == 50


class TestGetModelDistribution:
    """测试获取模型使用分布"""

    def test_get_model_distribution_empty(self, usage_stats_service, sample_enterprise_id):
        """测试空分布"""
        distribution = usage_stats_service.get_model_distribution(sample_enterprise_id)
        assert distribution == []

    def test_get_model_distribution_single_model(self, usage_stats_service, sample_enterprise_id, sample_user_id):
        """测试单个模型的分布"""
        for i in range(5):
            usage_stats_service.record_chat_usage(
                enterprise_id=sample_enterprise_id,
                user_id=sample_user_id,
                model="gpt-4",
                input_tokens=100,
                output_tokens=200,
                client_charge=Decimal("0.1"),
                backend_cost=Decimal("0.05")
            )

        distribution = usage_stats_service.get_model_distribution(sample_enterprise_id)

        assert len(distribution) == 1
        assert distribution[0]['model'] == "gpt-4"
        assert distribution[0]['count'] == 5
        assert distribution[0]['cost'] == 0.25

    def test_get_model_distribution_multiple_models(self, usage_stats_service, sample_enterprise_id, sample_user_id):
        """测试多个模型的分布"""
        models = [
            ("gpt-4", Decimal("0.05"), 3),
            ("gpt-3.5-turbo", Decimal("0.02"), 5),
            ("claude-3", Decimal("0.04"), 2)
        ]

        for model, cost, count in models:
            for i in range(count):
                usage_stats_service.record_chat_usage(
                    enterprise_id=sample_enterprise_id,
                    user_id=sample_user_id,
                    model=model,
                    input_tokens=100,
                    output_tokens=200,
                    client_charge=Decimal("0.1"),
                    backend_cost=cost
                )

        distribution = usage_stats_service.get_model_distribution(sample_enterprise_id)

        assert len(distribution) == 3
        model_counts = {d['model']: d['count'] for d in distribution}
        assert model_counts['gpt-4'] == 3
        assert model_counts['gpt-3.5-turbo'] == 5
        assert model_counts['claude-3'] == 2

    def test_get_model_distribution_custom_days(self, usage_stats_service, sample_enterprise_id, sample_user_id, db):
        """测试自定义天数的分布"""
        # 记录35天前的数据（超出默认30天范围）
        old_date = datetime.utcnow() - timedelta(days=35)
        stat = UsageStatistics(
            enterprise_id=sample_enterprise_id,
            user_id=sample_user_id,
            stat_type=StatType.CHAT,
            model="old-model",
            request_count=1,
            input_tokens=100,
            output_tokens=200,
            client_charge=Decimal("0.1"),
            backend_cost=Decimal("0.05"),
            profit=Decimal("0.05"),
            profit_margin=50.0,
            created_at=old_date
        )
        db.add(stat)
        db.commit()

        # 记录最近的数据
        usage_stats_service.record_chat_usage(
            enterprise_id=sample_enterprise_id,
            user_id=sample_user_id,
            model="new-model",
            input_tokens=100,
            output_tokens=200,
            client_charge=Decimal("0.1"),
            backend_cost=Decimal("0.05")
        )

        # 默认30天不应包含old-model
        distribution_30 = usage_stats_service.get_model_distribution(sample_enterprise_id, days=30)
        models_30 = [d['model'] for d in distribution_30]
        assert 'old-model' not in models_30
        assert 'new-model' in models_30

        # 40天应包含old-model
        distribution_40 = usage_stats_service.get_model_distribution(sample_enterprise_id, days=40)
        models_40 = [d['model'] for d in distribution_40]
        assert 'old-model' in models_40
        assert 'new-model' in models_40


class TestCheckProfitMargin:
    """测试检查利润率"""

    def test_check_profit_margin_no_data(self, usage_stats_service, sample_enterprise_id):
        """测试无数据时的利润率检查"""
        # 无数据时利润率为0，应该返回False
        result = usage_stats_service.check_profit_margin(sample_enterprise_id)
        assert result is False

    def test_check_profit_margin_low(self, usage_stats_service, sample_enterprise_id, sample_user_id):
        """测试低利润率"""
        # 记录低利润率的使用（10%）
        usage_stats_service.record_chat_usage(
            enterprise_id=sample_enterprise_id,
            user_id=sample_user_id,
            model="gpt-4",
            input_tokens=100,
            output_tokens=200,
            client_charge=Decimal("1.0"),
            backend_cost=Decimal("0.9")  # 90%成本，10%利润
        )

        result = usage_stats_service.check_profit_margin(sample_enterprise_id)
        assert result is False

    def test_check_profit_margin_acceptable(self, usage_stats_service, sample_enterprise_id, sample_user_id):
        """测试可接受的利润率"""
        # 记录高利润率的使用（50%）
        usage_stats_service.record_chat_usage(
            enterprise_id=sample_enterprise_id,
            user_id=sample_user_id,
            model="gpt-4",
            input_tokens=100,
            output_tokens=200,
            client_charge=Decimal("1.0"),
            backend_cost=Decimal("0.5")  # 50%成本，50%利润
        )

        result = usage_stats_service.check_profit_margin(sample_enterprise_id)
        assert result is True

    def test_check_profit_margin_threshold(self, usage_stats_service, sample_enterprise_id, sample_user_id):
        """测试利润率阈值边界"""
        # 记录刚好15%利润率的使用
        usage_stats_service.record_chat_usage(
            enterprise_id=sample_enterprise_id,
            user_id=sample_user_id,
            model="gpt-4",
            input_tokens=100,
            output_tokens=200,
            client_charge=Decimal("1.0"),
            backend_cost=Decimal("0.85")  # 85%成本，15%利润
        )

        result = usage_stats_service.check_profit_margin(sample_enterprise_id)
        assert result is True


class TestProfitCalculation:
    """测试利润计算"""

    def test_profit_calculation_positive(self, usage_stats_service, sample_enterprise_id, sample_user_id):
        """测试正利润计算"""
        stat = usage_stats_service.record_chat_usage(
            enterprise_id=sample_enterprise_id,
            user_id=sample_user_id,
            model="gpt-4",
            input_tokens=100,
            output_tokens=200,
            client_charge=Decimal("1.0"),
            backend_cost=Decimal("0.6")
        )

        assert stat.profit == Decimal("0.4")
        assert stat.profit_margin == 40.0

    def test_profit_calculation_zero(self, usage_stats_service, sample_enterprise_id, sample_user_id):
        """测试零利润计算"""
        stat = usage_stats_service.record_chat_usage(
            enterprise_id=sample_enterprise_id,
            user_id=sample_user_id,
            model="gpt-4",
            input_tokens=100,
            output_tokens=200,
            client_charge=Decimal("1.0"),
            backend_cost=Decimal("1.0")
        )

        assert stat.profit == Decimal("0.0")
        assert stat.profit_margin == 0.0

    def test_profit_calculation_negative(self, usage_stats_service, sample_enterprise_id, sample_user_id):
        """测试负利润计算（亏损）"""
        stat = usage_stats_service.record_chat_usage(
            enterprise_id=sample_enterprise_id,
            user_id=sample_user_id,
            model="gpt-4",
            input_tokens=100,
            output_tokens=200,
            client_charge=Decimal("1.0"),
            backend_cost=Decimal("1.5")
        )

        assert stat.profit == Decimal("-0.5")
        assert stat.profit_margin == -50.0
