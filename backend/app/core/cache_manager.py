"""
缓存管理器 - BUG-031修复

提供统一的缓存管理，避免重复代码和提高性能

版本: 1.0
更新日期: 2026-01-17
"""

import json
import redis
import threading
from typing import Any, Optional, List
from app.core.config import settings
from app.core.constants import REDIS_POOL_SIZE, REDIS_POOL_TIMEOUT
import logging

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis缓存管理器"""

    _instance: Optional['RedisCache'] = None
    _pool: Optional[redis.ConnectionPool] = None
    _client: Optional[redis.Redis] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'RedisCache':
        """线程安全的单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """初始化Redis连接"""
        try:
            RedisCache._pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=REDIS_POOL_SIZE,
                socket_connect_timeout=REDIS_POOL_TIMEOUT,
                socket_keepalive=True,
                decode_responses=True
            )
            RedisCache._client = redis.Redis(connection_pool=RedisCache._pool)
            
            # 测试连接
            RedisCache._client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {str(e)}")
            RedisCache._client = None

    def get_client(self) -> Optional[redis.Redis]:
        """获取Redis客户端"""
        if RedisCache._client is None:
            self._initialize()
        return RedisCache._client

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值（会自动序列化）
            ttl_seconds: 过期时间（秒）

        Returns:
            是否设置成功
        """
        try:
            client = self.get_client()
            if client is None:
                return False

            # 序列化值
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            
            # 设置缓存
            result = client.setex(
                key,
                ttl_seconds,  # setex expects integer seconds, not timedelta
                serialized_value
            )
            return result
        except Exception as e:
            logger.error(f"设置缓存失败 [{key}]: {str(e)}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        try:
            client = self.get_client()
            if client is None:
                return default

            value = client.get(key)
            if value is None:
                return default

            # 尝试反序列化
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"获取缓存失败 [{key}]: {str(e)}")
            return default

    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        try:
            client = self.get_client()
            if client is None:
                return False

            result = client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"删除缓存失败 [{key}]: {str(e)}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        删除匹配模式的所有缓存

        Args:
            pattern: 匹配模式（如：product:*）

        Returns:
            删除的键数量
        """
        try:
            client = self.get_client()
            if client is None:
                return 0

            # 扫描匹配的键
            deleted = 0
            for key in client.scan_iter(match=pattern):
                result = client.delete(key)
                deleted += result
            return deleted
        except Exception as e:
            logger.error(f"删除缓存模式失败 [{pattern}]: {str(e)}")
            return 0

    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        try:
            client = self.get_client()
            if client is None:
                return False

            return client.exists(key) > 0
        except Exception as e:
            logger.error(f"检查缓存失败 [{key}]: {str(e)}")
            return False

    def set_list(self, key: str, values: List[Any], ttl_seconds: int = 300) -> bool:
        """
        设置列表缓存

        Args:
            key: 缓存键
            values: 值列表
            ttl_seconds: 过期时间（秒）

        Returns:
            是否设置成功
        """
        try:
            client = self.get_client()
            if client is None:
                return False

            pipeline = client.pipeline()
            pipeline.delete(key)  # 先删除旧值
            
            for value in values:
                serialized = json.dumps(value) if not isinstance(value, str) else value
                pipeline.rpush(key, serialized)
            
            pipeline.expire(key, ttl_seconds)  # expire expects integer seconds, not timedelta
            pipeline.execute()
            return True
        except Exception as e:
            logger.error(f"设置列表缓存失败 [{key}]: {str(e)}")
            return False

    def get_list(self, key: str) -> List[Any]:
        """
        获取列表缓存

        Args:
            key: 缓存键

        Returns:
            缓存列表
        """
        try:
            client = self.get_client()
            if client is None:
                return []

            values = client.lrange(key, 0, -1)
            result = []
            for value in values:
                try:
                    result.append(json.loads(value))
                except (json.JSONDecodeError, TypeError):
                    result.append(value)
            return result
        except Exception as e:
            logger.error(f"获取列表缓存失败 [{key}]: {str(e)}")
            return []

    def mget(self, keys: List[str]) -> List[Any]:
        """批量获取缓存（优化：减少网络往返）"""
        try:
            client = self.get_client()
            if not client or not keys:
                return [None] * len(keys)

            values = client.mget(keys)
            return [json.loads(v) if v else None for v in values]
        except Exception as e:
            logger.error(f"批量获取缓存失败: {str(e)}")
            return [None] * len(keys)

    def mset(self, mapping: dict, ttl_seconds: int = 300) -> bool:
        """批量设置缓存（优化：使用pipeline）"""
        try:
            client = self.get_client()
            if not client or not mapping:
                return False

            pipeline = client.pipeline()
            for key, value in mapping.items():
                serialized = json.dumps(value) if not isinstance(value, str) else value
                pipeline.setex(key, ttl_seconds, serialized)  # setex expects integer seconds, not timedelta
            pipeline.execute()
            return True
        except Exception as e:
            logger.error(f"批量设置缓存失败: {str(e)}")
            return False

    def clear_all(self) -> bool:
        """清空所有缓存"""
        try:
            client = self.get_client()
            if client is None:
                return False

            client.flushdb()
            logger.info("已清空所有缓存")
            return True
        except Exception as e:
            logger.error(f"清空缓存失败: {str(e)}")
            return False

    def close(self) -> None:
        """关闭连接"""
        try:
            if RedisCache._pool:
                RedisCache._pool.disconnect()
                logger.info("Redis连接已关闭")
        except Exception as e:
            logger.error(f"关闭Redis连接失败: {str(e)}")


# 全局缓存实例
cache = RedisCache()

__all__ = ['cache', 'RedisCache']
