"""监控中间件"""
import time
import asyncio
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.monitoring import performance_monitor
from app.core.alerts import alert_manager, AlertLevel
from config.monitoring import monitoring_config
from loguru import logger

class MonitoringMiddleware(BaseHTTPMiddleware):
    """监控中间件"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # 记录请求
            performance_monitor.record_request(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code,
                duration=duration
            )

            # 慢请求告警
            if duration > 5.0:
                await alert_manager.send_alert(
                    level=AlertLevel.WARNING,
                    title="慢请求检测",
                    message=f"请求 {request.method} {request.url.path} 耗时 {duration:.2f}秒",
                    extra={'duration': duration, 'endpoint': str(request.url.path)}
                )

            # 错误状态码告警
            if response.status_code >= 500:
                await alert_manager.send_alert(
                    level=AlertLevel.ERROR,
                    title="服务器错误",
                    message=f"请求 {request.method} {request.url.path} 返回 {response.status_code}",
                    extra={'status': response.status_code, 'endpoint': str(request.url.path)}
                )

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Request failed: {request.method} {request.url.path} - {str(e)}")

            await alert_manager.send_alert(
                level=AlertLevel.CRITICAL,
                title="请求异常",
                message=f"请求 {request.method} {request.url.path} 发生异常: {str(e)}",
                extra={'error': str(e), 'endpoint': str(request.url.path)}
            )

            raise

class ResourceMonitoringMiddleware(BaseHTTPMiddleware):
    """资源监控中间件"""

    def __init__(self, app, check_interval: int = 5):
        """
        初始化资源监控中间件

        Args:
            app: FastAPI应用实例
            check_interval: 检查间隔（秒），避免频繁调用psutil
        """
        super().__init__(app)
        self.check_interval = check_interval
        self._last_check_time = 0
        self._last_check_result = {}

    async def dispatch(self, request: Request, call_next):
        # FIX Bug #2: Avoid blocking event loop with synchronous psutil calls
        # Only check resource every N seconds and cache result
        current_time = time.time()
        if current_time - self._last_check_time > self.check_interval:
            # Run blocking psutil calls in thread pool executor
            self._last_check_result = await asyncio.to_thread(self._check_resources)
            self._last_check_time = current_time

        response = await call_next(request)
        return response

    def _check_resources(self) -> dict:
        """
        检查系统资源使用情况（同步函数在线程池中运行）

        Returns:
            dict: 资源检查结果
        """
        try:
            import psutil
            cpu = psutil.cpu_percent()
            memory = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent

            # CPU告警
            if cpu > monitoring_config.CPU_THRESHOLD:
                # 这些告警应该通过后台任务处理，而不是在请求中
                logger.warning(f"CPU使用率过高: {cpu:.1f}%")

            # 内存告警
            if memory > monitoring_config.MEMORY_THRESHOLD:
                logger.warning(f"内存使用率过高: {memory:.1f}%")

            # 磁盘告警
            if disk > monitoring_config.DISK_THRESHOLD:
                logger.warning(f"磁盘使用率过高: {disk:.1f}%")

            return {"cpu": cpu, "memory": memory, "disk": disk}
        except Exception as e:
            logger.error(f"检查系统资源失败: {str(e)}")
            return {}
