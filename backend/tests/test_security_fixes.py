"""
安全修复测试

测试P0和P1问题的修复
"""

import pytest
from app.core.input_validation import input_validator
from app.core.rate_limiter import RateLimiter


class TestInputValidation:
    """测试输入验证 - P0-4修复"""
    
    def test_xss_protection(self):
        """测试XSS防护"""
        malicious = "<script>alert('XSS')</script>"
        safe = input_validator.sanitize_html(malicious)
        # HTML标签应该被转义
        assert "<script>" not in safe
        assert "&lt;script&gt;" in safe
        # 危险的JavaScript代码被转义，不会执行
    
    def test_username_validation_success(self):
        """测试用户名验证 - 成功案例"""
        valid, error = input_validator.validate_username("testuser")
        assert valid is True
        assert error is None
    
    def test_username_validation_failure(self):
        """测试用户名验证 - 失败案例"""
        # 太短
        valid, error = input_validator.validate_username("ab")
        assert valid is False
        assert "至少3个字符" in error
        
        # 包含非法字符
        valid, error = input_validator.validate_username("test<script>")
        assert valid is False
        assert "只能包含" in error
    
    def test_email_validation(self):
        """测试邮箱验证"""
        # 有效邮箱
        valid, error = input_validator.validate_email("test@example.com")
        assert valid is True
        
        # 无效邮箱
        valid, error = input_validator.validate_email("invalid-email")
        assert valid is False
    
    def test_phone_validation(self):
        """测试手机号验证"""
        # 有效手机号
        valid, error = input_validator.validate_phone("13800138000")
        assert valid is True
        
        # 无效手机号
        valid, error = input_validator.validate_phone("12345678901")
        assert valid is False
    
    def test_password_validation(self):
        """测试密码强度验证"""
        # 强密码
        valid, error = input_validator.validate_password("Password123")
        assert valid is True
        
        # 弱密码 - 太短
        valid, error = input_validator.validate_password("Pass1")
        assert valid is False
        assert "至少8个字符" in error
        
        # 弱密码 - 缺少数字
        valid, error = input_validator.validate_password("Password")
        assert valid is False
        assert "数字" in error
        
        # 弱密码 - 缺少字母
        valid, error = input_validator.validate_password("12345678")
        assert valid is False
        assert "字母" in error


class TestRateLimiter:
    """测试频率限制 - P1-6修复"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_memory(self):
        """测试内存存储的频率限制"""
        limiter = RateLimiter(redis_client=None)
        
        # 前5次应该成功
        for i in range(5):
            allowed, remaining = await limiter.check_rate_limit(
                key="test_user",
                max_requests=5,
                window_seconds=60
            )
            assert allowed is True
            assert remaining == 4 - i
        
        # 第6次应该失败
        allowed, remaining = await limiter.check_rate_limit(
            key="test_user",
            max_requests=5,
            window_seconds=60
        )
        assert allowed is False
        assert remaining == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
