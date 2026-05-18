"""
配额服务 - Quota Service

提供配额管理的核心功能：
- 配额检查
- 配额扣减
- 配额重置
- 配额预警
- 配额统计

版本: 1.0
更新日期: 2026-01-22
"""

from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import date, datetime, timedelta
from loguru import logger
import json
import redis
from redis.exceptions import RedisError, ConnectionError

from app.models.quota import (
    TenantQuota, QuotaUsage,
    QuotaResourceType, QuotaPeriodType, QuotaAlertLevel
)
from app.models.user import User
from app.models.enterprise import Enterprise
from app.core.errors import BusinessException, ErrorCode
from app.services.notification_service import NotificationService
from app.core.config import settings


class QuotaService:
    """配额服务 - 支持 Redis 加速和降级处理"""

    # Redis Lua 脚本：原子检查 + 扣减
    QUOTA_DEDUCT_SCRIPT = """
    local current = tonumber(redis.call('GET', KEYS[1]) or '0')
    local limit = tonumber(ARGV[1])
    local amount = tonumber(ARGV[2])
    local ttl = tonumber(ARGV[3])

    if current + amount <= limit then
        redis.call('INCRBY', KEYS[1], amount)
        local exp_result = redis.call('EXPIRE', KEYS[1], ttl)
        if exp_result == 0 then
            redis.call('DEL', KEYS[1])
            return 2
        end
        return 1
    else
        return 0
    end
    """

    def __init__(self, db: Session, redis_client: Optional[redis.Redis] = None):
        self.db = db
        self.notification_service = NotificationService(db)
        self._redis_url = settings.REDIS_URL

        # 初始化 Redis 客户端
        if redis_client:
            self.redis = redis_client
        else:
            self.redis = self._try_connect_redis()

        # 编译 Lua 脚本
        self.deduct_script = None
        if self.redis:
            try:
                self.deduct_script = self.redis.register_script(self.QUOTA_DEDUCT_SCRIPT)
            except RedisError as e:
                logger.warning(f"Lua 脚本注册失败: {e}")

    def _try_connect_redis(self) -> Optional[redis.Redis]:
        """尝试连接Redis，失败返回None"""
        try:
            client = redis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_keepalive=True,
                health_check_interval=10
            )
            client.ping()
            logger.info("Redis 连接成功")
            return client
        except (RedisError, ConnectionError) as e:
            logger.warning(f"Redis 连接失败，将使用数据库作为降级方案: {e}")
            return None

    def _ensure_redis(self) -> Optional[redis.Redis]:
        """懒重连：如果Redis断开则尝试重新连接"""
        if self.redis is not None:
            try:
                self.redis.ping()
                return self.redis
            except (RedisError, ConnectionError):
                logger.warning("Redis 连接断开，尝试重连...")
                self.redis = None
                self.deduct_script = None

        # 尝试重连
        self.redis = self._try_connect_redis()
        if self.redis:
            try:
                self.deduct_script = self.redis.register_script(self.QUOTA_DEDUCT_SCRIPT)
            except RedisError:
                pass
        return self.redis

    def _get_quota_cache_key(self, user_id: int, enterprise_id: Optional[int],
                            resource_type: QuotaResourceType, period_type: QuotaPeriodType) -> str:
        """生成配额缓存 key"""
        if enterprise_id:
            return f"quota:enterprise:{enterprise_id}:{resource_type.value}:{period_type.value}:{date.today()}"
        else:
            return f"quota:user:{user_id}:{resource_type.value}:{period_type.value}:{date.today()}"

    def _get_redis_ttl_seconds(self, period_type: QuotaPeriodType) -> int:
        """获取 Redis 过期时间（秒）"""
        if period_type == QuotaPeriodType.DAILY:
            return 86400  # 24 小时
        elif period_type == QuotaPeriodType.MONTHLY:
            return 86400 * 32  # 32 天
        else:
            return 86400 * 365  # 1 年

    # ==================== 配额检查 ====================

    def check_quota(
        self,
        resource_type: QuotaResourceType,
        required_amount: int = 1,
        enterprise_id: Optional[int] = None,
        user_id: Optional[int] = None,
        period_type: QuotaPeriodType = QuotaPeriodType.DAILY
    ) -> Tuple[bool, Optional[TenantQuota], str]:
        """
        检查配额是否充足

        参数:
            resource_type: 资源类型
            required_amount: 需要的数量
            enterprise_id: 企业ID（企业用户）
            user_id: 用户ID（个人用户）
            period_type: 周期类型

        返回:
            (是否充足, 配额对象, 消息)
        """
        # 获取或创建配额
        quota = self.get_or_create_quota(
            resource_type=resource_type,
            period_type=period_type,
            enterprise_id=enterprise_id,
            user_id=user_id
        )

        if not quota:
            return False, None, "配额不存在"

        if not quota.is_active:
            return False, quota, "配额已禁用"

        if quota.is_expired():
            # 自动重置过期配额；reset_quota 只 flush，此处负责提交
            self.reset_quota(quota.id)
            try:
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                logger.error(f"自动重置过期配额提交失败: {e}")
                raise
            quota = self.db.query(TenantQuota).filter(TenantQuota.id == quota.id).first()

        if not quota.is_sufficient(required_amount):
            remaining = quota.get_remaining()
            return False, quota, f"配额不足，剩余: {remaining}, 需要: {required_amount}"

        return True, quota, "配额充足"

    def check_quota_simple(
        self,
        resource_type: QuotaResourceType,
        required_amount: int = 1,
        enterprise_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> bool:
        """
        简单配额检查（仅返回是否充足）

        参数:
            resource_type: 资源类型
            required_amount: 需要的数量
            enterprise_id: 企业ID
            user_id: 用户ID

        返回:
            是否充足
        """
        is_sufficient, _, _ = self.check_quota(
            resource_type=resource_type,
            required_amount=required_amount,
            enterprise_id=enterprise_id,
            user_id=user_id
        )
        return is_sufficient

    # ==================== Redis 加速方法 ====================

    def check_quota_redis(
        self,
        resource_type: QuotaResourceType,
        required_amount: int = 1,
        enterprise_id: Optional[int] = None,
        user_id: Optional[int] = None,
        period_type: QuotaPeriodType = QuotaPeriodType.DAILY,
        use_fallback: bool = True
    ) -> Tuple[bool, str]:
        """
        使用 Redis 快速检查配额（1-5ms vs 200-500ms）

        参数:
            resource_type: 资源类型
            required_amount: 需要的数量
            enterprise_id: 企业ID
            user_id: 用户ID
            period_type: 周期类型
            use_fallback: Redis 失败时是否回退到数据库

        返回:
            (是否充足, 消息)
        """
        # 如果 Redis 不可用，降级到数据库
        if not self.redis:
            if use_fallback:
                is_sufficient, _, message = self.check_quota(
                    resource_type=resource_type,
                    required_amount=required_amount,
                    enterprise_id=enterprise_id,
                    user_id=user_id,
                    period_type=period_type
                )
                return is_sufficient, message
            else:
                return False, "Redis 不可用"

        try:
            # 生成缓存 key
            cache_key = self._get_quota_cache_key(
                user_id, enterprise_id, resource_type, period_type
            )

            # 从 Redis 获取已使用量；缓存未命中时从数据库加载并预热，避免假设 used=0
            raw_used = self.redis.get(cache_key)
            if raw_used is None:
                # 缓存未命中：从数据库读取真实已使用量并写入 Redis
                db_used = self._get_quota_used_from_db(
                    resource_type, period_type, enterprise_id, user_id
                )
                used = db_used if db_used is not None else 0
                ttl = self._get_redis_ttl_seconds(period_type)
                try:
                    self.redis.set(cache_key, used, ex=ttl, nx=True)
                except RedisError:
                    pass  # 预热失败不影响本次检查结果
            else:
                used = int(raw_used)

            # 获取配额限制
            quota_limit = self._get_quota_limit_from_db(
                resource_type, period_type, enterprise_id, user_id
            )

            if not quota_limit:
                return False, "配额不存在"

            # 检查是否充足
            if used + required_amount <= quota_limit:
                remaining = quota_limit - used - required_amount
                return True, f"配额充足，剩余: {remaining}"
            else:
                remaining = max(0, quota_limit - used)
                return False, f"配额不足，已用: {used}, 需要: {required_amount}, 剩余: {remaining}, 限额: {quota_limit}"

        except RedisError as e:
            logger.warning(f"Redis 检查失败，降级到数据库: {e}")
            if use_fallback:
                is_sufficient, _, message = self.check_quota(
                    resource_type=resource_type,
                    required_amount=required_amount,
                    enterprise_id=enterprise_id,
                    user_id=user_id,
                    period_type=period_type
                )
                return is_sufficient, message
            else:
                return False, "配额检查失败"

    def deduct_quota_redis(
        self,
        resource_type: QuotaResourceType,
        amount: int,
        enterprise_id: Optional[int] = None,
        user_id: Optional[int] = None,
        period_type: QuotaPeriodType = QuotaPeriodType.DAILY,
        operation: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_type_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        use_fallback: bool = True
    ) -> Tuple[bool, str]:
        """
        使用 Redis 原子操作扣减配额

        参数:
            resource_type: 资源类型
            amount: 扣减数量
            enterprise_id: 企业ID
            user_id: 用户ID
            period_type: 周期类型
            operation: 操作类型
            resource_id: 关联资源ID
            resource_type_name: 关联资源类型
            metadata: 元数据
            use_fallback: Redis 失败时是否回退到数据库

        返回:
            (是否成功, 消息)
        """
        if amount <= 0:
            return False, "扣减数量必须大于0"

        # 如果 Redis 不可用，降级到数据库
        if not self.redis or not self.deduct_script:
            if use_fallback:
                return self.deduct_quota(
                    resource_type=resource_type,
                    amount=amount,
                    enterprise_id=enterprise_id,
                    user_id=user_id,
                    period_type=period_type,
                    operation=operation,
                    resource_id=resource_id,
                    resource_type_name=resource_type_name,
                    metadata=metadata
                )
            else:
                return False, "Redis 不可用"

        try:
            # 生成缓存 key
            cache_key = self._get_quota_cache_key(
                user_id, enterprise_id, resource_type, period_type
            )

            # 获取配额限制
            quota_limit = self._get_quota_limit_from_db(
                resource_type, period_type, enterprise_id, user_id
            )

            if not quota_limit:
                return False, "配额不存在"

            # 获取 Redis TTL
            ttl = self._get_redis_ttl_seconds(period_type)

            # 使用 Lua 脚本原子扣减
            result = self.deduct_script(
                keys=[cache_key],
                args=[quota_limit, amount, ttl],
                client=self.redis
            )

            if result == 1:
                # 成功扣减，同时在数据库中记录
                self._record_quota_usage_async(
                    resource_type=resource_type,
                    amount=amount,
                    enterprise_id=enterprise_id,
                    user_id=user_id,
                    period_type=period_type,
                    operation=operation,
                    resource_id=resource_id,
                    resource_type_name=resource_type_name,
                    metadata=metadata
                )

                # 获取剩余配额
                used = int(self.redis.get(cache_key) or 0)
                remaining = quota_limit - used
                logger.info(f"Redis 配额扣减成功: {resource_type.value}, 数量: {amount}, 剩余: {remaining}")
                return True, f"配额扣减成功，剩余: {remaining}"
            elif result == 2:
                # Redis EXPIRE failed (OOM?), quota may not reset
                logger.error(f"Redis EXPIRE失败(OOM?), 配额可能无法重置: {resource_type.value}")
                return False, "Redis OOM - quota expiry failed, aborting deduction"
            else:
                used = int(self.redis.get(cache_key) or 0)
                remaining = max(0, quota_limit - used)
                message = f"配额不足，已用: {used}, 需要: {amount}, 剩余: {remaining}, 限额: {quota_limit}"
                logger.warning(f"Redis 配额不足: {message}")
                return False, message

        except RedisError as e:
            logger.warning(f"Redis 扣减失败，降级到数据库: {e}")
            if use_fallback:
                return self.deduct_quota(
                    resource_type=resource_type,
                    amount=amount,
                    enterprise_id=enterprise_id,
                    user_id=user_id,
                    period_type=period_type,
                    operation=operation,
                    resource_id=resource_id,
                    resource_type_name=resource_type_name,
                    metadata=metadata
                )
            else:
                return False, "配额扣减失败"

    def _get_quota_limit_from_db(
        self,
        resource_type: QuotaResourceType,
        period_type: QuotaPeriodType,
        enterprise_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Optional[int]:
        """从数据库获取配额限制"""
        today = date.today()

        query = self.db.query(TenantQuota).filter(
            and_(
                TenantQuota.resource_type == resource_type,
                TenantQuota.period_type == period_type,
                TenantQuota.period_start <= today,
                TenantQuota.period_end >= today,
                TenantQuota.is_active == 1
            )
        )

        if enterprise_id:
            query = query.filter(TenantQuota.enterprise_id == enterprise_id)
        elif user_id:
            query = query.filter(TenantQuota.user_id == user_id)
        else:
            return None

        quota = query.first()
        return quota.quota_limit if quota else None

    def _get_quota_used_from_db(
        self,
        resource_type: QuotaResourceType,
        period_type: QuotaPeriodType,
        enterprise_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Optional[int]:
        """从数据库获取当前已使用量（用于 Redis 缓存预热）"""
        today = date.today()

        query = self.db.query(TenantQuota).filter(
            and_(
                TenantQuota.resource_type == resource_type,
                TenantQuota.period_type == period_type,
                TenantQuota.period_start <= today,
                TenantQuota.period_end >= today,
                TenantQuota.is_active == 1
            )
        )

        if enterprise_id:
            query = query.filter(TenantQuota.enterprise_id == enterprise_id)
        elif user_id:
            query = query.filter(TenantQuota.user_id == user_id)
        else:
            return None

        quota = query.first()
        return quota.quota_used if quota else None

    def _record_quota_usage_async(
        self,
        resource_type: QuotaResourceType,
        amount: int,
        enterprise_id: Optional[int] = None,
        user_id: Optional[int] = None,
        period_type: QuotaPeriodType = QuotaPeriodType.DAILY,
        operation: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_type_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """异步记录配额使用（不阻塞主流程）"""
        try:
            # 这里可以使用任务队列（如 Celery）进行异步记录
            # 为了简化，这里直接同步记录，可根据需要优化为异步
            quota = self.get_or_create_quota(
                resource_type=resource_type,
                period_type=period_type,
                enterprise_id=enterprise_id,
                user_id=user_id,
                auto_create=False
            )

            if quota:
                # 记录使用
                usage_record = QuotaUsage(
                    quota_id=quota.id,
                    amount=amount,
                    operation=operation,
                    resource_id=resource_id,
                    resource_type=resource_type_name,
                    usage_metadata=json.dumps(metadata) if metadata else None,
                    used_at=datetime.utcnow()
                )
                self.db.add(usage_record)
                self.db.commit()

                logger.debug(f"配额使用记录: quota_id={quota.id}, amount={amount}")
        except Exception as e:
            try:
                self.db.rollback()
            except Exception as rollback_err:
                logger.error(f"DB配额记录失败且回滚异常(会话可能已损坏): 原错误={e}, 回滚错误={rollback_err}")
                return  # 会话已损坏，静默退出，不影响主流程
            logger.error(f"DB配额使用记录失败，已回滚: {e}")
            # 不 raise：此方法是 Redis 扣减成功后的异步记录，失败不应回滚已完成的扣减
    def sync_redis_to_db(self) -> int:
        """
        将 Redis 配额数据同步到数据库（定时任务调用）

        返回:
            同步的配额记录数
        """
        if not self.redis:
            logger.warning("Redis 不可用，无法执行同步")
            return 0

        try:
            # 获取所有配额 key
            quota_keys = self.redis.keys("quota:*")
            synced_count = 0

            for key in quota_keys:
                try:
                    # 解析 key 获取信息
                    parts = key.split(":")
                    if len(parts) < 5:
                        continue

                    owner_type = parts[1]  # "user" 或 "enterprise"
                    owner_id = int(parts[2])
                    resource_type_str = parts[3]
                    period_type_str = parts[4]

                    # 从 Redis 获取使用量
                    used = int(self.redis.get(key) or 0)

                    # 查询数据库中的配额
                    query = self.db.query(TenantQuota).filter(
                        and_(
                            TenantQuota.resource_type == resource_type_str,
                            TenantQuota.period_type == period_type_str,
                            TenantQuota.is_active == 1
                        )
                    )

                    if owner_type == "enterprise":
                        query = query.filter(TenantQuota.enterprise_id == owner_id)
                    else:
                        query = query.filter(TenantQuota.user_id == owner_id)

                    quota = query.first()

                    if quota:
                        # 同步使用量
                        quota.quota_used = used
                        self.db.commit()
                        synced_count += 1
                        logger.debug(f"同步配额: {key}, used={used}")

                except Exception as e:
                    try:
                        self.db.rollback()
                    except Exception as rollback_err:
                        logger.error(f"同步配额 {key} 失败且会话可能已损坏: 原错误={e}, 回滚错误={rollback_err}")
                        break  # Session corrupted, stop sync
                    logger.warning(f"同步单个配额 {key} 失败: {e}")
                    continue

            logger.info(f"配额同步完成: {synced_count} 条记录")
            return synced_count

        except RedisError as e:
            logger.error(f"Redis 同步失败: {e}")
            return 0

    def invalidate_redis_cache(
        self,
        enterprise_id: Optional[int] = None,
        user_id: Optional[int] = None,
        resource_type: Optional[QuotaResourceType] = None,
        period_type: Optional[QuotaPeriodType] = None
    ) -> int:
        """
        清除 Redis 缓存（配额变更时调用）

        返回:
            清除的 key 数量
        """
        if not self.redis:
            return 0

        try:
            # 构建匹配模式
            if enterprise_id:
                owner_part = f"enterprise:{enterprise_id}"
            elif user_id:
                owner_part = f"user:{user_id}"
            else:
                owner_part = "*"

            if resource_type:
                resource_part = resource_type.value
            else:
                resource_part = "*"

            if period_type:
                period_part = period_type.value
            else:
                period_part = "*"

            pattern = f"quota:{owner_part}:{resource_part}:{period_part}:*"

            # 获取匹配的 key
            keys_to_delete = self.redis.keys(pattern)
            if keys_to_delete:
                deleted = self.redis.delete(*keys_to_delete)
                logger.info(f"清除 Redis 配额缓存: {deleted} 个")
                return deleted
            return 0

        except RedisError as e:
            logger.error(f"清除 Redis 缓存失败: {e}")
            return 0

    # ==================== 配额扣减 ====================

    def deduct_quota(
        self,
        resource_type: QuotaResourceType,
        amount: int,
        enterprise_id: Optional[int] = None,
        user_id: Optional[int] = None,
        period_type: QuotaPeriodType = QuotaPeriodType.DAILY,
        operation: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_type_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        扣减配额

        参数:
            resource_type: 资源类型
            amount: 扣减数量
            enterprise_id: 企业ID
            user_id: 用户ID
            period_type: 周期类型
            operation: 操作类型
            resource_id: 关联资源ID
            resource_type_name: 关联资源类型
            metadata: 元数据

        返回:
            (是否成功, 消息)
        """
        if amount <= 0:
            return False, "扣减数量必须大于0"

        # 检查配额
        is_sufficient, quota, message = self.check_quota(
            resource_type=resource_type,
            required_amount=amount,
            enterprise_id=enterprise_id,
            user_id=user_id,
            period_type=period_type
        )

        if not is_sufficient:
            logger.warning(f"配额不足: {message}")
            return False, message

        # 重新以行锁获取配额，防止并发超扣
        quota = (
            self.db.query(TenantQuota)
            .filter(TenantQuota.id == quota.id)
            .with_for_update()
            .first()
        )
        if not quota or not quota.is_sufficient(amount):
            remaining = quota.get_remaining() if quota else 0
            return False, f"配额不足，剩余: {remaining}, 需要: {amount}"

        # 扣减配额
        quota.increment_usage(amount)

        # 记录使用
        usage_record = QuotaUsage(
            quota_id=quota.id,
            amount=amount,
            operation=operation,
            resource_id=resource_id,
            resource_type=resource_type_name,
            usage_metadata=json.dumps(metadata) if metadata else None,
            used_at=datetime.utcnow()
        )
        self.db.add(usage_record)

        # 检查是否需要预警
        alert_level = quota.should_alert()
        if alert_level and alert_level != quota.last_alert_level:
            self._send_quota_alert(quota, alert_level)
            quota.last_alert_level = alert_level
            quota.last_alert_at = datetime.utcnow()

        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"配额扣减提交失败: {e}")
            raise

        logger.info(
            f"配额扣减成功: {resource_type.value}, "
            f"数量: {amount}, "
            f"剩余: {quota.get_remaining()}"
        )

        return True, f"配额扣减成功，剩余: {quota.get_remaining()}"

    # ==================== 配额重置 ====================

    def reset_quota(self, quota_id: int) -> bool:
        """
        重置配额

        参数:
            quota_id: 配额ID

        返回:
            是否成功
        """
        quota = self.db.query(TenantQuota).filter(TenantQuota.id == quota_id).first()

        if not quota:
            logger.error(f"配额不存在: {quota_id}")
            return False

        # 重置使用量
        quota.reset_usage()

        # 更新周期
        today = date.today()
        if quota.period_type == QuotaPeriodType.DAILY:
            quota.period_start = today
            quota.period_end = today
        elif quota.period_type == QuotaPeriodType.MONTHLY:
            quota.period_start = date(today.year, today.month, 1)
            if today.month == 12:
                quota.period_end = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                quota.period_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
        elif quota.period_type == QuotaPeriodType.YEARLY:
            quota.period_start = date(today.year, 1, 1)
            quota.period_end = date(today.year, 12, 31)

        self.db.flush()

        logger.info(f"配额重置成功: {quota_id}")
        return True

    def reset_expired_quotas(self) -> int:
        """
        重置所有过期配额（定时任务调用）

        返回:
            重置的配额数量
        """
        today = date.today()

        # 查询所有过期的配额
        expired_quotas = self.db.query(TenantQuota).filter(
            and_(
                TenantQuota.period_end < today,
                TenantQuota.is_active == 1,
                TenantQuota.period_type != QuotaPeriodType.TOTAL  # 总计配额不重置
            )
        ).all()

        count = 0
        for quota in expired_quotas:
            if self.reset_quota(quota.id):
                count += 1

        # reset_quota 只 flush，由此处统一提交，保证批量操作的原子性
        if count > 0:
            try:
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                logger.error(f"批量重置配额提交失败: {e}")
                raise

        logger.info(f"批量重置过期配额: {count} 个")
        return count

    # ==================== 配额管理 ====================

    def get_or_create_quota(
        self,
        resource_type: QuotaResourceType,
        period_type: QuotaPeriodType,
        enterprise_id: Optional[int] = None,
        user_id: Optional[int] = None,
        auto_create: bool = True
    ) -> Optional[TenantQuota]:
        """
        获取或创建配额

        参数:
            resource_type: 资源类型
            period_type: 周期类型
            enterprise_id: 企业ID
            user_id: 用户ID
            auto_create: 是否自动创建

        返回:
            配额对象
        """
        today = date.today()

        # 查询现有配额
        query = self.db.query(TenantQuota).filter(
            and_(
                TenantQuota.resource_type == resource_type,
                TenantQuota.period_type == period_type,
                TenantQuota.period_start <= today,
                TenantQuota.period_end >= today,
                TenantQuota.is_active == 1
            )
        )

        if enterprise_id:
            query = query.filter(TenantQuota.enterprise_id == enterprise_id)
        elif user_id:
            query = query.filter(TenantQuota.user_id == user_id)
        else:
            logger.error("必须提供 enterprise_id 或 user_id")
            return None

        quota = query.first()

        # 如果不存在且允许自动创建
        if not quota and auto_create:
            quota = self._create_default_quota(
                resource_type=resource_type,
                period_type=period_type,
                enterprise_id=enterprise_id,
                user_id=user_id
            )

        return quota

    def create_quota(
        self,
        resource_type: QuotaResourceType,
        period_type: QuotaPeriodType,
        quota_limit: int,
        enterprise_id: Optional[int] = None,
        user_id: Optional[int] = None,
        start_date: Optional[date] = None,
        warning_threshold: int = 80,
        critical_threshold: int = 90,
        description: Optional[str] = None
    ) -> TenantQuota:
        """
        创建配额

        参数:
            resource_type: 资源类型
            period_type: 周期类型
            quota_limit: 配额限制
            enterprise_id: 企业ID
            user_id: 用户ID
            start_date: 开始日期
            warning_threshold: 预警阈值
            critical_threshold: 严重预警阈值
            description: 描述

        返回:
            配额对象
        """
        if not start_date:
            start_date = date.today()

        quota = TenantQuota.create_for_period(
            resource_type=resource_type,
            period_type=period_type,
            quota_limit=quota_limit,
            start_date=start_date,
            enterprise_id=enterprise_id,
            user_id=user_id,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            description=description
        )

        self.db.add(quota)
        self.db.commit()
        self.db.refresh(quota)

        logger.info(f"创建配额成功: {quota.id}")
        return quota

    def update_quota(
        self,
        quota_id: int,
        quota_limit: Optional[int] = None,
        warning_threshold: Optional[int] = None,
        critical_threshold: Optional[int] = None,
        is_active: Optional[bool] = None,
        description: Optional[str] = None
    ) -> Optional[TenantQuota]:
        """
        更新配额

        参数:
            quota_id: 配额ID
            quota_limit: 配额限制
            warning_threshold: 预警阈值
            critical_threshold: 严重预警阈值
            is_active: 是否启用
            description: 描述

        返回:
            配额对象
        """
        quota = self.db.query(TenantQuota).filter(TenantQuota.id == quota_id).first()

        if not quota:
            logger.error(f"配额不存在: {quota_id}")
            return None

        if quota_limit is not None:
            quota.quota_limit = quota_limit
        if warning_threshold is not None:
            quota.warning_threshold = warning_threshold
        if critical_threshold is not None:
            quota.critical_threshold = critical_threshold
        if is_active is not None:
            quota.is_active = 1 if is_active else 0
        if description is not None:
            quota.description = description

        self.db.commit()
        self.db.refresh(quota)

        # 清除 Redis 缓存
        self.invalidate_redis_cache(
            enterprise_id=quota.enterprise_id,
            user_id=quota.user_id,
            resource_type=quota.resource_type,
            period_type=quota.period_type
        )

        logger.info(f"更新配额成功: {quota_id}")
        return quota

    def delete_quota(self, quota_id: int) -> bool:
        """
        删除配额

        参数:
            quota_id: 配额ID

        返回:
            是否成功
        """
        quota = self.db.query(TenantQuota).filter(TenantQuota.id == quota_id).first()

        if not quota:
            logger.error(f"配额不存在: {quota_id}")
            return False

        # 清除 Redis 缓存
        self.invalidate_redis_cache(
            enterprise_id=quota.enterprise_id,
            user_id=quota.user_id,
            resource_type=quota.resource_type,
            period_type=quota.period_type
        )

        self.db.delete(quota)
        self.db.commit()

        logger.info(f"删除配额成功: {quota_id}")
        return True

    # ==================== 配额查询 ====================

    def get_quota(self, quota_id: int) -> Optional[TenantQuota]:
        """获取配额"""
        return self.db.query(TenantQuota).filter(TenantQuota.id == quota_id).first()

    def list_quotas(
        self,
        enterprise_id: Optional[int] = None,
        user_id: Optional[int] = None,
        resource_type: Optional[QuotaResourceType] = None,
        period_type: Optional[QuotaPeriodType] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[TenantQuota], int]:
        """
        查询配额列表

        参数:
            enterprise_id: 企业ID
            user_id: 用户ID
            resource_type: 资源类型
            period_type: 周期类型
            is_active: 是否启用
            page: 页码
            page_size: 每页数量

        返回:
            (配额列表, 总数)
        """
        query = self.db.query(TenantQuota)

        if enterprise_id:
            query = query.filter(TenantQuota.enterprise_id == enterprise_id)
        if user_id:
            query = query.filter(TenantQuota.user_id == user_id)
        if resource_type:
            query = query.filter(TenantQuota.resource_type == resource_type)
        if period_type:
            query = query.filter(TenantQuota.period_type == period_type)
        if is_active is not None:
            query = query.filter(TenantQuota.is_active == (1 if is_active else 0))

        total = query.count()

        quotas = query.order_by(TenantQuota.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return quotas, total

    def get_quota_usage_records(
        self,
        quota_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        operation: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[QuotaUsage], int]:
        """
        获取配额使用记录

        参数:
            quota_id: 配额ID
            start_date: 开始日期
            end_date: 结束日期
            operation: 操作类型
            page: 页码
            page_size: 每页数量

        返回:
            (使用记录列表, 总数)
        """
        query = self.db.query(QuotaUsage).filter(QuotaUsage.quota_id == quota_id)

        if start_date:
            query = query.filter(QuotaUsage.used_at >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(QuotaUsage.used_at <= datetime.combine(end_date, datetime.max.time()))
        if operation:
            query = query.filter(QuotaUsage.operation == operation)

        total = query.count()

        records = query.order_by(QuotaUsage.used_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return records, total

    # ==================== 配额统计 ====================

    def get_quota_statistics(
        self,
        enterprise_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取配额统计信息

        参数:
            enterprise_id: 企业ID
            user_id: 用户ID

        返回:
            统计信息字典
        """
        query = self.db.query(TenantQuota).filter(TenantQuota.is_active == 1)

        if enterprise_id:
            query = query.filter(TenantQuota.enterprise_id == enterprise_id)
        elif user_id:
            query = query.filter(TenantQuota.user_id == user_id)

        quotas = query.all()

        statistics = {
            "total_quotas": len(quotas),
            "by_resource_type": {},
            "by_period_type": {},
            "alerts": {
                "warning": 0,
                "critical": 0,
                "exhausted": 0
            },
            "total_usage": 0,
            "total_limit": 0
        }

        for quota in quotas:
            # 按资源类型统计
            resource_key = quota.resource_type.value
            if resource_key not in statistics["by_resource_type"]:
                statistics["by_resource_type"][resource_key] = {
                    "limit": 0,
                    "used": 0,
                    "remaining": 0,
                    "percentage": 0
                }

            statistics["by_resource_type"][resource_key]["limit"] += quota.quota_limit
            statistics["by_resource_type"][resource_key]["used"] += quota.quota_used
            statistics["by_resource_type"][resource_key]["remaining"] += quota.get_remaining()

            # 按周期类型统计
            period_key = quota.period_type.value
            if period_key not in statistics["by_period_type"]:
                statistics["by_period_type"][period_key] = 0
            statistics["by_period_type"][period_key] += 1

            # 预警统计
            alert_level = quota.should_alert()
            if alert_level:
                statistics["alerts"][alert_level.value] += 1

            # 总计
            statistics["total_usage"] += quota.quota_used
            statistics["total_limit"] += quota.quota_limit

        # 计算百分比
        for resource_type in statistics["by_resource_type"].values():
            if resource_type["limit"] > 0:
                resource_type["percentage"] = round(
                    (resource_type["used"] / resource_type["limit"] * 100), 2
                )

        return statistics

    # ==================== 私有方法 ====================

    def _create_default_quota(
        self,
        resource_type: QuotaResourceType,
        period_type: QuotaPeriodType,
        enterprise_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> TenantQuota:
        """创建默认配额"""
        # 获取默认配额限制
        quota_limit = self._get_default_quota_limit(
            resource_type=resource_type,
            period_type=period_type,
            enterprise_id=enterprise_id,
            user_id=user_id
        )

        return self.create_quota(
            resource_type=resource_type,
            period_type=period_type,
            quota_limit=quota_limit,
            enterprise_id=enterprise_id,
            user_id=user_id,
            description="系统自动创建"
        )

    def _get_default_quota_limit(
        self,
        resource_type: QuotaResourceType,
        period_type: QuotaPeriodType,
        enterprise_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> int:
        """获取默认配额限制"""
        # 企业用户配额
        if enterprise_id:
            enterprise = self.db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
            if enterprise:
                plan_quotas = enterprise.get_plan_quota()
                if period_type == QuotaPeriodType.DAILY:
                    if resource_type == QuotaResourceType.MESSAGE:
                        return plan_quotas.get("daily_chat_limit", 50)
                    elif resource_type == QuotaResourceType.GENERATION:
                        return plan_quotas.get("daily_generation_limit", 20)
                    elif resource_type == QuotaResourceType.TOKEN:
                        return plan_quotas.get("monthly_token_limit", 100000) // 30
                elif period_type == QuotaPeriodType.MONTHLY:
                    if resource_type == QuotaResourceType.TOKEN:
                        return plan_quotas.get("monthly_token_limit", 100000)

        # 个人用户默认配额
        default_quotas = {
            QuotaResourceType.TOKEN: {
                QuotaPeriodType.DAILY: 10000,
                QuotaPeriodType.MONTHLY: 100000,
            },
            QuotaResourceType.MESSAGE: {
                QuotaPeriodType.DAILY: 50,
                QuotaPeriodType.MONTHLY: 1000,
            },
            QuotaResourceType.API_CALL: {
                QuotaPeriodType.DAILY: 100,
                QuotaPeriodType.MONTHLY: 2000,
            },
            QuotaResourceType.GENERATION: {
                QuotaPeriodType.DAILY: 20,
                QuotaPeriodType.MONTHLY: 500,
            },
            QuotaResourceType.STORAGE: {
                QuotaPeriodType.TOTAL: 1024,  # 1GB
            },
        }

        return default_quotas.get(resource_type, {}).get(period_type, 1000)

    def _send_quota_alert(self, quota: TenantQuota, alert_level: QuotaAlertLevel) -> None:
        """发送配额预警"""
        try:
            # 构建预警消息
            percentage = quota.get_usage_percentage()
            remaining = quota.get_remaining()

            alert_messages = {
                QuotaAlertLevel.WARNING: f"配额预警：{quota.resource_type.value} 已使用 {percentage}%",
                QuotaAlertLevel.CRITICAL: f"配额严重预警：{quota.resource_type.value} 已使用 {percentage}%",
                QuotaAlertLevel.EXHAUSTED: f"配额耗尽：{quota.resource_type.value} 已用完"
            }

            message = alert_messages.get(alert_level, "配额预警")
            detail = f"剩余配额: {remaining}/{quota.quota_limit}"

            # 发送通知
            if quota.enterprise_id:
                # 通知企业管理员
                logger.info(f"发送企业配额预警: enterprise_id={quota.enterprise_id}, {message}")
                # TODO: 实现企业管理员通知
            elif quota.user_id:
                # 通知用户
                logger.info(f"发送用户配额预警: user_id={quota.user_id}, {message}")
                # TODO: 实现用户通知

        except Exception as e:
            logger.error(f"发送配额预警失败: {e}")
