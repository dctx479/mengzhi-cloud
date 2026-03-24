"""
系统配置模型 - 存储全局键值对设置

版本: 1.0
更新日期: 2026-03-24
"""

from sqlalchemy import Column, String, JSON, Text
from sqlalchemy.dialects.mysql import BIGINT

from .base import BaseModel


class SystemConfig(BaseModel):
    """系统配置表 - 键值对存储"""

    __tablename__ = "system_configs"

    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True, comment="配置键")
    config_value = Column(JSON, nullable=True, comment="配置值(JSON)")
    description = Column(Text, nullable=True, comment="配置说明")

    def __repr__(self):
        return f"<SystemConfig(key={self.config_key})>"
