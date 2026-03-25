"""
请求频率限制模块

P1-6修复: 添加请求频率限制
"""

import time
import threading
from typing import Tuple, Dict, Any
from loguru import logger


class RateLimiter:
    """请求频率限制器"""

    MAX_MEMORY_ENTRIES = 10000  # 内存存储最大条目数

    def __init__(self, redis_client=None):
        """初始化频率限制器"""
        self.redis_client = redis_client
        self._memory_store: Dict[str, Dict[str, Any]] = {}
        self._last_cleanup: float = 0.0
        self._lock = threading.Lock()  # 保护内存存储和cleanup时间戳
    
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

        # 在临界区内执行所有操作
        with self._lock:
            # 定期清理过期条目（每60秒最多清理一次）
            if now - self._last_cleanup > 60 or len(self._memory_store) > self.MAX_MEMORY_ENTRIES:
                self._cleanup_expired(now)

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

    def _cleanup_expired(self, now: float) -> None:
        """清理过期的内存条目（必须在_lock保护下调用）"""
        expired_keys = [k for k, v in self._memory_store.items() if now >= v["reset_at"]]
        for k in expired_keys:
            del self._memory_store[k]
        self._last_cleanup = now
