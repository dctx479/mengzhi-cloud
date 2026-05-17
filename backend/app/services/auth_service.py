"""
认证业务逻辑服务

版本: 1.0
更新日期: 2026-01-17
"""

from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
import bcrypt
import redis
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from loguru import logger

from app.core.config import settings
from app.core.redis_client import get_redis_optional
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


class AuthService:
    """认证服务"""

    def __init__(self, db: Session):
        self.db = db
        # 使用带异常处理的Redis客户端
        self.redis_client = get_redis_optional()
        if self.redis_client is None:
            logger.warning("Redis不可用，Token黑名单和验证码功能将无法使用")

    # ==================== 密码处理 ====================

    @staticmethod
    def hash_password(password: str) -> str:
        """
        使用bcrypt对密码进行加密

        Args:
            password: 明文密码

        Returns:
            bcrypt哈希值
        """
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        验证密码是否正确

        Args:
            password: 明文密码
            password_hash: bcrypt哈希值

        Returns:
            是否匹配
        """
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

    # ==================== Token处理 ====================

    def create_access_token(
        self,
        user_id: str,
        user_type: str,
        role: str,
        tenant_id: Optional[str] = None
    ) -> str:
        """
        生成Access Token（30分钟有效）

        Args:
            user_id: 用户ID
            user_type: 用户类型
            role: 用户角色
            tenant_id: 租户ID

        Returns:
            JWT Token
        """
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "iss": "ai-marketing-platform",
            "iat": now,
            "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            "nbf": now,
            "jti": str(uuid.uuid4()),
            "type": "access",
            "user_type": user_type,
            "role": role,
        }
        if tenant_id:
            payload["tenant_id"] = tenant_id

        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

    def create_refresh_token(
        self,
        user_id: str,
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> str:
        """
        生成Refresh Token（7天有效）

        Args:
            user_id: 用户ID
            device_id: 设备ID
            ip_address: IP地址

        Returns:
            JWT Token
        """
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "iss": "ai-marketing-platform",
            "iat": now,
            "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            "jti": str(uuid.uuid4()),
            "type": "refresh",
        }
        if device_id:
            payload["device_id"] = device_id
        if ip_address:
            import hashlib
            payload["ip_hash"] = hashlib.sha256(ip_address.encode()).hexdigest()[:16]

        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

    def decode_token(self, token: str) -> dict:
        """
        解码JWT Token

        Args:
            token: JWT Token

        Returns:
            Token载荷

        Raises:
            TokenExpiredError: Token已过期
            BusinessException: Token无效
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )

            # 检查是否在黑名单中
            jti = payload.get("jti")
            if self.is_token_blacklisted(jti):
                raise BusinessException(
                    code=ErrorCode.TOKEN_REVOKED,
                    message="Token已被撤销"
                )

            return payload

        except ExpiredSignatureError:
            raise TokenExpiredError()
        except JWTError as e:
            raise BusinessException(
                code=ErrorCode.TOKEN_INVALID,
                message="无效的Token"
            )

    # ==================== Token黑名单管理 ====================

    def add_token_to_blacklist(self, jti: str, ttl_seconds: int) -> None:
        """
        将Token加入黑名单

        Args:
            jti: Token ID
            ttl_seconds: 生存时间（秒）
        """
        if self.redis_client is None:
            logger.warning("Redis不可用，无法将Token加入黑名单")
            return

        try:
            key = f"token_blacklist:{jti}"
            self.redis_client.setex(key, ttl_seconds, "revoked")
        except redis.ConnectionError as e:
            logger.error(f"Redis连接错误: {e}")
        except Exception as e:
            logger.error(f"加入黑名单失败: {e}")

    def is_token_blacklisted(self, jti: str) -> bool:
        """
        检查Token是否在黑名单中

        Args:
            jti: Token ID

        Returns:
            是否在黑名单中
        """
        if not jti:
            return False
        
        if self.redis_client is None:
            logger.error(
                "SECURITY: Redis unavailable - treating token as revoked for safety. "
                "Check Redis connectivity immediately!"
            )
            return True

        try:
            key = f"token_blacklist:{jti}"
            return self.redis_client.exists(key) > 0
        except redis.ConnectionError as e:
            logger.error(f"Redis连接错误，保守策略拒绝token: {e}")
            return True
        except Exception as e:
            logger.error(f"检查黑名单失败，保守策略拒绝token: {e}")
            return True

    # ==================== 刷新Token ====================

    def refresh_tokens(self, refresh_token: str) -> Tuple[str, str]:
        """
        刷新Token对

        Args:
            refresh_token: 刷新令牌

        Returns:
            (新access_token, 新refresh_token)

        Raises:
            BusinessException: Token无效或已过期
        """
        try:
            # 1. 解码Refresh Token
            payload = jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )

            # 2. 验证Token类型
            if payload.get("type") != "refresh":
                raise BusinessException(
                    code=ErrorCode.REFRESH_TOKEN_INVALID,
                    message="无效的刷新令牌类型"
                )

            # 3. 检查黑名单
            jti = payload.get("jti")
            if self.is_token_blacklisted(jti):
                raise BusinessException(
                    code=ErrorCode.TOKEN_REVOKED,
                    message="刷新令牌已被撤销"
                )

            # 4. 从数据库获取用户信息
            user_id = payload.get("sub")
            user = self._get_user_by_id(user_id)
            if not user:
                raise UserNotFoundError()

            # 5. 生成新Token对
            user_type_val = user.user_type.value if hasattr(user.user_type, 'value') else str(user.user_type).lower()
            role_val = user.role.value if hasattr(user.role, 'value') else str(user.role).lower()
            new_access_token = self.create_access_token(
                user_id=user.user_uuid,
                user_type=user_type_val,
                role=role_val,
                tenant_id=str(user.enterprise_id) if user.enterprise_id else None
            )
            new_refresh_token = self.create_refresh_token(
                user_id=user.user_uuid,
                device_id=payload.get("device_id")
            )

            # 6. 将旧Refresh Token加入黑名单
            # payload["exp"] 是 jose 解码后的 Unix timestamp int，不是 datetime 对象
            exp_val = payload.get("exp")
            if isinstance(exp_val, datetime):
                exp_ts = int(exp_val.timestamp())
            else:
                exp_ts = int(exp_val)
            ttl = exp_ts - int(datetime.utcnow().timestamp())
            if ttl > 0:
                self.add_token_to_blacklist(jti, ttl)

            return new_access_token, new_refresh_token

        except ExpiredSignatureError:
            raise BusinessException(
                code=ErrorCode.REFRESH_TOKEN_EXPIRED,
                message="刷新令牌已过期"
            )
        except JWTError:
            raise BusinessException(
                code=ErrorCode.REFRESH_TOKEN_INVALID,
                message="无效的刷新令牌"
            )

    # ==================== 用户查询 ====================

    def _get_user_by_id(self, user_id: str):
        """
        根据用户UUID获取用户

        Args:
            user_id: 用户UUID

        Returns:
            用户ORM对象（支持 .role.value 等属性访问）
        """
        from app.models.user import User
        return self.db.query(User).filter(
            User.user_uuid == user_id,
            User.deleted_at.is_(None)
        ).first()

    def get_user_by_id_cached(self, user_id: str, ttl_seconds: int = 3600):
        """
        带缓存的用户查询（根据user_id）

        Args:
            user_id: 用户UUID
            ttl_seconds: 缓存有效期（秒），默认1小时

        Returns:
            用户对象或None（总是返回ORM对象，不是dict）
        """
        # 直接查询数据库，返回 ORM 对象
        # 注意：cache.get 返回 dict，无法替代 ORM 对象（调用方需要 .role.value 等属性）
        # 缓存仅用于写入（供其他轻量检查使用），读取路径始终走 DB 保证类型一致性
        user = self._get_user_by_id(user_id)

        # 将用户信息写入缓存（用于快速检查，但不用于返回）
        if user:
            try:
                user_dict = {
                    "id": user.id,
                    "user_uuid": user.user_uuid,
                    "username": user.username,
                    "email": user.email,
                    "phone": user.phone,
                    "password_hash": user.password_hash,
                    "user_type": user.user_type.value if hasattr(user.user_type, 'value') else str(user.user_type),
                    "status": user.status.value if hasattr(user.status, 'value') else str(user.status),
                    "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                    "enterprise_id": str(user.enterprise_id) if user.enterprise_id else None,
                    "last_login_at": str(user.last_login_at) if user.last_login_at else None,
                    "created_at": str(user.created_at) if user.created_at else None
                }
                cache.set(f"user:{user_id}", user_dict, ttl_seconds=ttl_seconds)
                logger.debug(f"用户信息已缓存: {user_id}, TTL={ttl_seconds}秒")
            except Exception as e:
                logger.warning(f"缓存用户信息失败 [{user_id}]: {str(e)}")

        return user

    def clear_user_cache(self, user_id: str) -> bool:
        """
        清除用户缓存

        Args:
            user_id: 用户UUID

        Returns:
            是否清除成功
        """
        cache_key = f"user:{user_id}"
        try:
            result = cache.delete(cache_key)
            logger.info(f"用户缓存已清除: {user_id}")
            return result
        except Exception as e:
            logger.warning(f"清除用户缓存失败 [{user_id}]: {str(e)}")
            return False

    def get_user_by_username(self, username: str):
        """
        根据用户名获取用户

        Args:
            username: 用户名

        Returns:
            用户对象
        """
        result = self.db.execute(
            text("""
                SELECT id, user_uuid, username, email, phone, password_hash,
                       user_type, status, role, enterprise_id, login_attempts,
                       locked_until, created_at, last_login_at
                FROM users
                WHERE username = :username AND deleted_at IS NULL
            """),
            {"username": username}
        )
        return result.first()

    def get_user_by_email(self, email: str):
        """根据邮箱获取用户"""
        result = self.db.execute(
            text("""
                SELECT id, user_uuid, username, email, phone, password_hash,
                       user_type, status, role, enterprise_id, login_attempts,
                       locked_until, created_at, last_login_at
                FROM users
                WHERE email = :email AND deleted_at IS NULL
            """),
            {"email": email}
        )
        return result.first()

    def get_user_by_phone(self, phone: str):
        """根据手机号获取用户"""
        result = self.db.execute(
            text("""
                SELECT id, user_uuid, username, email, phone, password_hash,
                       user_type, status, role, enterprise_id, login_attempts,
                       locked_until, created_at, last_login_at
                FROM users
                WHERE phone = :phone AND deleted_at IS NULL
            """),
            {"phone": phone}
        )
        return result.first()

    # ==================== 验证逻辑 ====================

    def check_account_status(self, user) -> None:
        """
        检查账号状态

        Args:
            user: 用户对象

        Raises:
            AccountDisabledError: 账号已禁用
            AccountLockedError: 账号已锁定
        """
        status_val = user.status.value if hasattr(user.status, 'value') else str(user.status).lower()
        if status_val == "banned":
            raise AccountDisabledError()

        if user.locked_until:
            try:
                # 处理不同类型的locked_until
                if isinstance(user.locked_until, str):
                    locked_time = datetime.fromisoformat(user.locked_until.replace('Z', '+00:00'))
                elif isinstance(user.locked_until, datetime):
                    locked_time = user.locked_until
                else:
                    # 安全原则：未知类型视为锁定
                    logger.warning(f"locked_until类型未知: {type(user.locked_until)}")
                    raise AccountLockedError()

                if locked_time > datetime.utcnow():
                    raise AccountLockedError()
            except AccountLockedError:
                raise
            except (ValueError, AttributeError) as e:
                # 安全原则：解析失败视为锁定，防止绕过
                logger.warning(f"解析locked_until失败，账号视为锁定: {e}")
                raise AccountLockedError()

    def check_and_update_login_attempts(self, user_id: int, success: bool = False) -> None:
        """
        检查和更新登录尝试次数（原子操作，防止并发竞态）

        Args:
            user_id: 用户内部ID
            success: 是否登录成功
        """
        if success:
            now = datetime.utcnow()
            # 登录成功，重置尝试次数
            self.db.execute(
                text("""
                    UPDATE users
                    SET login_attempts = 0, locked_until = NULL, last_login_at = :now
                    WHERE id = :user_id
                """),
                {"user_id": user_id, "now": now}
            )
        else:
            # 原子操作：递增计数并在同一语句中判断是否需要锁定
            # 避免 TOCTOU 竞态：先 UPDATE 再 SELECT 的两步操作在并发时可能导致
            # 多个请求同时读到相同的 login_attempts 值，绕过锁定阈值
            lock_until = datetime.utcnow() + timedelta(minutes=30)
            self.db.execute(
                text("""
                    UPDATE users
                    SET login_attempts = login_attempts + 1,
                        locked_until = CASE
                            WHEN login_attempts + 1 >= 5 THEN :lock_until
                            ELSE locked_until
                        END
                    WHERE id = :user_id
                """),
                {"user_id": user_id, "lock_until": lock_until}
            )

        self.db.commit()

    # ==================== 验证码管理 ====================

    def set_verification_code(
        self,
        identifier: str,
        code_type: str,
        code: str,
        ttl: int = 300
    ) -> None:
        """
        设置验证码

        Args:
            identifier: 标识符（邮箱或手机号）
            code_type: 验证码类型
            code: 验证码
            ttl: 有效期（秒）
        """
        if self.redis_client is None:
            raise BusinessException(
                code=ErrorCode.SYSTEM_ERROR,
                message="验证码服务暂时不可用"
            )

        try:
            key = f"verify_code:{identifier}:{code_type}"
            self.redis_client.setex(key, ttl, code)
        except redis.ConnectionError as e:
            logger.error(f"Redis连接错误: {e}")
            raise BusinessException(
                code=ErrorCode.SYSTEM_ERROR,
                message="验证码服务暂时不可用"
            )
        except Exception as e:
            logger.error(f"设置验证码失败: {e}")
            raise BusinessException(
                code=ErrorCode.SYSTEM_ERROR,
                message="验证码设置失败"
            )

    def verify_code(self, identifier: str, code_type: str, code: str) -> bool:
        """
        验证验证码（原子操作，防止并发重放攻击）

        Args:
            identifier: 标识符
            code_type: 验证码类型
            code: 验证码

        Returns:
            验证是否成功
        """
        if self.redis_client is None:
            raise BusinessException(
                code=ErrorCode.SYSTEM_ERROR,
                message="验证码服务暂时不可用"
            )

        try:
            key = f"verify_code:{identifier}:{code_type}"

            # 使用 Lua 脚本保证 get+delete 原子性，防止并发请求同时通过验证
            # （两个请求同时 GET 到相同验证码，都在 DELETE 前完成比较）
            lua_script = """
                local stored = redis.call('GET', KEYS[1])
                if stored == false then
                    return nil
                end
                redis.call('DEL', KEYS[1])
                return stored
            """
            stored_code = self.redis_client.eval(lua_script, 1, key)

            if stored_code is None:
                raise BusinessException(
                    code=ErrorCode.VERIFICATION_CODE_INVALID,
                    message="验证码无效或已过期"
                )

            # 确保stored_code是字符串类型
            if isinstance(stored_code, bytes):
                stored_code = stored_code.decode('utf-8')

            if stored_code == code:
                return True

            # 验证码错误：重新存回 Redis（已被原子删除，需要重新写入以保留剩余有效期）
            # 注意：此处不重新写入，验证码一旦被取出即失效，防止暴力枚举
            raise BusinessException(
                code=ErrorCode.VERIFICATION_CODE_INVALID,
                message="验证码无效或已过期"
            )
        except redis.ConnectionError as e:
            logger.error(f"Redis连接错误: {e}")
            raise BusinessException(
                code=ErrorCode.SYSTEM_ERROR,
                message="验证码服务暂时不可用"
            )
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"验证验证码失败: {e}")
            raise BusinessException(
                code=ErrorCode.SYSTEM_ERROR,
                message="验证码验证失败"
            )

    # ==================== 数据脱敏 ====================

    @staticmethod
    def mask_phone(phone: Optional[str]) -> Optional[str]:
        """
        对手机号进行脱敏

        Args:
            phone: 手机号

        Returns:
            脱敏后的手机号
        """
        if not phone or len(phone) < 7:
            return phone
        return phone[:3] + "****" + phone[-4:]

    @staticmethod
    def mask_email(email: Optional[str]) -> Optional[str]:
        """
        对邮箱进行脱敏

        Args:
            email: 邮箱

        Returns:
            脱敏后的邮箱
        """
        if not email or "@" not in email:
            return email
        local, domain = email.rsplit("@", 1)
        if len(local) <= 2:
            masked_local = local[0] + "***"
        else:
            masked_local = local[:2] + "***"
        return f"{masked_local}@{domain}"

    # ==================== 用户注册 - 私有方法 ====================

    def _validate_register_input(self, request) -> None:
        """
        验证注册输入参数

        Args:
            request: 注册请求对象

        Raises:
            ValidationError: 验证失败
        """
        from app.core.errors import ValidationError

        # 验证email和phone至少填一个
        if not request.email and not request.phone:
            raise ValidationError(
                message="邮箱和手机号至少填一个",
                errors=[{
                    "field": "email/phone",
                    "message": "邮箱和手机号至少填一个"
                }]
            )

        # 企业用户必须填写企业信息
        if request.user_type == "enterprise":
            if not request.enterprise_name:
                raise ValidationError(
                    message="企业用户必须填写企业名称",
                    errors=[{
                        "field": "enterprise_name",
                        "message": "企业用户必须填写企业名称"
                    }]
                )
            if not request.enterprise_license:
                raise ValidationError(
                    message="企业用户必须填写营业执照号",
                    errors=[{
                        "field": "enterprise_license",
                        "message": "企业用户必须填写营业执照号"
                    }]
                )

    def _check_existing_user(self, request) -> None:
        """
        检查用户是否已存在（用户名/邮箱/手机号）

        Args:
            request: 注册请求对象

        Raises:
            ValidationError: 用户已存在
        """
        from app.core.errors import ValidationError

        # 检查用户名
        existing_user = self.get_user_by_username(request.username)
        if existing_user:
            raise ValidationError(
                message="用户名已被注册",
                errors=[{
                    "field": "username",
                    "message": "该用户名已被注册"
                }]
            )

        # 检查邮箱
        if request.email:
            existing_user = self.get_user_by_email(request.email)
            if existing_user:
                raise ValidationError(
                    message="邮箱已被注册",
                    errors=[{
                        "field": "email",
                        "message": "该邮箱已被注册"
                    }]
                )

        # 检查手机号
        if request.phone:
            existing_user = self.get_user_by_phone(request.phone)
            if existing_user:
                raise ValidationError(
                    message="手机号已被注册",
                    errors=[{
                        "field": "phone",
                        "message": "该手机号已被注册"
                    }]
                )

    def _create_enterprise_if_needed(self, request) -> Optional[int]:
        """
        为企业用户创建企业记录

        Args:
            request: 注册请求对象

        Returns:
            企业ID（非企业用户返回None）

        Raises:
            ValidationError: 营业执照号已存在
        """
        from app.core.errors import ValidationError

        if request.user_type != "enterprise":
            return None

        # 检查营业执照号是否已存在
        existing_enterprise = self.db.execute(
            text("SELECT id FROM enterprises WHERE license_no = :license_no"),
            {"license_no": request.enterprise_license}
        ).fetchone()

        if existing_enterprise:
            raise ValidationError(
                message="营业执照号已被注册",
                errors=[{
                    "field": "enterprise_license",
                    "message": "该营业执照号已被注册"
                }]
            )

        # 创建企业
        enterprise_uuid = str(uuid.uuid4())
        now = datetime.utcnow()
        self.db.execute(
            text("""
                INSERT INTO enterprises (
                    enterprise_uuid, name, license_no, verify_status,
                    plan_type, created_at, updated_at
                ) VALUES (
                    :enterprise_uuid, :name, :license_no, :verify_status,
                    :plan_type, :now, :now
                )
            """),
            {
                "enterprise_uuid": enterprise_uuid,
                "name": request.enterprise_name,
                "license_no": request.enterprise_license,
                "verify_status": "pending",
                "plan_type": "free",
                "now": now
            }
        )

        # 获取企业ID
        enterprise_result = self.db.execute(
            text("SELECT id FROM enterprises WHERE enterprise_uuid = :uuid"),
            {"uuid": enterprise_uuid}
        ).fetchone()

        return enterprise_result[0] if enterprise_result else None

    def _create_user_record(self, request, enterprise_id: Optional[int]) -> str:
        """
        创建用户记录

        Args:
            request: 注册请求对象
            enterprise_id: 企业ID（可选）

        Returns:
            用户UUID
        """
        user_uuid = str(uuid.uuid4())
        password_hash = self.hash_password(request.password)
        now = datetime.utcnow()

        self.db.execute(
            text("""
                INSERT INTO users (
                    user_uuid, username, email, phone, password_hash,
                    user_type, status, role, enterprise_id, is_admin,
                    created_at, updated_at
                ) VALUES (
                    :user_uuid, :username, :email, :phone, :password_hash,
                    :user_type, :status, :role, :enterprise_id, :is_admin,
                    :now, :now
                )
            """),
            {
                "user_uuid": user_uuid,
                "username": request.username,
                "email": request.email,
                "phone": request.phone,
                "password_hash": password_hash,
                "user_type": request.user_type,
                "status": "active",
                "role": "enterprise_admin" if request.user_type == "enterprise" else "user",
                "enterprise_id": enterprise_id,
                "is_admin": False,
                "now": now
            }
        )

        return user_uuid

    # ==================== 用户登录 - 私有方法 ====================

    def _find_user(self, identifier: str):
        """
        根据用户名/邮箱/手机号查找用户

        Args:
            identifier: 用户标识符（用户名、邮箱或手机号）

        Returns:
            用户对象或None
        """
        user = (
            self.get_user_by_username(identifier) or
            self.get_user_by_email(identifier) or
            self.get_user_by_phone(identifier)
        )
        return user

    def _validate_credentials(self, user, password: str) -> None:
        """
        验证用户凭据（密码）

        Args:
            user: 用户对象
            password: 输入的密码

        Raises:
            PasswordIncorrectError: 密码错误
        """
        if not self.verify_password(password, user.password_hash):
            # 记录失败尝试
            self.check_and_update_login_attempts(user.id, success=False)
            raise PasswordIncorrectError()

    def _generate_login_tokens(
        self,
        user,
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        生成登录所需的Token对

        Args:
            user: 用户对象
            device_id: 设备ID（可选）
            ip_address: IP地址（可选）

        Returns:
            (access_token, refresh_token)
        """
        user_type_val = user.user_type.value if hasattr(user.user_type, 'value') else str(user.user_type).lower()
        role_val = user.role.value if hasattr(user.role, 'value') else str(user.role).lower()
        access_token = self.create_access_token(
            user_id=user.user_uuid,
            user_type=user_type_val,
            role=role_val,
            tenant_id=str(user.enterprise_id) if user.enterprise_id else None
        )
        refresh_token = self.create_refresh_token(
            user_id=user.user_uuid,
            device_id=device_id,
            ip_address=ip_address
        )
        return access_token, refresh_token

    def _update_successful_login(self, user_id: int) -> None:
        """
        更新成功登录信息（重置失败次数、更新最后登录时间）

        Args:
            user_id: 用户内部ID
        """
        self.check_and_update_login_attempts(user_id, success=True)
