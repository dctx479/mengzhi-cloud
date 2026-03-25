"""
JSON格式日志配置

提供结构化的JSON日志输出，方便ELK Stack采集和分析。

使用方法:
    from app.core.json_logging import setup_json_logging

    # 在应用启动时调用
    setup_json_logging()
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from loguru import logger


class JSONFormatter(logging.Formatter):
    """
    JSON格式化器

    将日志记录格式化为JSON格式，包含以下字段：
    - timestamp: ISO 8601格式的时间戳
    - level: 日志级别
    - logger: 日志器名称
    - message: 日志消息
    - module: 模块名
    - function: 函数名
    - line: 行号
    - exception: 异常信息（如果有）
    - extra: 额外字段（如果有）
    """

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON字符串"""
        # 基础日志数据
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加额外字段
        if hasattr(record, 'extra'):
            log_data.update(record.extra)

        # 添加进程和线程信息
        log_data["process_id"] = record.process
        log_data["thread_id"] = record.thread
        log_data["thread_name"] = record.threadName

        return json.dumps(log_data, ensure_ascii=False)


def json_sink(message):
    """
    Loguru的JSON sink函数

    将Loguru日志输出为JSON格式
    """
    record = message.record

    log_data = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "logger": record["name"],
        "message": record["message"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
        "process_id": record["process"].id,
        "thread_id": record["thread"].id,
        "thread_name": record["thread"].name,
    }

    # 添加异常信息
    if record["exception"]:
        log_data["exception"] = {
            "type": record["exception"].type.__name__,
            "value": str(record["exception"].value),
            "traceback": record["exception"].traceback
        }

    # 添加额外字段
    if "extra" in record:
        log_data.update(record["extra"])

    print(json.dumps(log_data, ensure_ascii=False))


def setup_json_logging(
    log_dir: str = "logs",
    log_file: str = "app.log",
    log_level: str = "INFO",
    rotation: str = "1 day",
    retention: str = "30 days",
    enable_console: bool = True
):
    """
    配置JSON格式日志

    参数:
        log_dir: 日志目录
        log_file: 日志文件名
        log_level: 日志级别
        rotation: 日志轮转周期
        retention: 日志保留时间
        enable_console: 是否输出到控制台

    示例:
        setup_json_logging(
            log_dir="logs",
            log_file="app.log",
            log_level="INFO",
            rotation="1 day",
            retention="30 days"
        )
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 移除默认的日志处理器
    logger.remove()

    # 添加控制台JSON输出
    if enable_console:
        logger.add(
            json_sink,
            level=log_level,
            format="{message}",
        )

    # 添加文件JSON输出
    log_file_path = log_path / log_file
    logger.add(
        log_file_path,
        level=log_level,
        format='<level>{{"timestamp":"{time:YYYY-MM-DDTHH:mm:ss.SSSZ}","level":"{level}","logger":"{name}","message":"{message}","module":"{module}","function":"{function}","line":{line}}}</level>',
        rotation=rotation,
        retention=retention,
        compression="zip",
        enqueue=True,  # 异步写入
        backtrace=True,  # 启用回溯
        diagnose=True,  # 启用诊断
    )

    # 添加错误日志单独文件
    error_log_file = log_path / f"error_{log_file}"
    logger.add(
        error_log_file,
        level="ERROR",
        format='<level>{{"timestamp":"{time:YYYY-MM-DDTHH:mm:ss.SSSZ}","level":"{level}","logger":"{name}","message":"{message}","module":"{module}","function":"{function}","line":{line},"exception":"{exception}"}}</level>',
        rotation=rotation,
        retention=retention,
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    logger.info(f"✅ JSON logging enabled: {log_file_path}")
    logger.info(f"✅ Error logging enabled: {error_log_file}")


def get_logger_with_context(**context):
    """
    获取带有上下文的日志器

    参数:
        **context: 上下文键值对（如 user_id, request_id 等）

    返回:
        带有上下文的日志器

    示例:
        log = get_logger_with_context(user_id="123", request_id="abc")
        log.info("User action", action="login")
    """
    return logger.bind(**context)


# 使用示例
"""
# 基本使用
from app.core.json_logging import setup_json_logging
setup_json_logging()

# 带上下文的日志
from app.core.json_logging import get_logger_with_context
log = get_logger_with_context(user_id="123", request_id="abc-def")
log.info("User login successful")

# 记录异常
try:
    1 / 0
except Exception as e:
    logger.exception("Division error occurred")

# 结构化日志
logger.info("API request", extra={
    "method": "POST",
    "path": "/api/v1/users",
    "status_code": 201,
    "response_time": 0.123
})
"""
