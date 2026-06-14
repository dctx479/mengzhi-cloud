#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱文化元素数据初始化脚本

功能：
1. 从 JSON 种子文件读取文化元素数据
2. 批量插入到 cultural_elements 表
3. 事务管理和错误处理
4. 去重检查（按 name 唯一键）

使用：
    python scripts/init_cultural_elements.py
    python scripts/init_cultural_elements.py --dry-run  # 仅预览，不实际插入
"""
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import argparse

# 设置 UTF-8 输出（Windows 兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, OperationalError
from app.core.config import settings


def load_seed_data(file_path: Path) -> List[Dict[str, Any]]:
    """加载种子数据文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"√ 成功加载 {len(data)} 条文化元素数据")
        return data
    except FileNotFoundError:
        print(f"× 错误: 找不到种子数据文件 {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"× 错误: JSON 格式无效 - {e}")
        sys.exit(1)


def init_cultural_elements(dry_run: bool = False) -> None:
    """初始化文化元素数据"""

    # 加载种子数据
    seed_file = project_root / "data" / "cultural_elements_seed.json"
    elements = load_seed_data(seed_file)

    if dry_run:
        print("\n=== 预览模式 - 不会实际插入数据 ===\n")
        for idx, elem in enumerate(elements, 1):
            print(f"{idx}. {elem['name']} ({elem['type']}) - 热度: {elem['hot_score']}")
        print(f"\n共 {len(elements)} 条数据")
        return

    # 创建数据库连接
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    inserted_count = 0
    skipped_count = 0
    error_count = 0

    try:
        print("\n开始插入数据...\n")

        for elem in elements:
            try:
                # 检查是否已存在
                check_query = text("SELECT id FROM cultural_elements WHERE name = :name")
                result = session.execute(check_query, {"name": elem['name']}).fetchone()

                if result:
                    print(f"o 跳过 (已存在): {elem['name']}")
                    skipped_count += 1
                    continue

                # 插入数据
                insert_query = text("""
                    INSERT INTO cultural_elements
                    (name, type, story, origin_region, hot_score, metadata, view_count)
                    VALUES
                    (:name, :type, :story, :origin_region, :hot_score, :metadata, 0)
                """)

                session.execute(insert_query, {
                    "name": elem['name'],
                    "type": elem['type'],
                    "story": elem['story'],
                    "origin_region": elem.get('origin_region'),
                    "hot_score": elem.get('hot_score', 50),
                    "metadata": json.dumps(elem.get('metadata', {}), ensure_ascii=False)
                })

                print(f"√ 插入成功: {elem['name']} ({elem['type']})")
                inserted_count += 1

            except IntegrityError as e:
                print(f"o 跳过 (唯一键冲突): {elem['name']} - {str(e)[:50]}")
                skipped_count += 1
                session.rollback()

            except SQLAlchemyError as e:
                print(f"× 插入失败: {elem['name']} - {e}")
                error_count += 1
                session.rollback()

        # 提交事务
        session.commit()
        print("\n" + "="*60)
        print(f"√ 数据初始化完成")
        print(f"  - 成功插入: {inserted_count} 条")
        print(f"  - 跳过 (已存在): {skipped_count} 条")
        print(f"  - 错误: {error_count} 条")
        print("="*60 + "\n")

    except Exception as e:
        session.rollback()
        print(f"\n× 发生严重错误: {e}")
        sys.exit(1)

    finally:
        session.close()
        engine.dispose()


def verify_table_exists() -> bool:
    """验证 cultural_elements 表是否存在"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) as cnt
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = 'cultural_elements'
            """))
            count = result.fetchone()[0]
            engine.dispose()
            return count > 0
    except OperationalError as e:
        if "Unknown database" in str(e):
            print(f"× 数据库连接失败: 数据库不存在")
            print(f"  DATABASE_URL: {settings.DATABASE_URL}")
        else:
            print(f"× 数据库连接失败: {e}")
        return False
    except Exception as e:
        print(f"× 验证表存在性失败: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='初始化知识图谱文化元素数据')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际插入数据')
    parser.add_argument('--verify', action='store_true', help='仅验证表是否存在')
    args = parser.parse_args()

    print("\n" + "="*60)
    print("知识图谱文化元素数据初始化脚本")
    print("="*60 + "\n")

    # 验证模式
    if args.verify:
        if verify_table_exists():
            print("√ cultural_elements 表已存在")
            sys.exit(0)
        else:
            print("× cultural_elements 表不存在，请先运行迁移: alembic upgrade head")
            sys.exit(1)

    # 检查表是否存在
    if not verify_table_exists():
        print("× 错误: cultural_elements 表不存在")
        print("  请先运行数据库迁移: alembic upgrade head\n")
        sys.exit(1)

    print("√ cultural_elements 表已存在")

    # 执行初始化
    init_cultural_elements(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
