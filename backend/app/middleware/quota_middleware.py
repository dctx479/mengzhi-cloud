"""
配额中间件 - Quota Middleware

提供配额检查和扣减的装饰器和中间件函数

版本: 1.0
更新日期: 2026-01-22
"""

from functools import wraps
from typing import Optional, Callable, Any
from sqlalchemy.orm import Session
from loguru import logger

from app.services.quota_service import QuotaService
from app.models.quota import QuotaResourceType, QuotaPeriodType
from app.models.user import User
from app.core.errors import BusinessException, ErrorCode


class QuotaMiddleware:
    """配额中间件"""

    def __init__(self, db: Session):
        self.db = db
        self.quota_service = QuotaService(db)

    def check_and_deduct(
        self,
        resource_type: QuotaResourceType,
        amount: int,
        user_id: Optional[int] = None,
        enterprise_id: Optional[int] = None,
        period_type: QuotaPeriodType = QuotaPeriodType.DAILY,
        operation: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_type_name: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        检查并扣减配额

        参数:
            resource_type: 资源类型
            amount: 使用量
            user_id: 用户ID
            enterprise_id: 企业ID
            period_type: 周期类型
            operation: 操作类型
            resource_id: 关联资源ID
            resource_type_name: 关联资源类型
            metadata: 元数据

        返回:
            是否成功

        异常:
            BusinessException: 配额不足
        """
        # 检查配额
        is_sufficient, quota, message = self.quota_service.check_quota(
            resource_type=resource_type,
            required_amount=amount,
            enterprise_id=enterprise_id,
            user_id=user_id,
            period_type=period_type
        )

        if not is_sufficient:
            logger.warning(f"配额检查失败: {message}")
            raise BusinessException(
                code=ErrorCode.QUOTA_EXCEEDED,
                message=f"配额不足: {message}"
            )

        # 扣减配额
        success, deduct_message = self.quota_service.deduct_quota(
            resource_type=resource_type,
            amount=amount,
            enterprise_id=enterprise_id,
            user_id=user_id,
            period_type=period_type,
            operation=operation,
            resource_id=resource_id,
            resource_type_name=resource_type_name,
            metadata=metadata
        )

        if not success:
            logger.error(f"配额扣减失败: {deduct_message}")
            raise BusinessException(
                code=ErrorCode.QUOTA_DEDUCT_FAILED,
                message=f"配额扣减失败: {deduct_message}"
            )

        return True


def require_quota(
    resource_type: QuotaResourceType,
    amount: int = 1,
    period_type: QuotaPeriodType = QuotaPeriodType.DAILY,
    operation: Optional[str] = None
):
    """
    配额检查装饰器

    用法:
        @require_quota(QuotaResourceType.MESSAGE, amount=1, operation="chat")
        async def send_message(self, user_id: int, content: str):
            ...

    参数:
        resource_type: 资源类型
        amount: 使用量
        period_type: 周期类型
        operation: 操作类型
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # 从参数中提取 db 和 user_id
            db = kwargs.get('db') or (args[0].db if hasattr(args[0], 'db') else None)
            user_id = kwargs.get('user_id')
            enterprise_id = kwargs.get('enterprise_id')

            if not db:
                raise ValueError("缺少数据库会话参数")

            # 如果有 user_id 字符串，转换为数据库 ID
            if user_id and isinstance(user_id, str):
                user = db.query(User).filter(User.user_uuid == user_id).first()
                if user:
                    user_id = user.id
                    enterprise_id = user.enterprise_id

            # 创建配额中间件
            middleware = QuotaMiddleware(db)

            # 检查并扣减配额
            middleware.check_and_deduct(
                resource_type=resource_type,
                amount=amount,
                user_id=user_id,
                enterprise_id=enterprise_id,
                period_type=period_type,
                operation=operation
            )

            # 执行原函数
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # 从参数中提取 db 和 user_id
            db = kwargs.get('db') or (args[0].db if hasattr(args[0], 'db') else None)
            user_id = kwargs.get('user_id')
            enterprise_id = kwargs.get('enterprise_id')

            if not db:
                raise ValueError("缺少数据库会话参数")

            # 如果有 user_id 字符串，转换为数据库 ID
            if user_id and isinstance(user_id, str):
                user = db.query(User).filter(User.user_uuid == user_id).first()
                if user:
                    user_id = user.id
                    enterprise_id = user.enterprise_id

            # 创建配额中间件
            middleware = QuotaMiddleware(db)

            # 检查并扣减配额
            middleware.check_and_deduct(
                resource_type=resource_type,
                amount=amount,
                user_id=user_id,
                enterprise_id=enterprise_id,
                period_type=period_type,
                operation=operation
            )

            # 执行原函数
            return func(*args, **kwargs)

        # 根据函数类型返回对应的包装器
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def check_quota_before_ai_call(
    db: Session,
    user_id: Optional[int] = None,
    enterprise_id: Optional[int] = None,
    estimated_tokens: int = 1000,
    operation: str = "ai_call"
) -> bool:
    """
    AI调用前检查配额

    参数:
        db: 数据库会话
        user_id: 用户ID
        enterprise_id: 企业ID
        estimated_tokens: 预估Token数
        operation: 操作类型

    返回:
        是否通过检查

    异常:
        BusinessException: 配额不足
    """
    middleware = QuotaMiddleware(db)

    # 检查消息配额
    middleware.check_and_deduct(
        resource_type=QuotaResourceType.MESSAGE,
        amount=1,
        user_id=user_id,
        enterprise_id=enterprise_id,
        period_type=QuotaPeriodType.DAILY,
        operation=operation
    )

    # 检查Token配额（预估）
    is_sufficient, _, message = middleware.quota_service.check_quota(
        resource_type=QuotaResourceType.TOKEN,
        required_amount=estimated_tokens,
        user_id=user_id,
        enterprise_id=enterprise_id,
        period_type=QuotaPeriodType.DAILY
    )

    if not is_sufficient:
        logger.warning(f"Token配额不足: {message}")
        raise BusinessException(
            code=ErrorCode.QUOTA_EXCEEDED,
            message=f"Token配额不足: {message}"
        )

    return True


def deduct_token_quota_after_ai_call(
    db: Session,
    user_id: Optional[int] = None,
    enterprise_id: Optional[int] = None,
    actual_tokens: int = 0,
    operation: str = "ai_call",
    resource_id: Optional[str] = None,
    metadata: Optional[dict] = None
) -> bool:
    """
    AI调用后扣减Token配额

    参数:
        db: 数据库会话
        user_id: 用户ID
        enterprise_id: 企业ID
        actual_tokens: 实际使用的Token数
        operation: 操作类型
        resource_id: 关联资源ID
        metadata: 元数据

    返回:
        是否成功
    """
    if actual_tokens <= 0:
        return True

    middleware = QuotaMiddleware(db)

    # 扣减Token配额
    success, message = middleware.quota_service.deduct_quota(
        resource_type=QuotaResourceType.TOKEN,
        amount=actual_tokens,
        user_id=user_id,
        enterprise_id=enterprise_id,
        period_type=QuotaPeriodType.DAILY,
        operation=operation,
        resource_id=resource_id,
        resource_type_name="ai_response",
        metadata=metadata
    )

    if not success:
        logger.error(f"Token配额扣减失败: {message}")
        # 不抛出异常，因为AI调用已经完成
        return False

    return True
