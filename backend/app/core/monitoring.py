"""监控核心模块"""

import time
import psutil
from typing import Dict, Any
from datetime import datetime
from loguru import logger
from prometheus_client import Gauge, generate_latest
from sqlalchemy import event
from sqlalchemy.engine import Engine

# 从中央 metrics 模块导入共享指标，避免重复注册
from app.core.metrics import (
    http_requests_total as request_count,
    http_request_duration as request_duration,
    db_query_duration,
)

# 本模块独有的系统级指标
active_connections = Gauge("db_active_connections", "Active database connections")
cpu_usage = Gauge("system_cpu_usage_percent", "CPU usage percentage")
memory_usage = Gauge("system_memory_usage_percent", "Memory usage percentage")
disk_usage = Gauge("system_disk_usage_percent", "Disk usage percentage")


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.slow_queries: list = []
        self.error_count: Dict[str, int] = {}

    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """记录HTTP请求"""
        request_count.labels(method=method, endpoint=endpoint, status=status).inc()
        request_duration.labels(method=method, endpoint=endpoint).observe(duration)

    def record_db_query(self, query_type: str, duration: float, query: str = ""):
        """记录数据库查询"""
        db_query_duration.labels(operation=query_type).observe(duration)


        if duration > 1.0:  # Default slow query threshold
            self.slow_queries.append({"query": query[:200], "duration": duration, "timestamp": datetime.now()})
            logger.warning(f"Slow query detected: {duration:.2f}s - {query[:100]}")

    def update_system_metrics(self):
        """更新系统指标（同步函数，应在线程池中调用）"""
        import os

        # 安全修复: interval=None 不阻塞（返回上次调用以来的CPU使用率），
        # 避免 interval=1 在事件循环中阻塞1秒
        cpu_usage.set(psutil.cpu_percent(interval=None))
        memory_usage.set(psutil.virtual_memory().percent)

        # 使用平台兼容的路径：Windows 使用 'C:\' (或其他盘符)，Unix 使用 '/'
        disk_path = 'C:\\' if os.name == 'nt' else '/'
        disk_usage.set(psutil.disk_usage(disk_path).percent)

    def get_metrics(self) -> bytes:
        """获取Prometheus指标"""
        return generate_latest()


performance_monitor = PerformanceMonitor()


# SQLAlchemy事件监听
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.time())


@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info["query_start_time"].pop(-1)
    query_type = statement.split()[0].upper() if statement else "UNKNOWN"
    performance_monitor.record_db_query(query_type, total, statement)
