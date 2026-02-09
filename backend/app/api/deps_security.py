"""
安全依赖注入模块

P0和P1问题修复的依赖项
"""

from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.input_validation import input_validator
from app.core.rate_limiter import RateLimiter
from app.core.redis_client import get_redis_optional
from app.core.constants import (
    RATE_LIMIT_LOGIN_MAX_REQUESTS,
    RATE_LIMIT_LOGIN_WINDOW_SECONDS,
    RATE_LIMIT_REGISTER_MAX_REQUESTS,
    RATE_LIMIT_REGISTER_WINDOW_SECONDS,
    RATE_LIMIT_CAPTCHA_MAX_REQUESTS,
    RATE_LIMIT_CAPTCHA_WINDOW_SECONDS,
)
from loguru import logger


# 全局频率限制器实例
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """获取频率限制器实例"""
    global _rate_limiter
    if _rate_limiter is None:
        redis_client = get_redis_optional()
        _rate_limiter = RateLimiter(redis_client)
    return _rate_limiter


async def check_login_rate_limit(request: Request) -> None:
    """检查登录频率限制
    
    P1-6修复: 防止暴力破解
    """
    limiter = get_rate_limiter()
    
    # 使用IP地址作为限制键
    client_ip = request.client.host if request.client else "unknown"
    key = f"login:{client_ip}"
    
    allowed, remaining = await limiter.check_rate_limit(
        key=key,
        max_requests=RATE_LIMIT_LOGIN_MAX_REQUESTS,
        window_seconds=RATE_LIMIT_LOGIN_WINDOW_SECONDS
    )
    
    if not allowed:
        logger.warning(f"登录频率限制触发: IP={client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录尝试过于频繁，请{RATE_LIMIT_LOGIN_WINDOW_SECONDS // 60}分钟后再试"
        )


async def check_register_rate_limit(request: Request) -> None:
    """检查注册频率限制
    
    P1-6修复: 防止批量注册
    """
    limiter = get_rate_limiter()
    
    client_ip = request.client.host if request.client else "unknown"
    key = f"register:{client_ip}"
    
    allowed, remaining = await limiter.check_rate_limit(
        key=key,
        max_requests=RATE_LIMIT_REGISTER_MAX_REQUESTS,
        window_seconds=RATE_LIMIT_REGISTER_WINDOW_SECONDS
    )
    
    if not allowed:
        logger.warning(f"注册频率限制触发: IP={client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"注册尝试过于频繁，请{RATE_LIMIT_REGISTER_WINDOW_SECONDS // 3600}小时后再试"
        )


async def check_captcha_rate_limit(request: Request) -> None:
    """检查验证码请求频率限制
    
    P1-6修复: 防止验证码滥用
    """
    limiter = get_rate_limiter()
    
    client_ip = request.client.host if request.client else "unknown"
    key = f"captcha:{client_ip}"
    
    allowed, remaining = await limiter.check_rate_limit(
        key=key,
        max_requests=RATE_LIMIT_CAPTCHA_MAX_REQUESTS,
        window_seconds=RATE_LIMIT_CAPTCHA_WINDOW_SECONDS
    )
    
    if not allowed:
        logger.warning(f"验证码频率限制触发: IP={client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="验证码请求过于频繁，请稍后再试"
        )


def validate_register_input(
    username: str,
    email: Optional[str],
    phone: Optional[str],
    password: str
) -> None:
    """验证注册输入
    
    P0-4修复: 输入验证和XSS防护
    """
    # 验证用户名
    valid, error = input_validator.validate_username(username)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"field": "username", "message": error}
        )
    
    # 验证邮箱
    if email:
        valid, error = input_validator.validate_email(email)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"field": "email", "message": error}
            )
    
    # 验证手机号
    if phone:
        valid, error = input_validator.validate_phone(phone)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"field": "phone", "message": error}
            )
    
    # 验证密码
    valid, error = input_validator.validate_password(password)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"field": "password", "message": error}
        )
