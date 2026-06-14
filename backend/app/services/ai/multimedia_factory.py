"""
多媒体 Provider 工厂

与 chat 语义的 AIProviderFactory (factory.py) 物理隔离: 复用其
「SHA-256 缓存键 + 线程锁 + create_from_config」模式, 但不带 chat 专属
的熔断/重试逻辑。用于统一注册、缓存、按租户配置解析多媒体 Provider。
"""
import hashlib
import threading
from typing import Dict, List, Optional, Type

from loguru import logger
from sqlalchemy.orm import Session

from app.core.security import decrypt_api_key
from app.models.tenant_ai_config import TenantAIConfig

from .multimedia_provider import MultimediaProvider
from .providers.jimeng_provider import JimengAI


class MultimediaProviderFactory:
    """多媒体 Provider 工厂 (含实例缓存)"""

    _providers: Dict[str, Type[MultimediaProvider]] = {
        "jimeng": JimengAI,
    }

    _instances: Dict[str, MultimediaProvider] = {}
    _instances_lock: threading.Lock = threading.Lock()

    @classmethod
    def create(
        cls,
        provider_type: str,
        api_key: str,
        base_url: Optional[str] = None,
        **kwargs,
    ) -> MultimediaProvider:
        """创建 Provider 实例 (带缓存, 线程安全)"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        cache_key = f"{provider_type}:{key_hash}"

        if cache_key in cls._instances:
            return cls._instances[cache_key]

        with cls._instances_lock:
            if cache_key in cls._instances:
                return cls._instances[cache_key]

            if provider_type not in cls._providers:
                raise ValueError(f"Unknown multimedia provider: {provider_type}")

            provider_class = cls._providers[provider_type]
            cls._instances[cache_key] = provider_class(api_key=api_key, base_url=base_url, **kwargs)

        return cls._instances[cache_key]

    @classmethod
    def create_from_config(cls, config: TenantAIConfig, api_key: str) -> MultimediaProvider:
        """从租户配置创建 Provider 实例 (api_key 须已解密)"""
        return cls.create(provider_type=config.provider, api_key=api_key, base_url=config.base_url)

    @classmethod
    def resolve_for_enterprise(
        cls,
        db: Session,
        enterprise_id: Optional[int] = None,
        provider_type: str = "jimeng",
    ) -> Optional[MultimediaProvider]:
        """按租户配置解析一个可用的多媒体 Provider 实例。

        查询 active 且匹配 provider_type 的 TenantAIConfig, 按 priority 降序取首条。
        enterprise_id 非 None 时才追加企业过滤 (None 表示不限企业, 取任一 active 配置)。

        无匹配配置返回 None; 有配置但解密失败时向上抛异常, 由调用方决定处理策略。
        """
        query = db.query(TenantAIConfig).filter(
            TenantAIConfig.provider == provider_type,
            TenantAIConfig.is_active == True,
        )
        if enterprise_id is not None:
            query = query.filter(TenantAIConfig.enterprise_id == enterprise_id)
        config = query.order_by(TenantAIConfig.priority.desc()).first()

        if not config:
            return None

        api_key = decrypt_api_key(config.api_key_encrypted)
        return cls.create_from_config(config, api_key)

    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """获取支持的多媒体 Provider 列表"""
        return list(cls._providers.keys())

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[MultimediaProvider]) -> None:
        """注册新的多媒体 Provider"""
        cls._providers[name] = provider_class

    @classmethod
    def clear_cache(cls) -> None:
        """清除 Provider 实例缓存"""
        with cls._instances_lock:
            cls._instances.clear()
        logger.info("Multimedia provider instance cache cleared")
