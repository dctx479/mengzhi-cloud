"""
配额套餐服务层

版本: 1.0
创建日期: 2026-01-23
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from loguru import logger

from app.models.quota_package import QuotaPackage
from app.core.errors import BusinessException, ErrorCode, RecordNotFoundError


class QuotaPackageService:
    """配额套餐服务类

    提供配额套餐相关的业务逻辑操作
    """

    def __init__(self, db: Session) -> None:
        """初始化服务

        Args:
            db: SQLAlchemy数据库会话
        """
        self.db = db

    def list_packages(
        self,
        is_active: Optional[bool] = None,
        package_type: Optional[str] = None,
        period: Optional[str] = None
    ) -> List[QuotaPackage]:
        """获取套餐列表

        Args:
            is_active: 是否启用
            package_type: 套餐类型
            period: 套餐周期

        Returns:
            套餐列表
        """
        try:
            query = self.db.query(QuotaPackage)

            # 应用筛选条件
            if is_active is not None:
                query = query.filter(QuotaPackage.is_active == is_active)

            if package_type:
                query = query.filter(QuotaPackage.package_type == package_type)

            if period:
                query = query.filter(QuotaPackage.period == period)

            # 按排序顺序和创建时间排序
            packages = query.order_by(
                asc(QuotaPackage.sort_order),
                desc(QuotaPackage.created_at)
            ).all()

            logger.info(f"获取套餐列表成功: count={len(packages)}")
            return packages

        except Exception as e:
            logger.error(f"获取套餐列表失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.DB_QUERY_FAILED,
                message="获取套餐列表失败"
            )

    def get_package_by_id(self, package_id: int) -> QuotaPackage:
        """根据ID获取套餐

        Args:
            package_id: 套餐ID

        Returns:
            套餐对象

        Raises:
            RecordNotFoundError: 套餐不存在
        """
        package = self.db.query(QuotaPackage).filter(
            QuotaPackage.id == package_id
        ).first()

        if not package:
            logger.warning(f"套餐不存在: {package_id}")
            raise RecordNotFoundError("套餐")

        return package

    def get_active_packages(self) -> List[QuotaPackage]:
        """获取所有启用的套餐

        Returns:
            启用的套餐列表
        """
        return self.list_packages(is_active=True)

    def get_recommended_package(self) -> Optional[QuotaPackage]:
        """获取推荐套餐

        Returns:
            推荐套餐或None
        """
        try:
            package = self.db.query(QuotaPackage).filter(
                QuotaPackage.is_active == True,
                QuotaPackage.is_recommended == True
            ).order_by(asc(QuotaPackage.sort_order)).first()

            return package

        except Exception as e:
            logger.error(f"获取推荐套餐失败: {str(e)}")
            return None
