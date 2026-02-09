"""
支付服务单元测试

P2-18: 添加支付服务的单元测试

测试覆盖:
- 支付创建
- 支付回调处理
- 配额发放
- 异常情况处理
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.payment_service import PaymentService
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.core.errors import BusinessException, ErrorCode, RecordNotFoundError


class TestPaymentService:
    """支付服务测试类"""

    @pytest.fixture
    def db_session(self):
        """模拟数据库会话"""
        session = Mock(spec=Session)
        return session

    @pytest.fixture
    def payment_service(self, db_session):
        """创建支付服务实例"""
        return PaymentService(db_session)

    @pytest.fixture
    def mock_user(self):
        """模拟用户"""
        user = Mock(spec=User)
        user.id = 1
        user.chat_quota = 100
        user.generation_quota = 50
        user.token_quota = 10000
        user.storage_quota_mb = 1024
        return user

    @pytest.fixture
    def mock_order(self):
        """模拟订单"""
        order = Mock(spec=Order)
        order.id = 1
        order.order_no = "ORD20260123123456"
        order.user_id = 1
        order.amount = Decimal("99.00")
        order.status = OrderStatus.PENDING
        order.chat_quota = 1000
        order.generation_quota = 500
        order.token_quota = 100000
        order.storage_quota_mb = 10240
        order.can_pay = Mock(return_value=True)
        order.mark_as_paid = Mock()
        order.mark_as_completed = Mock()
        return order

    @pytest.fixture
    def mock_payment(self):
        """模拟支付"""
        payment = Mock(spec=Payment)
        payment.id = 1
        payment.payment_no = "PAY20260123ABCD1234"
        payment.order_id = 1
        payment.amount = Decimal("99.00")
        payment.payment_method = PaymentMethod.ALIPAY
        payment.status = PaymentStatus.PENDING
        payment.is_success = Mock(return_value=False)
        payment.mark_as_success = Mock()
        payment.mark_as_failed = Mock()
        return payment

    # ==================== 支付创建测试 ====================

    def test_create_payment_success(self, payment_service, db_session, mock_order, mock_payment):
        """测试成功创建支付"""
        # 设置mock
        db_session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = mock_order
        db_session.query.return_value.filter.return_value.first.return_value = None  # 没有现有支付
        db_session.add = Mock()
        db_session.commit = Mock()
        db_session.refresh = Mock(side_effect=lambda x: setattr(x, 'id', 1))

        # 执行
        with patch.object(payment_service, '_generate_payment_no', return_value="PAY20260123ABCD1234"):
            with patch('app.core.config.settings.PAYMENT_DEV_MODE', False):
                result = payment_service.create_payment(
                    order_id=1,
                    payment_method="alipay",
                    user_id=1
                )

        # 验证
        assert result is not None
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()

    def test_create_payment_order_not_found(self, payment_service, db_session):
        """测试订单不存在"""
        # 设置mock
        db_session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None

        # 执行并验证
        with pytest.raises(RecordNotFoundError):
            payment_service.create_payment(
                order_id=999,
                payment_method="alipay",
                user_id=1
            )

    def test_create_payment_permission_denied(self, payment_service, db_session, mock_order):
        """测试无权支付订单"""
        # 设置mock
        mock_order.user_id = 2  # 不同的用户ID
        db_session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = mock_order

        # 执行并验证
        with pytest.raises(BusinessException) as exc_info:
            payment_service.create_payment(
                order_id=1,
                payment_method="alipay",
                user_id=1
            )
        assert exc_info.value.code == ErrorCode.PERMISSION_DENIED

    def test_create_payment_invalid_order_status(self, payment_service, db_session, mock_order):
        """测试订单状态不允许支付"""
        # 设置mock
        mock_order.can_pay.return_value = False
        db_session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = mock_order

        # 执行并验证
        with pytest.raises(BusinessException) as exc_info:
            payment_service.create_payment(
                order_id=1,
                payment_method="alipay",
                user_id=1
            )
        assert exc_info.value.code == ErrorCode.PARAM_ERROR

    def test_create_payment_invalid_method(self, payment_service, db_session, mock_order):
        """测试不支持的支付方式"""
        # 设置mock
        db_session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = mock_order

        # 执行并验证
        with pytest.raises(BusinessException) as exc_info:
            payment_service.create_payment(
                order_id=1,
                payment_method="invalid_method",
                user_id=1
            )
        assert exc_info.value.code == ErrorCode.PARAM_VALUE_INVALID

    def test_create_payment_existing_pending(self, payment_service, db_session, mock_order, mock_payment):
        """测试已有待支付记录"""
        # 设置mock
        db_session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = mock_order

        # 第一次查询返回订单，第二次查询返回现有支付
        query_mock = Mock()
        query_mock.filter.return_value.with_for_update.return_value.first.return_value = mock_order
        query_mock.filter.return_value.first.return_value = mock_payment
        db_session.query.return_value = query_mock

        # 执行
        result = payment_service.create_payment(
            order_id=1,
            payment_method="alipay",
            user_id=1
        )

        # 验证：应该返回现有支付，不创建新的
        assert result == mock_payment

    # ==================== 支付回调测试 ====================

    def test_handle_payment_callback_success(self, payment_service, db_session, mock_payment, mock_order, mock_user):
        """测试成功处理支付回调"""
        # 设置mock
        mock_payment.is_success.return_value = False
        mock_payment.payment_method = PaymentMethod.ALIPAY

        # 配置查询链
        payment_query = Mock()
        payment_query.filter.return_value.first.return_value = mock_payment

        order_query = Mock()
        order_query.filter.return_value.first.return_value = mock_order

        user_query = Mock()
        user_query.filter.return_value.first.return_value = mock_user

        # 根据查询的模型返回不同的mock
        def query_side_effect(model):
            if model == Payment:
                return payment_query
            elif model == Order:
                return order_query
            elif model == User:
                return user_query
            return Mock()

        db_session.query.side_effect = query_side_effect
        db_session.commit = Mock()
        db_session.flush = Mock()

        callback_data = {
            "transaction_id": "ALIPAY123456",
            "total_amount": "99.00"
        }

        # 执行
        with patch('app.core.config.settings.PAYMENT_DEV_MODE', True):
            result = payment_service.handle_payment_callback(
                payment_no="PAY20260123ABCD1234",
                callback_data=callback_data
            )

        # 验证
        assert result is True
        mock_payment.mark_as_success.assert_called_once()
        mock_order.mark_as_paid.assert_called_once()
        mock_order.mark_as_completed.assert_called_once()
        db_session.commit.assert_called()

    def test_handle_payment_callback_payment_not_found(self, payment_service, db_session):
        """测试支付记录不存在"""
        # 设置mock
        db_session.query.return_value.filter.return_value.first.return_value = None

        # 执行
        result = payment_service.handle_payment_callback(
            payment_no="INVALID_PAYMENT_NO",
            callback_data={}
        )

        # 验证
        assert result is False

    def test_handle_payment_callback_already_success(self, payment_service, db_session, mock_payment):
        """测试支付已经成功"""
        # 设置mock
        mock_payment.is_success.return_value = True
        db_session.query.return_value.filter.return_value.first.return_value = mock_payment

        # 执行
        result = payment_service.handle_payment_callback(
            payment_no="PAY20260123ABCD1234",
            callback_data={}
        )

        # 验证：应该直接返回True，不重复处理
        assert result is True
        mock_payment.mark_as_success.assert_not_called()

    def test_handle_payment_callback_amount_mismatch(self, payment_service, db_session, mock_payment):
        """测试支付金额不匹配"""
        # 设置mock
        mock_payment.is_success.return_value = False
        mock_payment.payment_method = PaymentMethod.ALIPAY
        mock_payment.amount = Decimal("99.00")
        db_session.query.return_value.filter.return_value.first.return_value = mock_payment
        db_session.commit = Mock()

        callback_data = {
            "transaction_id": "ALIPAY123456",
            "total_amount": "199.00"  # 金额不匹配
        }

        # 执行 - 需要mock签名验证通过，才能到金额验证
        with patch('app.core.config.settings.PAYMENT_DEV_MODE', False):
            with patch.object(payment_service, '_verify_alipay_callback', return_value=True):
                result = payment_service.handle_payment_callback(
                    payment_no="PAY20260123ABCD1234",
                    callback_data=callback_data
                )

        # 验证：应该失败
        assert result is False
        mock_payment.mark_as_failed.assert_called_once()

    # ==================== 配额发放测试 ====================

    def test_grant_quota_success(self, payment_service, db_session, mock_order, mock_user):
        """测试成功发放配额"""
        # 设置mock
        db_session.query.return_value.filter.return_value.first.return_value = mock_user
        db_session.flush = Mock()

        # 记录初始配额
        initial_chat = mock_user.chat_quota
        initial_generation = mock_user.generation_quota
        initial_token = mock_user.token_quota
        initial_storage = mock_user.storage_quota_mb

        # 执行
        payment_service._grant_quota(mock_order)

        # 验证：配额应该增加
        assert mock_user.chat_quota == initial_chat + mock_order.chat_quota
        assert mock_user.generation_quota == initial_generation + mock_order.generation_quota
        assert mock_user.token_quota == initial_token + mock_order.token_quota
        assert mock_user.storage_quota_mb == initial_storage + mock_order.storage_quota_mb
        db_session.flush.assert_called_once()

    def test_grant_quota_user_not_found(self, payment_service, db_session, mock_order):
        """测试用户不存在"""
        # 设置mock
        db_session.query.return_value.filter.return_value.first.return_value = None

        # 执行并验证
        with pytest.raises(BusinessException) as exc_info:
            payment_service._grant_quota(mock_order)
        assert exc_info.value.code == ErrorCode.RECORD_NOT_FOUND

    # ==================== 金额验证测试 ====================

    def test_verify_payment_amount_alipay_success(self, payment_service, mock_payment):
        """测试支付宝金额验证成功"""
        mock_payment.payment_method = PaymentMethod.ALIPAY
        mock_payment.amount = Decimal("99.00")

        callback_data = {
            "total_amount": "99.00"
        }

        result = payment_service._verify_payment_amount(mock_payment, callback_data)
        assert result is True

    def test_verify_payment_amount_wechat_success(self, payment_service, mock_payment):
        """测试微信金额验证成功"""
        mock_payment.payment_method = PaymentMethod.WECHAT
        mock_payment.amount = Decimal("99.00")

        callback_data = {
            "total_fee": 9900  # 微信使用分为单位
        }

        result = payment_service._verify_payment_amount(mock_payment, callback_data)
        assert result is True

    def test_verify_payment_amount_mismatch(self, payment_service, mock_payment):
        """测试金额不匹配"""
        mock_payment.payment_method = PaymentMethod.ALIPAY
        mock_payment.amount = Decimal("99.00")

        callback_data = {
            "total_amount": "199.00"  # 金额不匹配
        }

        result = payment_service._verify_payment_amount(mock_payment, callback_data)
        assert result is False

    def test_verify_payment_amount_tolerance(self, payment_service, mock_payment):
        """测试金额容差（0.01元以内）"""
        mock_payment.payment_method = PaymentMethod.ALIPAY
        mock_payment.amount = Decimal("99.00")

        callback_data = {
            "total_amount": "99.01"  # 差0.01元，应该通过
        }

        result = payment_service._verify_payment_amount(mock_payment, callback_data)
        assert result is True

    def test_verify_payment_amount_missing_data(self, payment_service, mock_payment):
        """测试缺少金额数据"""
        mock_payment.payment_method = PaymentMethod.ALIPAY
        mock_payment.amount = Decimal("99.00")

        callback_data = {}  # 没有金额字段

        with patch('app.core.config.settings.PAYMENT_DEV_MODE', True):
            result = payment_service._verify_payment_amount(mock_payment, callback_data)
            # 开发模式应该跳过验证
            assert result is True

        with patch('app.core.config.settings.PAYMENT_DEV_MODE', False):
            result = payment_service._verify_payment_amount(mock_payment, callback_data)
            # 生产模式应该失败
            assert result is False

    # ==================== 支付单号生成测试 ====================

    def test_generate_payment_no_format(self, payment_service, db_session):
        """测试支付单号格式"""
        # 设置mock：没有冲突
        db_session.query.return_value.filter.return_value.first.return_value = None

        payment_no = payment_service._generate_payment_no()

        # 验证格式：PAY + YYYYMMDD + 8位十六进制
        assert payment_no.startswith("PAY")
        assert len(payment_no) == 19  # PAY(3) + YYYYMMDD(8) + HEX(8)

        # 验证日期部分
        date_part = payment_no[3:11]
        datetime.strptime(date_part, "%Y%m%d")  # 应该能解析

    def test_generate_payment_no_uniqueness(self, payment_service, db_session):
        """测试支付单号唯一性检查"""
        # 设置mock：第一次冲突，第二次成功
        mock_existing = Mock()
        db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_existing,  # 第一次查询返回冲突
            None  # 第二次查询返回None（无冲突）
        ]

        payment_no = payment_service._generate_payment_no()

        # 验证：应该查询了两次
        assert db_session.query.return_value.filter.return_value.first.call_count == 2
        assert payment_no is not None

    # ==================== 开发模式支付测试 ====================

    def test_process_dev_payment_success(self, payment_service, db_session, mock_payment, mock_order, mock_user):
        """测试开发模式支付成功"""
        # 设置mock
        db_session.query.return_value.filter.return_value.first.return_value = mock_user
        db_session.commit = Mock()
        db_session.flush = Mock()
        db_session.begin_nested = Mock(return_value=Mock(commit=Mock(), rollback=Mock()))

        # 执行
        payment_service._process_dev_payment(mock_payment, mock_order)

        # 验证
        mock_payment.mark_as_success.assert_called_once()
        mock_order.mark_as_paid.assert_called_once()
        mock_order.mark_as_completed.assert_called_once()
        db_session.commit.assert_called()

    def test_process_dev_payment_quota_failure(self, payment_service, db_session, mock_payment, mock_order):
        """测试开发模式配额发放失败"""
        # 设置mock：用户不存在，导致配额发放失败
        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.commit = Mock()

        savepoint_mock = Mock()
        savepoint_mock.commit = Mock()
        savepoint_mock.rollback = Mock()
        db_session.begin_nested = Mock(return_value=savepoint_mock)

        # 执行并验证
        with pytest.raises(BusinessException) as exc_info:
            payment_service._process_dev_payment(mock_payment, mock_order)

        # 验证：应该回滚到保存点
        savepoint_mock.rollback.assert_called_once()
        mock_payment.mark_as_failed.assert_called_once()

    # ==================== 查询支付状态测试 ====================

    def test_get_payment_status_success(self, payment_service, db_session, mock_order, mock_payment):
        """测试查询支付状态成功"""
        # 设置mock
        mock_payment.is_success.return_value = True

        order_query = Mock()
        order_query.filter.return_value.first.return_value = mock_order

        payment_query = Mock()
        payment_query.filter.return_value.order_by.return_value.first.return_value = mock_payment

        def query_side_effect(model):
            if model == Order:
                return order_query
            elif model == Payment:
                return payment_query
            return Mock()

        db_session.query.side_effect = query_side_effect

        # 执行
        result = payment_service.get_payment_status(order_id=1, user_id=1)

        # 验证
        assert result["order_id"] == 1
        assert result["paid"] is True
        assert result["payment_no"] == mock_payment.payment_no

    def test_get_payment_status_order_not_found(self, payment_service, db_session):
        """测试订单不存在"""
        # 设置mock
        db_session.query.return_value.filter.return_value.first.return_value = None

        # 执行并验证
        with pytest.raises(RecordNotFoundError):
            payment_service.get_payment_status(order_id=999, user_id=1)

    def test_get_payment_status_permission_denied(self, payment_service, db_session, mock_order):
        """测试无权查询"""
        # 设置mock
        mock_order.user_id = 2  # 不同的用户ID
        db_session.query.return_value.filter.return_value.first.return_value = mock_order

        # 执行并验证
        with pytest.raises(BusinessException) as exc_info:
            payment_service.get_payment_status(order_id=1, user_id=1)
        assert exc_info.value.code == ErrorCode.PERMISSION_DENIED

    def test_get_payment_status_no_payment(self, payment_service, db_session, mock_order):
        """测试没有支付记录"""
        # 设置mock
        order_query = Mock()
        order_query.filter.return_value.first.return_value = mock_order

        payment_query = Mock()
        payment_query.filter.return_value.order_by.return_value.first.return_value = None

        def query_side_effect(model):
            if model == Order:
                return order_query
            elif model == Payment:
                return payment_query
            return Mock()

        db_session.query.side_effect = query_side_effect

        # 执行
        result = payment_service.get_payment_status(order_id=1, user_id=1)

        # 验证
        assert result["order_id"] == 1
        assert result["payment_status"] is None
        assert result["paid"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
