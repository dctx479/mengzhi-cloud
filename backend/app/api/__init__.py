"""
API路由模块初始化
"""

from .auth import router as auth_router
from . import chat
from . import cultural_tags

__all__ = ["auth_router", "chat", "cultural_tags"]
