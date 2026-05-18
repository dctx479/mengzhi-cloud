"""
数据库配置和初始化

版本: 1.0
更新日期: 2026-01-17

NOTE: 本文件是 app/core/database.py 的包装器，为向后兼容性而保留。
新代码应直接从 app.core.database 导入。
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.core.config import settings
from app.models.base import Base

# 创建数据库引擎
# SQLite不支持pool_size和max_overflow参数
if settings.DATABASE_URL.startswith('sqlite'):
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False}  # SQLite特定配置
    )
else:
    # MySQL生产配置（与app/core/database.py保持一致）
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=QueuePool,
        echo=settings.DEBUG,
        pool_size=5,       # 合理化: 避免耗尽MySQL max_connections
        max_overflow=10,    # 合理化: pool_size+max_overflow=15，为租户DB留余量
        pool_pre_ping=True,
        pool_recycle=3600,  # 重要: 回收连接防止MySQL 8小时超时
        pool_timeout=30,    # 连接池等待超时（秒）
        isolation_level="READ COMMITTED",  # 事务隔离级别
        connect_args={
            "charset": "utf8mb4",
        },
    )

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
