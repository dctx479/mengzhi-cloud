"""
Redis客户端管理 - 带连接验证和异常处理

版本: 1.0
更新日期: 2026-01-17
"""

import redis
from redis import Redis, ConnectionPool
from typing import Optional
from loguru import logger
from fastapi import HTTPException

from app.core.config import settings


class RedisClient:
    """Redis客户端单例"""
    
    _instance: Optional[Redis] = None
    _pool: Optional[ConnectionPool] = None
    
    @classmethod
    def get_instance(cls) -> Optional[Redis]:
        """获取Redis客户端实例，支持重连
        
        Returns:
            Redis客户端实例，如果连接失败返回None
        """
        if cls._instance is None:
            try:
                # 创建连接池（优化：增加连接数和重试）
                cls._pool = ConnectionPool(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    password=settings.REDIS_PASSWORD,
                    db=settings.REDIS_DB,
                    decode_responses=True,
                    socket_connect_timeout=3,
                    socket_timeout=3,
                    max_connections=50,
                    socket_keepalive=True,
                    health_check_interval=30
                )
                
                # 创建Redis客户端
                cls._instance = Redis(connection_pool=cls._pool)
                
                # 验证连接
                cls._instance.ping()
                logger.info("Redis连接成功")
                
            except redis.ConnectionError as e:
                logger.error(f"Redis连接失败: {e}")
                cls._instance = None
                cls._pool = None
            except Exception as e:
                logger.error(f"Redis初始化异常: {e}")
                cls._instance = None
                cls._pool = None
        
        # Health check: verify existing connection
        if cls._instance is not None:
            try:
                cls._instance.ping()
            except Exception as e:
                logger.warning(f"Redis连接已断开，重新初始化: {e}")
                cls._instance = None
                cls._pool = None
                return cls.get_instance()  # Recursive retry
                
        return cls._instance
    
    @classmethod
    def close(cls):
        """关闭Redis连接"""
        if cls._instance:
            try:
                cls._instance.close()
                logger.info("Redis连接已关闭")
            except Exception as e:
                logger.error(f"关闭Redis连接失败: {e}")
            finally:
                cls._instance = None
                cls._pool = None


def get_redis() -> Redis:
    """获取Redis客户端（依赖注入）
    
    Returns:
        Redis客户端实例
        
    Raises:
        HTTPException: Redis服务不可用
    """
    client = RedisClient.get_instance()
    
    if client is None:
        raise HTTPException(
            status_code=503,
            detail="Redis服务暂时不可用，请稍后重试"
        )
    
    return client


def get_redis_optional() -> Optional[Redis]:
    """获取Redis客户端（可选，不抛异常）
    
    Returns:
        Redis客户端实例或None
    """
    return RedisClient.get_instance()


# 导出
__all__ = ["RedisClient", "get_redis", "get_redis_optional"]
