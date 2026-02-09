"""
审计日志装饰器

自动记录API调用的审计日志

版本: 1.0
创建日期: 2026-01-22
"""

from functools import wraps
from typing import Optional, Callable, Any
from fastapi import Request, Response
from sqlalchemy.orm import Session
import json
import inspect

from app.services.audit_service import AuditService
from app.core.logging_config import logger


def audit_log(
    action: str,
    resource: str,
    get_resource_id: Optional[Callable] = None,
    capture_request_body: bool = False,
    capture_response_body: bool = False
):
    """
    审计日志装饰器

    自动记录API调用的审计日志，包括：
    - 操作类型和资源类型
    - 操作用户信息
    - 请求信息（IP、User-Agent、方法、路径）
    - 响应状态
    - 操作前后数据对比（可选）

    参数:
        action: 操作类型（create/update/delete/read等）
        resource: 资源类型（product/user/enterprise等）
        get_resource_id: 从函数参数中提取资源ID的回调函数
        capture_request_body: 是否捕获请求体
        capture_response_body: 是否捕获响应体

    示例:
        @router.post("/products")
        @audit_log(action="create", resource="product")
        async def create_product(
            product_data: ProductCreate,
            current_user: dict = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            ...

        @router.put("/products/{product_id}")
        @audit_log(
            action="update",
            resource="product",
            get_resource_id=lambda kwargs: kwargs.get("product_id"),
            capture_request_body=True
        )
        async def update_product(
            product_id: int,
            product_data: ProductUpdate,
            current_user: dict = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # 提取依赖注入的参数
            request: Optional[Request] = None
            db: Optional[Session] = None
            current_user: Optional[dict] = None

            # 从参数中提取
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif isinstance(arg, Session):
                    db = arg
                elif isinstance(arg, dict) and "user_id" in arg:
                    current_user = arg

            # 从关键字参数中提取
            request = request or kwargs.get("request")
            db = db or kwargs.get("db")
            current_user = current_user or kwargs.get("current_user")

            # 提取资源ID
            resource_id = None
            if get_resource_id:
                try:
                    resource_id = get_resource_id(kwargs)
                except Exception as e:
                    logger.warning(f"提取资源ID失败: {str(e)}")

            # 提取请求信息
            ip_address = None
            user_agent = None
            request_method = None
            request_path = None

            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
                request_method = request.method
                request_path = str(request.url.path)

            # 提取用户信息
            user_id = None
            username = None
            if current_user:
                user_id = current_user.get("user_id")
                username = current_user.get("username")

            # 捕获请求体
            request_body = None
            if capture_request_body and request:
                try:
                    # 尝试从kwargs中获取请求数据
                    for key, value in kwargs.items():
                        if hasattr(value, "dict"):
                            request_body = value.dict()
                            break
                        elif hasattr(value, "__dict__") and not isinstance(value, (Request, Session)):
                            request_body = value.__dict__
                            break
                except Exception as e:
                    logger.warning(f"捕获请求体失败: {str(e)}")

            # 执行原函数
            is_success = True
            error_message = None
            status_code = 200
            response_body = None

            try:
                result = await func(*args, **kwargs)

                # 捕获响应体
                if capture_response_body:
                    try:
                        if hasattr(result, "dict"):
                            response_body = result.dict()
                        elif isinstance(result, dict):
                            response_body = result
                    except Exception as e:
                        logger.warning(f"捕获响应体失败: {str(e)}")

                # 如果结果中包含资源ID，尝试提取
                if not resource_id and isinstance(result, dict):
                    resource_id = result.get("id") or result.get("data", {}).get("id")

                return result

            except Exception as e:
                is_success = False
                error_message = str(e)
                status_code = 500
                raise

            finally:
                # 记录审计日志
                if db:
                    try:
                        # 构建变更内容
                        changes = {}
                        if request_body:
                            changes["request"] = request_body
                        if response_body:
                            changes["response"] = response_body

                        # 构建详情
                        details = f"{action} {resource}"
                        if resource_id:
                            details += f" (ID: {resource_id})"

                        AuditService.log(
                            db=db,
                            user_id=user_id,
                            username=username,
                            action=action,
                            resource=resource,
                            resource_id=resource_id,
                            details=details,
                            changes=changes if changes else None,
                            ip=ip_address,
                            user_agent=user_agent,
                            request_method=request_method,
                            request_path=request_path,
                            status_code=status_code,
                            is_success=is_success,
                            error_message=error_message
                        )
                    except Exception as e:
                        logger.error(f"记录审计日志失败: {str(e)}")

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # 同步函数的包装器（类似逻辑）
            # 提取依赖注入的参数
            request: Optional[Request] = None
            db: Optional[Session] = None
            current_user: Optional[dict] = None

            # 从参数中提取
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif isinstance(arg, Session):
                    db = arg
                elif isinstance(arg, dict) and "user_id" in arg:
                    current_user = arg

            # 从关键字参数中提取
            request = request or kwargs.get("request")
            db = db or kwargs.get("db")
            current_user = current_user or kwargs.get("current_user")

            # 提取资源ID
            resource_id = None
            if get_resource_id:
                try:
                    resource_id = get_resource_id(kwargs)
                except Exception as e:
                    logger.warning(f"提取资源ID失败: {str(e)}")

            # 提取请求信息
            ip_address = None
            user_agent = None
            request_method = None
            request_path = None

            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
                request_method = request.method
                request_path = str(request.url.path)

            # 提取用户信息
            user_id = None
            username = None
            if current_user:
                user_id = current_user.get("user_id")
                username = current_user.get("username")

            # 捕获请求体
            request_body = None
            if capture_request_body and request:
                try:
                    for key, value in kwargs.items():
                        if hasattr(value, "dict"):
                            request_body = value.dict()
                            break
                        elif hasattr(value, "__dict__") and not isinstance(value, (Request, Session)):
                            request_body = value.__dict__
                            break
                except Exception as e:
                    logger.warning(f"捕获请求体失败: {str(e)}")

            # 执行原函数
            is_success = True
            error_message = None
            status_code = 200
            response_body = None

            try:
                result = func(*args, **kwargs)

                # 捕获响应体
                if capture_response_body:
                    try:
                        if hasattr(result, "dict"):
                            response_body = result.dict()
                        elif isinstance(result, dict):
                            response_body = result
                    except Exception as e:
                        logger.warning(f"捕获响应体失败: {str(e)}")

                # 如果结果中包含资源ID，尝试提取
                if not resource_id and isinstance(result, dict):
                    resource_id = result.get("id") or result.get("data", {}).get("id")

                return result

            except Exception as e:
                is_success = False
                error_message = str(e)
                status_code = 500
                raise

            finally:
                # 记录审计日志
                if db:
                    try:
                        # 构建变更内容
                        changes = {}
                        if request_body:
                            changes["request"] = request_body
                        if response_body:
                            changes["response"] = response_body

                        # 构建详情
                        details = f"{action} {resource}"
                        if resource_id:
                            details += f" (ID: {resource_id})"

                        AuditService.log(
                            db=db,
                            user_id=user_id,
                            username=username,
                            action=action,
                            resource=resource,
                            resource_id=resource_id,
                            details=details,
                            changes=changes if changes else None,
                            ip=ip_address,
                            user_agent=user_agent,
                            request_method=request_method,
                            request_path=request_path,
                            status_code=status_code,
                            is_success=is_success,
                            error_message=error_message
                        )
                    except Exception as e:
                        logger.error(f"记录审计日志失败: {str(e)}")

        # 根据函数类型返回对应的包装器
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def get_client_ip(request: Request) -> str:
    """
    获取客户端真实IP地址

    考虑代理和负载均衡器的情况

    参数:
        request: FastAPI Request对象

    返回:
        客户端IP地址
    """
    # 尝试从X-Forwarded-For头获取
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For可能包含多个IP，取第一个
        return forwarded_for.split(",")[0].strip()

    # 尝试从X-Real-IP头获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # 使用直接连接的IP
    if request.client:
        return request.client.host

    return "unknown"
