"""
API依赖注入和中间件

版本: 1.0
更新日期: 2026-01-17
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from jose.exceptions import JWTError

from app.core.config import settings
from app.core.errors import (
    BusinessException,
    TokenExpiredError,
    ErrorCode,
    ERROR_HTTP_STATUS,
)
from app.services.auth_service import AuthService
from app.database import SessionLocal, engine, get_db


# ==================== 数据库会话 ====================
# engine/SessionLocal/get_db 统一由 app.database 提供，此处直接复用


# ==================== 认证依赖 ====================

def get_token_from_request(request: Request) -> str:
    """
    从请求头中获取Token

    参数:
        request: FastAPI Request对象

    返回:
        JWT Token字符串

    异常:
        HTTPException: Token缺失或格式不正确
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺失认证令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌格式",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return parts[1]


def get_current_user(
    request: Request,
    token: str = Depends(get_token_from_request),
    db: Session = Depends(get_db)
) -> dict:
    """
    获取当前登录用户信息

    参数:
        request: FastAPI Request对象
        token: JWT Token
        db: 数据库会话

    返回:
        用户信息字典，包含:
        - user_id: 用户UUID
        - user_type: 用户类型
        - role: 用户角色
        - tenant_id: 租户ID（可选）

    异常:
        HTTPException: Token无效、过期或用户不存在

    示例:
        @router.get("/users/me")
        async def get_profile(current_user: dict = Depends(get_current_user)):
            return {"user_id": current_user["user_id"]}
    """
    auth_service = AuthService(db)

    try:
        # 解码Token
        payload = auth_service.decode_token(token)

        # 验证Token类型
        token_type = payload.get("type")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌类型"
            )

        # 获取用户信息
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌载荷"
            )

        # 返回用户信息
        return {
            "user_id": user_id,
            "user_type": payload.get("user_type"),
            "role": payload.get("role"),
            "tenant_id": payload.get("tenant_id"),
            "jti": payload.get("jti")
        }

    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证令牌已过期，请重新登录",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except BusinessException as e:
        http_status = ERROR_HTTP_STATUS.get(e.code, 401)
        raise HTTPException(
            status_code=http_status,
            detail=e.message
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[dict]:
    """
    获取当前用户（可选，如果不存在则返回None）

    参数:
        request: FastAPI Request对象
        db: 数据库会话

    返回:
        用户信息字典或None

    示例:
        @router.get("/products")
        async def list_products(user: Optional[dict] = Depends(get_optional_user)):
            ...
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None

    try:
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        token = parts[1]
        auth_service = AuthService(db)
        payload = auth_service.decode_token(token)

        return {
            "user_id": payload.get("sub"),
            "user_type": payload.get("user_type"),
            "role": payload.get("role"),
            "tenant_id": payload.get("tenant_id")
        }
    except (TokenExpiredError, BusinessException, JWTError):
        return None


# ==================== 权限检查 ====================

def require_role(*allowed_roles: str):
    """
    要求特定角色

    参数:
        allowed_roles: 允许的角色列表

    返回:
        依赖注入函数

    示例:
        @router.post("/admin/users")
        async def create_user(
            current_user: dict = Depends(get_current_user),
            _: None = Depends(require_role("admin", "enterprise_admin"))
        ):
            ...
    """
    async def check_role(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        return current_user

    return check_role


def require_user_type(*allowed_types: str):
    """
    要求特定用户类型

    参数:
        allowed_types: 允许的用户类型列表

    返回:
        依赖注入函数

    示例:
        @router.post("/enterprise/settings")
        async def update_settings(
            current_user: dict = Depends(get_current_user),
            _: None = Depends(require_user_type("enterprise"))
        ):
            ...
    """
    async def check_user_type(current_user: dict = Depends(get_current_user)):
        if current_user["user_type"] not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="该操作仅限特定用户类型"
            )
        return current_user

    return check_user_type


# ==================== 管理员权限检查 ====================

async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    要求管理员权限

    参数:
        current_user: 当前用户信息

    返回:
        当前用户信息

    异常:
        HTTPException: 权限不足

    示例:
        @router.post("/admin/users")
        async def create_user(
            current_user: dict = Depends(require_admin)
        ):
            ...
    """
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def require_enterprise_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    要求企业管理员权限

    参数:
        current_user: 当前用户信息

    返回:
        当前用户信息

    异常:
        HTTPException: 权限不足
    """
    if current_user["role"] not in ["admin", "enterprise_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要企业管理员权限"
        )
    return current_user


# ==================== 租户隔离 ====================

def get_tenant_id(
    current_user: dict = Depends(get_current_user)
) -> str:
    """
    获取当前用户的租户ID

    参数:
        current_user: 当前用户信息

    返回:
        租户ID

    异常:
        HTTPException: 用户不是企业用户

    说明:
        用于确保企业用户的数据隔离
    """
    tenant_id = current_user.get("tenant_id")

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="该操作需要企业用户身份"
        )

    return tenant_id


# ==================== RBAC权限验证 ====================

def require_permission(resource: str, action: str):
    """
    基于RBAC的权限验证装饰器

    参数:
        resource: 资源名称，如 product, user, chat
        action: 操作名称，如 create, read, update, delete

    返回:
        依赖注入函数

    示例:
        from app.api.deps import require_permission

        @router.post("/products")
        async def create_product(
            product_data: ProductCreate,
            current_user: dict = Depends(require_permission("product", "create")),
            db: Session = Depends(get_db)
        ):
            ...

    说明:
        - 检查用户是否通过角色拥有指定权限
        - 管理员（role=admin）自动拥有所有权限
        - 返回当前用户信息供后续使用
    """
    async def permission_checker(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> dict:
        # 管理员拥有所有权限
        if current_user.get("role") == "admin":
            return current_user

        # 获取用户ID（从UUID转换为数据库ID）
        from app.models import User
        user = db.query(User).filter(User.user_uuid == current_user["user_id"]).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 检查用户是否有指定权限
        has_permission = user.has_permission(resource, action)

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要 {resource}:{action} 权限"
            )

        return current_user

    return permission_checker


def check_permission(
    user_id: int,
    resource: str,
    action: str,
    db: Session
) -> bool:
    """
    检查用户是否有指定权限（工具函数）

    参数:
        user_id: 用户数据库ID
        resource: 资源名称
        action: 操作名称
        db: 数据库会话

    返回:
        bool: 是否有权限

    示例:
        if check_permission(user.id, "product", "delete", db):
            # 执行删除操作
            pass
    """
    from app.models import User

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    # 管理员拥有所有权限
    if user.role.value == "admin":
        return True

    return user.has_permission(resource, action)


# ==================== 速率限制（可选） ====================

def rate_limit_dependency(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user)
) -> None:
    """
    速率限制检查（可选实现）

    参数:
        request: FastAPI Request对象
        db: 数据库会话
        current_user: 当前用户信息

    异常:
        HTTPException: 请求过于频繁
    """
    # 这是一个可选的速率限制实现
    # 具体实现需要根据业务需求进行配置
    pass


__all__ = [
    "get_db",
    "get_token_from_request",
    "get_current_user",
    "get_optional_user",
    "require_role",
    "require_user_type",
    "require_admin",
    "require_enterprise_admin",
    "get_tenant_id",
    "require_permission",
    "check_permission",
]
