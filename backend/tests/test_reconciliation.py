"""
对账系统测试用例

版本: 1.0
创建日期: 2026-01-23
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.models.reconciliation import (
    ReconciliationRecord, ReconciliationDifference,
    ReconciliationStatus, ReconciliationType,
    DifferenceType, DifferenceStatus
)
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.order import Order, OrderStatus
from app.models.user import User, UserType, UserStatus
from app.services.reconciliation_service import (
    ReconciliationService, RemoteTransaction, ReconciliationSummary
)
from app.core.errors import BusinessException, RecordNotFoundError


class TestReconciliationModels:
    """测试对账数据模型"""

    def test_reconciliation_record_creation(self, test_db: Session):
        """测试对账记录创建"""
        record = ReconciliationRecord(
            reconciliation_date="2026-01-22",
            reconciliation_type=ReconciliationType.DAILY,
            start_time=datetime(2026, 1, 22, 0, 0, 0),
            end_time=datetime(2026, 1, 22, 23, 59, 59)
        )

        test_db.add(record)
        test_db.commit()
        test_db.refresh(record)

        assert record.id is not None
        assert record.batch_no is not None
        assert record.reconciliation_date == "2026-01-22"
        assert record.status == ReconciliationStatus.PENDING
        assert record.is_pending()

    def test_reconciliation_record_status_methods(self, test_db: Session):
        """测试对账记录状态方法"""
        record = ReconciliationRecord(
            reconciliation_date="2026-01-22",
            reconciliation_type=ReconciliationType.DAILY,
            start_time=datetime(2026, 1, 22, 0, 0, 0),
            end_time=datetime(2026, 1, 22, 23, 59, 59)
        )

        # 测试开始对账
        record.start_reconciliation()
        assert record.is_processing()
        assert record.started_at is not None

        # 测试完成对账
        record.complete_reconciliation(has_differences=False)
        assert record.is_success()
        assert record.completed_at is not None
        assert record.duration_seconds is not None

        # 测试失败对账
        record.fail_reconciliation("测试错误")
        assert record.is_failed()
        assert record.error_message == "测试错误"

    def test_reconciliation_difference_creation(self, test_db: Session):
        """测试差异记录创建"""
        # 先创建对账记录
        reconciliation_record = ReconciliationRecord(
            reconciliation_date="2026-01-22",
            reconciliation_type=ReconciliationType.DAILY,
            start_time=datetime(2026, 1, 22, 0, 0, 0),
            end_time=datetime(2026, 1, 22, 23, 59, 59)
        )
        test_db.add(reconciliation_record)
        test_db.commit()

        # 创建差异记录
        difference = ReconciliationDifference(
            reconciliation_id=reconciliation_record.id,
            difference_type=DifferenceType.MISSING_LOCAL,
            remote_transaction_id="remote_123",
            remote_amount=Decimal("100.00"),
            description="本地缺失交易记录"
        )

        test_db.add(difference)
        test_db.commit()
        test_db.refresh(difference)

        assert difference.id is not None
        assert difference.is_pending()
        assert difference.difference_type == DifferenceType.MISSING_LOCAL

    def test_reconciliation_difference_data_methods(self, test_db: Session):
        """测试差异记录数据方法"""
        reconciliation_record = ReconciliationRecord(
            reconciliation_date="2026-01-22",
            reconciliation_type=ReconciliationType.DAILY,
            start_time=datetime(2026, 1, 22, 0, 0, 0),
            end_time=datetime(2026, 1, 22, 23, 59, 59)
        )
        test_db.add(reconciliation_record)
        test_db.commit()

        difference = ReconciliationDifference(
            reconciliation_id=reconciliation_record.id,
            difference_type=DifferenceType.AMOUNT_MISMATCH
        )

        # 测试设置和获取数据
        test_data = {"transaction_id": "123", "amount": 100.00}
        difference.set_local_data(test_data)
        difference.set_remote_data(test_data)

        assert difference.get_local_data() == test_data
        assert difference.get_remote_data() == test_data

    def test_reconciliation_difference_status_methods(self, test_db: Session):
        """测试差异记录状态方法"""
        reconciliation_record = ReconciliationRecord(
            reconciliation_date="2026-01-22",
            reconciliation_type=ReconciliationType.DAILY,
            start_time=datetime(2026, 1, 22, 0, 0, 0),
            end_time=datetime(2026, 1, 22, 23, 59, 59)
        )
        test_db.add(reconciliation_record)
        test_db.commit()

        difference = ReconciliationDifference(
            reconciliation_id=reconciliation_record.id,
            difference_type=DifferenceType.MISSING_LOCAL
        )

        # 测试开始处理
        difference.start_processing("admin")
        assert difference.is_processing()
        assert difference.processed_by == "admin"

        # 测试标记为已解决
        difference.mark_as_resolved("auto_supplement", "已自动补单")
        assert difference.is_resolved()
        assert difference.resolution_action == "auto_supplement"

        # 测试标记为已忽略
        difference.mark_as_ignored("测试忽略")
        assert difference.is_ignored()
        assert difference.remark == "测试忽略"


class TestReconciliationService:
    """测试对账服务"""

    @pytest.fixture
    def reconciliation_service(self, test_db: Session):
        """创建对账服务实例"""
        return ReconciliationService(test_db)

    @pytest.fixture
    def sample_user(self, test_db: Session):
        """创建测试用户"""
        user = User(
            username="testuser",
            email="test@example.com",
            user_type=UserType.INDIVIDUAL,
            status=UserStatus.ACTIVE
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        return user

    @pytest.fixture
    def sample_order(self, test_db: Session, sample_user):
        """创建测试订单"""
        order = Order(
            user_id=sample_user.id,
            package_name="测试套餐",
            package_type="basic",
            amount=Decimal("100.00"),
            chat_quota=1000,
            generation_quota=500,
            token_quota=10000,
            storage_quota_mb=1024,
            status=OrderStatus.PAID
        )
        test_db.add(order)
        test_db.commit()
        test_db.refresh(order)
        return order

    @pytest.fixture
    def sample_payment(self, test_db: Session, sample_order):
        """创建测试支付记录"""
        payment = Payment(
            order_id=sample_order.id,
            amount=Decimal("100.00"),
            payment_method=PaymentMethod.ALIPAY,
            status=PaymentStatus.SUCCESS,
            transaction_id="test_transaction_123",
            paid_at=datetime.utcnow()
        )
        test_db.add(payment)
        test_db.commit()
        test_db.refresh(payment)
        return payment

    def test_start_reconciliation_success(self, reconciliation_service, test_db: Session):
        """测试启动对账成功"""
        target_date = "2026-01-22"

        with patch.object(reconciliation_service, '_execute_reconciliation') as mock_execute:
            record = reconciliation_service.start_reconciliation(
                reconciliation_date=target_date,
                reconciliation_type=ReconciliationType.MANUAL
            )

            assert record.reconciliation_date == target_date
            assert record.reconciliation_type == ReconciliationType.MANUAL
            mock_execute.assert_called_once_with(record)

    def test_start_reconciliation_invalid_date(self, reconciliation_service):
        """测试启动对账 - 无效日期"""
        with pytest.raises(BusinessException) as exc_info:
            reconciliation_service.start_reconciliation("invalid-date")

        assert "对账日期格式无效" in str(exc_info.value.message)

    def test_start_reconciliation_duplicate(self, reconciliation_service, test_db: Session):
        """测试启动对账 - 重复对账"""
        target_date = "2026-01-22"

        # 创建已存在的对账记录
        existing_record = ReconciliationRecord(
            reconciliation_date=target_date,
            reconciliation_type=ReconciliationType.DAILY,
            start_time=datetime(2026, 1, 22, 0, 0, 0),
            end_time=datetime(2026, 1, 22, 23, 59, 59),
            status=ReconciliationStatus.SUCCESS
        )
        test_db.add(existing_record)
        test_db.commit()

        # 尝试重复对账
        with pytest.raises(BusinessException) as exc_info:
            reconciliation_service.start_reconciliation(target_date)

        assert "对账记录已存在" in str(exc_info.value.message)

    def test_get_local_payments(self, reconciliation_service, test_db: Session, sample_payment):
        """测试获取本地支付记录"""
        start_time = datetime(2026, 1, 22, 0, 0, 0)
        end_time = datetime(2026, 1, 22, 23, 59, 59)

        # 更新支付时间到测试范围内
        sample_payment.paid_at = datetime(2026, 1, 22, 12, 0, 0)
        test_db.commit()

        payments = reconciliation_service._get_local_payments(start_time, end_time)

        assert len(payments) == 1
        assert payments[0].id == sample_payment.id

    def test_match_transactions_perfect_match(self, reconciliation_service, sample_payment):
        """测试交易匹配 - 完美匹配"""
        local_payments = [sample_payment]
        remote_transactions = [
            RemoteTransaction(
                transaction_id=sample_payment.transaction_id,
                order_no=sample_payment.order.order_no,
                amount=sample_payment.amount,
                status="success",
                paid_at=sample_payment.paid_at,
                channel="alipay",
                raw_data={}
            )
        ]

        summary, differences = reconciliation_service._match_transactions(
            local_payments, remote_transactions
        )

        assert summary.matched_count == 1
        assert summary.difference_count == 0
        assert len(differences) == 0

    def test_match_transactions_missing_remote(self, reconciliation_service, sample_payment):
        """测试交易匹配 - 第三方缺失"""
        local_payments = [sample_payment]
        remote_transactions = []

        summary, differences = reconciliation_service._match_transactions(
            local_payments, remote_transactions
        )

        assert summary.matched_count == 0
        assert summary.difference_count == 1
        assert len(differences) == 1
        assert differences[0]['type'] == DifferenceType.MISSING_REMOTE

    def test_match_transactions_missing_local(self, reconciliation_service):
        """测试交易匹配 - 本地缺失"""
        local_payments = []
        remote_transactions = [
            RemoteTransaction(
                transaction_id="remote_123",
                order_no="order_123",
                amount=Decimal("100.00"),
                status="success",
                paid_at=datetime.utcnow(),
                channel="alipay",
                raw_data={}
            )
        ]

        summary, differences = reconciliation_service._match_transactions(
            local_payments, remote_transactions
        )

        assert summary.matched_count == 0
        assert summary.difference_count == 1
        assert len(differences) == 1
        assert differences[0]['type'] == DifferenceType.MISSING_LOCAL

    def test_match_transactions_amount_mismatch(self, reconciliation_service, sample_payment):
        """测试交易匹配 - 金额不匹配"""
        local_payments = [sample_payment]
        remote_transactions = [
            RemoteTransaction(
                transaction_id=sample_payment.transaction_id,
                order_no=sample_payment.order.order_no,
                amount=Decimal("200.00"),  # 不同的金额
                status="success",
                paid_at=sample_payment.paid_at,
                channel="alipay",
                raw_data={}
            )
        ]

        summary, differences = reconciliation_service._match_transactions(
            local_payments, remote_transactions
        )

        assert summary.matched_count == 0
        assert summary.difference_count == 1
        assert len(differences) == 1
        assert differences[0]['type'] == DifferenceType.AMOUNT_MISMATCH

    def test_get_reconciliation_records(self, reconciliation_service, test_db: Session):
        """测试查询对账记录"""
        # 创建测试数据
        record1 = ReconciliationRecord(
            reconciliation_date="2026-01-22",
            reconciliation_type=ReconciliationType.DAILY,
            start_time=datetime(2026, 1, 22, 0, 0, 0),
            end_time=datetime(2026, 1, 22, 23, 59, 59),
            status=ReconciliationStatus.SUCCESS
        )
        record2 = ReconciliationRecord(
            reconciliation_date="2026-01-21",
            reconciliation_type=ReconciliationType.DAILY,
            start_time=datetime(2026, 1, 21, 0, 0, 0),
            end_time=datetime(2026, 1, 21, 23, 59, 59),
            status=ReconciliationStatus.FAILED
        )

        test_db.add_all([record1, record2])
        test_db.commit()

        # 测试查询所有记录
        records, total = reconciliation_service.get_reconciliation_records()
        assert total == 2
        assert len(records) == 2

        # 测试状态过滤
        records, total = reconciliation_service.get_reconciliation_records(
            status=ReconciliationStatus.SUCCESS
        )
        assert total == 1
        assert records[0].status == ReconciliationStatus.SUCCESS

    def test_fix_difference_auto_supplement(self, reconciliation_service, test_db: Session):
        """测试修复差异 - 自动补单"""
        # 创建对账记录和差异记录
        reconciliation_record = ReconciliationRecord(
            reconciliation_date="2026-01-22",
            reconciliation_type=ReconciliationType.DAILY,
            start_time=datetime(2026, 1, 22, 0, 0, 0),
            end_time=datetime(2026, 1, 22, 23, 59, 59)
        )
        test_db.add(reconciliation_record)
        test_db.commit()

        difference = ReconciliationDifference(
            reconciliation_id=reconciliation_record.id,
            difference_type=DifferenceType.MISSING_LOCAL,
            remote_transaction_id="remote_123"
        )
        test_db.add(difference)
        test_db.commit()

        # Mock自动补单方法
        with patch.object(reconciliation_service, '_auto_supplement_transaction', return_value="补单成功"):
            result = reconciliation_service.fix_difference(
                difference_id=difference.id,
                action="auto_supplement",
                processed_by="admin"
            )

            assert result.is_resolved()
            assert result.resolution_action == "auto_supplement"

    def test_fix_difference_ignore(self, reconciliation_service, test_db: Session):
        """测试修复差异 - 忽略"""
        # 创建对账记录和差异记录
        reconciliation_record = ReconciliationRecord(
            reconciliation_date="2026-01-22",
            reconciliation_type=ReconciliationType.DAILY,
            start_time=datetime(2026, 1, 22, 0, 0, 0),
            end_time=datetime(2026, 1, 22, 23, 59, 59)
        )
        test_db.add(reconciliation_record)
        test_db.commit()

        difference = ReconciliationDifference(
            reconciliation_id=reconciliation_record.id,
            difference_type=DifferenceType.AMOUNT_MISMATCH
        )
        test_db.add(difference)
        test_db.commit()

        result = reconciliation_service.fix_difference(
            difference_id=difference.id,
            action="ignore",
            processed_by="admin",
            remark="测试忽略"
        )

        assert result.is_ignored()
        assert result.remark == "测试忽略"

    def test_fix_difference_not_found(self, reconciliation_service):
        """测试修复差异 - 记录不存在"""
        with pytest.raises(RecordNotFoundError):
            reconciliation_service.fix_difference(
                difference_id=99999,
                action="ignore",
                processed_by="admin"
            )

    def test_generate_reconciliation_report(self, reconciliation_service, test_db: Session):
        """测试生成对账报告"""
        # 创建对账记录
        record = ReconciliationRecord(
            reconciliation_date="2026-01-22",
            reconciliation_type=ReconciliationType.DAILY,
            start_time=datetime(2026, 1, 22, 0, 0, 0),
            end_time=datetime(2026, 1, 22, 23, 59, 59),
            total_local_count=10,
            total_remote_count=9,
            matched_count=8,
            difference_count=2,
            total_local_amount=Decimal("1000.00"),
            matched_amount=Decimal("800.00"),
            difference_amount=Decimal("200.00")
        )
        test_db.add(record)
        test_db.commit()

        # 创建差异记录
        difference = ReconciliationDifference(
            reconciliation_id=record.id,
            difference_type=DifferenceType.MISSING_LOCAL,
            status=DifferenceStatus.PENDING
        )
        test_db.add(difference)
        test_db.commit()

        # 生成报告
        report = reconciliation_service.generate_reconciliation_report(record.id)

        assert "reconciliation_info" in report
        assert "summary" in report
        assert "differences" in report
        assert "difference_statistics" in report

        # 验证汇总信息
        summary = report["summary"]
        assert summary["total_local_count"] == 10
        assert summary["matched_count"] == 8
        assert summary["match_rate"] == 80.0

    def test_retry_failed_reconciliation(self, reconciliation_service, test_db: Session):
        """测试重试失败的对账"""
        # 创建失败的对账记录
        failed_record = ReconciliationRecord(
            reconciliation_date="2026-01-22",
            reconciliation_type=ReconciliationType.DAILY,
            start_time=datetime(2026, 1, 22, 0, 0, 0),
            end_time=datetime(2026, 1, 22, 23, 59, 59),
            status=ReconciliationStatus.FAILED
        )
        test_db.add(failed_record)
        test_db.commit()

        with patch.object(reconciliation_service, '_execute_reconciliation'):
            new_record = reconciliation_service.retry_failed_reconciliation(failed_record.id)

            assert new_record.reconciliation_date == failed_record.reconciliation_date
            assert new_record.reconciliation_type == ReconciliationType.RETRY
            assert new_record.id != failed_record.id


class TestReconciliationIntegration:
    """对账系统集成测试"""

    @pytest.fixture
    def reconciliation_service(self, test_db: Session):
        """创建对账服务实例"""
        return ReconciliationService(test_db)

    def test_full_reconciliation_workflow(self, reconciliation_service, test_db: Session):
        """测试完整的对账工作流程"""
        target_date = "2026-01-22"

        # Mock第三方交易数据
        with patch.object(reconciliation_service, '_get_remote_transactions', return_value=[]):
            with patch.object(reconciliation_service, '_get_local_payments', return_value=[]):
                # 启动对账
                record = reconciliation_service.start_reconciliation(target_date)

                # 验证对账记录状态
                assert record.reconciliation_date == target_date
                assert record.is_success()  # 没有交易数据，应该成功完成

                # 查询对账记录
                records, total = reconciliation_service.get_reconciliation_records()
                assert total == 1
                assert records[0].id == record.id

                # 生成报告
                report = reconciliation_service.generate_reconciliation_report(record.id)
                assert report["summary"]["total_local_count"] == 0
                assert report["summary"]["total_remote_count"] == 0