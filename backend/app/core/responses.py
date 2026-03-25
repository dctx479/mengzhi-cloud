"""
统一响应格式定义

版本: 1.0
更新日期: 2026-01-17
"""

from pydantic import BaseModel, Field
from typing import TypeVar, Generic, Optional, List, Any
from datetime import datetime
import uuid

T = TypeVar("T")


class FieldError(BaseModel):
    """字段错误信息"""

    field: str = Field(..., description="字段名称")
    message: str = Field(..., description="错误消息")


class APIResponse(BaseModel, Generic[T]):
    """标准API响应格式"""

    code: int = Field(default=200, description="业务状态码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "success",
                "data": {},
                "timestamp": "2026-01-17T10:00:00"
            }
        }


class ErrorResponse(BaseModel):
    """错误响应格式"""

    code: int = Field(..., description="错误码")
    message: str = Field(..., description="错误消息")
    data: Optional[Any] = Field(default=None, description="数据为空")
    errors: Optional[List[FieldError]] = Field(default=None, description="字段错误详情")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间戳")
    request_id: Optional[str] = Field(default=None, description="请求ID")

    class Config:
        json_schema_extra = {
            "example": {
                "code": 10001,
                "message": "参数验证失败",
                "data": None,
                "errors": [
                    {
                        "field": "email",
                        "message": "邮箱格式不正确"
                    }
                ],
                "timestamp": "2026-01-17T10:00:00",
                "request_id": "uuid-v4"
            }
        }


class PaginationInfo(BaseModel):
    """分页信息"""

    page: int = Field(..., ge=1, description="当前页码")
    size: int = Field(..., ge=1, le=100, description="每页数量")
    total: int = Field(..., ge=0, description="总记录数")
    pages: int = Field(..., ge=0, description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


class PaginatedData(BaseModel, Generic[T]):
    """分页数据容器"""

    items: List[T] = Field(default_factory=list, description="数据项列表")
    pagination: PaginationInfo = Field(..., description="分页信息")


def success_response(data: Any = None, message: str = "success") -> APIResponse:
    """生成成功响应"""
    return APIResponse(code=200, message=message, data=data)


def error_response(
    code: int,
    message: str,
    errors: Optional[List[FieldError]] = None,
    request_id: Optional[str] = None
) -> ErrorResponse:
    """生成错误响应"""
    return ErrorResponse(
        code=code,
        message=message,
        errors=errors,
        request_id=request_id or str(uuid.uuid4())
    )


def paginated_response(
    items: List[Any],
    page: int,
    size: int,
    total: int,
    message: str = "success"
) -> APIResponse:
    """生成分页响应"""
    pages = (total + size - 1) // size if size > 0 else 0

    pagination = PaginationInfo(
        page=page,
        size=size,
        total=total,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )

    data = PaginatedData(items=items, pagination=pagination)
    return APIResponse(code=200, message=message, data=data)
