"""
验证和工具函数集合

包含所有验证逻辑的公共函数，避免代码重复。

版本: 1.0
更新日期: 2026-01-17
"""

import re
from typing import Tuple, List
from datetime import datetime


class ValidationError(Exception):
    """验证错误异常"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class Validators:
    """通用验证器集合"""

    # ==================== 邮箱验证 ====================

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        验证邮箱格式

        Args:
            email: 邮箱地址

        Returns:
            (是否有效, 错误信息)

        示例:
            >>> is_valid, error = Validators.validate_email('test@example.com')
            >>> print(is_valid)
            True
        """
        if not email:
            return False, "邮箱不能为空"

        if len(email) > 255:
            return False, "邮箱长度不超过255个字符"

        # RFC 5322 简化版本
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "邮箱格式不正确"

        return True, ""

    # ==================== 用户名验证 ====================

    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        验证用户名

        要求:
        - 长度: 3-100个字符
        - 仅包含字母、数字、下划线、中划线
        - 不能以数字开头

        Args:
            username: 用户名

        Returns:
            (是否有效, 错误信息)
        """
        if not username:
            return False, "用户名不能为空"

        if len(username) < 3:
            return False, "用户名至少需要3个字符"

        if len(username) > 100:
            return False, "用户名不超过100个字符"

        # 仅允许字母、数字、下划线、中划线
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', username):
            return False, "用户名仅包含字母、数字、下划线、中划线，且不能以数字开头"

        return True, ""

    # ==================== 密码验证 ====================

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """
        验证密码强度

        要求:
        - 长度: 8-128个字符
        - 需要包含大写字母
        - 需要包含小写字母
        - 需要包含数字
        - 需要包含特殊字符 (!@#$%^&*)

        Args:
            password: 密码

        Returns:
            (是否有效, 错误信息)
        """
        if not password:
            return False, "密码不能为空"

        if len(password) < 8:
            return False, "密码至少需要8个字符"

        if len(password) > 128:
            return False, "密码不超过128个字符"

        if not re.search(r'[A-Z]', password):
            return False, "密码需要包含至少一个大写字母"

        if not re.search(r'[a-z]', password):
            return False, "密码需要包含至少一个小写字母"

        if not re.search(r'\d', password):
            return False, "密码需要包含至少一个数字"

        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/`~\\|]', password):
            return False, "密码需要包含至少一个特殊字符"

        return True, ""

    # ==================== 手机号验证 ====================

    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str]:
        """
        验证中国大陆手机号

        要求:
        - 11个数字
        - 以1开头
        - 第二位为3-9

        Args:
            phone: 手机号

        Returns:
            (是否有效, 错误信息)
        """
        if not phone:
            return False, "手机号不能为空"

        phone = phone.strip()

        if len(phone) != 11:
            return False, "手机号必须是11位数字"

        if not phone.isdigit():
            return False, "手机号仅包含数字"

        if not re.match(r'^1[3-9]\d{9}$', phone):
            return False, "手机号格式不正确"

        return True, ""

    # ==================== URL验证 ====================

    @staticmethod
    def validate_url(url: str) -> Tuple[bool, str]:
        """
        验证URL格式

        Args:
            url: URL地址

        Returns:
            (是否有效, 错误信息)
        """
        if not url:
            return False, "URL不能为空"

        if len(url) > 2048:
            return False, "URL长度不超过2048个字符"

        pattern = r'^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=]+$'
        if not re.match(pattern, url):
            return False, "URL格式不正确"

        return True, ""

    # ==================== 身份证号验证 ====================

    @staticmethod
    def validate_id_card(id_card: str) -> Tuple[bool, str]:
        """
        验证中国大陆身份证号（18位）

        Args:
            id_card: 身份证号

        Returns:
            (是否有效, 错误信息)
        """
        if not id_card:
            return False, "身份证号不能为空"

        id_card = id_card.strip().upper()

        if len(id_card) != 18:
            return False, "身份证号长度必须为18位"

        # 检查格式：前17位为数字，最后一位为数字或X
        if not re.match(r'^\d{17}[\dX]$', id_card):
            return False, "身份证号格式不正确"

        # 计算校验位
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        sum_val = sum(int(id_card[i]) * weights[i] for i in range(17))
        mod_val = sum_val % 11

        check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        if check_codes[mod_val] != id_card[17]:
            return False, "身份证号校验位不正确"

        return True, ""

    # ==================== 日期验证 ====================

    @staticmethod
    def validate_date(date_str: str, format_str: str = '%Y-%m-%d') -> Tuple[bool, str]:
        """
        验证日期格式

        Args:
            date_str: 日期字符串
            format_str: 日期格式（默认YYYY-MM-DD）

        Returns:
            (是否有效, 错误信息)
        """
        if not date_str:
            return False, "日期不能为空"

        try:
            datetime.strptime(date_str, format_str)
            return True, ""
        except ValueError:
            return False, f"日期格式不正确，应为 {format_str}"

    # ==================== 金额验证 ====================

    @staticmethod
    def validate_amount(amount: str, max_amount: float = 999999.99) -> Tuple[bool, str]:
        """
        验证金额格式

        Args:
            amount: 金额字符串
            max_amount: 最大金额（默认999999.99）

        Returns:
            (是否有效, 错误信息)
        """
        if not amount:
            return False, "金额不能为空"

        try:
            amount_float = float(amount)
        except ValueError:
            return False, "金额必须是数字"

        if amount_float < 0:
            return False, "金额不能为负数"

        if amount_float > max_amount:
            return False, f"金额不超过 {max_amount}"

        # 检查小数位数
        if len(str(amount_float).split('.')[-1]) > 2:
            return False, "金额最多保留两位小数"

        return True, ""

    # ==================== 长度验证 ====================

    @staticmethod
    def validate_length(
        value: str,
        min_len: int = 0,
        max_len: int = 255,
        field_name: str = "字段"
    ) -> Tuple[bool, str]:
        """
        验证字符串长度

        Args:
            value: 字符串
            min_len: 最小长度
            max_len: 最大长度
            field_name: 字段名称（用于错误信息）

        Returns:
            (是否有效, 错误信息)
        """
        if not value:
            if min_len > 0:
                return False, f"{field_name}不能为空"
            return True, ""

        length = len(value)

        if length < min_len:
            return False, f"{field_name}长度至少需要{min_len}个字符"

        if length > max_len:
            return False, f"{field_name}长度不超过{max_len}个字符"

        return True, ""

    # ==================== 批量验证 ====================

    @staticmethod
    def validate_batch(validations: dict) -> Tuple[bool, dict]:
        """
        批量验证多个字段

        Args:
            validations: 验证规则字典
            格式: {
                'email': {'value': 'test@example.com', 'validator': Validators.validate_email},
                'password': {'value': 'Pass123!', 'validator': Validators.validate_password},
            }

        Returns:
            (是否全部有效, 错误字典)

        示例:
            >>> is_valid, errors = Validators.validate_batch({
            ...     'email': {'value': 'test@example.com', 'validator': Validators.validate_email},
            ...     'password': {'value': 'Pass123!', 'validator': Validators.validate_password},
            ... })
            >>> if not is_valid:
            ...     print(errors)
        """
        errors = {}
        all_valid = True

        for field, rules in validations.items():
            value = rules.get('value')
            validator = rules.get('validator')

            if validator is None:
                continue

            is_valid, error_msg = validator(value)
            if not is_valid:
                errors[field] = error_msg
                all_valid = False

        return all_valid, errors


class Sanitizers:
    """数据清理器集合"""

    @staticmethod
    def trim(value: str) -> str:
        """
        去除字符串两端空白

        Args:
            value: 字符串

        Returns:
            清理后的字符串
        """
        return value.strip() if value else ""

    @staticmethod
    def normalize_email(email: str) -> str:
        """
        规范化邮箱（转小写、去空白）

        Args:
            email: 邮箱

        Returns:
            规范化的邮箱
        """
        return email.strip().lower() if email else ""

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """
        规范化手机号（仅保留数字）

        Args:
            phone: 手机号

        Returns:
            规范化的手机号
        """
        return ''.join(c for c in phone if c.isdigit()) if phone else ""

    @staticmethod
    def truncate(value: str, max_length: int = 255, suffix: str = "...") -> str:
        """
        截断字符串到指定长度

        Args:
            value: 字符串
            max_length: 最大长度
            suffix: 超长时的后缀

        Returns:
            截断后的字符串
        """
        if not value or len(value) <= max_length:
            return value

        return value[:max_length - len(suffix)] + suffix

    @staticmethod
    def remove_html_tags(value: str) -> str:
        """
        移除HTML标签

        Args:
            value: 字符串

        Returns:
            移除标签后的字符串
        """
        pattern = r'<[^>]+>'
        return re.sub(pattern, '', value) if value else ""

    @staticmethod
    def escape_sql(value: str) -> str:
        """
        SQL转义（注意：应使用参数化查询而非此方法）

        Args:
            value: 字符串

        Returns:
            转义后的字符串
        """
        if not value:
            return ""

        # 替换单引号
        return value.replace("'", "''")
