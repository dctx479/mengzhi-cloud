#!/usr/bin/env python3
"""数据库初始化脚本

功能:
- 创建数据库表（通过Alembic迁移）
- 初始化种子数据
- 验证数据库连接

使用:
    python -m scripts.init_db [--seed] [--drop]

选项:
    --seed: 同时创建种子数据
    --drop: 删除现有表后重建
    --verbose: 显示详细输出
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from app.database import engine, SessionLocal, init_db
from app.models.base import Base
from app.core.config import settings


def check_connection() -> bool:
    """检查数据库连接"""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            return True
    except Exception as e:
        print(f"错误: 无法连接到数据库")
        print(f"详情: {str(e)}")
        return False


def get_existing_tables() -> set:
    """获取现有的表列表"""
    inspector = inspect(engine)
    return set(inspector.get_table_names())


def create_tables() -> bool:
    """创建所有表"""
    try:
        print("开始创建数据库表...")
        init_db()
        print("✓ 数据库表创建成功!")
        return True
    except Exception as e:
        print(f"✗ 创建数据库表失败: {str(e)}")
        return False


def drop_tables() -> bool:
    """删除所有表"""
    try:
        print("正在删除现有表...")
        Base.metadata.drop_all(bind=engine)
        print("✓ 现有表已删除")
        return True
    except Exception as e:
        print(f"✗ 删除表失败: {str(e)}")
        return False


def verify_tables() -> bool:
    """验证表是否创建成功"""
    try:
        existing_tables = get_existing_tables()
        required_tables = {'users', 'products', 'conversations', 'messages'}

        created_tables = required_tables & existing_tables
        missing_tables = required_tables - existing_tables

        print("\n表状态检查:")
        print(f"已创建的表: {', '.join(sorted(created_tables)) if created_tables else '无'}")
        if missing_tables:
            print(f"缺失的表: {', '.join(sorted(missing_tables))}")
            return False

        return len(missing_tables) == 0
    except Exception as e:
        print(f"✗ 验证表失败: {str(e)}")
        return False


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_config():
    """打印配置信息"""
    print(f"数据库URL: {settings.DATABASE_URL.replace(':pass', ':***')}")
    print(f"调试模式: {settings.DEBUG}")
    print(f"应用名称: {settings.APP_NAME}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="数据库初始化脚本"
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="创建种子数据"
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="删除现有表后重建"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细输出"
    )

    args = parser.parse_args()

    print_header("数据库初始化")
    print_config()

    # 检查数据库连接
    print("\n检查数据库连接...")
    if not check_connection():
        sys.exit(1)
    print("✓ 数据库连接成功")

    # 显示现有表
    existing_tables = get_existing_tables()
    if existing_tables:
        print(f"\n现有表: {', '.join(sorted(existing_tables))}")

    # 删除表（如果指定）
    if args.drop:
        if not drop_tables():
            sys.exit(1)

    # 创建表
    if not create_tables():
        sys.exit(1)

    # 验证表
    print("\n验证表结构...")
    if not verify_tables():
        print("✗ 表验证失败")
        sys.exit(1)

    print("✓ 所有表都已成功创建")

    # 创建种子数据
    if args.seed:
        print("\n创建种子数据...")
        try:
            from scripts.seed_data import seed_database
            if seed_database():
                print("✓ 种子数据创建成功")
            else:
                print("⚠ 种子数据创建失败，但表已创建")
        except ImportError:
            print("⚠ seed_data模块未找到，跳过种子数据创建")
        except Exception as e:
            print(f"⚠ 种子数据创建失败: {str(e)}")

    print_header("初始化完成")
    print("✓ 数据库已准备就绪!")


if __name__ == "__main__":
    main()
