"""
认证相关Schema定义

版本: 1.0
更新日期: 2026-01-17
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime


class RegisterRequest(BaseModel):
    """用户注册请求"""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="用户名，3-50字符"
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="邮箱地址（与phone至少填一个）"
    )
    phone: Optional[str] = Field(
        default=None,
        min_length=11,
        max_length=20,
        description="手机号码（与email至少填一个）"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=32,
        description="密码，8-32字符，必须包含大小写字母、数字和特殊字符"
    )
    user_type: str = Field(
        ...,
        description="用户类型：personal/enterprise"
    )
    verification_code: str = Field(
        ...,
        description="验证码（邮箱或手机）"
    )
    enterprise_name: Optional[str] = Field(
        default=None,
        max_length=200,
        description="企业名称（企业用户必填）"
    )
    enterprise_license: Optional[str] = Field(
        default=None,
        max_length=50,
        description="营业执照号（企业用户必填）"
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        """验证用户名格式"""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """验证密码强度 - 必须包含大小写字母、数字和特殊字符"""
        import re

        # 检查长度
        if len(v) < 8 or len(v) > 32:
            raise ValueError("密码长度必须在8-32字符之间")

        # 检查大写字母
        if not re.search(r'[A-Z]', v):
            raise ValueError("密码必须包含至少一个大写字母")

        # 检查小写字母
        if not re.search(r'[a-z]', v):
            raise ValueError("密码必须包含至少一个小写字母")

        # 检查数字
        if not re.search(r'\d', v):
            raise ValueError("密码必须包含至少一个数字")

        # 检查特殊字符
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/`~]', v):
            raise ValueError("密码必须包含至少一个特殊字符（如: !@#$%^&*等）")

        return v

    @field_validator("user_type")
    @classmethod
    def validate_user_type(cls, v):
        """验证用户类型"""
        if v not in ["personal", "enterprise"]:
            raise ValueError("用户类型必须是personal或enterprise")
        return v

    def model_post_init(self, __context):
        """自定义验证逻辑"""
        if not self.email and not self.phone:
            raise ValueError("邮箱和手机号至少填一个")

        if self.user_type == "enterprise":
            if not self.enterprise_name:
                raise ValueError("企业用户必须填写企业名称")
            if not self.enterprise_license:
                raise ValueError("企业用户必须填写营业执照号")


class LoginRequest(BaseModel):
    """用户登录请求"""

    username: str = Field(
        ...,
        description="用户名或邮箱或手机号"
    )
    password: str = Field(
        ...,
        description="密码"
    )
    device_id: Optional[str] = Field(
        default=None,
        description="设备ID（可选，用于多设备登录控制）"
    )


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""

    refresh_token: str = Field(
        ...,
        description="刷新令牌"
    )


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""

    old_password: str = Field(
        ...,
        description="原密码"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=32,
        description="新密码，8-32字符，必须包含大小写字母、数字和特殊字符"
    )

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        """验证新密码强度"""
        import re

        if len(v) < 8 or len(v) > 32:
            raise ValueError("密码长度必须在8-32字符之间")
        if not re.search(r'[A-Z]', v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not re.search(r'[a-z]', v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not re.search(r'\d', v):
            raise ValueError("密码必须包含至少一个数字")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/`~]', v):
            raise ValueError("密码必须包含至少一个特殊字符")
        return v


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""

    identifier: str = Field(
        ...,
        description="邮箱或手机号"
    )
    verification_code: str = Field(
        ...,
        description="验证码"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=32,
        description="新密码，8-32字符，必须包含大小写字母、数字和特殊字符"
    )

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        """验证新密码强度"""
        import re

        if len(v) < 8 or len(v) > 32:
            raise ValueError("密码长度必须在8-32字符之间")
        if not re.search(r'[A-Z]', v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not re.search(r'[a-z]', v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not re.search(r'\d', v):
            raise ValueError("密码必须包含至少一个数字")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/`~]', v):
            raise ValueError("密码必须包含至少一个特殊字符")
        return v


class UpdateProfileRequest(BaseModel):
    """更新用户信息请求"""

    nickname: Optional[str] = Field(
        default=None,
        max_length=100,
        description="昵称"
    )
    avatar_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="头像URL"
    )
    gender: Optional[int] = Field(
        default=None,
        ge=0,
        le=2,
        description="性别：0未知/1男/2女"
    )
    bio: Optional[str] = Field(
        default=None,
        max_length=500,
        description="个人简介"
    )
    location: Optional[str] = Field(
        default=None,
        max_length=200,
        description="所在地"
    )
    website: Optional[str] = Field(
        default=None,
        max_length=500,
        description="个人网站"
    )


class TokenResponse(BaseModel):
    """Token响应"""

    access_token: str = Field(
        ...,
        description="访问令牌（30分钟有效）"
    )
    refresh_token: str = Field(
        ...,
        description="刷新令牌（7天有效）"
    )
    token_type: str = Field(
        default="Bearer",
        description="令牌类型"
    )
    expires_in: int = Field(
        ...,
        description="访问令牌过期时间（秒）"
    )


class UserResponse(BaseModel):
    """用户信息响应"""
    model_config = ConfigDict(from_attributes=True)

    user_id: str = Field(
        ...,
        description="用户UUID"
    )
    username: str = Field(
        ...,
        description="用户名"
    )
    email: Optional[str] = Field(
        default=None,
        description="邮箱（已脱敏）"
    )
    phone: Optional[str] = Field(
        default=None,
        description="手机号（已脱敏）"
    )
    nickname: Optional[str] = Field(
        default=None,
        description="昵称"
    )
    avatar_url: Optional[str] = Field(
        default=None,
        description="头像URL"
    )
    gender: int = Field(
        default=0,
        description="性别"
    )
    enterprise_id: Optional[int] = Field(
        default=None,
        description="企业ID"
    )
    user_type: str = Field(
        ...,
        description="用户类型：personal/enterprise"
    )
    status: str = Field(
        ...,
        description="账号状态"
    )
    role: str = Field(
        ...,
        description="用户角色"
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="创建时间"
    )
    last_login_at: Optional[datetime] = Field(
        default=None,
        description="最后登录时间"
    )
    bio: Optional[str] = Field(
        default=None,
        description="个人简介"
    )
    location: Optional[str] = Field(
        default=None,
        description="所在地"
    )
    website: Optional[str] = Field(
        default=None,
        description="个人网站"
    )


class LoginResponse(BaseModel):
    """登录响应"""

    user: UserResponse = Field(
        ...,
        description="用户信息"
    )
    tokens: TokenResponse = Field(
        ...,
        description="令牌信息"
    )


class RegisterResponse(BaseModel):
    """注册响应"""

    user_id: str = Field(
        ...,
        description="用户UUID"
    )
    username: str = Field(
        ...,
        description="用户名"
    )
    email: Optional[str] = Field(
        default=None,
        description="邮箱"
    )
    phone: Optional[str] = Field(
        default=None,
        description="手机号"
    )
    user_type: str = Field(
        ...,
        description="用户类型"
    )
    created_at: datetime = Field(
        ...,
        description="创建时间"
    )


class ChangePasswordResponse(BaseModel):
    """修改密码响应"""

    message: str = Field(
        default="密码修改成功",
        description="响应消息"
    )
    changed_at: datetime = Field(
        default_factory=lambda: datetime.utcnow(),
        description="修改时间"
    )


class ResetPasswordResponse(BaseModel):
    """重置密码响应"""

    message: str = Field(
        default="密码重置成功",
        description="响应消息"
    )
    reset_at: datetime = Field(
        default_factory=lambda: datetime.utcnow(),
        description="重置时间"
    )
