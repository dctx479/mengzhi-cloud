"""监控中间件"""
import time
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

    async def dispatch(self, request: Request, call_next):
        # 更新系统指标
        performance_monitor.update_system_metrics()

        # 检查资源使用情况
        import psutil
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent

        # CPU告警
        if cpu > monitoring_config.CPU_THRESHOLD:
            await alert_manager.send_alert(
                level=AlertLevel.WARNING,
                title="CPU使用率过高",
                message=f"当前CPU使用率: {cpu:.1f}%",
                extra={'cpu_usage': cpu}
            )

        # 内存告警
        if memory > monitoring_config.MEMORY_THRESHOLD:
            await alert_manager.send_alert(
                level=AlertLevel.WARNING,
                title="内存使用率过高",
                message=f"当前内存使用率: {memory:.1f}%",
                extra={'memory_usage': memory}
            )

        # 磁盘告警
        if disk > monitoring_config.DISK_THRESHOLD:
            await alert_manager.send_alert(
                level=AlertLevel.ERROR,
                title="磁盘使用率过高",
                message=f"当前磁盘使用率: {disk:.1f}%",
                extra={'disk_usage': disk}
            )

        response = await call_next(request)
        return response
