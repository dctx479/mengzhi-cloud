"""
验证码服务 - 图片验证码和短信/邮箱验证码

版本: 1.0
更新日期: 2026-01-17
"""

import random
import string
from typing import Tuple, Optional
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import hashlib
from loguru import logger

from app.core.redis_client import get_redis_optional
from app.core.errors import BusinessException, ErrorCode


class CaptchaService:
    """验证码服务"""

    def __init__(self):
        self.redis_client = get_redis_optional()

    # ==================== 图片验证码 ====================

    def generate_image_captcha(self, length: int = 4) -> Tuple[str, BytesIO]:
        """
        生成图片验证码

        Args:
            length: 验证码长度

        Returns:
            (验证码文本, 图片BytesIO)
        """
        # 生成随机验证码
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

        # 创建图片
        width, height = 120, 40
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)

        # 绘制干扰线
        for _ in range(5):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = random.randint(0, width)
            y2 = random.randint(0, height)
            draw.line([(x1, y1), (x2, y2)], fill='gray', width=1)

        # 绘制验证码文本
        try:
            # 尝试使用系统字体
            font = ImageFont.truetype("arial.ttf", 28)
        except (OSError, IOError) as e:
            logger.debug(f"加载系统字体失败，使用默认字体: {e}")
            # 如果系统字体不可用，使用默认字体
            font = ImageFont.load_default()

        # 绘制每个字符
        char_width = width // length
        for i, char in enumerate(code):
            x = char_width * i + random.randint(5, 10)
            y = random.randint(5, 10)
            color = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
            draw.text((x, y), char, fill=color, font=font)

        # 绘制干扰点
        for _ in range(100):
            x = random.randint(0, width)
            y = random.randint(0, height)
            draw.point((x, y), fill='gray')

        # 转换为BytesIO
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)

        return code, buffer

    def store_image_captcha(self, identifier: str, code: str, expire: int = 300) -> None:
        """
        存储图片验证码到Redis

        Args:
            identifier: 唯一标识（如session_id）
            code: 验证码
            expire: 过期时间（秒）
        """
        if self.redis_client is None:
            raise BusinessException(
                code=ErrorCode.SYSTEM_ERROR,
                message="验证码服务暂时不可用"
            )

        try:
            key = f"image_captcha:{identifier}"
            self.redis_client.setex(key, expire, code.upper())
        except Exception as e:
            logger.error(f"存储图片验证码失败: {e}")
            raise BusinessException(
                code=ErrorCode.SYSTEM_ERROR,
                message="验证码存储失败"
            )

    def verify_image_captcha(self, identifier: str, code: str) -> bool:
        """
        验证图片验证码（原子操作，防止并发重放）

        Args:
            identifier: 唯一标识
            code: 用户输入的验证码

        Returns:
            是否验证成功
        """
        if self.redis_client is None:
            raise BusinessException(
                code=ErrorCode.SYSTEM_ERROR,
                message="验证码服务暂时不可用"
            )

        try:
            key = f"image_captcha:{identifier}"

            # Lua 脚本保证 get+delete 原子性，防止并发请求同时通过验证
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
                return False

            if isinstance(stored_code, bytes):
                stored_code = stored_code.decode('utf-8')

            return stored_code.upper() == code.upper()
        except Exception as e:
            logger.error(f"验证图片验证码失败: {e}")
            raise BusinessException(
                code=ErrorCode.SYSTEM_ERROR,
                message="验证码验证失败"
            )

    # ==================== 邮箱/手机验证码 ====================

    def generate_code(self, length: int = 6) -> str:
        """
        生成数字验证码

        Args:
            length: 验证码长度

        Returns:
            验证码字符串
        """
        return ''.join(random.choices(string.digits, k=length))

    def _get_code_hash(self, code: str) -> str:
        """生成验证码的哈希值用于日志记录
        
        Args:
            code: 验证码
            
        Returns:
            哈希值（掩码形式：**...** ）
        """
        if len(code) <= 4:
            return "*" * len(code)
        return f"{code[:2]}...{code[-2:]}"

    def _check_send_rate_limit(self, identifier: str, code_type: str) -> None:
        """
        检查验证码发送频率限制，防止短信/邮件轰炸

        规则：
        - 同一 identifier+code_type 60 秒内只能发送 1 次
        - 同一 identifier 24 小时内最多发送 10 次

        Args:
            identifier: 邮箱或手机号
            code_type: 验证码类型

        Raises:
            BusinessException: 超出频率限制
        """
        if self.redis_client is None:
            return  # Redis 不可用时跳过限制检查（降级处理）

        try:
            # 60 秒冷却键
            cooldown_key = f"code_cooldown:{identifier}:{code_type}"
            if self.redis_client.exists(cooldown_key):
                raise BusinessException(
                    code=ErrorCode.SYSTEM_ERROR,
                    message="发送过于频繁，请60秒后再试"
                )

            # 24 小时内发送次数上限
            daily_key = f"code_daily:{identifier}"
            daily_count = self.redis_client.get(daily_key)
            if daily_count and int(daily_count) >= 10:
                raise BusinessException(
                    code=ErrorCode.SYSTEM_ERROR,
                    message="今日发送次数已达上限，请明日再试"
                )

            # 设置冷却期（60 秒）
            self.redis_client.setex(cooldown_key, 60, "1")

            # 递增日计数（首次设置 24 小时 TTL）
            pipe = self.redis_client.pipeline()
            pipe.incr(daily_key)
            pipe.expire(daily_key, 86400)
            pipe.execute()

        except BusinessException:
            raise
        except Exception as e:
            logger.warning(f"频率限制检查失败（降级跳过）: {e}")

    def send_email_code(self, email: str, code_type: str = "register") -> str:
        """
        发送邮箱验证码

        Args:
            email: 邮箱地址
            code_type: 验证码类型（register/reset_password/login）

        Returns:
            验证码
        """
        code = self.generate_code()

        # 存储到Redis
        if self.redis_client is None:
            raise BusinessException(
                code=ErrorCode.SYSTEM_ERROR,
                message="验证码服务暂时不可用"
            )

        # 频率限制检查（防止邮件轰炸）
        self._check_send_rate_limit(email, code_type)

        try:
            key = f"verify_code:{email}:{code_type}"
            self.redis_client.setex(key, 300, code)  # 5分钟有效期

            # 调用邮件服务发送验证码
            from app.services.notification_service import email_service
            email_service.send_verification_email(email, code)

            # 安全日志：不记录完整验证码 (Security: never log full verification codes)
            code_masked = self._get_code_hash(code)
            logger.info(f"邮箱验证码已发送: {email} (code: {code_masked})")
            return code
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"发送邮箱验证码失败: {e}")
            raise BusinessException(
                code=ErrorCode.SYSTEM_ERROR,
                message="验证码发送失败"
            )

    def send_sms_code(self, phone: str, code_type: str = "register") -> str:
        """
        发送短信验证码

        Args:
            phone: 手机号
            code_type: 验证码类型

        Returns:
            验证码
        """
        code = self.generate_code()

        # 存储到Redis
        if self.redis_client is None:
            raise BusinessException(
                code=ErrorCode.SYSTEM_ERROR,
                message="验证码服务暂时不可用"
            )

        # 频率限制检查（防止短信轰炸）
        self._check_send_rate_limit(phone, code_type)

        try:
            key = f"verify_code:{phone}:{code_type}"
            self.redis_client.setex(key, 300, code)  # 5分钟有效期

            # 调用短信服务发送验证码
            from app.services.notification_service import sms_service
            sms_service.send_verification_sms(phone, code)

            # 安全日志：不记录完整验证码 (Security: never log full verification codes)
            code_masked = self._get_code_hash(code)
            logger.info(f"短信验证码已发送: {phone} (code: {code_masked})")
            return code
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"发送短信验证码失败: {e}")
            raise BusinessException(
                code=ErrorCode.SYSTEM_ERROR,
                message="验证码发送失败"
            )


__all__ = ["CaptchaService"]
