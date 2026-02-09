"""
数据库查询工具 - BUG-019修复

提供安全的数据库查询方法，避免SQL注入风险

版本: 1.0
更新日期: 2026-01-17
"""

from typing import Any, Dict, List, Optional, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy import text, select
from sqlalchemy.sql import Select
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SafeQueryBuilder:
    """安全的SQL查询构建器"""

    def __init__(self, db: Session) -> None:
        """
        初始化查询构建器

        Args:
            db: SQLAlchemy Session对象
        """
        self.db = db

    def execute_safe_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        执行参数化查询，防止SQL注入

        Args:
            query: SQL查询字符串，使用:param_name形式的参数占位符
            params: 参数字典，如 {"user_id": 123}

        Returns:
            查询结果

        Example:
            >>> builder = SafeQueryBuilder(db)
            >>> result = builder.execute_safe_query(
            ...     "SELECT * FROM users WHERE id = :user_id",
            ...     {"user_id": 123}
            ... )
        """
        if not params:
            params = {}

        try:
            stmt = text(query)
            result = self.db.execute(stmt, params)
            return result
        except Exception as e:
            logger.error(f"查询执行失败: {str(e)}")
            raise

    def execute_select_safe(
        self,
        select_stmt: Select[T]
    ) -> List[T]:
        """
        执行SQLAlchemy select查询（推荐方式）

        Args:
            select_stmt: SQLAlchemy select对象

        Returns:
            查询结果列表

        Example:
            >>> from sqlalchemy import select
            >>> from app.models.user import User
            >>> builder = SafeQueryBuilder(db)
            >>> stmt = select(User).where(User.id == 123)
            >>> users = builder.execute_select_safe(stmt)
        """
        try:
            result = self.db.execute(select_stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"查询执行失败: {str(e)}")
            raise

    def execute_insert_safe(
        self,
        table_name: str,
        data: Dict[str, Any]
    ) -> int:
        """
        安全的插入操作

        Args:
            table_name: 表名
            data: 要插入的数据字典

        Returns:
            影响的行数
        """
        # 直接使用SQLAlchemy ORM的add和commit更安全
        # 此方法仅用于文本SQL的补充
        raise NotImplementedError("请使用SQLAlchemy ORM的add方法进行插入")

    def execute_update_safe(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        安全的更新操作

        Args:
            query: UPDATE SQL语句
            params: 参数字典

        Returns:
            影响的行数

        Example:
            >>> builder = SafeQueryBuilder(db)
            >>> affected = builder.execute_update_safe(
            ...     "UPDATE users SET status = :status WHERE id = :user_id",
            ...     {"status": "active", "user_id": 123}
            ... )
        """
        if not params:
            params = {}

        try:
            stmt = text(query)
            result = self.db.execute(stmt, params)
            self.db.commit()
            return result.rowcount
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新失败: {str(e)}")
            raise

    def execute_delete_safe(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        安全的删除操作

        Args:
            query: DELETE SQL语句
            params: 参数字典

        Returns:
            影响的行数

        Example:
            >>> builder = SafeQueryBuilder(db)
            >>> affected = builder.execute_delete_safe(
            ...     "DELETE FROM users WHERE id = :user_id",
            ...     {"user_id": 123}
            ... )
        """
        if not params:
            params = {}

        try:
            stmt = text(query)
            result = self.db.execute(stmt, params)
            self.db.commit()
            return result.rowcount
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除失败: {str(e)}")
            raise


class QueryHelper:
    """查询辅助函数"""

    @staticmethod
    def build_like_pattern(keyword: str) -> str:
        """
        构建LIKE模式，避免SQL注入

        Args:
            keyword: 搜索关键词

        Returns:
            LIKE模式字符串

        Note:
            This escapes special characters used in LIKE clauses
        """
        # 转义特殊字符
        escaped = keyword.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        return f"%{escaped}%"

    @staticmethod
    def validate_sort_field(field: str, allowed_fields: List[str]) -> str:
        """
        验证排序字段，防止注入

        Args:
            field: 要排序的字段
            allowed_fields: 允许的字段列表

        Returns:
            验证后的字段名

        Raises:
            ValueError: 字段不在允许列表中
        """
        if field not in allowed_fields:
            raise ValueError(f"不支持按 {field} 排序")
        return field

    @staticmethod
    def validate_sort_order(order: str) -> str:
        """
        验证排序顺序

        Args:
            order: 排序顺序（asc或desc）

        Returns:
            验证后的排序顺序

        Raises:
            ValueError: 排序顺序无效
        """
        if order.lower() not in ('asc', 'desc'):
            raise ValueError(f"排序顺序必须是 asc 或 desc，而不是 {order}")
        return order.lower()


__all__ = ['SafeQueryBuilder', 'QueryHelper']
