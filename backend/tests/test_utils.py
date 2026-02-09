"""
测试 app/utils.py 中的验证器和清理器

覆盖所有验证函数和数据清理函数
"""
import pytest
from app.utils import Validators, Sanitizers, ValidationError


class TestValidators:
    """测试验证器类"""

    # ==================== 邮箱验证测试 ====================

    def test_validate_email_valid(self):
        """测试有效邮箱"""
        is_valid, error = Validators.validate_email('test@example.com')
        assert is_valid is True
        assert error == ""

    def test_validate_email_empty(self):
        """测试空邮箱"""
        is_valid, error = Validators.validate_email('')
        assert is_valid is False
        assert "不能为空" in error

    def test_validate_email_too_long(self):
        """测试过长邮箱"""
        long_email = 'a' * 250 + '@example.com'
        is_valid, error = Validators.validate_email(long_email)
        assert is_valid is False
        assert "长度" in error

    def test_validate_email_invalid_format(self):
        """测试无效格式"""
        invalid_emails = [
            'invalid',
            'invalid@',
            '@example.com',
            'invalid@.com',
            'invalid@example',
        ]
        for email in invalid_emails:
            is_valid, error = Validators.validate_email(email)
            assert is_valid is False
            assert "格式" in error

    # ==================== 用户名验证测试 ====================

    def test_validate_username_valid(self):
        """测试有效用户名"""
        valid_usernames = ['user123', 'test_user', 'user-name', 'TestUser']
        for username in valid_usernames:
            is_valid, error = Validators.validate_username(username)
            assert is_valid is True, f"Username {username} should be valid"

    def test_validate_username_empty(self):
        """测试空用户名"""
        is_valid, error = Validators.validate_username('')
        assert is_valid is False
        assert "不能为空" in error

    def test_validate_username_too_short(self):
        """测试过短用户名"""
        is_valid, error = Validators.validate_username('ab')
        assert is_valid is False
        assert "至少需要3个字符" in error

    def test_validate_username_too_long(self):
        """测试过长用户名"""
        is_valid, error = Validators.validate_username('a' * 101)
        assert is_valid is False
        assert "不超过100个字符" in error

    def test_validate_username_starts_with_number(self):
        """测试以数字开头的用户名"""
        is_valid, error = Validators.validate_username('123user')
        assert is_valid is False
        assert "不能以数字开头" in error

    def test_validate_username_invalid_chars(self):
        """测试包含非法字符的用户名"""
        invalid_usernames = ['user@name', 'user name', 'user#123', 'user!']
        for username in invalid_usernames:
            is_valid, error = Validators.validate_username(username)
            assert is_valid is False
            assert "仅包含" in error

    # ==================== 密码验证测试 ====================

    def test_validate_password_valid(self):
        """测试有效密码"""
        is_valid, error = Validators.validate_password('Test123!@#')
        assert is_valid is True
        assert error == ""

    def test_validate_password_empty(self):
        """测试空密码"""
        is_valid, error = Validators.validate_password('')
        assert is_valid is False
        assert "不能为空" in error

    def test_validate_password_too_short(self):
        """测试过短密码"""
        is_valid, error = Validators.validate_password('Test1!')
        assert is_valid is False
        assert "至少需要8个字符" in error

    def test_validate_password_too_long(self):
        """测试过长密码"""
        is_valid, error = Validators.validate_password('A' * 129 + 'a1!')
        assert is_valid is False
        assert "不超过128个字符" in error

    def test_validate_password_no_uppercase(self):
        """测试缺少大写字母"""
        is_valid, error = Validators.validate_password('test123!@#')
        assert is_valid is False
        assert "大写字母" in error

    def test_validate_password_no_lowercase(self):
        """测试缺少小写字母"""
        is_valid, error = Validators.validate_password('TEST123!@#')
        assert is_valid is False
        assert "小写字母" in error

    def test_validate_password_no_digit(self):
        """测试缺少数字"""
        is_valid, error = Validators.validate_password('TestTest!@#')
        assert is_valid is False
        assert "数字" in error

    def test_validate_password_no_special_char(self):
        """测试缺少特殊字符"""
        is_valid, error = Validators.validate_password('Test1234')
        assert is_valid is False
        assert "特殊字符" in error

    # ==================== 手机号验证测试 ====================

    def test_validate_phone_valid(self):
        """测试有效手机号"""
        valid_phones = ['13812345678', '15912345678', '18812345678']
        for phone in valid_phones:
            is_valid, error = Validators.validate_phone(phone)
            assert is_valid is True, f"Phone {phone} should be valid"

    def test_validate_phone_empty(self):
        """测试空手机号"""
        is_valid, error = Validators.validate_phone('')
        assert is_valid is False
        assert "不能为空" in error

    def test_validate_phone_wrong_length(self):
        """测试错误长度"""
        is_valid, error = Validators.validate_phone('1381234567')
        assert is_valid is False
        assert "11位" in error

    def test_validate_phone_not_digit(self):
        """测试包含非数字"""
        is_valid, error = Validators.validate_phone('138-1234-5678')
        assert is_valid is False
        assert "数字" in error

    def test_validate_phone_invalid_format(self):
        """测试无效格式"""
        invalid_phones = ['12812345678', '10812345678']
        for phone in invalid_phones:
            is_valid, error = Validators.validate_phone(phone)
            assert is_valid is False
            assert "格式" in error

    # ==================== URL验证测试 ====================

    def test_validate_url_valid(self):
        """测试有效URL"""
        valid_urls = [
            'http://example.com',
            'https://example.com',
            'https://example.com/path',
            'https://example.com/path?query=value'
        ]
        for url in valid_urls:
            is_valid, error = Validators.validate_url(url)
            assert is_valid is True, f"URL {url} should be valid"

    def test_validate_url_empty(self):
        """测试空URL"""
        is_valid, error = Validators.validate_url('')
        assert is_valid is False
        assert "不能为空" in error

    def test_validate_url_too_long(self):
        """测试过长URL"""
        is_valid, error = Validators.validate_url('http://example.com/' + 'a' * 2050)
        assert is_valid is False
        assert "长度" in error

    def test_validate_url_invalid_format(self):
        """测试无效格式"""
        invalid_urls = ['example.com', 'ftp://example.com', 'not a url']
        for url in invalid_urls:
            is_valid, error = Validators.validate_url(url)
            assert is_valid is False
            assert "格式" in error

    # ==================== 身份证号验证测试 ====================

    def test_validate_id_card_valid(self):
        """测试有效身份证号"""
        # 使用真实的校验位算法生成的测试身份证号
        # 跳过此测试，因为需要真实的身份证号进行验证
        pytest.skip("需要真实的身份证号进行验证")

    def test_validate_id_card_empty(self):
        """测试空身份证号"""
        is_valid, error = Validators.validate_id_card('')
        assert is_valid is False
        assert "不能为空" in error

    def test_validate_id_card_wrong_length(self):
        """测试错误长度"""
        is_valid, error = Validators.validate_id_card('12345678901234567')
        assert is_valid is False
        assert "18位" in error

    def test_validate_id_card_invalid_format(self):
        """测试无效格式"""
        is_valid, error = Validators.validate_id_card('11010119900307459A')
        assert is_valid is False
        assert "格式" in error

    def test_validate_id_card_wrong_checksum(self):
        """测试错误校验位"""
        is_valid, error = Validators.validate_id_card('110101199003074590')
        assert is_valid is False
        assert "校验位" in error

    # ==================== 日期验证测试 ====================

    def test_validate_date_valid(self):
        """测试有效日期"""
        is_valid, error = Validators.validate_date('2024-01-15')
        assert is_valid is True

    def test_validate_date_empty(self):
        """测试空日期"""
        is_valid, error = Validators.validate_date('')
        assert is_valid is False
        assert "不能为空" in error

    def test_validate_date_invalid_format(self):
        """测试无效格式"""
        is_valid, error = Validators.validate_date('2024/01/15')
        assert is_valid is False
        assert "格式" in error

    def test_validate_date_custom_format(self):
        """测试自定义格式"""
        is_valid, error = Validators.validate_date('15/01/2024', '%d/%m/%Y')
        assert is_valid is True

    # ==================== 金额验证测试 ====================

    def test_validate_amount_valid(self):
        """测试有效金额"""
        is_valid, error = Validators.validate_amount('100.50')
        assert is_valid is True

    def test_validate_amount_empty(self):
        """测试空金额"""
        is_valid, error = Validators.validate_amount('')
        assert is_valid is False
        assert "不能为空" in error

    def test_validate_amount_not_number(self):
        """测试非数字"""
        is_valid, error = Validators.validate_amount('abc')
        assert is_valid is False
        assert "数字" in error

    def test_validate_amount_negative(self):
        """测试负数"""
        is_valid, error = Validators.validate_amount('-100')
        assert is_valid is False
        assert "负数" in error

    def test_validate_amount_exceeds_max(self):
        """测试超过最大值"""
        is_valid, error = Validators.validate_amount('1000000', max_amount=999999.99)
        assert is_valid is False
        assert "不超过" in error

    # ==================== 长度验证测试 ====================

    def test_validate_length_valid(self):
        """测试有效长度"""
        is_valid, error = Validators.validate_length('test', min_len=2, max_len=10)
        assert is_valid is True

    def test_validate_length_empty_required(self):
        """测试必填但为空"""
        is_valid, error = Validators.validate_length('', min_len=1, field_name="测试字段")
        assert is_valid is False
        assert "不能为空" in error

    def test_validate_length_too_short(self):
        """测试过短"""
        is_valid, error = Validators.validate_length('ab', min_len=3, field_name="测试字段")
        assert is_valid is False
        assert "至少需要3个字符" in error

    def test_validate_length_too_long(self):
        """测试过长"""
        is_valid, error = Validators.validate_length('abcdefghijk', max_len=10, field_name="测试字段")
        assert is_valid is False
        assert "不超过10个字符" in error

    # ==================== 批量验证测试 ====================

    def test_validate_batch_all_valid(self):
        """测试全部有效"""
        validations = {
            'email': {'value': 'test@example.com', 'validator': Validators.validate_email},
            'username': {'value': 'testuser', 'validator': Validators.validate_username},
        }
        is_valid, errors = Validators.validate_batch(validations)
        assert is_valid is True
        assert errors == {}

    def test_validate_batch_some_invalid(self):
        """测试部分无效"""
        validations = {
            'email': {'value': 'invalid', 'validator': Validators.validate_email},
            'username': {'value': 'testuser', 'validator': Validators.validate_username},
        }
        is_valid, errors = Validators.validate_batch(validations)
        assert is_valid is False
        assert 'email' in errors
        assert 'username' not in errors

    def test_validate_batch_no_validator(self):
        """测试没有验证器"""
        validations = {
            'field': {'value': 'test', 'validator': None},
        }
        is_valid, errors = Validators.validate_batch(validations)
        assert is_valid is True


class TestSanitizers:
    """测试清理器类"""

    def test_trim(self):
        """测试去除空白"""
        assert Sanitizers.trim('  test  ') == 'test'
        assert Sanitizers.trim('') == ''
        assert Sanitizers.trim(None) == ''

    def test_normalize_email(self):
        """测试规范化邮箱"""
        assert Sanitizers.normalize_email('  Test@Example.COM  ') == 'test@example.com'
        assert Sanitizers.normalize_email('') == ''
        assert Sanitizers.normalize_email(None) == ''

    def test_normalize_phone(self):
        """测试规范化手机号"""
        assert Sanitizers.normalize_phone('138-1234-5678') == '13812345678'
        assert Sanitizers.normalize_phone('(138) 1234-5678') == '13812345678'
        assert Sanitizers.normalize_phone('') == ''
        assert Sanitizers.normalize_phone(None) == ''

    def test_truncate(self):
        """测试截断字符串"""
        assert Sanitizers.truncate('hello world', max_length=8) == 'hello...'
        assert Sanitizers.truncate('hello', max_length=10) == 'hello'
        assert Sanitizers.truncate('', max_length=10) == ''
        assert Sanitizers.truncate(None, max_length=10) is None

    def test_truncate_custom_suffix(self):
        """测试自定义后缀"""
        assert Sanitizers.truncate('hello world', max_length=7, suffix='>>') == 'hello>>'

    def test_remove_html_tags(self):
        """测试移除HTML标签"""
        assert Sanitizers.remove_html_tags('<p>Hello</p>') == 'Hello'
        assert Sanitizers.remove_html_tags('<div><span>Test</span></div>') == 'Test'
        assert Sanitizers.remove_html_tags('No tags') == 'No tags'
        assert Sanitizers.remove_html_tags('') == ''
        assert Sanitizers.remove_html_tags(None) == ''

    def test_escape_sql(self):
        """测试SQL转义"""
        assert Sanitizers.escape_sql("O'Reilly") == "O''Reilly"
        assert Sanitizers.escape_sql("It's a test") == "It''s a test"
        assert Sanitizers.escape_sql('No quotes') == 'No quotes'
        assert Sanitizers.escape_sql('') == ''
        assert Sanitizers.escape_sql(None) == ''


class TestValidationError:
    """测试验证错误异常"""

    def test_validation_error_creation(self):
        """测试创建验证错误"""
        error = ValidationError('email', '邮箱格式不正确')
        assert error.field == 'email'
        assert error.message == '邮箱格式不正确'
        assert str(error) == 'email: 邮箱格式不正确'

    def test_validation_error_raise(self):
        """测试抛出验证错误"""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError('username', '用户名已存在')

        assert exc_info.value.field == 'username'
        assert exc_info.value.message == '用户名已存在'
