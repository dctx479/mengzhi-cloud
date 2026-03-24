"""
统一异常处理器

P1-10: 提供全局异常处理，避免在每个API端点重复异常处理代码
P1修复: 增加服务层装饰器，细粒度异常映射

版本: 1.1
创建日期: 2026-01-23
更新日期: 2026-02-10
"""

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
import uuid
from typing import Union, Callable, TypeVar, Any
from functools import wraps
import asyncio

from app.core.errors import (
    BusinessException, ErrorCode, ERROR_HTTP_STATUS,
    DatabaseError, DuplicateRecordError, ExternalServiceError
)
from app.core.responses import error_response

# 导入常见异常类型
try:
    from sqlalchemy.exc import (
        SQLAlchemyError, IntegrityError, OperationalError,
        DataError, ProgrammingError
    )
except ImportError:
    SQLAlchemyError = IntegrityError = OperationalError = DataError = ProgrammingError = Exception

try:
    from redis.exceptions import RedisError, ConnectionError as RedisConnectionError
except ImportError:
    RedisError = RedisConnectionError = Exception

try:
    from httpx import HTTPError, TimeoutException
except ImportError:
    HTTPError = TimeoutException = Exception


T = TypeVar('T')


# ==================== 服务层异常处理装饰器 ====================

def handle_service_exceptions(operation_name: str = "操作") -> Callable:
    """
    服务层统一异常处理装饰器

    将各类底层异常转换为具体的业务异常，避免笼统的 except Exception

    P1修复: 解决笼统异常捕获问题，提供具体的异常类型映射

    Args:
        operation_name: 操作名称，用于日志记录和错误消息

    使用示例:
        @handle_service_exceptions("创建订单")
        def create_order(self, data):
            ...

        @handle_service_exceptions("查询用户")
        async def get_user(self, user_id):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except BusinessException:
                raise  # 业务异常直接重新抛出
            except IntegrityError as e:
                logger.warning(f"{operation_name}失败 - 数据库约束冲突: {e}")
                raise DuplicateRecordError("数据") from e
            except OperationalError as e:
                logger.error(f"{operation_name}失败 - 数据库连接错误: {e}")
                raise DatabaseError("数据库连接异常，请稍后重试") from e
            except DataError as e:
                logger.warning(f"{operation_name}失败 - 数据类型错误: {e}")
                raise BusinessException(code=ErrorCode.PARAM_TYPE_ERROR, message="数据格式错误") from e
            except SQLAlchemyError as e:
                logger.error(f"{operation_name}失败 - 数据库错误: {e}")
                raise DatabaseError(f"{operation_name}失败，请稍后重试") from e
            except RedisConnectionError as e:
                logger.error(f"{operation_name}失败 - Redis连接错误: {e}")
                raise ExternalServiceError("缓存服务暂时不可用") from e
            except RedisError as e:
                logger.warning(f"{operation_name}失败 - Redis错误: {e}")
                raise ExternalServiceError("缓存操作失败") from e
            except TimeoutException as e:
                logger.warning(f"{operation_name}失败 - 请求超时: {e}")
                raise ExternalServiceError("外部服务请求超时") from e
            except HTTPError as e:
                logger.error(f"{operation_name}失败 - HTTP请求错误: {e}")
                raise ExternalServiceError("外部服务请求失败") from e
            except ValueError as e:
                logger.warning(f"{operation_name}失败 - 参数错误: {e}")
                raise BusinessException(code=ErrorCode.PARAM_VALUE_INVALID, message=str(e)) from e
            except Exception as e:
                logger.exception(f"{operation_name}失败 - 未预期的异常: {type(e).__name__}: {e}")
                raise BusinessException(code=ErrorCode.INTERNAL_ERROR, message=f"{operation_name}失败，请稍后重试") from e

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except BusinessException:
                raise
            except IntegrityError as e:
                logger.warning(f"{operation_name}失败 - 数据库约束冲突: {e}")
                raise DuplicateRecordError("数据") from e
            except OperationalError as e:
                logger.error(f"{operation_name}失败 - 数据库连接错误: {e}")
                raise DatabaseError("数据库连接异常，请稍后重试") from e
            except DataError as e:
                logger.warning(f"{operation_name}失败 - 数据类型错误: {e}")
                raise BusinessException(code=ErrorCode.PARAM_TYPE_ERROR, message="数据格式错误") from e
            except SQLAlchemyError as e:
                logger.error(f"{operation_name}失败 - 数据库错误: {e}")
                raise DatabaseError(f"{operation_name}失败，请稍后重试") from e
            except RedisConnectionError as e:
                logger.error(f"{operation_name}失败 - Redis连接错误: {e}")
                raise ExternalServiceError("缓存服务暂时不可用") from e
            except RedisError as e:
                logger.warning(f"{operation_name}失败 - Redis错误: {e}")
                raise ExternalServiceError("缓存操作失败") from e
            except TimeoutException as e:
                logger.warning(f"{operation_name}失败 - 请求超时: {e}")
                raise ExternalServiceError("外部服务请求超时") from e
            except HTTPError as e:
                logger.error(f"{operation_name}失败 - HTTP请求错误: {e}")
                raise ExternalServiceError("外部服务请求失败") from e
            except ValueError as e:
                logger.warning(f"{operation_name}失败 - 参数错误: {e}")
                raise BusinessException(code=ErrorCode.PARAM_VALUE_INVALID, message=str(e)) from e
            except Exception as e:
                logger.exception(f"{operation_name}失败 - 未预期的异常: {type(e).__name__}: {e}")
                raise BusinessException(code=ErrorCode.INTERNAL_ERROR, message=f"{operation_name}失败，请稍后重试") from e

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# ==================== 全局异常处理器 ====================


async def business_exception_handler(
    request: Request,
    exc: BusinessException
) -> JSONResponse:
    """业务异常处理器

    处理所有BusinessException类型的异常，返回统一格式的错误响应

    Args:
        request: FastAPI请求对象
        exc: 业务异常对象

    Returns:
        JSON格式的错误响应
    """
    # 记录业务异常日志
    logger.warning(
        f"业务异常: {exc.message} | "
        f"code={exc.code} | "
        f"path={request.url.path} | "
        f"method={request.method} | "
        f"request_id={exc.request_id}"
    )

    # 获取HTTP状态码
    http_status = ERROR_HTTP_STATUS.get(exc.code, status.HTTP_400_BAD_REQUEST)

    # 返回统一格式的错误响应
    return JSONResponse(
        status_code=http_status,
        content=error_response(
            code=exc.code,
            message=exc.message,
            errors=exc.errors,
            request_id=exc.request_id or str(uuid.uuid4())
        ).model_dump(mode='json')
    )


async def validation_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """参数验证异常处理器

    处理Pydantic和FastAPI请求验证异常，返回友好的错误信息
    """
    validation_errors = []

    if isinstance(exc, RequestValidationError):
        validation_errors = exc.errors()
    else:
        from pydantic import ValidationError
        if isinstance(exc, ValidationError):
            validation_errors = exc.errors()
        else:
            return await general_exception_handler(request, exc)

    errors = []
    for error in validation_errors:
        field = '.'.join(str(loc) for loc in error['loc'])
        errors.append({
            'field': field,
            'message': error['msg'],
            'type': error['type']
        })

    logger.warning(
        f"参数验证失败: path={request.url.path} | "
        f"method={request.method} | "
        f"errors={errors}"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(
            code=ErrorCode.PARAM_VALIDATION_FAILED,
            message="参数验证失败",
            errors=errors,
            request_id=str(uuid.uuid4())
        ).model_dump(mode='json')
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """通用异常处理器

    处理所有未被捕获的异常，记录详细日志并返回通用错误响应

    Args:
        request: FastAPI请求对象
        exc: 异常对象

    Returns:
        JSON格式的错误响应
    """
    # 生成请求ID
    request_id = str(uuid.uuid4())

    # 记录详细的异常信息
    logger.error(
        f"未处理异常: {type(exc).__name__}: {str(exc)} | "
        f"path={request.url.path} | "
        f"method={request.method} | "
        f"request_id={request_id}",
        exc_info=True  # 包含完整的堆栈跟踪
    )

    # 返回通用错误响应（不暴露内部错误详情）
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            code=ErrorCode.SYSTEM_ERROR,
            message="系统内部错误，请稍后重试",
            request_id=request_id
        ).model_dump(mode='json')
    )


def register_exception_handlers(app) -> None:
    """注册所有异常处理器到FastAPI应用

    Args:
        app: FastAPI应用实例
    """
    from pydantic import ValidationError

    # 注册业务异常处理器
    app.add_exception_handler(BusinessException, business_exception_handler)

    # 注册参数验证异常处理器
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # 注册通用异常处理器（捕获所有未处理的异常）
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("异常处理器注册完成")
