"""
API频率限制中间件
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import deque
import time
import threading

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, deque] = {}
        self._last_global_cleanup = time.monotonic()
        self._lock = threading.RLock()

    async def dispatch(self, request: Request, call_next):
        # 获取客户端标识（IP或用户ID）
        # BUG FIX #1: Safe attribute access - use getattr to handle missing 'host'
        client_id = "unknown"
        if request.client:
            client_id = getattr(request.client, "host", "unknown")
        
        if hasattr(request.state, "user") and request.state.user:
            user_id = getattr(request.state.user, "id", None) or getattr(request.state.user, "user_id", None)
            if user_id:
                client_id = f"user_{user_id}"

        now = time.monotonic()
        cutoff = now - 60  # 1分钟窗口

        # BUG FIX #2: Calculate remaining inside lock to avoid race condition
        remaining = 0
        with self._lock:
            # 获取或创建该客户端的请求队列
            if client_id not in self.requests:
                self.requests[client_id] = deque()
            client_deque = self.requests[client_id]

            # O(1) 清理：从左侧弹出过期的时间戳
            while client_deque and client_deque[0] < cutoff:
                client_deque.popleft()

            # 定期全局清理空队列（每120秒一次，避免内存泄漏）
            if now - self._last_global_cleanup > 120:
                empty_keys = [k for k, v in self.requests.items() if not v]
                for k in empty_keys:
                    del self.requests[k]
                self._last_global_cleanup = now

            # 检查频率限制
            if len(client_deque) >= self.requests_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={
                        "code": 42901,
                        "message": "请求过于频繁，请稍后再试",
                        "retry_after": 60
                    }
                )

            # 记录请求
            client_deque.append(now)
            current_queue_len = len(client_deque)
            # Calculate remaining inside lock to get accurate value
            remaining = max(0, self.requests_per_minute - current_queue_len)

        # 继续处理请求
        response = await call_next(request)

        # 添加速率限制头（使用lock内计算的值，避免race condition）
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
