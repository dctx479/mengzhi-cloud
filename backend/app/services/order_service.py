"""
订单服务层

版本: 1.0
创建日期: 2026-01-23
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta
from loguru import logger

from app.models.order import Order, OrderStatus
from app.models.quota_package import QuotaPackage
from app.models.user import User
from app.schemas.orders import OrderCreateRequest
from app.core.errors import BusinessException, ErrorCode, RecordNotFoundError


class OrderService:
    """订单服务类

    提供订单相关的业务逻辑操作
    """

    def __init__(self, db: Session) -> None:
        """初始化服务

        Args:
            db: SQLAlchemy数据库会话
        """
        self.db = db

    def create_order(self, request: OrderCreateRequest, user_id: int) -> Order:
        """创建订单

        Args:
            request: 订单创建请求
            user_id: 用户ID

        Returns:
            创建的订单对象

        Raises:
            BusinessException: 套餐不存在或创建失败
        """
        # 获取套餐信息
        package = self.db.query(QuotaPackage).filter(
            QuotaPackage.id == request.package_id,
            QuotaPackage.is_active == True
        ).first()

        if not package:
            logger.warning(f"套餐不存在或已下架: {request.package_id}")
            raise BusinessException(
                code=ErrorCode.RECORD_NOT_FOUND,
                message="套餐不存在或已下架"
            )

        try:
            # 生成订单号
            order_no = self._generate_order_no()

            # 计算过期时间(30分钟后)
            expired_at = datetime.utcnow() + timedelta(minutes=30)

            # 创建订单
            order = Order(
                order_no=order_no,
                user_id=user_id,
                package_id=package.id,
                package_name=package.name,
                package_type=package.package_type.value,
                amount=package.price,
                original_amount=package.original_price,
                discount_amount=(package.original_price - package.price) if package.original_price else 0,
                chat_quota=package.chat_quota,
                generation_quota=package.generation_quota,
                token_quota=package.token_quota,
                storage_quota_mb=package.storage_quota_mb,
                validity_days=package.validity_days,
                status=OrderStatus.PENDING,
                expired_at=expired_at
            )

            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)

            logger.info(f"订单创建成功: {order.order_no} (user_id={user_id}, package_id={package.id})")
            return order

        except Exception as e:
            self.db.rollback()
            logger.error(f"订单创建失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.DB_INSERT_FAILED,
                message="订单创建失败"
            )

    def get_order_by_id(self, order_id: int) -> Order:
        """根据ID获取订单

        Args:
            order_id: 订单ID

        Returns:
            订单对象

        Raises:
            RecordNotFoundError: 订单不存在
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            logger.warning(f"订单不存在: {order_id}")
            raise RecordNotFoundError("订单")
        return order

    def get_order_by_no(self, order_no: str) -> Order:
        """根据订单号获取订单

        Args:
            order_no: 订单号

        Returns:
            订单对象

        Raises:
            RecordNotFoundError: 订单不存在
        """
        order = self.db.query(Order).filter(Order.order_no == order_no).first()
        if not order:
            logger.warning(f"订单不存在: {order_no}")
            raise RecordNotFoundError("订单")
        return order

    def get_user_orders(
        self,
        user_id: int,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> tuple[List[Order], int]:
        """获取用户订单列表

        P2-15: 使用joinedload预加载关联数据，避免N+1查询问题

        Args:
            user_id: 用户ID
            status: 订单状态筛选
            page: 页码
            size: 每页数量

        Returns:
            (订单列表, 总数)
        """
        try:
            from sqlalchemy.orm import joinedload

            # P2-15: 使用joinedload预加载关联的用户和套餐信息
            # 虽然当前响应不需要这些数据，但预加载可以避免将来访问时的N+1问题
            query = self.db.query(Order).filter(Order.user_id == user_id)

            if status:
                query = query.filter(Order.status == status)

            total = query.count()

            # 修复 N+1 查询：预加载 user 和 package 关系
            query = query.options(
                joinedload(Order.user),
                joinedload(Order.package)
            )

            orders = query.order_by(Order.created_at.desc()).offset(
                (page - 1) * size
            ).limit(size).all()

            logger.info(f"获取用户订单列表: user_id={user_id}, total={total}")
            return orders, total

        except Exception as e:
            logger.error(f"获取用户订单列表失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.DB_QUERY_FAILED,
                message="获取订单列表失败"
            )

    def _generate_order_no(self) -> str:
        """生成订单号

        格式: ORD + YYYYMMDD + 6位随机数

        Returns:
            订单号
        """
        import random
        date_str = datetime.utcnow().strftime("%Y%m%d")
        random_str = str(random.randint(100000, 999999))
        return f"ORD{date_str}{random_str}"
