"""
订单服务层

版本: 1.1
创建日期: 2026-01-23
更新日期: 2026-02-10

P1修复: 应用统一异常处理装饰器
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta
from loguru import logger
import secrets

from app.models.order import Order, OrderStatus
from app.models.quota_package import QuotaPackage
from app.models.user import User
from app.schemas.orders import OrderCreateRequest
from app.core.errors import BusinessException, ErrorCode, RecordNotFoundError
from app.core.exception_handlers import handle_service_exceptions


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

    @handle_service_exceptions("创建订单")
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
            logger.info(f"套餐不存在或已下架: {request.package_id}")
            raise BusinessException(
                code=ErrorCode.RECORD_NOT_FOUND,
                message="套餐不存在或已下架"
            )

        # 检查是否存在未支付的同类订单（with_for_update防止并发重复创建）
        existing_pending = self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.package_id == request.package_id,
            Order.status == OrderStatus.PENDING,
            Order.expired_at > datetime.utcnow()
        ).with_for_update().first()
        if existing_pending:
            raise BusinessException(
                code=ErrorCode.RECORD_ALREADY_EXISTS,
                message=f"您已有一个未支付的同套餐订单({existing_pending.order_no})，请先完成支付或取消"
            )

        # 生成订单号
        order_no = self._generate_order_no()

        # 计算过期时间(30分钟后)
        expired_at = datetime.utcnow() + timedelta(minutes=30)

        # 计算折扣金额（原价存在时才计算折扣）
        discount_amount = None
        if package.original_price is not None and package.original_price > package.price:
            discount_amount = package.original_price - package.price

        # 创建订单
        order = Order(
            order_no=order_no,
            user_id=user_id,
            package_id=package.id,
            package_name=package.name,
            package_type=package.package_type.value,
            amount=package.price,
            original_amount=package.original_price,
            discount_amount=discount_amount,
            chat_quota=package.chat_quota,
            generation_quota=package.generation_quota,
            token_quota=package.token_quota,
            storage_quota_mb=package.storage_quota_mb,
            validity_days=package.validity_days,
            status=OrderStatus.PENDING,
            expired_at=expired_at
        )

        try:
            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)
        except Exception:
            self.db.rollback()
            raise

        logger.info(f"订单创建成功: {order.order_no} (user_id={user_id}, package_id={package.id})")
        return order

    @handle_service_exceptions("获取订单")
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
            logger.info(f"订单不存在: {order_id}")
            raise RecordNotFoundError("订单")
        return order

    @handle_service_exceptions("获取订单")
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
            logger.info(f"订单不存在: {order_no}")
            raise RecordNotFoundError("订单")
        return order

    @handle_service_exceptions("获取订单列表")
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
        # P2-15: 使用joinedload预加载关联的用户和套餐信息
        query = self.db.query(Order).filter(Order.user_id == user_id)

        if status:
            # 将字符串状态转换为枚举值进行查询
            try:
                status_enum = OrderStatus(status)
                query = query.filter(Order.status == status_enum)
            except ValueError:
                logger.warning(f"无效的订单状态: {status}")
                # 无效的状态值，返回空结果
                return [], 0

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

    def _generate_order_no(self) -> str:
        """生成订单号

        格式: ORD + YYYYMMDD + 6位安全随机十六进制
        使用 secrets 模块生成密码学安全的随机数，并检查唯一性

        Returns:
            订单号
        """
        date_str = datetime.utcnow().strftime("%Y%m%d")
        max_retries = 10
        for attempt in range(max_retries):
            # 使用 secrets 生成安全随机数（3字节 = 6个十六进制字符）
            random_str = secrets.token_hex(3).upper()
            order_no = f"ORD{date_str}{random_str}"
            # 检查唯一性
            existing = self.db.query(Order).filter(Order.order_no == order_no).first()
            if not existing:
                return order_no
            logger.warning(f"订单号冲突，重试 {attempt + 1}/{max_retries}: {order_no}")
        # 重试耗尽，使用UUID后备方案
        import uuid
        fallback_id = uuid.uuid4().hex[:6].upper()
        order_no = f"ORD{date_str}{fallback_id}"
        logger.warning(f"使用UUID后备方案生成订单号: {order_no}")
        return order_no
