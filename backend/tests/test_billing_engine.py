"""
测试 app/services/billing_engine.py - 计费引擎服务

覆盖使用量记录、账单生成、统计分析等核心功能
"""
import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.billing_engine import BillingEngine
from app.models.billing import (
    BillingPlan, BillingRecord, Invoice,
    BillingMode, InvoiceStatus, PaymentMethod
)
from app.models.user import User


@pytest.fixture
def billing_engine(db: Session):
    """创建计费引擎实例"""
    return BillingEngine(db)


@pytest.fixture
def sample_user(db: Session):
    """创建示例用户"""
    user = User(
        username="test_billing_user",
        email="billing@example.com",
        hashed_password="hashed_pwd"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def token_plan(db: Session):
    """创建Token计费方案"""
    plan = BillingPlan(
        name="Token计费方案",
        billing_mode=BillingMode.TOKEN,
        pricing_rules={
            "unit_price": 0.01,
            "currency": "CNY"
        },
        is_default=True,
        is_active=True
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@pytest.fixture
def tiered_plan(db: Session):
    """创建阶梯计费方案"""
    plan = BillingPlan(
        name="阶梯计费方案",
        billing_mode=BillingMode.TIERED,
        pricing_rules={
            "tiers": [
                {"min": 0, "max": 1000, "unit_price": 0.01},
                {"min": 1001, "max": 5000, "unit_price": 0.008},
                {"min": 5001, "max": None, "unit_price": 0.005}
            ],
            "currency": "CNY"
        },
        is_active=True
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@pytest.fixture
def monthly_plan(db: Session):
    """创建包月计费方案"""
    plan = BillingPlan(
        name="包月计费方案",
        billing_mode=BillingMode.MONTHLY,
        pricing_rules={
            "monthly_fee": 99.0,
            "currency": "CNY"
        },
        is_active=True
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


class TestGetUserPlan:
    """测试获取用户计费方案"""

    def test_get_user_plan_default(self, billing_engine, sample_user, token_plan):
        """测试获取默认计费方案"""
        plan = billing_engine.get_user_plan(sample_user.id)
        assert plan is not None
        assert plan.is_default is True
        assert plan.name == "Token计费方案"

    def test_get_user_plan_no_plan(self, billing_engine, sample_user, db):
        """测试没有计费方案时"""
        # 删除所有计费方案
        db.query(BillingPlan).delete()
        db.commit()

        plan = billing_engine.get_user_plan(sample_user.id)
        assert plan is None


class TestRecordUsage:
    """测试记录使用量并计费"""

    def test_record_usage_token_mode(self, billing_engine, sample_user, token_plan):
        """测试Token计费模式"""
        usage_data = {"tokens": 1000}
        record = billing_engine.record_usage(
            user_id=sample_user.id,
            billing_mode=BillingMode.TOKEN,
            usage_data=usage_data,
            resource_type="chat",
            resource_id=1
        )

        assert record is not None
        assert record.user_id == sample_user.id
        assert record.billing_mode == BillingMode.TOKEN
        assert record.quantity == 1000
        assert record.unit_price == Decimal("0.01")
        assert record.amount == Decimal("10.00")
        assert record.currency == "CNY"

    def test_record_usage_message_mode(self, billing_engine, sample_user, db):
        """测试消息计费模式"""
        # 创建消息计费方案
        plan = BillingPlan(
            name="消息计费",
            billing_mode=BillingMode.MESSAGE,
            pricing_rules={"unit_price": 0.5, "currency": "CNY"},
            is_default=True,
            is_active=True
        )
        db.add(plan)
        db.commit()

        usage_data = {"messages": 10}
        record = billing_engine.record_usage(
            user_id=sample_user.id,
            billing_mode=BillingMode.MESSAGE,
            usage_data=usage_data
        )

        assert record.quantity == 10
        assert record.amount == Decimal("5.00")

    def test_record_usage_api_call_mode(self, billing_engine, sample_user, db):
        """测试API调用计费模式"""
        plan = BillingPlan(
            name="API计费",
            billing_mode=BillingMode.API_CALL,
            pricing_rules={"unit_price": 1.0, "currency": "CNY"},
            is_default=True,
            is_active=True
        )
        db.add(plan)
        db.commit()

        usage_data = {"api_calls": 50}
        record = billing_engine.record_usage(
            user_id=sample_user.id,
            billing_mode=BillingMode.API_CALL,
            usage_data=usage_data
        )

        assert record.quantity == 50
        assert record.amount == Decimal("50.00")

    def test_record_usage_monthly_mode(self, billing_engine, sample_user, monthly_plan):
        """测试包月计费模式"""
        usage_data = {}
        record = billing_engine.record_usage(
            user_id=sample_user.id,
            billing_mode=BillingMode.MONTHLY,
            usage_data=usage_data
        )

        assert record.quantity == 1
        assert record.amount == Decimal("99.00")

    def test_record_usage_tiered_mode_tier1(self, billing_engine, sample_user, tiered_plan, db):
        """测试阶梯计费 - 第一档"""
        # 设置为默认方案
        db.query(BillingPlan).update({BillingPlan.is_default: False})
        tiered_plan.is_default = True
        db.commit()

        usage_data = {"tokens": 500}
        record = billing_engine.record_usage(
            user_id=sample_user.id,
            billing_mode=BillingMode.TIERED,
            usage_data=usage_data
        )

        assert record.quantity == 500
        assert record.unit_price == Decimal("0.01")
        assert record.amount == Decimal("5.00")

    def test_record_usage_tiered_mode_tier2(self, billing_engine, sample_user, tiered_plan, db):
        """测试阶梯计费 - 第二档"""
        db.query(BillingPlan).update({BillingPlan.is_default: False})
        tiered_plan.is_default = True
        db.commit()

        usage_data = {"tokens": 3000}
        record = billing_engine.record_usage(
            user_id=sample_user.id,
            billing_mode=BillingMode.TIERED,
            usage_data=usage_data
        )

        assert record.quantity == 3000
        assert record.unit_price == Decimal("0.008")
        assert record.amount == Decimal("24.00")

    def test_record_usage_tiered_mode_tier3(self, billing_engine, sample_user, tiered_plan, db):
        """测试阶梯计费 - 第三档"""
        db.query(BillingPlan).update({BillingPlan.is_default: False})
        tiered_plan.is_default = True
        db.commit()

        usage_data = {"tokens": 10000}
        record = billing_engine.record_usage(
            user_id=sample_user.id,
            billing_mode=BillingMode.TIERED,
            usage_data=usage_data
        )

        assert record.quantity == 10000
        assert record.unit_price == Decimal("0.005")
        assert record.amount == Decimal("50.00")

    def test_record_usage_with_notes(self, billing_engine, sample_user, token_plan):
        """测试记录使用量时添加备注"""
        usage_data = {"tokens": 100}
        record = billing_engine.record_usage(
            user_id=sample_user.id,
            billing_mode=BillingMode.TOKEN,
            usage_data=usage_data,
            notes="测试备注"
        )

        assert record.notes == "测试备注"

    def test_record_usage_no_plan(self, billing_engine, sample_user, db):
        """测试没有计费方案时抛出异常"""
        # 删除所有计费方案
        db.query(BillingPlan).delete()
        db.commit()

        with pytest.raises(ValueError, match="No billing plan found"):
            billing_engine.record_usage(
                user_id=sample_user.id,
                billing_mode=BillingMode.TOKEN,
                usage_data={"tokens": 100}
            )


class TestExtractQuantity:
    """测试提取数量"""

    def test_extract_quantity_token(self, billing_engine):
        """测试提取Token数量"""
        quantity = billing_engine._extract_quantity(BillingMode.TOKEN, {"tokens": 1000})
        assert quantity == 1000

    def test_extract_quantity_message(self, billing_engine):
        """测试提取消息数量"""
        quantity = billing_engine._extract_quantity(BillingMode.MESSAGE, {"messages": 50})
        assert quantity == 50

    def test_extract_quantity_api_call(self, billing_engine):
        """测试提取API调用数量"""
        quantity = billing_engine._extract_quantity(BillingMode.API_CALL, {"api_calls": 100})
        assert quantity == 100

    def test_extract_quantity_monthly(self, billing_engine):
        """测试包月模式数量"""
        quantity = billing_engine._extract_quantity(BillingMode.MONTHLY, {})
        assert quantity == 1

    def test_extract_quantity_tiered_with_tokens(self, billing_engine):
        """测试阶梯模式提取Token数量"""
        quantity = billing_engine._extract_quantity(BillingMode.TIERED, {"tokens": 5000})
        assert quantity == 5000

    def test_extract_quantity_tiered_with_messages(self, billing_engine):
        """测试阶梯模式提取消息数量"""
        quantity = billing_engine._extract_quantity(BillingMode.TIERED, {"messages": 200})
        assert quantity == 200

    def test_extract_quantity_empty_data(self, billing_engine):
        """测试空数据"""
        quantity = billing_engine._extract_quantity(BillingMode.TOKEN, {})
        assert quantity == 0


class TestCalculateUnitPrice:
    """测试计算单价"""

    def test_calculate_unit_price_token_plan(self, billing_engine, token_plan):
        """测试Token计费方案单价"""
        unit_price = billing_engine._calculate_unit_price(token_plan, 1000)
        assert unit_price == 0.01

    def test_calculate_unit_price_monthly_plan(self, billing_engine, monthly_plan):
        """测试包月计费方案单价"""
        unit_price = billing_engine._calculate_unit_price(monthly_plan, 1)
        assert unit_price == 99.0

    def test_calculate_unit_price_tiered_tier1(self, billing_engine, tiered_plan):
        """测试阶梯定价第一档"""
        unit_price = billing_engine._calculate_unit_price(tiered_plan, 500)
        assert unit_price == 0.01

    def test_calculate_unit_price_tiered_tier2(self, billing_engine, tiered_plan):
        """测试阶梯定价第二档"""
        unit_price = billing_engine._calculate_unit_price(tiered_plan, 3000)
        assert unit_price == 0.008

    def test_calculate_unit_price_tiered_tier3(self, billing_engine, tiered_plan):
        """测试阶梯定价第三档"""
        unit_price = billing_engine._calculate_unit_price(tiered_plan, 10000)
        assert unit_price == 0.005


class TestGenerateInvoice:
    """测试生成账单"""

    def test_generate_invoice_basic(self, billing_engine, sample_user, token_plan, db):
        """测试基本账单生成"""
        # 创建一些计费记录
        today = date.today()
        for i in range(3):
            record = BillingRecord(
                user_id=sample_user.id,
                plan_id=token_plan.id,
                billing_mode=BillingMode.TOKEN,
                usage_data={"tokens": 1000},
                unit_price=Decimal("0.01"),
                quantity=1000,
                amount=Decimal("10.00"),
                currency="CNY",
                billing_date=today - timedelta(days=i),
                billing_month=today.strftime("%Y-%m")
            )
            db.add(record)
        db.commit()

        # 生成账单
        period_start = today - timedelta(days=7)
        period_end = today
        invoice = billing_engine.generate_invoice(sample_user.id, period_start, period_end)

        assert invoice is not None
        assert invoice.user_id == sample_user.id
        assert invoice.status == InvoiceStatus.PENDING
        assert invoice.total_amount == Decimal("30.00")
        assert len(invoice.billing_records) == 3

    def test_generate_invoice_no_records(self, billing_engine, sample_user):
        """测试没有计费记录时抛出异常"""
        today = date.today()
        period_start = today - timedelta(days=7)
        period_end = today

        with pytest.raises(ValueError, match="No billing records found"):
            billing_engine.generate_invoice(sample_user.id, period_start, period_end)

    def test_generate_invoice_custom_due_days(self, billing_engine, sample_user, token_plan, db):
        """测试自定义到期天数"""
        # 创建计费记录
        today = date.today()
        record = BillingRecord(
            user_id=sample_user.id,
            plan_id=token_plan.id,
            billing_mode=BillingMode.TOKEN,
            usage_data={"tokens": 500},
            unit_price=Decimal("0.01"),
            quantity=500,
            amount=Decimal("5.00"),
            currency="CNY",
            billing_date=today,
            billing_month=today.strftime("%Y-%m")
        )
        db.add(record)
        db.commit()

        # 生成账单，指定30天到期
        period_start = today - timedelta(days=1)
        period_end = today
        invoice = billing_engine.generate_invoice(sample_user.id, period_start, period_end, due_days=30)

        expected_due_date = today + timedelta(days=30)
        assert invoice.due_date == expected_due_date

    def test_generate_invoice_excludes_invoiced_records(self, billing_engine, sample_user, token_plan, db):
        """测试生成账单时排除已关联账单的记录"""
        # 创建一些计费记录，其中一些已关联账单
        today = date.today()

        # 未关联账单的记录
        for i in range(2):
            record = BillingRecord(
                user_id=sample_user.id,
                plan_id=token_plan.id,
                billing_mode=BillingMode.TOKEN,
                usage_data={"tokens": 100},
                unit_price=Decimal("0.01"),
                quantity=100,
                amount=Decimal("1.00"),
                currency="CNY",
                billing_date=today,
                billing_month=today.strftime("%Y-%m"),
                invoice_id=None
            )
            db.add(record)

        # 已关联账单的记录
        record_with_invoice = BillingRecord(
            user_id=sample_user.id,
            plan_id=token_plan.id,
            billing_mode=BillingMode.TOKEN,
            usage_data={"tokens": 100},
            unit_price=Decimal("0.01"),
            quantity=100,
            amount=Decimal("1.00"),
            currency="CNY",
            billing_date=today,
            billing_month=today.strftime("%Y-%m"),
            invoice_id="existing_invoice_id"
        )
        db.add(record_with_invoice)
        db.commit()

        # 生成账单
        period_start = today - timedelta(days=1)
        period_end = today
        invoice = billing_engine.generate_invoice(sample_user.id, period_start, period_end)

        # 应该只包含未关联账单的2条记录
        assert len(invoice.billing_records) == 2
        assert invoice.total_amount == Decimal("2.00")


class TestGetBillingRecords:
    """测试查询计费记录"""

    def test_get_billing_records_all(self, billing_engine, sample_user, token_plan, db):
        """测试获取所有计费记录"""
        # 创建测试记录
        today = date.today()
        for i in range(5):
            record = BillingRecord(
                user_id=sample_user.id,
                plan_id=token_plan.id,
                billing_mode=BillingMode.TOKEN,
                usage_data={"tokens": 100},
                unit_price=Decimal("0.01"),
                quantity=100,
                amount=Decimal("1.00"),
                currency="CNY",
                billing_date=today - timedelta(days=i),
                billing_month=today.strftime("%Y-%m")
            )
            db.add(record)
        db.commit()

        records = billing_engine.get_billing_records(sample_user.id)
        assert len(records) >= 5

    def test_get_billing_records_by_date_range(self, billing_engine, sample_user, token_plan, db):
        """测试按日期范围查询计费记录"""
        today = date.today()
        for i in range(10):
            record = BillingRecord(
                user_id=sample_user.id,
                plan_id=token_plan.id,
                billing_mode=BillingMode.TOKEN,
                usage_data={"tokens": 100},
                unit_price=Decimal("0.01"),
                quantity=100,
                amount=Decimal("1.00"),
                currency="CNY",
                billing_date=today - timedelta(days=i),
                billing_month=today.strftime("%Y-%m")
            )
            db.add(record)
        db.commit()

        # 查询最近3天的记录
        start_date = today - timedelta(days=2)
        end_date = today
        records = billing_engine.get_billing_records(
            sample_user.id,
            start_date=start_date,
            end_date=end_date
        )

        assert len(records) == 3


class TestGetUserStatistics:
    """测试用户统计"""

    def test_get_user_statistics(self, billing_engine, sample_user, token_plan, db):
        """测试获取用户统计信息"""
        # 创建测试数据
        today = date.today()
        for i in range(5):
            record = BillingRecord(
                user_id=sample_user.id,
                plan_id=token_plan.id,
                billing_mode=BillingMode.TOKEN,
                usage_data={"tokens": 1000},
                unit_price=Decimal("0.01"),
                quantity=1000,
                amount=Decimal("10.00"),
                currency="CNY",
                billing_date=today - timedelta(days=i),
                billing_month=today.strftime("%Y-%m")
            )
            db.add(record)
        db.commit()

        stats = billing_engine.get_user_statistics(
            sample_user.id,
            start_date=today - timedelta(days=7),
            end_date=today
        )

        assert stats is not None
        assert "total_amount" in stats
        assert "total_records" in stats
        assert "total_tokens" in stats or "total_quantity" in stats
        assert stats["total_amount"] == Decimal("50.00")
        assert stats["total_records"] == 5
