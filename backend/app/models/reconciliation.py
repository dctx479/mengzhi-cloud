"""
对账数据模型 - SQLAlchemy ORM

版本: 1.0
创建日期: 2026-01-23
"""

from sqlalchemy import (
    Column, BIGINT, String, DECIMAL, Enum, TIMESTAMP, Boolean,
    ForeignKey, Index, Text, Integer
)
from sqlalchemy.orm import relationship
from datetime import datetime, date
from typing import Dict, Any, Optional, List
import enum
import json

from .base import BaseModel, generate_uuid


class ReconciliationStatus(enum.Enum):
    """对账状态枚举"""
    PENDING = "pending"  # 待对账
    PROCESSING = "processing"  # 对账中
    SUCCESS = "success"  # 对账成功
    FAILED = "failed"  # 对账失败
    PARTIAL = "partial"  # 部分成功(有差异)


class ReconciliationType(enum.Enum):
    """对账类型枚举"""
    DAILY = "daily"  # 日对账
    MANUAL = "manual"  # 手动对账
    RETRY = "retry"  # 重试对账


class DifferenceType(enum.Enum):
    """差异类型枚举"""
    MISSING_LOCAL = "missing_local"  # 本地缺失(第三方有,本地无)
    MISSING_REMOTE = "missing_remote"  # 远程缺失(本地有,第三方无)
    AMOUNT_MISMATCH = "amount_mismatch"  # 金额不匹配
    STATUS_MISMATCH = "status_mismatch"  # 状态不匹配
    TIME_MISMATCH = "time_mismatch"  # 时间不匹配


class DifferenceStatus(enum.Enum):
    """差异处理状态枚举"""
    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    RESOLVED = "resolved"  # 已解决
    IGNORED = "ignored"  # 已忽略
    FAILED = "failed"  # 处理失败


class ReconciliationRecord(BaseModel):
    """对账记录模型

    记录每次对账的基本信息:
    - 对账时间范围和类型
    - 对账结果统计
    - 差异汇总信息
    """

    __tablename__ = "reconciliation_records"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="对账记录ID"
    )

    # 对账批次号(唯一)
    batch_no = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        default=generate_uuid,
        comment="对账批次号"
    )

    # 对账信息
    reconciliation_date = Column(
        String(10),  # YYYY-MM-DD
        nullable=False,
        index=True,
        comment="对账日期"
    )

    reconciliation_type = Column(
        Enum(ReconciliationType),
        nullable=False,
        default=ReconciliationType.DAILY,
        comment="对账类型"
    )

    status = Column(
        Enum(ReconciliationStatus),
        nullable=False,
        default=ReconciliationStatus.PENDING,
        index=True,
        comment="对账状态"
    )

    # 对账范围
    start_time = Column(
        TIMESTAMP,
        nullable=False,
        comment="对账开始时间"
    )

    end_time = Column(
        TIMESTAMP,
        nullable=False,
        comment="对账结束时间"
    )

    # 统计信息
    total_local_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="本地交易总数"
    )

    total_remote_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="第三方交易总数"
    )

    matched_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="匹配成功数量"
    )

    difference_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="差异数量"
    )

    # 金额统计
    total_local_amount = Column(
        DECIMAL(15, 2),
        nullable=False,
        default=0,
        comment="本地交易总金额"
    )

    total_remote_amount = Column(
        DECIMAL(15, 2),
        nullable=False,
        default=0,
        comment="第三方交易总金额"
    )

    matched_amount = Column(
        DECIMAL(15, 2),
        nullable=False,
        default=0,
        comment="匹配成功金额"
    )

    difference_amount = Column(
        DECIMAL(15, 2),
        nullable=False,
        default=0,
        comment="差异金额"
    )

    # 执行信息
    started_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="开始执行时间"
    )

    completed_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="完成时间"
    )

    duration_seconds = Column(
        Integer,
        nullable=True,
        comment="执行耗时(秒)"
    )

    # 错误信息
    error_message = Column(
        Text,
        nullable=True,
        comment="错误信息"
    )

    # 备注
    remark = Column(
        Text,
        nullable=True,
        comment="备注"
    )

    # 关系
    differences = relationship(
        "ReconciliationDifference",
        back_populates="reconciliation_record",
        cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index("idx_reconciliation_date", "reconciliation_date"),
        Index("idx_status", "status"),
        Index("idx_type", "reconciliation_type"),
        Index("idx_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ReconciliationRecord(id={self.id}, batch_no={self.batch_no}, date={self.reconciliation_date})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "batch_no": self.batch_no,
            "reconciliation_date": self.reconciliation_date,
            "reconciliation_type": self.reconciliation_type.value if self.reconciliation_type else None,
            "status": self.status.value if self.status else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "statistics": {
                "total_local_count": self.total_local_count,
                "total_remote_count": self.total_remote_count,
                "matched_count": self.matched_count,
                "difference_count": self.difference_count,
                "total_local_amount": float(self.total_local_amount) if self.total_local_amount else 0,
                "total_remote_amount": float(self.total_remote_amount) if self.total_remote_amount else 0,
                "matched_amount": float(self.matched_amount) if self.matched_amount else 0,
                "difference_amount": float(self.difference_amount) if self.difference_amount else 0,
            },
            "execution": {
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
                "duration_seconds": self.duration_seconds,
            },
            "error_message": self.error_message,
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_pending(self) -> bool:
        """检查是否待对账"""
        return self.status == ReconciliationStatus.PENDING

    def is_processing(self) -> bool:
        """检查是否对账中"""
        return self.status == ReconciliationStatus.PROCESSING

    def is_success(self) -> bool:
        """检查是否对账成功"""
        return self.status == ReconciliationStatus.SUCCESS

    def is_failed(self) -> bool:
        """检查是否对账失败"""
        return self.status == ReconciliationStatus.FAILED

    def has_differences(self) -> bool:
        """检查是否有差异"""
        return self.difference_count > 0

    def start_reconciliation(self) -> None:
        """开始对账"""
        self.status = ReconciliationStatus.PROCESSING
        self.started_at = datetime.utcnow()

    def complete_reconciliation(self, has_differences: bool = False) -> None:
        """完成对账"""
        self.status = ReconciliationStatus.PARTIAL if has_differences else ReconciliationStatus.SUCCESS
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())

    def fail_reconciliation(self, error_message: str) -> None:
        """对账失败"""
        self.status = ReconciliationStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())


class ReconciliationDifference(BaseModel):
    """对账差异记录模型

    记录对账过程中发现的差异:
    - 差异类型和详细信息
    - 涉及的交易记录
    - 处理状态和结果
    """

    __tablename__ = "reconciliation_differences"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="差异记录ID"
    )

    # 关联对账记录
    reconciliation_id = Column(
        BIGINT,
        ForeignKey("reconciliation_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="对账记录ID"
    )

    # 差异信息
    difference_type = Column(
        Enum(DifferenceType),
        nullable=False,
        index=True,
        comment="差异类型"
    )

    status = Column(
        Enum(DifferenceStatus),
        nullable=False,
        default=DifferenceStatus.PENDING,
        index=True,
        comment="处理状态"
    )

    # 交易信息
    local_payment_id = Column(
        BIGINT,
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="本地支付记录ID"
    )

    local_transaction_id = Column(
        String(128),
        nullable=True,
        index=True,
        comment="本地交易号"
    )

    remote_transaction_id = Column(
        String(128),
        nullable=True,
        index=True,
        comment="第三方交易号"
    )

    # 金额信息
    local_amount = Column(
        DECIMAL(10, 2),
        nullable=True,
        comment="本地金额"
    )

    remote_amount = Column(
        DECIMAL(10, 2),
        nullable=True,
        comment="第三方金额"
    )

    amount_difference = Column(
        DECIMAL(10, 2),
        nullable=True,
        comment="金额差异"
    )

    # 状态信息
    local_status = Column(
        String(50),
        nullable=True,
        comment="本地状态"
    )

    remote_status = Column(
        String(50),
        nullable=True,
        comment="第三方状态"
    )

    # 时间信息
    local_paid_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="本地支付时间"
    )

    remote_paid_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="第三方支付时间"
    )

    # 详细信息
    local_data = Column(
        Text,
        nullable=True,
        comment="本地交易数据(JSON)"
    )

    remote_data = Column(
        Text,
        nullable=True,
        comment="第三方交易数据(JSON)"
    )

    # 处理信息
    processed_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="处理时间"
    )

    processed_by = Column(
        String(100),
        nullable=True,
        comment="处理人/系统"
    )

    resolution_action = Column(
        String(100),
        nullable=True,
        comment="解决方案"
    )

    resolution_result = Column(
        Text,
        nullable=True,
        comment="处理结果"
    )

    # 备注
    description = Column(
        Text,
        nullable=True,
        comment="差异描述"
    )

    remark = Column(
        Text,
        nullable=True,
        comment="备注"
    )

    # 关系
    reconciliation_record = relationship(
        "ReconciliationRecord",
        foreign_keys=[reconciliation_id],
        back_populates="differences"
    )

    local_payment = relationship(
        "Payment",
        foreign_keys=[local_payment_id]
    )

    # 索引
    __table_args__ = (
        Index("idx_reconciliation_id", "reconciliation_id"),
        Index("idx_difference_type", "difference_type"),
        Index("idx_status", "status"),
        Index("idx_local_transaction_id", "local_transaction_id"),
        Index("idx_remote_transaction_id", "remote_transaction_id"),
        Index("idx_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ReconciliationDifference(id={self.id}, type={self.difference_type.value}, status={self.status.value})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "reconciliation_id": self.reconciliation_id,
            "difference_type": self.difference_type.value if self.difference_type else None,
            "status": self.status.value if self.status else None,
            "transaction_info": {
                "local_payment_id": self.local_payment_id,
                "local_transaction_id": self.local_transaction_id,
                "remote_transaction_id": self.remote_transaction_id,
            },
            "amount_info": {
                "local_amount": float(self.local_amount) if self.local_amount else None,
                "remote_amount": float(self.remote_amount) if self.remote_amount else None,
                "amount_difference": float(self.amount_difference) if self.amount_difference else None,
            },
            "status_info": {
                "local_status": self.local_status,
                "remote_status": self.remote_status,
            },
            "time_info": {
                "local_paid_at": self.local_paid_at.isoformat() if self.local_paid_at else None,
                "remote_paid_at": self.remote_paid_at.isoformat() if self.remote_paid_at else None,
            },
            "processing": {
                "processed_at": self.processed_at.isoformat() if self.processed_at else None,
                "processed_by": self.processed_by,
                "resolution_action": self.resolution_action,
                "resolution_result": self.resolution_result,
            },
            "description": self.description,
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_pending(self) -> bool:
        """检查是否待处理"""
        return self.status == DifferenceStatus.PENDING

    def is_processing(self) -> bool:
        """检查是否处理中"""
        return self.status == DifferenceStatus.PROCESSING

    def is_resolved(self) -> bool:
        """检查是否已解决"""
        return self.status == DifferenceStatus.RESOLVED

    def is_ignored(self) -> bool:
        """检查是否已忽略"""
        return self.status == DifferenceStatus.IGNORED

    def get_local_data(self) -> Optional[Dict[str, Any]]:
        """获取本地交易数据"""
        if self.local_data:
            try:
                return json.loads(self.local_data)
            except json.JSONDecodeError:
                return None
        return None

    def set_local_data(self, data: Dict[str, Any]) -> None:
        """设置本地交易数据"""
        self.local_data = json.dumps(data, ensure_ascii=False)

    def get_remote_data(self) -> Optional[Dict[str, Any]]:
        """获取第三方交易数据"""
        if self.remote_data:
            try:
                return json.loads(self.remote_data)
            except json.JSONDecodeError:
                return None
        return None

    def set_remote_data(self, data: Dict[str, Any]) -> None:
        """设置第三方交易数据"""
        self.remote_data = json.dumps(data, ensure_ascii=False)

    def start_processing(self, processed_by: str) -> None:
        """开始处理"""
        self.status = DifferenceStatus.PROCESSING
        self.processed_by = processed_by
        self.processed_at = datetime.utcnow()

    def mark_as_resolved(self, action: str, result: str) -> None:
        """标记为已解决"""
        self.status = DifferenceStatus.RESOLVED
        self.resolution_action = action
        self.resolution_result = result
        if not self.processed_at:
            self.processed_at = datetime.utcnow()

    def mark_as_ignored(self, reason: str) -> None:
        """标记为已忽略"""
        self.status = DifferenceStatus.IGNORED
        self.remark = reason
        if not self.processed_at:
            self.processed_at = datetime.utcnow()

    def mark_as_failed(self, error_message: str) -> None:
        """标记为处理失败"""
        self.status = DifferenceStatus.FAILED
        self.resolution_result = error_message
        if not self.processed_at:
            self.processed_at = datetime.utcnow()