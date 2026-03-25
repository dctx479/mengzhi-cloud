"""
风控系统数据模型

包含风控规则、风险事件、黑名单等核心模型，用于支付风控和业务风险防范。

版本: 1.0
更新日期: 2026-01-23
"""

import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, Text, Boolean, DateTime,
    Numeric, ForeignKey, Index, JSON
)
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import relationship
from .base import BaseModel, generate_uuid


class RiskLevel(enum.Enum):
    """风险等级枚举"""
    LOW = "low"          # 低风险
    MEDIUM = "medium"    # 中风险
    HIGH = "high"        # 高风险
    CRITICAL = "critical"  # 严重风险


class RiskAction(enum.Enum):
    """风险处理动作枚举"""
    ALLOW = "allow"          # 允许通过
    REVIEW = "review"        # 人工审核
    BLOCK = "block"          # 直接拦截
    DELAY = "delay"          # 延迟处理


class RuleType(enum.Enum):
    """规则类型枚举"""
    FREQUENCY = "frequency"      # 频率限制
    AMOUNT = "amount"           # 金额限制
    BEHAVIOR = "behavior"       # 行为分析
    BLACKLIST = "blacklist"     # 黑名单检查
    DEVICE = "device"           # 设备指纹
    LOCATION = "location"       # 地理位置
    TIME = "time"              # 时间限制


class EventType(enum.Enum):
    """事件类型枚举"""
    PAYMENT = "payment"         # 支付事件
    LOGIN = "login"            # 登录事件
    REGISTER = "register"      # 注册事件
    TRANSFER = "transfer"      # 转账事件
    WITHDRAW = "withdraw"      # 提现事件


class BlacklistType(enum.Enum):
    """黑名单类型枚举"""
    USER = "user"              # 用户黑名单
    IP = "ip"                  # IP黑名单
    DEVICE = "device"          # 设备黑名单
    PHONE = "phone"            # 手机号黑名单
    EMAIL = "email"            # 邮箱黑名单
    CARD = "card"              # 银行卡黑名单


class RiskRule(BaseModel):
    """风控规则模型"""

    __tablename__ = "risk_rules"

    id = Column(BIGINT, primary_key=True, autoincrement=True, comment="规则ID")
    name = Column(String(100), nullable=False, comment="规则名称")
    description = Column(Text, comment="规则描述")
    rule_type = Column(String(20), nullable=False, comment="规则类型")

    # 规则配置
    conditions = Column(JSON, nullable=False, comment="规则条件配置")
    risk_level = Column(String(20), nullable=False, comment="风险等级")
    action = Column(String(20), nullable=False, comment="处理动作")

    # 规则参数
    threshold_value = Column(Numeric(15, 2), comment="阈值")
    time_window = Column(Integer, comment="时间窗口(秒)")
    max_count = Column(Integer, comment="最大次数")

    # 状态控制
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    priority = Column(Integer, default=100, nullable=False, comment="优先级(数字越小优先级越高)")

    # 统计信息
    hit_count = Column(Integer, default=0, nullable=False, comment="命中次数")
    last_hit_at = Column(DateTime, comment="最后命中时间")

    # 创建者信息
    created_by = Column(String(36), comment="创建者ID")

    def __repr__(self):
        return f"<RiskRule(id={self.id}, name={self.name}, type={self.rule_type})>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "rule_type": self.rule_type,
            "conditions": self.conditions,
            "risk_level": self.risk_level,
            "action": self.action,
            "threshold_value": float(self.threshold_value) if self.threshold_value else None,
            "time_window": self.time_window,
            "max_count": self.max_count,
            "is_active": self.is_active,
            "priority": self.priority,
            "hit_count": self.hit_count,
            "last_hit_at": self.last_hit_at.isoformat() if self.last_hit_at else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class RiskEvent(BaseModel):
    """风险事件模型"""

    __tablename__ = "risk_events"

    id = Column(BIGINT, primary_key=True, autoincrement=True, comment="事件ID")
    event_type = Column(String(20), nullable=False, comment="事件类型")

    # 关联信息
    user_id = Column(BIGINT, ForeignKey("users.id"), nullable=True, comment="用户ID")
    order_id = Column(BIGINT, ForeignKey("orders.id"), nullable=True, comment="订单ID")
    payment_id = Column(BIGINT, ForeignKey("payments.id"), nullable=True, comment="支付ID")

    # 事件详情
    event_data = Column(JSON, nullable=False, comment="事件数据")
    risk_score = Column(Integer, default=0, nullable=False, comment="风险评分")
    risk_level = Column(String(20), nullable=False, comment="风险等级")

    # 触发的规则
    triggered_rules = Column(JSON, comment="触发的规则列表")
    final_action = Column(String(20), nullable=False, comment="最终处理动作")

    # 处理状态
    is_processed = Column(Boolean, default=False, nullable=False, comment="是否已处理")
    processed_at = Column(DateTime, comment="处理时间")
    processed_by = Column(String(36), comment="处理人ID")
    process_result = Column(Text, comment="处理结果")

    # 环境信息
    ip_address = Column(String(45), comment="IP地址")
    user_agent = Column(Text, comment="用户代理")
    device_fingerprint = Column(String(100), comment="设备指纹")
    location = Column(JSON, comment="地理位置信息")

    def __repr__(self):
        return f"<RiskEvent(id={self.id}, type={self.event_type}, risk_level={self.risk_level})>"

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "order_id": self.order_id,
            "payment_id": self.payment_id,
            "event_data": self.event_data,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "triggered_rules": self.triggered_rules,
            "final_action": self.final_action,
            "is_processed": self.is_processed,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "processed_by": self.processed_by,
            "process_result": self.process_result,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "device_fingerprint": self.device_fingerprint,
            "location": self.location,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class RiskBlacklist(BaseModel):
    """风险黑名单模型"""

    __tablename__ = "risk_blacklist"

    id = Column(BIGINT, primary_key=True, autoincrement=True, comment="黑名单ID")
    blacklist_type = Column(String(20), nullable=False, comment="黑名单类型")
    value = Column(String(200), nullable=False, comment="黑名单值")

    # 黑名单信息
    reason = Column(Text, comment="加入黑名单原因")
    risk_level = Column(String(20), nullable=False, comment="风险等级")

    # 状态控制
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    expires_at = Column(DateTime, comment="过期时间")

    # 统计信息
    hit_count = Column(Integer, default=0, nullable=False, comment="命中次数")
    last_hit_at = Column(DateTime, comment="最后命中时间")

    # 创建者信息
    created_by = Column(String(36), comment="创建者ID")

    # 索引
    __table_args__ = (
        Index('idx_blacklist_type_value', 'blacklist_type', 'value'),
        Index('idx_blacklist_active', 'is_active'),
        Index('idx_blacklist_expires', 'expires_at'),
    )

    def __repr__(self):
        return f"<RiskBlacklist(id={self.id}, type={self.blacklist_type}, value={self.value})>"

    def to_dict(self):
        return {
            "id": self.id,
            "blacklist_type": self.blacklist_type,
            "value": self.value,
            "reason": self.reason,
            "risk_level": self.risk_level,
            "is_active": self.is_active,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "hit_count": self.hit_count,
            "last_hit_at": self.last_hit_at.isoformat() if self.last_hit_at else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def is_expired(self) -> bool:
        """检查是否已过期"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class RiskStatistics(BaseModel):
    """风险统计模型"""

    __tablename__ = "risk_statistics"

    id = Column(BIGINT, primary_key=True, autoincrement=True, comment="统计ID")
    date = Column(DateTime, nullable=False, comment="统计日期")

    # 事件统计
    total_events = Column(Integer, default=0, nullable=False, comment="总事件数")
    high_risk_events = Column(Integer, default=0, nullable=False, comment="高风险事件数")
    blocked_events = Column(Integer, default=0, nullable=False, comment="拦截事件数")

    # 规则统计
    rule_hits = Column(JSON, comment="规则命中统计")

    # 黑名单统计
    blacklist_hits = Column(Integer, default=0, nullable=False, comment="黑名单命中数")

    # 处理统计
    auto_processed = Column(Integer, default=0, nullable=False, comment="自动处理数")
    manual_processed = Column(Integer, default=0, nullable=False, comment="人工处理数")

    def __repr__(self):
        return f"<RiskStatistics(date={self.date}, total_events={self.total_events})>"

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "total_events": self.total_events,
            "high_risk_events": self.high_risk_events,
            "blocked_events": self.blocked_events,
            "rule_hits": self.rule_hits,
            "blacklist_hits": self.blacklist_hits,
            "auto_processed": self.auto_processed,
            "manual_processed": self.manual_processed,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }