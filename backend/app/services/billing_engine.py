"""
计费规则引擎服务

提供灵活的计费功能：
- 支持多种计费模式（Token、消息、API调用、包月、阶梯定价）
- 自动计算费用
- 生成账单
- 账单统计分析

版本: 1.0
更新日期: 2026-01-22
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from loguru import logger

from app.models.billing import BillingPlan, BillingRecord, Invoice, BillingMode, InvoiceStatus, PaymentMethod
from app.models.user import User


class BillingEngine:
    """计费引擎

    核心功能：
    1. 记录使用量并计费
    2. 生成账单
    3. 统计分析
    """

    def __init__(self, db: Session):
        """初始化计费引擎

        参数:
            db: 数据库会话
        """
        self.db = db

    def get_user_plan(self, user_id: int) -> Optional[BillingPlan]:
        """获取用户的计费方案

        参数:
            user_id: 用户ID

        返回:
            BillingPlan: 计费方案，如果没有则返回默认方案
        """
        # TODO: 实现用户与计费方案的关联逻辑
        # 目前返回默认方案
        return self.db.query(BillingPlan).filter(BillingPlan.is_default == True, BillingPlan.is_active == True).first()

    def record_usage(
        self,
        user_id: int,
        billing_mode: BillingMode,
        usage_data: Dict[str, Any],
        resource_type: str = None,
        resource_id: int = None,
        notes: str = None,
    ) -> BillingRecord:
        """记录使用量并计费

        参数:
            user_id: 用户ID
            billing_mode: 计费模式
            usage_data: 使用量数据，如 {"tokens": 1000} 或 {"messages": 5}
            resource_type: 资源类型
            resource_id: 资源ID
            notes: 备注

        返回:
            BillingRecord: 计费记录
        """
        # 获取用户的计费方案
        plan = self.get_user_plan(user_id)
        if not plan:
            raise ValueError(f"No billing plan found for user {user_id}")

        # 计算费用
        amount = plan.calculate_cost(usage_data)

        # 确定数量和单价
        quantity = self._extract_quantity(billing_mode, usage_data)
        unit_price = self._calculate_unit_price(plan, quantity)

        # 获取当前日期
        today = date.today()
        billing_month = today.strftime("%Y-%m")

        # 创建计费记录（带事务保护）
        record = BillingRecord(
            user_id=user_id,
            plan_id=plan.id,
            billing_mode=billing_mode,
            usage_data=usage_data,
            unit_price=Decimal(str(unit_price)),
            quantity=quantity,
            amount=Decimal(str(amount)),
            currency=plan.pricing_rules.get("currency", "CNY"),
            resource_type=resource_type,
            resource_id=resource_id,
            billing_date=today,
            billing_month=billing_month,
            notes=notes,
        )

        try:
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"计费记录写入失败: {e}")

        return record

    def _extract_quantity(self, billing_mode: BillingMode, usage_data: Dict[str, Any]) -> int:
        """从使用量数据中提取数量

        参数:
            billing_mode: 计费模式
            usage_data: 使用量数据

        返回:
            int: 数量（必为正整数）

        抛出:
            ValueError: 当数量为负数时
        """
        quantity = 0

        if billing_mode == BillingMode.TOKEN:
            quantity = usage_data.get("tokens", 0)
        elif billing_mode == BillingMode.MESSAGE:
            quantity = usage_data.get("messages", 0)
        elif billing_mode == BillingMode.API_CALL:
            quantity = usage_data.get("api_calls", 0)
        elif billing_mode == BillingMode.MONTHLY:
            quantity = 1
        elif billing_mode == BillingMode.TIERED:
            # 取第一个非零值（优先级：tokens > messages > api_calls）
            quantity = usage_data.get("tokens", 0)
            if quantity <= 0:
                quantity = usage_data.get("messages", 0)
            if quantity <= 0:
                quantity = usage_data.get("api_calls", 0)

        # 验证数量必须为非负整数
        if quantity < 0:
            raise ValueError(f"Invalid quantity: {quantity}, must be non-negative")

        return int(quantity)

    def _calculate_unit_price(self, plan: BillingPlan, quantity: int) -> float:
        """计算单价

        参数:
            plan: 计费方案
            quantity: 数量

        返回:
            float: 单价
        """
        if plan.billing_mode == BillingMode.TIERED:
            # 阶梯定价，返回平均单价
            tiers = plan.pricing_rules.get("tiers", [])
            for tier in sorted(tiers, key=lambda x: x["min"]):
                if tier["min"] <= quantity:
                    if tier.get("max") is None or quantity <= tier["max"]:
                        return tier["unit_price"]
            return 0.0
        else:
            return plan.pricing_rules.get("unit_price", 0) or plan.pricing_rules.get("monthly_fee", 0)

    def generate_invoice(self, user_id: int, period_start: date, period_end: date, due_days: int = 7) -> Invoice:
        """生成账单

        参数:
            user_id: 用户ID
            period_start: 账单周期开始日期
            period_end: 账单周期结束日期
            due_days: 到期天数，默认7天

        返回:
            Invoice: 账单
        """
        # 查询该周期内未关联账单的计费记录
        records = (
            self.db.query(BillingRecord)
            .filter(
                BillingRecord.user_id == user_id,
                BillingRecord.billing_date >= period_start,
                BillingRecord.billing_date <= period_end,
                BillingRecord.invoice_id == None,
            )
            .all()
        )

        if not records:
            raise ValueError(f"No billing records found for user {user_id} in period {period_start} to {period_end}")

        # 生成账单编号
        invoice_number = Invoice.generate_invoice_number(user_id, period_start)

        # 计算到期日期
        due_date = date.today() + timedelta(days=due_days)

        # 创建账单
        invoice = Invoice(
            invoice_number=invoice_number,
            user_id=user_id,
            billing_period_start=period_start,
            billing_period_end=period_end,
            due_date=due_date,
            status=InvoiceStatus.PENDING,
        )

        self.db.add(invoice)
        self.db.flush()  # 获取invoice.id

        # 关联计费记录到账单
        for record in records:
            record.invoice_id = invoice.id

        # 计算账单总额
        invoice.calculate_totals()

        # 生成使用量汇总
        invoice.usage_summary = self._generate_usage_summary(records)

        # 单次提交保证原子性：invoice和所有records关联同时成功或同时失败
        self.db.commit()
        self.db.refresh(invoice)

        return invoice

    def _generate_usage_summary(self, records: List[BillingRecord]) -> Dict[str, Any]:
        """生成使用量汇总

        参数:
            records: 计费记录列表

        返回:
            Dict: 使用量汇总
        """
        summary = {"total_tokens": 0, "total_messages": 0, "total_api_calls": 0, "by_mode": {}}

        for record in records:
            # 统计总量
            usage_data = record.usage_data or {}
            summary["total_tokens"] += usage_data.get("tokens", 0)
            summary["total_messages"] += usage_data.get("messages", 0)
            summary["total_api_calls"] += usage_data.get("api_calls", 0)

            # 按计费模式统计（保留Decimal精度）
            mode = record.billing_mode.value
            if mode not in summary["by_mode"]:
                summary["by_mode"][mode] = {"quantity": 0, "amount": Decimal("0.00")}

            summary["by_mode"][mode]["quantity"] += record.quantity
            summary["by_mode"][mode]["amount"] += record.amount

        # 转换Decimal为float以支持JSON序列化
        for mode in summary["by_mode"]:
            summary["by_mode"][mode]["amount"] = float(summary["by_mode"][mode]["amount"])

        return summary

    def pay_invoice(self, invoice_id: int, payment_method: PaymentMethod, transaction_id: str = None) -> Invoice:
        """支付账单

        参数:
            invoice_id: 账单ID
            payment_method: 支付方式
            transaction_id: 交易ID

        返回:
            Invoice: 更新后的账单
        """
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        if invoice.status == InvoiceStatus.PAID:
            raise ValueError(f"Invoice {invoice_id} is already paid")

        invoice.mark_as_paid(payment_method, transaction_id)
        self.db.commit()
        self.db.refresh(invoice)

        return invoice

    def get_user_billing_records(
        self,
        user_id: int,
        start_date: date = None,
        end_date: date = None,
        billing_mode: BillingMode = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[BillingRecord], int]:
        """获取用户的计费记录

        参数:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            billing_mode: 计费模式
            limit: 每页数量
            offset: 偏移量

        返回:
            Tuple[List[BillingRecord], int]: (记录列表, 总数)
        """
        query = self.db.query(BillingRecord).filter(BillingRecord.user_id == user_id)

        if start_date:
            query = query.filter(BillingRecord.billing_date >= start_date)
        if end_date:
            query = query.filter(BillingRecord.billing_date <= end_date)
        if billing_mode:
            query = query.filter(BillingRecord.billing_mode == billing_mode)

        total = query.count()
        records = query.order_by(BillingRecord.created_at.desc()).limit(limit).offset(offset).all()

        return records, total

    def get_user_invoices(
        self, user_id: int, status: InvoiceStatus = None, limit: int = 100, offset: int = 0
    ) -> Tuple[List[Invoice], int]:
        """获取用户的账单

        参数:
            user_id: 用户ID
            status: 账单状态
            limit: 每页数量
            offset: 偏移量

        返回:
            Tuple[List[Invoice], int]: (账单列表, 总数)
        """
        query = self.db.query(Invoice).filter(Invoice.user_id == user_id)

        if status:
            query = query.filter(Invoice.status == status)

        total = query.count()
        invoices = query.order_by(Invoice.created_at.desc()).limit(limit).offset(offset).all()

        return invoices, total

    def get_billing_statistics(self, user_id: int, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """获取计费统计信息

        参数:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期

        返回:
            Dict: 统计信息
        """
        query = self.db.query(BillingRecord).filter(BillingRecord.user_id == user_id)

        if start_date:
            query = query.filter(BillingRecord.billing_date >= start_date)
        if end_date:
            query = query.filter(BillingRecord.billing_date <= end_date)

        records = query.all()

        # 统计总费用
        total_amount = sum(float(record.amount) for record in records)

        # 按计费模式统计
        by_mode = {}
        for record in records:
            mode = record.billing_mode.value
            if mode not in by_mode:
                by_mode[mode] = {"count": 0, "quantity": 0, "amount": 0.0}

            by_mode[mode]["count"] += 1
            by_mode[mode]["quantity"] += record.quantity
            by_mode[mode]["amount"] += float(record.amount)

        # 按日期统计
        by_date = {}
        for record in records:
            date_str = record.billing_date.isoformat()
            if date_str not in by_date:
                by_date[date_str] = {"count": 0, "amount": 0.0}

            by_date[date_str]["count"] += 1
            by_date[date_str]["amount"] += float(record.amount)

        # 按月份统计
        by_month = {}
        for record in records:
            month = record.billing_month
            if month not in by_month:
                by_month[month] = {"count": 0, "amount": 0.0}

            by_month[month]["count"] += 1
            by_month[month]["amount"] += float(record.amount)

        return {
            "total_records": len(records),
            "total_amount": total_amount,
            "by_mode": by_mode,
            "by_date": by_date,
            "by_month": by_month,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        }

    def auto_generate_monthly_invoices(self, target_month: date = None) -> List[Invoice]:
        """自动生成月度账单

        为所有有计费记录的用户生成上月账单

        参数:
            target_month: 目标月份（默认为上个月）

        返回:
            List[Invoice]: 生成的账单列表
        """
        if target_month is None:
            # 默认为上个月
            today = date.today()
            if today.month == 1:
                target_month = date(today.year - 1, 12, 1)
            else:
                target_month = date(today.year, today.month - 1, 1)

        # 计算账单周期
        period_start = target_month
        if target_month.month == 12:
            period_end = date(target_month.year + 1, 1, 1) - timedelta(days=1)
        else:
            period_end = date(target_month.year, target_month.month + 1, 1) - timedelta(days=1)

        # 查询该月有计费记录但未生成账单的用户
        user_ids = (
            self.db.query(BillingRecord.user_id)
            .filter(
                BillingRecord.billing_date >= period_start,
                BillingRecord.billing_date <= period_end,
                BillingRecord.invoice_id == None,
            )
            .distinct()
            .all()
        )

        invoices = []
        for (user_id,) in user_ids:
            try:
                invoice = self.generate_invoice(user_id, period_start, period_end)
                invoices.append(invoice)
            except Exception as e:
                logger.warning(f"Failed to generate invoice for user {user_id}: {e}")
                continue

        return invoices

    def check_overdue_invoices(self) -> List[Invoice]:
        """检查并更新逾期账单

        返回:
            List[Invoice]: 逾期账单列表
        """
        today = date.today()

        # 查询逾期的待支付账单
        overdue_invoices = (
            self.db.query(Invoice).filter(Invoice.status == InvoiceStatus.PENDING, Invoice.due_date < today).all()
        )

        # 更新状态为逾期
        for invoice in overdue_invoices:
            invoice.status = InvoiceStatus.OVERDUE

        if overdue_invoices:
            self.db.commit()

        return overdue_invoices


class BillingPlanManager:
    """计费方案管理器

    用于管理计费方案的CRUD操作
    """

    def __init__(self, db: Session):
        """初始化管理器

        参数:
            db: 数据库会话
        """
        self.db = db

    def create_plan(self, plan_data: Dict[str, Any]) -> BillingPlan:
        """创建计费方案

        参数:
            plan_data: 方案数据

        返回:
            BillingPlan: 创建的方案
        """
        plan = BillingPlan(**plan_data)
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def get_plan(self, plan_id: int) -> Optional[BillingPlan]:
        """获取计费方案

        参数:
            plan_id: 方案ID

        返回:
            BillingPlan: 方案
        """
        return self.db.query(BillingPlan).filter(BillingPlan.id == plan_id).first()

    def get_plans(
        self, is_active: bool = None, billing_mode: BillingMode = None, applicable_to: str = None
    ) -> List[BillingPlan]:
        """获取计费方案列表

        参数:
            is_active: 是否启用
            billing_mode: 计费模式
            applicable_to: 适用对象

        返回:
            List[BillingPlan]: 方案列表
        """
        query = self.db.query(BillingPlan)

        if is_active is not None:
            query = query.filter(BillingPlan.is_active == is_active)
        if billing_mode:
            query = query.filter(BillingPlan.billing_mode == billing_mode)
        if applicable_to:
            query = query.filter(or_(BillingPlan.applicable_to == applicable_to, BillingPlan.applicable_to == "all"))

        return query.order_by(BillingPlan.sort_order, BillingPlan.created_at).all()

    def update_plan(self, plan_id: int, plan_data: Dict[str, Any]) -> BillingPlan:
        """更新计费方案

        参数:
            plan_id: 方案ID
            plan_data: 更新数据

        返回:
            BillingPlan: 更新后的方案
        """
        plan = self.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        for key, value in plan_data.items():
            if hasattr(plan, key):
                setattr(plan, key, value)

        self.db.commit()
        self.db.refresh(plan)
        return plan

    def delete_plan(self, plan_id: int) -> bool:
        """删除计费方案（软删除）

        参数:
            plan_id: 方案ID

        返回:
            bool: 是否成功
        """
        plan = self.get_plan(plan_id)
        if not plan:
            return False

        plan.deleted_at = datetime.utcnow()
        self.db.commit()
        return True

    def set_default_plan(self, plan_id: int) -> BillingPlan:
        """设置默认方案

        参数:
            plan_id: 方案ID

        返回:
            BillingPlan: 设置后的方案
        """
        # 取消其他默认方案
        self.db.query(BillingPlan).filter(BillingPlan.is_default == True).update({"is_default": False})

        # 设置新的默认方案
        plan = self.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        plan.is_default = True
        self.db.commit()
        self.db.refresh(plan)
        return plan
