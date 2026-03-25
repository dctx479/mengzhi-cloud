"""
日志配置模块 - BUG-017修复

统一日志记录配置，避免不同模块的日志记录不一致

版本: 1.0
更新日期: 2026-01-17
"""

import logging
import sys
from typing import Optional
from pathlib import Path
from loguru import logger as loguru_logger
from app.core.constants import (
    LOG_FORMAT,
    LOG_LEVEL,
    LOG_FILE_PATH,
    LOG_ROTATION,
    LOG_RETENTION
)


class LoggerConfig:
    """日志配置类"""

    _instance: Optional['LoggerConfig'] = None
    _logger_configured: bool = False

    def __new__(cls) -> 'LoggerConfig':
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化日志配置"""
        if not LoggerConfig._logger_configured:
            self._configure_loguru()
            LoggerConfig._logger_configured = True

    @staticmethod
    def _configure_loguru() -> None:
        """配置loguru日志"""
        # 移除默认的处理器
        loguru_logger.remove()

        # 添加控制台输出
        loguru_logger.add(
            sys.stderr,
            format=LOG_FORMAT,
            level=LOG_LEVEL,
            colorize=True
        )

        # 添加文件输出
        log_path = Path(LOG_FILE_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        loguru_logger.add(
            str(log_path),
            format=LOG_FORMAT,
            level=LOG_LEVEL,
            rotation=LOG_ROTATION,
            retention=LOG_RETENTION,
            encoding="utf-8"
        )

    @staticmethod
    def get_logger(name: str):
        """获取日志记录器"""
        # 确保已初始化
        LoggerConfig()
        return loguru_logger.bind(name=name)


# 全局日志记录器实例
logger = loguru_logger


def configure_logging() -> None:
    """配置应用日志"""
    LoggerConfig()


# 导出供外部使用
__all__ = ['logger', 'LoggerConfig', 'configure_logging']
