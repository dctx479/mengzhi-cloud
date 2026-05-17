"""
错误码枚举和异常定义

版本: 1.0
更新日期: 2026-01-17
"""

from enum import IntEnum
from typing import List, Optional


class ErrorCode(IntEnum):
    """错误码枚举 - 参考API设计规范"""

    # 参数错误 10xxx
    PARAM_ERROR = 10000
    PARAM_VALIDATION_FAILED = 10001
    PARAM_MISSING = 10002
    PARAM_TYPE_ERROR = 10003
    PARAM_FORMAT_ERROR = 10004
    PARAM_VALUE_INVALID = 10005
    PARAM_LENGTH_EXCEEDED = 10006
    PARAM_DUPLICATE = 10007
    FILE_TYPE_NOT_ALLOWED = 10008
    FILE_SIZE_EXCEEDED = 10009
    JSON_PARSE_ERROR = 10010

    # 认证授权错误 20xxx
    AUTH_ERROR = 20000
    TOKEN_MISSING = 20001
    TOKEN_INVALID = 20002
    TOKEN_EXPIRED = 20003
    TOKEN_REVOKED = 20004
    REFRESH_TOKEN_INVALID = 20005
    REFRESH_TOKEN_EXPIRED = 20006
    USER_NOT_FOUND = 20010
    PASSWORD_INCORRECT = 20011
    ACCOUNT_DISABLED = 20012
    ACCOUNT_LOCKED = 20013
    LOGIN_TOO_FREQUENT = 20014
    VERIFICATION_CODE_INVALID = 20015
    VERIFICATION_CODE_EXPIRED = 20016
    PERMISSION_DENIED = 20020
    RESOURCE_ACCESS_DENIED = 20021
    ROLE_NOT_ALLOWED = 20022

    # 数据库错误 40xxx
    DB_ERROR = 40000
    DB_CONNECTION_FAILED = 40001
    DB_QUERY_FAILED = 40002
    DB_INSERT_FAILED = 40003
    DB_UPDATE_FAILED = 40004
    DB_DELETE_FAILED = 40005
    DB_DUPLICATE_ENTRY = 40006
    RECORD_NOT_FOUND = 40010
    RECORD_ALREADY_EXISTS = 40011

    # 配额错误 30xxx
    QUOTA_ERROR = 30000
    QUOTA_EXCEEDED = 30001
    QUOTA_NOT_FOUND = 30002
    QUOTA_DEDUCT_FAILED = 30003
    QUOTA_DISABLED = 30004

    # 风控错误 35xxx
    RISK_CONTROL_BLOCKED = 35000
    RISK_CONTROL_REVIEW_REQUIRED = 35001
    RISK_CONTROL_SERVICE_ERROR = 35002

    # 系统错误 50xxx
    SYSTEM_ERROR = 50000
    INTERNAL_ERROR = 50001
    SERVICE_UNAVAILABLE = 50002


# 错误码对应的HTTP状态码
ERROR_HTTP_STATUS = {
    # 参数错误 10xxx -> 400
    ErrorCode.PARAM_ERROR: 400,
    ErrorCode.PARAM_VALIDATION_FAILED: 400,
    ErrorCode.PARAM_MISSING: 400,
    ErrorCode.PARAM_TYPE_ERROR: 400,
    ErrorCode.PARAM_FORMAT_ERROR: 400,
    ErrorCode.PARAM_VALUE_INVALID: 400,
    ErrorCode.PARAM_LENGTH_EXCEEDED: 400,
    ErrorCode.PARAM_DUPLICATE: 400,
    ErrorCode.FILE_TYPE_NOT_ALLOWED: 400,
    ErrorCode.FILE_SIZE_EXCEEDED: 400,
    ErrorCode.JSON_PARSE_ERROR: 400,

    # 认证授权错误 20xxx -> 401/403/404
    ErrorCode.AUTH_ERROR: 401,
    ErrorCode.TOKEN_EXPIRED: 401,
    ErrorCode.TOKEN_INVALID: 401,
    ErrorCode.TOKEN_MISSING: 401,
    ErrorCode.TOKEN_REVOKED: 401,
    ErrorCode.REFRESH_TOKEN_INVALID: 401,
    ErrorCode.REFRESH_TOKEN_EXPIRED: 401,
    ErrorCode.USER_NOT_FOUND: 404,
    ErrorCode.PASSWORD_INCORRECT: 401,
    ErrorCode.ACCOUNT_DISABLED: 403,
    ErrorCode.ACCOUNT_LOCKED: 403,
    ErrorCode.LOGIN_TOO_FREQUENT: 429,
    ErrorCode.VERIFICATION_CODE_INVALID: 400,
    ErrorCode.VERIFICATION_CODE_EXPIRED: 400,
    ErrorCode.PERMISSION_DENIED: 403,
    ErrorCode.RESOURCE_ACCESS_DENIED: 403,
    ErrorCode.ROLE_NOT_ALLOWED: 403,

    # 数据库错误 40xxx -> 500
    ErrorCode.DB_ERROR: 500,
    ErrorCode.DB_CONNECTION_FAILED: 500,
    ErrorCode.DB_QUERY_FAILED: 500,
    ErrorCode.DB_INSERT_FAILED: 500,
    ErrorCode.DB_UPDATE_FAILED: 500,
    ErrorCode.DB_DELETE_FAILED: 500,
    ErrorCode.DB_DUPLICATE_ENTRY: 409,
    ErrorCode.RECORD_NOT_FOUND: 404,
    ErrorCode.RECORD_ALREADY_EXISTS: 409,

    # 配额错误 30xxx -> 429/403/404/500
    ErrorCode.QUOTA_ERROR: 429,
    ErrorCode.QUOTA_EXCEEDED: 429,
    ErrorCode.QUOTA_NOT_FOUND: 404,
    ErrorCode.QUOTA_DEDUCT_FAILED: 500,
    ErrorCode.QUOTA_DISABLED: 403,

    # 风控错误 35xxx -> 403/202/500
    ErrorCode.RISK_CONTROL_BLOCKED: 403,
    ErrorCode.RISK_CONTROL_REVIEW_REQUIRED: 202,
    ErrorCode.RISK_CONTROL_SERVICE_ERROR: 500,

    # 系统错误 50xxx -> 500/503
    ErrorCode.SYSTEM_ERROR: 500,
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
}

# 错误码对应的默认消息
ERROR_MESSAGES = {
    # 参数错误 10xxx
    ErrorCode.PARAM_ERROR: "参数错误",
    ErrorCode.PARAM_VALIDATION_FAILED: "参数验证失败",
    ErrorCode.PARAM_MISSING: "缺少必要参数",
    ErrorCode.PARAM_TYPE_ERROR: "参数类型错误",
    ErrorCode.PARAM_FORMAT_ERROR: "参数格式错误",
    ErrorCode.PARAM_VALUE_INVALID: "参数值无效",
    ErrorCode.PARAM_LENGTH_EXCEEDED: "参数长度超限",
    ErrorCode.PARAM_DUPLICATE: "参数重复",
    ErrorCode.FILE_TYPE_NOT_ALLOWED: "不支持的文件类型",
    ErrorCode.FILE_SIZE_EXCEEDED: "文件过大",
    ErrorCode.JSON_PARSE_ERROR: "JSON解析错误",

    # 认证授权错误 20xxx
    ErrorCode.AUTH_ERROR: "认证错误",
    ErrorCode.TOKEN_MISSING: "未提供认证令牌",
    ErrorCode.TOKEN_INVALID: "无效的认证令牌",
    ErrorCode.TOKEN_EXPIRED: "认证令牌已过期，请重新登录",
    ErrorCode.TOKEN_REVOKED: "认证令牌已被撤销",
    ErrorCode.REFRESH_TOKEN_INVALID: "无效的刷新令牌",
    ErrorCode.REFRESH_TOKEN_EXPIRED: "刷新令牌已过期",
    ErrorCode.USER_NOT_FOUND: "用户不存在",
    ErrorCode.PASSWORD_INCORRECT: "密码错误",
    ErrorCode.ACCOUNT_DISABLED: "账号已禁用",
    ErrorCode.ACCOUNT_LOCKED: "账号已锁定，请稍后再试",
    ErrorCode.LOGIN_TOO_FREQUENT: "登录过于频繁，请稍后再试",
    ErrorCode.VERIFICATION_CODE_INVALID: "验证码无效",
    ErrorCode.VERIFICATION_CODE_EXPIRED: "验证码已过期",
    ErrorCode.PERMISSION_DENIED: "权限不足",
    ErrorCode.RESOURCE_ACCESS_DENIED: "无法访问该资源",
    ErrorCode.ROLE_NOT_ALLOWED: "角色不允许执行此操作",

    # 数据库错误 40xxx
    ErrorCode.DB_ERROR: "数据库操作失败",
    ErrorCode.DB_CONNECTION_FAILED: "数据库连接失败",
    ErrorCode.DB_QUERY_FAILED: "数据库查询失败",
    ErrorCode.DB_INSERT_FAILED: "数据插入失败",
    ErrorCode.DB_UPDATE_FAILED: "数据更新失败",
    ErrorCode.DB_DELETE_FAILED: "数据删除失败",
    ErrorCode.DB_DUPLICATE_ENTRY: "数据已存在",
    ErrorCode.RECORD_NOT_FOUND: "记录不存在",
    ErrorCode.RECORD_ALREADY_EXISTS: "用户名/邮箱/手机号已被注册",

    # 配额错误 30xxx
    ErrorCode.QUOTA_ERROR: "配额错误",
    ErrorCode.QUOTA_EXCEEDED: "配额已用完，请升级套餐或等待配额重置",
    ErrorCode.QUOTA_NOT_FOUND: "配额不存在",
    ErrorCode.QUOTA_DEDUCT_FAILED: "配额扣减失败",
    ErrorCode.QUOTA_DISABLED: "配额已禁用",

    # 风控错误 35xxx
    ErrorCode.RISK_CONTROL_BLOCKED: "操作被风控系统拦截",
    ErrorCode.RISK_CONTROL_REVIEW_REQUIRED: "操作需要人工审核",
    ErrorCode.RISK_CONTROL_SERVICE_ERROR: "风控服务异常",

    # 系统错误 50xxx
    ErrorCode.SYSTEM_ERROR: "系统错误，请稍后再试",
    ErrorCode.INTERNAL_ERROR: "内部服务器错误",
    ErrorCode.SERVICE_UNAVAILABLE: "服务暂时不可用",
}


class BusinessException(Exception):
    """业务异常"""

    def __init__(
        self,
        code: ErrorCode,
        message: Optional[str] = None,
        errors: Optional[List[dict]] = None,
        request_id: Optional[str] = None
    ):
        self.code = code
        self.message = message or ERROR_MESSAGES.get(code, "未知错误")
        self.errors = errors
        self.request_id = request_id
        super().__init__(self.message)

    def get_http_status(self) -> int:
        """获取HTTP状态码"""
        return ERROR_HTTP_STATUS.get(self.code, 500)


class ValidationError(BusinessException):
    """验证错误"""

    def __init__(self, message: str = "参数验证失败", errors: Optional[List[dict]] = None):
        super().__init__(
            code=ErrorCode.PARAM_VALIDATION_FAILED,
            message=message,
            errors=errors
        )


class AuthenticationError(BusinessException):
    """认证错误"""

    def __init__(self, message: str = "认证失败"):
        super().__init__(
            code=ErrorCode.AUTH_ERROR,
            message=message
        )


class TokenExpiredError(BusinessException):
    """Token过期错误"""

    def __init__(self):
        super().__init__(
            code=ErrorCode.TOKEN_EXPIRED,
            message=ERROR_MESSAGES[ErrorCode.TOKEN_EXPIRED]
        )


class UserNotFoundError(BusinessException):
    """用户不存在错误"""

    def __init__(self):
        super().__init__(
            code=ErrorCode.USER_NOT_FOUND,
            message=ERROR_MESSAGES[ErrorCode.USER_NOT_FOUND]
        )


class PasswordIncorrectError(BusinessException):
    """密码错误"""

    def __init__(self):
        super().__init__(
            code=ErrorCode.PASSWORD_INCORRECT,
            message=ERROR_MESSAGES[ErrorCode.PASSWORD_INCORRECT]
        )


class AccountDisabledError(BusinessException):
    """账号已禁用错误"""

    def __init__(self):
        super().__init__(
            code=ErrorCode.ACCOUNT_DISABLED,
            message=ERROR_MESSAGES[ErrorCode.ACCOUNT_DISABLED]
        )


class AccountLockedError(BusinessException):
    """账号被锁定错误"""

    def __init__(self):
        super().__init__(
            code=ErrorCode.ACCOUNT_LOCKED,
            message=ERROR_MESSAGES[ErrorCode.ACCOUNT_LOCKED]
        )

# ==================== 数据库异常 ====================

class DatabaseError(BusinessException):
    """数据库相关错误的基类"""

    def __init__(self, message: str = "数据库操作失败"):
        super().__init__(
            code=ErrorCode.DB_ERROR,
            message=message
        )


class RecordNotFoundError(BusinessException):
    """记录未找到"""

    def __init__(self, resource_name: str = "资源"):
        super().__init__(
            code=ErrorCode.RECORD_NOT_FOUND,
            message=f"{resource_name}不存在"
        )


class RecordAlreadyExistsError(BusinessException):
    """记录已存在"""

    def __init__(self, message: str = "记录已存在"):
        super().__init__(
            code=ErrorCode.RECORD_ALREADY_EXISTS,
            message=message
        )


class DuplicateRecordError(BusinessException):
    """重复记录错误"""

    def __init__(self, field_name: str = "字段"):
        super().__init__(
            code=ErrorCode.DB_DUPLICATE_ENTRY,
            message=f"{field_name}已存在"
        )


# ==================== 文件操作异常 ====================

class FileOperationError(BusinessException):
    """文件操作错误"""

    def __init__(self, message: str = "文件操作失败"):
        super().__init__(
            code=ErrorCode.SYSTEM_ERROR,
            message=message
        )


class FileSizeExceededError(BusinessException):
    """文件过大"""

    def __init__(self, max_size: int = 0):
        message = f"文件大小超过限制" if not max_size else f"文件大小不能超过 {max_size}MB"
        super().__init__(
            code=ErrorCode.FILE_SIZE_EXCEEDED,
            message=message
        )


class FileTypeNotAllowedError(BusinessException):
    """文件类型不允许"""

    def __init__(self, allowed_types: Optional[List] = None):
        message = "文件类型不支持"
        if allowed_types:
            message += f"，支持的类型：{', '.join(allowed_types)}"
        super().__init__(
            code=ErrorCode.FILE_TYPE_NOT_ALLOWED,
            message=message
        )


# ==================== 权限异常 ====================

class PermissionDeniedError(BusinessException):
    """权限不足"""

    def __init__(self, message: str = "权限不足"):
        super().__init__(
            code=ErrorCode.PERMISSION_DENIED,
            message=message
        )


class ResourceAccessDeniedError(BusinessException):
    """资源访问被拒绝"""

    def __init__(self, message: str = "无法访问该资源"):
        super().__init__(
            code=ErrorCode.RESOURCE_ACCESS_DENIED,
            message=message
        )


# ==================== 参数异常 ====================

class ParameterError(BusinessException):
    """参数错误"""

    def __init__(self, message: str = "参数错误"):
        super().__init__(
            code=ErrorCode.PARAM_ERROR,
            message=message
        )


class InvalidParameterError(BusinessException):
    """参数无效"""

    def __init__(self, param_name: str = "", message: str = None):
        if not message:
            message = f"参数 {param_name} 无效" if param_name else "参数无效"
        super().__init__(
            code=ErrorCode.PARAM_VALUE_INVALID,
            message=message
        )


class MissingParameterError(BusinessException):
    """缺少必要参数"""

    def __init__(self, param_name: str = ""):
        message = f"缺少必要参数：{param_name}" if param_name else "缺少必要参数"
        super().__init__(
            code=ErrorCode.PARAM_MISSING,
            message=message
        )


# ==================== 业务异常 ====================

class BusinessLogicError(BusinessException):
    """业务逻辑错误"""

    def __init__(self, message: str = "业务操作失败"):
        super().__init__(
            code=ErrorCode.SYSTEM_ERROR,
            message=message
        )


# ==================== 外部服务异常 ====================

class ExternalServiceError(BusinessException):
    """外部服务错误"""

    def __init__(self, message: str = "外部服务调用失败"):
        super().__init__(
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message=message
        )
