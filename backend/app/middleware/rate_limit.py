"""
API频率限制中间件
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import deque
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, deque] = {}
        self._last_global_cleanup = time.monotonic()

    async def dispatch(self, request: Request, call_next):
        # 获取客户端标识（IP或用户ID）
        client_id = request.client.host if request.client else "unknown"
        if hasattr(request.state, "user") and request.state.user:
            client_id = f"user_{request.state.user.id}"

        now = time.monotonic()
        cutoff = now - 60  # 1分钟窗口

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

        # 继续处理请求
        response = await call_next(request)

        # 添加速率限制头
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(client_deque)
        )

        return response
