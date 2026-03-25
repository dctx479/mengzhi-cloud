"""
认证API路由 - 8个核心端点

版本: 1.0
更新日期: 2026-01-17

包含端点:
1. POST /api/v1/auth/register - 用户注册
2. POST /api/v1/auth/login - 用户登录
3. POST /api/v1/auth/refresh - 刷新Token
4. POST /api/v1/auth/logout - 用户登出
5. GET /api/v1/auth/me - 获取当前用户信息
6. PUT /api/v1/auth/me - 更新用户信息
7. POST /api/v1/auth/change-password - 修改密码
8. POST /api/v1/auth/reset-password - 重置密码
"""

from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from loguru import logger

from app.core.responses import APIResponse, success_response, error_response
from app.core.errors import (
    BusinessException,
    ErrorCode,
    ERROR_HTTP_STATUS,
    ERROR_MESSAGES,
    UserNotFoundError,
    PasswordIncorrectError,
    ValidationError,
)
from app.api.deps import (
    get_db,
    get_current_user,
    SessionLocal,
)
from app.services.auth_service import AuthService
from app.services.captcha_service import CaptchaService
from app.schemas.auth import (
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

# 创建路由
router = APIRouter()


def _enum_val(v):
    """Convert ORM Enum or raw SQL uppercase string to lowercase."""
    return v.value if hasattr(v, 'value') else str(v).lower()


# ==================== 1. 用户注册 ====================

@router.post(
    "/register",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="注册新用户账号，支持个人和企业用户",
    tags=["认证"]
)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
) -> APIResponse:
    import json
    from loguru import logger
    logger.info(f"Register request: {json.dumps(request.dict(), ensure_ascii=False)}")
    """
    用户注册端点

    参数:
        request: 注册请求数据
        db: 数据库会话

    返回:
        成功: 201 Created
        失败: 400 参数错误 / 409 用户已存在

    示例请求:
        POST /api/v1/auth/register
        {
            "username": "zhangsan",
            "email": "zhangsan@example.com",
            "phone": "13800138000",
            "password": "Password123",
            "user_type": "enterprise",
            "verification_code": "123456",
            "enterprise_name": "内蒙古草原牧业有限公司",
            "enterprise_license": "91150100MA0N1234X5"
        }

    示例响应:
        {
            "code": 200,
            "message": "注册成功",
            "data": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "zhangsan",
                "email": "zhangsan@example.com",
                "user_type": "enterprise",
                "created_at": "2026-01-17T10:00:00"
            },
            "timestamp": "2026-01-17T10:00:00"
        }
    """
    try:
        auth_service = AuthService(db)

        # 1. 验证验证码（开发环境下可选）
        if request.verification_code:
            identifier = request.email or request.phone
            try:
                auth_service.verify_code(
                    identifier=identifier,
                    code_type="register",
                    code=request.verification_code
                )
            except BusinessException:
                raise ValidationError(
                    message="验证码无效或已过期",
                    errors=[{
                        "field": "verification_code",
                        "message": "验证码无效或已过期"
                    }]
                )

        # 2. 验证输入参数
        auth_service._validate_register_input(request)

        # 3. 检查用户是否已存在
        auth_service._check_existing_user(request)

        # 4. 创建企业（如果是企业用户）
        enterprise_id = auth_service._create_enterprise_if_needed(request)

        # 5. 创建用户
        user_uuid = auth_service._create_user_record(request, enterprise_id)
        db.commit()

        # 6. 返回成功响应
        response_data = RegisterResponse(
            user_id=user_uuid,
            username=request.username,
            email=request.email,
            phone=request.phone,
            user_type=request.user_type,
            created_at=datetime.utcnow()
        )

        return APIResponse(
            code=200,
            message="注册成功",
            data=response_data
        )

    except ValidationError:
        raise
    except BusinessException as e:
        db.rollback()
        return APIResponse(
            code=e.code,
            message=e.message,
            data=None
        )
    except Exception as e:
        db.rollback()
        return APIResponse(
            code=ErrorCode.SYSTEM_ERROR,
            message=ERROR_MESSAGES[ErrorCode.SYSTEM_ERROR],
            data=None
        )


# ==================== 2. 用户登录 ====================

@router.post(
    "/login",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="用户登录",
    description="使用用户名/邮箱/手机号和密码登录",
    tags=["认证"]
)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
    req: Request = None
) -> APIResponse:
    """
    用户登录端点

    参数:
        request: 登录请求数据
        db: 数据库会话

    返回:
        成功: 200 OK
        失败: 401 未授权 / 403 账号被锁定

    示例请求:
        POST /api/v1/auth/login
        {
            "username": "zhangsan",
            "password": "Password123"
        }

    示例响应:
        {
            "code": 200,
            "message": "登录成功",
            "data": {
                "user": {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "username": "zhangsan",
                    "email": "zh***@example.com",
                    "user_type": "enterprise",
                    "status": "active"
                },
                "tokens": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "Bearer",
                    "expires_in": 1800
                }
            },
            "timestamp": "2026-01-17T10:00:00"
        }
    """
    try:
        auth_service = AuthService(db)

        # 1. 根据用户名/邮箱/手机号查找用户
        user = auth_service._find_user(request.username)
        if not user:
            raise UserNotFoundError()

        # 2. 检查账号状态
        auth_service.check_account_status(user)

        # 3. 验证密码
        auth_service._validate_credentials(user, request.password)

        # 4. 生成Token
        access_token, refresh_token = auth_service._generate_login_tokens(
            user,
            device_id=request.device_id,
            ip_address=req.client.host if req else None
        )

        # 5. 更新登录信息
        auth_service._update_successful_login(user.id)

        # 6. 构建响应 (normalize enum values to lowercase for frontend)
        user_data = UserResponse(
            user_id=user.user_uuid,
            username=user.username,
            email=auth_service.mask_email(user.email),
            phone=auth_service.mask_phone(user.phone),
            user_type=_enum_val(user.user_type),
            status=_enum_val(user.status),
            role=_enum_val(user.role),
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )

        tokens = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=1800  # 30分钟
        )

        response_data = LoginResponse(
            user=user_data,
            tokens=tokens
        )

        return APIResponse(
            code=200,
            message="登录成功",
            data=response_data
        )

    except BusinessException as e:
        return APIResponse(
            code=e.code,
            message=e.message,
            data=None
        )
    except Exception as e:
        return APIResponse(
            code=ErrorCode.SYSTEM_ERROR,
            message=ERROR_MESSAGES[ErrorCode.SYSTEM_ERROR],
            data=None
        )


# ==================== 3. 刷新Token ====================

@router.post(
    "/refresh",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="刷新Token",
    description="使用Refresh Token刷新Access Token",
    tags=["认证"]
)
async def refresh(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    刷新Token端点

    参数:
        request: 刷新请求数据
        db: 数据库会话

    返回:
        成功: 200 OK
        失败: 401 未授权

    示例请求:
        POST /api/v1/auth/refresh
        {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }

    示例响应:
        {
            "code": 200,
            "message": "Token刷新成功",
            "data": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 1800
            },
            "timestamp": "2026-01-17T10:00:00"
        }
    """
    try:
        auth_service = AuthService(db)

        # 刷新Token
        new_access_token, new_refresh_token = auth_service.refresh_tokens(
            request.refresh_token
        )

        response_data = TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=1800
        )

        return APIResponse(
            code=200,
            message="Token刷新成功",
            data=response_data
        )

    except BusinessException as e:
        return APIResponse(
            code=e.code,
            message=e.message,
            data=None
        )
    except Exception as e:
        return APIResponse(
            code=ErrorCode.SYSTEM_ERROR,
            message=ERROR_MESSAGES[ErrorCode.SYSTEM_ERROR],
            data=None
        )


# ==================== 4. 用户登出 ====================

@router.post(
    "/logout",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="用户登出",
    description="用户登出，Token加入黑名单",
    tags=["认证"]
)
async def logout(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    用户登出端点

    参数:
        current_user: 当前用户信息
        db: 数据库会话

    返回:
        成功: 200 OK

    示例请求:
        POST /api/v1/auth/logout
        Headers:
            Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

    示例响应:
        {
            "code": 200,
            "message": "登出成功",
            "data": {"message": "已成功登出"},
            "timestamp": "2026-01-17T10:00:00"
        }
    """
    try:
        auth_service = AuthService(db)

        # 将Token加入黑名单
        jti = current_user.get("jti")
        if jti:
            # Token有效期为30分钟，转换为秒
            auth_service.add_token_to_blacklist(jti, 30 * 60)

        # 清除用户缓存
        user_id = current_user.get("user_id")
        if user_id:
            auth_service.clear_user_cache(user_id)

        return APIResponse(
            code=200,
            message="登出成功",
            data={"message": "已成功登出"}
        )

    except Exception as e:
        # 即使出错也返回成功，因为登出是客户端行为
        return APIResponse(
            code=200,
            message="登出成功",
            data={"message": "已成功登出"}
        )


# ==================== 5. 获取当前用户信息 ====================

@router.get(
    "/me",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息",
    tags=["认证"]
)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    获取当前用户信息端点

    参数:
        current_user: 当前用户信息
        db: 数据库会话

    返回:
        成功: 200 OK
        失败: 401 未授权 / 404 用户不存在

    示例请求:
        GET /api/v1/auth/me
        Headers:
            Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

    示例响应:
        {
            "code": 200,
            "message": "success",
            "data": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "zhangsan",
                "email": "zh***@example.com",
                "user_type": "enterprise",
                "status": "active",
                "role": "user",
                "created_at": "2026-01-17T10:00:00"
            },
            "timestamp": "2026-01-17T10:00:00"
        }
    """
    try:
        auth_service = AuthService(db)

        # 使用缓存获取用户详细信息
        user = auth_service.get_user_by_id_cached(current_user["user_id"])

        if not user:
            raise UserNotFoundError()

        def _attr(obj, key, default=None):
            """Get attribute from ORM Row or dict."""
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        response_data = UserResponse(
            user_id=_attr(user, 'user_uuid'),
            username=_attr(user, 'username'),
            email=auth_service.mask_email(_attr(user, 'email')),
            phone=auth_service.mask_phone(_attr(user, 'phone')),
            user_type=_enum_val(_attr(user, 'user_type', 'personal')),
            status=_enum_val(_attr(user, 'status', 'active')),
            role=_enum_val(_attr(user, 'role', 'user')),
            created_at=_attr(user, 'created_at'),
            last_login_at=_attr(user, 'last_login_at')
        )

        return APIResponse(
            code=200,
            message="success",
            data=response_data
        )

    except UserNotFoundError:
        raise
    except Exception as e:
        return error_response(
            code=ErrorCode.SYSTEM_ERROR,
            message=ERROR_MESSAGES[ErrorCode.SYSTEM_ERROR]
        )


# ==================== 6. 更新用户信息 ====================

@router.put(
    "/me",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="更新用户信息",
    description="更新当前用户的个人信息（昵称、头像等）",
    tags=["认证"]
)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    更新用户信息端点

    参数:
        request: 更新请求数据
        current_user: 当前用户信息
        db: 数据库会话

    返回:
        成功: 200 OK
        失败: 400 参数错误 / 404 用户不存在

    示例请求:
        PUT /api/v1/auth/me
        Headers:
            Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        {
            "nickname": "张三",
            "avatar_url": "https://example.com/avatar.jpg",
            "gender": 1
        }

    示例响应:
        {
            "code": 200,
            "message": "个人信息更新成功",
            "data": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "nickname": "张三",
                "avatar_url": "https://example.com/avatar.jpg"
            },
            "timestamp": "2026-01-17T10:00:00"
        }
    """
    try:
        from sqlalchemy import text

        # Whitelist of allowed column names to prevent SQL injection.
        # Only these columns may appear in the dynamic UPDATE statement.
        ALLOWED_UPDATE_COLUMNS = {
            "nickname",
            "avatar_url",
            "gender",
            "updated_at",
            "bio",
            "location",
            "website",
        }
        # 构建更新字段
        update_fields = []
        params = {"user_id": current_user["user_id"]}

        if request.nickname is not None:
            update_fields.append(("nickname", request.nickname))

        if request.avatar_url is not None:
            update_fields.append(("avatar_url", request.avatar_url))

        if request.gender is not None:
            update_fields.append(("gender", request.gender))

        if request.bio is not None:
            update_fields.append(("bio", request.bio))

        if request.location is not None:
            update_fields.append(("location", request.location))

        if request.website is not None:
            update_fields.append(("website", request.website))
        # 如果没有字段要更新
        if not update_fields:
            auth_service = AuthService(db)
            user = auth_service._get_user_by_id(current_user["user_id"])
            if not user:
                raise UserNotFoundError()

            return APIResponse(
                code=200,
                message="personal info updated successfully",
                data={"message": "no changes"}
            )

        # Always update the timestamp
        update_fields.append(("updated_at", datetime.utcnow()))

        # Validate all column names against the whitelist before building SQL
        set_clauses = []
        for col_name, col_value in update_fields:
            if col_name not in ALLOWED_UPDATE_COLUMNS:
                raise ValueError(f"Column '{col_name}' is not in the allowed update whitelist")
            set_clauses.append(f"{col_name} = :{col_name}")
            params[col_name] = col_value

        sql = text(f"UPDATE users SET {', '.join(set_clauses)} WHERE user_uuid = :user_id")

        db.execute(sql, params)
        db.commit()

        # 清除用户缓存
        auth_service = AuthService(db)
        auth_service.clear_user_cache(current_user["user_id"])

        return APIResponse(
            code=200,
            message="个人信息更新成功",
            data={"updated": True}
        )

    except ValueError as e:
        db.rollback()
        logger.warning(f"SQL injection validation failed in update_profile: {str(e)}")
        return APIResponse(
            code=400,
            message="Invalid field in update request",
            data=None
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in update_profile: {str(e)}", exc_info=True)
        return error_response(
            code=ErrorCode.SYSTEM_ERROR,
            message=ERROR_MESSAGES[ErrorCode.SYSTEM_ERROR]
        )


# ==================== 7. 修改密码 ====================

@router.post(
    "/change-password",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="修改密码",
    description="用户修改自己的密码，需要提供旧密码验证",
    tags=["认证"]
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    修改密码端点

    参数:
        request: 修改密码请求
        current_user: 当前用户信息
        db: 数据库会话

    返回:
        成功: 200 OK
        失败: 401 未授权 / 400 参数错误

    示例请求:
        POST /api/v1/auth/change-password
        Headers:
            Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        {
            "old_password": "OldPassword123",
            "new_password": "NewPassword123"
        }

    示例响应:
        {
            "code": 200,
            "message": "密码修改成功",
            "data": {
                "message": "密码修改成功",
                "changed_at": "2026-01-17T10:00:00"
            },
            "timestamp": "2026-01-17T10:00:00"
        }
    """
    try:
        auth_service = AuthService(db)

        # 获取用户
        user = auth_service._get_user_by_id(current_user["user_id"])
        if not user:
            raise UserNotFoundError()

        # 验证旧密码
        if not AuthService.verify_password(request.old_password, user.password_hash):
            raise PasswordIncorrectError()

        # 验证新密码不同于旧密码
        if request.old_password == request.new_password:
            raise ValidationError(
                message="新密码不能与旧密码相同",
                errors=[{
                    "field": "new_password",
                    "message": "新密码不能与旧密码相同"
                }]
            )

        # 加密新密码
        new_password_hash = AuthService.hash_password(request.new_password)

        # 更新密码
        from sqlalchemy import text
        now = datetime.utcnow()
        db.execute(
            text("""
                UPDATE users
                SET password_hash = :password_hash,
                    password_changed_at = :now,
                    updated_at = :now
                WHERE user_uuid = :user_id
            """),
            {
                "password_hash": new_password_hash,
                "user_id": current_user["user_id"],
                "now": now
            }
        )
        db.commit()

        response_data = ChangePasswordResponse(
            message="密码修改成功",
            changed_at=datetime.utcnow()
        )

        return APIResponse(
            code=200,
            message="密码修改成功",
            data=response_data
        )

    except (PasswordIncorrectError, ValidationError):
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in change_password: {str(e)}", exc_info=True)
        return error_response(
            code=ErrorCode.SYSTEM_ERROR,
            message=ERROR_MESSAGES[ErrorCode.SYSTEM_ERROR]
        )


# ==================== 8. 重置密码 ====================

@router.post(
    "/reset-password",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="重置密码",
    description="通过验证码重置忘记的密码",
    tags=["认证"]
)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    重置密码端点

    参数:
        request: 重置密码请求
        db: 数据库会话

    返回:
        成功: 200 OK
        失败: 400 参数错误 / 404 用户不存在

    说明:
        1. 用户通过邮箱/手机号收到验证码
        2. 提供验证码和新密码重置密码
        3. 重置成功后需要重新登录

    示例请求:
        POST /api/v1/auth/reset-password
        {
            "identifier": "zhangsan@example.com",
            "verification_code": "123456",
            "new_password": "NewPassword123"
        }

    示例响应:
        {
            "code": 200,
            "message": "密码重置成功",
            "data": {
                "message": "密码重置成功",
                "reset_at": "2026-01-17T10:00:00"
            },
            "timestamp": "2026-01-17T10:00:00"
        }
    """
    try:
        auth_service = AuthService(db)

        # 验证验证码
        try:
            auth_service.verify_code(
                identifier=request.identifier,
                code_type="reset_password",
                code=request.verification_code
            )
        except BusinessException:
            raise ValidationError(
                message="验证码无效或已过期",
                errors=[{
                    "field": "verification_code",
                    "message": "验证码无效或已过期"
                }]
            )

        # 查找用户
        user = (
            auth_service.get_user_by_email(request.identifier) or
            auth_service.get_user_by_phone(request.identifier)
        )

        if not user:
            raise UserNotFoundError()

        # 加密新密码
        new_password_hash = AuthService.hash_password(request.new_password)

        # 更新密码
        from sqlalchemy import text
        now = datetime.utcnow()
        db.execute(
            text("""
                UPDATE users
                SET password_hash = :password_hash,
                    password_changed_at = :now,
                    updated_at = :now
                WHERE id = :user_id
            """),
            {
                "password_hash": new_password_hash,
                "user_id": user.id,
                "now": now
            }
        )
        db.commit()

        response_data = ResetPasswordResponse(
            message="密码重置成功",
            reset_at=datetime.utcnow()
        )

        return APIResponse(
            code=200,
            message="密码重置成功",
            data=response_data
        )

    except (ValidationError, UserNotFoundError):
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in reset_password: {str(e)}", exc_info=True)
        return error_response(
            code=ErrorCode.SYSTEM_ERROR,
            message=ERROR_MESSAGES[ErrorCode.SYSTEM_ERROR]
        )


# ==================== 9. 发送验证码 ====================

@router.post(
    "/send-code",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="发送验证码",
    description="发送邮箱或手机验证码",
    tags=["认证"]
)
async def send_verification_code(
    identifier: str,
    code_type: str,
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    发送验证码端点

    参数:
        identifier: 邮箱或手机号
        code_type: 验证码类型（register/reset_password/login）
        db: 数据库会话

    返回:
        成功: 200 OK

    示例请求:
        POST /api/v1/auth/send-code?identifier=user@example.com&code_type=register

    示例响应:
        {
            "code": 200,
            "message": "验证码已发送",
            "data": {
                "identifier": "user@example.com",
                "code_type": "register",
                "expire_seconds": 300
            }
        }
    """
    try:
        captcha_service = CaptchaService()

        # 判断是邮箱还是手机号
        if "@" in identifier:
            # 邮箱验证码
            code = captcha_service.send_email_code(identifier, code_type)
        else:
            # 手机验证码
            code = captcha_service.send_sms_code(identifier, code_type)

        return APIResponse(
            code=200,
            message="验证码已发送",
            data={
                "identifier": identifier,
                "code_type": code_type,
                "expire_seconds": 300
            }
        )

    except BusinessException as e:
        return APIResponse(
            code=e.code,
            message=e.message,
            data=None
        )
    except Exception as e:
        return APIResponse(
            code=ErrorCode.SYSTEM_ERROR,
            message=ERROR_MESSAGES[ErrorCode.SYSTEM_ERROR],
            data=None
        )


# ==================== 10. 获取图片验证码 ====================

@router.get(
    "/captcha",
    summary="获取图片验证码",
    description="获取图片验证码（用于登录等场景）",
    tags=["认证"]
)
async def get_captcha(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    获取图片验证码端点

    参数:
        session_id: 会话ID（前端生成的唯一标识）
        db: 数据库会话

    返回:
        PNG图片

    示例请求:
        GET /api/v1/auth/captcha?session_id=abc123

    响应:
        Content-Type: image/png
        [PNG图片数据]
    """
    try:
        captcha_service = CaptchaService()

        # 生成验证码
        code, image_buffer = captcha_service.generate_image_captcha()

        # 存储验证码
        captcha_service.store_image_captcha(session_id, code)

        # 返回图片
        return StreamingResponse(
            image_buffer,
            media_type="image/png",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

    except BusinessException as e:
        return APIResponse(
            code=e.code,
            message=e.message,
            data=None
        )
    except Exception as e:
        return APIResponse(
            code=ErrorCode.SYSTEM_ERROR,
            message=ERROR_MESSAGES[ErrorCode.SYSTEM_ERROR],
            data=None
        )


# ==================== 11. 检查用户名/邮箱是否可用 ====================

@router.get(
    "/check-availability",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="检查用户名/邮箱是否可用",
    description="实时验证用户名或邮箱是否已被注册",
    tags=["认证"]
)
async def check_availability(
    field: str,
    value: str,
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    检查用户名/邮箱可用性

    参数:
        field: 字段类型 (username/email)
        value: 字段值
        db: 数据库会话

    返回:
        成功: 200 OK

    示例请求:
        GET /api/v1/auth/check-availability?field=username&value=testuser

    示例响应:
        {
            "code": 200,
            "message": "可用",
            "data": {
                "available": true,
                "field": "username",
                "value": "testuser"
            }
        }
    """
    try:
        auth_service = AuthService(db)

        if field == "username":
            existing = auth_service.get_user_by_username(value)
        elif field == "email":
            existing = auth_service.get_user_by_email(value)
        else:
            return APIResponse(
                code=400,
                message="无效的字段类型",
                data=None
            )

        available = existing is None

        return APIResponse(
            code=200,
            message="可用" if available else "已被使用",
            data={
                "available": available,
                "field": field,
                "value": value
            }
        )

    except Exception as e:
        logger.error(f"Unexpected error in check_availability: {str(e)}", exc_info=True)
        return APIResponse(
            code=ErrorCode.SYSTEM_ERROR,
            message=ERROR_MESSAGES[ErrorCode.SYSTEM_ERROR],
            data=None
        )


