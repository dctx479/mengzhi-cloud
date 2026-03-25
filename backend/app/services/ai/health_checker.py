"""
AI Provider 健康检查服务

功能:
- 定期健康检查（心跳）
- 检测API响应时间
- 检测错误率
- 标记不健康的Provider
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List
from loguru import logger
from sqlalchemy.orm import Session

from app.models.tenant_ai_config import TenantAIConfig, HealthStatus
from app.services.ai.base_provider import BaseAIProvider, ChatCompletionRequest, ChatMessage
from app.services.ai.factory import AIProviderFactory
from app.core.security import decrypt_api_key


class HealthCheckConfig:
    """健康检查配置"""
    # 检查间隔（秒）
    CHECK_INTERVAL = 60
    # 超时时间（秒）
    TIMEOUT = 10
    # 响应时间阈值（毫秒）
    RESPONSE_TIME_THRESHOLD = 5000
    # 错误率阈值（百分比）
    ERROR_RATE_THRESHOLD = 20
    # 连续错误阈值
    CONSECUTIVE_ERROR_THRESHOLD = 3
    # 熔断器开启时长（秒）
    CIRCUIT_BREAKER_DURATION = 300


class HealthChecker:
    """健康检查器"""

    def __init__(self, db: Session):
        self.db = db
        self.config = HealthCheckConfig()
        self._running = False

    async def check_provider_health(
        self,
        config: TenantAIConfig,
        api_key: str
    ) -> bool:
        """检查单个Provider的健康状态

        Args:
            config: AI配置
            api_key: 解密后的API密钥

        Returns:
            bool: 是否健康
        """
        try:
            # 检查熔断器
            if config.is_circuit_breaker_open():
                logger.warning(
                    f"Provider {config.provider} (ID: {config.id}) circuit breaker is open"
                )
                return False

            # 创建Provider实例
            try:
                provider = AIProviderFactory.create(
                    provider_type=config.provider,
                    api_key=api_key,
                    base_url=config.base_url
                )
            except Exception as e:
                error_msg = f"Failed to create provider: {str(e)}"
                config.record_failure(error_msg)
                config.update_health_status()
                
                if config.error_count >= self.config.CONSECUTIVE_ERROR_THRESHOLD:
                    config.open_circuit_breaker(self.config.CIRCUIT_BREAKER_DURATION)
                    logger.error(
                        f"Provider {config.provider} (ID: {config.id}) "
                        f"circuit breaker opened due to consecutive errors"
                    )
                
                config.last_check_time = datetime.utcnow()
                self.db.commit()
                
                logger.error(
                    f"Provider {config.provider} (ID: {config.id}) "
                    f"health check failed: {error_msg}"
                )
                return False


            # 执行健康检查请求
            start_time = datetime.utcnow()
            test_request = ChatCompletionRequest(
                messages=[ChatMessage(role="user", content="ping")],
                max_tokens=5,
                temperature=0.1
            )

            try:
                response = await asyncio.wait_for(
                    provider.chat(test_request),
                    timeout=self.config.TIMEOUT
                )
                end_time = datetime.utcnow()

                # 计算响应时间
                response_time = (end_time - start_time).total_seconds() * 1000

                # 记录成功
                config.record_success(response_time)

                # 检查响应时间是否超过阈值
                if response_time > self.config.RESPONSE_TIME_THRESHOLD:
                    logger.warning(
                        f"Provider {config.provider} (ID: {config.id}) "
                        f"response time {response_time:.2f}ms exceeds threshold"
                    )
                    config.health_status = HealthStatus.DEGRADED.value
                else:
                    config.health_status = HealthStatus.HEALTHY.value

                # 如果之前有熔断器，现在恢复了，关闭熔断器
                if config.circuit_breaker_open_until:
                    config.close_circuit_breaker()
                    logger.info(
                        f"Provider {config.provider} (ID: {config.id}) "
                        f"circuit breaker closed"
                    )

                config.last_check_time = datetime.utcnow()
                self.db.commit()

                logger.info(
                    f"Provider {config.provider} (ID: {config.id}) "
                    f"health check passed, response time: {response_time:.2f}ms"
                )
                return True

            except asyncio.TimeoutError:
                error_msg = f"Health check timeout after {self.config.TIMEOUT}s"
                config.record_failure(error_msg)
                config.update_health_status()

                # 检查是否需要开启熔断器
                if config.error_count >= self.config.CONSECUTIVE_ERROR_THRESHOLD:
                    config.open_circuit_breaker(self.config.CIRCUIT_BREAKER_DURATION)
                    logger.error(
                        f"Provider {config.provider} (ID: {config.id}) "
                        f"circuit breaker opened due to consecutive errors"
                    )

                config.last_check_time = datetime.utcnow()
                self.db.commit()

                logger.error(
                    f"Provider {config.provider} (ID: {config.id}) "
                    f"health check failed: {error_msg}"
                )
                return False

            except Exception as e:
                error_msg = str(e)
                config.record_failure(error_msg)
                config.update_health_status()

                # 检查是否需要开启熔断器
                if config.error_count >= self.config.CONSECUTIVE_ERROR_THRESHOLD:
                    config.open_circuit_breaker(self.config.CIRCUIT_BREAKER_DURATION)
                    logger.error(
                        f"Provider {config.provider} (ID: {config.id}) "
                        f"circuit breaker opened due to consecutive errors"
                    )

                config.last_check_time = datetime.utcnow()
                self.db.commit()

                logger.error(
                    f"Provider {config.provider} (ID: {config.id}) "
                    f"health check failed: {error_msg}"
                )
                return False

        except Exception as e:
            logger.error(
                f"Error checking provider {config.provider} (ID: {config.id}): {e}"
            )
            return False

    async def check_all_providers(self):
        """检查所有活跃的Provider"""
        try:
            # 获取所有活跃的配置
            configs = self.db.query(TenantAIConfig).filter(
                TenantAIConfig.is_active == True,
                TenantAIConfig.deleted_at.is_(None)
            ).all()

            logger.info(f"Starting health check for {len(configs)} providers")

            # 并发检查所有Provider
            tasks = []
            for config in configs:
                # 这里需要解密API密钥
                # 实际实现中应该使用加密服务解密
                try:
                    api_key = decrypt_api_key(config.api_key_encrypted)
                except Exception as e:
                    logger.error(f"Failed to decrypt API key for provider {config.id}: {e}")
                    continue
                tasks.append(self.check_provider_health(config, api_key))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # BUG FIX: Only count True results, not Exception objects
            healthy_count = sum(1 for r in results if r is True)
            logger.info(
                f"Health check completed: {healthy_count}/{len(tasks)} providers healthy"
            )

        except Exception as e:
            logger.error(f"Error in check_all_providers: {e}")

    async def start_periodic_check(self):
        """启动定期健康检查"""
        self._running = True
        logger.info(
            f"Starting periodic health check, interval: {self.config.CHECK_INTERVAL}s"
        )

        while self._running:
            try:
                await self.check_all_providers()
            except Exception as e:
                logger.error(f"Error in periodic health check: {e}")

            # 等待下一次检查
            await asyncio.sleep(self.config.CHECK_INTERVAL)

    def stop_periodic_check(self):
        """停止定期健康检查"""
        self._running = False
        logger.info("Stopping periodic health check")

    async def check_and_recover_circuit_breakers(self):
        """检查并恢复熔断器

        对于熔断器已过期的Provider，尝试恢复
        """
        try:
            now = datetime.utcnow()
            configs = self.db.query(TenantAIConfig).filter(
                TenantAIConfig.circuit_breaker_open_until.isnot(None),
                TenantAIConfig.circuit_breaker_open_until <= now,
                TenantAIConfig.deleted_at.is_(None)
            ).all()

            logger.info(f"Found {len(configs)} providers with expired circuit breakers")

            for config in configs:
                logger.info(
                    f"Attempting to recover provider {config.provider} (ID: {config.id})"
                )

                # 尝试健康检查
                try:
                    api_key = decrypt_api_key(config.api_key_encrypted)
                except Exception as e:
                    logger.error(f"Failed to decrypt API key for provider {config.id}: {e}")
                    config.open_circuit_breaker(self.config.CIRCUIT_BREAKER_DURATION)
                    self.db.commit()
                    continue
                is_healthy = await self.check_provider_health(config, api_key)

                if is_healthy:
                    # BUG FIX: Add missing commit after successful recovery
                    self.db.commit()
                    logger.info(
                        f"Provider {config.provider} (ID: {config.id}) recovered"
                    )
                else:
                    # 如果仍然不健康，延长熔断时间
                    config.open_circuit_breaker(self.config.CIRCUIT_BREAKER_DURATION)
                    self.db.commit()
                    logger.warning(
                        f"Provider {config.provider} (ID: {config.id}) "
                        f"still unhealthy, circuit breaker extended"
                    )

        except Exception as e:
            logger.error(f"Error in check_and_recover_circuit_breakers: {e}")

    def get_provider_statistics(self, config_id: int) -> dict:
        """获取Provider统计信息

        Args:
            config_id: 配置ID

        Returns:
            dict: 统计信息
        """
        try:
            config = self.db.query(TenantAIConfig).filter(
                TenantAIConfig.id == config_id
            ).first()

            if not config:
                return {}

            return {
                "provider": config.provider,
                "health_status": config.health_status,
                "is_active": config.is_active,
                "priority": config.priority,
                "total_requests": config.total_requests,
                "failed_requests": config.failed_requests,
                "error_rate": config.get_error_rate(),
                "avg_response_time": config.avg_response_time,
                "error_count": config.error_count,
                "last_check_time": config.last_check_time.isoformat() if config.last_check_time else None,
                "last_error_time": config.last_error_time.isoformat() if config.last_error_time else None,
                "last_error_message": config.last_error_message,
                "is_circuit_breaker_open": config.is_circuit_breaker_open(),
                "circuit_breaker_open_until": config.circuit_breaker_open_until.isoformat() if config.circuit_breaker_open_until else None,
            }

        except Exception as e:
            logger.error(f"Error getting provider statistics: {e}")
            return {}
