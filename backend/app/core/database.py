"""
数据库连接和初始化模块

功能：
- SQLAlchemy引擎和会话配置
- 数据库表创建和初始化
- 数据库连接管理

版本: 1.0
更新日期: 2026-01-17
"""

from typing import Generator
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger

# 导入所有模型和基类
from ..models.base import Base
from ..models import (
    User,
    UserType,
    UserStatus,
    UserRole,
    Gender,
    Enterprise,
    EnterpriseScale,
    VerifyStatus,
    PlanType,
    Product,
    ProductStatus,
    Conversation,
    AgentType,
    ConversationStatus,
    Message,
    MessageRole,
    ContentType,
    ContentRecord,
    Platform,
    Style,
    LengthType,
    RecordStatus,
    GenerationTemplate,
    TemplateContentType,
    TemplatePlatform,
    UserQuota,
    QuotaType,
)
from ..core.config import settings

# 数据库URL配置：统一从 settings 读取，避免硬编码凭据
DATABASE_URL = settings.DATABASE_URL

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,  # 合理化: 避免耗尽MySQL max_connections
    max_overflow=10,  # 合理化: 与 app/database.py 保持一致
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=30,
    echo=False,
    isolation_level="READ COMMITTED",
    connect_args={
        "charset": "utf8mb4",
    },
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

# 使用scoped_session进行线程局部存储
db_session = scoped_session(SessionLocal)


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话 - 用于依赖注入

    使用方式 (FastAPI):
        @app.get("/")
        def read_root(db: Session = Depends(get_db)):
            ...
    """
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """初始化数据库

    创建所有表并进行初始化设置
    """
    try:
        # 创建所有表（connect事件监听器已设置FOREIGN_KEY_CHECKS=0）
        Base.metadata.create_all(bind=engine)
        logger.info("✓ 数据库表创建成功")

        # 初始化系统配置
        session = SessionLocal()
        try:
            # 检查是否已初始化
            if session.query(User).filter_by(username="admin").first() is None:
                logger.info("✓ 首次初始化，创建默认数据...")
                _init_default_data(session)
            logger.info("✓ 数据库初始化完成")
        finally:
            session.close()

    except SQLAlchemyError as e:
        logger.error(f"✗ 数据库初始化失败: {str(e)}")
        raise


def drop_db() -> None:
    """删除所有表 - 用于测试和重置"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("✓ 所有表已删除")
    except SQLAlchemyError as e:
        logger.error(f"✗ 删除表失败: {str(e)}")
        raise


def reset_db() -> None:
    """重置数据库 - 删除所有表并重新创建"""
    drop_db()
    init_db()


def _init_default_data(session: Session) -> None:
    """初始化默认数据"""
    # 创建默认管理员账户（实际应该提示用户创建）
    # admin_user = User(
    #     user_uuid=generate_uuid(),
    #     username="admin",
    #     email="admin@example.com",
    #     password_hash="...",  # 应该使用hash
    #     user_type=UserType.PERSONAL,
    #     status=UserStatus.ACTIVE,
    #     role=UserRole.ADMIN,
    # )
    # session.add(admin_user)
    # session.commit()
    pass


def check_db_connection() -> bool:
    """检查数据库连接

    Returns:
        bool: 连接是否成功
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ 数据库连接成功")
        return True
    except Exception as e:
        logger.error(f"✗ 数据库连接失败: {str(e)}")
        return False


def get_table_info() -> dict:
    """获取数据库表信息

    Returns:
        dict: 表名称和列信息
    """
    inspector = inspect(engine)
    tables_info = {}

    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        tables_info[table_name] = {
            "columns": [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                    "default": col["default"],
                }
                for col in columns
            ]
        }

    return tables_info


# SQLAlchemy事件监听器
@event.listens_for(engine, "connect")
def set_mysql_session_vars(dbapi_conn, connection_record):
    """MySQL连接时设置会话参数"""
    pass


# 导出
__all__ = [
    "engine",
    "SessionLocal",
    "db_session",
    "get_db",
    "init_db",
    "drop_db",
    "reset_db",
    "check_db_connection",
    "get_table_info",
    "Base",
]
