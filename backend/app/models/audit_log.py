"""
操作日志模型 - BUG-028修复

记录所有关键操作的审计日志

版本: 1.0
创建日期: 2026-01-17
"""

from sqlalchemy import Column, BIGINT, VARCHAR, Text, TIMESTAMP, Integer, Index
from datetime import datetime

from .base import BaseModel


class AuditLog(BaseModel):
    """操作日志模型
    
    记录用户的关键操作，用于审计和追溯
    """

    __tablename__ = "audit_logs"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="日志ID"
    )

    # 用户信息
    user_id = Column(
        BIGINT,
        nullable=True,
        index=True,
        comment="操作用户ID"
    )
    username = Column(
        VARCHAR(50),
        nullable=True,
        comment="操作用户名"
    )

    # 操作信息
    action = Column(
        VARCHAR(50),
        nullable=False,
        index=True,
        comment="操作类型：create/update/delete/login/logout等"
    )
    resource = Column(
        VARCHAR(50),
        nullable=False,
        index=True,
        comment="资源类型：product/user/enterprise等"
    )
    resource_id = Column(
        BIGINT,
        nullable=True,
        comment="资源ID"
    )

    # 详细信息
    details = Column(
        Text,
        nullable=True,
        comment="操作详情（JSON格式）"
    )
    changes = Column(
        Text,
        nullable=True,
        comment="变更内容（JSON格式）"
    )
    before_data = Column(
        Text,
        nullable=True,
        comment="操作前数据（JSON格式）"
    )
    after_data = Column(
        Text,
        nullable=True,
        comment="操作后数据（JSON格式）"
    )

    # 请求信息
    ip_address = Column(
        VARCHAR(45),
        nullable=True,
        comment="操作IP地址（支持IPv6）"
    )
    user_agent = Column(
        VARCHAR(500),
        nullable=True,
        comment="User-Agent"
    )
    request_method = Column(
        VARCHAR(10),
        nullable=True,
        comment="HTTP方法"
    )
    request_path = Column(
        VARCHAR(500),
        nullable=True,
        comment="请求路径"
    )

    # 结果信息
    status_code = Column(
        Integer,
        nullable=True,
        comment="响应状态码"
    )
    is_success = Column(
        Integer,
        default=1,
        comment="是否成功：1成功/0失败"
    )
    error_message = Column(
        Text,
        nullable=True,
        comment="错误消息"
    )

    # 时间戳
    created_at = Column(
        TIMESTAMP,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="操作时间"
    )

    # 索引
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_action", "action"),
        Index("idx_resource", "resource", "resource_id"),
        Index("idx_created_at", "created_at"),
        Index("idx_user_action", "user_id", "action"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, user={self.username}, "
            f"action={self.action}, resource={self.resource})>"
        )
