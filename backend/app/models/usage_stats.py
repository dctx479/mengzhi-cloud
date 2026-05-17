"""
使用统计模型
"""
from sqlalchemy import Column, BIGINT, VARCHAR, DECIMAL, INTEGER, Enum as SQLEnum, Index
from datetime import datetime
import enum

from .base import BaseModel


class StatType(str, enum.Enum):
    """统计类型"""
    CHAT = "chat"
    IMAGE = "image"
    VIDEO = "video"


class UsageStatistics(BaseModel):
    """使用统计模型"""

    __tablename__ = "usage_statistics"

    id = Column(BIGINT, primary_key=True, autoincrement=True)

    # 关联信息
    enterprise_id = Column(BIGINT, nullable=False, index=True)
    user_id = Column(BIGINT, nullable=True, index=True)

    # 统计类型
    stat_type = Column(SQLEnum(StatType), nullable=False)

    # 模型信息
    model = Column(VARCHAR(50), nullable=True)
    resolution = Column(VARCHAR(20), nullable=True)
    duration = Column(INTEGER, nullable=True)

    # 客户端计费（按次）
    request_count = Column(INTEGER, default=1)
    client_charge = Column(DECIMAL(10, 4), nullable=False, comment="客户端收费")

    # 后台统计（实际消耗）
    input_tokens = Column(INTEGER, default=0)
    output_tokens = Column(INTEGER, default=0)
    backend_cost = Column(DECIMAL(10, 4), nullable=False, comment="后台成本")

    # 利润分析
    profit = Column(DECIMAL(10, 4), nullable=False, comment="利润")
    profit_margin = Column(DECIMAL(5, 2), nullable=False, comment="利润率%")

    # 索引（created_at 继承自 BaseModel）
    __table_args__ = (
        Index("idx_enterprise_created", "enterprise_id", "created_at"),
        Index("idx_stat_type", "stat_type"),
        Index("idx_model", "model"),
    )
