"""
通用Schema定义 - 分页、错误响应等

版本: 1.0
更新日期: 2026-01-17
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, List, Generic, TypeVar
from datetime import datetime


# ==================== 分页参数 ====================

class PaginationParams(BaseModel):
    """统一分页参数"""

    page: int = Field(
        default=1,
        ge=1,
        description="页码，从1开始"
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="每页数量，范围1-100"
    )

    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """获取限制数量"""
        return self.page_size


class SortParams(BaseModel):
    """排序参数"""

    sort_by: str = Field(
        default="created_at",
        description="排序字段"
    )
    sort_order: str = Field(
        default="desc",
        pattern="^(asc|desc)$",
        description="排序顺序：asc/desc"
    )


# ==================== 错误响应 ====================

class ErrorDetail(BaseModel):
    """错误详情"""

    field: str = Field(..., description="错误字段")
    message: str = Field(..., description="错误消息")
    code: Optional[str] = Field(None, description="错误代码")


class ErrorResponse(BaseModel):
    """统一错误响应格式"""

    code: int = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: Optional[List[ErrorDetail]] = Field(
        None,
        description="错误详情列表"
    )
    request_id: Optional[str] = Field(
        None,
        description="请求追踪ID"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="时间戳"
    )


# ==================== 成功响应 ====================

T = TypeVar('T')


class SuccessResponse(BaseModel, Generic[T]):
    """统一成功响应格式"""

    code: int = Field(default=200, description="响应代码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="时间戳"
    )


# ==================== 分页响应 ====================

class PageInfo(BaseModel):
    """分页信息"""

    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total: int = Field(..., description="总记录数")
    total_pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""

    code: int = Field(default=200, description="响应代码")
    message: str = Field(default="success", description="响应消息")
    data: List[T] = Field(default_factory=list, description="数据列表")
    pagination: PageInfo = Field(..., description="分页信息")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="时间戳"
    )


# ==================== ID响应 ====================

class IDResponse(BaseModel):
    """ID响应（用于创建/删除等操作）"""

    id: int = Field(..., description="资源ID")
    message: Optional[str] = Field(None, description="额外消息")


class UUIDResponse(BaseModel):
    """UUID响应"""

    uuid: str = Field(..., description="资源UUID")
    message: Optional[str] = Field(None, description="额外消息")


# ==================== 操作结果响应 ====================

class OperationResponse(BaseModel):
    """操作结果响应"""

    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="操作消息")
    affected_rows: Optional[int] = Field(None, description="影响的行数")


__all__ = [
    "PaginationParams",
    "SortParams",
    "ErrorDetail",
    "ErrorResponse",
    "SuccessResponse",
    "PageInfo",
    "PaginatedResponse",
    "IDResponse",
    "UUIDResponse",
    "OperationResponse",
]
