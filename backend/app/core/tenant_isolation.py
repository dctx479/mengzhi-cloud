"""
多租户完全隔离实现
支持企业独立数据库和用户独立数据表
"""
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from ..core.config import settings

class TenantIsolationManager:
    """租户隔离管理器"""

    def __init__(self):
        self._tenant_engines = {}  # 企业独立数据库连接池

    def get_tenant_database_url(self, enterprise_id: int) -> str:
        """获取企业独立数据库URL"""
        return f"{settings.DATABASE_URL}_enterprise_{enterprise_id}"

    @contextmanager
    def get_tenant_session(self, enterprise_id: int) -> Session:
        """获取企业独立数据库会话"""
        if enterprise_id not in self._tenant_engines:
            db_url = self.get_tenant_database_url(enterprise_id)
            engine = create_engine(db_url, pool_pre_ping=True)
            self._tenant_engines[enterprise_id] = sessionmaker(bind=engine)

        SessionLocal = self._tenant_engines[enterprise_id]
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

# 全局实例
tenant_isolation = TenantIsolationManager()
