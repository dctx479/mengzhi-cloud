"""
租户AI配置模型
"""
from sqlalchemy import Column, BIGINT, VARCHAR, TEXT, Boolean, ForeignKey, Index, Integer, Float, DateTime
from sqlalchemy.orm import relationship
from typing import Dict, Any
from datetime import datetime
import enum

from .base import BaseModel


class HealthStatus(enum.Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"  # 健康
    DEGRADED = "degraded"  # 降级
    UNHEALTHY = "unhealthy"  # 不健康


class TenantAIConfig(BaseModel):
    """租户AI配置模型

    每个租户可以配置自己的AI服务商和API密钥
    支持故障转移和健康检查
    """

    __tablename__ = "tenant_ai_configs"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="配置ID"
    )

    # 租户关联
    enterprise_id = Column(
        BIGINT,
        ForeignKey("enterprises.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属企业ID"
    )

    # Provider配置
    provider = Column(
        VARCHAR(50),
        nullable=False,
        comment="AI服务商: deepseek, openai, qwen"
    )

    api_key_encrypted = Column(
        TEXT,
        nullable=False,
        comment="加密的API密钥"
    )

    base_url = Column(
        VARCHAR(255),
        nullable=True,
        comment="自定义API地址"
    )

    default_model = Column(
        VARCHAR(100),
        nullable=True,
        comment="默认模型"
    )

    # 状态
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用"
    )

    # 故障转移字段
    priority = Column(
        Integer,
        default=0,
        nullable=False,
        comment="优先级(0-100,数值越大优先级越高)"
    )

    health_status = Column(
        VARCHAR(20),
        default=HealthStatus.HEALTHY.value,
        nullable=False,
        comment="健康状态: healthy, degraded, unhealthy"
    )

    last_check_time = Column(
        DateTime,
        nullable=True,
        comment="最后健康检查时间"
    )

    error_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="连续错误计数"
    )

    total_requests = Column(
        BIGINT,
        default=0,
        nullable=False,
        comment="总请求数"
    )

    failed_requests = Column(
        BIGINT,
        default=0,
        nullable=False,
        comment="失败请求数"
    )

    avg_response_time = Column(
        Float,
        nullable=True,
        comment="平均响应时间(毫秒)"
    )

    last_error_message = Column(
        TEXT,
        nullable=True,
        comment="最后错误信息"
    )

    last_error_time = Column(
        DateTime,
        nullable=True,
        comment="最后错误时间"
    )

    circuit_breaker_open_until = Column(
        DateTime,
        nullable=True,
        comment="熔断器开启截止时间"
    )

    # 关系
    enterprise = relationship(
        "Enterprise",
        back_populates="ai_configs"
    )

    # 索引
    __table_args__ = (
        Index("idx_enterprise_provider", "enterprise_id", "provider", unique=True),
        Index("idx_is_active", "is_active"),
        Index("idx_health_status", "health_status"),
        Index("idx_priority", "priority"),
        Index("idx_enterprise_priority", "enterprise_id", "priority", "health_status"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（不包含敏感信息）"""
        return {
            "id": self.id,
            "enterprise_id": self.enterprise_id,
            "provider": self.provider,
            "base_url": self.base_url,
            "default_model": self.default_model,
            "is_active": self.is_active,
            "priority": self.priority,
            "health_status": self.health_status,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "error_count": self.error_count,
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "avg_response_time": self.avg_response_time,
            "error_rate": self.get_error_rate(),
            "is_circuit_breaker_open": self.is_circuit_breaker_open(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_healthy(self) -> bool:
        """检查是否健康"""
        return self.health_status == HealthStatus.HEALTHY.value and self.is_active

    def is_circuit_breaker_open(self) -> bool:
        """检查熔断器是否开启"""
        if not self.circuit_breaker_open_until:
            return False
        return datetime.utcnow() < self.circuit_breaker_open_until

    def get_error_rate(self) -> float:
        """获取错误率"""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100

    def record_success(self, response_time: float):
        """记录成功请求"""
        self.total_requests += 1
        self.error_count = 0

        # 更新平均响应时间
        if self.avg_response_time is None:
            self.avg_response_time = response_time
        else:
            # 使用指数移动平均
            self.avg_response_time = 0.9 * self.avg_response_time + 0.1 * response_time

    def record_failure(self, error_message: str):
        """记录失败请求"""
        self.total_requests += 1
        self.failed_requests += 1
        self.error_count += 1
        self.last_error_message = error_message[:1000]  # 限制长度
        self.last_error_time = datetime.utcnow()

    def update_health_status(self):
        """更新健康状态"""
        error_rate = self.get_error_rate()

        if self.error_count >= 5 or error_rate > 50:
            self.health_status = HealthStatus.UNHEALTHY.value
        elif self.error_count >= 3 or error_rate > 20:
            self.health_status = HealthStatus.DEGRADED.value
        else:
            self.health_status = HealthStatus.HEALTHY.value

        self.last_check_time = datetime.utcnow()

    def open_circuit_breaker(self, duration_seconds: int = 60):
        """开启熔断器"""
        from datetime import timedelta
        self.circuit_breaker_open_until = datetime.utcnow() + timedelta(seconds=duration_seconds)
        self.health_status = HealthStatus.UNHEALTHY.value

    def close_circuit_breaker(self):
        """关闭熔断器"""
        self.circuit_breaker_open_until = None
        self.error_count = 0
        self.health_status = HealthStatus.HEALTHY.value
