"""
Pytest配置和全局Fixtures

包含：
- 数据库会话设置
- 测试客户端
- 模拟数据
- 认证fixture
"""

import pytest
import os
from datetime import datetime
from typing import Generator
from unittest.mock import Mock, patch, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# 导入应用和配置
from app.main import app
from app.core.database import Base
from app.api.deps import get_db, SessionLocal
from app.services.auth_service import AuthService


# ==================== 数据库配置 ====================

# 使用SQLite内存数据库进行测试
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_db_engine():
    """创建测试数据库引擎（会话级别）"""
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    yield engine

    # 清理
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """创建测试数据库会话（函数级别）"""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()

    yield session

    # 回滚事务，恢复数据库状态
    try:
        session.close()
    except Exception:
        pass
    try:
        transaction.rollback()
    except Exception:
        pass
    try:
        connection.close()
    except Exception:
        pass


@pytest.fixture
def db_override(test_db_session):
    """覆盖FastAPI依赖中的get_db"""
    def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db
    yield test_db_session
    del app.dependency_overrides[get_db]


# ==================== 客户端配置 ====================

@pytest.fixture
def client(db_override):
    """创建测试客户端"""
    return TestClient(app)


# ==================== 认证和用户数据 ====================

@pytest.fixture
def test_user_data():
    """基础测试用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "phone": "13800138000",
        "password": "TestPassword123!",
        "user_type": "personal",
        "verification_code": "123456"
    }


@pytest.fixture
def test_enterprise_user_data():
    """测试企业用户数据"""
    return {
        "username": "enterprise_user",
        "email": "enterprise@example.com",
        "phone": "13800138001",
        "password": "EnterprisePassword123!",
        "user_type": "enterprise",
        "verification_code": "123456",
        "enterprise_name": "测试企业有限公司",
        "enterprise_license": "91150100MA0N1234X5"
    }


@pytest.fixture
def test_user_token(client, test_user_data, test_db_session):
    """获取测试用户的认证Token"""
    # 注册用户
    from sqlalchemy import text
    import uuid

    user_uuid = str(uuid.uuid4())
    password_hash = AuthService.hash_password(test_user_data["password"])

    test_db_session.execute(
        text("""
            INSERT INTO users (
                user_uuid, username, email, phone, password_hash,
                user_type, status, role, created_at, updated_at
            ) VALUES (
                :user_uuid, :username, :email, :phone, :password_hash,
                :user_type, :status, :role, NOW(), NOW()
            )
        """),
        {
            "user_uuid": user_uuid,
            "username": test_user_data["username"],
            "email": test_user_data["email"],
            "phone": test_user_data["phone"],
            "password_hash": password_hash,
            "user_type": test_user_data["user_type"],
            "status": "active",
            "role": "user"
        }
    )
    test_db_session.commit()

    # 登录获取Token
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
    )

    # 验证登录响应
    assert login_response.status_code == 200, (
        f"Login failed with status {login_response.status_code}: {login_response.text}"
    )

    response_data = login_response.json()
    assert response_data.get("code") == 200, (
        f"Login failed with code {response_data.get('code')}: {response_data.get('message')}"
    )
    assert "data" in response_data and "tokens" in response_data["data"], (
        "Invalid login response structure: missing 'data.tokens'"
    )

    tokens = response_data["data"]["tokens"]
    assert "access_token" in tokens and "refresh_token" in tokens, (
        "Invalid tokens structure: missing 'access_token' or 'refresh_token'"
    )

    return tokens["access_token"], tokens["refresh_token"], user_uuid


@pytest.fixture
def auth_headers(test_user_token):
    """获取带有授权Header的字典"""
    access_token = test_user_token[0]
    return {"Authorization": f"Bearer {access_token}"}


# ==================== 模拟数据 ====================

@pytest.fixture
def mock_redis():
    """模拟Redis客户端"""
    mock = MagicMock()
    mock.exists.return_value = False
    mock.get.return_value = None
    mock.setex.return_value = True
    mock.delete.return_value = True
    return mock


@pytest.fixture
def mock_deepseek_client():
    """模拟DeepSeek AI客户端"""
    mock = MagicMock()
    mock.health_check.return_value = True
    mock.generate_content.return_value = "这是AI生成的响应内容"
    mock.count_tokens.return_value = 100
    return mock


@pytest.fixture
def mock_email_service():
    """模拟邮件服务"""
    mock = MagicMock()
    mock.send_verification_code.return_value = True
    mock.send_reset_password_link.return_value = True
    return mock


# ==================== 产品测试数据 ====================

@pytest.fixture
def test_product_data():
    """测试产品数据"""
    return {
        "sku": "PROD-001",
        "name": "内蒙古羊肉",
        "category": "肉类",
        "price": 99.99,
        "cost": 50.00,
        "stock": 100,
        "region": "内蒙古",
        "region_code": "15",
        "cultural_tags": ["有机", "草原"],
        "cultural_description": "来自内蒙古草原的优质羊肉",
        "origin_story": "传统畜牧业产品",
        "efficacy": "营养丰富",
        "usage": "烤羊肉",
        "status": "published",
        "is_featured": True
    }


@pytest.fixture
def test_product_data_multiple():
    """测试产品数据（多个）"""
    return [
        {
            "sku": f"PROD-00{i}",
            "name": f"产品{i}",
            "category": "肉类" if i % 2 == 0 else "乳制品",
            "price": 50.00 + i * 10,
            "cost": 20.00 + i * 5,
            "stock": 100 + i * 10,
            "region": "内蒙古",
            "region_code": "15",
            "cultural_tags": ["优质", "正宗"],
            "cultural_description": f"优质产品{i}",
            "origin_story": f"产品{i}的故事",
            "efficacy": "营养丰富",
            "usage": "食用",
            "status": "published",
            "is_featured": i < 3  # 前3个产品为精选
        }
        for i in range(1, 6)
    ]


# ==================== AI对话测试数据 ====================

@pytest.fixture
def test_conversation_data():
    """测试对话数据"""
    return {
        "title": "农产品营销方案",
        "agent_type": "marketing_expert",
        "product_id": 1,
        "metadata": {
            "platform": "wechat",
            "tone": "professional"
        }
    }


@pytest.fixture
def test_message_data():
    """测试消息数据"""
    return {
        "content": "请帮我制定羊肉产品的营销方案",
        "content_type": "text",
        "role": "user"
    }


# ==================== 工具函数 ====================

@pytest.fixture
def clean_db(test_db_session):
    """清理数据库工具"""
    def _clean():
        from sqlalchemy import text
        from sqlalchemy.exc import OperationalError

        # 清理所有表
        tables = [
            "user_quotas",
            "generation_templates",
            "content_records",
            "conversations",
            "messages",
            "products",
            "enterprises",
            "users"
        ]
        for table in tables:
            try:
                test_db_session.execute(text(f"DELETE FROM {table}"))
            except OperationalError:
                # 表不存在，跳过
                pass
        test_db_session.commit()

    return _clean


# ==================== 补丁配置 ====================

@pytest.fixture
def patch_redis(mock_redis):
    """补丁Redis客户端"""
    with patch("app.services.auth_service.redis.Redis") as mock:
        mock.return_value = mock_redis
        yield mock_redis


@pytest.fixture
def patch_deepseek(mock_deepseek_client):
    """补丁DeepSeek客户端"""
    with patch("app.services.ai.deepseek_client.DeepSeekClient") as mock:
        mock.return_value = mock_deepseek_client
        yield mock_deepseek_client


@pytest.fixture
def patch_email(mock_email_service):
    """补丁邮件服务"""
    with patch("app.services.email_service.EmailService") as mock:
        mock.return_value = mock_email_service
        yield mock_email_service


# ==================== Marker注册 ====================

def pytest_configure(config):
    """注册自定义markers"""
    config.addinivalue_line(
        "markers", "unit: 单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试"
    )


# ==================== 钩子函数 ====================

def pytest_collection_modifyitems(config, items):
    """修改测试收集行为"""
    for item in items:
        # 根据文件名自动标记
        if "test_auth" in item.nodeid:
            item.add_marker(pytest.mark.auth)
        elif "test_product" in item.nodeid:
            item.add_marker(pytest.mark.product)
        elif "test_chat" in item.nodeid:
            item.add_marker(pytest.mark.chat)
        elif "test_model" in item.nodeid:
            item.add_marker(pytest.mark.models)


__all__ = [
    "test_db_engine",
    "test_db_session",
    "db_override",
    "client",
    "test_user_data",
    "test_enterprise_user_data",
    "test_user_token",
    "auth_headers",
    "mock_redis",
    "mock_deepseek_client",
    "mock_email_service",
    "test_product_data",
    "test_product_data_multiple",
    "test_conversation_data",
    "test_message_data",
    "clean_db",
    "patch_redis",
    "patch_deepseek",
    "patch_email",
]
