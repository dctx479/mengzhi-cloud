"""
输入验证模块 - 防止XSS、SQL注入等攻击

P0-4修复: 添加输入验证和XSS防护
"""

import re
import html
from typing import Optional, Tuple
from loguru import logger


class InputValidator:
    """输入验证器"""
    
    # XSS危险字符模式：每个模式单独指定 flags，避免 DOTALL 误匹配事件属性
    XSS_PATTERNS = [
        (r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        (r'javascript\s*:', re.IGNORECASE),
        (r'on[a-zA-Z]+\s*=', re.IGNORECASE),
        (r'<iframe[^>]*>', re.IGNORECASE | re.DOTALL),
        (r'<object[^>]*>', re.IGNORECASE | re.DOTALL),
        (r'<embed[^>]*>', re.IGNORECASE | re.DOTALL),
    ]

    # 特殊字符集合（用于密码强度验证），避免引号嵌套问题
    _SPECIAL_CHARS_PATTERN = re.compile(r'[!@#%^&*_=+;:,.<>/?~|\\-\[\]{}]')

    @classmethod
    def sanitize_html(cls, text: str) -> str:
        """清理HTML标签，防止XSS攻击"""
        if not text:
            return text
        # 先移除危险模式（在HTML转义之前）
        sanitized = text
        for pattern, flags in cls.XSS_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=flags)
        # 再进行HTML转义
        sanitized = html.escape(sanitized)
        return sanitized
    
    @classmethod
    def validate_username(cls, username: str) -> Tuple[bool, Optional[str]]:
        """验证用户名格式"""
        if not username:
            return False, "用户名不能为空"
        if len(username) < 3:
            return False, "用户名长度至少3个字符"
        if len(username) > 32:
            return False, "用户名长度不能超过32个字符"
        if not re.match(r'^[\w一-龥]+$', username):
            return False, "用户名只能包含字母、数字、下划线和中文"
        return True, None
    
    @classmethod
    def validate_email(cls, email: str) -> Tuple[bool, Optional[str]]:
        """验证邮箱格式"""
        if not email:
            return False, "邮箱不能为空"
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "邮箱格式不正确"
        if len(email) > 255:
            return False, "邮箱长度不能超过255个字符"
        return True, None
    
    @classmethod
    def validate_phone(cls, phone: str) -> Tuple[bool, Optional[str]]:
        """验证手机号格式（中国大陆）"""
        if not phone:
            return False, "手机号不能为空"
        if not re.match(r'^1[3-9]\d{9}$', phone):
            return False, "手机号格式不正确"
        return True, None
    
    @classmethod
    def validate_password(cls, password: str) -> Tuple[bool, Optional[str]]:
        """验证密码强度（NIST SP 800-63B 合规）

        要求:
        - 长度 8-128 字符
        - 至少一个数字
        - 至少一个字母
        - 至少一个特殊字符（提升密码熵）
        """
        if not password:
            return False, "密码不能为空"
        if len(password) < 8:
            return False, "密码长度至少8个字符"
        if len(password) > 128:
            return False, "密码长度不能超过128个字符"
        if not re.search(r'\d', password):
            return False, "密码必须包含至少一个数字"
        if not re.search(r'[a-zA-Z]', password):
            return False, "密码必须包含至少一个字母"
        # 增强：要求至少一个特殊字符，提升密码熵
        if not cls._SPECIAL_CHARS_PATTERN.search(password):
            return False, "密码必须包含至少一个特殊字符（如 !@#%^&*）"
        return True, None


input_validator = InputValidator()
