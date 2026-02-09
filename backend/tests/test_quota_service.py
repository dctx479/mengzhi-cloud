"""
配额服务单元测试

测试内容:
- 配额检查和扣减
- 配额创建和更新
- 配额重置
- 配额统计
- 配额预警
- Redis 加速方法
- 降级处理和缓存同步

运行: pytest tests/test_quota_service.py -v --cov=app/services/quota_service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime, timedelta
from decimal import Decimal
import redis
from redis.exceptions import RedisError, ConnectionError

from sqlalchemy.orm import Session

from app.services.quota_service import QuotaService
from app.models.quota import (
    TenantQuota, QuotaUsage,
    QuotaResourceType, QuotaPeriodType, QuotaAlertLevel
)
from app.models.user import User
from app.models.enterprise import Enterprise
from app.core.errors import BusinessException


# ==================== Fixtures ====================

@pytest.fixture
def quota_service(test_db_session):
    """创建配额服务实例"""
    return QuotaService(test_db_session)


@pytest.fixture
def mock_quota():
    """Mock配额对象"""
    quota = MagicMock(spec=TenantQuota)
    quota.id = 1
    quota.resource_type = QuotaResourceType.TOKEN
    quota.period_type = QuotaPeriodType.DAILY
    quota.quota_limit = 10000
    quota.quota_used = 0
    quota.is_active = 1
    quota.warning_threshold = 80
    quota.critical_threshold = 90
    quota.enterprise_id = None
    quota.user_id = 123
    quota.period_start = date.today()
    quota.period_end = date.today()
    quota.last_alert_level = None
    quota.last_alert_at = None

    quota.is_expired.return_value = False
    quota.is_sufficient.return_value = True
    quota.get_remaining.return_value = 10000
    quota.get_usage_percentage.return_value = 0.0
    quota.should_alert.return_value = None
    quota.increment_usage.return_value = None
    quota.reset_usage.return_value = None

    return quota


# ==================== 配额检查测试 ====================

class TestCheckQuota:
    """配额检查功能测试"""

    @pytest.mark.unit
    def test_check_quota_sufficient(self, quota_service, test_db_session, mock_quota):
        """测试配额充足"""
        with patch.object(quota_service, 'get_or_create_quota', return_value=mock_quota):
            is_sufficient, quota, message = quota_service.check_quota(
                resource_type=QuotaResourceType.TOKEN,
                required_amount=100,
                user_id=123
            )

        assert is_sufficient is True
        assert quota == mock_quota
        assert "充足" in message

    @pytest.mark.unit
    def test_check_quota_insufficient(self, quota_service, test_db_session, mock_quota):
        """测试配额不足"""
        mock_quota.is_sufficient.return_value = False
        mock_quota.get_remaining.return_value = 50

        with patch.object(quota_service, 'get_or_create_quota', return_value=mock_quota):
            is_sufficient, quota, message = quota_service.check_quota(
                resource_type=QuotaResourceType.TOKEN,
                required_amount=100,
                user_id=123
            )

        assert is_sufficient is False
        assert "不足" in message
        assert "50" in message

    @pytest.mark.unit
    def test_check_quota_not_found(self, quota_service, test_db_session):
        """测试配额不存在"""
        with patch.object(quota_service, 'get_or_create_quota', return_value=None):
            is_sufficient, quota, message = quota_service.check_quota(
                resource_type=QuotaResourceType.TOKEN,
                required_amount=100,
                user_id=123
            )

        assert is_sufficient is False
        assert quota is None
        assert "不存在" in message

    @pytest.mark.unit
    def test_check_quota_disabled(self, quota_service, test_db_session, mock_quota):
        """测试配额已禁用"""
        mock_quota.is_active = 0

        with patch.object(quota_service, 'get_or_create_quota', return_value=mock_quota):
            is_sufficient, quota, message = quota_service.check_quota(
                resource_type=QuotaResourceType.TOKEN,
                required_amount=100,
                user_id=123
            )

        assert is_sufficient is False
        assert "禁用" in message

    @pytest.mark.unit
    def test_check_quota_expired(self, quota_service, test_db_session, mock_quota):
        """测试配额已过期"""
        mock_quota.is_expired.return_value = True

        with patch.object(quota_service, 'get_or_create_quota', return_value=mock_quota):
            with patch.object(quota_service, 'reset_quota'):
                with patch.object(test_db_session, 'query') as mock_query:
                    mock_query.return_value.filter.return_value.first.return_value = mock_quota
                    mock_quota.is_expired.return_value = False

                    is_sufficient, quota, message = quota_service.check_quota(
                        resource_type=QuotaResourceType.TOKEN,
                        required_amount=100,
                        user_id=123
                    )

        # 应该触发重置
        quota_service.reset_quota.assert_called_once()

    @pytest.mark.unit
    def test_check_quota_simple(self, quota_service, test_db_session, mock_quota):
        """测试简单配额检查"""
        with patch.object(quota_service, 'get_or_create_quota', return_value=mock_quota):
            is_sufficient = quota_service.check_quota_simple(
                resource_type=QuotaResourceType.TOKEN,
                required_amount=100,
                user_id=123
            )

        assert is_sufficient is True


# ==================== 配额扣减测试 ====================

class TestDeductQuota:
    """配额扣减功能测试"""

    @pytest.mark.unit
    def test_deduct_quota_success(self, quota_service, test_db_session, mock_quota):
        """测试成功扣减配额"""
        with patch.object(quota_service, 'check_quota', return_value=(True, mock_quota, "充足")):
            with patch.object(test_db_session, 'add'):
                with patch.object(test_db_session, 'commit'):
                    success, message = quota_service.deduct_quota(
                        resource_type=QuotaResourceType.TOKEN,
                        amount=100,
                        user_id=123,
                        operation="chat"
                    )

        assert success is True
        assert "成功" in message
        mock_quota.increment_usage.assert_called_once_with(100)

    @pytest.mark.unit
    def test_deduct_quota_insufficient(self, quota_service, test_db_session):
        """测试配额不足时扣减"""
        with patch.object(quota_service, 'check_quota', return_value=(False, None, "配额不足")):
            success, message = quota_service.deduct_quota(
                resource_type=QuotaResourceType.TOKEN,
                amount=100,
                user_id=123
            )

        assert success is False
        assert "不足" in message

    @pytest.mark.unit
    def test_deduct_quota_with_alert(self, quota_service, test_db_session, mock_quota):
        """测试扣减配额触发预警"""
        mock_quota.should_alert.return_value = QuotaAlertLevel.WARNING

        with patch.object(quota_service, 'check_quota', return_value=(True, mock_quota, "充足")):
            with patch.object(quota_service, '_send_quota_alert') as mock_alert:
                with patch.object(test_db_session, 'add'):
                    with patch.object(test_db_session, 'commit'):
                        quota_service.deduct_quota(
                            resource_type=QuotaResourceType.TOKEN,
                            amount=9000,  # 触发预警
                            user_id=123
                        )

        mock_alert.assert_called_once()
        assert mock_quota.last_alert_level == QuotaAlertLevel.WARNING

    @pytest.mark.unit
    def test_deduct_quota_with_metadata(self, quota_service, test_db_session, mock_quota):
        """测试带元数据扣减配额"""
        metadata = {"model": "gpt-4", "tokens": 100}

        with patch.object(quota_service, 'check_quota', return_value=(True, mock_quota, "充足")):
            with patch.object(test_db_session, 'add') as mock_add:
                with patch.object(test_db_session, 'commit'):
                    quota_service.deduct_quota(
                        resource_type=QuotaResourceType.TOKEN,
                        amount=100,
                        user_id=123,
                        operation="chat",
                        resource_id="conv-123",
                        resource_type_name="conversation",
                        metadata=metadata
                    )

        # 验证使用记录被创建
        mock_add.assert_called_once()


# ==================== 配额重置测试 ====================

class TestResetQuota:
    """配额重置功能测试"""

    @pytest.mark.unit
    def test_reset_quota_success(self, quota_service, test_db_session, mock_quota):
        """测试成功重置配额"""
        today = date.today()
        mock_quota.period_type = QuotaPeriodType.DAILY

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_quota

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with patch.object(test_db_session, 'commit'):
                success = quota_service.reset_quota(quota_id=1)

        assert success is True
        mock_quota.reset_usage.assert_called_once()
        assert mock_quota.period_start == today
        assert mock_quota.period_end == today

    @pytest.mark.unit
    def test_reset_quota_monthly(self, quota_service, test_db_session, mock_quota):
        """测试重置月度配额"""
        today = date.today()
        mock_quota.period_type = QuotaPeriodType.MONTHLY

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_quota

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with patch.object(test_db_session, 'commit'):
                success = quota_service.reset_quota(quota_id=1)

        assert success is True
        # 验证月度周期设置正确
        assert mock_quota.period_start.day == 1

    @pytest.mark.unit
    def test_reset_quota_yearly(self, quota_service, test_db_session, mock_quota):
        """测试重置年度配额"""
        today = date.today()
        mock_quota.period_type = QuotaPeriodType.YEARLY

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_quota

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with patch.object(test_db_session, 'commit'):
                success = quota_service.reset_quota(quota_id=1)

        assert success is True
        assert mock_quota.period_start.month == 1
        assert mock_quota.period_start.day == 1

    @pytest.mark.unit
    def test_reset_quota_not_found(self, quota_service, test_db_session):
        """测试重置不存在的配额"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None

        with patch.object(test_db_session, 'query', return_value=mock_query):
            success = quota_service.reset_quota(quota_id=999)

        assert success is False

    @pytest.mark.unit
    def test_reset_expired_quotas(self, quota_service, test_db_session):
        """测试批量重置过期配额"""
        mock_quota1 = MagicMock()
        mock_quota1.id = 1
        mock_quota2 = MagicMock()
        mock_quota2.id = 2

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [mock_quota1, mock_quota2]

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with patch.object(quota_service, 'reset_quota', return_value=True):
                count = quota_service.reset_expired_quotas()

        assert count == 2


# ==================== 配额管理测试 ====================

class TestQuotaManagement:
    """配额管理功能测试"""

    @pytest.mark.unit
    def test_get_or_create_quota_existing(self, quota_service, test_db_session, mock_quota):
        """测试获取已存在的配额"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_quota

        with patch.object(test_db_session, 'query', return_value=mock_query):
            quota = quota_service.get_or_create_quota(
                resource_type=QuotaResourceType.TOKEN,
                period_type=QuotaPeriodType.DAILY,
                user_id=123
            )

        assert quota == mock_quota

    @pytest.mark.unit
    def test_get_or_create_quota_create_new(self, quota_service, test_db_session):
        """测试创建新配额"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with patch.object(quota_service, '_create_default_quota') as mock_create:
                mock_quota = MagicMock()
                mock_create.return_value = mock_quota

                quota = quota_service.get_or_create_quota(
                    resource_type=QuotaResourceType.TOKEN,
                    period_type=QuotaPeriodType.DAILY,
                    user_id=123,
                    auto_create=True
                )

        mock_create.assert_called_once()
        assert quota == mock_quota

    @pytest.mark.unit
    def test_get_or_create_quota_no_user_or_enterprise(self, quota_service, test_db_session):
        """测试未提供用户ID或企业ID"""
        quota = quota_service.get_or_create_quota(
            resource_type=QuotaResourceType.TOKEN,
            period_type=QuotaPeriodType.DAILY
        )

        assert quota is None

    @pytest.mark.unit
    def test_create_quota(self, quota_service, test_db_session):
        """测试创建配额"""
        with patch.object(test_db_session, 'add'):
            with patch.object(test_db_session, 'commit'):
                with patch.object(test_db_session, 'refresh'):
                    with patch('app.services.quota_service.TenantQuota.create_for_period') as mock_create:
                        mock_quota = MagicMock()
                        mock_create.return_value = mock_quota

                        quota = quota_service.create_quota(
                            resource_type=QuotaResourceType.TOKEN,
                            period_type=QuotaPeriodType.DAILY,
                            quota_limit=10000,
                            user_id=123
                        )

        assert quota == mock_quota

    @pytest.mark.unit
    def test_update_quota(self, quota_service, test_db_session, mock_quota):
        """测试更新配额"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_quota

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with patch.object(test_db_session, 'commit'):
                with patch.object(test_db_session, 'refresh'):
                    quota = quota_service.update_quota(
                        quota_id=1,
                        quota_limit=20000,
                        warning_threshold=85
                    )

        assert mock_quota.quota_limit == 20000
        assert mock_quota.warning_threshold == 85

    @pytest.mark.unit
    def test_update_quota_not_found(self, quota_service, test_db_session):
        """测试更新不存在的配额"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None

        with patch.object(test_db_session, 'query', return_value=mock_query):
            quota = quota_service.update_quota(quota_id=999, quota_limit=20000)

        assert quota is None

    @pytest.mark.unit
    def test_delete_quota(self, quota_service, test_db_session, mock_quota):
        """测试删除配额"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_quota

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with patch.object(test_db_session, 'delete'):
                with patch.object(test_db_session, 'commit'):
                    success = quota_service.delete_quota(quota_id=1)

        assert success is True

    @pytest.mark.unit
    def test_delete_quota_not_found(self, quota_service, test_db_session):
        """测试删除不存在的配额"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None

        with patch.object(test_db_session, 'query', return_value=mock_query):
            success = quota_service.delete_quota(quota_id=999)

        assert success is False


# ==================== 配额查询测试 ====================

class TestQuotaQuery:
    """配额查询功能测试"""

    @pytest.mark.unit
    def test_get_quota(self, quota_service, test_db_session, mock_quota):
        """测试获取配额"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_quota

        with patch.object(test_db_session, 'query', return_value=mock_query):
            quota = quota_service.get_quota(quota_id=1)

        assert quota == mock_quota

    @pytest.mark.unit
    def test_list_quotas(self, quota_service, test_db_session):
        """测试列表查询配额"""
        mock_quota1 = MagicMock()
        mock_quota2 = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_quota1, mock_quota2]

        with patch.object(test_db_session, 'query', return_value=mock_query):
            quotas, total = quota_service.list_quotas(user_id=123)

        assert len(quotas) == 2
        assert total == 2

    @pytest.mark.unit
    def test_list_quotas_with_filters(self, quota_service, test_db_session):
        """测试带筛选条件的列表查询"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        with patch.object(test_db_session, 'query', return_value=mock_query):
            quotas, total = quota_service.list_quotas(
                user_id=123,
                resource_type=QuotaResourceType.TOKEN,
                period_type=QuotaPeriodType.DAILY,
                is_active=True
            )

        # 验证筛选条件被应用
        assert mock_query.filter.called

    @pytest.mark.unit
    def test_get_quota_usage_records(self, quota_service, test_db_session):
        """测试获取配额使用记录"""
        mock_usage1 = MagicMock()
        mock_usage2 = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_usage1, mock_usage2]

        with patch.object(test_db_session, 'query', return_value=mock_query):
            records, total = quota_service.get_quota_usage_records(quota_id=1)

        assert len(records) == 2
        assert total == 2


# ==================== 配额统计测试 ====================

class TestQuotaStatistics:
    """配额统计功能测试"""

    @pytest.mark.unit
    def test_get_quota_statistics(self, quota_service, test_db_session):
        """测试获取配额统计"""
        mock_quota1 = MagicMock()
        mock_quota1.resource_type = QuotaResourceType.TOKEN
        mock_quota1.period_type = QuotaPeriodType.DAILY
        mock_quota1.quota_limit = 10000
        mock_quota1.quota_used = 5000
        mock_quota1.get_remaining.return_value = 5000
        mock_quota1.get_usage_percentage.return_value = 50.0
        mock_quota1.should_alert.return_value = None

        mock_quota2 = MagicMock()
        mock_quota2.resource_type = QuotaResourceType.MESSAGE
        mock_quota2.period_type = QuotaPeriodType.DAILY
        mock_quota2.quota_limit = 100
        mock_quota2.quota_used = 90
        mock_quota2.get_remaining.return_value = 10
        mock_quota2.get_usage_percentage.return_value = 90.0
        mock_quota2.should_alert.return_value = QuotaAlertLevel.CRITICAL

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_quota1, mock_quota2]

        with patch.object(test_db_session, 'query', return_value=mock_query):
            stats = quota_service.get_quota_statistics(user_id=123)

        assert stats["total_quotas"] == 2
        assert "by_resource_type" in stats
        assert "by_period_type" in stats
        assert "alerts" in stats
        assert stats["alerts"]["critical"] == 1

    @pytest.mark.unit
    def test_get_quota_statistics_empty(self, quota_service, test_db_session):
        """测试空配额统计"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        with patch.object(test_db_session, 'query', return_value=mock_query):
            stats = quota_service.get_quota_statistics(user_id=123)

        assert stats["total_quotas"] == 0
        assert stats["total_usage"] == 0


# ==================== 私有方法测试 ====================

class TestPrivateMethods:
    """私有方法测试"""

    @pytest.mark.unit
    def test_get_default_quota_limit_personal(self, quota_service, test_db_session):
        """测试获取个人用户默认配额"""
        limit = quota_service._get_default_quota_limit(
            resource_type=QuotaResourceType.TOKEN,
            period_type=QuotaPeriodType.DAILY,
            user_id=123
        )

        assert limit == 10000  # 个人用户默认Token配额

    @pytest.mark.unit
    def test_get_default_quota_limit_enterprise(self, quota_service, test_db_session):
        """测试获取企业用户默认配额"""
        mock_enterprise = MagicMock()
        mock_enterprise.get_plan_quota.return_value = {
            "daily_chat_limit": 200,
            "monthly_token_limit": 500000
        }

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_enterprise

        with patch.object(test_db_session, 'query', return_value=mock_query):
            limit = quota_service._get_default_quota_limit(
                resource_type=QuotaResourceType.MESSAGE,
                period_type=QuotaPeriodType.DAILY,
                enterprise_id=1
            )

        assert limit == 200

    @pytest.mark.unit
    def test_send_quota_alert(self, quota_service, test_db_session, mock_quota):
        """测试发送配额预警"""
        mock_quota.get_usage_percentage.return_value = 85.0
        mock_quota.get_remaining.return_value = 1500
        mock_quota.user_id = 123

        # 不应该抛出异常
        quota_service._send_quota_alert(mock_quota, QuotaAlertLevel.WARNING)

    @pytest.mark.unit
    def test_create_default_quota(self, quota_service, test_db_session):
        """测试创建默认配额"""
        with patch.object(quota_service, '_get_default_quota_limit', return_value=10000):
            with patch.object(quota_service, 'create_quota') as mock_create:
                mock_quota = MagicMock()
                mock_create.return_value = mock_quota

                quota = quota_service._create_default_quota(
                    resource_type=QuotaResourceType.TOKEN,
                    period_type=QuotaPeriodType.DAILY,
                    user_id=123
                )

        mock_create.assert_called_once()
        assert quota == mock_quota


# ==================== Redis 加速方法测试 ====================

class TestRedisQuotaMethods:
    """Redis 加速方法测试"""

    @pytest.fixture
    def redis_quota_service(self, test_db_session):
        """创建带 Redis 的配额服务"""
        mock_redis = MagicMock(spec=redis.Redis)
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = "0"
        mock_redis.register_script.return_value = MagicMock()
        return QuotaService(test_db_session, redis_client=mock_redis)

    @pytest.mark.unit
    def test_check_quota_redis_sufficient(self, redis_quota_service, test_db_session):
        """测试 Redis 配额检查 - 充足"""
        redis_quota_service.redis.get.return_value = "1000"  # 已使用 1000

        with patch.object(redis_quota_service, '_get_quota_limit_from_db', return_value=10000):
            is_sufficient, message = redis_quota_service.check_quota_redis(
                resource_type=QuotaResourceType.TOKEN,
                required_amount=100,
                user_id=123
            )

        assert is_sufficient is True
        assert "充足" in message

    @pytest.mark.unit
    def test_check_quota_redis_insufficient(self, redis_quota_service, test_db_session):
        """测试 Redis 配额检查 - 不足"""
        redis_quota_service.redis.get.return_value = "9900"  # 已使用 9900

        with patch.object(redis_quota_service, '_get_quota_limit_from_db', return_value=10000):
            is_sufficient, message = redis_quota_service.check_quota_redis(
                resource_type=QuotaResourceType.TOKEN,
                required_amount=200,  # 需要 200，但只剩 100
                user_id=123
            )

        assert is_sufficient is False
        assert "不足" in message

    @pytest.mark.unit
    def test_check_quota_redis_fallback_to_db(self, redis_quota_service, test_db_session):
        """测试 Redis 失败时降级到数据库"""
        redis_quota_service.redis.get.side_effect = RedisError("连接失败")

        with patch.object(redis_quota_service, 'check_quota', return_value=(True, None, "使用数据库")):
            is_sufficient, message = redis_quota_service.check_quota_redis(
                resource_type=QuotaResourceType.TOKEN,
                required_amount=100,
                user_id=123,
                use_fallback=True
            )

        # 应该使用 check_quota 方法
        redis_quota_service.check_quota.assert_called_once()

    @pytest.mark.unit
    def test_check_quota_redis_no_redis_fallback(self, test_db_session):
        """测试 Redis 不可用时降级到数据库"""
        # 创建没有 Redis 的服务
        quota_service = QuotaService(test_db_session, redis_client=None)

        with patch.object(quota_service, 'check_quota', return_value=(True, None, "使用数据库")):
            is_sufficient, message = quota_service.check_quota_redis(
                resource_type=QuotaResourceType.TOKEN,
                required_amount=100,
                user_id=123,
                use_fallback=True
            )

        # 应该直接使用 check_quota
        assert is_sufficient is True
        quota_service.check_quota.assert_called_once()

    @pytest.mark.unit
    def test_deduct_quota_redis_success(self, redis_quota_service, test_db_session):
        """测试 Redis 原子扣减 - 成功"""
        redis_quota_service.deduct_script = MagicMock(return_value=1)
        redis_quota_service.redis.get.return_value = "100"  # 扣减后为 100

        with patch.object(redis_quota_service, '_get_quota_limit_from_db', return_value=10000):
            with patch.object(redis_quota_service, '_record_quota_usage_async'):
                is_success, message = redis_quota_service.deduct_quota_redis(
                    resource_type=QuotaResourceType.TOKEN,
                    amount=100,
                    user_id=123
                )

        assert is_success is True
        assert "成功" in message
        # 验证 Lua 脚本被调用
        redis_quota_service.deduct_script.assert_called_once()

    @pytest.mark.unit
    def test_deduct_quota_redis_insufficient(self, redis_quota_service, test_db_session):
        """测试 Redis 原子扣减 - 配额不足"""
        redis_quota_service.deduct_script = MagicMock(return_value=0)  # 返回 0 表示失败
        redis_quota_service.redis.get.return_value = "9900"

        with patch.object(redis_quota_service, '_get_quota_limit_from_db', return_value=10000):
            is_success, message = redis_quota_service.deduct_quota_redis(
                resource_type=QuotaResourceType.TOKEN,
                amount=200,
                user_id=123
            )

        assert is_success is False
        assert "不足" in message

    @pytest.mark.unit
    def test_deduct_quota_redis_fallback(self, redis_quota_service, test_db_session):
        """测试 Redis 失败时扣减回退到数据库"""
        redis_quota_service.deduct_script = MagicMock(side_effect=RedisError("连接失败"))

        with patch.object(redis_quota_service, '_get_quota_limit_from_db', return_value=10000):
            with patch.object(redis_quota_service, 'deduct_quota', return_value=(True, "使用数据库")):
                is_success, message = redis_quota_service.deduct_quota_redis(
                    resource_type=QuotaResourceType.TOKEN,
                    amount=100,
                    user_id=123,
                    use_fallback=True
                )

        # 应该使用 deduct_quota
        redis_quota_service.deduct_quota.assert_called_once()

    @pytest.mark.unit
    def test_sync_redis_to_db(self, redis_quota_service, test_db_session):
        """测试将 Redis 数据同步到数据库"""
        # Mock Redis keys
        redis_quota_service.redis.keys.return_value = [
            "quota:user:123:token:daily:2024-01-15",
            "quota:enterprise:1:token:daily:2024-01-15"
        ]
        redis_quota_service.redis.get.side_effect = ["5000", "8000"]

        # Mock 数据库查询
        mock_quota1 = MagicMock()
        mock_quota1.quota_used = 0
        mock_quota2 = MagicMock()
        mock_quota2.quota_used = 0

        with patch.object(test_db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value = MagicMock()
            mock_query.return_value.filter.return_value.first.side_effect = [mock_quota1, mock_quota2]

            with patch.object(test_db_session, 'commit'):
                synced_count = redis_quota_service.sync_redis_to_db()

        # 应该同步 2 条记录
        assert synced_count == 2
        assert mock_quota1.quota_used == 5000
        assert mock_quota2.quota_used == 8000

    @pytest.mark.unit
    def test_sync_redis_to_db_no_redis(self, test_db_session):
        """测试 Redis 不可用时同步失败"""
        quota_service = QuotaService(test_db_session, redis_client=None)
        synced_count = quota_service.sync_redis_to_db()

        assert synced_count == 0

    @pytest.mark.unit
    def test_invalidate_redis_cache_all(self, redis_quota_service, test_db_session):
        """测试清除所有 Redis 缓存"""
        redis_quota_service.redis.keys.return_value = [
            "quota:user:123:token:daily:2024-01-15",
            "quota:user:123:message:daily:2024-01-15"
        ]
        redis_quota_service.redis.delete.return_value = 2

        deleted = redis_quota_service.invalidate_redis_cache()

        assert deleted == 2
        redis_quota_service.redis.keys.assert_called_once()
        redis_quota_service.redis.delete.assert_called_once()

    @pytest.mark.unit
    def test_invalidate_redis_cache_specific_user(self, redis_quota_service, test_db_session):
        """测试清除特定用户的 Redis 缓存"""
        redis_quota_service.redis.keys.return_value = [
            "quota:user:123:token:daily:2024-01-15"
        ]
        redis_quota_service.redis.delete.return_value = 1

        deleted = redis_quota_service.invalidate_redis_cache(user_id=123)

        assert deleted == 1
        # 验证 pattern 包含用户 ID
        call_args = redis_quota_service.redis.keys.call_args
        assert "123" in call_args[0][0]

    @pytest.mark.unit
    def test_invalidate_redis_cache_on_update(self, redis_quota_service, test_db_session):
        """测试更新配额时清除 Redis 缓存"""
        mock_quota = MagicMock()
        mock_quota.id = 1
        mock_quota.user_id = 123
        mock_quota.enterprise_id = None
        mock_quota.resource_type = QuotaResourceType.TOKEN
        mock_quota.period_type = QuotaPeriodType.DAILY
        mock_quota.quota_limit = 10000
        mock_quota.warning_threshold = 80
        mock_quota.critical_threshold = 90
        mock_quota.is_active = 1

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_quota

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with patch.object(test_db_session, 'commit'):
                with patch.object(test_db_session, 'refresh'):
                    with patch.object(redis_quota_service, 'invalidate_redis_cache') as mock_invalidate:
                        redis_quota_service.update_quota(
                            quota_id=1,
                            quota_limit=20000
                        )

        # 应该清除缓存
        mock_invalidate.assert_called_once()

    @pytest.mark.unit
    def test_invalidate_redis_cache_on_delete(self, redis_quota_service, test_db_session):
        """测试删除配额时清除 Redis 缓存"""
        mock_quota = MagicMock()
        mock_quota.id = 1
        mock_quota.user_id = 123
        mock_quota.enterprise_id = None
        mock_quota.resource_type = QuotaResourceType.TOKEN
        mock_quota.period_type = QuotaPeriodType.DAILY

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_quota

        with patch.object(test_db_session, 'query', return_value=mock_query):
            with patch.object(test_db_session, 'delete'):
                with patch.object(test_db_session, 'commit'):
                    with patch.object(redis_quota_service, 'invalidate_redis_cache') as mock_invalidate:
                        redis_quota_service.delete_quota(quota_id=1)

        # 应该清除缓存
        mock_invalidate.assert_called_once()

    @pytest.mark.unit
    def test_get_quota_cache_key_generation(self, redis_quota_service):
        """测试配额缓存 key 生成"""
        key = redis_quota_service._get_quota_cache_key(
            user_id=123,
            enterprise_id=None,
            resource_type=QuotaResourceType.TOKEN,
            period_type=QuotaPeriodType.DAILY
        )

        assert "quota:user:123:token:daily:" in key
        assert str(date.today()) in key

    @pytest.mark.unit
    def test_get_redis_ttl_seconds(self, redis_quota_service):
        """测试 Redis TTL 计算"""
        # 日度配额
        ttl = redis_quota_service._get_redis_ttl_seconds(QuotaPeriodType.DAILY)
        assert ttl == 86400

        # 月度配额
        ttl = redis_quota_service._get_redis_ttl_seconds(QuotaPeriodType.MONTHLY)
        assert ttl == 86400 * 32

        # 年度配额
        ttl = redis_quota_service._get_redis_ttl_seconds(QuotaPeriodType.YEARLY)
        assert ttl == 86400 * 365


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
