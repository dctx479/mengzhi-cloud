"""
SLA (Service Level Agreement) 模型

版本: 1.0
更新日期: 2026-01-22
"""

import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text,
    ForeignKey, Enum, JSON, Index, CheckConstraint
)
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import relationship

from .base import BaseModel, generate_uuid


class SLALevel(str, enum.Enum):
    """SLA等级"""
    BASIC = "BASIC"           # 基础版：99.0%
    STANDARD = "STANDARD"     # 标准版：99.5%
    PREMIUM = "PREMIUM"       # 高级版：99.9%
    ENTERPRISE = "ENTERPRISE" # 企业版：99.95%


class MetricType(str, enum.Enum):
    """指标类型"""
    AVAILABILITY = "AVAILABILITY"       # 可用性
    RESPONSE_TIME = "RESPONSE_TIME"     # 响应时间
    ERROR_RATE = "ERROR_RATE"           # 错误率
    THROUGHPUT = "THROUGHPUT"           # 吞吐量
    SUCCESS_RATE = "SUCCESS_RATE"       # 成功率


class ViolationSeverity(str, enum.Enum):
    """违约严重程度"""
    LOW = "LOW"           # 低：轻微超标
    MEDIUM = "MEDIUM"     # 中：明显超标
    HIGH = "HIGH"         # 高：严重超标
    CRITICAL = "CRITICAL" # 严重：系统故障


class SLAAgreement(BaseModel):
    """SLA协议表"""

    __tablename__ = "sla_agreements"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    agreement_uuid = Column(String(36), unique=True, nullable=False, default=generate_uuid, comment="协议UUID")

    # 关联信息 - 类型必须与 enterprises.id / users.id (BIGINT) 一致
    enterprise_id = Column(BIGINT, ForeignKey("enterprises.id"), nullable=True, comment="企业ID")
    user_id = Column(BIGINT, ForeignKey("users.id"), nullable=True, comment="用户ID")

    # 协议基本信息
    name = Column(String(200), nullable=False, comment="协议名称")
    level = Column(Enum(SLALevel), nullable=False, default=SLALevel.STANDARD, comment="SLA等级")
    description = Column(Text, nullable=True, comment="协议描述")

    # 协议期限
    start_date = Column(String(20), nullable=False, comment="开始日期")
    end_date = Column(String(20), nullable=False, comment="结束日期")

    # SLA指标定义
    availability_target = Column(Float, nullable=False, default=99.5, comment="可用性目标(%)")
    response_time_target = Column(Integer, nullable=False, default=2000, comment="响应时间目标(ms)")
    error_rate_target = Column(Float, nullable=False, default=0.1, comment="错误率目标(%)")
    throughput_target = Column(Integer, nullable=False, default=100, comment="吞吐量目标(req/s)")

    # 补偿条款
    compensation_enabled = Column(Boolean, nullable=False, default=True, comment="是否启用补偿")
    compensation_rules = Column(JSON, nullable=True, comment="补偿规则(JSON)")

    # 状态
    is_active = Column(Boolean, nullable=False, default=True, comment="是否激活")

    # 关系
    metrics = relationship("SLAMetric", back_populates="agreement", cascade="all, delete-orphan")
    violations = relationship("SLAViolation", back_populates="agreement", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        # enterprise_id 和 user_id 不能同时为 NULL（至少关联一个主体）
        CheckConstraint(
            "(enterprise_id IS NOT NULL) OR (user_id IS NOT NULL)",
            name="ck_sla_agreement_has_owner"
        ),
        Index("idx_agreement_enterprise", "enterprise_id"),
        Index("idx_agreement_user", "user_id"),
        Index("idx_agreement_level", "level"),
        Index("idx_agreement_active", "is_active"),
        Index("idx_agreement_dates", "start_date", "end_date"),
    )

    def __repr__(self):
        return f"<SLAAgreement(id={self.id}, name={self.name}, level={self.level})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "agreement_uuid": self.agreement_uuid,
            "enterprise_id": self.enterprise_id,
            "user_id": self.user_id,
            "name": self.name,
            "level": self.level.value if self.level else None,
            "description": self.description,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "availability_target": self.availability_target,
            "response_time_target": self.response_time_target,
            "error_rate_target": self.error_rate_target,
            "throughput_target": self.throughput_target,
            "compensation_enabled": self.compensation_enabled,
            "compensation_rules": self.compensation_rules,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SLAMetric(BaseModel):
    """SLA指标记录表"""

    __tablename__ = "sla_metrics"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    metric_uuid = Column(String(36), unique=True, nullable=False, default=generate_uuid, comment="指标UUID")

    # 关联协议
    agreement_id = Column(BIGINT, ForeignKey("sla_agreements.id"), nullable=False, comment="协议ID")

    # 指标信息
    metric_type = Column(Enum(MetricType), nullable=False, comment="指标类型")
    metric_name = Column(String(100), nullable=False, comment="指标名称")

    # 时间范围
    period_start = Column(String(30), nullable=False, comment="统计开始时间")
    period_end = Column(String(30), nullable=False, comment="统计结束时间")

    # 指标值
    target_value = Column(Float, nullable=False, comment="目标值")
    actual_value = Column(Float, nullable=False, comment="实际值")
    achievement_rate = Column(Float, nullable=False, comment="达成率(%)")

    # 统计数据
    total_requests = Column(Integer, nullable=False, default=0, comment="总请求数")
    successful_requests = Column(Integer, nullable=False, default=0, comment="成功请求数")
    failed_requests = Column(Integer, nullable=False, default=0, comment="失败请求数")

    # 响应时间统计
    avg_response_time = Column(Float, nullable=True, comment="平均响应时间(ms)")
    min_response_time = Column(Float, nullable=True, comment="最小响应时间(ms)")
    max_response_time = Column(Float, nullable=True, comment="最大响应时间(ms)")
    p50_response_time = Column(Float, nullable=True, comment="P50响应时间(ms)")
    p95_response_time = Column(Float, nullable=True, comment="P95响应时间(ms)")
    p99_response_time = Column(Float, nullable=True, comment="P99响应时间(ms)")

    # 是否达标
    is_compliant = Column(Boolean, nullable=False, default=True, comment="是否达标")

    # 备注
    notes = Column(Text, nullable=True, comment="备注")

    # 关系
    agreement = relationship("SLAAgreement", back_populates="metrics")

    # 索引
    __table_args__ = (
        Index("idx_metric_agreement", "agreement_id"),
        Index("idx_metric_type", "metric_type"),
        Index("idx_metric_period", "period_start", "period_end"),
        Index("idx_metric_compliant", "is_compliant"),
    )

    def __repr__(self):
        return f"<SLAMetric(id={self.id}, type={self.metric_type}, compliant={self.is_compliant})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "metric_uuid": self.metric_uuid,
            "agreement_id": self.agreement_id,
            "metric_type": self.metric_type.value if self.metric_type else None,
            "metric_name": self.metric_name,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "target_value": self.target_value,
            "actual_value": self.actual_value,
            "achievement_rate": self.achievement_rate,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "avg_response_time": self.avg_response_time,
            "min_response_time": self.min_response_time,
            "max_response_time": self.max_response_time,
            "p50_response_time": self.p50_response_time,
            "p95_response_time": self.p95_response_time,
            "p99_response_time": self.p99_response_time,
            "is_compliant": self.is_compliant,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SLAViolation(BaseModel):
    """SLA违约记录表"""

    __tablename__ = "sla_violations"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    violation_uuid = Column(String(36), unique=True, nullable=False, default=generate_uuid, comment="违约UUID")

    # 关联协议
    agreement_id = Column(BIGINT, ForeignKey("sla_agreements.id"), nullable=False, comment="协议ID")

    # 违约信息
    metric_type = Column(Enum(MetricType), nullable=False, comment="违约指标类型")
    severity = Column(Enum(ViolationSeverity), nullable=False, comment="严重程度")

    # 违约详情
    target_value = Column(Float, nullable=False, comment="目标值")
    actual_value = Column(Float, nullable=False, comment="实际值")
    deviation = Column(Float, nullable=False, comment="偏差值")
    deviation_rate = Column(Float, nullable=False, comment="偏差率(%)")

    # 时间信息
    violation_time = Column(String(30), nullable=False, comment="违约时间")
    duration = Column(Integer, nullable=True, comment="持续时间(秒)")

    # 影响范围
    affected_users = Column(Integer, nullable=False, default=0, comment="影响用户数")
    affected_requests = Column(Integer, nullable=False, default=0, comment="影响请求数")

    # 处理信息
    is_resolved = Column(Boolean, nullable=False, default=False, comment="是否已解决")
    resolved_at = Column(String(30), nullable=True, comment="解决时间")
    resolution_notes = Column(Text, nullable=True, comment="解决说明")

    # 补偿信息
    compensation_amount = Column(Float, nullable=True, comment="补偿金额")
    compensation_status = Column(String(20), nullable=True, comment="补偿状态")

    # 描述
    description = Column(Text, nullable=True, comment="违约描述")

    # 关系
    agreement = relationship("SLAAgreement", back_populates="violations")

    # 索引
    __table_args__ = (
        Index("idx_violation_agreement", "agreement_id"),
        Index("idx_violation_type", "metric_type"),
        Index("idx_violation_severity", "severity"),
        Index("idx_violation_time", "violation_time"),
        Index("idx_violation_resolved", "is_resolved"),
    )

    def __repr__(self):
        return f"<SLAViolation(id={self.id}, type={self.metric_type}, severity={self.severity})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "violation_uuid": self.violation_uuid,
            "agreement_id": self.agreement_id,
            "metric_type": self.metric_type.value if self.metric_type else None,
            "severity": self.severity.value if self.severity else None,
            "target_value": self.target_value,
            "actual_value": self.actual_value,
            "deviation": self.deviation,
            "deviation_rate": self.deviation_rate,
            "violation_time": self.violation_time,
            "duration": self.duration,
            "affected_users": self.affected_users,
            "affected_requests": self.affected_requests,
            "is_resolved": self.is_resolved,
            "resolved_at": self.resolved_at,
            "resolution_notes": self.resolution_notes,
            "compensation_amount": self.compensation_amount,
            "compensation_status": self.compensation_status,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PerformanceLog(BaseModel):
    """性能日志表 - 用于记录每个请求的性能数据"""

    __tablename__ = "performance_logs"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    log_uuid = Column(String(36), unique=True, nullable=False, default=generate_uuid, comment="日志UUID")

    # 请求信息
    request_id = Column(String(36), nullable=False, comment="请求ID")
    endpoint = Column(String(500), nullable=False, comment="请求端点")
    method = Column(String(10), nullable=False, comment="请求方法")

    # 用户信息
    user_id = Column(BIGINT, nullable=True, comment="用户ID")
    enterprise_id = Column(BIGINT, nullable=True, comment="企业ID")

    # 性能数据
    response_time = Column(Float, nullable=False, comment="响应时间(ms)")
    status_code = Column(Integer, nullable=False, comment="HTTP状态码")
    is_success = Column(Boolean, nullable=False, comment="是否成功")

    # 额外信息
    request_size = Column(Integer, nullable=True, comment="请求大小(bytes)")
    response_size = Column(Integer, nullable=True, comment="响应大小(bytes)")
    error_message = Column(Text, nullable=True, comment="错误信息")

    # 时间戳
    timestamp = Column(String(30), nullable=False, comment="时间戳")

    # 索引
    __table_args__ = (
        Index("idx_perflog_timestamp", "timestamp"),
        Index("idx_perflog_endpoint", "endpoint"),
        Index("idx_perflog_user", "user_id"),
        Index("idx_perflog_enterprise", "enterprise_id"),
        Index("idx_perflog_success", "is_success"),
        Index("idx_perflog_response_time", "response_time"),
    )

    def __repr__(self):
        return f"<PerformanceLog(id={self.id}, endpoint={self.endpoint}, response_time={self.response_time}ms)>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "log_uuid": self.log_uuid,
            "request_id": self.request_id,
            "endpoint": self.endpoint,
            "method": self.method,
            "user_id": self.user_id,
            "enterprise_id": self.enterprise_id,
            "response_time": self.response_time,
            "status_code": self.status_code,
            "is_success": self.is_success,
            "request_size": self.request_size,
            "response_size": self.response_size,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
        }
