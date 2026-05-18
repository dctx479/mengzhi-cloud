"""
计费系统数据模型 - SQLAlchemy ORM

包含：
- 计费方案（BillingPlan）
- 计费记录（BillingRecord）
- 账单（Invoice）

版本: 1.0
更新日期: 2026-01-22
"""

from sqlalchemy import (
    Column, BIGINT, VARCHAR, Enum, Integer, DECIMAL, TIMESTAMP, Boolean,
    Index, UniqueConstraint, Text, JSON, ForeignKey, DATE
)
from sqlalchemy.orm import relationship
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any, List
import enum

from .base import BaseModel, generate_uuid
from .payment import PaymentMethod


class BillingMode(enum.Enum):
    """计费模式枚举"""
    TOKEN = "token"  # 按Token计费
    MESSAGE = "message"  # 按消息数计费
    API_CALL = "api_call"  # 按API调用计费
    MONTHLY = "monthly"  # 包月套餐
    TIERED = "tiered"  # 阶梯定价


class PricingType(enum.Enum):
    """定价类型枚举"""
    FIXED = "fixed"  # 固定价格
    UNIT = "unit"  # 单价
    TIERED = "tiered"  # 阶梯价格


class InvoiceStatus(enum.Enum):
    """账单状态枚举"""
    PENDING = "pending"  # 待支付
    PAID = "paid"  # 已支付
    OVERDUE = "overdue"  # 已逾期
    CANCELLED = "cancelled"  # 已取消
    REFUNDED = "refunded"  # 已退款


class BillingPlan(BaseModel):
    """计费方案模型

    定义不同的计费方案，支持多种计费模式和定价规则。
    """

    __tablename__ = "billing_plans"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="计费方案ID"
    )

    # UUID标识
    plan_uuid = Column(
        VARCHAR(36),
        nullable=False,
        unique=True,
        index=True,
        default=generate_uuid,
        comment="方案UUID"
    )

    # 方案基本信息
    name = Column(
        VARCHAR(100),
        nullable=False,
        comment="方案名称"
    )
    description = Column(
        Text,
        nullable=True,
        comment="方案描述"
    )
    billing_mode = Column(
        Enum(BillingMode),
        nullable=False,
        default=BillingMode.TOKEN,
        index=True,
        comment="计费模式"
    )
    pricing_type = Column(
        Enum(PricingType),
        nullable=False,
        default=PricingType.UNIT,
        comment="定价类型"
    )

    # 定价规则（JSON格式存储灵活的定价配置）
    pricing_rules = Column(
        JSON,
        nullable=False,
        comment="定价规则配置"
    )
    # 示例：
    # TOKEN模式: {"unit_price": 0.001, "currency": "CNY"}
    # MESSAGE模式: {"unit_price": 0.1, "currency": "CNY"}
    # MONTHLY模式: {"monthly_fee": 99, "included_tokens": 100000, "currency": "CNY"}
    # TIERED模式: {
    #   "tiers": [
    #     {"min": 0, "max": 10000, "unit_price": 0.002},
    #     {"min": 10001, "max": 50000, "unit_price": 0.0015},
    #     {"min": 50001, "max": null, "unit_price": 0.001}
    #   ],
    #   "currency": "CNY"
    # }

    # 配额限制
    quota_limits = Column(
        JSON,
        nullable=True,
        comment="配额限制配置"
    )
    # 示例：
    # {
    #   "daily_tokens": 10000,
    #   "monthly_tokens": 300000,
    #   "daily_messages": 100,
    #   "monthly_messages": 3000,
    #   "daily_api_calls": 1000,
    #   "monthly_api_calls": 30000
    # }

    # 方案状态
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用"
    )
    is_default = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否为默认方案"
    )

    # 适用范围
    applicable_to = Column(
        VARCHAR(50),
        nullable=True,
        comment="适用对象：all/personal/enterprise"
    )

    # 有效期
    valid_from = Column(
        DATE,
        nullable=True,
        comment="生效日期"
    )
    valid_until = Column(
        DATE,
        nullable=True,
        comment="失效日期"
    )

    # 排序
    sort_order = Column(
        Integer,
        default=0,
        comment="排序顺序"
    )

    # 关系
    billing_records = relationship(
        "BillingRecord",
        back_populates="plan",
        cascade="all, delete-orphan"
    )

    # 索引定义
    __table_args__ = (
        UniqueConstraint("plan_uuid", name="uk_plan_uuid"),
        Index("idx_billing_mode", "billing_mode"),
        Index("idx_is_active", "is_active"),
        Index("idx_is_default", "is_default"),
        Index("idx_sort_order", "sort_order"),
    )

    def __repr__(self) -> str:
        return f"<BillingPlan(id={self.id}, name={self.name}, mode={self.billing_mode.value})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "plan_uuid": self.plan_uuid,
            "name": self.name,
            "description": self.description,
            "billing_mode": self.billing_mode.value if self.billing_mode else None,
            "pricing_type": self.pricing_type.value if self.pricing_type else None,
            "pricing_rules": self.pricing_rules,
            "quota_limits": self.quota_limits,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "applicable_to": self.applicable_to,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def calculate_cost(self, usage: Dict[str, Any]) -> float:
        """计算费用

        参数:
            usage: 使用量数据，如 {"tokens": 1000} 或 {"messages": 10}

        返回:
            float: 计算出的费用
        """
        if not self.pricing_rules:
            return 0.0

        if self.billing_mode == BillingMode.TOKEN:
            tokens = usage.get("tokens", 0)
            unit_price = self.pricing_rules.get("unit_price", 0)
            return tokens * unit_price

        elif self.billing_mode == BillingMode.MESSAGE:
            messages = usage.get("messages", 0)
            unit_price = self.pricing_rules.get("unit_price", 0)
            return messages * unit_price

        elif self.billing_mode == BillingMode.API_CALL:
            api_calls = usage.get("api_calls", 0)
            unit_price = self.pricing_rules.get("unit_price", 0)
            return api_calls * unit_price

        elif self.billing_mode == BillingMode.MONTHLY:
            return self.pricing_rules.get("monthly_fee", 0)

        elif self.billing_mode == BillingMode.TIERED:
            # 阶梯定价
            quantity = usage.get("tokens", 0) or usage.get("messages", 0) or usage.get("api_calls", 0)
            tiers = self.pricing_rules.get("tiers", [])

            total_cost = 0.0
            remaining = quantity

            for tier in sorted(tiers, key=lambda x: x["min"]):
                tier_min = tier["min"]
                tier_max = tier.get("max")
                unit_price = tier["unit_price"]

                if remaining <= 0:
                    break

                if tier_max is None:
                    # 最后一档，无上限
                    total_cost += remaining * unit_price
                    break
                else:
                    tier_quantity = min(remaining, tier_max - tier_min + 1)
                    total_cost += tier_quantity * unit_price
                    remaining -= tier_quantity

            return total_cost

        return 0.0

    def is_valid(self, check_date: date = None) -> bool:
        """检查方案是否有效

        参数:
            check_date: 检查日期，默认为今天

        返回:
            bool: 是否有效
        """
        if not self.is_active:
            return False

        if check_date is None:
            check_date = date.today()

        if self.valid_from and check_date < self.valid_from:
            return False

        if self.valid_until and check_date > self.valid_until:
            return False

        return True


class BillingRecord(BaseModel):
    """计费记录模型

    记录每次使用产生的计费信息。
    """

    __tablename__ = "billing_records"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="计费记录ID"
    )

    # UUID标识
    record_uuid = Column(
        VARCHAR(36),
        nullable=False,
        unique=True,
        index=True,
        default=generate_uuid,
        comment="记录UUID"
    )

    # 关联信息
    user_id = Column(
        BIGINT,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    plan_id = Column(
        BIGINT,
        ForeignKey("billing_plans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="计费方案ID"
    )

    # 计费信息
    billing_mode = Column(
        Enum(BillingMode),
        nullable=False,
        index=True,
        comment="计费模式"
    )

    # 使用量数据（JSON格式）
    usage_data = Column(
        JSON,
        nullable=False,
        comment="使用量数据"
    )
    # 示例：
    # {"tokens": 1000, "input_tokens": 800, "output_tokens": 200}
    # {"messages": 5}
    # {"api_calls": 10, "endpoint": "/api/chat"}

    # 费用信息
    unit_price = Column(
        DECIMAL(10, 6),
        nullable=False,
        comment="单价"
    )
    quantity = Column(
        Integer,
        nullable=False,
        comment="数量"
    )
    amount = Column(
        DECIMAL(10, 2),
        nullable=False,
        comment="金额"
    )
    currency = Column(
        VARCHAR(10),
        default="CNY",
        nullable=False,
        comment="货币单位"
    )

    # 关联资源
    resource_type = Column(
        VARCHAR(50),
        nullable=True,
        comment="资源类型：conversation/content_generation/api"
    )
    resource_id = Column(
        BIGINT,
        nullable=True,
        comment="资源ID"
    )

    # 计费周期
    billing_date = Column(
        DATE,
        nullable=False,
        index=True,
        comment="计费日期"
    )
    billing_month = Column(
        VARCHAR(7),
        nullable=False,
        index=True,
        comment="计费月份（YYYY-MM）"
    )

    # 账单关联
    invoice_id = Column(
        BIGINT,
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="所属账单ID"
    )

    # 备注
    notes = Column(
        Text,
        nullable=True,
        comment="备注信息"
    )

    # 关系
    user = relationship(
        "User",
        foreign_keys=[user_id],
        backref="billing_records"
    )
    plan = relationship(
        "BillingPlan",
        foreign_keys=[plan_id],
        back_populates="billing_records"
    )
    invoice = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
        back_populates="records"
    )

    # 索引定义
    __table_args__ = (
        UniqueConstraint("record_uuid", name="uk_record_uuid"),
        Index("idx_user_id", "user_id"),
        Index("idx_plan_id", "plan_id"),
        Index("idx_billing_mode", "billing_mode"),
        Index("idx_billing_date", "billing_date"),
        Index("idx_billing_month", "billing_month"),
        Index("idx_invoice_id", "invoice_id"),
        Index("idx_resource", "resource_type", "resource_id"),
    )

    def __repr__(self) -> str:
        return f"<BillingRecord(id={self.id}, user_id={self.user_id}, amount={self.amount})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "record_uuid": self.record_uuid,
            "user_id": self.user_id,
            "plan_id": self.plan_id,
            "billing_mode": self.billing_mode.value if self.billing_mode else None,
            "usage_data": self.usage_data,
            "unit_price": float(self.unit_price) if self.unit_price else 0,
            "quantity": self.quantity,
            "amount": float(self.amount) if self.amount else 0,
            "currency": self.currency,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "billing_date": self.billing_date.isoformat() if self.billing_date else None,
            "billing_month": self.billing_month,
            "invoice_id": self.invoice_id,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Invoice(BaseModel):
    """账单模型

    汇总一段时间内的计费记录，生成账单。
    """

    __tablename__ = "invoices"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="账单ID"
    )

    # UUID标识
    invoice_uuid = Column(
        VARCHAR(36),
        nullable=False,
        unique=True,
        index=True,
        default=generate_uuid,
        comment="账单UUID"
    )

    # 账单编号
    invoice_number = Column(
        VARCHAR(50),
        nullable=False,
        unique=True,
        index=True,
        comment="账单编号"
    )

    # 关联信息
    user_id = Column(
        BIGINT,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )

    # 账单周期
    billing_period_start = Column(
        DATE,
        nullable=False,
        comment="账单周期开始日期"
    )
    billing_period_end = Column(
        DATE,
        nullable=False,
        comment="账单周期结束日期"
    )

    # 金额信息
    subtotal = Column(
        DECIMAL(10, 2),
        nullable=False,
        default=0,
        comment="小计金额"
    )
    discount = Column(
        DECIMAL(10, 2),
        nullable=False,
        default=0,
        comment="折扣金额"
    )
    tax = Column(
        DECIMAL(10, 2),
        nullable=False,
        default=0,
        comment="税费"
    )
    total = Column(
        DECIMAL(10, 2),
        nullable=False,
        default=0,
        comment="总金额"
    )
    currency = Column(
        VARCHAR(10),
        default="CNY",
        nullable=False,
        comment="货币单位"
    )

    # 账单状态
    status = Column(
        Enum(InvoiceStatus),
        nullable=False,
        default=InvoiceStatus.PENDING,
        index=True,
        comment="账单状态"
    )

    # 支付信息
    payment_method = Column(
        Enum(PaymentMethod),
        nullable=True,
        comment="支付方式"
    )
    paid_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="支付时间"
    )
    payment_transaction_id = Column(
        VARCHAR(100),
        nullable=True,
        comment="支付交易ID"
    )

    # 到期日期
    due_date = Column(
        DATE,
        nullable=False,
        index=True,
        comment="到期日期"
    )

    # 统计信息（JSON格式）
    usage_summary = Column(
        JSON,
        nullable=True,
        comment="使用量汇总"
    )
    # 示例：
    # {
    #   "total_tokens": 50000,
    #   "total_messages": 200,
    #   "total_api_calls": 500,
    #   "by_mode": {
    #     "token": {"quantity": 50000, "amount": 50.00},
    #     "message": {"quantity": 200, "amount": 20.00}
    #   }
    # }

    # 备注
    notes = Column(
        Text,
        nullable=True,
        comment="备注信息"
    )

    # 关系
    user = relationship(
        "User",
        foreign_keys=[user_id],
        backref="invoices"
    )
    records = relationship(
        "BillingRecord",
        foreign_keys="BillingRecord.invoice_id",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )

    # 索引定义
    __table_args__ = (
        UniqueConstraint("invoice_uuid", name="uk_invoice_uuid"),
        UniqueConstraint("invoice_number", name="uk_invoice_number"),
        Index("idx_user_id", "user_id"),
        Index("idx_status", "status"),
        Index("idx_due_date", "due_date"),
        Index("idx_billing_period", "billing_period_start", "billing_period_end"),
    )

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, number={self.invoice_number}, total={self.total})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "invoice_uuid": self.invoice_uuid,
            "invoice_number": self.invoice_number,
            "user_id": self.user_id,
            "billing_period": {
                "start": self.billing_period_start.isoformat() if self.billing_period_start else None,
                "end": self.billing_period_end.isoformat() if self.billing_period_end else None,
            },
            "amounts": {
                "subtotal": float(self.subtotal) if self.subtotal else 0,
                "discount": float(self.discount) if self.discount else 0,
                "tax": float(self.tax) if self.tax else 0,
                "total": float(self.total) if self.total else 0,
                "currency": self.currency,
            },
            "status": self.status.value if self.status else None,
            "payment": {
                "method": self.payment_method.value if self.payment_method else None,
                "paid_at": self.paid_at.isoformat() if self.paid_at else None,
                "transaction_id": self.payment_transaction_id,
            },
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "usage_summary": self.usage_summary,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_overdue(self) -> bool:
        """检查账单是否逾期"""
        if self.status == InvoiceStatus.PAID:
            return False
        return date.today() > self.due_date

    def mark_as_paid(self, payment_method: PaymentMethod, transaction_id: str = None):
        """标记为已支付

        参数:
            payment_method: 支付方式
            transaction_id: 交易ID
        """
        self.status = InvoiceStatus.PAID
        self.payment_method = payment_method
        self.paid_at = datetime.utcnow()
        self.payment_transaction_id = transaction_id

    def calculate_totals(self):
        """计算账单总额"""
        self.subtotal = sum((record.amount or Decimal("0")) for record in self.records)
        self.total = self.subtotal - (self.discount or Decimal("0")) + (self.tax or Decimal("0"))

    @staticmethod
    def generate_invoice_number(user_id: int, period_start: date) -> str:
        """生成账单编号

        格式: INV-{YYYYMM}-{USER_ID}-{RANDOM}

        参数:
            user_id: 用户ID
            period_start: 账单周期开始日期

        返回:
            str: 账单编号
        """
        import random
        period_str = period_start.strftime("%Y%m")
        random_suffix = random.randint(1000, 9999)
        return f"INV-{period_str}-{user_id}-{random_suffix}"
