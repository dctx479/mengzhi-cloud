"""
风控系统测试用例

测试风险检测、规则引擎、黑名单功能等核心风控功能。

版本: 1.0
更新日期: 2026-01-23
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.models.risk_control import (
    RiskRule, RiskEvent, RiskBlacklist, RiskStatistics,
    RiskLevel, RiskAction, RuleType, EventType, BlacklistType
)
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.services.risk_control_service import RiskControlService
from app.services.payment_service import PaymentService
from app.core.errors import BusinessException, ErrorCode


class TestRiskControlService:
    """风控服务测试类"""

    @pytest.fixture
    def risk_service(self, db_session: Session):
        """创建风控服务实例"""
        return RiskControlService(db_session)

    @pytest.fixture
    def sample_user(self, db_session: Session):
        """创建测试用户"""
        user = User(
            id="test_user_001",
            username="testuser",
            email="test@example.com",
            phone="13800138000"
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def sample_order(self, db_session: Session, sample_user):
        """创建测试订单"""
        order = Order(
            id=1,
            user_id=sample_user.id,
            amount=Decimal("100.00"),
            status=OrderStatus.PENDING
        )
        db_session.add(order)
        db_session.commit()
        return order

    def test_create_risk_rule(self, risk_service: RiskControlService):
        """测试创建风控规则"""
        rule_data = {
            "name": "频率限制规则",
            "description": "限制用户支付频率",
            "rule_type": RuleType.FREQUENCY.value,
            "conditions": {"event_types": ["payment"]},
            "risk_level": RiskLevel.MEDIUM.value,
            "action": RiskAction.REVIEW.value,
            "time_window": 3600,
            "max_count": 5,
            "created_by": "admin"
        }

        rule = risk_service.create_rule(rule_data)

        assert rule.name == "频率限制规则"
        assert rule.rule_type == RuleType.FREQUENCY.value
        assert rule.risk_level == RiskLevel.MEDIUM.value
        assert rule.action == RiskAction.REVIEW.value
        assert rule.time_window == 3600
        assert rule.max_count == 5
        assert rule.is_active is True

    def test_create_blacklist(self, risk_service: RiskControlService):
        """测试创建黑名单"""
        blacklist_data = {
            "blacklist_type": BlacklistType.IP.value,
            "value": "192.168.1.100",
            "reason": "恶意攻击",
            "risk_level": RiskLevel.HIGH.value,
            "created_by": "admin"
        }

        blacklist = risk_service.add_to_blacklist(blacklist_data)

        assert blacklist.blacklist_type == BlacklistType.IP.value
        assert blacklist.value == "192.168.1.100"
        assert blacklist.reason == "恶意攻击"
        assert blacklist.risk_level == RiskLevel.HIGH.value
        assert blacklist.is_active is True

    def test_check_risk_low_risk(self, risk_service: RiskControlService, sample_user):
        """测试低风险场景"""
        event_data = {
            "order_id": 1,
            "amount": 50.0,
            "payment_method": "alipay"
        }

        context = {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0"
        }

        result = risk_service.check_risk(
            event_type=EventType.PAYMENT.value,
            user_id=sample_user.id,
            event_data=event_data,
            context=context
        )

        assert result["risk_level"] == RiskLevel.LOW.value
        assert result["action"] == RiskAction.ALLOW.value
        assert result["risk_score"] < 20

    def test_check_risk_blacklist_hit(self, risk_service: RiskControlService, sample_user):
        """测试黑名单命中"""
        # 先添加IP黑名单
        blacklist_data = {
            "blacklist_type": BlacklistType.IP.value,
            "value": "192.168.1.100",
            "reason": "恶意IP",
            "risk_level": RiskLevel.HIGH.value,
            "created_by": "admin"
        }
        risk_service.add_to_blacklist(blacklist_data)

        event_data = {
            "order_id": 1,
            "amount": 100.0,
            "payment_method": "alipay"
        }

        context = {
            "ip_address": "192.168.1.100",  # 黑名单IP
            "user_agent": "Mozilla/5.0"
        }

        result = risk_service.check_risk(
            event_type=EventType.PAYMENT.value,
            user_id=sample_user.id,
            event_data=event_data,
            context=context
        )

        assert len(result["blacklist_hits"]) > 0
        assert result["blacklist_hits"][0]["value"] == "192.168.1.100"
        assert result["risk_score"] >= 30  # 黑名单命中会增加风险分数

    def test_check_risk_frequency_rule(self, risk_service: RiskControlService, sample_user):
        """测试频率限制规则"""
        # 创建频率限制规则
        rule_data = {
            "name": "支付频率限制",
            "rule_type": RuleType.FREQUENCY.value,
            "conditions": {"event_types": ["payment"]},
            "risk_level": RiskLevel.MEDIUM.value,
            "action": RiskAction.REVIEW.value,
            "time_window": 3600,  # 1小时
            "max_count": 2,       # 最多2次
            "created_by": "admin"
        }
        risk_service.create_rule(rule_data)

        # 模拟多次支付事件
        event_data = {
            "order_id": 1,
            "amount": 100.0,
            "payment_method": "alipay"
        }

        context = {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0"
        }

        # 第一次支付 - 应该通过
        result1 = risk_service.check_risk(
            event_type=EventType.PAYMENT.value,
            user_id=sample_user.id,
            event_data=event_data,
            context=context
        )

        # 第二次支付 - 应该通过
        result2 = risk_service.check_risk(
            event_type=EventType.PAYMENT.value,
            user_id=sample_user.id,
            event_data=event_data,
            context=context
        )

        # 第三次支付 - 应该触发频率限制
        result3 = risk_service.check_risk(
            event_type=EventType.PAYMENT.value,
            user_id=sample_user.id,
            event_data=event_data,
            context=context
        )

        assert result1["action"] == RiskAction.ALLOW.value
        assert result2["action"] == RiskAction.ALLOW.value
        assert len(result3["triggered_rules"]) > 0
        assert result3["triggered_rules"][0]["name"] == "支付频率限制"

    def test_check_risk_amount_rule(self, risk_service: RiskControlService, sample_user):
        """测试金额限制规则"""
        # 创建金额限制规则
        rule_data = {
            "name": "大额支付限制",
            "rule_type": RuleType.AMOUNT.value,
            "conditions": {"event_types": ["payment"]},
            "risk_level": RiskLevel.HIGH.value,
            "action": RiskAction.REVIEW.value,
            "threshold_value": Decimal("1000.00"),
            "created_by": "admin"
        }
        risk_service.create_rule(rule_data)

        # 小额支付 - 应该通过
        small_event_data = {
            "order_id": 1,
            "amount": 500.0,
            "payment_method": "alipay"
        }

        result1 = risk_service.check_risk(
            event_type=EventType.PAYMENT.value,
            user_id=sample_user.id,
            event_data=small_event_data,
            context={}
        )

        # 大额支付 - 应该触发规则
        large_event_data = {
            "order_id": 2,
            "amount": 1500.0,
            "payment_method": "alipay"
        }

        result2 = risk_service.check_risk(
            event_type=EventType.PAYMENT.value,
            user_id=sample_user.id,
            event_data=large_event_data,
            context={}
        )

        assert result1["action"] == RiskAction.ALLOW.value
        assert len(result2["triggered_rules"]) > 0
        assert result2["triggered_rules"][0]["name"] == "大额支付限制"

    def test_get_risk_events(self, risk_service: RiskControlService, sample_user):
        """测试查询风险事件"""
        # 先创建一些风险事件
        event_data = {
            "order_id": 1,
            "amount": 100.0,
            "payment_method": "alipay"
        }

        risk_service.check_risk(
            event_type=EventType.PAYMENT.value,
            user_id=sample_user.id,
            event_data=event_data,
            context={}
        )

        # 查询事件
        events = risk_service.get_risk_events(
            user_id=sample_user.id,
            event_type=EventType.PAYMENT.value
        )

        assert len(events) > 0
        assert events[0].user_id == sample_user.id
        assert events[0].event_type == EventType.PAYMENT.value

    def test_process_risk_event(self, risk_service: RiskControlService, sample_user):
        """测试处理风险事件"""
        # 先创建风险事件
        event_data = {
            "order_id": 1,
            "amount": 100.0,
            "payment_method": "alipay"
        }

        result = risk_service.check_risk(
            event_type=EventType.PAYMENT.value,
            user_id=sample_user.id,
            event_data=event_data,
            context={}
        )

        event_id = result["event_id"]

        # 处理事件
        success = risk_service.process_risk_event(
            event_id=event_id,
            processed_by="admin",
            result="审核通过"
        )

        assert success is True

        # 验证事件状态
        events = risk_service.get_risk_events()
        processed_event = next((e for e in events if e.id == event_id), None)
        assert processed_event is not None
        assert processed_event.is_processed is True
        assert processed_event.processed_by == "admin"
        assert processed_event.process_result == "审核通过"

    def test_get_risk_statistics(self, risk_service: RiskControlService, sample_user):
        """测试风险统计"""
        # 创建一些风险事件
        for i in range(5):
            event_data = {
                "order_id": i + 1,
                "amount": 100.0 * (i + 1),
                "payment_method": "alipay"
            }

            risk_service.check_risk(
                event_type=EventType.PAYMENT.value,
                user_id=sample_user.id,
                event_data=event_data,
                context={}
            )

        # 获取统计
        start_date = datetime.utcnow() - timedelta(days=1)
        end_date = datetime.utcnow() + timedelta(days=1)

        stats = risk_service.get_risk_statistics(start_date, end_date)

        assert stats["total_events"] >= 5
        assert "block_rate" in stats
        assert "rule_hits" in stats


class TestPaymentRiskIntegration:
    """支付风控集成测试类"""

    @pytest.fixture
    def payment_service(self, db_session: Session):
        """创建支付服务实例"""
        return PaymentService(db_session)

    @pytest.fixture
    def sample_user(self, db_session: Session):
        """创建测试用户"""
        user = User(
            id="test_user_002",
            username="payuser",
            email="pay@example.com",
            phone="13800138001"
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def sample_order(self, db_session: Session, sample_user):
        """创建测试订单"""
        order = Order(
            id=2,
            user_id=sample_user.id,
            amount=Decimal("200.00"),
            status=OrderStatus.PENDING
        )
        db_session.add(order)
        db_session.commit()
        return order

    def test_payment_risk_check_allow(self, payment_service: PaymentService, sample_order, sample_user):
        """测试支付风控检查 - 允许通过"""
        context = {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0"
        }

        # 正常支付应该通过
        payment = payment_service.create_payment(
            order_id=sample_order.id,
            payment_method="alipay",
            user_id=sample_user.id,
            context=context
        )

        assert payment is not None
        assert payment.order_id == sample_order.id
        assert payment.amount == sample_order.amount

    def test_payment_risk_check_blocked(self, payment_service: PaymentService, sample_order, sample_user, db_session):
        """测试支付风控检查 - 被拦截"""
        # 先添加用户到黑名单
        from app.services.risk_control_service import get_risk_control_service
        risk_service = get_risk_control_service(db_session)

        blacklist_data = {
            "blacklist_type": BlacklistType.USER.value,
            "value": sample_user.id,
            "reason": "恶意用户",
            "risk_level": RiskLevel.CRITICAL.value,
            "created_by": "admin"
        }
        risk_service.add_to_blacklist(blacklist_data)

        context = {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0"
        }

        # 支付应该被拦截
        with pytest.raises(BusinessException) as exc_info:
            payment_service.create_payment(
                order_id=sample_order.id,
                payment_method="alipay",
                user_id=sample_user.id,
                context=context
            )

        assert exc_info.value.code == ErrorCode.RISK_CONTROL_BLOCKED

    @patch('app.services.risk_control_service.RiskControlService.check_risk')
    def test_payment_risk_check_review(self, mock_check_risk, payment_service: PaymentService, sample_order, sample_user):
        """测试支付风控检查 - 需要审核"""
        # 模拟风控返回需要审核
        mock_check_risk.return_value = {
            "risk_score": 60,
            "risk_level": RiskLevel.HIGH.value,
            "action": RiskAction.REVIEW.value,
            "triggered_rules": [{"name": "高风险规则"}],
            "blacklist_hits": [],
            "recommendations": ["建议人工审核"],
            "event_id": "test_event_001"
        }

        context = {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0"
        }

        # 支付应该创建待审核记录
        payment = payment_service.create_payment(
            order_id=sample_order.id,
            payment_method="alipay",
            user_id=sample_user.id,
            context=context
        )

        assert payment is not None
        assert payment.remark is not None  # 包含风险信息

        # 验证风险信息
        import json
        risk_info = json.loads(payment.remark)
        assert risk_info["risk_score"] == 60
        assert risk_info["risk_level"] == RiskLevel.HIGH.value

    @patch('app.services.risk_control_service.RiskControlService.check_risk')
    def test_payment_risk_check_delay(self, mock_check_risk, payment_service: PaymentService, sample_order, sample_user):
        """测试支付风控检查 - 延迟处理"""
        # 模拟风控返回延迟处理
        mock_check_risk.return_value = {
            "risk_score": 30,
            "risk_level": RiskLevel.MEDIUM.value,
            "action": RiskAction.DELAY.value,
            "triggered_rules": [],
            "blacklist_hits": [],
            "recommendations": ["延迟处理"],
            "event_id": "test_event_002"
        }

        context = {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0"
        }

        # 支付应该延迟后正常创建
        import time
        start_time = time.time()

        payment = payment_service.create_payment(
            order_id=sample_order.id,
            payment_method="alipay",
            user_id=sample_user.id,
            context=context
        )

        end_time = time.time()

        assert payment is not None
        assert (end_time - start_time) >= 2  # 验证确实延迟了

    @patch('app.services.risk_control_service.get_risk_control_service')
    def test_payment_risk_service_error(self, mock_get_service, payment_service: PaymentService, sample_order, sample_user):
        """测试风控服务异常处理"""
        # 模拟风控服务异常
        mock_service = Mock()
        mock_service.check_risk.side_effect = Exception("风控服务异常")
        mock_get_service.return_value = mock_service

        context = {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0"
        }

        # 风控服务异常时应该采用保守策略（审核）
        payment = payment_service.create_payment(
            order_id=sample_order.id,
            payment_method="alipay",
            user_id=sample_user.id,
            context=context
        )

        assert payment is not None
        # 验证包含错误信息
        import json
        risk_info = json.loads(payment.remark)
        assert "error" in risk_info


class TestRiskControlAPI:
    """风控API测试类"""

    def test_risk_check_endpoint(self, client, auth_headers):
        """测试风险检查接口"""
        request_data = {
            "event_type": "payment",
            "user_id": "test_user_001",
            "event_data": {
                "order_id": 1,
                "amount": 100.0,
                "payment_method": "alipay"
            },
            "context": {
                "ip_address": "192.168.1.1"
            }
        }

        response = client.post(
            "/api/v1/risk/check",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "risk_score" in data
        assert "risk_level" in data
        assert "action" in data
        assert "event_id" in data

    def test_create_rule_endpoint(self, client, auth_headers):
        """测试创建规则接口"""
        rule_data = {
            "name": "测试规则",
            "description": "测试用规则",
            "rule_type": "frequency",
            "conditions": {"event_types": ["payment"]},
            "risk_level": "medium",
            "action": "review",
            "time_window": 3600,
            "max_count": 5
        }

        response = client.post(
            "/api/v1/risk/rules",
            json=rule_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "规则创建成功"
        assert "rule" in data

    def test_add_blacklist_endpoint(self, client, auth_headers):
        """测试添加黑名单接口"""
        blacklist_data = {
            "blacklist_type": "ip",
            "value": "192.168.1.100",
            "reason": "测试黑名单",
            "risk_level": "high"
        }

        response = client.post(
            "/api/v1/risk/blacklist",
            json=blacklist_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "黑名单添加成功"
        assert "blacklist" in data

    def test_get_events_endpoint(self, client, auth_headers):
        """测试查询事件接口"""
        response = client.get(
            "/api/v1/risk/events",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "total" in data

    def test_get_statistics_endpoint(self, client, auth_headers):
        """测试统计接口"""
        response = client.get(
            "/api/v1/risk/statistics",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "statistics" in data
        assert "period" in data

    def test_get_enums_endpoint(self, client):
        """测试枚举值接口"""
        response = client.get("/api/v1/risk/enums")

        assert response.status_code == 200
        data = response.json()
        assert "risk_levels" in data
        assert "risk_actions" in data
        assert "rule_types" in data
        assert "event_types" in data
        assert "blacklist_types" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])