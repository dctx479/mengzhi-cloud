"""
认证API路由单元测试

测试内容：
- 用户注册端点
- 用户登录端点
- Token刷新端点
- 用户登出端点
- 获取用户信息端点
- 修改密码端点

运行: pytest tests/test_auth_api.py -v
"""

import pytest
from unittest.mock import patch
from sqlalchemy import text

from app.services.auth_service import AuthService
from app.core.config import settings


# ==================== 注册端点测试 ====================

class TestRegisterEndpoint:
    """注册端点功能测试"""

    @pytest.mark.unit
    def test_register_personal_user_success(self, client, test_db_session, test_user_data):
        """测试个人用户注册成功"""
        # Mock验证码验证
        with patch('app.services.auth_service.AuthService.verify_code', return_value=True):
            response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "注册成功"
        assert data["data"]["username"] == test_user_data["username"]

    @pytest.mark.unit
    def test_register_enterprise_user_success(self, client, test_db_session, test_enterprise_user_data):
        """测试企业用户注册成功"""
        with patch('app.services.auth_service.AuthService.verify_code', return_value=True):
            response = client.post("/api/v1/auth/register", json=test_enterprise_user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["user_type"] == "enterprise"

    @pytest.mark.unit
    def test_register_invalid_verification_code(self, client, test_db_session, test_user_data):
        """测试无效验证码"""
        with patch('app.services.auth_service.AuthService.verify_code', side_effect=Exception("Invalid code")):
            response = client.post("/api/v1/auth/register", json=test_user_data)

        # 应该返回验证码相关错误
        assert response.status_code in [400, 422]

    @pytest.mark.unit
    def test_register_duplicate_username(self, client, test_db_session, test_user_data):
        """测试用户名重复"""
        # 首先注册
        with patch('app.services.auth_service.AuthService.verify_code', return_value=True):
            response1 = client.post("/api/v1/auth/register", json=test_user_data)
            assert response1.status_code == 201

        # 再次注册相同用户名
        with patch('app.services.auth_service.AuthService.verify_code', return_value=True):
            response2 = client.post("/api/v1/auth/register", json=test_user_data)

        # 应该返回400错误
        assert response2.status_code == 400

    @pytest.mark.unit
    def test_register_missing_email_and_phone(self, client, test_user_data):
        """测试缺少邮箱和手机号"""
        incomplete_data = {
            "username": "testuser",
            "password": "TestPassword123!",
            "user_type": "personal",
            "verification_code": "123456"
        }

        response = client.post("/api/v1/auth/register", json=incomplete_data)

        # 应该返回422验证错误
        assert response.status_code == 422


# ==================== 登录端点测试 ====================

class TestLoginEndpoint:
    """登录端点功能测试"""

    @pytest.mark.unit
    def test_login_success(self, client, test_db_session, test_user_data):
        """测试登录成功"""
        # 先创建用户
        user_uuid = "test-uuid-123"
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

        # 登录
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
        assert "tokens" in data["data"]
        assert "access_token" in data["data"]["tokens"]

    @pytest.mark.unit
    def test_login_with_email(self, client, test_db_session, test_user_data):
        """测试使用邮箱登录"""
        user_uuid = "test-uuid-123"
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

        # 使用邮箱登录
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200

    @pytest.mark.unit
    def test_login_user_not_found(self, client):
        """测试用户不存在"""
        login_data = {
            "username": "nonexistent",
            "password": "Password123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 404

    @pytest.mark.unit
    def test_login_wrong_password(self, client, test_db_session, test_user_data):
        """测试密码错误"""
        user_uuid = "test-uuid-123"
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

        login_data = {
            "username": test_user_data["username"],
            "password": "WrongPassword123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401


# ==================== Token刷新端点测试 ====================

class TestRefreshEndpoint:
    """Token刷新端点功能测试"""

    @pytest.mark.unit
    def test_refresh_token_success(self, client, test_db_session, test_user_token):
        """测试Token刷新成功"""
        _, refresh_token, _ = test_user_token

        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

    @pytest.mark.unit
    def test_refresh_invalid_token(self, client):
        """测试无效的刷新Token"""
        refresh_data = {"refresh_token": "invalid_token"}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 401


# ==================== 获取用户信息端点测试 ====================

class TestGetMeEndpoint:
    """获取当前用户信息端点功能测试"""

    @pytest.mark.unit
    def test_get_me_success(self, client, test_user_token):
        """测试获取用户信息成功"""
        access_token, _, _ = test_user_token

        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data

    @pytest.mark.unit
    def test_get_me_without_token(self, client):
        """测试不提供Token"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.unit
    def test_get_me_with_invalid_token(self, client):
        """测试使用无效Token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 401

    @pytest.mark.unit
    def test_get_me_with_malformed_header(self, client):
        """测试格式错误的Authorization header"""
        headers = {"Authorization": "InvalidFormat"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 401


# ==================== 修改密码端点测试 ====================

class TestChangePasswordEndpoint:
    """修改密码端点功能测试"""

    @pytest.mark.unit
    def test_change_password_success(self, client, test_db_session, test_user_token, test_user_data):
        """测试修改密码成功"""
        access_token, _, _ = test_user_token

        headers = {"Authorization": f"Bearer {access_token}"}
        change_data = {
            "old_password": test_user_data["password"],
            "new_password": "NewPassword123!"
        }
        response = client.post("/api/v1/auth/change-password", json=change_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.unit
    def test_change_password_wrong_old_password(self, client, test_user_token):
        """测试旧密码错误"""
        access_token, _, _ = test_user_token

        headers = {"Authorization": f"Bearer {access_token}"}
        change_data = {
            "old_password": "WrongPassword",
            "new_password": "NewPassword123!"
        }
        response = client.post("/api/v1/auth/change-password", json=change_data, headers=headers)

        assert response.status_code == 401

    @pytest.mark.unit
    def test_change_password_without_token(self, client):
        """测试不提供Token"""
        change_data = {
            "old_password": "OldPassword123!",
            "new_password": "NewPassword123!"
        }
        response = client.post("/api/v1/auth/change-password", json=change_data)

        assert response.status_code == 401


# ==================== 登出端点测试 ====================

class TestLogoutEndpoint:
    """登出端点功能测试"""

    @pytest.mark.unit
    def test_logout_success(self, client, test_user_token):
        """测试登出成功"""
        access_token, _, _ = test_user_token

        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post("/api/v1/auth/logout", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.unit
    def test_logout_without_token(self, client):
        """测试不提供Token"""
        response = client.post("/api/v1/auth/logout")

        # 登出即使没有token也应该返回200
        assert response.status_code in [200, 401]


# ==================== 更新用户信息端点测试 ====================

class TestUpdateProfileEndpoint:
    """更新用户信息端点功能测试"""

    @pytest.mark.unit
    def test_update_profile_success(self, client, test_user_token):
        """测试更新用户信息成功"""
        access_token, _, _ = test_user_token

        headers = {"Authorization": f"Bearer {access_token}"}
        update_data = {
            "nickname": "张三",
            "gender": 1
        }
        response = client.put("/api/v1/auth/me", json=update_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

    @pytest.mark.unit
    def test_update_profile_without_token(self, client):
        """测试不提供Token"""
        update_data = {"nickname": "张三"}
        response = client.put("/api/v1/auth/me", json=update_data)

        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
