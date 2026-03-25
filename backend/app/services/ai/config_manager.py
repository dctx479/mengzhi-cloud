"""
故障转移配置管理服务

功能:
- 配置Provider优先级
- 配置故障转移策略
- 配置健康检查参数
- 配置告警规则
"""
from typing import Optional, Dict, Any, List
from loguru import logger
from sqlalchemy.orm import Session

from app.models.tenant_ai_config import TenantAIConfig, HealthStatus
from .failover import FailoverStrategy


class FailoverConfig:
    """故障转移配置"""

    def __init__(
        self,
        strategy: FailoverStrategy = FailoverStrategy.PRIORITY_BASED,
        max_retries: int = 3,
        health_check_interval: int = 60,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_duration: int = 300,
        error_rate_warning_threshold: float = 10.0,
        error_rate_critical_threshold: float = 30.0,
        response_time_warning_threshold: float = 3000.0,
        response_time_critical_threshold: float = 5000.0,
    ):
        self.strategy = strategy
        self.max_retries = max_retries
        self.health_check_interval = health_check_interval
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_duration = circuit_breaker_duration
        self.error_rate_warning_threshold = error_rate_warning_threshold
        self.error_rate_critical_threshold = error_rate_critical_threshold
        self.response_time_warning_threshold = response_time_warning_threshold
        self.response_time_critical_threshold = response_time_critical_threshold

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "strategy": self.strategy.value,
            "max_retries": self.max_retries,
            "health_check_interval": self.health_check_interval,
            "circuit_breaker_threshold": self.circuit_breaker_threshold,
            "circuit_breaker_duration": self.circuit_breaker_duration,
            "error_rate_warning_threshold": self.error_rate_warning_threshold,
            "error_rate_critical_threshold": self.error_rate_critical_threshold,
            "response_time_warning_threshold": self.response_time_warning_threshold,
            "response_time_critical_threshold": self.response_time_critical_threshold,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FailoverConfig":
        """从字典创建配置"""
        return cls(
            strategy=FailoverStrategy(data.get("strategy", FailoverStrategy.PRIORITY_BASED.value)),
            max_retries=data.get("max_retries", 3),
            health_check_interval=data.get("health_check_interval", 60),
            circuit_breaker_threshold=data.get("circuit_breaker_threshold", 5),
            circuit_breaker_duration=data.get("circuit_breaker_duration", 300),
            error_rate_warning_threshold=data.get("error_rate_warning_threshold", 10.0),
            error_rate_critical_threshold=data.get("error_rate_critical_threshold", 30.0),
            response_time_warning_threshold=data.get("response_time_warning_threshold", 3000.0),
            response_time_critical_threshold=data.get("response_time_critical_threshold", 5000.0),
        )


class ConfigManager:
    """配置管理器"""

    def __init__(self, db: Session):
        self.db = db

    def set_provider_priority(
        self,
        config_id: int,
        priority: int
    ) -> bool:
        """设置Provider优先级

        Args:
            config_id: 配置ID
            priority: 优先级（0-100）

        Returns:
            bool: 是否成功
        """
        try:
            if not 0 <= priority <= 100:
                raise ValueError("Priority must be between 0 and 100")

            config = self.db.query(TenantAIConfig).filter(
                TenantAIConfig.id == config_id
            ).first()

            if not config:
                logger.error(f"Config {config_id} not found")
                return False

            config.priority = priority
            self.db.commit()

            logger.info(
                f"Set priority {priority} for provider {config.provider} (ID: {config_id})"
            )
            return True

        except Exception as e:
            logger.error(f"Error setting provider priority: {e}")
            self.db.rollback()
            return False

    def set_provider_active(
        self,
        config_id: int,
        is_active: bool
    ) -> bool:
        """设置Provider启用状态

        Args:
            config_id: 配置ID
            is_active: 是否启用

        Returns:
            bool: 是否成功
        """
        try:
            config = self.db.query(TenantAIConfig).filter(
                TenantAIConfig.id == config_id
            ).first()

            if not config:
                logger.error(f"Config {config_id} not found")
                return False

            config.is_active = is_active
            self.db.commit()

            logger.info(
                f"Set active={is_active} for provider {config.provider} (ID: {config_id})"
            )
            return True

        except Exception as e:
            logger.error(f"Error setting provider active status: {e}")
            self.db.rollback()
            return False

    def reset_provider_statistics(
        self,
        config_id: int
    ) -> bool:
        """重置Provider统计信息

        Args:
            config_id: 配置ID

        Returns:
            bool: 是否成功
        """
        try:
            config = self.db.query(TenantAIConfig).filter(
                TenantAIConfig.id == config_id
            ).first()

            if not config:
                logger.error(f"Config {config_id} not found")
                return False

            config.total_requests = 0
            config.failed_requests = 0
            config.error_count = 0
            config.avg_response_time = None
            config.last_error_message = None
            config.last_error_time = None
            config.health_status = HealthStatus.HEALTHY.value
            config.close_circuit_breaker()

            self.db.commit()

            logger.info(
                f"Reset statistics for provider {config.provider} (ID: {config_id})"
            )
            return True

        except Exception as e:
            logger.error(f"Error resetting provider statistics: {e}")
            self.db.rollback()
            return False

    def force_close_circuit_breaker(
        self,
        config_id: int
    ) -> bool:
        """强制关闭熔断器

        Args:
            config_id: 配置ID

        Returns:
            bool: 是否成功
        """
        try:
            config = self.db.query(TenantAIConfig).filter(
                TenantAIConfig.id == config_id
            ).first()

            if not config:
                logger.error(f"Config {config_id} not found")
                return False

            config.close_circuit_breaker()
            self.db.commit()

            logger.info(
                f"Force closed circuit breaker for provider {config.provider} (ID: {config_id})"
            )
            return True

        except Exception as e:
            logger.error(f"Error closing circuit breaker: {e}")
            self.db.rollback()
            return False

    def batch_set_priorities(
        self,
        enterprise_id: int,
        priorities: Dict[int, int]
    ) -> bool:
        """批量设置Provider优先级

        Args:
            enterprise_id: 企业ID
            priorities: 配置ID -> 优先级的映射

        Returns:
            bool: 是否成功
        """
        try:
            for config_id, priority in priorities.items():
                if not 0 <= priority <= 100:
                    raise ValueError(f"Priority {priority} must be between 0 and 100")

                config = self.db.query(TenantAIConfig).filter(
                    TenantAIConfig.id == config_id,
                    TenantAIConfig.enterprise_id == enterprise_id
                ).first()

                if not config:
                    logger.warning(f"Config {config_id} not found or not owned by enterprise {enterprise_id}")
                    continue

                config.priority = priority

            self.db.commit()

            logger.info(
                f"Batch set priorities for {len(priorities)} providers in enterprise {enterprise_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error batch setting priorities: {e}")
            self.db.rollback()
            return False

    def get_provider_config(
        self,
        config_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取Provider配置

        Args:
            config_id: 配置ID

        Returns:
            Optional[Dict[str, Any]]: 配置信息
        """
        try:
            config = self.db.query(TenantAIConfig).filter(
                TenantAIConfig.id == config_id
            ).first()

            if not config:
                return None

            return config.to_dict()

        except Exception as e:
            logger.error(f"Error getting provider config: {e}")
            return None

    def list_enterprise_providers(
        self,
        enterprise_id: int,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """列出企业的所有Provider

        Args:
            enterprise_id: 企业ID
            include_inactive: 是否包含未启用的Provider

        Returns:
            List[Dict[str, Any]]: Provider列表
        """
        try:
            query = self.db.query(TenantAIConfig).filter(
                TenantAIConfig.enterprise_id == enterprise_id,
                TenantAIConfig.deleted_at.is_(None)
            )

            if not include_inactive:
                query = query.filter(TenantAIConfig.is_active == True)

            configs = query.order_by(TenantAIConfig.priority.desc()).all()

            return [config.to_dict() for config in configs]

        except Exception as e:
            logger.error(f"Error listing enterprise providers: {e}")
            return []

    def get_recommended_priorities(
        self,
        enterprise_id: int
    ) -> Dict[int, int]:
        """获取推荐的优先级配置

        基于Provider的性能指标推荐优先级

        Args:
            enterprise_id: 企业ID

        Returns:
            Dict[int, int]: 配置ID -> 推荐优先级的映射
        """
        try:
            configs = self.db.query(TenantAIConfig).filter(
                TenantAIConfig.enterprise_id == enterprise_id,
                TenantAIConfig.is_active == True,
                TenantAIConfig.deleted_at.is_(None)
            ).all()

            if not configs:
                return {}

            # 计算每个Provider的得分
            scores = {}
            for config in configs:
                score = 0.0

                # 健康状态得分（40%）
                if config.health_status == HealthStatus.HEALTHY.value:
                    score += 40
                elif config.health_status == HealthStatus.DEGRADED.value:
                    score += 20

                # 错误率得分（30%）
                error_rate = config.get_error_rate()
                score += (100 - min(error_rate, 100)) * 0.3

                # 响应时间得分（20%）
                if config.avg_response_time:
                    response_score = max(0, 100 - (config.avg_response_time / 50))
                    score += response_score * 0.2
                else:
                    score += 20  # 默认得分

                # 可用性得分（10%）
                if config.total_requests > 0:
                    availability = (config.total_requests - config.failed_requests) / config.total_requests
                    score += availability * 10

                scores[config.id] = score

            # 归一化到0-100
            max_score = max(scores.values()) if scores else 1
            min_score = min(scores.values()) if scores else 0
            score_range = max_score - min_score if max_score > min_score else 1

            priorities = {}
            for config_id, score in scores.items():
                normalized_score = ((score - min_score) / score_range) * 100
                priorities[config_id] = int(normalized_score)

            logger.info(
                f"Generated recommended priorities for {len(priorities)} providers "
                f"in enterprise {enterprise_id}"
            )

            return priorities

        except Exception as e:
            logger.error(f"Error getting recommended priorities: {e}")
            return {}

    def apply_recommended_priorities(
        self,
        enterprise_id: int
    ) -> bool:
        """应用推荐的优先级配置

        Args:
            enterprise_id: 企业ID

        Returns:
            bool: 是否成功
        """
        try:
            priorities = self.get_recommended_priorities(enterprise_id)

            if not priorities:
                logger.warning(f"No recommended priorities for enterprise {enterprise_id}")
                return False

            return self.batch_set_priorities(enterprise_id, priorities)

        except Exception as e:
            logger.error(f"Error applying recommended priorities: {e}")
            return False

    def export_config(
        self,
        enterprise_id: int
    ) -> Dict[str, Any]:
        """导出企业的故障转移配置

        Args:
            enterprise_id: 企业ID

        Returns:
            Dict[str, Any]: 配置数据
        """
        try:
            from datetime import datetime
            providers = self.list_enterprise_providers(enterprise_id, include_inactive=True)

            logger.info(f"Exporting config for enterprise {enterprise_id}")

            return {
                "enterprise_id": enterprise_id,
                "providers": providers,
                "exported_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error exporting config: {e}")
            return {}

    def import_config(
        self,
        enterprise_id: int,
        config_data: Dict[str, Any]
    ) -> bool:
        """导入企业的故障转移配置

        Args:
            enterprise_id: 企业ID
            config_data: 配置数据

        Returns:
            bool: 是否成功
        """
        try:
            providers = config_data.get("providers", [])

            for provider_data in providers:
                config_id = provider_data.get("id")
                if not config_id:
                    continue

                config = self.db.query(TenantAIConfig).filter(
                    TenantAIConfig.id == config_id,
                    TenantAIConfig.enterprise_id == enterprise_id
                ).first()

                if not config:
                    logger.warning(f"Config {config_id} not found")
                    continue

                # 更新配置
                if "priority" in provider_data:
                    config.priority = provider_data["priority"]
                if "is_active" in provider_data:
                    config.is_active = provider_data["is_active"]

            self.db.commit()

            logger.info(f"Imported config for enterprise {enterprise_id}")
            return True

        except Exception as e:
            logger.error(f"Error importing config: {e}")
            self.db.rollback()
            return False
