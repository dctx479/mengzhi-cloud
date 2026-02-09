"""
计费功能测试
"""
import pytest
from decimal import Decimal
from app.services.strict_billing import StrictBillingService, InsufficientQuotaError, InsufficientBalanceError


class TestStrictBilling:
    """严谨计费服务测试"""

    def test_calculate_chat_cost(self, db):
        """测试对话计费"""
        billing = StrictBillingService(db)

        # DeepSeek计费
        cost = billing.calculate_cost("chat", {
            "provider": "deepseek",
            "input_tokens": 1000,
            "output_tokens": 2000
        })
        assert cost == Decimal("0.5")  # 1000*0.0001 + 2000*0.0002

        # GPT-4计费
        cost = billing.calculate_cost("chat", {
            "provider": "openai_gpt4",
            "input_tokens": 1000,
            "output_tokens": 2000
        })
        assert cost == Decimal("5.0")  # 1000*0.001 + 2000*0.002

    def test_calculate_image_cost(self, db):
        """测试图片计费"""
        billing = StrictBillingService(db)

        # 512x512
        cost = billing.calculate_cost("jimeng_image", {"resolution": "512x512"})
        assert cost == Decimal("0.1")

        # 1024x1024
        cost = billing.calculate_cost("jimeng_image", {"resolution": "1024x1024"})
        assert cost == Decimal("0.3")

        # 2048x2048
        cost = billing.calculate_cost("jimeng_image", {"resolution": "2048x2048"})
        assert cost == Decimal("0.8")

    def test_calculate_video_cost_by_second(self, db):
        """测试视频按秒计费"""
        billing = StrictBillingService(db)

        # 720p, 10秒
        cost = billing.calculate_cost("jimeng_video", {
            "resolution": "720p",
            "duration": 10
        })
        assert cost == Decimal("5.0")  # 10 * 0.5

        # 1080p, 10秒
        cost = billing.calculate_cost("jimeng_video", {
            "resolution": "1080p",
            "duration": 10
        })
        assert cost == Decimal("10.0")  # 10 * 1.0

    def test_calculate_video_cost_by_frame(self, db):
        """测试视频按帧计费"""
        billing = StrictBillingService(db)

        # 720p 30fps, 300帧（10秒）
        cost = billing.calculate_cost("jimeng_video_frames", {
            "resolution": "720p_30fps",
            "frames": 300
        })
        assert cost == Decimal("5.1")  # 300 * 0.017

        # 1080p 24fps, 240帧（10秒）
        cost = billing.calculate_cost("jimeng_video_frames", {
            "resolution": "1080p_24fps",
            "frames": 240
        })
        assert cost == Decimal("9.6")  # 240 * 0.04

    def test_idempotency(self, db, test_enterprise):
        """测试幂等性"""
        billing = StrictBillingService(db)

        # 第一次请求
        transaction1 = billing.pre_deduct(
            enterprise_id=test_enterprise.id,
            service_type="jimeng_image",
            params={"resolution": "1024x1024"},
            idempotency_key="test-key-123"
        )

        # 第二次相同请求（应返回相同交易）
        transaction2 = billing.pre_deduct(
            enterprise_id=test_enterprise.id,
            service_type="jimeng_image",
            params={"resolution": "1024x1024"},
            idempotency_key="test-key-123"
        )

        assert transaction1.id == transaction2.id

    def test_insufficient_quota(self, db, test_enterprise_low_quota):
        """测试配额不足"""
        billing = StrictBillingService(db)

        with pytest.raises(InsufficientQuotaError):
            billing.pre_deduct(
                enterprise_id=test_enterprise_low_quota.id,
                service_type="jimeng_image",
                params={"resolution": "1024x1024"}
            )

    def test_insufficient_balance(self, db, test_enterprise_low_balance):
        """测试余额不足"""
        billing = StrictBillingService(db)

        with pytest.raises(InsufficientBalanceError):
            billing.pre_deduct(
                enterprise_id=test_enterprise_low_balance.id,
                service_type="jimeng_video",
                params={"resolution": "1080p", "duration": 100}
            )

    def test_refund(self, db, test_enterprise):
        """测试退款"""
        billing = StrictBillingService(db)

        # 预扣费
        transaction = billing.pre_deduct(
            enterprise_id=test_enterprise.id,
            service_type="jimeng_image",
            params={"resolution": "1024x1024"}
        )

        original_balance = test_enterprise.quota.balance

        # 退款
        billing.refund_transaction(
            transaction.id,
            reason="生成失败",
            refund_percentage=100
        )

        # 验证余额恢复
        db.refresh(test_enterprise.quota)
        assert test_enterprise.quota.balance == original_balance

    def test_confirm_transaction(self, db, test_enterprise):
        """测试确认交易"""
        billing = StrictBillingService(db)

        # 预扣费
        transaction = billing.pre_deduct(
            enterprise_id=test_enterprise.id,
            service_type="jimeng_image",
            params={"resolution": "1024x1024"}
        )

        # 确认交易
        billing.confirm_transaction(
            transaction.id,
            actual_usage={"result_url": "https://example.com/image.png"}
        )

        # 验证状态
        db.refresh(transaction)
        assert transaction.status == "completed"
        assert transaction.completed_at is not None


# Fixtures
@pytest.fixture
def test_enterprise(db):
    """测试企业（正常配额和余额）"""
    from app.models.enterprise import Enterprise
    from app.models.quota import TenantQuota

    enterprise = Enterprise(name="测试企业", contact_email="test@example.com")
    db.add(enterprise)
    db.commit()

    quota = TenantQuota(
        enterprise_id=enterprise.id,
        monthly_tokens=100000,
        daily_tokens=5000,
        monthly_images=100,
        daily_images=20,
        monthly_video_seconds=60,
        daily_video_seconds=10,
        balance=Decimal("100.00")
    )
    db.add(quota)
    db.commit()

    enterprise.quota = quota
    return enterprise


@pytest.fixture
def test_enterprise_low_quota(db):
    """测试企业（配额不足）"""
    from app.models.enterprise import Enterprise
    from app.models.quota import TenantQuota

    enterprise = Enterprise(name="低配额企业", contact_email="low@example.com")
    db.add(enterprise)
    db.commit()

    quota = TenantQuota(
        enterprise_id=enterprise.id,
        monthly_images=1,
        daily_images=0,  # 今日配额已用完
        balance=Decimal("100.00")
    )
    db.add(quota)
    db.commit()

    enterprise.quota = quota
    return enterprise


@pytest.fixture
def test_enterprise_low_balance(db):
    """测试企业（余额不足）"""
    from app.models.enterprise import Enterprise
    from app.models.quota import TenantQuota

    enterprise = Enterprise(name="低余额企业", contact_email="lowbal@example.com")
    db.add(enterprise)
    db.commit()

    quota = TenantQuota(
        enterprise_id=enterprise.id,
        monthly_video_seconds=100,
        daily_video_seconds=20,
        balance=Decimal("1.00")  # 余额不足
    )
    db.add(quota)
    db.commit()

    enterprise.quota = quota
    return enterprise
