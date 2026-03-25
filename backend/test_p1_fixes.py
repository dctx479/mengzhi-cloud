#!/usr/bin/env python3
"""
P1修复验证脚本

验证所有P1修复是否正常工作
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """测试所有新增模块是否可以正常导入"""
    print("=" * 60)
    print("测试 1: 模块导入验证")
    print("=" * 60)
    
    try:
        from app.core.redis_client import RedisClient, get_redis, get_redis_optional
        print("✓ Redis客户端模块导入成功")
    except Exception as e:
        print(f"✗ Redis客户端模块导入失败: {e}")
        return False
    
    try:
        from app.services.captcha_service import CaptchaService
        print("✓ 验证码服务模块导入成功")
    except Exception as e:
        print(f"✗ 验证码服务模块导入失败: {e}")
        return False
    
    try:
        from app.schemas.common import (
            PaginationParams, ErrorResponse, SuccessResponse,
            PaginatedResponse, PageInfo
        )
        print("✓ 通用Schema模块导入成功")
    except Exception as e:
        print(f"✗ 通用Schema模块导入失败: {e}")
        return False
    
    try:
        from app.api.deps import require_admin, require_enterprise_admin
        print("✓ 管理员权限依赖导入成功")
    except Exception as e:
        print(f"✗ 管理员权限依赖导入失败: {e}")
        return False
    
    return True


def test_password_validation():
    """测试密码验证规则"""
    print("\n" + "=" * 60)
    print("测试 2: 密码验证规则")
    print("=" * 60)
    
    from app.schemas.auth import RegisterRequest
    from pydantic import ValidationError
    
    # 测试合法密码
    valid_passwords = [
        "Password123!",
        "Test@2026Abc",
        "MyP@ssw0rd",
    ]
    
    for pwd in valid_passwords:
        try:
            RegisterRequest(
                username="testuser",
                email="test@example.com",
                password=pwd,
                user_type="personal",
                verification_code="123456"
            )
            print(f"✓ 合法密码通过: {pwd}")
        except ValidationError as e:
            print(f"✗ 合法密码被拒绝: {pwd} - {e}")
            return False
    
    # 测试不合法密码
    invalid_passwords = [
        ("password", "缺少大写字母和数字"),
        ("PASSWORD123", "缺少小写字母和特殊字符"),
        ("Pass123", "缺少特殊字符"),
        ("Pass@word", "缺少数字"),
    ]
    
    for pwd, reason in invalid_passwords:
        try:
            RegisterRequest(
                username="testuser",
                email="test@example.com",
                password=pwd,
                user_type="personal",
                verification_code="123456"
            )
            print(f"✗ 不合法密码未被拒绝: {pwd} ({reason})")
            return False
        except ValidationError:
            print(f"✓ 不合法密码正确拒绝: {pwd} ({reason})")
    
    return True


def test_pagination_schema():
    """测试分页参数Schema"""
    print("\n" + "=" * 60)
    print("测试 3: 分页参数统一")
    print("=" * 60)
    
    from app.schemas.common import PaginationParams
    
    # 测试默认值
    params = PaginationParams()
    assert params.page == 1, "默认页码应该是1"
    assert params.page_size == 20, "默认页大小应该是20"
    print("✓ 默认分页参数正确")
    
    # 测试offset计算
    params = PaginationParams(page=2, page_size=10)
    assert params.offset == 10, "第2页偏移量应该是10"
    print("✓ 偏移量计算正确")
    
    # 测试边界值
    try:
        PaginationParams(page=0, page_size=20)
        print("✗ 页码0应该被拒绝")
        return False
    except Exception:
        print("✓ 页码0正确被拒绝")

    try:
        PaginationParams(page=1, page_size=200)
        print("✗ 页大小200应该被拒绝（最大100）")
        return False
    except Exception:
        print("✓ 页大小200正确被拒绝")
    
    return True


def test_config():
    """测试配置完整性"""
    print("\n" + "=" * 60)
    print("测试 4: 配置完整性")
    print("=" * 60)
    
    from app.core.config import settings
    
    # 检查所有新配置项
    required_settings = [
        'ENVIRONMENT',
        'REDIS_HOST',
        'REDIS_PORT',
        'REDIS_DB',
        'DEEPSEEK_API_URL',
        'DEEPSEEK_MODEL',
    ]
    
    for setting in required_settings:
        if hasattr(settings, setting):
            value = getattr(settings, setting)
            print(f"✓ {setting} = {value}")
        else:
            print(f"✗ 缺少配置: {setting}")
            return False
    
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("P1 修复验证测试套件")
    print("=" * 60 + "\n")
    
    tests = [
        ("模块导入", test_imports),
        ("密码验证规则", test_password_validation),
        ("分页参数统一", test_pagination_schema),
        ("配置完整性", test_config),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ 测试异常: {name} - {e}")
            results.append((name, False))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}: {name}")
    
    print(f"\n通过: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 所有测试通过！P1修复验证成功！")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个测试失败，需要进一步检查")
        return 1


if __name__ == "__main__":
    sys.exit(main())
