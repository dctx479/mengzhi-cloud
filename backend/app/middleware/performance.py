"""
性能监控中间件

功能：
1. 记录每个请求的响应时间
2. 记录错误率
3. 记录吞吐量
4. 存储性能日志到数据库

版本: 1.0
更新日期: 2026-01-22
"""

import time
import uuid
from datetime import datetime
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from app.models.sla import PerformanceLog
from app.core.database import SessionLocal


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""

    def __init__(self, app, exclude_paths: list = None):
        """
        初始化中间件

        Args:
            app: FastAPI应用实例
            exclude_paths: 排除的路径列表（不记录性能数据）
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/favicon.ico",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并记录性能数据

        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理器

        Returns:
            Response: 响应对象
        """
        # 检查是否需要排除此路径
        if self._should_exclude(request.url.path):
            return await call_next(request)

        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 记录开始时间
        start_time = time.time()

        # 初始化变量
        response = None
        status_code = 500
        error_message = None

        try:
            # 调用下一个处理器
            response = await call_next(request)
            status_code = response.status_code

        except Exception as e:
            # 捕获异常
            error_message = str(e)
            status_code = 500
            raise

        finally:
            # 计算响应时间（毫秒）
            response_time = (time.time() - start_time) * 1000

            # 判断是否成功（2xx和3xx状态码）
            is_success = 200 <= status_code < 400

            # 获取用户信息
            user_id = None
            enterprise_id = None
            if hasattr(request.state, "user"):
                user = request.state.user
                user_id = getattr(user, "id", None)
                enterprise_id = getattr(user, "enterprise_id", None)

            # 异步记录性能日志
            self._log_performance(
                request_id=request_id,
                endpoint=request.url.path,
                method=request.method,
                user_id=user_id,
                enterprise_id=enterprise_id,
                response_time=response_time,
                status_code=status_code,
                is_success=is_success,
                error_message=error_message,
            )

        return response

    def _should_exclude(self, path: str) -> bool:
        """
        判断路径是否应该被排除

        Args:
            path: 请求路径

        Returns:
            bool: 是否排除
        """
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        return False

    def _log_performance(
        self,
        request_id: str,
        endpoint: str,
        method: str,
        user_id: int,
        enterprise_id: int,
        response_time: float,
        status_code: int,
        is_success: bool,
        error_message: str = None,
    ):
        """
        记录性能日志到数据库

        Args:
            request_id: 请求ID
            endpoint: 端点路径
            method: 请求方法
            user_id: 用户ID
            enterprise_id: 企业ID
            response_time: 响应时间（毫秒）
            status_code: HTTP状态码
            is_success: 是否成功
            error_message: 错误信息
        """
        db: Session = None
        try:
            db = SessionLocal()

            # 创建性能日志记录
            log = PerformanceLog(
                request_id=request_id,
                endpoint=endpoint,
                method=method,
                user_id=user_id,
                enterprise_id=enterprise_id,
                response_time=response_time,
                status_code=status_code,
                is_success=is_success,
                error_message=error_message,
                timestamp=datetime.utcnow().isoformat(),
            )

            db.add(log)
            db.commit()

        except Exception as e:
            # 记录日志失败不应该影响请求处理
            print(f"Failed to log performance: {str(e)}")
            if db:
                db.rollback()

        finally:
            if db:
                db.close()


class PerformanceMonitor:
    """性能监控工具类 - 用于手动记录性能数据"""

    @staticmethod
    def record_metric(
        db: Session,
        operation: str,
        duration: float,
        success: bool = True,
        metadata: dict = None,
    ):
        """
        手动记录性能指标

        Args:
            db: 数据库会话
            operation: 操作名称
            duration: 持续时间（毫秒）
            success: 是否成功
            metadata: 额外的元数据
        """
        try:
            log = PerformanceLog(
                request_id=str(uuid.uuid4()),
                endpoint=operation,
                method="INTERNAL",
                response_time=duration,
                status_code=200 if success else 500,
                is_success=success,
                error_message=metadata.get("error") if metadata else None,
                timestamp=datetime.utcnow().isoformat(),
            )

            db.add(log)
            db.commit()

        except Exception as e:
            print(f"Failed to record metric: {str(e)}")
            db.rollback()

    @staticmethod
    def measure_time(func):
        """
        装饰器：测量函数执行时间

        使用示例:
            @PerformanceMonitor.measure_time
            def my_function():
                pass
        """
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = (time.time() - start_time) * 1000
                print(f"{func.__name__} took {duration:.2f}ms")
        return wrapper


# 性能统计工具
class PerformanceStats:
    """性能统计工具"""

    @staticmethod
    def calculate_percentile(values: list, percentile: float) -> float:
        """
        计算百分位数

        Args:
            values: 数值列表
            percentile: 百分位（0-100）

        Returns:
            float: 百分位数值
        """
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * (percentile / 100))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]

    @staticmethod
    def calculate_stats(values: list) -> dict:
        """
        计算统计数据

        Args:
            values: 数值列表

        Returns:
            dict: 统计数据
        """
        if not values:
            return {
                "count": 0,
                "min": 0,
                "max": 0,
                "avg": 0,
                "p50": 0,
                "p95": 0,
                "p99": 0,
            }

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "p50": PerformanceStats.calculate_percentile(values, 50),
            "p95": PerformanceStats.calculate_percentile(values, 95),
            "p99": PerformanceStats.calculate_percentile(values, 99),
        }
