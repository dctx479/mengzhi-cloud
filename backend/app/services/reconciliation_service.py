"""
对账服务层

版本: 1.0
创建日期: 2026-01-23
"""

from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date, timedelta
from loguru import logger
from decimal import Decimal
import json
import asyncio
import os
from dataclasses import dataclass

from app.models.reconciliation import (
    ReconciliationRecord, ReconciliationDifference,
    ReconciliationStatus, ReconciliationType,
    DifferenceType, DifferenceStatus
)
from app.models.payment import Payment, PaymentStatus
from app.models.order import Order, OrderStatus
from app.core.errors import BusinessException, ErrorCode, RecordNotFoundError
from app.core.config import settings


@dataclass
class RemoteTransaction:
    """第三方交易记录数据类"""
    transaction_id: str
    order_no: str
    amount: Decimal
    status: str
    paid_at: datetime
    channel: str
    raw_data: Dict[str, Any]


@dataclass
class ReconciliationSummary:
    """对账汇总数据类"""
    total_local_count: int
    total_remote_count: int
    matched_count: int
    difference_count: int
    total_local_amount: Decimal
    total_remote_amount: Decimal
    matched_amount: Decimal
    difference_amount: Decimal


class ReconciliationService:
    """对账服务类

    提供支付对账相关的业务逻辑操作:
    - 每日自动对账
    - 与支付平台账单对比
    - 差异检测和报告
    - 自动补单
    - 对账报告生成
    """

    def __init__(self, db: Session) -> None:
        """初始化服务

        Args:
            db: SQLAlchemy数据库会话
        """
        self.db = db

    def start_reconciliation(
        self,
        reconciliation_date: str,
        reconciliation_type: ReconciliationType = ReconciliationType.DAILY,
        force: bool = False
    ) -> ReconciliationRecord:
        """启动对账流程

        Args:
            reconciliation_date: 对账日期 (YYYY-MM-DD)
            reconciliation_type: 对账类型
            force: 是否强制重新对账

        Returns:
            对账记录对象

        Raises:
            BusinessException: 对账日期无效、已存在对账记录等
        """
        logger.info(f"开始对账: date={reconciliation_date}, type={reconciliation_type.value}")

        # 验证对账日期
        try:
            target_date = datetime.strptime(reconciliation_date, "%Y-%m-%d").date()
        except ValueError:
            raise BusinessException(
                code=ErrorCode.INVALID_PARAMETER,
                message="对账日期格式无效，应为 YYYY-MM-DD"
            )

        # 检查是否已存在对账记录
        existing_record = self.db.query(ReconciliationRecord).filter(
            and_(
                ReconciliationRecord.reconciliation_date == reconciliation_date,
                ReconciliationRecord.status.in_([
                    ReconciliationStatus.PENDING,
                    ReconciliationStatus.PROCESSING,
                    ReconciliationStatus.SUCCESS
                ])
            )
        ).first()

        if existing_record and not force:
            logger.warning(f"对账记录已存在: {existing_record.batch_no}")
            raise BusinessException(
                code=ErrorCode.DUPLICATE_OPERATION,
                message=f"日期 {reconciliation_date} 的对账记录已存在"
            )

        # 计算对账时间范围
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = datetime.combine(target_date, datetime.max.time())

        # 创建对账记录
        reconciliation_record = ReconciliationRecord(
            reconciliation_date=reconciliation_date,
            reconciliation_type=reconciliation_type,
            start_time=start_time,
            end_time=end_time
        )

        self.db.add(reconciliation_record)
        try:
            self.db.commit()
        except IntegrityError:
            # 并发场景：另一个请求在检查之后、commit 之前已插入相同日期的记录
            self.db.rollback()
            raise BusinessException(
                code=ErrorCode.DUPLICATE_OPERATION,
                message=f"日期 {reconciliation_date} 的对账记录已存在（并发冲突）"
            )
        self.db.refresh(reconciliation_record)

        logger.info(f"创建对账记录: {reconciliation_record.batch_no}")

        # 异步执行对账
        try:
            self._execute_reconciliation(reconciliation_record)
        except Exception as e:
            logger.error(f"对账执行失败: {str(e)}")
            reconciliation_record.fail_reconciliation(str(e))
            self.db.commit()
            raise

        return reconciliation_record

    def _execute_reconciliation(self, record: ReconciliationRecord) -> None:
        """执行对账流程

        Args:
            record: 对账记录
        """
        record.start_reconciliation()
        self.db.commit()

        try:
            # 1. 获取本地交易数据
            local_payments = self._get_local_payments(record.start_time, record.end_time)
            logger.info(f"获取本地交易数据: {len(local_payments)} 条")

            # 2. 获取第三方交易数据
            remote_transactions = self._get_remote_transactions(record.start_time, record.end_time)
            logger.info(f"获取第三方交易数据: {len(remote_transactions)} 条")

            # 3. 执行对账匹配
            summary, differences = self._match_transactions(local_payments, remote_transactions)

            # 4. 更新对账记录统计信息
            self._update_reconciliation_summary(record, summary)

            # 5. 保存差异记录
            if differences:
                self._save_differences(record.id, differences)
                logger.warning(f"发现 {len(differences)} 条差异记录")

            # 6. 完成对账
            record.complete_reconciliation(has_differences=len(differences) > 0)
            self.db.commit()

            logger.info(f"对账完成: {record.batch_no}, 差异数量: {len(differences)}")

        except Exception as e:
            logger.error(f"对账执行异常: {str(e)}")
            record.fail_reconciliation(str(e))
            self.db.commit()
            raise

    def _get_local_payments(self, start_time: datetime, end_time: datetime) -> List[Payment]:
        """获取本地支付记录

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            支付记录列表
        """
        return self.db.query(Payment).filter(
            and_(
                Payment.status == PaymentStatus.SUCCESS,
                Payment.paid_at >= start_time,
                Payment.paid_at <= end_time,
                Payment.transaction_id.isnot(None)
            )
        ).all()

    def _get_remote_transactions(self, start_time: datetime, end_time: datetime) -> List[RemoteTransaction]:
        """获取第三方交易记录

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            第三方交易记录列表

        实现方式：
        1. 遍历 channels=['wechat', 'alipay']
        2. 用对应 Fetcher 下载对账单文件
        3. 用对应 Parser 解析为 RemoteTransaction 列表
        4. 合并返回

        注：Fetcher 默认 Mock 模式（不下载真实账单），返回示例文件路径。
        设置环境变量 WECHAT_BILL_API_KEY / ALIPAY_BILL_API_KEY 后启用真实模式。
        """
        from app.services.reconciliation.fetchers import get_fetcher
        from app.services.reconciliation.parsers import get_parser

        remote_transactions: List[RemoteTransaction] = []
        channels = ["wechat", "alipay"]

        for channel in channels:
            try:
                fetcher = get_fetcher(channel)
                bill_path = fetcher.fetch(start_time.date())
                if not bill_path or not os.path.exists(bill_path):
                    logger.debug(f"[_get_remote_transactions] No bill file for channel={channel}")
                    continue
                parser = get_parser(channel)
                txs = parser.parse(bill_path)
                # 按时间窗口过滤
                filtered = [t for t in txs if start_time <= t.paid_at <= end_time]
                remote_transactions.extend(filtered)
                logger.info(
                    f"[_get_remote_transactions] channel={channel}: parsed={len(txs)}, in_window={len(filtered)}"
                )
            except Exception as e:
                logger.error(f"[_get_remote_transactions] channel={channel} failed: {e}")
                continue

        return remote_transactions

    def _match_transactions(
        self,
        local_payments: List[Payment],
        remote_transactions: List[RemoteTransaction]
    ) -> Tuple[ReconciliationSummary, List[Dict[str, Any]]]:
        """匹配本地和第三方交易记录

        Args:
            local_payments: 本地支付记录
            remote_transactions: 第三方交易记录

        Returns:
            对账汇总信息和差异记录列表
        """
        logger.info("开始匹配交易记录")

        # 构建索引以提高匹配效率
        local_index = {p.transaction_id: p for p in local_payments if p.transaction_id}
        remote_index = {t.transaction_id: t for t in remote_transactions}

        matched_count = 0
        matched_amount = Decimal('0')
        differences = []

        # 1. 检查本地记录在第三方是否存在
        for payment in local_payments:
            if not payment.transaction_id:
                continue

            remote_transaction = remote_index.get(payment.transaction_id)

            if remote_transaction is None:
                # 本地有，第三方无
                differences.append({
                    'type': DifferenceType.MISSING_REMOTE,
                    'local_payment': payment,
                    'remote_transaction': None,
                    'description': f"第三方缺失交易记录: {payment.transaction_id}"
                })
            else:
                # 检查金额是否匹配
                if abs(payment.amount - remote_transaction.amount) > Decimal('0.01'):
                    differences.append({
                        'type': DifferenceType.AMOUNT_MISMATCH,
                        'local_payment': payment,
                        'remote_transaction': remote_transaction,
                        'description': f"金额不匹配: 本地={payment.amount}, 第三方={remote_transaction.amount}"
                    })
                else:
                    matched_count += 1
                    matched_amount += payment.amount

        # 2. 检查第三方记录在本地是否存在
        for transaction in remote_transactions:
            if transaction.transaction_id not in local_index:
                # 第三方有，本地无
                differences.append({
                    'type': DifferenceType.MISSING_LOCAL,
                    'local_payment': None,
                    'remote_transaction': transaction,
                    'description': f"本地缺失交易记录: {transaction.transaction_id}"
                })

        # 构建汇总信息
        total_local_amount = sum((p.amount for p in local_payments), Decimal('0'))
        total_remote_amount = sum((t.amount for t in remote_transactions), Decimal('0'))
        # difference_amount 表示本地与第三方的净金额差异（绝对值）
        difference_amount = abs(total_local_amount - total_remote_amount)

        summary = ReconciliationSummary(
            total_local_count=len(local_payments),
            total_remote_count=len(remote_transactions),
            matched_count=matched_count,
            difference_count=len(differences),
            total_local_amount=total_local_amount,
            total_remote_amount=total_remote_amount,
            matched_amount=matched_amount,
            difference_amount=difference_amount
        )

        logger.info(f"匹配完成: 匹配={matched_count}, 差异={len(differences)}")
        return summary, differences

    def _update_reconciliation_summary(
        self,
        record: ReconciliationRecord,
        summary: ReconciliationSummary
    ) -> None:
        """更新对账记录汇总信息

        Args:
            record: 对账记录
            summary: 汇总信息
        """
        record.total_local_count = summary.total_local_count
        record.total_remote_count = summary.total_remote_count
        record.matched_count = summary.matched_count
        record.difference_count = summary.difference_count
        record.total_local_amount = summary.total_local_amount
        record.total_remote_amount = summary.total_remote_amount
        record.matched_amount = summary.matched_amount
        record.difference_amount = summary.difference_amount

    def _save_differences(self, reconciliation_id: int, differences: List[Dict[str, Any]]) -> None:
        """保存差异记录

        Args:
            reconciliation_id: 对账记录ID
            differences: 差异记录列表
        """
        for diff_data in differences:
            difference = ReconciliationDifference(
                reconciliation_id=reconciliation_id,
                difference_type=diff_data['type'],
                description=diff_data['description']
            )

            # 设置本地支付信息
            local_payment = diff_data.get('local_payment')
            if local_payment:
                difference.local_payment_id = local_payment.id
                difference.local_transaction_id = local_payment.transaction_id
                difference.local_amount = local_payment.amount
                difference.local_status = local_payment.status.value
                difference.local_paid_at = local_payment.paid_at
                difference.set_local_data(local_payment.to_dict())

            # 设置第三方交易信息
            remote_transaction = diff_data.get('remote_transaction')
            if remote_transaction:
                difference.remote_transaction_id = remote_transaction.transaction_id
                difference.remote_amount = remote_transaction.amount
                difference.remote_status = remote_transaction.status
                difference.remote_paid_at = remote_transaction.paid_at
                difference.set_remote_data(remote_transaction.raw_data)

            # 计算金额差异
            if local_payment and remote_transaction:
                difference.amount_difference = local_payment.amount - remote_transaction.amount

            self.db.add(difference)

        # Flush to ensure all differences are inserted and assigned IDs
        self.db.flush()

    def get_reconciliation_records(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[ReconciliationStatus] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Tuple[List[ReconciliationRecord], int]:
        """查询对账记录

        Args:
            page: 页码
            page_size: 每页大小
            status: 对账状态
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            对账记录列表和总数
        """
        query = self.db.query(ReconciliationRecord)

        # 状态过滤
        if status:
            query = query.filter(ReconciliationRecord.status == status)

        # 日期范围过滤
        if start_date:
            query = query.filter(ReconciliationRecord.reconciliation_date >= start_date)
        if end_date:
            query = query.filter(ReconciliationRecord.reconciliation_date <= end_date)

        # 获取总数
        total = query.count()

        # 分页查询
        records = query.order_by(ReconciliationRecord.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return records, total

    def get_reconciliation_differences(
        self,
        reconciliation_id: Optional[int] = None,
        status: Optional[DifferenceStatus] = None,
        difference_type: Optional[DifferenceType] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ReconciliationDifference], int]:
        """查询差异记录

        Args:
            reconciliation_id: 对账记录ID
            status: 差异状态
            difference_type: 差异类型
            page: 页码
            page_size: 每页大小

        Returns:
            差异记录列表和总数
        """
        query = self.db.query(ReconciliationDifference)

        # 对账记录过滤
        if reconciliation_id:
            query = query.filter(ReconciliationDifference.reconciliation_id == reconciliation_id)

        # 状态过滤
        if status:
            query = query.filter(ReconciliationDifference.status == status)

        # 类型过滤
        if difference_type:
            query = query.filter(ReconciliationDifference.difference_type == difference_type)

        # 获取总数
        total = query.count()

        # 分页查询
        differences = query.order_by(ReconciliationDifference.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return differences, total

    def fix_difference(
        self,
        difference_id: int,
        action: str,
        processed_by: str,
        remark: Optional[str] = None
    ) -> ReconciliationDifference:
        """修复差异

        Args:
            difference_id: 差异记录ID
            action: 修复动作 (auto_supplement, manual_supplement, ignore)
            processed_by: 处理人
            remark: 备注

        Returns:
            更新后的差异记录

        Raises:
            RecordNotFoundError: 差异记录不存在
            BusinessException: 差异状态不允许修复
        """
        difference = self.db.query(ReconciliationDifference).filter(
            ReconciliationDifference.id == difference_id
        ).first()

        if not difference:
            raise RecordNotFoundError("差异记录")

        if not difference.is_pending():
            raise BusinessException(
                code=ErrorCode.INVALID_OPERATION,
                message="差异记录状态不允许修复"
            )

        difference.start_processing(processed_by)

        try:
            if action == "auto_supplement":
                result = self._auto_supplement_transaction(difference)
                difference.mark_as_resolved(action, result)
            elif action == "manual_supplement":
                result = self._manual_supplement_transaction(difference)
                difference.mark_as_resolved(action, result)
            elif action == "ignore":
                reason = remark or "手动忽略"
                difference.mark_as_ignored(reason)
            else:
                raise BusinessException(
                    code=ErrorCode.INVALID_PARAMETER,
                    message=f"不支持的修复动作: {action}"
                )

            self.db.commit()
            logger.info(f"差异修复完成: {difference_id}, action={action}")

        except Exception as e:
            logger.error(f"差异修复失败: {difference_id}, error={str(e)}")
            difference.mark_as_failed(str(e))
            self.db.commit()
            raise

        return difference

    def _auto_supplement_transaction(self, difference: ReconciliationDifference) -> str:
        """自动补单

        Args:
            difference: 差异记录

        Returns:
            处理结果描述
        """
        if difference.difference_type == DifferenceType.MISSING_LOCAL:
            # 本地缺失，需要补充本地记录
            return self._supplement_local_payment(difference)
        elif difference.difference_type == DifferenceType.MISSING_REMOTE:
            # 第三方缺失，需要查询第三方状态
            return self._query_remote_status(difference)
        else:
            raise BusinessException(
                code=ErrorCode.INVALID_OPERATION,
                message="该类型差异不支持自动补单"
            )

    def _supplement_local_payment(self, difference: ReconciliationDifference) -> str:
        """补充本地支付记录

        Args:
            difference: 差异记录

        Returns:
            处理结果描述
        """
        try:
            transaction_id = getattr(difference, 'remote_transaction_id', None) or getattr(difference, 'transaction_id', None)
            order_no = getattr(difference, 'local_order_no', None) or getattr(difference, 'order_no', None)

            if not transaction_id or not order_no:
                return f"差异 {difference.id} 缺少 transaction_id 或 order_no，跳过"

            # 查找本地订单
            order = self.db.query(Order).filter(Order.order_no == order_no).first()
            if not order:
                return f"未找到订单 order_no={order_no}"

            # 查找或创建 Payment 记录
            existing_payment = self.db.query(Payment).filter(
                Payment.transaction_id == transaction_id
            ).first()

            if existing_payment:
                existing_payment.status = PaymentStatus.SUCCESS
                existing_payment.paid_at = datetime.utcnow()
                payment = existing_payment
            else:
                payment = Payment(
                    order_id=order.id,
                    transaction_id=transaction_id,
                    amount=order.amount,
                    payment_method=getattr(difference, 'channel', 'unknown'),
                    status=PaymentStatus.SUCCESS,
                    paid_at=datetime.utcnow(),
                )
                self.db.add(payment)

            order.status = OrderStatus.PAID
            difference.status = DifferenceStatus.RESOLVED
            difference.resolved_at = datetime.now().isoformat()
            self.db.commit()

            logger.info(f"补充本地支付记录成功: order_no={order_no}, transaction_id={transaction_id}")
            return f"已补充本地支付记录 (order={order_no})"
        except Exception as e:
            self.db.rollback()
            logger.error(f"补充本地支付记录失败: difference_id={difference.id}, error={e}")
            return f"补充失败: {str(e)[:100]}"

    def _query_remote_status(self, difference: ReconciliationDifference) -> str:
        """查询第三方状态

        Args:
            difference: 差异记录

        Returns:
            处理结果描述
        """
        try:
            transaction_id = getattr(difference, 'remote_transaction_id', None) or getattr(difference, 'transaction_id', None)
            channel = (getattr(difference, 'channel', None) or 'wechat').lower()

            if not transaction_id:
                return f"差异 {difference.id} 缺少 transaction_id"

            from app.services.reconciliation.fetchers import get_fetcher
            try:
                fetcher = get_fetcher(channel)
                status = fetcher.query_transaction(transaction_id)
                logger.info(f"查询第三方状态: transaction_id={transaction_id}, channel={channel}, status={status}")
                return f"已查询 {channel} 状态: {status or 'UNKNOWN'}"
            except ValueError as e:
                logger.warning(f"不支持的 channel={channel}: {e}")
                return f"不支持的 channel: {channel}"
        except Exception as e:
            logger.error(f"查询第三方状态失败: {e}")
            return f"查询失败: {str(e)[:100]}"

    def _manual_supplement_transaction(self, difference: ReconciliationDifference) -> str:
        """手动补单

        Args:
            difference: 差异记录

        Returns:
            处理结果描述
        """
        try:
            order_no = getattr(difference, 'local_order_no', None) or getattr(difference, 'order_no', None)
            transaction_id = getattr(difference, 'remote_transaction_id', None) or getattr(difference, 'transaction_id', None)

            if not order_no:
                return f"差异 {difference.id} 缺少 order_no，无法手动补单"
            if not transaction_id:
                return f"差异 {difference.id} 缺少 transaction_id，无法手动补单"

            order = self.db.query(Order).filter(Order.order_no == order_no).first()
            if not order:
                return f"未找到订单 order_no={order_no}"

            payment = self.db.query(Payment).filter(Payment.transaction_id == transaction_id).first()
            if not payment:
                payment = Payment(
                    order_id=order.id,
                    transaction_id=transaction_id,
                    amount=order.amount,
                    payment_method='manual',
                    status=PaymentStatus.SUCCESS,
                    paid_at=datetime.utcnow(),
                )
                self.db.add(payment)
            else:
                payment.status = PaymentStatus.SUCCESS

            order.status = OrderStatus.PAID
            difference.status = DifferenceStatus.RESOLVED
            difference.resolved_at = datetime.now().isoformat()
            difference.remark = f"manual supplement at {datetime.now().isoformat()}"
            self.db.commit()

            logger.info(f"手动补单成功: difference_id={difference.id}, order_no={order_no}")
            return f"已手动补单 (order={order_no})"
        except Exception as e:
            self.db.rollback()
            logger.error(f"手动补单失败: difference_id={difference.id}, error={e}")
            return f"手动补单失败: {str(e)[:100]}"

    def generate_reconciliation_report(
        self,
        reconciliation_id: int,
        format_type: str = "json"
    ) -> Dict[str, Any]:
        """生成对账报告

        Args:
            reconciliation_id: 对账记录ID
            format_type: 报告格式 (json, excel, pdf)

        Returns:
            对账报告数据

        Raises:
            RecordNotFoundError: 对账记录不存在
        """
        record = self.db.query(ReconciliationRecord).filter(
            ReconciliationRecord.id == reconciliation_id
        ).first()

        if not record:
            raise RecordNotFoundError("对账记录")

        # 获取差异记录
        differences = self.db.query(ReconciliationDifference).filter(
            ReconciliationDifference.reconciliation_id == reconciliation_id
        ).all()

        # 构建报告数据
        # 防御性处理：对账未完成时 count 字段可能为 None
        total_local_count = record.total_local_count or 0
        matched_count = record.matched_count or 0
        report = {
            "reconciliation_info": record.to_dict(),
            "summary": {
                "total_local_count": total_local_count,
                "total_remote_count": record.total_remote_count or 0,
                "matched_count": matched_count,
                "difference_count": record.difference_count or 0,
                "match_rate": round(matched_count / max(total_local_count, 1) * 100, 2),
                "total_local_amount": float(record.total_local_amount or 0),
                "total_remote_amount": float(record.total_remote_amount or 0),
                "matched_amount": float(record.matched_amount or 0),
                "difference_amount": float(record.difference_amount or 0),
            },
            "differences": [diff.to_dict() for diff in differences],
            "difference_statistics": self._calculate_difference_statistics(differences),
            "generated_at": datetime.utcnow().isoformat()
        }

        logger.info(f"生成对账报告: {reconciliation_id}, format={format_type}")
        return report

    def _calculate_difference_statistics(
        self,
        differences: List[ReconciliationDifference]
    ) -> Dict[str, Any]:
        """计算差异统计信息

        Args:
            differences: 差异记录列表

        Returns:
            差异统计信息
        """
        stats = {
            "by_type": {},
            "by_status": {},
            "total_amount_difference": 0
        }

        for diff in differences:
            # 按类型统计
            type_key = diff.difference_type.value
            if type_key not in stats["by_type"]:
                stats["by_type"][type_key] = {"count": 0, "amount": 0}
            stats["by_type"][type_key]["count"] += 1
            if diff.amount_difference:
                stats["by_type"][type_key]["amount"] += float(diff.amount_difference)

            # 按状态统计
            status_key = diff.status.value
            if status_key not in stats["by_status"]:
                stats["by_status"][status_key] = 0
            stats["by_status"][status_key] += 1

            # 总金额差异
            if diff.amount_difference:
                stats["total_amount_difference"] += float(diff.amount_difference)

        return stats

    def get_daily_reconciliation_status(self, target_date: str) -> Optional[ReconciliationRecord]:
        """获取指定日期的对账状态

        Args:
            target_date: 目标日期 (YYYY-MM-DD)

        Returns:
            对账记录，如果不存在则返回None
        """
        return self.db.query(ReconciliationRecord).filter(
            ReconciliationRecord.reconciliation_date == target_date
        ).first()

    def retry_failed_reconciliation(self, reconciliation_id: int) -> ReconciliationRecord:
        """重试失败的对账

        Args:
            reconciliation_id: 对账记录ID

        Returns:
            新的对账记录

        Raises:
            RecordNotFoundError: 对账记录不存在
            BusinessException: 对账状态不允许重试
        """
        original_record = self.db.query(ReconciliationRecord).filter(
            ReconciliationRecord.id == reconciliation_id
        ).first()

        if not original_record:
            raise RecordNotFoundError("对账记录")

        if not original_record.is_failed():
            raise BusinessException(
                code=ErrorCode.INVALID_OPERATION,
                message="只能重试失败的对账记录"
            )

        # 创建重试对账记录
        return self.start_reconciliation(
            reconciliation_date=original_record.reconciliation_date,
            reconciliation_type=ReconciliationType.RETRY,
            force=True
        )