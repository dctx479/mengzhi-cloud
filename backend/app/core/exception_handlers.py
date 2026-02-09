"""
统一异常处理器

P1-10: 提供全局异常处理，避免在每个API端点重复异常处理代码

版本: 1.0
创建日期: 2026-01-23
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from loguru import logger
import uuid
from typing import Union

from app.core.errors import BusinessException, ErrorCode, ERROR_HTTP_STATUS
from app.core.responses import error_response


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

    处理Pydantic的ValidationError，返回友好的错误信息

    Args:
        request: FastAPI请求对象
        exc: 验证异常对象

    Returns:
        JSON格式的错误响应
    """
    from pydantic import ValidationError

    if isinstance(exc, ValidationError):
        # 提取验证错误详情
        errors = []
        for error in exc.errors():
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
                code=ErrorCode.INVALID_PARAMETER,
                message="参数验证失败",
                errors=errors,
                request_id=str(uuid.uuid4())
            ).model_dump(mode='json')
        )

    # 如果不是ValidationError，返回通用错误
    return await general_exception_handler(request, exc)


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

    # 注册通用异常处理器（捕获所有未处理的异常）
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("异常处理器注册完成")
