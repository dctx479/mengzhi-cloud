"""
AI媒体生成模型
"""

import enum
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import BIGINT, JSON, Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, TEXT, VARCHAR, Enum
from sqlalchemy.orm import relationship

from .base import BaseModel, generate_uuid


def enum_values(enum_cls):
    return [item.value for item in enum_cls]


class MediaProviderType(enum.Enum):
    IMAGE = "image"
    VIDEO = "video"


class MediaProviderCode(enum.Enum):
    TONGYI_WANXIANG = "tongyi_wanxiang"
    WENXIN_YIGE = "wenxin_yige"
    SPARK_DRAWING = "spark_drawing"
    JIANYING = "jianying"
    TENCENT_ZHIYING = "tencent_zhiying"


class MediaTaskStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class MediaProvider(BaseModel):
    """AI媒体生成服务商配置"""

    __tablename__ = "media_providers"

    id = Column(BIGINT, primary_key=True, autoincrement=True, comment="服务商ID")
    provider_uuid = Column(
        VARCHAR(36), nullable=False, unique=True, index=True, default=generate_uuid, comment="服务商UUID"
    )
    provider_code = Column(VARCHAR(50), nullable=False, comment="服务商代码")
    provider_name = Column(VARCHAR(100), nullable=False, comment="服务商名称")
    provider_type = Column(
        Enum(MediaProviderType, values_callable=enum_values), nullable=False, index=True, comment="服务商类型"
    )
    api_key_encrypted = Column(TEXT, nullable=False, comment="加密的API密钥")
    app_id = Column(VARCHAR(100), nullable=True, comment="应用ID")
    api_endpoint = Column(VARCHAR(500), nullable=True, comment="API地址")
    default_model = Column(VARCHAR(100), nullable=True, comment="默认模型")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    is_primary = Column(Boolean, default=False, nullable=False, comment="是否主服务商")
    priority = Column(Integer, default=0, nullable=False, comment="优先级")
    cost_per_unit = Column(Float, default=0.0, nullable=False, comment="单次生成成本")
    rate_limit_per_minute = Column(Integer, default=60, nullable=False, comment="每分钟限流")
    config = Column(JSON, nullable=True, comment="扩展配置")
    health_status = Column(VARCHAR(20), default="healthy", nullable=False, comment="健康状态")
    last_check_time = Column(DateTime, nullable=True, comment="最后健康检查时间")
    error_count = Column(Integer, default=0, nullable=False, comment="连续错误计数")
    last_error_message = Column(TEXT, nullable=True, comment="最后错误信息")
    last_error_time = Column(DateTime, nullable=True, comment="最后错误时间")

    tasks = relationship("MediaGenerationTask", back_populates="provider")
    costs = relationship("MediaGenerationCost", back_populates="provider")

    __table_args__ = (
        Index("idx_media_provider_code", "provider_code"),
        Index("idx_media_provider_type_active", "provider_type", "is_active", "priority"),
        Index("idx_media_provider_primary", "provider_type", "is_primary", "is_active"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "provider_uuid": self.provider_uuid,
            "provider_code": self.provider_code,
            "provider_name": self.provider_name,
            "provider_type": self.provider_type.value if self.provider_type else None,
            "app_id": self.app_id,
            "api_endpoint": self.api_endpoint,
            "default_model": self.default_model,
            "is_active": self.is_active,
            "is_primary": self.is_primary,
            "priority": self.priority,
            "cost_per_unit": self.cost_per_unit,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "config": self.config,
            "health_status": self.health_status,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "error_count": self.error_count,
            "last_error_message": self.last_error_message,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def record_success(self) -> None:
        self.error_count = 0
        self.health_status = "healthy"
        self.last_check_time = datetime.now(timezone.utc)

    def record_failure(self, error_message: str) -> None:
        self.error_count += 1
        self.last_error_message = error_message[:1000]
        self.last_error_time = datetime.now(timezone.utc)
        self.last_check_time = datetime.now(timezone.utc)
        self.health_status = "unhealthy" if self.error_count >= 3 else "degraded"


class MediaGenerationTask(BaseModel):
    """AI媒体生成任务"""

    __tablename__ = "media_generation_tasks"

    id = Column(BIGINT, primary_key=True, autoincrement=True, comment="任务ID")
    task_uuid = Column(VARCHAR(36), nullable=False, unique=True, index=True, default=generate_uuid, comment="任务UUID")
    user_id = Column(BIGINT, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    enterprise_id = Column(
        BIGINT, ForeignKey("enterprises.id", ondelete="SET NULL"), nullable=True, index=True, comment="企业ID"
    )
    provider_id = Column(
        BIGINT, ForeignKey("media_providers.id", ondelete="SET NULL"), nullable=True, index=True, comment="服务商ID"
    )
    media_type = Column(
        Enum(MediaProviderType, values_callable=enum_values), nullable=False, index=True, comment="媒体类型"
    )
    status = Column(
        Enum(MediaTaskStatus, values_callable=enum_values),
        nullable=False,
        default=MediaTaskStatus.PENDING,
        index=True,
        comment="任务状态",
    )
    prompt = Column(TEXT, nullable=False, comment="生成提示词")
    negative_prompt = Column(TEXT, nullable=True, comment="反向提示词")
    model = Column(VARCHAR(100), nullable=True, comment="模型名称")
    width = Column(Integer, nullable=True, comment="宽度")
    height = Column(Integer, nullable=True, comment="高度")
    duration = Column(Integer, nullable=True, comment="视频时长秒")
    result_count = Column(Integer, default=1, nullable=False, comment="结果数量")
    provider_task_id = Column(VARCHAR(255), nullable=True, index=True, comment="第三方任务ID")
    request_params = Column(JSON, nullable=True, comment="请求参数")
    error_message = Column(TEXT, nullable=True, comment="错误信息")
    cost_amount = Column(Float, default=0.0, nullable=False, comment="成本金额")
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    user = relationship("User")
    enterprise = relationship("Enterprise")
    provider = relationship("MediaProvider", back_populates="tasks")
    results = relationship("MediaGenerationResult", back_populates="task", cascade="all, delete-orphan")
    costs = relationship("MediaGenerationCost", back_populates="task")

    __table_args__ = (
        Index("idx_media_task_user_status", "user_id", "status", "created_at"),
        Index("idx_media_task_enterprise_status", "enterprise_id", "status", "created_at"),
        Index("idx_media_task_provider_status", "provider_id", "status"),
        Index("idx_media_task_type_status", "media_type", "status"),
    )

    def to_dict(self, include_results: bool = True) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "task_uuid": self.task_uuid,
            "user_id": self.user_id,
            "enterprise_id": self.enterprise_id,
            "provider_id": self.provider_id,
            "provider": self.provider.to_dict() if self.provider else None,
            "media_type": self.media_type.value if self.media_type else None,
            "status": self.status.value if self.status else None,
            "prompt": self.prompt,
            "negative_prompt": self.negative_prompt,
            "model": self.model,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "result_count": self.result_count,
            "provider_task_id": self.provider_task_id,
            "request_params": self.request_params,
            "error_message": self.error_message,
            "cost_amount": self.cost_amount,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_results:
            data["results"] = [result.to_dict() for result in self.results]
        return data


class MediaGenerationResult(BaseModel):
    """AI媒体生成结果"""

    __tablename__ = "media_generation_results"

    id = Column(BIGINT, primary_key=True, autoincrement=True, comment="结果ID")
    result_uuid = Column(
        VARCHAR(36), nullable=False, unique=True, index=True, default=generate_uuid, comment="结果UUID"
    )
    task_id = Column(
        BIGINT,
        ForeignKey("media_generation_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="任务ID",
    )
    media_id = Column(
        BIGINT, ForeignKey("media.id", ondelete="SET NULL"), nullable=True, index=True, comment="媒体素材ID"
    )
    file_url = Column(VARCHAR(1000), nullable=False, comment="文件URL")
    thumbnail_url = Column(VARCHAR(1000), nullable=True, comment="缩略图URL")
    file_size = Column(BIGINT, nullable=True, comment="文件大小")
    width = Column(Integer, nullable=True, comment="宽度")
    height = Column(Integer, nullable=True, comment="高度")
    duration = Column(Integer, nullable=True, comment="视频时长秒")
    metadata_json = Column(JSON, nullable=True, comment="结果元数据")

    task = relationship("MediaGenerationTask", back_populates="results")
    media = relationship("Media")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "result_uuid": self.result_uuid,
            "task_id": self.task_id,
            "media_id": self.media_id,
            "file_url": self.file_url,
            "thumbnail_url": self.thumbnail_url,
            "file_size": self.file_size,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "metadata": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class MediaGenerationCost(BaseModel):
    """AI媒体生成成本记录"""

    __tablename__ = "media_generation_costs"

    id = Column(BIGINT, primary_key=True, autoincrement=True, comment="成本ID")
    task_id = Column(
        BIGINT,
        ForeignKey("media_generation_tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="任务ID",
    )
    provider_id = Column(
        BIGINT, ForeignKey("media_providers.id", ondelete="SET NULL"), nullable=True, index=True, comment="服务商ID"
    )
    user_id = Column(BIGINT, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="用户ID")
    enterprise_id = Column(
        BIGINT, ForeignKey("enterprises.id", ondelete="SET NULL"), nullable=True, index=True, comment="企业ID"
    )
    media_type = Column(
        Enum(MediaProviderType, values_callable=enum_values), nullable=False, index=True, comment="媒体类型"
    )
    unit_count = Column(Integer, default=1, nullable=False, comment="计费单位数")
    unit_price = Column(Float, default=0.0, nullable=False, comment="单价")
    total_amount = Column(Float, default=0.0, nullable=False, comment="总金额")
    billing_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True, comment="计费时间")

    task = relationship("MediaGenerationTask", back_populates="costs")
    provider = relationship("MediaProvider", back_populates="costs")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "provider_id": self.provider_id,
            "provider_name": self.provider.provider_name if self.provider else None,
            "user_id": self.user_id,
            "enterprise_id": self.enterprise_id,
            "media_type": self.media_type.value if self.media_type else None,
            "unit_count": self.unit_count,
            "unit_price": self.unit_price,
            "total_amount": self.total_amount,
            "billing_date": self.billing_date.isoformat() if self.billing_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
