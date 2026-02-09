"""
租户数据迁移脚本

版本: 1.0
更新日期: 2026-01-22

功能：
- 将现有租户迁移到独立数据库
- 数据完整性验证
- 回滚机制
- 批量迁移支持

使用方法：
    python scripts/migrate_to_isolated.py --enterprise-id 1
    python scripts/migrate_to_isolated.py --all --plan-type pro
    python scripts/migrate_to_isolated.py --dry-run
"""

import sys
import os
import argparse
import logging
from typing import List, Dict
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.enterprise import Enterprise, IsolationMode, PlanType
from app.services.tenant_db_manager import get_tenant_db_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TenantMigrationScript:
    """租户迁移脚本"""

    def __init__(self, dry_run: bool = False):
        """
        初始化迁移脚本

        参数:
            dry_run: 是否为演练模式（不实际执行）
        """
        self.dry_run = dry_run
        self.manager = get_tenant_db_manager()
        self.db: Session = SessionLocal()

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'db'):
            self.db.close()

    def migrate_enterprise(self, enterprise_id: int) -> Dict:
        """
        迁移单个企业

        参数:
            enterprise_id: 企业ID

        返回:
            Dict: 迁移结果
        """
        try:
            # 获取企业信息
            enterprise = self.db.query(Enterprise).filter(
                Enterprise.id == enterprise_id
            ).first()

            if not enterprise:
                raise ValueError(f"Enterprise {enterprise_id} not found")

            logger.info(f"Starting migration for enterprise {enterprise_id}: {enterprise.name}")

            # 检查当前状态
            if enterprise.isolation_mode == IsolationMode.ISOLATED:
                logger.warning(f"Enterprise {enterprise_id} is already in isolated mode")
                return {
                    "success": False,
                    "enterprise_id": enterprise_id,
                    "error": "Already in isolated mode"
                }

            if self.dry_run:
                logger.info(f"[DRY RUN] Would migrate enterprise {enterprise_id} to isolated mode")
                return {
                    "success": True,
                    "enterprise_id": enterprise_id,
                    "dry_run": True
                }

            # 执行迁移
            result = self.manager.migrate_to_isolated(enterprise_id, self.db)

            logger.info(f"Successfully migrated enterprise {enterprise_id}")
            logger.info(f"  Database: {result['database_name']}")
            logger.info(f"  Migrated tables: {', '.join(result['migrated_tables'])}")

            return result

        except Exception as e:
            logger.error(f"Failed to migrate enterprise {enterprise_id}: {e}")
            return {
                "success": False,
                "enterprise_id": enterprise_id,
                "error": str(e)
            }

    def migrate_by_plan_type(self, plan_type: str) -> List[Dict]:
        """
        按套餐类型批量迁移

        参数:
            plan_type: 套餐类型（pro/enterprise）

        返回:
            List[Dict]: 迁移结果列表
        """
        try:
            # 查询符合条件的企业
            enterprises = self.db.query(Enterprise).filter(
                Enterprise.plan_type == PlanType(plan_type),
                Enterprise.isolation_mode == IsolationMode.SHARED
            ).all()

            logger.info(f"Found {len(enterprises)} enterprises with plan type {plan_type}")

            results = []
            for enterprise in enterprises:
                logger.info(f"\n{'='*60}")
                logger.info(f"Migrating enterprise {enterprise.id}: {enterprise.name}")
                logger.info(f"{'='*60}")

                result = self.migrate_enterprise(enterprise.id)
                results.append(result)

                # 添加延迟以避免过载
                if not self.dry_run:
                    import time
                    time.sleep(1)

            return results

        except Exception as e:
            logger.error(f"Failed to migrate by plan type {plan_type}: {e}")
            raise

    def migrate_all_eligible(self) -> List[Dict]:
        """
        迁移所有符合条件的企业

        符合条件：
        - 套餐类型为 PRO 或 ENTERPRISE
        - 当前为共享模式

        返回:
            List[Dict]: 迁移结果列表
        """
        try:
            # 查询符合条件的企业
            enterprises = self.db.query(Enterprise).filter(
                Enterprise.plan_type.in_([PlanType.PRO, PlanType.ENTERPRISE]),
                Enterprise.isolation_mode == IsolationMode.SHARED
            ).all()

            logger.info(f"Found {len(enterprises)} eligible enterprises for migration")

            results = []
            for enterprise in enterprises:
                logger.info(f"\n{'='*60}")
                logger.info(f"Migrating enterprise {enterprise.id}: {enterprise.name}")
                logger.info(f"  Plan: {enterprise.plan_type.value}")
                logger.info(f"{'='*60}")

                result = self.migrate_enterprise(enterprise.id)
                results.append(result)

                # 添加延迟以避免过载
                if not self.dry_run:
                    import time
                    time.sleep(1)

            return results

        except Exception as e:
            logger.error(f"Failed to migrate all eligible enterprises: {e}")
            raise

    def generate_report(self, results: List[Dict]) -> None:
        """
        生成迁移报告

        参数:
            results: 迁移结果列表
        """
        logger.info(f"\n{'='*60}")
        logger.info("MIGRATION REPORT")
        logger.info(f"{'='*60}")

        total = len(results)
        success = sum(1 for r in results if r.get("success"))
        failed = total - success

        logger.info(f"Total enterprises: {total}")
        logger.info(f"Successful: {success}")
        logger.info(f"Failed: {failed}")

        if failed > 0:
            logger.info(f"\nFailed enterprises:")
            for result in results:
                if not result.get("success"):
                    logger.info(f"  - Enterprise {result['enterprise_id']}: {result.get('error')}")

        logger.info(f"\n{'='*60}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="租户数据迁移脚本")

    # 迁移模式
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--enterprise-id",
        type=int,
        help="迁移指定企业ID"
    )
    group.add_argument(
        "--plan-type",
        choices=["pro", "enterprise"],
        help="按套餐类型批量迁移"
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="迁移所有符合条件的企业"
    )

    # 选项
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="演练模式（不实际执行）"
    )

    args = parser.parse_args()

    # 创建迁移脚本实例
    script = TenantMigrationScript(dry_run=args.dry_run)

    try:
        if args.dry_run:
            logger.info("Running in DRY RUN mode - no actual changes will be made")

        # 执行迁移
        if args.enterprise_id:
            logger.info(f"Migrating single enterprise: {args.enterprise_id}")
            result = script.migrate_enterprise(args.enterprise_id)
            script.generate_report([result])

        elif args.plan_type:
            logger.info(f"Migrating enterprises with plan type: {args.plan_type}")
            results = script.migrate_by_plan_type(args.plan_type)
            script.generate_report(results)

        elif args.all:
            logger.info("Migrating all eligible enterprises")
            results = script.migrate_all_eligible()
            script.generate_report(results)

        logger.info("\nMigration completed!")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
