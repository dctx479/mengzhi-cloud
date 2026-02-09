"""
订单服务单元测试

测试内容:
- 订单创建
- 订单查询
- 订单列表获取
- 订单号生成
- 异常情况处理

运行: pytest tests/test_order_service.py -v
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.order_service import OrderService
from app.models.order import Order, OrderStatus
from app.models.quota_package import QuotaPackage, PackageType
from app.models.user import User
from app.schemas.orders import OrderCreateRequest
from app.core.errors import BusinessException, ErrorCode, RecordNotFoundError


# ==================== 订单创建测试 ====================

class TestOrderCreation:
    """订单创建功能测试"""

    @pytest.fixture
    def db_session(self):
        """模拟数据库会话"""
        session = Mock(spec=Session)
        return session

    @pytest.fixture
    def order_service(self, db_session):
        """创建订单服务实例"""
        return OrderService(db_session)

    @pytest.fixture
    def mock_package(self):
        """模拟套餐"""
        package = Mock(spec=QuotaPackage)
        package.id = 1
        package.name = "基础套餐"
        package.package_type = PackageType.BASIC
        package.price = Decimal("99.00")
        package.original_price = Decimal("199.00")
        package.chat_quota = 1000
        package.generation_quota = 500
        package.token_quota = 100000
        package.storage_quota_mb = 10240
        package.validity_days = 30
        package.is_active = True
        return package

    @pytest.mark.unit
    def test_create_order_success(self, order_service, db_session, mock_package):
        """测试成功创建订单"""
        # 设置mock
        db_session.query.return_value.filter.return_value.first.return_value = mock_package
        db_session.add = Mock()
        db_session.commit = Mock()
        db_session.refresh = Mock(side_effect=lambda x: setattr(x, 'id', 1))

        request = OrderCreateRequest(package_id=1)

        with patch.object(order_service, '_generate_order_no', return_value="ORD20260123123456"):
            order = order_service.create_order(request, user_id=1)

        # 验证订单创建
        assert order is not None
        assert order.order_no == "ORD20260123123456"
        assert order.user_id == 1
        assert order.package_id == 1
        assert order.amount == Decimal("99.00")
        assert order.status == OrderStatus.PENDING

        # 验证数据库操作
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()

    @pytest.mark.unit
    def test_create_order_package_not_found(self, order_service, db_session):
        """测试套餐不存在"""
        # 设置mock返回None
        db_session.query.return_value.filter.return_value.first.return_value = None

        request = OrderCreateRequest(package_id=999)

        with pytest.raises(BusinessException) as exc_info:
            order_service.create_order(request, user_id=1)

        assert exc_info.value.code == ErrorCode.RECORD_NOT_FOUND
        assert "套餐不存在" in str(exc_info.value.message)

    @pytest.mark.unit
    def test_create_order_package_inactive(self, order_service, db_session):
        """测试套餐已下架"""
        # 设置mock返回None（因为is_active=False会被过滤掉）
        db_session.query.return_value.filter.return_value.first.return_value = None

        request = OrderCreateRequest(package_id=1)

        with pytest.raises(BusinessException) as exc_info:
            order_service.create_order(request, user_id=1)

        assert exc_info.value.code == ErrorCode.RECORD_NOT_FOUND

    @pytest.mark.unit
    def test_create_order_db_error(self, order_service, db_session, mock_package):
        """测试数据库错误"""
        # 设置mock
        db_session.query.return_value.filter.return_value.first.return_value = mock_package
        db_session.add = Mock()
        db_session.commit = Mock(side_effect=Exception("Database error"))
        db_session.rollback = Mock()

        request = OrderCreateRequest(package_id=1)

        with patch.object(order_service, '_generate_order_no', return_value="ORD20260123123456"):
            with pytest.raises(BusinessException) as exc_info:
                order_service.create_order(request, user_id=1)

        assert exc_info.value.code == ErrorCode.DB_INSERT_FAILED
        db_session.rollback.assert_called_once()

    @pytest.mark.unit
    def test_create_order_with_discount(self, order_service, db_session, mock_package):
        """测试创建带折扣的订单"""
        # 设置mock
        db_session.query.return_value.filter.return_value.first.return_value = mock_package
        db_session.add = Mock()
        db_session.commit = Mock()
        db_session.refresh = Mock(side_effect=lambda x: setattr(x, 'id', 1))

        request = OrderCreateRequest(package_id=1)

        with patch.object(order_service, '_generate_order_no', return_value="ORD20260123123456"):
            order = order_service.create_order(request, user_id=1)

        # 验证折扣计算
        assert order.original_amount == Decimal("199.00")
        assert order.amount == Decimal("99.00")
        assert order.discount_amount == Decimal("100.00")

    @pytest.mark.unit
    def test_create_order_no_discount(self, order_service, db_session, mock_package):
        """测试创建无折扣的订单"""
        # 修改mock套餐，无原价
        mock_package.original_price = None

        # 设置mock
        db_session.query.return_value.filter.return_value.first.return_value = mock_package
        db_session.add = Mock()
        db_session.commit = Mock()
        db_session.refresh = Mock(side_effect=lambda x: setattr(x, 'id', 1))

        request = OrderCreateRequest(package_id=1)

        with patch.object(order_service, '_generate_order_no', return_value="ORD20260123123456"):
            order = order_service.create_order(request, user_id=1)

        # 验证无折扣
        assert order.discount_amount == 0

    @pytest.mark.unit
    def test_create_order_expiration_time(self, order_service, db_session, mock_package):
        """测试订单过期时间设置"""
        # 设置mock
        db_session.query.return_value.filter.return_value.first.return_value = mock_package
        db_session.add = Mock()
        db_session.commit = Mock()
        db_session.refresh = Mock(side_effect=lambda x: setattr(x, 'id', 1))

        request = OrderCreateRequest(package_id=1)

        before = datetime.utcnow()
        with patch.object(order_service, '_generate_order_no', return_value="ORD20260123123456"):
            order = order_service.create_order(request, user_id=1)
        after = datetime.utcnow()

        # 验证过期时间约为30分钟后
        expected_min = before + timedelta(minutes=29)
        expected_max = after + timedelta(minutes=31)
        assert expected_min <= order.expired_at <= expected_max


# ==================== 订单查询测试 ====================

class TestOrderQuery:
    """订单查询功能测试"""

    @pytest.fixture
    def db_session(self):
        """模拟数据库会话"""
        session = Mock(spec=Session)
        return session

    @pytest.fixture
    def order_service(self, db_session):
        """创建订单服务实例"""
        return OrderService(db_session)

    @pytest.fixture
    def mock_order(self):
        """模拟订单"""
        order = Mock(spec=Order)
        order.id = 1
        order.order_no = "ORD20260123123456"
        order.user_id = 1
        order.status = OrderStatus.PENDING
        return order

    @pytest.mark.unit
    def test_get_order_by_id_success(self, order_service, db_session, mock_order):
        """测试根据ID获取订单成功"""
        db_session.query.return_value.filter.return_value.first.return_value = mock_order

        order = order_service.get_order_by_id(1)

        assert order is not None
        assert order.id == 1
        assert order.order_no == "ORD20260123123456"

    @pytest.mark.unit
    def test_get_order_by_id_not_found(self, order_service, db_session):
        """测试订单不存在"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(RecordNotFoundError):
            order_service.get_order_by_id(999)

    @pytest.mark.unit
    def test_get_order_by_no_success(self, order_service, db_session, mock_order):
        """测试根据订单号获取订单成功"""
        db_session.query.return_value.filter.return_value.first.return_value = mock_order

        order = order_service.get_order_by_no("ORD20260123123456")

        assert order is not None
        assert order.order_no == "ORD20260123123456"

    @pytest.mark.unit
    def test_get_order_by_no_not_found(self, order_service, db_session):
        """测试订单号不存在"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(RecordNotFoundError):
            order_service.get_order_by_no("INVALID_ORDER_NO")


# ==================== 订单列表测试 ====================

class TestOrderList:
    """订单列表功能测试"""

    @pytest.fixture
    def db_session(self):
        """模拟数据库会话"""
        session = Mock(spec=Session)
        return session

    @pytest.fixture
    def order_service(self, db_session):
        """创建订单服务实例"""
        return OrderService(db_session)

    @pytest.fixture
    def mock_orders(self):
        """模拟订单列表"""
        orders = []
        for i in range(5):
            order = Mock(spec=Order)
            order.id = i + 1
            order.order_no = f"ORD2026012312345{i}"
            order.user_id = 1
            order.status = OrderStatus.PENDING
            orders.append(order)
        return orders

    @pytest.mark.unit
    def test_get_user_orders_success(self, order_service, db_session, mock_orders):
        """测试获取用户订单列表成功"""
        # 设置mock
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_orders

        db_session.query.return_value = mock_query

        orders, total = order_service.get_user_orders(user_id=1, page=1, size=10)

        assert len(orders) == 5
        assert total == 5
        assert orders[0].order_no == "ORD20260123123450"

    @pytest.mark.unit
    def test_get_user_orders_with_status_filter(self, order_service, db_session, mock_orders):
        """测试按状态筛选订单"""
        # 设置mock
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_orders[:3]

        db_session.query.return_value = mock_query

        orders, total = order_service.get_user_orders(
            user_id=1,
            status=OrderStatus.PENDING.value,
            page=1,
            size=10
        )

        assert len(orders) == 3
        assert total == 3

    @pytest.mark.unit
    def test_get_user_orders_pagination(self, order_service, db_session, mock_orders):
        """测试分页功能"""
        # 设置mock
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 15
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_orders

        db_session.query.return_value = mock_query

        # 第2页，每页5条
        orders, total = order_service.get_user_orders(user_id=1, page=2, size=5)

        assert total == 15
        # 验证offset被正确调用
        mock_query.offset.assert_called_with(5)  # (2-1) * 5
        mock_query.limit.assert_called_with(5)

    @pytest.mark.unit
    def test_get_user_orders_empty_result(self, order_service, db_session):
        """测试空结果"""
        # 设置mock
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        db_session.query.return_value = mock_query

        orders, total = order_service.get_user_orders(user_id=999, page=1, size=10)

        assert len(orders) == 0
        assert total == 0

    @pytest.mark.unit
    def test_get_user_orders_db_error(self, order_service, db_session):
        """测试数据库错误"""
        # 设置mock抛出异常
        db_session.query.side_effect = Exception("Database error")

        with pytest.raises(BusinessException) as exc_info:
            order_service.get_user_orders(user_id=1, page=1, size=10)

        assert exc_info.value.code == ErrorCode.DB_QUERY_FAILED


# ==================== 订单号生成测试 ====================

class TestOrderNoGeneration:
    """订单号生成功能测试"""

    @pytest.fixture
    def db_session(self):
        """模拟数据库会话"""
        session = Mock(spec=Session)
        return session

    @pytest.fixture
    def order_service(self, db_session):
        """创建订单服务实例"""
        return OrderService(db_session)

    @pytest.mark.unit
    def test_generate_order_no_format(self, order_service):
        """测试订单号格式"""
        order_no = order_service._generate_order_no()

        # 验证格式: ORD + YYYYMMDD + 6位数字
        assert order_no.startswith("ORD")
        assert len(order_no) == 17  # ORD(3) + YYYYMMDD(8) + 6位数字
        assert order_no[3:11].isdigit()  # 日期部分是数字
        assert order_no[11:].isdigit()  # 随机数部分是数字

    @pytest.mark.unit
    def test_generate_order_no_date_part(self, order_service):
        """测试订单号日期部分"""
        order_no = order_service._generate_order_no()
        date_part = order_no[3:11]

        # 验证日期格式
        today = datetime.utcnow().strftime("%Y%m%d")
        assert date_part == today

    @pytest.mark.unit
    def test_generate_order_no_random_part(self, order_service):
        """测试订单号随机部分"""
        order_no = order_service._generate_order_no()
        random_part = order_no[11:]

        # 验证随机数范围
        random_num = int(random_part)
        assert 100000 <= random_num <= 999999

    @pytest.mark.unit
    def test_generate_order_no_uniqueness(self, order_service):
        """测试订单号唯一性（概率测试）"""
        order_nos = set()
        for _ in range(100):
            order_no = order_service._generate_order_no()
            order_nos.add(order_no)

        # 100次生成应该有很高概率产生不同的订单号
        # 由于随机数范围是100000-999999，碰撞概率很低
        assert len(order_nos) >= 95  # 允许少量碰撞

    @pytest.mark.unit
    def test_generate_order_no_consistency(self, order_service):
        """测试订单号生成一致性"""
        order_no1 = order_service._generate_order_no()
        order_no2 = order_service._generate_order_no()

        # 两个订单号应该有相同的前缀和日期
        assert order_no1[:11] == order_no2[:11]  # ORD + 日期相同


# ==================== 边界条件测试 ====================

class TestOrderServiceEdgeCases:
    """订单服务边界条件测试"""

    @pytest.fixture
    def db_session(self):
        """模拟数据库会话"""
        session = Mock(spec=Session)
        return session

    @pytest.fixture
    def order_service(self, db_session):
        """创建订单服务实例"""
        return OrderService(db_session)

    @pytest.mark.unit
    def test_get_user_orders_page_zero(self, order_service, db_session):
        """测试页码为0"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        db_session.query.return_value = mock_query

        orders, total = order_service.get_user_orders(user_id=1, page=0, size=10)

        # 页码为0时，offset应该是负数，但不应该崩溃
        assert isinstance(orders, list)
        assert isinstance(total, int)

    @pytest.mark.unit
    def test_get_user_orders_large_page_size(self, order_service, db_session):
        """测试大页面大小"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        db_session.query.return_value = mock_query

        orders, total = order_service.get_user_orders(user_id=1, page=1, size=1000)

        # 应该正常处理大页面大小
        mock_query.limit.assert_called_with(1000)

    @pytest.mark.unit
    def test_create_order_with_zero_price(self, order_service, db_session):
        """测试创建零价格订单"""
        mock_package = Mock(spec=QuotaPackage)
        mock_package.id = 1
        mock_package.name = "免费套餐"
        mock_package.package_type = PackageType.BASIC
        mock_package.price = Decimal("0.00")
        mock_package.original_price = Decimal("0.00")
        mock_package.chat_quota = 100
        mock_package.generation_quota = 50
        mock_package.token_quota = 10000
        mock_package.storage_quota_mb = 1024
        mock_package.validity_days = 7
        mock_package.is_active = True

        db_session.query.return_value.filter.return_value.first.return_value = mock_package
        db_session.add = Mock()
        db_session.commit = Mock()
        db_session.refresh = Mock(side_effect=lambda x: setattr(x, 'id', 1))

        request = OrderCreateRequest(package_id=1)

        with patch.object(order_service, '_generate_order_no', return_value="ORD20260123123456"):
            order = order_service.create_order(request, user_id=1)

        # 验证零价格订单
        assert order.amount == Decimal("0.00")
        assert order.discount_amount == Decimal("0.00")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
