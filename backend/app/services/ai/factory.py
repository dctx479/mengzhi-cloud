"""
AI Provider 工厂类

支持:
- Provider实例创建和缓存
- 故障转移
- 自动重试
- 健康检查集成
"""
import time
import threading
from typing import Dict, Type, Optional, Tuple
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session

from .base_provider import BaseAIProvider, ChatCompletionRequest, ChatCompletionResponse
from .providers.deepseek_provider import DeepSeekProvider
from .providers.openai_provider import OpenAIProvider
from .failover import FailoverManager, FailoverStrategy
from app.models.tenant_ai_config import TenantAIConfig
from app.core.security import decrypt_api_key


class AIProviderFactory:
    """AI Provider 工厂

    集成故障转移和自动重试功能
    """

    _providers: Dict[str, Type[BaseAIProvider]] = {
        "deepseek": DeepSeekProvider,
        "openai": OpenAIProvider,
        # 国产模型 - 使用 OpenAI 兼容接口
        "qwen": OpenAIProvider,       # 通义千问 (阿里)
        "glm": OpenAIProvider,         # 智谱GLM
        "moonshot": OpenAIProvider,    # 月之暗面
        "wenxin": OpenAIProvider,      # 文心一言 (百度) - 需配置endpoint
        "spark": OpenAIProvider,       # 讯飞星火 - 需配置endpoint
        "anthropic": OpenAIProvider,   # Anthropic
        "azure": OpenAIProvider,       # Azure OpenAI
        "custom": OpenAIProvider,      # 自定义
    }

    _instances: Dict[str, BaseAIProvider] = {}
    # 保护 _instances 字典的并发写入
    _instances_lock: threading.Lock = threading.Lock()

    @classmethod
    def create(
        cls,
        provider_type: str,
        api_key: str,
        base_url: Optional[str] = None,
        **kwargs
    ) -> BaseAIProvider:
        """创建Provider实例（带缓存，线程安全）

        Args:
            provider_type: Provider类型
            api_key: API密钥
            base_url: 自定义API地址
            **kwargs: 其他参数

        Returns:
            BaseAIProvider: Provider实例
        """
        import hashlib as _hashlib
        # 用完整 api_key 的 SHA-256 前 16 字节作为缓存键，避免尾部 8 字符碰撞
        _key_hash = _hashlib.sha256(api_key.encode()).hexdigest()[:16]
        cache_key = f"{provider_type}:{_key_hash}"

        # 先不加锁检查（快速路径）
        if cache_key in cls._instances:
            return cls._instances[cache_key]

        # 加锁后再次检查，防止并发重复创建
        with cls._instances_lock:
            if cache_key in cls._instances:
                return cls._instances[cache_key]

            if provider_type not in cls._providers:
                raise ValueError(f"Unknown provider: {provider_type}")

            provider_class = cls._providers[provider_type]
            cls._instances[cache_key] = provider_class(
                api_key=api_key,
                base_url=base_url,
                **kwargs
            )

        return cls._instances[cache_key]

    @classmethod
    def create_from_config(
        cls,
        config: TenantAIConfig,
        api_key: str
    ) -> BaseAIProvider:
        """从配置创建Provider实例

        Args:
            config: AI配置
            api_key: 解密后的API密钥

        Returns:
            BaseAIProvider: Provider实例
        """
        return cls.create(
            provider_type=config.provider,
            api_key=api_key,
            base_url=config.base_url
        )

    @classmethod
    async def chat_with_failover(
        cls,
        db: Session,
        enterprise_id: int,
        request: ChatCompletionRequest,
        strategy: FailoverStrategy = FailoverStrategy.PRIORITY_BASED,
        max_retries: int = 3,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_duration: int = 300,
    ) -> Tuple[ChatCompletionResponse, TenantAIConfig]:
        """带故障转移的对话请求

        Args:
            db: 数据库会话
            enterprise_id: 企业ID
            request: 对话请求
            strategy: 故障转移策略
            max_retries: 最大重试次数
            circuit_breaker_threshold: 触发熔断的连续失败次数
            circuit_breaker_duration: 熔断持续时间（秒）

        Returns:
            Tuple[ChatCompletionResponse, TenantAIConfig]: 响应和使用的配置

        Raises:
            Exception: 所有Provider都失败时抛出异常
        """
        failover_manager = FailoverManager(db)
        last_error = None
        failed_config_id = None
        config = None

        for attempt in range(max_retries):
            try:
                # 选择Provider
                if attempt == 0:
                    config = failover_manager.select_provider(enterprise_id, strategy)
                else:
                    # 故障转移
                    config = failover_manager.retry_with_failover(
                        enterprise_id=enterprise_id,
                        failed_config_id=failed_config_id,
                        strategy=strategy,
                        max_retries=1
                    )

                if not config:
                    raise Exception("No available provider found")

                logger.info(
                    f"Attempt {attempt + 1}/{max_retries}: Using provider "
                    f"{config.provider} (ID: {config.id}) for enterprise {enterprise_id}"
                )

                # 检查熔断器
                if config.is_circuit_breaker_open():
                    logger.warning(
                        f"Provider {config.provider} (ID: {config.id}) "
                        f"circuit breaker is open, skipping"
                    )
                    failed_config_id = config.id
                    continue

                # 创建Provider实例
                # 解密API密钥
                try:
                    api_key = decrypt_api_key(config.api_key_encrypted)
                except Exception as decrypt_err:
                    logger.error(f"Failed to decrypt API key for provider {config.id}: {decrypt_err}")
                    config.record_failure(f"API key decryption failed: {decrypt_err}")
                    config.update_health_status()
                    db.commit()
                    failed_config_id = config.id
                    continue
                provider = cls.create_from_config(config, api_key)

                # 执行请求
                start_time = time.time()
                response = await provider.chat(request)
                end_time = time.time()

                # 计算响应时间（毫秒）
                response_time = (end_time - start_time) * 1000

                # 记录成功
                config.record_success(response_time)
                config.update_health_status()
                db.commit()

                logger.info(
                    f"Request succeeded with provider {config.provider} "
                    f"(ID: {config.id}), response time: {response_time:.2f}ms"
                )

                return response, config

            except Exception as e:
                last_error = e
                logger.error(
                    f"Request failed with provider {config.provider if config else 'unknown'} "
                    f"(attempt {attempt + 1}/{max_retries}): {e}"
                )

                if config:
                    # 记录失败
                    config.record_failure(str(e))
                    config.update_health_status()

                    # 检查是否需要开启熔断器
                    if config.error_count >= circuit_breaker_threshold:
                        config.open_circuit_breaker(duration_seconds=circuit_breaker_duration)
                        logger.error(
                            f"Circuit breaker opened for provider {config.provider} "
                            f"(ID: {config.id})"
                        )

                    db.commit()
                    failed_config_id = config.id

                # 如果是最后一次尝试，抛出异常
                if attempt == max_retries - 1:
                    raise Exception(
                        f"All providers failed after {max_retries} attempts. "
                        f"Last error: {last_error}"
                    )

        # 不应该到达这里
        raise Exception(f"Unexpected error in chat_with_failover: {last_error}")

    @classmethod
    async def chat_stream_with_failover(
        cls,
        db: Session,
        enterprise_id: int,
        request: ChatCompletionRequest,
        strategy: FailoverStrategy = FailoverStrategy.PRIORITY_BASED,
        max_retries: int = 3,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_duration: int = 300,
    ):
        """带故障转移的流式对话请求

        Args:
            db: 数据库会话
            enterprise_id: 企业ID
            request: 对话请求
            strategy: 故障转移策略
            max_retries: 最大重试次数

        Yields:
            str: 流式响应内容

        Raises:
            Exception: 所有Provider都失败时抛出异常（仅在第一个 chunk yield 之前）
        """
        failover_manager = FailoverManager(db)
        last_error = None
        failed_config_id = None
        config = None

        for attempt in range(max_retries):
            # --- Provider 选择阶段（yield 之前，异常可以正常传播）---
            try:
                if attempt == 0:
                    config = failover_manager.select_provider(enterprise_id, strategy)
                else:
                    config = failover_manager.retry_with_failover(
                        enterprise_id=enterprise_id,
                        failed_config_id=failed_config_id,
                        strategy=strategy,
                        max_retries=1
                    )

                if not config:
                    raise Exception("No available provider found")

                logger.info(
                    f"Attempt {attempt + 1}/{max_retries}: Using provider "
                    f"{config.provider} (ID: {config.id}) for enterprise {enterprise_id}"
                )

                if config.is_circuit_breaker_open():
                    logger.warning(
                        f"Provider {config.provider} (ID: {config.id}) "
                        f"circuit breaker is open, skipping"
                    )
                    failed_config_id = config.id
                    last_error = Exception(f"Circuit breaker open for provider {config.provider}")
                    continue

                try:
                    api_key = decrypt_api_key(config.api_key_encrypted)
                except Exception as decrypt_err:
                    logger.error(f"Failed to decrypt API key for provider {config.id}: {decrypt_err}")
                    config.record_failure(f"API key decryption failed: {decrypt_err}")
                    config.update_health_status()
                    db.commit()
                    failed_config_id = config.id
                    last_error = decrypt_err
                    continue

                provider = cls.create_from_config(config, api_key)

            except Exception as e:
                last_error = e
                logger.error(
                    f"Provider selection failed (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt == max_retries - 1:
                    raise Exception(
                        f"All providers failed after {max_retries} attempts. "
                        f"Last error: {last_error}"
                    )
                continue

            # --- 流式迭代阶段（yield 之后异常会直接传播给调用方）---
            start_time = time.time()
            chunk_count = 0
            stream_error = None

            try:
                async for chunk in provider.chat_stream(request):
                    chunk_count += 1
                    yield chunk
            except Exception as e:
                stream_error = e

            end_time = time.time()
            response_time = (end_time - start_time) * 1000

            if stream_error is None:
                # 流式成功完成
                config.record_success(response_time)
                config.update_health_status()
                db.commit()
                logger.info(
                    f"Stream request succeeded with provider {config.provider} "
                    f"(ID: {config.id}), chunks: {chunk_count}, "
                    f"response time: {response_time:.2f}ms"
                )
                return

            # 流中途失败：记录错误，尝试下一个 provider
            last_error = stream_error
            logger.error(
                f"Stream request failed with provider {config.provider} "
                f"(attempt {attempt + 1}/{max_retries}): {stream_error}"
            )
            config.record_failure(str(stream_error))
            config.update_health_status()
            if config.error_count >= circuit_breaker_threshold:
                config.open_circuit_breaker(duration_seconds=circuit_breaker_duration)
                logger.error(
                    f"Circuit breaker opened for provider {config.provider} "
                    f"(ID: {config.id})"
                )
            db.commit()
            failed_config_id = config.id

            # 如果已经 yield 了部分数据，无法重试（调用方已收到部分响应）
            if chunk_count > 0:
                raise Exception(
                    f"Stream interrupted after {chunk_count} chunks: {stream_error}"
                )

            if attempt == max_retries - 1:
                raise Exception(
                    f"All providers failed after {max_retries} attempts. "
                    f"Last error: {last_error}"
                )

        raise Exception(f"Unexpected error in chat_stream_with_failover: {last_error}")

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """获取支持的Provider列表"""
        return list(cls._providers.keys())

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseAIProvider]):
        """注册新的Provider"""
        cls._providers[name] = provider_class

    @classmethod
    def clear_cache(cls):
        """清除Provider实例缓存"""
        with cls._instances_lock:
            cls._instances.clear()
        logger.info("Provider instance cache cleared")
