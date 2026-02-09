"""
AI Provider 故障转移策略

支持多种故障转移策略:
- 主备模式（Primary-Backup）
- 轮询模式（Round-Robin）
- 加权轮询（Weighted Round-Robin）
- 最少连接（Least Connections）
"""
import enum
from typing import List, Optional
from loguru import logger
from sqlalchemy.orm import Session

from app.models.tenant_ai_config import TenantAIConfig, HealthStatus


class FailoverStrategy(enum.Enum):
    """故障转移策略枚举"""
    PRIMARY_BACKUP = "primary_backup"  # 主备模式
    ROUND_ROBIN = "round_robin"  # 轮询模式
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"  # 加权轮询
    LEAST_CONNECTIONS = "least_connections"  # 最少连接
    PRIORITY_BASED = "priority_based"  # 基于优先级


class FailoverManager:
    """故障转移管理器"""

    def __init__(self, db: Session):
        self.db = db
        self._round_robin_index = {}  # 企业ID -> 当前索引

    def get_available_providers(
        self,
        enterprise_id: int,
        include_degraded: bool = False
    ) -> List[TenantAIConfig]:
        """获取可用的Provider列表

        Args:
            enterprise_id: 企业ID
            include_degraded: 是否包含降级状态的Provider

        Returns:
            List[TenantAIConfig]: 可用的Provider列表
        """
        query = self.db.query(TenantAIConfig).filter(
            TenantAIConfig.enterprise_id == enterprise_id,
            TenantAIConfig.is_active == True,
            TenantAIConfig.deleted_at.is_(None)
        )

        # 排除熔断器开启的Provider
        configs = [c for c in query.all() if not c.is_circuit_breaker_open()]

        # 根据健康状态过滤
        if include_degraded:
            configs = [
                c for c in configs
                if c.health_status in [HealthStatus.HEALTHY.value, HealthStatus.DEGRADED.value]
            ]
        else:
            configs = [
                c for c in configs
                if c.health_status == HealthStatus.HEALTHY.value
            ]

        return configs

    def select_provider_primary_backup(
        self,
        enterprise_id: int
    ) -> Optional[TenantAIConfig]:
        """主备模式选择Provider

        选择优先级最高的健康Provider
        如果主Provider不可用，自动切换到备用Provider

        Args:
            enterprise_id: 企业ID

        Returns:
            Optional[TenantAIConfig]: 选中的Provider配置
        """
        # 先尝试获取健康的Provider
        configs = self.get_available_providers(enterprise_id, include_degraded=False)

        # 如果没有健康的，尝试降级的
        if not configs:
            logger.warning(
                f"No healthy providers for enterprise {enterprise_id}, "
                f"trying degraded providers"
            )
            configs = self.get_available_providers(enterprise_id, include_degraded=True)

        if not configs:
            logger.error(f"No available providers for enterprise {enterprise_id}")
            return None

        # 按优先级排序，选择最高优先级的
        configs.sort(key=lambda x: x.priority, reverse=True)
        selected = configs[0]

        logger.info(
            f"Selected provider {selected.provider} (ID: {selected.id}, "
            f"priority: {selected.priority}) for enterprise {enterprise_id}"
        )

        return selected

    def select_provider_round_robin(
        self,
        enterprise_id: int
    ) -> Optional[TenantAIConfig]:
        """轮询模式选择Provider

        在所有健康的Provider之间轮询

        Args:
            enterprise_id: 企业ID

        Returns:
            Optional[TenantAIConfig]: 选中的Provider配置
        """
        configs = self.get_available_providers(enterprise_id, include_degraded=False)

        if not configs:
            logger.warning(
                f"No healthy providers for enterprise {enterprise_id}, "
                f"trying degraded providers"
            )
            configs = self.get_available_providers(enterprise_id, include_degraded=True)

        if not configs:
            logger.error(f"No available providers for enterprise {enterprise_id}")
            return None

        # 按ID排序以保证顺序一致
        configs.sort(key=lambda x: x.id)

        # 获取当前索引
        current_index = self._round_robin_index.get(enterprise_id, 0)

        # 选择Provider
        selected = configs[current_index % len(configs)]

        # 更新索引
        self._round_robin_index[enterprise_id] = (current_index + 1) % len(configs)

        logger.info(
            f"Selected provider {selected.provider} (ID: {selected.id}) "
            f"for enterprise {enterprise_id} using round-robin"
        )

        return selected

    def select_provider_weighted_round_robin(
        self,
        enterprise_id: int
    ) -> Optional[TenantAIConfig]:
        """加权轮询模式选择Provider

        根据优先级权重进行轮询

        Args:
            enterprise_id: 企业ID

        Returns:
            Optional[TenantAIConfig]: 选中的Provider配置
        """
        configs = self.get_available_providers(enterprise_id, include_degraded=False)

        if not configs:
            logger.warning(
                f"No healthy providers for enterprise {enterprise_id}, "
                f"trying degraded providers"
            )
            configs = self.get_available_providers(enterprise_id, include_degraded=True)

        if not configs:
            logger.error(f"No available providers for enterprise {enterprise_id}")
            return None

        # 计算总权重
        total_weight = sum(max(c.priority, 1) for c in configs)

        # 获取当前索引
        current_index = self._round_robin_index.get(enterprise_id, 0)

        # 根据权重选择
        target = current_index % total_weight
        cumulative_weight = 0

        for config in configs:
            weight = max(config.priority, 1)
            cumulative_weight += weight
            if cumulative_weight > target:
                selected = config
                break
        else:
            selected = configs[0]

        # 更新索引
        self._round_robin_index[enterprise_id] = current_index + 1

        logger.info(
            f"Selected provider {selected.provider} (ID: {selected.id}, "
            f"priority: {selected.priority}) for enterprise {enterprise_id} "
            f"using weighted round-robin"
        )

        return selected

    def select_provider_least_connections(
        self,
        enterprise_id: int
    ) -> Optional[TenantAIConfig]:
        """最少连接模式选择Provider

        选择当前请求数最少的Provider

        Args:
            enterprise_id: 企业ID

        Returns:
            Optional[TenantAIConfig]: 选中的Provider配置
        """
        configs = self.get_available_providers(enterprise_id, include_degraded=False)

        if not configs:
            logger.warning(
                f"No healthy providers for enterprise {enterprise_id}, "
                f"trying degraded providers"
            )
            configs = self.get_available_providers(enterprise_id, include_degraded=True)

        if not configs:
            logger.error(f"No available providers for enterprise {enterprise_id}")
            return None

        # 选择总请求数最少的
        selected = min(configs, key=lambda x: x.total_requests)

        logger.info(
            f"Selected provider {selected.provider} (ID: {selected.id}, "
            f"total_requests: {selected.total_requests}) for enterprise {enterprise_id} "
            f"using least connections"
        )

        return selected

    def select_provider_priority_based(
        self,
        enterprise_id: int
    ) -> Optional[TenantAIConfig]:
        """基于优先级选择Provider

        综合考虑优先级、健康状态、响应时间等因素

        Args:
            enterprise_id: 企业ID

        Returns:
            Optional[TenantAIConfig]: 选中的Provider配置
        """
        configs = self.get_available_providers(enterprise_id, include_degraded=True)

        if not configs:
            logger.error(f"No available providers for enterprise {enterprise_id}")
            return None

        # 计算每个Provider的得分
        def calculate_score(config: TenantAIConfig) -> float:
            score = 0.0

            # 优先级权重 (40%)
            score += config.priority * 0.4

            # 健康状态权重 (30%)
            if config.health_status == HealthStatus.HEALTHY.value:
                score += 30
            elif config.health_status == HealthStatus.DEGRADED.value:
                score += 15

            # 错误率权重 (20%)
            error_rate = config.get_error_rate()
            score += (100 - error_rate) * 0.2

            # 响应时间权重 (10%)
            if config.avg_response_time:
                # 响应时间越短得分越高
                response_score = max(0, 100 - (config.avg_response_time / 50))
                score += response_score * 0.1

            return score

        # 选择得分最高的
        selected = max(configs, key=calculate_score)

        logger.info(
            f"Selected provider {selected.provider} (ID: {selected.id}, "
            f"priority: {selected.priority}, score: {calculate_score(selected):.2f}) "
            f"for enterprise {enterprise_id} using priority-based strategy"
        )

        return selected

    def select_provider(
        self,
        enterprise_id: int,
        strategy: FailoverStrategy = FailoverStrategy.PRIORITY_BASED
    ) -> Optional[TenantAIConfig]:
        """根据策略选择Provider

        Args:
            enterprise_id: 企业ID
            strategy: 故障转移策略

        Returns:
            Optional[TenantAIConfig]: 选中的Provider配置
        """
        try:
            if strategy == FailoverStrategy.PRIMARY_BACKUP:
                return self.select_provider_primary_backup(enterprise_id)
            elif strategy == FailoverStrategy.ROUND_ROBIN:
                return self.select_provider_round_robin(enterprise_id)
            elif strategy == FailoverStrategy.WEIGHTED_ROUND_ROBIN:
                return self.select_provider_weighted_round_robin(enterprise_id)
            elif strategy == FailoverStrategy.LEAST_CONNECTIONS:
                return self.select_provider_least_connections(enterprise_id)
            elif strategy == FailoverStrategy.PRIORITY_BASED:
                return self.select_provider_priority_based(enterprise_id)
            else:
                logger.error(f"Unknown failover strategy: {strategy}")
                return self.select_provider_priority_based(enterprise_id)

        except Exception as e:
            logger.error(f"Error selecting provider: {e}")
            return None

    def retry_with_failover(
        self,
        enterprise_id: int,
        failed_config_id: int,
        strategy: FailoverStrategy = FailoverStrategy.PRIORITY_BASED,
        max_retries: int = 3
    ) -> Optional[TenantAIConfig]:
        """失败重试并故障转移

        Args:
            enterprise_id: 企业ID
            failed_config_id: 失败的配置ID
            strategy: 故障转移策略
            max_retries: 最大重试次数

        Returns:
            Optional[TenantAIConfig]: 备用Provider配置
        """
        logger.warning(
            f"Provider {failed_config_id} failed, attempting failover "
            f"for enterprise {enterprise_id}"
        )

        # 获取所有可用的Provider（排除失败的）
        configs = self.get_available_providers(enterprise_id, include_degraded=True)
        configs = [c for c in configs if c.id != failed_config_id]

        if not configs:
            logger.error(
                f"No backup providers available for enterprise {enterprise_id}"
            )
            return None

        # 根据策略选择备用Provider
        for attempt in range(max_retries):
            backup = self.select_provider(enterprise_id, strategy)

            if backup and backup.id != failed_config_id:
                logger.info(
                    f"Failover to provider {backup.provider} (ID: {backup.id}) "
                    f"for enterprise {enterprise_id}, attempt {attempt + 1}"
                )
                return backup

        logger.error(
            f"Failed to find backup provider after {max_retries} attempts "
            f"for enterprise {enterprise_id}"
        )
        return None

    def get_failover_statistics(self, enterprise_id: int) -> dict:
        """获取故障转移统计信息

        Args:
            enterprise_id: 企业ID

        Returns:
            dict: 统计信息
        """
        try:
            configs = self.db.query(TenantAIConfig).filter(
                TenantAIConfig.enterprise_id == enterprise_id,
                TenantAIConfig.deleted_at.is_(None)
            ).all()

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
            circuit_breaker_open = sum(1 for c in configs if c.is_circuit_breaker_open())

            total_requests = sum(c.total_requests for c in configs)
            total_failures = sum(c.failed_requests for c in configs)
            overall_error_rate = (
                (total_failures / total_requests * 100) if total_requests > 0 else 0
            )

            return {
                "enterprise_id": enterprise_id,
                "total_providers": total_providers,
                "active_providers": active_providers,
                "healthy_providers": healthy_providers,
                "degraded_providers": degraded_providers,
                "unhealthy_providers": unhealthy_providers,
                "circuit_breaker_open": circuit_breaker_open,
                "total_requests": total_requests,
                "total_failures": total_failures,
                "overall_error_rate": round(overall_error_rate, 2),
                "providers": [
                    {
                        "id": c.id,
                        "provider": c.provider,
                        "priority": c.priority,
                        "health_status": c.health_status,
                        "is_active": c.is_active,
                        "error_rate": round(c.get_error_rate(), 2),
                        "avg_response_time": c.avg_response_time,
                        "is_circuit_breaker_open": c.is_circuit_breaker_open(),
                    }
                    for c in configs
                ]
            }

        except Exception as e:
            logger.error(f"Error getting failover statistics: {e}")
            return {}
