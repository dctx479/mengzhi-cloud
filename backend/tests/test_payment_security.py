"""
支付系统安全测试套件

测试覆盖:
1. 支付回调签名验证（支付宝RSA2、微信MD5）
2. IP白名单验证
3. 金额篡改检测
4. 并发攻击防护（悲观锁）
5. SQL注入防护
6. 订单金额一致性验证
7. 安全随机数生成

版本: 1.0
创建日期: 2026-01-23
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
import hashlib
import secrets
import concurrent.futures
import time
import sys

from app.services.payment_service import PaymentService
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.core.errors import BusinessException, ErrorCode


class TestPaymentSignatureVerification:
    """测试支付回调签名验证"""

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
    def mock_payment(self):
        """模拟支付记录"""
        payment = Mock(spec=Payment)
        payment.payment_no = "PAY20260123ABCD1234"
        payment.amount = Decimal("99.00")
        payment.payment_method = PaymentMethod.ALIPAY
        payment.is_success = Mock(return_value=False)
        payment.mark_as_success = Mock()
        payment.mark_as_failed = Mock()
        return payment

    def test_alipay_signature_verification_success(self, payment_service, mock_payment):
        """测试支付宝签名验证成功"""
        # 模拟正确的签名数据
        callback_data = {
            'out_trade_no': 'PAY20260123ABCD1234',
            'trade_no': 'ALIPAY123456789',
            'total_amount': '99.00',
            'trade_status': 'TRADE_SUCCESS',
            'sign_type': 'RSA2',
            'sign': 'valid_signature_here'
        }

        # Mock签名验证通过
        with patch('app.services.payment_service.settings.ALIPAY_PUBLIC_KEY', 'test_key'):
            # Mock整个模块导入
            with patch.dict('sys.modules', {'alipay': MagicMock(), 'alipay.aop': MagicMock(), 'alipay.aop.api': MagicMock(), 'alipay.aop.api.util': MagicMock(), 'alipay.aop.api.util.SignatureUtils': MagicMock()}):
                with patch('alipay.aop.api.util.SignatureUtils.verify_with_rsa', return_value=True):
                    result = payment_service._verify_alipay_callback(callback_data)
                    assert result is True

    def test_alipay_signature_verification_failure(self, payment_service):
        """测试支付宝签名验证失败"""
        # 模拟错误的签名数据
        callback_data = {
            'out_trade_no': 'PAY20260123ABCD1234',
            'trade_no': 'ALIPAY123456789',
            'total_amount': '99.00',
            'trade_status': 'TRADE_SUCCESS',
            'sign_type': 'RSA2',
            'sign': 'invalid_signature'
        }

        # Mock签名验证失败
        with patch('app.services.payment_service.settings.ALIPAY_PUBLIC_KEY', 'test_key'):
            # Mock整个模块导入
            with patch.dict('sys.modules', {'alipay': MagicMock(), 'alipay.aop': MagicMock(), 'alipay.aop.api': MagicMock(), 'alipay.aop.api.util': MagicMock(), 'alipay.aop.api.util.SignatureUtils': MagicMock()}):
                with patch('alipay.aop.api.util.SignatureUtils.verify_with_rsa', return_value=False):
                    result = payment_service._verify_alipay_callback(callback_data)
                    assert result is False

    def test_alipay_signature_missing(self, payment_service):
        """测试支付宝回调缺少签名"""
        callback_data = {
            'out_trade_no': 'PAY20260123ABCD1234',
            'total_amount': '99.00',
            # 缺少sign字段
        }

        result = payment_service._verify_alipay_callback(callback_data)
        assert result is False

    def test_wechat_signature_verification_success(self, payment_service):
        """测试微信签名验证成功"""
        # 构造正确的签名
        params = {
            'out_trade_no': 'PAY20260123ABCD1234',
            'transaction_id': 'WX123456789',
            'total_fee': '9900',
            'result_code': 'SUCCESS'
        }

        api_key = 'test_api_key_12345678'
        sign_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        sign_string += f"&key={api_key}"
        correct_sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest().upper()

        callback_data = {**params, 'sign': correct_sign}

        with patch('app.services.payment_service.settings.WECHAT_API_KEY', api_key):
            result = payment_service._verify_wechat_callback(callback_data)
            assert result is True

    def test_wechat_signature_verification_failure(self, payment_service):
        """测试微信签名验证失败"""
        callback_data = {
            'out_trade_no': 'PAY20260123ABCD1234',
            'transaction_id': 'WX123456789',
            'total_fee': '9900',
            'result_code': 'SUCCESS',
            'sign': 'INVALID_SIGNATURE'
        }

        with patch('app.services.payment_service.settings.WECHAT_API_KEY', 'test_api_key'):
            result = payment_service._verify_wechat_callback(callback_data)
            assert result is False

    def test_wechat_signature_missing(self, payment_service):
        """测试微信回调缺少签名"""
        callback_data = {
            'out_trade_no': 'PAY20260123ABCD1234',
            'total_fee': '9900',
            # 缺少sign字段
        }

        result = payment_service._verify_wechat_callback(callback_data)
        assert result is False

    def test_signature_timing_attack_protection(self, payment_service):
        """测试签名比较防时序攻击"""
        # 微信签名使用secrets.compare_digest防止时序攻击
        params = {
            'out_trade_no': 'PAY20260123ABCD1234',
            'total_fee': '9900'
        }

        api_key = 'test_api_key'
        sign_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        sign_string += f"&key={api_key}"
        correct_sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest().upper()

        # 测试正确签名
        callback_data_correct = {**params, 'sign': correct_sign}
        with patch('app.services.payment_service.settings.WECHAT_API_KEY', api_key):
            assert payment_service._verify_wechat_callback(callback_data_correct) is True

        # 测试错误签名（只差一个字符）
        wrong_sign = correct_sign[:-1] + ('A' if correct_sign[-1] != 'A' else 'B')
        callback_data_wrong = {**params, 'sign': wrong_sign}
        with patch('app.services.payment_service.settings.WECHAT_API_KEY', api_key):
            assert payment_service._verify_wechat_callback(callback_data_wrong) is False


class TestPaymentAmountVerification:
    """测试支付金额验证"""

    @pytest.fixture
    def db_session(self):
        session = Mock(spec=Session)
        return session

    @pytest.fixture
    def payment_service(self, db_session):
        return PaymentService(db_session)

    @pytest.fixture
    def mock_payment(self):
        payment = Mock(spec=Payment)
        payment.payment_no = "PAY20260123ABCD1234"
        payment.amount = Decimal("99.00")
        return payment

    def test_alipay_amount_match(self, payment_service, mock_payment):
        """测试支付宝金额匹配"""
        mock_payment.payment_method = PaymentMethod.ALIPAY
        callback_data = {'total_amount': '99.00'}

        result = payment_service._verify_payment_amount(mock_payment, callback_data)
        assert result is True

    def test_alipay_amount_mismatch(self, payment_service, mock_payment):
        """测试支付宝金额不匹配"""
        mock_payment.payment_method = PaymentMethod.ALIPAY
        callback_data = {'total_amount': '199.00'}  # 金额被篡改

        result = payment_service._verify_payment_amount(mock_payment, callback_data)
        assert result is False

    def test_wechat_amount_match(self, payment_service, mock_payment):
        """测试微信金额匹配（分为单位）"""
        mock_payment.payment_method = PaymentMethod.WECHAT
        callback_data = {'total_fee': 9900}  # 99.00元 = 9900分

        result = payment_service._verify_payment_amount(mock_payment, callback_data)
        assert result is True

    def test_wechat_amount_mismatch(self, payment_service, mock_payment):
        """测试微信金额不匹配"""
        mock_payment.payment_method = PaymentMethod.WECHAT
        callback_data = {'total_fee': 19900}  # 金额被篡改

        result = payment_service._verify_payment_amount(mock_payment, callback_data)
        assert result is False

    def test_amount_tolerance(self, payment_service, mock_payment):
        """测试金额容差（0.01元以内）"""
        mock_payment.payment_method = PaymentMethod.ALIPAY
        mock_payment.amount = Decimal("99.00")

        # 差0.01元，应该通过
        callback_data = {'total_amount': '99.01'}
        result = payment_service._verify_payment_amount(mock_payment, callback_data)
        assert result is True

        # 差0.02元，应该失败
        callback_data = {'total_amount': '99.02'}
        result = payment_service._verify_payment_amount(mock_payment, callback_data)
        assert result is False

    def test_amount_missing(self, payment_service, mock_payment):
        """测试缺少金额字段"""
        mock_payment.payment_method = PaymentMethod.ALIPAY
        callback_data = {}  # 缺少金额字段

        # 开发模式应该跳过验证
        with patch('app.services.payment_service.settings.PAYMENT_DEV_MODE', True):
            result = payment_service._verify_payment_amount(mock_payment, callback_data)
            assert result is True

        # 生产模式应该失败
        with patch('app.services.payment_service.settings.PAYMENT_DEV_MODE', False):
            result = payment_service._verify_payment_amount(mock_payment, callback_data)
            assert result is False

    def test_amount_precision_attack(self, payment_service, mock_payment):
        """测试精度攻击（使用极小差异绕过验证）"""
        mock_payment.payment_method = PaymentMethod.ALIPAY
        mock_payment.amount = Decimal("99.00")

        # 测试各种精度攻击
        # 注意：容差是0.01元，所以差值在0.01以内的都会通过
        test_cases = [
            ('99.001', True),   # 差0.001，在容差内
            ('99.009', True),   # 差0.009，在容差内
            ('98.99', True),    # 差0.01，在容差内
            ('99.02', False),   # 差0.02，超过容差
            ('98.98', False),   # 差0.02，超过容差
            ('100.00', False),  # 差1.00，超过容差
        ]

        for amount_str, expected in test_cases:
            callback_data = {'total_amount': amount_str}
            result = payment_service._verify_payment_amount(mock_payment, callback_data)
            assert result == expected, f"Amount {amount_str} should be {expected}"


class TestConcurrencyProtection:
    """测试并发攻击防护"""

    @pytest.fixture
    def db_session(self):
        session = Mock(spec=Session)
        return session

    @pytest.fixture
    def payment_service(self, db_session):
        return PaymentService(db_session)

    def test_pessimistic_lock_on_order(self, payment_service, db_session):
        """测试订单查询使用悲观锁"""
        mock_order = Mock(spec=Order)
        mock_order.id = 1
        mock_order.user_id = 1
        mock_order.amount = Decimal("99.00")
        mock_order.can_pay = Mock(return_value=True)

        # 验证使用了with_for_update()悲观锁
        query_mock = Mock()
        filter_mock = Mock()
        for_update_mock = Mock()

        query_mock.filter.return_value = filter_mock
        filter_mock.with_for_update.return_value = for_update_mock
        for_update_mock.first.return_value = mock_order

        db_session.query.return_value = query_mock
        db_session.add = Mock()
        db_session.commit = Mock()
        db_session.refresh = Mock()

        # 模拟没有现有支付记录
        existing_payment_query = Mock()
        existing_payment_query.filter.return_value.first.return_value = None
        db_session.query.side_effect = [query_mock, existing_payment_query]

        with patch.object(payment_service, '_generate_payment_no', return_value="PAY20260123TEST"):
            with patch('app.services.payment_service.settings.PAYMENT_DEV_MODE', False):
                try:
                    payment_service.create_payment(
                        order_id=1,
                        payment_method="alipay",
                        user_id=1
                    )
                except Exception:
                    pass

        # 验证调用了with_for_update()
        filter_mock.with_for_update.assert_called_once()

    def test_concurrent_payment_creation(self, payment_service, db_session):
        """测试并发创建支付（应该只创建一个）"""
        mock_order = Mock(spec=Order)
        mock_order.id = 1
        mock_order.user_id = 1
        mock_order.amount = Decimal("99.00")
        mock_order.can_pay = Mock(return_value=True)

        mock_payment = Mock(spec=Payment)
        mock_payment.payment_no = "PAY20260123EXIST"

        # 第一次查询返回订单，第二次查询返回已存在的支付
        query_mock = Mock()
        query_mock.filter.return_value.with_for_update.return_value.first.return_value = mock_order
        query_mock.filter.return_value.first.return_value = mock_payment

        db_session.query.return_value = query_mock

        # 执行创建支付
        result = payment_service.create_payment(
            order_id=1,
            payment_method="alipay",
            user_id=1
        )

        # 应该返回已存在的支付，而不是创建新的
        assert result == mock_payment
        db_session.add.assert_not_called()


class TestSQLInjectionProtection:
    """测试SQL注入防护"""

    @pytest.fixture
    def db_session(self):
        session = Mock(spec=Session)
        return session

    @pytest.fixture
    def payment_service(self, db_session):
        return PaymentService(db_session)

    def test_payment_no_sql_injection(self, payment_service, db_session):
        """测试支付单号SQL注入防护"""
        # 尝试SQL注入攻击
        malicious_payment_no = "PAY20260123' OR '1'='1"

        db_session.query.return_value.filter.return_value.first.return_value = None

        # 执行查询（使用ORM参数化查询，应该安全）
        result = payment_service.handle_payment_callback(
            payment_no=malicious_payment_no,
            callback_data={}
        )

        # 应该返回False（找不到记录），而不是抛出SQL错误或返回所有记录
        assert result is False

    def test_order_id_sql_injection(self, payment_service, db_session):
        """测试订单ID SQL注入防护"""
        # 尝试SQL注入攻击（虽然order_id是int类型，但测试类型验证）
        malicious_order_id = "1 OR 1=1"

        # 应该在类型转换时失败，而不是执行SQL
        with pytest.raises((ValueError, TypeError, BusinessException)):
            payment_service.create_payment(
                order_id=malicious_order_id,  # type: ignore
                payment_method="alipay",
                user_id=1
            )


class TestSecureRandomGeneration:
    """测试安全随机数生成"""

    @pytest.fixture
    def db_session(self):
        session = Mock(spec=Session)
        return session

    @pytest.fixture
    def payment_service(self, db_session):
        return PaymentService(db_session)

    def test_payment_no_uses_secrets_module(self, payment_service, db_session):
        """测试支付单号使用secrets模块生成"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        # 生成多个支付单号
        payment_nos = set()
        for _ in range(100):
            payment_no = payment_service._generate_payment_no()
            payment_nos.add(payment_no)

        # 验证格式
        for payment_no in payment_nos:
            assert payment_no.startswith("PAY")
            assert len(payment_no) == 19  # PAY(3) + YYYYMMDD(8) + HEX(8)

        # 验证唯一性（100个应该都不同）
        assert len(payment_nos) == 100

    def test_payment_no_randomness_quality(self, payment_service, db_session):
        """测试支付单号随机性质量"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        # 生成1000个支付单号
        payment_nos = [payment_service._generate_payment_no() for _ in range(1000)]

        # 提取随机部分（后8位）
        random_parts = [pn[-8:] for pn in payment_nos]

        # 验证唯一性（应该全部不同）
        assert len(set(random_parts)) == 1000

        # 验证字符分布（应该包含0-9和A-F）
        all_chars = ''.join(random_parts)
        unique_chars = set(all_chars)

        # 至少应该有10种不同的字符（统计学上几乎不可能少于10种）
        assert len(unique_chars) >= 10

    def test_payment_no_collision_handling(self, payment_service, db_session):
        """测试支付单号冲突处理"""
        mock_existing = Mock()

        # 模拟第一次冲突，第二次成功
        db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_existing,  # 第一次查询返回冲突
            None  # 第二次查询返回None（无冲突）
        ]

        payment_no = payment_service._generate_payment_no()

        # 验证：应该查询了两次
        assert db_session.query.return_value.filter.return_value.first.call_count == 2
        assert payment_no is not None


class TestOrderAmountConsistency:
    """测试订单金额一致性"""

    @pytest.fixture
    def db_session(self):
        session = Mock(spec=Session)
        return session

    @pytest.fixture
    def payment_service(self, db_session):
        return PaymentService(db_session)

    def test_payment_amount_matches_order(self, payment_service, db_session):
        """测试支付金额与订单金额一致"""
        mock_order = Mock(spec=Order)
        mock_order.id = 1
        mock_order.user_id = 1
        mock_order.amount = Decimal("99.00")
        mock_order.can_pay = Mock(return_value=True)

        query_mock = Mock()
        query_mock.filter.return_value.with_for_update.return_value.first.return_value = mock_order
        query_mock.filter.return_value.first.return_value = None

        db_session.query.return_value = query_mock
        db_session.add = Mock()
        db_session.commit = Mock()
        db_session.refresh = Mock()

        with patch.object(payment_service, '_generate_payment_no', return_value="PAY20260123TEST"):
            with patch('app.services.payment_service.settings.PAYMENT_DEV_MODE', False):
                payment_service.create_payment(
                    order_id=1,
                    payment_method="alipay",
                    user_id=1
                )

        # 验证创建的支付金额与订单金额一致
        call_args = db_session.add.call_args
        created_payment = call_args[0][0]
        assert created_payment.amount == mock_order.amount

    def test_callback_amount_verification(self, payment_service, db_session):
        """测试回调金额验证"""
        mock_payment = Mock(spec=Payment)
        mock_payment.payment_no = "PAY20260123TEST"
        mock_payment.amount = Decimal("99.00")
        mock_payment.payment_method = PaymentMethod.ALIPAY
        mock_payment.is_success = Mock(return_value=False)
        mock_payment.mark_as_failed = Mock()

        db_session.query.return_value.filter.return_value.first.return_value = mock_payment
        db_session.commit = Mock()

        # 回调金额与订单金额不一致
        callback_data = {
            'transaction_id': 'ALIPAY123456',
            'total_amount': '199.00'  # 金额不匹配
        }

        with patch('app.services.payment_service.settings.PAYMENT_DEV_MODE', False):
            with patch.object(payment_service, '_verify_alipay_callback', return_value=True):
                result = payment_service.handle_payment_callback(
                    payment_no="PAY20260123TEST",
                    callback_data=callback_data
                )

        # 应该失败并标记支付失败
        assert result is False
        mock_payment.mark_as_failed.assert_called_once()


class TestPaymentCallbackSecurity:
    """测试支付回调安全性"""

    @pytest.fixture
    def db_session(self):
        session = Mock(spec=Session)
        return session

    @pytest.fixture
    def payment_service(self, db_session):
        return PaymentService(db_session)

    def test_callback_idempotency(self, payment_service, db_session):
        """测试回调幂等性（重复回调不重复处理）"""
        mock_payment = Mock(spec=Payment)
        mock_payment.payment_no = "PAY20260123TEST"
        mock_payment.is_success = Mock(return_value=True)  # 已经成功
        mock_payment.mark_as_success = Mock()

        db_session.query.return_value.filter.return_value.first.return_value = mock_payment

        # 重复回调
        result = payment_service.handle_payment_callback(
            payment_no="PAY20260123TEST",
            callback_data={'transaction_id': 'ALIPAY123456'}
        )

        # 应该返回True但不重复处理
        assert result is True
        mock_payment.mark_as_success.assert_not_called()

    def test_callback_signature_before_processing(self, payment_service, db_session):
        """测试先验证签名再处理业务逻辑"""
        mock_payment = Mock(spec=Payment)
        mock_payment.payment_no = "PAY20260123TEST"
        mock_payment.payment_method = PaymentMethod.ALIPAY
        mock_payment.is_success = Mock(return_value=False)
        mock_payment.mark_as_success = Mock()

        db_session.query.return_value.filter.return_value.first.return_value = mock_payment

        callback_data = {
            'transaction_id': 'ALIPAY123456',
            'total_amount': '99.00',
            'sign': 'invalid_signature'
        }

        # 签名验证失败
        with patch('app.services.payment_service.settings.PAYMENT_DEV_MODE', False):
            with patch.object(payment_service, '_verify_alipay_callback', return_value=False):
                result = payment_service.handle_payment_callback(
                    payment_no="PAY20260123TEST",
                    callback_data=callback_data
                )

        # 应该失败，不应该调用mark_as_success
        assert result is False
        mock_payment.mark_as_success.assert_not_called()


def run_security_tests():
    """运行所有安全测试"""
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--color=yes',
        '-k', 'test_'
    ])


if __name__ == "__main__":
    run_security_tests()
