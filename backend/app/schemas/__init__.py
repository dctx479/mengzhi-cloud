"""
Schema模块初始化
"""

from .auth import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    ResetPasswordRequest,
    UpdateProfileRequest,
    TokenResponse,
    UserResponse,
    LoginResponse,
    RegisterResponse,
    ChangePasswordResponse,
    ResetPasswordResponse,
)

__all__ = [
    "RegisterRequest",
    "LoginRequest",
    "RefreshTokenRequest",
    "ChangePasswordRequest",
    "ResetPasswordRequest",
    "UpdateProfileRequest",
    "TokenResponse",
    "UserResponse",
    "LoginResponse",
    "RegisterResponse",
    "ChangePasswordResponse",
    "ResetPasswordResponse",
]
