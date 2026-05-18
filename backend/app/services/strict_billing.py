"""
严谨的计费服务
支持预扣费、幂等性、审计等机制
"""
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
import hashlib
import json
from loguru import logger

from ..models.quota import TenantQuota, QuotaUsage
from ..models.billing_transaction import BillingTransaction, BillingStatus
from ..core.database import get_db


class BillingError(Exception):
    """计费错误"""
    pass


class InsufficientQuotaError(BillingError):
    """配额不足"""
    pass


class InsufficientBalanceError(BillingError):
    """余额不足"""
    pass


class StrictBillingService:
    """严谨的计费服务"""

    def __init__(self, db: Session):
        self.db = db

    def generate_idempotency_key(self, enterprise_id: int, request_data: Dict) -> str:
        """生成幂等性key"""
        data_str = json.dumps(request_data, sort_keys=True)
        raw = f"{enterprise_id}:{data_str}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def check_idempotency(self, idempotency_key: str) -> Optional[BillingTransaction]:
        """检查是否重复请求"""
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        return self.db.query(BillingTransaction).filter(
            and_(
                BillingTransaction.idempotency_key == idempotency_key,
                BillingTransaction.created_at > cutoff_time
            )
        ).first()

    def validate_quota(
        self,
        quota: TenantQuota,
        resource_type: str,
        amount: int
    ) -> bool:
        """验证配额是否充足"""
        if resource_type == "token":
            daily_used = self._get_daily_usage(quota.id, "token")
            monthly_used = self._get_monthly_usage(quota.id, "token")

            if quota.daily_tokens != -1 and daily_used + amount > quota.daily_tokens:
                raise InsufficientQuotaError(f"每日Token配额不足: {daily_used}/{quota.daily_tokens}")

            if quota.monthly_tokens != -1 and monthly_used + amount > quota.monthly_tokens:
                raise InsufficientQuotaError(f"每月Token配额不足: {monthly_used}/{quota.monthly_tokens}")

        elif resource_type == "image":
            daily_used = self._get_daily_usage(quota.id, "image")
            monthly_used = self._get_monthly_usage(quota.id, "image")

            if quota.daily_images != -1 and daily_used + amount > quota.daily_images:
                raise InsufficientQuotaError(f"每日图片配额不足: {daily_used}/{quota.daily_images}")

            if quota.monthly_images != -1 and monthly_used + amount > quota.monthly_images:
                raise InsufficientQuotaError(f"每月图片配额不足: {monthly_used}/{quota.monthly_images}")

        elif resource_type == "video_seconds":
            daily_used = self._get_daily_usage(quota.id, "video_seconds")
            monthly_used = self._get_monthly_usage(quota.id, "video_seconds")

            if quota.daily_video_seconds != -1 and daily_used + amount > quota.daily_video_seconds:
                raise InsufficientQuotaError(f"每日视频配额不足: {daily_used}/{quota.daily_video_seconds}秒")

            if quota.monthly_video_seconds != -1 and monthly_used + amount > quota.monthly_video_seconds:
                raise InsufficientQuotaError(f"每月视频配额不足: {monthly_used}/{quota.monthly_video_seconds}秒")

        elif resource_type == "video_frames":
            daily_used = self._get_daily_usage(quota.id, "video_frames")
            monthly_used = self._get_monthly_usage(quota.id, "video_frames")

            if quota.daily_video_frames != -1 and daily_used + amount > quota.daily_video_frames:
                raise InsufficientQuotaError(f"每日视频帧数配额不足: {daily_used}/{quota.daily_video_frames}帧")

            if quota.monthly_video_frames != -1 and monthly_used + amount > quota.monthly_video_frames:
                raise InsufficientQuotaError(f"每月视频帧数配额不足: {monthly_used}/{quota.monthly_video_frames}帧")

        return True

    def calculate_cost(
        self,
        service_type: str,
        params: Dict[str, Any]
    ) -> Decimal:
        """计算成本"""
        if service_type == "jimeng_image":
            resolution = params.get("resolution", "1024x1024")
            pricing = {
                "512x512": Decimal("0.1"),
                "1024x1024": Decimal("0.3"),
                "2048x2048": Decimal("0.8")
            }
            return pricing.get(resolution, Decimal("0.3"))

        elif service_type == "jimeng_video":
            resolution = params.get("resolution", "720p")
            duration = params.get("duration", 5)  # 秒
            pricing_per_second = {
                "720p": Decimal("0.5"),
                "1080p": Decimal("1.0"),
                "4k": Decimal("3.0")
            }
            return pricing_per_second.get(resolution, Decimal("0.5")) * Decimal(duration)

        elif service_type == "jimeng_video_frames":
            # 按帧数计费（参考即梦/字节跳动官方文档）
            resolution = params.get("resolution", "720p_30fps")
            frames = params.get("frames", 150)  # 帧数
            pricing_per_frame = {
                "720p_24fps": Decimal("0.02"),
                "720p_30fps": Decimal("0.017"),
                "1080p_24fps": Decimal("0.04"),
                "1080p_30fps": Decimal("0.033"),
                "4k_24fps": Decimal("0.12"),
                "4k_30fps": Decimal("0.1")
            }
            return pricing_per_frame.get(resolution, Decimal("0.017")) * Decimal(frames)

        elif service_type == "chat":
            input_tokens = params.get("input_tokens", 0)
            output_tokens = params.get("output_tokens", 0)
            provider = params.get("provider", "deepseek")

            pricing = {
                "deepseek": {"input": Decimal("0.0001"), "output": Decimal("0.0002")},
                "openai_gpt4": {"input": Decimal("0.001"), "output": Decimal("0.002")},
                "openai_gpt35": {"input": Decimal("0.0001"), "output": Decimal("0.0002")}
            }

            provider_pricing = pricing.get(provider, pricing["deepseek"])
            return (
                Decimal(input_tokens) * provider_pricing["input"] +
                Decimal(output_tokens) * provider_pricing["output"]
            )

        return Decimal("0")

    def pre_deduct(
        self,
        enterprise_id: int,
        service_type: str,
        params: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ) -> BillingTransaction:
        """预扣费"""
        # 1. 检查幂等性
        if idempotency_key:
            existing = self.check_idempotency(idempotency_key)
            if existing:
                logger.info(f"检测到重复请求: {idempotency_key}")
                return existing

        # 2. 获取配额（行锁防止并发超扣）
        quota = self.db.query(TenantQuota).filter_by(enterprise_id=enterprise_id).with_for_update().first()
        if not quota:
            raise BillingError("未找到企业配额")

        # 3. 计算成本
        cost = self.calculate_cost(service_type, params)

        # 边界条件：费用必须为正数
        if cost <= Decimal("0"):
            raise BillingError(f"计算费用异常，费用必须为正数: {cost}")

        # 4. 验证配额
        if service_type == "chat":
            total_tokens = params.get("input_tokens", 0) + params.get("output_tokens", 0)
            self.validate_quota(quota, "token", total_tokens)

        elif service_type == "jimeng_image":
            resolution = params.get("resolution", "1024x1024")
            quota_cost = {"512x512": 1, "1024x1024": 3, "2048x2048": 8}.get(resolution, 3)
            self.validate_quota(quota, "image", quota_cost)

        elif service_type == "jimeng_video":
            duration = params.get("duration", 5)
            resolution = params.get("resolution", "720p")
            quota_cost_per_sec = {"720p": 1, "1080p": 2, "4k": 5}.get(resolution, 1)
            self.validate_quota(quota, "video_seconds", duration * quota_cost_per_sec)

        elif service_type == "jimeng_video_frames":
            frames = params.get("frames", 150)
            resolution = params.get("resolution", "720p_30fps")
            quota_cost_per_frame = {
                "720p_24fps": 1, "720p_30fps": 1,
                "1080p_24fps": 2, "1080p_30fps": 2,
                "4k_24fps": 5, "4k_30fps": 5
            }.get(resolution, 1)
            self.validate_quota(quota, "video_frames", frames * quota_cost_per_frame)

        # 5. 验证余额
        balance = Decimal(str(quota.balance)) if not isinstance(quota.balance, Decimal) else quota.balance
        if balance < cost:
            raise InsufficientBalanceError(f"余额不足: {balance} < {cost}")

        # 6. 创建预扣费交易
        transaction = BillingTransaction(
            enterprise_id=enterprise_id,
            quota_id=quota.id,
            service_type=service_type,
            amount=cost,
            status=BillingStatus.PENDING,
            idempotency_key=idempotency_key,
            request_params=json.dumps(params),
            created_at=datetime.utcnow()
        )

        # 7. 扣除余额
        quota.balance = balance - cost
        pending = Decimal(str(quota.pending_amount)) if not isinstance(quota.pending_amount, Decimal) else quota.pending_amount
        quota.pending_amount = pending + cost

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)

        logger.info(f"预扣费成功: 企业{enterprise_id}, 金额{cost}, 交易ID{transaction.id}")

        return transaction

    def confirm_transaction(
        self,
        transaction_id: int,
        actual_usage: Optional[Dict[str, Any]] = None
    ) -> BillingTransaction:
        """确认交易（生成成功）"""
        transaction = self.db.query(BillingTransaction).filter_by(id=transaction_id).first()
        if not transaction:
            raise BillingError(f"未找到交易: {transaction_id}")

        if transaction.status != BillingStatus.PENDING:
            logger.warning(f"交易状态异常: {transaction.status}")
            return transaction

        quota = self.db.query(TenantQuota).filter_by(id=transaction.quota_id).with_for_update().first()
        if not quota:
            raise BillingError(f"未找到配额记录: quota_id={transaction.quota_id}, transaction_id={transaction_id}")

        # 更新交易状态
        transaction.status = BillingStatus.COMPLETED
        transaction.completed_at = datetime.utcnow()
        transaction.actual_usage = json.dumps(actual_usage) if actual_usage else None

        # 更新配额
        pending = Decimal(str(quota.pending_amount)) if not isinstance(quota.pending_amount, Decimal) else quota.pending_amount
        tx_amount = Decimal(str(transaction.amount)) if not isinstance(transaction.amount, Decimal) else transaction.amount
        quota.pending_amount = pending - tx_amount

        # 计算实际资源使用量（用于配额追踪，单位与 validate_quota 一致）
        request_params = json.loads(transaction.request_params) if transaction.request_params else {}
        actual_params = actual_usage or request_params
        if transaction.service_type == "chat":
            usage_count = (
                actual_params.get("input_tokens", 0) + actual_params.get("output_tokens", 0)
            )
        elif transaction.service_type == "jimeng_image":
            resolution = actual_params.get("resolution", "1024x1024")
            usage_count = {"512x512": 1, "1024x1024": 3, "2048x2048": 8}.get(resolution, 3)
        elif transaction.service_type == "jimeng_video":
            duration = actual_params.get("duration", 5)
            resolution = actual_params.get("resolution", "720p")
            quota_cost_per_sec = {"720p": 1, "1080p": 2, "4k": 5}.get(resolution, 1)
            usage_count = duration * quota_cost_per_sec
        elif transaction.service_type == "jimeng_video_frames":
            frames = actual_params.get("frames", 150)
            resolution = actual_params.get("resolution", "720p_30fps")
            quota_cost_per_frame = {
                "720p_24fps": 1, "720p_30fps": 1,
                "1080p_24fps": 2, "1080p_30fps": 2,
                "4k_24fps": 5, "4k_30fps": 5,
            }.get(resolution, 1)
            usage_count = frames * quota_cost_per_frame
        else:
            usage_count = 0

        # 记录配额使用（amount 存储实际资源用量，与 validate_quota 的单位一致）
        usage = QuotaUsage(
            quota_id=quota.id,
            amount=usage_count,
            operation=transaction.service_type,
            usage_metadata=transaction.actual_usage,
            used_at=datetime.utcnow()
        )

        self.db.add(usage)
        self.db.commit()

        logger.info(f"交易确认成功: 交易ID{transaction_id}")

        return transaction

    def refund_transaction(
        self,
        transaction_id: int,
        reason: str,
        refund_percentage: int = 100
    ) -> BillingTransaction:
        """退款（生成失败）"""
        transaction = self.db.query(BillingTransaction).filter_by(id=transaction_id).first()
        if not transaction:
            raise BillingError(f"未找到交易: {transaction_id}")

        if transaction.status != BillingStatus.PENDING:
            logger.warning(f"交易状态异常: {transaction.status}")
            return transaction

        quota = self.db.query(TenantQuota).filter_by(id=transaction.quota_id).with_for_update().first()
        if not quota:
            raise BillingError(f"未找到配额记录: quota_id={transaction.quota_id}, transaction_id={transaction_id}")
        tx_amount = Decimal(str(transaction.amount)) if not isinstance(transaction.amount, Decimal) else transaction.amount
        refund_amount = tx_amount * Decimal(refund_percentage) / Decimal(100)

        # 更新交易状态
        transaction.status = BillingStatus.REFUNDED
        transaction.refunded_at = datetime.utcnow()
        transaction.refund_amount = refund_amount
        transaction.refund_reason = reason

        # 退款到余额
        balance = Decimal(str(quota.balance)) if not isinstance(quota.balance, Decimal) else quota.balance
        pending = Decimal(str(quota.pending_amount)) if not isinstance(quota.pending_amount, Decimal) else quota.pending_amount
        quota.balance = balance + refund_amount
        quota.pending_amount = pending - tx_amount

        self.db.commit()

        logger.info(f"交易退款成功: 交易ID{transaction_id}, 退款{refund_amount}")

        return transaction

    def _get_daily_usage(self, quota_id: int, resource_type: str) -> int:
        """获取今日使用量"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = self.db.query(QuotaUsage).filter(
            and_(
                QuotaUsage.quota_id == quota_id,
                QuotaUsage.operation.like(f"%{resource_type}%"),
                QuotaUsage.used_at >= today_start
            )
        ).all()
        return sum(u.amount or 0 for u in result)

    def _get_monthly_usage(self, quota_id: int, resource_type: str) -> int:
        """获取本月使用量"""
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        result = self.db.query(QuotaUsage).filter(
            and_(
                QuotaUsage.quota_id == quota_id,
                QuotaUsage.operation.like(f"%{resource_type}%"),
                QuotaUsage.used_at >= month_start
            )
        ).all()
        return sum(u.amount or 0 for u in result)
