"""
初始化默认文化标签数据

该脚本用于在数据库迁移后初始化默认的文化标签数据

使用方法:
    python scripts/init_cultural_tags.py

版本: 1.0
更新日期: 2026-01-17
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from loguru import logger
from app.database import SessionLocal
from app.services.cultural_tag_service import CulturalTagService


def main():
    """初始化默认文化标签"""
    logger.info("开始初始化默认文化标签...")

    db = SessionLocal()
    try:
        # 初始化默认标签
        created_count = CulturalTagService.initialize_default_tags(db)

        logger.success(f"默认文化标签初始化完成！创建了 {created_count} 个标签")

        # 显示统计信息
        service = CulturalTagService(db)
        stats = service.get_tag_statistics()

        logger.info(f"标签统计:")
        logger.info(f"  - 总标签数: {stats['total_tags']}")
        logger.info(f"  - 启用标签数: {stats['active_tags']}")
        logger.info(f"  - 分类分布:")
        for code, data in stats['category_distribution'].items():
            logger.info(f"    * {data['name']}: {data['count']} 个")

        return 0

    except Exception as e:
        logger.error(f"初始化失败: {str(e)}")
        db.rollback()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
