#!/usr/bin/env python3
"""数据库迁移辅助脚本

功能:
- 创建新迁移
- 查看迁移历史
- 升级到指定版本
- 回滚到指定版本
- 验证迁移状态

使用:
    python -m scripts.db_migrate [命令] [选项]

命令:
    status          查看当前迁移状态
    history         查看迁移历史
    upgrade         升级到最新版本
    downgrade       回滚一个版本
    heads           查看最新版本
    branches        查看分支信息
    current         查看当前版本
"""

import sys
import os
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


def run_alembic_command(args: list) -> int:
    """运行Alembic命令"""
    cmd = ["alembic"] + args
    print(f"执行: {' '.join(cmd)}")
    return subprocess.call(cmd)


def status():
    """查看迁移状态"""
    print("\n" + "=" * 60)
    print("  迁移状态")
    print("=" * 60)

    print("\n当前版本:")
    run_alembic_command(["current"])

    print("\n最新版本:")
    run_alembic_command(["heads"])

    print("\n升级历史:")
    run_alembic_command(["history", "--oneline"])

    print("=" * 60)


def history():
    """查看迁移历史"""
    print("\n" + "=" * 60)
    print("  迁移历史")
    print("=" * 60)

    run_alembic_command(["history", "--verbose"])

    print("=" * 60)


def upgrade(target: str = "head"):
    """升级到指定版本"""
    print("\n" + "=" * 60)
    print(f"  升级到版本: {target}")
    print("=" * 60)

    print(f"数据库: {settings.DATABASE_URL.split('@')[1]}")

    code = run_alembic_command(["upgrade", target])

    if code == 0:
        print("\n✓ 升级成功!")
    else:
        print("\n✗ 升级失败!")
        return code

    # 显示最新状态
    print("\n当前版本:")
    run_alembic_command(["current"])

    print("=" * 60)
    return code


def downgrade(target: str = "-1"):
    """回滚到指定版本"""
    print("\n" + "=" * 60)
    print(f"  回滚到版本: {target}")
    print("=" * 60)

    print(f"数据库: {settings.DATABASE_URL.split('@')[1]}")

    code = run_alembic_command(["downgrade", target])

    if code == 0:
        print("\n✓ 回滚成功!")
    else:
        print("\n✗ 回滚失败!")
        return code

    # 显示最新状态
    print("\n当前版本:")
    run_alembic_command(["current"])

    print("=" * 60)
    return code


def heads():
    """查看最新版本"""
    print("\n" + "=" * 60)
    print("  最新版本")
    print("=" * 60)

    run_alembic_command(["heads"])

    print("=" * 60)


def branches():
    """查看分支信息"""
    print("\n" + "=" * 60)
    print("  分支信息")
    print("=" * 60)

    run_alembic_command(["branches"])

    print("=" * 60)


def current():
    """查看当前版本"""
    print("\n" + "=" * 60)
    print("  当前版本")
    print("=" * 60)

    run_alembic_command(["current"])

    print("=" * 60)


def print_header():
    """打印配置信息"""
    print("\n" + "=" * 60)
    print("  数据库迁移工具")
    print("=" * 60)
    print(f"数据库: {settings.DATABASE_URL.replace('password', '****')}")
    print(f"应用: {settings.APP_NAME}")
    print("=" * 60)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="数据库迁移管理工具"
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # status命令
    subparsers.add_parser("status", help="查看迁移状态")

    # history命令
    subparsers.add_parser("history", help="查看迁移历史")

    # upgrade命令
    upgrade_parser = subparsers.add_parser("upgrade", help="升级到指定版本")
    upgrade_parser.add_argument(
        "target",
        nargs="?",
        default="head",
        help="目标版本（默认: head）"
    )

    # downgrade命令
    downgrade_parser = subparsers.add_parser("downgrade", help="回滚到指定版本")
    downgrade_parser.add_argument(
        "target",
        nargs="?",
        default="-1",
        help="目标版本（默认: -1，即前一个版本）"
    )

    # heads命令
    subparsers.add_parser("heads", help="查看最新版本")

    # branches命令
    subparsers.add_parser("branches", help="查看分支信息")

    # current命令
    subparsers.add_parser("current", help="查看当前版本")

    args = parser.parse_args()

    print_header()

    if not args.command:
        status()
    elif args.command == "status":
        status()
    elif args.command == "history":
        history()
    elif args.command == "upgrade":
        sys.exit(upgrade(args.target))
    elif args.command == "downgrade":
        sys.exit(downgrade(args.target))
    elif args.command == "heads":
        heads()
    elif args.command == "branches":
        branches()
    elif args.command == "current":
        current()
    else:
        print(f"未知命令: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
