"""
请求频率限制模块

P1-6修复: 添加请求频率限制
"""

import time
from typing import Tuple, Dict, Any
from loguru import logger


class RateLimiter:
    """请求频率限制器"""
    
    def __init__(self, redis_client=None):
        """初始化频率限制器"""
        self.redis_client = redis_client
        self._memory_store: Dict[str, Dict[str, Any]] = {}
    
    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int]:
        """检查是否超过频率限制
        
        Args:
            key: 限制键（如用户ID、IP地址）
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）
            
        Returns:
            (是否允许, 剩余请求数)
        """
        if self.redis_client:
            return await self._check_rate_limit_redis(key, max_requests, window_seconds)
        else:
            return await self._check_rate_limit_memory(key, max_requests, window_seconds)
    
    async def _check_rate_limit_redis(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int]:
        """使用Redis检查频率限制"""
        try:
            rate_key = f"rate_limit:{key}"
            current = self.redis_client.get(rate_key)
            
            if current is None:
                self.redis_client.setex(rate_key, window_seconds, 1)
                return True, max_requests - 1
            
            current = int(current)
            if current >= max_requests:
                return False, 0
            
            self.redis_client.incr(rate_key)
            return True, max_requests - current - 1
            
        except Exception as e:
            logger.error(f"Redis频率限制检查失败: {e}")
            return await self._check_rate_limit_memory(key, max_requests, window_seconds)
    
    async def _check_rate_limit_memory(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int]:
        """使用内存检查频率限制"""
        now = time.time()
        rate_key = f"rate_limit:{key}"
        
        if rate_key not in self._memory_store:
            self._memory_store[rate_key] = {
                "count": 1,
                "reset_at": now + window_seconds
            }
            return True, max_requests - 1
        
        data = self._memory_store[rate_key]
        
        if now >= data["reset_at"]:
            self._memory_store[rate_key] = {
                "count": 1,
                "reset_at": now + window_seconds
            }
            return True, max_requests - 1
        
        if data["count"] >= max_requests:
            return False, 0
        
        data["count"] += 1
        return True, max_requests - data["count"]
