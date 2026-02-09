"""
环境检查和服务健康测试
测试所有必要服务和依赖项是否正常运行
"""

import os
import sys
import pytest
import redis
import pymysql
from sqlalchemy import create_engine, text
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.config import settings


class TestEnvironment:
    """环境检查测试类"""

    def test_python_version(self):
        """检查Python版本 >= 3.11"""
        assert sys.version_info >= (3, 11), f"Python版本过低: {sys.version_info}"
        print(f"✓ Python版本: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    def test_environment_variables(self):
        """检查必要的环境变量"""
        required_vars = [
            'DATABASE_URL',
            'SECRET_KEY',
            'REDIS_HOST',
        ]

        missing_vars = []
        for var in required_vars:
            if not hasattr(settings, var) or getattr(settings, var) is None:
                missing_vars.append(var)

        assert len(missing_vars) == 0, f"缺少环境变量: {', '.join(missing_vars)}"
        print("✓ 所有必要环境变量已配置")

    def test_mysql_connection(self):
        """测试MySQL数据库连接"""
        try:
            # 尝试创建连接
            engine = create_engine(settings.DATABASE_URL)
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                assert result.scalar() == 1
            print(f"✓ MySQL连接成功: {settings.DATABASE_URL.split('@')[1].split('/')[0]}")
        except Exception as e:
            pytest.fail(f"MySQL连接失败: {str(e)}")

    def test_mysql_version(self):
        """检查MySQL版本 >= 8.0"""
        try:
            engine = create_engine(settings.DATABASE_URL)
            with engine.connect() as connection:
                result = connection.execute(text("SELECT VERSION()"))
                version = result.scalar()
                major_version = int(version.split('.')[0])
                assert major_version >= 8, f"MySQL版本过低: {version}"
                print(f"✓ MySQL版本: {version}")
        except Exception as e:
            pytest.fail(f"MySQL版本检查失败: {str(e)}")

    def test_database_tables(self):
        """检查数据库表是否存在"""
        required_tables = [
            'users',
            'products',
            'conversations',
            'messages',
            'roles',
            'permissions',
            'cultural_tags',
            'media_files',
        ]

        try:
            engine = create_engine(settings.DATABASE_URL)
            with engine.connect() as connection:
                result = connection.execute(text("SHOW TABLES"))
                existing_tables = [row[0] for row in result]

                missing_tables = [t for t in required_tables if t not in existing_tables]

                if missing_tables:
                    print(f"⚠ 缺少数据表: {', '.join(missing_tables)}")
                    print(f"提示: 请运行 'alembic upgrade head' 初始化数据库")
                else:
                    print(f"✓ 所有必要数据表已创建 ({len(existing_tables)}个表)")
        except Exception as e:
            pytest.fail(f"数据表检查失败: {str(e)}")

    def test_redis_connection(self):
        """测试Redis连接"""
        try:
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )

            # 测试ping
            assert r.ping(), "Redis ping失败"

            # 测试读写
            test_key = "_test_key_"
            r.set(test_key, "test_value", ex=10)
            assert r.get(test_key) == "test_value"
            r.delete(test_key)

            print(f"✓ Redis连接成功: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            pytest.fail(f"Redis连接失败: {str(e)}")

    def test_redis_version(self):
        """检查Redis版本 >= 7.0"""
        try:
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB
            )
            info = r.info()
            version = info['redis_version']
            major_version = int(version.split('.')[0])
            assert major_version >= 7, f"Redis版本过低: {version}"
            print(f"✓ Redis版本: {version}")
        except Exception as e:
            pytest.fail(f"Redis版本检查失败: {str(e)}")

    def test_upload_directory(self):
        """检查上传目录是否存在和可写"""
        upload_dir = Path(settings.UPLOAD_DIR)

        # 检查目录存在
        if not upload_dir.exists():
            print(f"⚠ 上传目录不存在，正在创建: {upload_dir}")
            upload_dir.mkdir(parents=True, exist_ok=True)

        # 检查可写
        test_file = upload_dir / ".test_write"
        try:
            test_file.write_text("test")
            test_file.unlink()
            print(f"✓ 上传目录可写: {upload_dir}")
        except Exception as e:
            pytest.fail(f"上传目录不可写: {str(e)}")

    def test_deepseek_api_key(self):
        """检查DeepSeek API密钥是否配置"""
        api_key = settings.DEEPSEEK_API_KEY

        if not api_key or api_key == "your-deepseek-api-key-here":
            print("⚠ DeepSeek API密钥未配置（跳过AI功能测试）")
        else:
            print(f"✓ DeepSeek API密钥已配置: {api_key[:10]}...")

    def test_dependencies(self):
        """检查关键依赖包是否安装"""
        required_packages = [
            'fastapi',
            'sqlalchemy',
            'redis',
            'pymysql',
            'pydantic',
            'jose',
            'passlib',
            'loguru',
            'alembic',
            'httpx',
            'pillow',
        ]

        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)

        assert len(missing_packages) == 0, f"缺少依赖包: {', '.join(missing_packages)}"
        print(f"✓ 所有关键依赖包已安装 ({len(required_packages)}个)")


if __name__ == "__main__":
    # 运行环境检查
    print("=" * 60)
    print("集成测试 - 环境检查")
    print("=" * 60)

    pytest.main([__file__, "-v", "-s"])
