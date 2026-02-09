"""
测试 app/services/risk_control_service.py - 风控服务

覆盖风险检查、规则引擎、黑名单管理等核心功能
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.risk_control_service import RiskControlService
from app.models.risk_control import (
    RiskRule, RiskEvent, RiskBlacklist, RiskStatistics,
    RiskLevel, RiskAction, RuleType, EventType, BlacklistType
)


@pytest.fixture
def risk_service(db: Session):
    """创建风控服务实例"""
    return RiskControlService(db)


@pytest.fixture
def sample_user_id():
    """示例用户ID"""
    return "user_123"


@pytest.fixture
def sample_event_data():
    """示例事件数据"""
    return {
        "amount": "100.00",
        "phone": "13812345678",
        "email": "test@example.com"
    }


@pytest.fixture
def sample_context():
    """示例上下文信息"""
    return {
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0",
        "device_fingerprint": "device_123"
    }


class TestCheckRisk:
    """测试风险检查主流程"""

    def test_check_risk_low_risk(self, risk_service, sample_user_id, sample_event_data, sample_context):
        """测试低风险场景"""
        result = risk_service.check_risk(
            event_type=EventType.LOGIN.value,
            user_id=sample_user_id,
            event_data=sample_event_data,
            context=sample_context
        )

        assert result is not None
        assert "risk_score" in result
        assert "risk_level" in result
        assert "action" in result
        assert result["action"] == RiskAction.ALLOW.value

    def test_check_risk_returns_event_id(self, risk_service, sample_user_id, sample_event_data, sample_context):
        """测试返回事件ID"""
        result = risk_service.check_risk(
            event_type=EventType.LOGIN.value,
            user_id=sample_user_id,
            event_data=sample_event_data,
            context=sample_context
        )

        assert "event_id" in result
        assert result["event_id"] != ""

    def test_check_risk_with_recommendations(self, risk_service, sample_user_id, sample_event_data, sample_context):
        """测试生成建议"""
        result = risk_service.check_risk(
            event_type=EventType.LOGIN.value,
            user_id=sample_user_id,
            event_data=sample_event_data,
            context=sample_context
        )

        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)
        assert len(result["recommendations"]) > 0

    def test_check_risk_error_handling(self, risk_service):
        """测试错误处理"""
        # 传入无效数据触发异常
        result = risk_service.check_risk(
            event_type=None,
            user_id=None,
            event_data={},
            context=None
        )

        # 错误时应返回保守策略
        assert result["risk_level"] == RiskLevel.HIGH.value
        assert result["action"] == RiskAction.REVIEW.value
        assert "error" in result


class TestCheckBlacklist:
    """测试黑名单检查"""

    def test_check_blacklist_no_hits(self, risk_service, sample_user_id, sample_event_data, sample_context):
        """测试无黑名单命中"""
        result = risk_service._check_blacklist(sample_user_id, sample_event_data, sample_context)

        assert result["hits"] == []
        assert result["score"] == 0

    def test_check_blacklist_user_hit(self, risk_service, sample_user_id, sample_event_data, sample_context, db):
        """测试用户黑名单命中"""
        # 添加用户到黑名单
        blacklist = RiskBlacklist(
            blacklist_type=BlacklistType.USER.value,
            value=sample_user_id,
            risk_level=RiskLevel.HIGH.value,
            reason="测试黑名单",
            is_active=True
        )
        db.add(blacklist)
        db.commit()

        result = risk_service._check_blacklist(sample_user_id, sample_event_data, sample_context)

        assert len(result["hits"]) == 1
        assert result["hits"][0]["type"] == BlacklistType.USER.value
        assert result["score"] > 0

    def test_check_blacklist_ip_hit(self, risk_service, sample_user_id, sample_event_data, sample_context, db):
        """测试IP黑名单命中"""
        blacklist = RiskBlacklist(
            blacklist_type=BlacklistType.IP.value,
            value=sample_context["ip_address"],
            risk_level=RiskLevel.MEDIUM.value,
            reason="可疑IP",
            is_active=True
        )
        db.add(blacklist)
        db.commit()

        result = risk_service._check_blacklist(sample_user_id, sample_event_data, sample_context)

        assert len(result["hits"]) == 1
        assert result["hits"][0]["type"] == BlacklistType.IP.value

    def test_check_blacklist_multiple_hits(self, risk_service, sample_user_id, sample_event_data, sample_context, db):
        """测试多个黑名单命中"""
        # 添加用户和IP到黑名单
        blacklists = [
            RiskBlacklist(
                blacklist_type=BlacklistType.USER.value,
                value=sample_user_id,
                risk_level=RiskLevel.HIGH.value,
                reason="用户黑名单",
                is_active=True
            ),
            RiskBlacklist(
                blacklist_type=BlacklistType.IP.value,
                value=sample_context["ip_address"],
                risk_level=RiskLevel.MEDIUM.value,
                reason="IP黑名单",
                is_active=True
            )
        ]
        for bl in blacklists:
            db.add(bl)
        db.commit()

        result = risk_service._check_blacklist(sample_user_id, sample_event_data, sample_context)

        assert len(result["hits"]) == 2
        assert result["score"] > 0

    def test_check_blacklist_expired(self, risk_service, sample_user_id, sample_event_data, sample_context, db):
        """测试过期黑名单不命中"""
        blacklist = RiskBlacklist(
            blacklist_type=BlacklistType.USER.value,
            value=sample_user_id,
            risk_level=RiskLevel.HIGH.value,
            reason="已过期",
            is_active=True,
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        db.add(blacklist)
        db.commit()

        result = risk_service._check_blacklist(sample_user_id, sample_event_data, sample_context)

        assert len(result["hits"]) == 0

    def test_check_blacklist_inactive(self, risk_service, sample_user_id, sample_event_data, sample_context, db):
        """测试未激活黑名单不命中"""
        blacklist = RiskBlacklist(
            blacklist_type=BlacklistType.USER.value,
            value=sample_user_id,
            risk_level=RiskLevel.HIGH.value,
            reason="未激活",
            is_active=False
        )
        db.add(blacklist)
        db.commit()

        result = risk_service._check_blacklist(sample_user_id, sample_event_data, sample_context)

        assert len(result["hits"]) == 0


class TestCheckRules:
    """测试规则引擎"""

    def test_check_rules_no_rules(self, risk_service, sample_user_id, sample_event_data, sample_context):
        """测试无规则时"""
        result = risk_service._check_rules(
            EventType.LOGIN.value,
            sample_user_id,
            sample_event_data,
            sample_context
        )

        assert result["triggered"] == []
        assert result["score"] == 0

    def test_check_rules_frequency_rule(self, risk_service, sample_user_id, sample_event_data, sample_context, db):
        """测试频率限制规则"""
        # 创建频率规则
        rule = RiskRule(
            name="登录频率限制",
            rule_type=RuleType.FREQUENCY.value,
            risk_level=RiskLevel.MEDIUM.value,
            action=RiskAction.DELAY.value,
            conditions={"event_types": [EventType.LOGIN.value]},
            time_window=3600,
            max_count=3,
            is_active=True,
            priority=1
        )
        db.add(rule)
        db.commit()

        # 创建多个历史事件
        for i in range(4):
            event = RiskEvent(
                event_type=EventType.LOGIN.value,
                user_id=sample_user_id,
                event_data={},
                risk_score=0,
                risk_level=RiskLevel.LOW.value,
                final_action=RiskAction.ALLOW.value,
                created_at=datetime.utcnow() - timedelta(minutes=i * 10)
            )
            db.add(event)
        db.commit()

        result = risk_service._check_rules(
            EventType.LOGIN.value,
            sample_user_id,
            sample_event_data,
            sample_context
        )

        assert len(result["triggered"]) > 0
        assert result["score"] > 0

    def test_check_rules_amount_rule(self, risk_service, sample_user_id, sample_context, db):
        """测试金额限制规则"""
        rule = RiskRule(
            name="大额交易限制",
            rule_type=RuleType.AMOUNT.value,
            risk_level=RiskLevel.HIGH.value,
            action=RiskAction.REVIEW.value,
            conditions={"event_types": [EventType.PAYMENT.value]},
            threshold_value=Decimal("1000.00"),
            is_active=True,
            priority=1
        )
        db.add(rule)
        db.commit()

        # 测试超过阈值的金额
        event_data = {"amount": "1500.00"}
        result = risk_service._check_rules(
            EventType.PAYMENT.value,
            sample_user_id,
            event_data,
            sample_context
        )

        assert len(result["triggered"]) > 0


class TestCalculateRiskLevel:
    """测试风险等级计算"""

    def test_calculate_risk_level_low(self, risk_service):
        """测试低风险"""
        level = risk_service._calculate_risk_level(10)
        assert level == RiskLevel.LOW.value

    def test_calculate_risk_level_medium(self, risk_service):
        """测试中风险"""
        level = risk_service._calculate_risk_level(30)
        assert level == RiskLevel.MEDIUM.value

    def test_calculate_risk_level_high(self, risk_service):
        """测试高风险"""
        level = risk_service._calculate_risk_level(60)
        assert level == RiskLevel.HIGH.value

    def test_calculate_risk_level_critical(self, risk_service):
        """测试严重风险"""
        level = risk_service._calculate_risk_level(90)
        assert level == RiskLevel.CRITICAL.value


class TestDetermineAction:
    """测试处理动作确定"""

    def test_determine_action_blacklist_block(self, risk_service):
        """测试黑名单触发拦截"""
        blacklist_hits = [{"risk_level": RiskLevel.CRITICAL.value}]
        action = risk_service._determine_action(RiskLevel.LOW.value, [], blacklist_hits)
        assert action == RiskAction.BLOCK.value

    def test_determine_action_rule_block(self, risk_service):
        """测试规则触发拦截"""
        triggered_rules = [{"action": RiskAction.BLOCK.value}]
        action = risk_service._determine_action(RiskLevel.LOW.value, triggered_rules, [])
        assert action == RiskAction.BLOCK.value

    def test_determine_action_by_risk_level(self, risk_service):
        """测试根据风险等级确定动作"""
        # 严重风险 -> 拦截
        action = risk_service._determine_action(RiskLevel.CRITICAL.value, [], [])
        assert action == RiskAction.BLOCK.value

        # 高风险 -> 审核
        action = risk_service._determine_action(RiskLevel.HIGH.value, [], [])
        assert action == RiskAction.REVIEW.value

        # 中风险 -> 延迟
        action = risk_service._determine_action(RiskLevel.MEDIUM.value, [], [])
        assert action == RiskAction.DELAY.value

        # 低风险 -> 允许
        action = risk_service._determine_action(RiskLevel.LOW.value, [], [])
        assert action == RiskAction.ALLOW.value


class TestRuleManagement:
    """测试规则管理"""

    def test_create_rule(self, risk_service, db):
        """测试创建规则"""
        rule_data = {
            "name": "测试规则",
            "rule_type": RuleType.FREQUENCY.value,
            "risk_level": RiskLevel.MEDIUM.value,
            "action": RiskAction.DELAY.value,
            "conditions": {},
            "is_active": True,
            "priority": 1
        }

        rule = risk_service.create_rule(rule_data)

        assert rule is not None
        assert rule.name == "测试规则"
        assert rule.id is not None

    def test_update_rule(self, risk_service, db):
        """测试更新规则"""
        # 先创建规则
        rule = RiskRule(
            name="原规则",
            rule_type=RuleType.FREQUENCY.value,
            risk_level=RiskLevel.LOW.value,
            action=RiskAction.ALLOW.value,
            conditions={},
            is_active=True,
            priority=1
        )
        db.add(rule)
        db.commit()

        # 更新规则
        updated = risk_service.update_rule(rule.id, {"name": "新规则", "risk_level": RiskLevel.HIGH.value})

        assert updated is not None
        assert updated.name == "新规则"
        assert updated.risk_level == RiskLevel.HIGH.value

    def test_update_rule_not_found(self, risk_service):
        """测试更新不存在的规则"""
        result = risk_service.update_rule("nonexistent", {"name": "test"})
        assert result is None

    def test_delete_rule(self, risk_service, db):
        """测试删除规则"""
        rule = RiskRule(
            name="待删除规则",
            rule_type=RuleType.FREQUENCY.value,
            risk_level=RiskLevel.LOW.value,
            action=RiskAction.ALLOW.value,
            conditions={},
            is_active=True,
            priority=1
        )
        db.add(rule)
        db.commit()
        rule_id = rule.id

        result = risk_service.delete_rule(rule_id)
        assert result is True

        # 验证已删除
        deleted_rule = db.query(RiskRule).filter(RiskRule.id == rule_id).first()
        assert deleted_rule is None

    def test_delete_rule_not_found(self, risk_service):
        """测试删除不存在的规则"""
        result = risk_service.delete_rule("nonexistent")
        assert result is False

    def test_get_rules(self, risk_service, db):
        """测试获取规则列表"""
        # 创建多个规则
        for i in range(5):
            rule = RiskRule(
                name=f"规则{i}",
                rule_type=RuleType.FREQUENCY.value,
                risk_level=RiskLevel.LOW.value,
                action=RiskAction.ALLOW.value,
                conditions={},
                is_active=True,
                priority=i
            )
            db.add(rule)
        db.commit()

        rules = risk_service.get_rules(skip=0, limit=10)
        assert len(rules) >= 5


class TestBlacklistManagement:
    """测试黑名单管理"""

    def test_add_to_blacklist(self, risk_service, db):
        """测试添加黑名单"""
        blacklist_data = {
            "blacklist_type": BlacklistType.USER.value,
            "value": "user_456",
            "risk_level": RiskLevel.HIGH.value,
            "reason": "测试黑名单",
            "is_active": True
        }

        blacklist = risk_service.add_to_blacklist(blacklist_data)

        assert blacklist is not None
        assert blacklist.value == "user_456"
        assert blacklist.id is not None

    def test_remove_from_blacklist(self, risk_service, db):
        """测试移除黑名单"""
        blacklist = RiskBlacklist(
            blacklist_type=BlacklistType.USER.value,
            value="user_789",
            risk_level=RiskLevel.HIGH.value,
            reason="待移除",
            is_active=True
        )
        db.add(blacklist)
        db.commit()
        blacklist_id = blacklist.id

        result = risk_service.remove_from_blacklist(blacklist_id)
        assert result is True

        # 验证已删除
        deleted = db.query(RiskBlacklist).filter(RiskBlacklist.id == blacklist_id).first()
        assert deleted is None

    def test_remove_from_blacklist_not_found(self, risk_service):
        """测试移除不存在的黑名单"""
        result = risk_service.remove_from_blacklist("nonexistent")
        assert result is False

    def test_get_blacklist(self, risk_service, db):
        """测试获取黑名单列表"""
        # 创建多个黑名单项
        for i in range(3):
            blacklist = RiskBlacklist(
                blacklist_type=BlacklistType.USER.value,
                value=f"user_{i}",
                risk_level=RiskLevel.MEDIUM.value,
                reason=f"测试{i}",
                is_active=True
            )
            db.add(blacklist)
        db.commit()

        blacklist_items = risk_service.get_blacklist(skip=0, limit=10)
        assert len(blacklist_items) >= 3


class TestRiskEventQueries:
    """测试风险事件查询"""

    def test_get_risk_events_all(self, risk_service, db):
        """测试获取所有事件"""
        # 创建测试事件
        for i in range(3):
            event = RiskEvent(
                event_type=EventType.LOGIN.value,
                user_id=f"user_{i}",
                event_data={},
                risk_score=10,
                risk_level=RiskLevel.LOW.value,
                final_action=RiskAction.ALLOW.value
            )
            db.add(event)
        db.commit()

        events = risk_service.get_risk_events(skip=0, limit=10)
        assert len(events) >= 3

    def test_get_risk_events_by_user(self, risk_service, db):
        """测试按用户查询事件"""
        user_id = "specific_user"
        event = RiskEvent(
            event_type=EventType.LOGIN.value,
            user_id=user_id,
            event_data={},
            risk_score=10,
            risk_level=RiskLevel.LOW.value,
            final_action=RiskAction.ALLOW.value
        )
        db.add(event)
        db.commit()

        events = risk_service.get_risk_events(user_id=user_id)
        assert len(events) > 0
        assert all(e.user_id == user_id for e in events)

    def test_get_risk_events_by_risk_level(self, risk_service, db):
        """测试按风险等级查询事件"""
        event = RiskEvent(
            event_type=EventType.LOGIN.value,
            user_id="user_test",
            event_data={},
            risk_score=60,
            risk_level=RiskLevel.HIGH.value,
            final_action=RiskAction.REVIEW.value
        )
        db.add(event)
        db.commit()

        events = risk_service.get_risk_events(risk_level=RiskLevel.HIGH.value)
        assert len(events) > 0
        assert all(e.risk_level == RiskLevel.HIGH.value for e in events)

    def test_process_risk_event(self, risk_service, db):
        """测试处理风险事件"""
        event = RiskEvent(
            event_type=EventType.LOGIN.value,
            user_id="user_test",
            event_data={},
            risk_score=60,
            risk_level=RiskLevel.HIGH.value,
            final_action=RiskAction.REVIEW.value,
            is_processed=False
        )
        db.add(event)
        db.commit()
        event_id = event.id

        result = risk_service.process_risk_event(event_id, "admin", "已审核通过")
        assert result is True

        # 验证已处理
        processed_event = db.query(RiskEvent).filter(RiskEvent.id == event_id).first()
        assert processed_event.is_processed is True
        assert processed_event.processed_by == "admin"
        assert processed_event.process_result == "已审核通过"


class TestRiskStatistics:
    """测试风险统计"""

    def test_get_risk_statistics(self, risk_service, db):
        """测试获取风险统计"""
        start_date = datetime.utcnow() - timedelta(days=1)
        end_date = datetime.utcnow()

        # 创建测试事件
        events_data = [
            (RiskLevel.LOW.value, RiskAction.ALLOW.value),
            (RiskLevel.HIGH.value, RiskAction.REVIEW.value),
            (RiskLevel.CRITICAL.value, RiskAction.BLOCK.value),
        ]

        for risk_level, action in events_data:
            event = RiskEvent(
                event_type=EventType.LOGIN.value,
                user_id="user_test",
                event_data={},
                risk_score=50,
                risk_level=risk_level,
                final_action=action
            )
            db.add(event)
        db.commit()

        stats = risk_service.get_risk_statistics(start_date, end_date)

        assert stats is not None
        assert "total_events" in stats
        assert "high_risk_events" in stats
        assert "blocked_events" in stats
        assert "block_rate" in stats
        assert stats["total_events"] >= 3
