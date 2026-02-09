"""
认证API测试用例

版本: 1.0
更新日期: 2026-01-17

运行: pytest tests/test_auth.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.api.deps import get_db


# ==================== 测试配置 ====================

@pytest.fixture(scope="function")
def db():
    """创建测试数据库会话"""
    # 这里应该配置测试数据库
    # 通常使用SQLite内存数据库或独立的测试数据库
    pass


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def test_user_data():
    """测试用户数据"""
    return {
        "username": "test_user",
        "email": "test@example.com",
        "phone": "13800138000",
        "password": "TestPassword123",
        "user_type": "personal",
        "verification_code": "123456"
    }


@pytest.fixture
def test_enterprise_data():
    """测试企业数据"""
    return {
        "username": "test_enterprise",
        "email": "enterprise@example.com",
        "phone": "13800138001",
        "password": "EnterprisePassword123",
        "user_type": "enterprise",
        "verification_code": "123456",
        "enterprise_name": "测试企业有限公司",
        "enterprise_license": "91150100MA0N1234X5"
    }


# ==================== 用户注册测试 ====================

class TestRegister:
    """用户注册测试"""

    def test_register_personal_user_success(self, client, test_user_data):
        """测试个人用户注册成功"""
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "注册成功"
        assert "data" in data
        assert data["data"]["username"] == "test_user"

    def test_register_enterprise_user_success(self, client, test_enterprise_data):
        """测试企业用户注册成功"""
        response = client.post("/api/v1/auth/register", json=test_enterprise_data)

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["user_type"] == "enterprise"

    def test_register_duplicate_username(self, client, test_user_data):
        """测试用户名重复注册失败"""
        # 第一次注册
        client.post("/api/v1/auth/register", json=test_user_data)

        # 第二次注册相同用户名
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 400
        data = response.json()
        assert data["code"] == 10001  # 参数验证失败

    def test_register_invalid_password(self, client, test_user_data):
        """测试无效密码（太短）"""
        test_user_data["password"] = "short"
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 422  # FastAPI验证错误

    def test_register_missing_email_and_phone(self, client, test_user_data):
        """测试邮箱和手机号都缺失"""
        del test_user_data["email"]
        del test_user_data["phone"]

        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 422  # FastAPI验证错误

    def test_register_invalid_verification_code(self, client, test_user_data):
        """测试无效验证码"""
        test_user_data["verification_code"] = "wrong_code"
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 400
        data = response.json()
        assert "验证码" in data["message"]


# ==================== 用户登录测试 ====================

class TestLogin:
    """用户登录测试"""

    def test_login_success(self, client, test_user_data):
        """测试登录成功"""
        # 先注册
        client.post("/api/v1/auth/register", json=test_user_data)

        # 再登录
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "登录成功"
        assert "data" in data
        assert "tokens" in data["data"]
        assert "access_token" in data["data"]["tokens"]
        assert "refresh_token" in data["data"]["tokens"]

    def test_login_with_email(self, client, test_user_data):
        """测试使用邮箱登录"""
        client.post("/api/v1/auth/register", json=test_user_data)

        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        assert response.json()["code"] == 200

    def test_login_with_phone(self, client, test_user_data):
        """测试使用手机号登录"""
        client.post("/api/v1/auth/register", json=test_user_data)

        login_data = {
            "username": test_user_data["phone"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        assert response.json()["code"] == 200

    def test_login_user_not_found(self, client):
        """测试用户不存在"""
        login_data = {
            "username": "nonexistent",
            "password": "Password123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 404
        data = response.json()
        assert data["code"] == 20010  # 用户不存在

    def test_login_wrong_password(self, client, test_user_data):
        """测试密码错误"""
        client.post("/api/v1/auth/register", json=test_user_data)

        login_data = {
            "username": test_user_data["username"],
            "password": "WrongPassword123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == 20011  # 密码错误

    def test_login_multiple_failed_attempts(self, client, test_user_data):
        """测试多次失败登录锁定账号"""
        client.post("/api/v1/auth/register", json=test_user_data)

        login_data = {
            "username": test_user_data["username"],
            "password": "WrongPassword"
        }

        # 尝试5次失败登录
        for _ in range(5):
            response = client.post("/api/v1/auth/login", json=login_data)
            assert response.status_code == 401

        # 第6次应该返回账号被锁定
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == 20013  # 账号已锁定


# ==================== Token刷新测试 ====================

class TestRefresh:
    """Token刷新测试"""

    def test_refresh_token_success(self, client, test_user_data):
        """测试刷新Token成功"""
        # 注册和登录
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        old_refresh_token = login_response.json()["data"]["tokens"]["refresh_token"]

        # 刷新Token
        refresh_data = {"refresh_token": old_refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        # 新token应该不同于旧token
        assert data["data"]["refresh_token"] != old_refresh_token

    def test_refresh_invalid_token(self, client):
        """测试无效的刷新Token"""
        refresh_data = {"refresh_token": "invalid_token"}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == 20005  # 刷新Token无效


# ==================== 获取用户信息测试 ====================

class TestGetMe:
    """获取当前用户信息测试"""

    def test_get_me_success(self, client, test_user_data):
        """测试获取当前用户信息成功"""
        # 注册和登录
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        access_token = login_response.json()["data"]["tokens"]["access_token"]

        # 获取用户信息
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["username"] == test_user_data["username"]

    def test_get_me_without_token(self, client):
        """测试不提供Token"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == 20001  # Token缺失

    def test_get_me_with_invalid_token(self, client):
        """测试使用无效Token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == 20002  # Token无效


# ==================== 修改密码测试 ====================

class TestChangePassword:
    """修改密码测试"""

    def test_change_password_success(self, client, test_user_data):
        """测试修改密码成功"""
        # 注册和登录
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        access_token = login_response.json()["data"]["tokens"]["access_token"]

        # 修改密码
        headers = {"Authorization": f"Bearer {access_token}"}
        change_data = {
            "old_password": test_user_data["password"],
            "new_password": "NewPassword123"
        }
        response = client.post("/api/v1/auth/change-password", json=change_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

        # 使用新密码登录
        login_response = client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": "NewPassword123"
        })
        assert login_response.status_code == 200

    def test_change_password_wrong_old_password(self, client, test_user_data):
        """测试旧密码错误"""
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        access_token = login_response.json()["data"]["tokens"]["access_token"]

        headers = {"Authorization": f"Bearer {access_token}"}
        change_data = {
            "old_password": "WrongPassword",
            "new_password": "NewPassword123"
        }
        response = client.post("/api/v1/auth/change-password", json=change_data, headers=headers)

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == 20011  # 密码错误


# ==================== 登出测试 ====================

class TestLogout:
    """用户登出测试"""

    def test_logout_success(self, client, test_user_data):
        """测试登出成功"""
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        access_token = login_response.json()["data"]["tokens"]["access_token"]

        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post("/api/v1/auth/logout", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
