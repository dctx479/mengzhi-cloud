"""
租户数据库路由器

版本: 1.0
更新日期: 2026-01-22

功能：
- 根据租户ID路由到对应数据库
- 动态创建和管理数据库连接
- 连接池管理和优化
- 自动创建租户数据库
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging
import threading

from app.core.config import settings
from app.models.base import Base

logger = logging.getLogger(__name__)


class TenantDatabaseRouter:
    """租户数据库路由器

    管理多个租户数据库的连接和路由
    """

    def __init__(self):
        """初始化路由器"""
        self._engines: Dict[str, any] = {}  # 数据库引擎缓存
        self._session_factories: Dict[str, sessionmaker] = {}  # 会话工厂缓存
        self._last_used: Dict[str, datetime] = {}  # 最后使用时间
        self._cleanup_interval = timedelta(hours=1)  # 清理间隔
        # BUG FIX #2: Add thread lock to prevent race conditions during database creation
        self._creation_lock = threading.Lock()
        self._max_idle_time = timedelta(hours=2)  # 最大空闲时间

    def get_database_url(self, tenant_id: int) -> str:
        """
        获取租户数据库URL

        参数:
            tenant_id: 租户ID

        返回:
            str: 数据库连接URL
        """
        database_name = f"{settings.TENANT_DB_PREFIX}{tenant_id}"
        return (
            f"mysql+pymysql://{settings.TENANT_DB_USER}:{settings.TENANT_DB_PASSWORD}"
            f"@{settings.TENANT_DB_HOST}:{settings.TENANT_DB_PORT}"
            f"/{database_name}?charset=utf8mb4"
        )

    def get_engine(self, tenant_id: int, create_if_not_exists: bool = True):
        """
        获取租户数据库引擎（线程安全）

        参数:
            tenant_id: 租户ID
            create_if_not_exists: 如果数据库不存在是否创建

        返回:
            Engine: SQLAlchemy引擎
        """
        cache_key = f"tenant_{tenant_id}"

        # 快速路径：无锁读取缓存（已存在则直接返回）
        if cache_key in self._engines:
            self._last_used[cache_key] = datetime.now()
            return self._engines[cache_key]

        # 慢路径：加锁创建引擎，防止多线程重复创建
        with self._creation_lock:
            # Double-check: 另一个线程可能已经创建
            if cache_key in self._engines:
                self._last_used[cache_key] = datetime.now()
                return self._engines[cache_key]

            database_url = self.get_database_url(tenant_id)

            try:
                engine = create_engine(
                    database_url,
                    echo=settings.DEBUG,
                    pool_size=settings.TENANT_DB_POOL_SIZE,
                    max_overflow=settings.TENANT_DB_MAX_OVERFLOW,
                    pool_timeout=settings.TENANT_DB_POOL_TIMEOUT,
                    pool_recycle=settings.TENANT_DB_POOL_RECYCLE,
                    pool_pre_ping=True,
                    poolclass=QueuePool
                )

                # 测试连接
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))

                # 写入缓存（在锁内，线程安全）
                self._engines[cache_key] = engine
                self._last_used[cache_key] = datetime.now()

                logger.info(f"Created database engine for tenant {tenant_id}")
                return engine

            except Exception as e:
                if create_if_not_exists and "Unknown database" in str(e):
                    logger.info(f"Database for tenant {tenant_id} not found, creating...")
                    self._create_tenant_database(tenant_id)
                    # 递归调用时 create_if_not_exists=False 避免无限循环
                    # 此时已在锁内，需要直接创建引擎而非递归（避免死锁）
                    database_url2 = self.get_database_url(tenant_id)
                    engine2 = create_engine(
                        database_url2,
                        echo=settings.DEBUG,
                        pool_size=settings.TENANT_DB_POOL_SIZE,
                        max_overflow=settings.TENANT_DB_MAX_OVERFLOW,
                        pool_timeout=settings.TENANT_DB_POOL_TIMEOUT,
                        pool_recycle=settings.TENANT_DB_POOL_RECYCLE,
                        pool_pre_ping=True,
                        poolclass=QueuePool
                    )
                    self._engines[cache_key] = engine2
                    self._last_used[cache_key] = datetime.now()
                    return engine2
                else:
                    logger.error(f"Failed to create engine for tenant {tenant_id}: {e}")
                    raise

    def get_session_factory(self, tenant_id: int) -> sessionmaker:
        """
        获取租户数据库会话工厂

        参数:
            tenant_id: 租户ID

        返回:
            sessionmaker: 会话工厂
        """
        cache_key = f"tenant_{tenant_id}"

        # 检查缓存
        if cache_key in self._session_factories:
            return self._session_factories[cache_key]

        # 创建新会话工厂
        engine = self.get_engine(tenant_id)
        session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )

        # 缓存会话工厂
        self._session_factories[cache_key] = session_factory

        logger.info(f"Created session factory for tenant {tenant_id}")
        return session_factory

    def get_session(self, tenant_id: int) -> Session:
        """
        获取租户数据库会话

        参数:
            tenant_id: 租户ID

        返回:
            Session: 数据库会话
        """
        session_factory = self.get_session_factory(tenant_id)
        return session_factory()

    def _create_tenant_database(self, tenant_id: int):
        """
        创建租户数据库

        参数:
            tenant_id: 租户ID
        """
        database_name = f"{settings.TENANT_DB_PREFIX}{tenant_id}"

        # 连接到MySQL服务器（不指定数据库）
        server_url = (
            f"mysql+pymysql://{settings.TENANT_DB_USER}:{settings.TENANT_DB_PASSWORD}"
            f"@{settings.TENANT_DB_HOST}:{settings.TENANT_DB_PORT}"
            f"/?charset=utf8mb4"
        )

        engine = create_engine(server_url)

        try:
            with engine.begin() as conn:
                # 创建数据库
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                logger.info(f"Created database: {database_name}")

            # 初始化表结构
            self._init_tenant_schema(tenant_id)

        except Exception as e:
            logger.error(f"Failed to create database {database_name}: {e}")
            raise
        finally:
            engine.dispose()

    def _init_tenant_schema(self, tenant_id: int):
        """
        初始化租户数据库表结构

        参数:
            tenant_id: 租户ID
        """
        engine = self.get_engine(tenant_id, create_if_not_exists=False)

        try:
            # 创建所有表
            Base.metadata.create_all(bind=engine)
            logger.info(f"Initialized schema for tenant {tenant_id}")

        except Exception as e:
            logger.error(f"Failed to initialize schema for tenant {tenant_id}: {e}")
            raise

    def drop_tenant_database(self, tenant_id: int):
        """
        删除租户数据库（线程安全）

        参数:
            tenant_id: 租户ID
        """
        database_name = f"{settings.TENANT_DB_PREFIX}{tenant_id}"
        cache_key = f"tenant_{tenant_id}"

        # 加锁清理缓存，防止并发访问已销毁的引擎
        with self._creation_lock:
            if cache_key in self._engines:
                self._engines[cache_key].dispose()
                del self._engines[cache_key]

            if cache_key in self._session_factories:
                del self._session_factories[cache_key]

            if cache_key in self._last_used:
                del self._last_used[cache_key]

        # 连接到MySQL服务器
        server_url = (
            f"mysql+pymysql://{settings.TENANT_DB_USER}:{settings.TENANT_DB_PASSWORD}"
            f"@{settings.TENANT_DB_HOST}:{settings.TENANT_DB_PORT}"
            f"/?charset=utf8mb4"
        )

        engine = create_engine(server_url)

        try:
            with engine.begin() as conn:
                # 删除数据库
                conn.execute(text(f"DROP DATABASE IF EXISTS `{database_name}`"))
                logger.info(f"Dropped database: {database_name}")

        except Exception as e:
            logger.error(f"Failed to drop database {database_name}: {e}")
            raise
        finally:
            engine.dispose()

    def cleanup_idle_connections(self):
        """清理空闲连接（线程安全）"""
        now = datetime.now()

        with self._creation_lock:
            idle_keys = [
                key for key, last_used in self._last_used.items()
                if now - last_used > self._max_idle_time
            ]

            for key in idle_keys:
                logger.info(f"Cleaning up idle connection: {key}")

                if key in self._engines:
                    self._engines[key].dispose()
                    del self._engines[key]

                if key in self._session_factories:
                    del self._session_factories[key]

                del self._last_used[key]

    def get_connection_stats(self) -> Dict:
        """
        获取连接统计信息

        返回:
            Dict: 统计信息
        """
        stats = {
            "total_engines": len(self._engines),
            "total_session_factories": len(self._session_factories),
            "engines": {}
        }

        for key, engine in self._engines.items():
            pool = engine.pool
            stats["engines"][key] = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "last_used": self._last_used.get(key).isoformat() if key in self._last_used else None
            }

        return stats


# 全局路由器实例
_router: Optional[TenantDatabaseRouter] = None


def get_tenant_router() -> TenantDatabaseRouter:
    """
    获取全局租户数据库路由器

    返回:
        TenantDatabaseRouter: 路由器实例
    """
    global _router
    if _router is None:
        _router = TenantDatabaseRouter()
    return _router


def get_tenant_db(tenant_id: int) -> Session:
    """
    获取租户数据库会话（便捷函数）

    参数:
        tenant_id: 租户ID

    返回:
        Session: 数据库会话
    """
    router = get_tenant_router()
    return router.get_session(tenant_id)


def get_tenant_db_dependency(tenant_id: int):
    """
    FastAPI依赖注入：获取租户数据库会话

    参数:
        tenant_id: 租户ID

    Yields:
        Session: 数据库会话
    """
    db = get_tenant_db(tenant_id)
    try:
        yield db
    finally:
        db.close()


__all__ = [
    "TenantDatabaseRouter",
    "get_tenant_router",
    "get_tenant_db",
    "get_tenant_db_dependency",
]
