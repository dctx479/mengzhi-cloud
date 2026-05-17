"""
使用统计服务
客户端按次计费，后台完整统计
"""
from typing import Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from loguru import logger

from ..models.usage_stats import UsageStatistics, StatType
from ..models.billing_transaction import BillingTransaction


class UsageStatsService:
    """使用统计服务"""

    def __init__(self, db: Session):
        self.db = db

    def record_chat_usage(
        self,
        enterprise_id: int,
        user_id: int,
        model: str,
        input_tokens: int,
        output_tokens: int,
        client_charge: Decimal,
        backend_cost: Decimal
    ):
        """
        记录对话使用

        客户端：按次计费（¥0.1/次）
        后台：统计Token和成本
        """
        stat = UsageStatistics(
            enterprise_id=enterprise_id,
            user_id=user_id,
            stat_type=StatType.CHAT,
            model=model,

            # 客户端计费
            request_count=1,
            client_charge=client_charge,  # ¥0.1

            # 后台统计
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            backend_cost=backend_cost,

            # 利润（防止除零）
            profit=client_charge - backend_cost,
            profit_margin=float((client_charge - backend_cost) / client_charge * 100) if client_charge else 0.0,

            created_at=datetime.utcnow()
        )

        try:
            self.db.add(stat)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return stat

    def record_image_usage(
        self,
        enterprise_id: int,
        user_id: int,
        resolution: str,
        client_charge: Decimal,
        backend_cost: Decimal
    ):
        """
        记录图片生成使用

        客户端：按次计费（¥0.5/次）
        后台：统计实际成本
        """
        stat = UsageStatistics(
            enterprise_id=enterprise_id,
            user_id=user_id,
            stat_type=StatType.IMAGE,
            resolution=resolution,

            request_count=1,
            client_charge=client_charge,  # ¥0.5
            backend_cost=backend_cost,

            profit=client_charge - backend_cost,
            profit_margin=float((client_charge - backend_cost) / client_charge * 100) if client_charge else 0.0,

            created_at=datetime.utcnow()
        )

        try:
            self.db.add(stat)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return stat

    def record_video_usage(
        self,
        enterprise_id: int,
        user_id: int,
        resolution: str,
        duration: int,
        client_charge: Decimal,
        backend_cost: Decimal
    ):
        """
        记录视频生成使用

        客户端：按次计费（¥2.0/次）
        后台：统计实际成本（按秒）
        """
        stat = UsageStatistics(
            enterprise_id=enterprise_id,
            user_id=user_id,
            stat_type=StatType.VIDEO,
            resolution=resolution,
            duration=duration,

            request_count=1,
            client_charge=client_charge,  # ¥2.0
            backend_cost=backend_cost,

            profit=client_charge - backend_cost,
            profit_margin=float((client_charge - backend_cost) / client_charge * 100) if client_charge else 0.0,

            created_at=datetime.utcnow()
        )

        try:
            self.db.add(stat)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return stat

    def get_daily_stats(self, enterprise_id: int, date: datetime = None):
        """获取每日统计"""
        if date is None:
            date = datetime.utcnow()

        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = date.replace(hour=23, minute=59, second=59, microsecond=999999)

        stats = self.db.query(
            func.count(UsageStatistics.id).label('total_requests'),
            func.sum(UsageStatistics.client_charge).label('total_revenue'),
            func.sum(UsageStatistics.backend_cost).label('total_cost'),
            func.sum(UsageStatistics.profit).label('total_profit'),
            func.sum(UsageStatistics.input_tokens).label('total_input_tokens'),
            func.sum(UsageStatistics.output_tokens).label('total_output_tokens')
        ).filter(
            and_(
                UsageStatistics.enterprise_id == enterprise_id,
                UsageStatistics.created_at >= start,
                UsageStatistics.created_at <= end
            )
        ).first()

        return {
            'total_requests': stats.total_requests or 0,
            'total_revenue': float(stats.total_revenue or 0),
            'total_cost': float(stats.total_cost or 0),
            'total_profit': float(stats.total_profit or 0),
            'profit_margin': float(stats.total_profit / stats.total_revenue * 100) if stats.total_revenue else 0,
            'total_input_tokens': stats.total_input_tokens or 0,
            'total_output_tokens': stats.total_output_tokens or 0
        }

    def get_model_distribution(self, enterprise_id: int, days: int = 30):
        """获取模型使用分布"""
        start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start = start - timedelta(days=days)

        stats = self.db.query(
            UsageStatistics.model,
            func.count(UsageStatistics.id).label('count'),
            func.sum(UsageStatistics.backend_cost).label('cost')
        ).filter(
            and_(
                UsageStatistics.enterprise_id == enterprise_id,
                UsageStatistics.created_at >= start,
                UsageStatistics.stat_type == StatType.CHAT
            )
        ).group_by(UsageStatistics.model).all()

        return [
            {
                'model': s.model,
                'count': s.count,
                'cost': float(s.cost or 0)
            }
            for s in stats
        ]

    def check_profit_margin(self, enterprise_id: int):
        """检查利润率"""
        stats = self.get_daily_stats(enterprise_id)

        if stats['profit_margin'] < 15:
            # 利润率过低，发送告警
            logger.warning(f"企业{enterprise_id}利润率过低: {stats['profit_margin']}%")
            return False

        return True
