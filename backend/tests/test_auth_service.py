"""
认证服务单元测试

测试内容：
- 密码哈希和验证
- Token生成和验证
- Token刷新
- 账号状态检查
- 验证码管理
- 数据脱敏
- 用户缓存

运行: pytest tests/test_auth_service.py -v
"""

import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from sqlalchemy.orm import Session

from app.services.auth_service import AuthService
from app.core.config import settings
from app.core.cache_manager import cache
from app.core.errors import (
    BusinessException,
    UserNotFoundError,
    PasswordIncorrectError,
    AccountDisabledError,
    AccountLockedError,
    TokenExpiredError,
    ErrorCode,
)


# ==================== 密码处理测试 ====================

class TestPasswordHandling:
    """密码处理功能测试"""

    @pytest.mark.unit
    def test_hash_password_creates_hash(self):
        """测试密码哈希生成"""
        password = "TestPassword123!"
        hashed = AuthService.hash_password(password)

        # 应该生成hash而不是明文
        assert hashed != password
        assert len(hashed) > 20
        assert hashed.startswith("$2b$")  # bcrypt标识

    @pytest.mark.unit
    def test_hash_password_different_each_time(self):
        """测试相同密码生成不同hash"""
        password = "TestPassword123!"
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)

        # 由于bcrypt使用随机salt，相同密码应该生成不同hash
        assert hash1 != hash2

    @pytest.mark.unit
    def test_verify_password_correct(self):
        """测试正确密码验证"""
        password = "TestPassword123!"
        hashed = AuthService.hash_password(password)

        # 验证应该成功
        assert AuthService.verify_password(password, hashed) is True

    @pytest.mark.unit
    def test_verify_password_incorrect(self):
        """测试错误密码验证"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = AuthService.hash_password(password)

        # 验证应该失败
        assert AuthService.verify_password(wrong_password, hashed) is False

    @pytest.mark.unit
    def test_verify_password_case_sensitive(self):
        """测试密码区分大小写"""
        password = "TestPassword123!"
        hashed = AuthService.hash_password(password)

        # 大小写不同应该验证失败
        assert AuthService.verify_password(password.lower(), hashed) is False
        assert AuthService.verify_password(password.upper(), hashed) is False


# ==================== Token生成和验证测试 ====================

class TestTokenGeneration:
    """Token生成功能测试"""

    @pytest.mark.unit
    def test_create_access_token(self, test_db_session):
        """测试创建Access Token"""
        auth_service = AuthService(test_db_session)

        token = auth_service.create_access_token(
            user_id="user-123",
            user_type="personal",
            role="user"
        )

        # 应该返回有效的JWT token
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50

    @pytest.mark.unit
    def test_access_token_contains_payload(self, test_db_session):
        """测试Access Token包含正确的载荷"""
        auth_service = AuthService(test_db_session)
        user_id = "user-123"
        user_type = "enterprise"
        role = "admin"

        token = auth_service.create_access_token(
            user_id=user_id,
            user_type=user_type,
            role=role
        )

        # 解码token验证载荷
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == user_id
        assert payload["user_type"] == user_type
        assert payload["role"] == role
        assert payload["type"] == "access"

    @pytest.mark.unit
    def test_access_token_expiration(self, test_db_session):
        """测试Access Token有效期"""
        auth_service = AuthService(test_db_session)
        before = datetime.utcnow()

        token = auth_service.create_access_token(
            user_id="user-123",
            user_type="personal",
            role="user"
        )

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        after = datetime.utcnow()

        # 验证过期时间约为30分钟后
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_min = before + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES - 1)
        expected_max = after + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES + 1)

        assert expected_min <= exp_time <= expected_max

    @pytest.mark.unit
    def test_create_refresh_token(self, test_db_session):
        """测试创建Refresh Token"""
        auth_service = AuthService(test_db_session)

        token = auth_service.create_refresh_token(
            user_id="user-123",
            device_id="device-456",
            ip_address="192.168.1.1"
        )

        # 应该返回有效的JWT token
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50

    @pytest.mark.unit
    def test_refresh_token_contains_payload(self, test_db_session):
        """测试Refresh Token包含正确的载荷"""
        auth_service = AuthService(test_db_session)
        user_id = "user-123"
        device_id = "device-456"

        token = auth_service.create_refresh_token(
            user_id=user_id,
            device_id=device_id
        )

        # 解码token验证载荷
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert payload.get("device_id") == device_id

    @pytest.mark.unit
    def test_decode_token_success(self, test_db_session):
        """测试成功解码Token"""
        auth_service = AuthService(test_db_session)

        token = auth_service.create_access_token(
            user_id="user-123",
            user_type="personal",
            role="user"
        )

        # 使用mock redis避免黑名单检查
        with patch.object(auth_service, 'is_token_blacklisted', return_value=False):
            payload = auth_service.decode_token(token)

        assert payload["sub"] == "user-123"
        assert payload["user_type"] == "personal"
        assert payload["role"] == "user"

    @pytest.mark.unit
    def test_decode_token_expired(self, test_db_session):
        """测试解码过期Token"""
        auth_service = AuthService(test_db_session)

        # 创建一个已过期的token
        now = datetime.utcnow()
        payload = {
            "sub": "user-123",
            "iss": "ai-marketing-platform",
            "iat": now,
            "exp": now - timedelta(hours=1),  # 已过期
            "type": "access",
            "user_type": "personal",
            "role": "user",
            "jti": "test-jti"
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        # 应该抛出TokenExpiredError
        with pytest.raises(TokenExpiredError):
            auth_service.decode_token(token)

    @pytest.mark.unit
    def test_decode_token_invalid(self, test_db_session):
        """测试解码无效Token"""
        auth_service = AuthService(test_db_session)

        # 应该抛出BusinessException
        with pytest.raises(BusinessException):
            auth_service.decode_token("invalid-token")

    @pytest.mark.unit
    def test_decode_token_blacklisted(self, test_db_session):
        """测试解码被黑名单的Token"""
        auth_service = AuthService(test_db_session)

        token = auth_service.create_access_token(
            user_id="user-123",
            user_type="personal",
            role="user"
        )

        # Mock黑名单检查返回True
        with patch.object(auth_service, 'is_token_blacklisted', return_value=True):
            with pytest.raises(BusinessException) as exc_info:
                auth_service.decode_token(token)
            assert "已被撤销" in str(exc_info.value.message)


# ==================== Token黑名单管理 ====================

class TestTokenBlacklist:
    """Token黑名单功能测试"""

    @pytest.mark.unit
    def test_add_token_to_blacklist(self, test_db_session):
        """测试将Token加入黑名单"""
        auth_service = AuthService(test_db_session)

        with patch.object(auth_service, 'redis_client') as mock_redis:
            auth_service.add_token_to_blacklist("test-jti", 3600)
            mock_redis.setex.assert_called_once_with("token_blacklist:test-jti", 3600, "revoked")

    @pytest.mark.unit
    def test_is_token_blacklisted_true(self, test_db_session):
        """测试Token在黑名单中"""
        auth_service = AuthService(test_db_session)

        with patch.object(auth_service, 'redis_client') as mock_redis:
            mock_redis.exists.return_value = 1
            result = auth_service.is_token_blacklisted("test-jti")
            assert result is True

    @pytest.mark.unit
    def test_is_token_blacklisted_false(self, test_db_session):
        """测试Token不在黑名单中"""
        auth_service = AuthService(test_db_session)

        with patch.object(auth_service, 'redis_client') as mock_redis:
            mock_redis.exists.return_value = 0
            result = auth_service.is_token_blacklisted("test-jti")
            assert result is False

    @pytest.mark.unit
    def test_is_token_blacklisted_empty_jti(self, test_db_session):
        """测试空JTI"""
        auth_service = AuthService(test_db_session)

        result = auth_service.is_token_blacklisted("")
        assert result is False

        result = auth_service.is_token_blacklisted(None)
        assert result is False

    @pytest.mark.unit
    def test_is_token_blacklisted_redis_unavailable(self, test_db_session):
        """测试Redis不可用时检查黑名单"""
        auth_service = AuthService(test_db_session)
        auth_service.redis_client = None

        result = auth_service.is_token_blacklisted("test-jti")
        assert result is False

    @pytest.mark.unit
    def test_add_token_to_blacklist_redis_unavailable(self, test_db_session):
        """测试Redis不可用时添加到黑名单"""
        auth_service = AuthService(test_db_session)
        auth_service.redis_client = None

        # 不应该抛出异常，只是记录日志
        auth_service.add_token_to_blacklist("test-jti", 3600)

    @pytest.mark.unit
    def test_is_token_blacklisted_redis_connection_error(self, test_db_session):
        """测试Redis连接错误时检查黑名单"""
        import redis
        auth_service = AuthService(test_db_session)

        with patch.object(auth_service, 'redis_client') as mock_redis:
            mock_redis.exists.side_effect = redis.ConnectionError("Connection failed")
            result = auth_service.is_token_blacklisted("test-jti")
            assert result is False  # 出错时返回False


# ==================== Token刷新 ====================

class TestTokenRefresh:
    """Token刷新功能测试"""

    @pytest.mark.unit
    def test_refresh_tokens_success(self, test_db_session):
        """测试成功刷新Token"""
        auth_service = AuthService(test_db_session)

        # 创建refresh token
        refresh_token = auth_service.create_refresh_token(user_id="user-123")

        # Mock用户查询
        mock_user = MagicMock()
        mock_user.user_uuid = "user-123"
        mock_user.user_type = "personal"
        mock_user.role = "user"
        mock_user.enterprise_id = None

        with patch.object(auth_service, '_get_user_by_id', return_value=mock_user):
            with patch.object(auth_service, 'is_token_blacklisted', return_value=False):
                new_access_token, new_refresh_token = auth_service.refresh_tokens(refresh_token)

        # 应该返回新的access token和refresh token
        assert new_access_token is not None
        assert new_refresh_token is not None
        assert new_access_token != "error"

    @pytest.mark.unit
    def test_refresh_token_expired(self, test_db_session):
        """测试过期的Refresh Token"""
        auth_service = AuthService(test_db_session)

        # 创建一个已过期的refresh token
        now = datetime.utcnow()
        payload = {
            "sub": "user-123",
            "iss": "ai-marketing-platform",
            "iat": now,
            "exp": now - timedelta(hours=1),  # 已过期
            "type": "refresh",
            "jti": "test-jti"
        }
        refresh_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        # 应该抛出BusinessException
        with pytest.raises(BusinessException) as exc_info:
            auth_service.refresh_tokens(refresh_token)
        assert exc_info.value.code == ErrorCode.REFRESH_TOKEN_EXPIRED

    @pytest.mark.unit
    def test_refresh_token_user_not_found(self, test_db_session):
        """测试用户不存在"""
        auth_service = AuthService(test_db_session)

        refresh_token = auth_service.create_refresh_token(user_id="nonexistent")

        with patch.object(auth_service, 'is_token_blacklisted', return_value=False):
            with patch.object(auth_service, '_get_user_by_id', return_value=None):
                with pytest.raises(UserNotFoundError):
                    auth_service.refresh_tokens(refresh_token)

    @pytest.mark.unit
    def test_refresh_token_wrong_type(self, test_db_session):
        """测试使用access token作为refresh token"""
        auth_service = AuthService(test_db_session)

        # 创建access token而非refresh token
        access_token = auth_service.create_access_token(
            user_id="user-123",
            user_type="personal",
            role="user"
        )

        with patch.object(auth_service, 'is_token_blacklisted', return_value=False):
            with pytest.raises(BusinessException) as exc_info:
                auth_service.refresh_tokens(access_token)
            assert exc_info.value.code == ErrorCode.REFRESH_TOKEN_INVALID
            assert "无效的刷新令牌类型" in str(exc_info.value.message)

    @pytest.mark.unit
    def test_refresh_token_blacklisted(self, test_db_session):
        """测试刷新被撤销的refresh token"""
        auth_service = AuthService(test_db_session)

        refresh_token = auth_service.create_refresh_token(user_id="user-123")

        with patch.object(auth_service, 'is_token_blacklisted', return_value=True):
            with pytest.raises(BusinessException) as exc_info:
                auth_service.refresh_tokens(refresh_token)
            assert exc_info.value.code == ErrorCode.TOKEN_REVOKED
            assert "已被撤销" in str(exc_info.value.message)

    @pytest.mark.unit
    def test_refresh_token_invalid_format(self, test_db_session):
        """测试无效格式的refresh token"""
        auth_service = AuthService(test_db_session)

        with pytest.raises(BusinessException) as exc_info:
            auth_service.refresh_tokens("invalid-token-format")
        assert exc_info.value.code == ErrorCode.REFRESH_TOKEN_INVALID

    @pytest.mark.unit
    def test_refresh_token_with_tenant_id(self, test_db_session):
        """测试刷新企业用户的token"""
        auth_service = AuthService(test_db_session)

        refresh_token = auth_service.create_refresh_token(
            user_id="user-123",
            device_id="device-456"
        )

        # Mock企业用户
        mock_user = MagicMock()
        mock_user.user_uuid = "user-123"
        mock_user.user_type = "enterprise"
        mock_user.role = "admin"
        mock_user.enterprise_id = "enterprise-789"

        with patch.object(auth_service, '_get_user_by_id', return_value=mock_user):
            with patch.object(auth_service, 'is_token_blacklisted', return_value=False):
                new_access_token, new_refresh_token = auth_service.refresh_tokens(refresh_token)

        # 验证新token包含tenant_id
        payload = jwt.decode(new_access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload.get("tenant_id") == "enterprise-789"


# ==================== 账号状态检查 ====================

class TestAccountStatusCheck:
    """账号状态检查功能测试"""

    @pytest.mark.unit
    def test_check_account_status_active(self, test_db_session):
        """测试正常账号状态"""
        auth_service = AuthService(test_db_session)

        mock_user = MagicMock()
        mock_user.status = "active"
        mock_user.locked_until = None

        # 不应该抛出异常
        auth_service.check_account_status(mock_user)

    @pytest.mark.unit
    def test_check_account_status_banned(self, test_db_session):
        """测试被禁用的账号"""
        auth_service = AuthService(test_db_session)

        mock_user = MagicMock()
        mock_user.status = "banned"
        mock_user.locked_until = None

        # 应该抛出AccountDisabledError
        with pytest.raises(AccountDisabledError):
            auth_service.check_account_status(mock_user)

    @pytest.mark.unit
    def test_check_account_status_locked(self, test_db_session):
        """测试被锁定的账号"""
        auth_service = AuthService(test_db_session)

        mock_user = MagicMock()
        mock_user.status = "active"
        # 锁定时间为未来
        mock_user.locked_until = (datetime.utcnow() + timedelta(minutes=30)).isoformat()

        # 应该抛出AccountLockedError
        with pytest.raises(AccountLockedError):
            auth_service.check_account_status(mock_user)

    @pytest.mark.unit
    def test_check_account_status_lock_expired(self, test_db_session):
        """测试锁定期已过期"""
        auth_service = AuthService(test_db_session)

        mock_user = MagicMock()
        mock_user.status = "active"
        # 锁定时间为过去
        mock_user.locked_until = (datetime.utcnow() - timedelta(minutes=30)).isoformat()

        # 不应该抛出异常
        auth_service.check_account_status(mock_user)


# ==================== 登录尝试检查 ====================

class TestLoginAttempts:
    """登录尝试检查功能测试"""

    @pytest.mark.unit
    def test_check_and_update_login_attempts_success(self, test_db_session):
        """测试成功登录重置尝试次数"""
        auth_service = AuthService(test_db_session)

        with patch.object(test_db_session, 'execute') as mock_execute:
            with patch.object(test_db_session, 'commit'):
                auth_service.check_and_update_login_attempts(user_id=1, success=True)

        # 应该执行UPDATE语句
        mock_execute.assert_called()

    @pytest.mark.unit
    def test_check_and_update_login_attempts_failure(self, test_db_session):
        """测试失败登录增加尝试次数"""
        auth_service = AuthService(test_db_session)

        with patch.object(test_db_session, 'execute') as mock_execute:
            with patch.object(test_db_session, 'commit'):
                auth_service.check_and_update_login_attempts(user_id=1, success=False)

        # 应该执行UPDATE语句增加尝试次数
        mock_execute.assert_called()

    @pytest.mark.unit
    def test_check_and_update_login_attempts_lock_account(self, test_db_session):
        """测试5次失败后锁定账号"""
        auth_service = AuthService(test_db_session)

        # Mock返回5次失败尝试
        mock_result = MagicMock()
        mock_result.__getitem__.return_value = 5

        with patch.object(test_db_session, 'execute') as mock_execute:
            mock_execute.return_value.first.return_value = mock_result
            with patch.object(test_db_session, 'commit'):
                auth_service.check_and_update_login_attempts(user_id=1, success=False)

        # 应该执行锁定账号的UPDATE语句
        assert mock_execute.call_count >= 2  # increment + lock


# ==================== 用户查询 ====================

class TestUserQuery:
    """用户查询功能测试"""

    @pytest.mark.unit
    def test_get_user_by_username(self, test_db_session):
        """测试根据用户名获取用户"""
        auth_service = AuthService(test_db_session)

        with patch.object(test_db_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_execute.return_value.first.return_value = mock_result

            user = auth_service.get_user_by_username("testuser")

        assert user is not None
        mock_execute.assert_called_once()

    @pytest.mark.unit
    def test_get_user_by_email(self, test_db_session):
        """测试根据邮箱获取用户"""
        auth_service = AuthService(test_db_session)

        with patch.object(test_db_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_execute.return_value.first.return_value = mock_result

            user = auth_service.get_user_by_email("test@example.com")

        assert user is not None
        mock_execute.assert_called_once()

    @pytest.mark.unit
    def test_get_user_by_phone(self, test_db_session):
        """测试根据手机号获取用户"""
        auth_service = AuthService(test_db_session)

        with patch.object(test_db_session, 'execute') as mock_execute:
            mock_result = MagicMock()
            mock_execute.return_value.first.return_value = mock_result

            user = auth_service.get_user_by_phone("13800138000")

        assert user is not None
        mock_execute.assert_called_once()


# ==================== 验证码管理 ====================

class TestVerificationCode:
    """验证码管理功能测试"""

    @pytest.mark.unit
    def test_set_verification_code(self, test_db_session):
        """测试设置验证码"""
        auth_service = AuthService(test_db_session)

        with patch.object(auth_service, 'redis_client') as mock_redis:
            auth_service.set_verification_code(
                identifier="test@example.com",
                code_type="register",
                code="123456",
                ttl=300
            )

            mock_redis.setex.assert_called_once_with(
                "verify_code:test@example.com:register",
                300,
                "123456"
            )

    @pytest.mark.unit
    def test_verify_code_success(self, test_db_session):
        """测试验证码验证成功"""
        auth_service = AuthService(test_db_session)

        with patch.object(auth_service, 'redis_client') as mock_redis:
            mock_redis.get.return_value = "123456"
            result = auth_service.verify_code(
                identifier="test@example.com",
                code_type="register",
                code="123456"
            )

            assert result is True
            mock_redis.delete.assert_called_once()

    @pytest.mark.unit
    def test_verify_code_incorrect(self, test_db_session):
        """测试验证码不匹配"""
        auth_service = AuthService(test_db_session)

        with patch.object(auth_service, 'redis_client') as mock_redis:
            mock_redis.get.return_value = "123456"
            with pytest.raises(BusinessException):
                auth_service.verify_code(
                    identifier="test@example.com",
                    code_type="register",
                    code="wrong_code"
                )

    @pytest.mark.unit
    def test_verify_code_expired(self, test_db_session):
        """测试验证码已过期"""
        auth_service = AuthService(test_db_session)

        with patch.object(auth_service, 'redis_client') as mock_redis:
            mock_redis.get.return_value = None
            with pytest.raises(BusinessException):
                auth_service.verify_code(
                    identifier="test@example.com",
                    code_type="register",
                    code="123456"
                )

    @pytest.mark.unit
    def test_verify_code_bytes_stored(self, test_db_session):
        """测试验证码以bytes形式存储"""
        auth_service = AuthService(test_db_session)

        with patch.object(auth_service, 'redis_client') as mock_redis:
            # Redis返回bytes类型
            mock_redis.get.return_value = b"123456"
            result = auth_service.verify_code(
                identifier="test@example.com",
                code_type="register",
                code="123456"
            )

            assert result is True
            mock_redis.delete.assert_called_once()

    @pytest.mark.unit
    def test_set_verification_code_redis_unavailable(self, test_db_session):
        """测试Redis不可用时设置验证码"""
        auth_service = AuthService(test_db_session)
        auth_service.redis_client = None

        with pytest.raises(BusinessException) as exc_info:
            auth_service.set_verification_code(
                identifier="test@example.com",
                code_type="register",
                code="123456"
            )
        assert "验证码服务暂时不可用" in str(exc_info.value.message)

    @pytest.mark.unit
    def test_verify_code_redis_unavailable(self, test_db_session):
        """测试Redis不可用时验证验证码"""
        auth_service = AuthService(test_db_session)
        auth_service.redis_client = None

        with pytest.raises(BusinessException) as exc_info:
            auth_service.verify_code(
                identifier="test@example.com",
                code_type="register",
                code="123456"
            )
        assert "验证码服务暂时不可用" in str(exc_info.value.message)

    @pytest.mark.unit
    def test_set_verification_code_redis_connection_error(self, test_db_session):
        """测试Redis连接错误时设置验证码"""
        import redis
        auth_service = AuthService(test_db_session)

        with patch.object(auth_service, 'redis_client') as mock_redis:
            mock_redis.setex.side_effect = redis.ConnectionError("Connection failed")
            with pytest.raises(BusinessException) as exc_info:
                auth_service.set_verification_code(
                    identifier="test@example.com",
                    code_type="register",
                    code="123456"
                )
            assert "验证码服务暂时不可用" in str(exc_info.value.message)

    @pytest.mark.unit
    def test_verify_code_redis_connection_error(self, test_db_session):
        """测试Redis连接错误时验证验证码"""
        import redis
        auth_service = AuthService(test_db_session)

        with patch.object(auth_service, 'redis_client') as mock_redis:
            mock_redis.get.side_effect = redis.ConnectionError("Connection failed")
            with pytest.raises(BusinessException) as exc_info:
                auth_service.verify_code(
                    identifier="test@example.com",
                    code_type="register",
                    code="123456"
                )
            assert "验证码服务暂时不可用" in str(exc_info.value.message)


# ==================== 数据脱敏 ====================

class TestDataMasking:
    """数据脱敏功能测试"""

    @pytest.mark.unit
    def test_mask_phone_valid(self):
        """测试手机号脱敏"""
        phone = "13800138000"
        masked = AuthService.mask_phone(phone)

        assert masked == "138****8000"
        assert "138" in masked
        assert "8000" in masked

    @pytest.mark.unit
    def test_mask_phone_too_short(self):
        """测试短手机号"""
        phone = "123"
        masked = AuthService.mask_phone(phone)

        assert masked == "123"

    @pytest.mark.unit
    def test_mask_phone_none(self):
        """测试None手机号"""
        masked = AuthService.mask_phone(None)
        assert masked is None

    @pytest.mark.unit
    def test_mask_email_valid(self):
        """测试邮箱脱敏"""
        email = "test@example.com"
        masked = AuthService.mask_email(email)

        assert "***@example.com" in masked
        assert "test" not in masked

    @pytest.mark.unit
    def test_mask_email_short_local(self):
        """测试短本地部分邮箱"""
        email = "a@example.com"
        masked = AuthService.mask_email(email)

        assert "***@example.com" in masked

    @pytest.mark.unit
    def test_mask_email_invalid(self):
        """测试无效邮箱"""
        email = "invalid"
        masked = AuthService.mask_email(email)

        assert masked == "invalid"

    @pytest.mark.unit
    def test_mask_email_none(self):
        """测试None邮箱"""
        masked = AuthService.mask_email(None)
        assert masked is None


# ==================== 用户缓存测试 ====================

class TestUserCaching:
    """用户缓存功能测试"""

    @pytest.mark.unit
    def test_get_user_by_id_cached_hit(self, test_db_session):
        """测试缓存命中"""
        auth_service = AuthService(test_db_session)
        user_id = "user-123"

        # Mock缓存数据
        cached_user = {
            "id": 1,
            "user_uuid": user_id,
            "username": "testuser",
            "email": "test@example.com",
            "phone": "13800138000",
            "password_hash": "hashed_password",
            "user_type": "personal",
            "status": "active",
            "role": "user",
            "enterprise_id": None,
            "last_login_at": None
        }

        with patch.object(cache, 'get', return_value=cached_user):
            with patch.object(auth_service, '_get_user_by_id') as mock_db:
                user = auth_service.get_user_by_id_cached(user_id)

                # 应该返回缓存数据
                assert user is not None
                assert user == cached_user
                # 数据库不应该被调用
                mock_db.assert_not_called()

    @pytest.mark.unit
    def test_get_user_by_id_cached_miss(self, test_db_session):
        """测试缓存未命中"""
        auth_service = AuthService(test_db_session)
        user_id = "user-123"

        # Mock数据库返回
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.user_uuid = user_id
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.phone = "13800138000"
        mock_user.password_hash = "hashed_password"
        mock_user.user_type = "personal"
        mock_user.status = "active"
        mock_user.role = "user"
        mock_user.enterprise_id = None
        mock_user.last_login_at = None

        with patch.object(cache, 'get', return_value=None):
            with patch.object(cache, 'set') as mock_cache_set:
                with patch.object(auth_service, '_get_user_by_id', return_value=mock_user):
                    user = auth_service.get_user_by_id_cached(user_id)

                    # 应该返回数据库数据
                    assert user is not None
                    # 应该写入缓存
                    mock_cache_set.assert_called_once()
                    call_args = mock_cache_set.call_args
                    assert call_args[0][0] == f"user:{user_id}"

    @pytest.mark.unit
    def test_get_user_by_id_cached_user_not_found(self, test_db_session):
        """测试用户不存在"""
        auth_service = AuthService(test_db_session)
        user_id = "nonexistent"

        with patch.object(cache, 'get', return_value=None):
            with patch.object(cache, 'set') as mock_cache_set:
                with patch.object(auth_service, '_get_user_by_id', return_value=None):
                    user = auth_service.get_user_by_id_cached(user_id)

                    # 应该返回None
                    assert user is None
                    # 不应该写入缓存
                    mock_cache_set.assert_not_called()

    @pytest.mark.unit
    def test_get_user_by_id_cached_with_custom_ttl(self, test_db_session):
        """测试自定义TTL"""
        auth_service = AuthService(test_db_session)
        user_id = "user-123"
        custom_ttl = 7200  # 2小时

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.user_uuid = user_id
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.phone = "13800138000"
        mock_user.password_hash = "hashed_password"
        mock_user.user_type = "personal"
        mock_user.status = "active"
        mock_user.role = "user"
        mock_user.enterprise_id = None
        mock_user.last_login_at = None

        with patch.object(cache, 'get', return_value=None):
            with patch.object(cache, 'set') as mock_cache_set:
                with patch.object(auth_service, '_get_user_by_id', return_value=mock_user):
                    user = auth_service.get_user_by_id_cached(user_id, ttl_seconds=custom_ttl)

                    # 应该使用自定义TTL
                    call_args = mock_cache_set.call_args
                    assert call_args[1]['ttl_seconds'] == custom_ttl

    @pytest.mark.unit
    def test_get_user_by_id_cached_cache_read_error(self, test_db_session):
        """测试缓存读取错误时降级"""
        auth_service = AuthService(test_db_session)
        user_id = "user-123"

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.user_uuid = user_id
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.phone = "13800138000"
        mock_user.password_hash = "hashed_password"
        mock_user.user_type = "personal"
        mock_user.status = "active"
        mock_user.role = "user"
        mock_user.enterprise_id = None
        mock_user.last_login_at = None

        with patch.object(cache, 'get', side_effect=Exception("Cache error")):
            with patch.object(auth_service, '_get_user_by_id', return_value=mock_user):
                user = auth_service.get_user_by_id_cached(user_id)

                # 应该降级到数据库查询
                assert user is not None
                assert user.user_uuid == user_id

    @pytest.mark.unit
    def test_get_user_by_id_cached_cache_write_error(self, test_db_session):
        """测试缓存写入错误时继续"""
        auth_service = AuthService(test_db_session)
        user_id = "user-123"

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.user_uuid = user_id
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.phone = "13800138000"
        mock_user.password_hash = "hashed_password"
        mock_user.user_type = "personal"
        mock_user.status = "active"
        mock_user.role = "user"
        mock_user.enterprise_id = None
        mock_user.last_login_at = None

        with patch.object(cache, 'get', return_value=None):
            with patch.object(cache, 'set', side_effect=Exception("Cache write error")):
                with patch.object(auth_service, '_get_user_by_id', return_value=mock_user):
                    user = auth_service.get_user_by_id_cached(user_id)

                    # 即使缓存写入失败，也应该返回用户对象
                    assert user is not None
                    assert user.user_uuid == user_id

    @pytest.mark.unit
    def test_clear_user_cache_success(self, test_db_session):
        """测试成功清除用户缓存"""
        auth_service = AuthService(test_db_session)
        user_id = "user-123"

        with patch.object(cache, 'delete', return_value=True) as mock_delete:
            result = auth_service.clear_user_cache(user_id)

            assert result is True
            mock_delete.assert_called_once_with(f"user:{user_id}")

    @pytest.mark.unit
    def test_clear_user_cache_not_exist(self, test_db_session):
        """测试清除不存在的缓存"""
        auth_service = AuthService(test_db_session)
        user_id = "user-123"

        with patch.object(cache, 'delete', return_value=False) as mock_delete:
            result = auth_service.clear_user_cache(user_id)

            assert result is False
            mock_delete.assert_called_once_with(f"user:{user_id}")

    @pytest.mark.unit
    def test_clear_user_cache_error(self, test_db_session):
        """测试缓存清除错误"""
        auth_service = AuthService(test_db_session)
        user_id = "user-123"

        with patch.object(cache, 'delete', side_effect=Exception("Cache error")):
            result = auth_service.clear_user_cache(user_id)

            assert result is False

    @pytest.mark.unit
    def test_cache_key_format(self, test_db_session):
        """测试缓存键格式"""
        auth_service = AuthService(test_db_session)
        user_id = "user-123-abc"

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.user_uuid = user_id
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.phone = "13800138000"
        mock_user.password_hash = "hashed_password"
        mock_user.user_type = "personal"
        mock_user.status = "active"
        mock_user.role = "user"
        mock_user.enterprise_id = None
        mock_user.last_login_at = None

        with patch.object(cache, 'get', return_value=None):
            with patch.object(cache, 'set') as mock_set:
                with patch.object(auth_service, '_get_user_by_id', return_value=mock_user):
                    auth_service.get_user_by_id_cached(user_id)

                    call_args = mock_set.call_args
                    cache_key = call_args[0][0]
                    assert cache_key == f"user:{user_id}"
                    assert "user:" in cache_key


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
