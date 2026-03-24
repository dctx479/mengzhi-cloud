"""
租户数据库管理服务

版本: 1.1
更新日期: 2026-02-10

功能：
- 创建租户数据库
- 初始化表结构
- 数据迁移（共享<->独立）
- 数据库备份和恢复
- 数据库删除

安全说明：
- S-P0-002: 所有 subprocess 调用均使用白名单验证
- 数据库名称和文件路径经过严格验证
"""

from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import Session
import logging
import subprocess
import os
import re
import shutil

from app.core.config import settings
from app.core.tenant_database import get_tenant_router, TenantDatabaseRouter
from app.models.base import Base
from app.models.enterprise import Enterprise, IsolationMode

logger = logging.getLogger(__name__)


# S-P0-002: 安全验证函数
def _validate_database_name(db_name: str) -> bool:
    """验证数据库名称是否安全（防止注入）

    只允许字母、数字、下划线，长度 1-64
    """
    if not db_name:
        return False
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]{0,63}$'
    return bool(re.match(pattern, db_name))


def _validate_backup_path(file_path: str, base_dir: str) -> bool:
    """验证备份文件路径是否在允许的目录内（防止路径遍历）

    Args:
        file_path: 要验证的文件路径
        base_dir: 允许的基础目录

    Returns:
        bool: 路径是否安全
    """
    try:
        # 解析绝对路径
        abs_path = os.path.abspath(file_path)
        abs_base = os.path.abspath(base_dir)

        # 检查是否在基础目录内
        return abs_path.startswith(abs_base + os.sep) or abs_path == abs_base
    except Exception:
        return False


def _get_mysql_binary(binary_name: str) -> str:
    """获取 MySQL 二进制文件的安全路径

    Args:
        binary_name: 二进制名称 (mysql 或 mysqldump)

    Returns:
        str: 二进制文件的完整路径

    Raises:
        FileNotFoundError: 找不到二进制文件
    """
    # 白名单：只允许特定的 MySQL 命令
    allowed_binaries = {'mysql', 'mysqldump'}
    if binary_name not in allowed_binaries:
        raise ValueError(f"不允许的命令: {binary_name}")

    # 尝试从系统路径查找
    binary_path = shutil.which(binary_name)
    if binary_path:
        return binary_path

    # Windows 上尝试常见路径
    if os.name == 'nt':
        common_paths = [
            r"C:\Program Files\MySQL\MySQL Server 8.0\bin",
            r"C:\Program Files\MySQL\MySQL Server 5.7\bin",
            r"C:\xampp\mysql\bin",
        ]
        for path in common_paths:
            full_path = os.path.join(path, f"{binary_name}.exe")
            if os.path.exists(full_path):
                return full_path

    raise FileNotFoundError(f"找不到 {binary_name} 命令，请确保 MySQL 客户端已安装")


class TenantDatabaseManager:
    """租户数据库管理器

    提供租户数据库的完整生命周期管理
    """

    def __init__(self):
        """初始化管理器"""
        self.router: TenantDatabaseRouter = get_tenant_router()

    def create_tenant_database(
        self,
        enterprise_id: int,
        db: Session,
        initialize_schema: bool = True
    ) -> Dict:
        """
        创建租户数据库

        参数:
            enterprise_id: 企业ID
            db: 主数据库会话
            initialize_schema: 是否初始化表结构

        返回:
            Dict: 创建结果
        """
        try:
            # 获取企业信息
            enterprise = db.query(Enterprise).filter(
                Enterprise.id == enterprise_id
            ).first()

            if not enterprise:
                raise ValueError(f"Enterprise {enterprise_id} not found")

            if enterprise.isolation_mode != IsolationMode.ISOLATED:
                raise ValueError(f"Enterprise {enterprise_id} is not in isolated mode")

            if enterprise.database_name:
                raise ValueError(f"Database already exists for enterprise {enterprise_id}")

            # 生成数据库名称
            database_name = f"{settings.TENANT_DB_PREFIX}{enterprise_id}"

            # 创建数据库
            logger.info(f"Creating database for enterprise {enterprise_id}: {database_name}")
            self.router.get_engine(enterprise_id, create_if_not_exists=True)

            # 更新企业信息
            enterprise.database_name = database_name
            enterprise.database_created_at = datetime.utcnow()
            db.commit()

            logger.info(f"Successfully created database for enterprise {enterprise_id}")

            return {
                "success": True,
                "enterprise_id": enterprise_id,
                "database_name": database_name,
                "created_at": enterprise.database_created_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to create database for enterprise {enterprise_id}: {e}")
            db.rollback()
            raise

    def drop_tenant_database(
        self,
        enterprise_id: int,
        db: Session,
        backup_first: bool = True
    ) -> Dict:
        """
        删除租户数据库

        参数:
            enterprise_id: 企业ID
            db: 主数据库会话
            backup_first: 是否先备份

        返回:
            Dict: 删除结果
        """
        try:
            # 获取企业信息
            enterprise = db.query(Enterprise).filter(
                Enterprise.id == enterprise_id
            ).first()

            if not enterprise:
                raise ValueError(f"Enterprise {enterprise_id} not found")

            if not enterprise.database_name:
                raise ValueError(f"No database found for enterprise {enterprise_id}")

            # 备份数据库
            backup_file = None
            if backup_first:
                backup_result = self.backup_tenant_database(enterprise_id, db)
                backup_file = backup_result.get("backup_file")

            # 删除数据库
            logger.info(f"Dropping database for enterprise {enterprise_id}: {enterprise.database_name}")
            self.router.drop_tenant_database(enterprise_id)

            # 更新企业信息
            enterprise.database_name = None
            enterprise.database_created_at = None
            db.commit()

            logger.info(f"Successfully dropped database for enterprise {enterprise_id}")

            return {
                "success": True,
                "enterprise_id": enterprise_id,
                "backup_file": backup_file
            }

        except Exception as e:
            logger.error(f"Failed to drop database for enterprise {enterprise_id}: {e}")
            db.rollback()
            raise

    def migrate_to_isolated(
        self,
        enterprise_id: int,
        db: Session
    ) -> Dict:
        """
        将租户从共享模式迁移到独立模式

        参数:
            enterprise_id: 企业ID
            db: 主数据库会话

        返回:
            Dict: 迁移结果
        """
        try:
            # 获取企业信息
            enterprise = db.query(Enterprise).filter(
                Enterprise.id == enterprise_id
            ).first()

            if not enterprise:
                raise ValueError(f"Enterprise {enterprise_id} not found")

            if enterprise.isolation_mode == IsolationMode.ISOLATED:
                raise ValueError(f"Enterprise {enterprise_id} is already in isolated mode")

            logger.info(f"Starting migration to isolated mode for enterprise {enterprise_id}")

            # 1. 创建租户数据库
            self.create_tenant_database(enterprise_id, db, initialize_schema=True)

            # 2. 获取租户数据库会话
            tenant_db = self.router.get_session(enterprise_id)

            try:
                # 3. 迁移数据
                migrated_tables = self._copy_enterprise_data(
                    enterprise_id,
                    source_db=db,
                    target_db=tenant_db
                )

                # 4. 验证数据完整性
                validation_result = self._validate_migration(
                    enterprise_id,
                    source_db=db,
                    target_db=tenant_db,
                    tables=migrated_tables
                )

                if not validation_result["valid"]:
                    raise ValueError(f"Data validation failed: {validation_result['errors']}")

                # 5. 更新企业隔离模式
                enterprise.isolation_mode = IsolationMode.ISOLATED
                db.commit()
                tenant_db.commit()

                logger.info(f"Successfully migrated enterprise {enterprise_id} to isolated mode")

                return {
                    "success": True,
                    "enterprise_id": enterprise_id,
                    "database_name": enterprise.database_name,
                    "migrated_tables": migrated_tables,
                    "validation": validation_result
                }

            finally:
                tenant_db.close()

        except Exception as e:
            logger.error(f"Failed to migrate enterprise {enterprise_id} to isolated mode: {e}")
            db.rollback()
            # 清理已创建的数据库
            try:
                self.router.drop_tenant_database(enterprise_id)
            except Exception as cleanup_err:
                logger.warning(f"Failed to cleanup tenant database for enterprise {enterprise_id}: {cleanup_err}")
            raise

    def migrate_to_shared(
        self,
        enterprise_id: int,
        db: Session
    ) -> Dict:
        """
        将租户从独立模式迁移到共享模式

        参数:
            enterprise_id: 企业ID
            db: 主数据库会话

        返回:
            Dict: 迁移结果
        """
        try:
            # 获取企业信息
            enterprise = db.query(Enterprise).filter(
                Enterprise.id == enterprise_id
            ).first()

            if not enterprise:
                raise ValueError(f"Enterprise {enterprise_id} not found")

            if enterprise.isolation_mode == IsolationMode.SHARED:
                raise ValueError(f"Enterprise {enterprise_id} is already in shared mode")

            logger.info(f"Starting migration to shared mode for enterprise {enterprise_id}")

            # 1. 获取租户数据库会话
            tenant_db = self.router.get_session(enterprise_id)

            try:
                # 2. 迁移数据到主数据库
                migrated_tables = self._copy_enterprise_data(
                    enterprise_id,
                    source_db=tenant_db,
                    target_db=db
                )

                # 3. 验证数据完整性
                validation_result = self._validate_migration(
                    enterprise_id,
                    source_db=tenant_db,
                    target_db=db,
                    tables=migrated_tables
                )

                if not validation_result["valid"]:
                    raise ValueError(f"Data validation failed: {validation_result['errors']}")

                # 4. 更新企业隔离模式
                enterprise.isolation_mode = IsolationMode.SHARED
                db.commit()

                # 5. 删除租户数据库
                self.drop_tenant_database(enterprise_id, db, backup_first=True)

                logger.info(f"Successfully migrated enterprise {enterprise_id} to shared mode")

                return {
                    "success": True,
                    "enterprise_id": enterprise_id,
                    "migrated_tables": migrated_tables,
                    "validation": validation_result
                }

            finally:
                tenant_db.close()

        except Exception as e:
            logger.error(f"Failed to migrate enterprise {enterprise_id} to shared mode: {e}")
            db.rollback()
            raise

    def backup_tenant_database(
        self,
        enterprise_id: int,
        db: Session,
        output_dir: Optional[str] = None
    ) -> Dict:
        """
        备份租户数据库

        参数:
            enterprise_id: 企业ID
            db: 主数据库会话
            output_dir: 输出目录

        返回:
            Dict: 备份结果
        """
        try:
            # 获取企业信息
            enterprise = db.query(Enterprise).filter(
                Enterprise.id == enterprise_id
            ).first()

            if not enterprise:
                raise ValueError(f"Enterprise {enterprise_id} not found")

            if not enterprise.database_name:
                raise ValueError(f"No database found for enterprise {enterprise_id}")

            # S-P0-002: 验证数据库名称安全性
            if not _validate_database_name(enterprise.database_name):
                raise ValueError(f"Invalid database name: {enterprise.database_name}")

            # 设置输出目录
            if output_dir is None:
                output_dir = os.path.join(settings.UPLOAD_DIR, "backups")

            os.makedirs(output_dir, exist_ok=True)

            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(
                output_dir,
                f"backup_{enterprise_id}_{timestamp}.sql"
            )

            # S-P0-002: 验证备份路径安全性（防止路径遍历）
            if not _validate_backup_path(backup_file, output_dir):
                raise ValueError(f"Invalid backup path: {backup_file}")

            # 执行备份
            logger.info(f"Backing up database for enterprise {enterprise_id} to {backup_file}")

            # S-P0-002: 使用安全的二进制路径
            mysqldump_path = _get_mysql_binary("mysqldump")

            cmd = [
                mysqldump_path,
                "-h", settings.TENANT_DB_HOST,
                "-P", str(settings.TENANT_DB_PORT),
                "-u", settings.TENANT_DB_USER,
                f"-p{settings.TENANT_DB_PASSWORD}",
                enterprise.database_name,
                "--result-file", backup_file
            ]

            # S-P0-002: 禁用 shell=True，使用列表参数防止命令注入
            result = subprocess.run(cmd, capture_output=True, text=True, shell=False)

            if result.returncode != 0:
                raise RuntimeError(f"Backup failed: {result.stderr}")

            logger.info(f"Successfully backed up database for enterprise {enterprise_id}")

            return {
                "success": True,
                "enterprise_id": enterprise_id,
                "database_name": enterprise.database_name,
                "backup_file": backup_file,
                "backup_size": os.path.getsize(backup_file),
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to backup database for enterprise {enterprise_id}: {e}")
            raise

    def restore_tenant_database(
        self,
        enterprise_id: int,
        db: Session,
        backup_file: str
    ) -> Dict:
        """
        恢复租户数据库

        参数:
            enterprise_id: 企业ID
            db: 主数据库会话
            backup_file: 备份文件路径

        返回:
            Dict: 恢复结果
        """
        try:
            # 获取企业信息
            enterprise = db.query(Enterprise).filter(
                Enterprise.id == enterprise_id
            ).first()

            if not enterprise:
                raise ValueError(f"Enterprise {enterprise_id} not found")

            if not enterprise.database_name:
                raise ValueError(f"No database found for enterprise {enterprise_id}")

            # S-P0-002: 验证数据库名称安全性
            if not _validate_database_name(enterprise.database_name):
                raise ValueError(f"Invalid database name: {enterprise.database_name}")

            if not os.path.exists(backup_file):
                raise ValueError(f"Backup file not found: {backup_file}")

            # S-P0-002: 验证备份文件路径安全性
            backup_base_dir = os.path.join(settings.UPLOAD_DIR, "backups")
            if not _validate_backup_path(backup_file, backup_base_dir):
                raise ValueError(f"Backup file must be in the backups directory: {backup_file}")

            # S-P0-002: 验证备份文件扩展名
            if not backup_file.endswith('.sql'):
                raise ValueError(f"Invalid backup file extension: {backup_file}")

            # 执行恢复
            logger.info(f"Restoring database for enterprise {enterprise_id} from {backup_file}")

            # S-P0-002: 使用安全的二进制路径
            mysql_path = _get_mysql_binary("mysql")

            cmd = [
                mysql_path,
                "-h", settings.TENANT_DB_HOST,
                "-P", str(settings.TENANT_DB_PORT),
                "-u", settings.TENANT_DB_USER,
                f"-p{settings.TENANT_DB_PASSWORD}",
                enterprise.database_name
            ]

            with open(backup_file, 'r') as f:
                # S-P0-002: 禁用 shell=True，使用列表参数防止命令注入
                result = subprocess.run(cmd, stdin=f, capture_output=True, text=True, shell=False)

            if result.returncode != 0:
                raise RuntimeError(f"Restore failed: {result.stderr}")

            logger.info(f"Successfully restored database for enterprise {enterprise_id}")

            return {
                "success": True,
                "enterprise_id": enterprise_id,
                "database_name": enterprise.database_name,
                "backup_file": backup_file,
                "restored_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to restore database for enterprise {enterprise_id}: {e}")
            raise

    def _copy_enterprise_data(
        self,
        enterprise_id: int,
        source_db: Session,
        target_db: Session
    ) -> List[str]:
        """
        复制企业数据

        参数:
            enterprise_id: 企业ID
            source_db: 源数据库会话
            target_db: 目标数据库会话

        返回:
            List[str]: 已迁移的表列表
        """
        # 需要迁移的表（包含enterprise_id字段的表）
        tables_to_migrate = [
            "products",
            "conversations",
            "messages",
            "content_records",
            "media",
            # 添加其他需要迁移的表
        ]

        migrated_tables = []

        for table_name in tables_to_migrate:
            try:
                # 这里需要根据实际模型实现数据复制
                # 示例：复制产品数据
                if table_name == "products":
                    from app.models.product import Product
                    products = source_db.query(Product).filter(
                        Product.enterprise_id == enterprise_id
                    ).all()

                    for product in products:
                        # 创建新对象（避免主键冲突）
                        product_dict = {
                            k: v for k, v in product.__dict__.items()
                            if not k.startswith('_') and k != 'id'
                        }
                        new_product = Product(**product_dict)
                        target_db.add(new_product)

                    target_db.commit()
                    migrated_tables.append(table_name)
                    logger.info(f"Migrated {len(products)} records from {table_name}")

                # 添加其他表的迁移逻辑...

            except Exception as e:
                logger.error(f"Failed to migrate table {table_name}: {e}")
                raise

        return migrated_tables

    def _validate_migration(
        self,
        enterprise_id: int,
        source_db: Session,
        target_db: Session,
        tables: List[str]
    ) -> Dict:
        """
        验证数据迁移完整性

        参数:
            enterprise_id: 企业ID
            source_db: 源数据库会话
            target_db: 目标数据库会话
            tables: 需要验证的表列表

        返回:
            Dict: 验证结果
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "table_counts": {}
        }

        for table_name in tables:
            try:
                # 这里需要根据实际模型实现数据验证
                # 示例：验证产品数据
                if table_name == "products":
                    from app.models.product import Product
                    source_count = source_db.query(Product).filter(
                        Product.enterprise_id == enterprise_id
                    ).count()
                    target_count = target_db.query(Product).filter(
                        Product.enterprise_id == enterprise_id
                    ).count()

                    validation_result["table_counts"][table_name] = {
                        "source": source_count,
                        "target": target_count
                    }

                    if source_count != target_count:
                        validation_result["valid"] = False
                        validation_result["errors"].append(
                            f"Table {table_name}: count mismatch (source={source_count}, target={target_count})"
                        )

                # 添加其他表的验证逻辑...

            except Exception as e:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Table {table_name}: validation error - {str(e)}")

        return validation_result


# 全局管理器实例
_manager: Optional[TenantDatabaseManager] = None


def get_tenant_db_manager() -> TenantDatabaseManager:
    """
    获取全局租户数据库管理器

    返回:
        TenantDatabaseManager: 管理器实例
    """
    global _manager
    if _manager is None:
        _manager = TenantDatabaseManager()
    return _manager


__all__ = [
    "TenantDatabaseManager",
    "get_tenant_db_manager",
]
