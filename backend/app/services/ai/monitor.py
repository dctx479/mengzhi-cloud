"""
AI Provider 监控和告警服务

功能:
- 实时监控Provider状态
- 故障告警（邮件/Webhook/短信，通过 core/alerts.alert_manager 统一入口）
- 故障恢复通知
- 性能指标收集

注意：本模块的告警实现已委托到 backend/app/core/alerts.py 的 alert_manager。
历史遗留的 _send_email_alert / _send_webhook_alert / _send_sms_alert 方法
已废弃并移除，所有调用方统一通过 alert_manager.send_alert() 发送告警。
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from loguru import logger
from sqlalchemy.orm import Session

from app.models.tenant_ai_config import TenantAIConfig, HealthStatus
from app.core.alerts import alert_manager


class AlertLevel:
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel:
    """告警渠道"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SMS = "sms"


class Alert:
    """告警信息"""

    def __init__(
        self,
        level: str,
        title: str,
        message: str,
        provider_id: Optional[int] = None,
        enterprise_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.level = level
        self.title = title
        self.message = message
        self.provider_id = provider_id
        self.enterprise_id = enterprise_id
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "level": self.level,
            "title": self.title,
            "message": self.message,
            "provider_id": self.provider_id,
            "enterprise_id": self.enterprise_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class MonitorConfig:
    """监控配置"""
    # 告警阈值
    ERROR_RATE_WARNING_THRESHOLD = 10  # 错误率警告阈值（百分比）
    ERROR_RATE_CRITICAL_THRESHOLD = 30  # 错误率严重阈值（百分比）
    RESPONSE_TIME_WARNING_THRESHOLD = 3000  # 响应时间警告阈值（毫秒）
    RESPONSE_TIME_CRITICAL_THRESHOLD = 5000  # 响应时间严重阈值（毫秒）

    # 告警频率限制（秒）
    ALERT_COOLDOWN = 300  # 同一告警的冷却时间

    # Webhook配置
    WEBHOOK_TIMEOUT = 10  # Webhook超时时间（秒）
    WEBHOOK_RETRY = 3  # Webhook重试次数


class Monitor:
    """监控器"""

    def __init__(self, db: Session):
        self.db = db
        self.config = MonitorConfig()
        self._alert_history: Dict[str, datetime] = {}  # 告警历史（用于频率限制）
        self._running = False

    def _should_send_alert(self, alert_key: str) -> bool:
        """检查是否应该发送告警（频率限制）

        Args:
            alert_key: 告警键

        Returns:
            bool: 是否应该发送
        """
        last_alert_time = self._alert_history.get(alert_key)
        if not last_alert_time:
            return True

        time_since_last = (datetime.utcnow() - last_alert_time).total_seconds()
        return time_since_last >= self.config.ALERT_COOLDOWN

    def _record_alert(self, alert_key: str):
        """记录告警时间

        Args:
            alert_key: 告警键
        """
        self._alert_history[alert_key] = datetime.utcnow()

    async def send_alert(
        self,
        alert: "Alert",
        channels: List[str] = None
    ):
        """发送告警（委托到 core/alerts.alert_manager 统一入口）

        Args:
            alert: 告警信息
            channels: 告警渠道列表；None 时使用 alert 默认配置
        """
        # 频率限制保留在 Monitor 层（按企业+provider+level+title 维度）
        alert_key = f"{alert.enterprise_id}:{alert.provider_id}:{alert.level}:{alert.title}"

        if not self._should_send_alert(alert_key):
            logger.debug(f"Alert {alert_key} skipped due to cooldown")
            return

        logger.info(
            f"Sending alert: {alert.title} (level: {alert.level}, "
            f"provider: {alert.provider_id}, enterprise: {alert.enterprise_id})"
        )

        # 把本模块的 channel 名称映射到 core.alerts 的 channel 名称
        if channels is None:
            core_channels = None  # 让 alert_manager 按全局配置自动选择
        else:
            core_channels = []
            if AlertChannel.EMAIL in channels:
                core_channels.append('email')
            if AlertChannel.WEBHOOK in channels:
                core_channels.append('dingtalk')  # 通用 Webhook 走钉钉通道
            if AlertChannel.SMS in channels:
                core_channels.append('sms')

        # 委托到统一告警管理器
        await alert_manager.send_alert(
            level=alert.level,
            title=alert.title,
            message=alert.message,
            extra={
                "provider_id": alert.provider_id,
                "enterprise_id": alert.enterprise_id,
                **(alert.metadata or {}),
            },
            channels=core_channels,
            enterprise_id=str(alert.enterprise_id) if alert.enterprise_id is not None else None,
        )

        # 记录告警时间
        self._record_alert(alert_key)

    async def check_provider_health_and_alert(self, config: TenantAIConfig):
        """检查Provider健康状态并发送告警

        Args:
            config: AI配置
        """
        try:
            # 检查健康状态
            if config.health_status == HealthStatus.UNHEALTHY.value:
                alert = Alert(
                    level=AlertLevel.CRITICAL,
                    title=f"Provider {config.provider} is unhealthy",
                    message=(
                        f"Provider {config.provider} (ID: {config.id}) is unhealthy. "
                        f"Error count: {config.error_count}, "
                        f"Error rate: {config.get_error_rate():.2f}%, "
                        f"Last error: {config.last_error_message}"
                    ),
                    provider_id=config.id,
                    enterprise_id=config.enterprise_id,
                    metadata={
                        "provider": config.provider,
                        "error_count": config.error_count,
                        "error_rate": config.get_error_rate(),
                        "last_error_message": config.last_error_message,
                        "last_error_time": config.last_error_time.isoformat() if config.last_error_time else None,
                    }
                )
                await self.send_alert(alert)

            elif config.health_status == HealthStatus.DEGRADED.value:
                alert = Alert(
                    level=AlertLevel.WARNING,
                    title=f"Provider {config.provider} is degraded",
                    message=(
                        f"Provider {config.provider} (ID: {config.id}) is degraded. "
                        f"Error count: {config.error_count}, "
                        f"Error rate: {config.get_error_rate():.2f}%, "
                        f"Avg response time: {config.avg_response_time:.2f}ms"
                    ),
                    provider_id=config.id,
                    enterprise_id=config.enterprise_id,
                    metadata={
                        "provider": config.provider,
                        "error_count": config.error_count,
                        "error_rate": config.get_error_rate(),
                        "avg_response_time": config.avg_response_time,
                    }
                )
                await self.send_alert(alert)

            # 检查错误率
            error_rate = config.get_error_rate()
            if error_rate >= self.config.ERROR_RATE_CRITICAL_THRESHOLD:
                alert = Alert(
                    level=AlertLevel.CRITICAL,
                    title=f"High error rate for provider {config.provider}",
                    message=(
                        f"Provider {config.provider} (ID: {config.id}) has high error rate: "
                        f"{error_rate:.2f}% (threshold: {self.config.ERROR_RATE_CRITICAL_THRESHOLD}%)"
                    ),
                    provider_id=config.id,
                    enterprise_id=config.enterprise_id,
                    metadata={
                        "provider": config.provider,
                        "error_rate": error_rate,
                        "threshold": self.config.ERROR_RATE_CRITICAL_THRESHOLD,
                    }
                )
                await self.send_alert(alert)

            elif error_rate >= self.config.ERROR_RATE_WARNING_THRESHOLD:
                alert = Alert(
                    level=AlertLevel.WARNING,
                    title=f"Elevated error rate for provider {config.provider}",
                    message=(
                        f"Provider {config.provider} (ID: {config.id}) has elevated error rate: "
                        f"{error_rate:.2f}% (threshold: {self.config.ERROR_RATE_WARNING_THRESHOLD}%)"
                    ),
                    provider_id=config.id,
                    enterprise_id=config.enterprise_id,
                    metadata={
                        "provider": config.provider,
                        "error_rate": error_rate,
                        "threshold": self.config.ERROR_RATE_WARNING_THRESHOLD,
                    }
                )
                await self.send_alert(alert)

            # 检查响应时间
            if config.avg_response_time:
                if config.avg_response_time >= self.config.RESPONSE_TIME_CRITICAL_THRESHOLD:
                    alert = Alert(
                        level=AlertLevel.CRITICAL,
                        title=f"High response time for provider {config.provider}",
                        message=(
                            f"Provider {config.provider} (ID: {config.id}) has high response time: "
                            f"{config.avg_response_time:.2f}ms "
                            f"(threshold: {self.config.RESPONSE_TIME_CRITICAL_THRESHOLD}ms)"
                        ),
                        provider_id=config.id,
                        enterprise_id=config.enterprise_id,
                        metadata={
                            "provider": config.provider,
                            "avg_response_time": config.avg_response_time,
                            "threshold": self.config.RESPONSE_TIME_CRITICAL_THRESHOLD,
                        }
                    )
                    await self.send_alert(alert)

                elif config.avg_response_time >= self.config.RESPONSE_TIME_WARNING_THRESHOLD:
                    alert = Alert(
                        level=AlertLevel.WARNING,
                        title=f"Elevated response time for provider {config.provider}",
                        message=(
                            f"Provider {config.provider} (ID: {config.id}) has elevated response time: "
                            f"{config.avg_response_time:.2f}ms "
                            f"(threshold: {self.config.RESPONSE_TIME_WARNING_THRESHOLD}ms)"
                        ),
                        provider_id=config.id,
                        enterprise_id=config.enterprise_id,
                        metadata={
                            "provider": config.provider,
                            "avg_response_time": config.avg_response_time,
                            "threshold": self.config.RESPONSE_TIME_WARNING_THRESHOLD,
                        }
                    )
                    await self.send_alert(alert)

            # 检查熔断器
            if config.is_circuit_breaker_open():
                alert = Alert(
                    level=AlertLevel.CRITICAL,
                    title=f"Circuit breaker opened for provider {config.provider}",
                    message=(
                        f"Circuit breaker opened for provider {config.provider} (ID: {config.id}). "
                        f"Will remain open until {config.circuit_breaker_open_until.isoformat()}"
                    ),
                    provider_id=config.id,
                    enterprise_id=config.enterprise_id,
                    metadata={
                        "provider": config.provider,
                        "circuit_breaker_open_until": config.circuit_breaker_open_until.isoformat(),
                    }
                )
                await self.send_alert(alert)

        except Exception as e:
            logger.error(f"Error checking provider health and alerting: {e}")

    async def send_recovery_notification(self, config: TenantAIConfig):
        """发送恢复通知

        Args:
            config: AI配置
        """
        try:
            alert = Alert(
                level=AlertLevel.INFO,
                title=f"Provider {config.provider} recovered",
                message=(
                    f"Provider {config.provider} (ID: {config.id}) has recovered. "
                    f"Current status: {config.health_status}"
                ),
                provider_id=config.id,
                enterprise_id=config.enterprise_id,
                metadata={
                    "provider": config.provider,
                    "health_status": config.health_status,
                }
            )
            await self.send_alert(alert)

        except Exception as e:
            logger.error(f"Error sending recovery notification: {e}")

    async def monitor_all_providers(self):
        """监控所有Provider"""
        try:
            configs = self.db.query(TenantAIConfig).filter(
                TenantAIConfig.is_active == True,
                TenantAIConfig.deleted_at.is_(None)
            ).all()

            logger.info(f"Monitoring {len(configs)} providers")

            tasks = []
            for config in configs:
                tasks.append(self.check_provider_health_and_alert(config))

            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Error monitoring all providers: {e}")

    async def start_periodic_monitoring(self, interval: int = 60):
        """启动定期监控

        Args:
            interval: 监控间隔（秒）
        """
        self._running = True
        logger.info(f"Starting periodic monitoring, interval: {interval}s")

        while self._running:
            try:
                await self.monitor_all_providers()
            except Exception as e:
                logger.error(f"Error in periodic monitoring: {e}")

            await asyncio.sleep(interval)

    def stop_periodic_monitoring(self):
        """停止定期监控"""
        self._running = False
        logger.info("Stopping periodic monitoring")

    def get_monitoring_summary(self, enterprise_id: Optional[int] = None) -> Dict[str, Any]:
        """获取监控摘要

        Args:
            enterprise_id: 企业ID（可选，如果不提供则返回所有企业的摘要）

        Returns:
            Dict[str, Any]: 监控摘要
        """
        try:
            query = self.db.query(TenantAIConfig).filter(
                TenantAIConfig.deleted_at.is_(None)
            )

            if enterprise_id:
                query = query.filter(TenantAIConfig.enterprise_id == enterprise_id)

            configs = query.all()

            total_providers = len(configs)
            active_providers = sum(1 for c in configs if c.is_active)
            healthy_providers = sum(
                1 for c in configs
                if c.health_status == HealthStatus.HEALTHY.value and c.is_active
            )
            degraded_providers = sum(
                1 for c in configs
                if c.health_status == HealthStatus.DEGRADED.value and c.is_active
            )
            unhealthy_providers = sum(
                1 for c in configs
                if c.health_status == HealthStatus.UNHEALTHY.value or not c.is_active
            )

            total_requests = sum(c.total_requests for c in configs)
            total_failures = sum(c.failed_requests for c in configs)
            overall_error_rate = (
                (total_failures / total_requests * 100) if total_requests > 0 else 0
            )

            avg_response_times = [
                c.avg_response_time for c in configs
                if c.avg_response_time is not None
            ]
            overall_avg_response_time = (
                sum(avg_response_times) / len(avg_response_times)
                if avg_response_times else None
            )

            return {
                "enterprise_id": enterprise_id,
                "total_providers": total_providers,
                "active_providers": active_providers,
                "healthy_providers": healthy_providers,
                "degraded_providers": degraded_providers,
                "unhealthy_providers": unhealthy_providers,
                "total_requests": total_requests,
                "total_failures": total_failures,
                "overall_error_rate": round(overall_error_rate, 2),
                "overall_avg_response_time": round(overall_avg_response_time, 2) if overall_avg_response_time else None,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting monitoring summary: {e}")
            return {}
