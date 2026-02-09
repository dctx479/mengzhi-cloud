#!/usr/bin/env python3
"""
安全修复验证脚本

验证所有P0和P1问题的修复
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def check_file_exists(filepath: str, description: str) -> bool:
    """检查文件是否存在"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}缺失: {filepath}")
        return False

def check_module_import(module_path: str, description: str) -> bool:
    """检查模块是否可以导入"""
    try:
        __import__(module_path)
        print(f"✅ {description}可以导入: {module_path}")
        return True
    except ImportError as e:
        print(f"❌ {description}导入失败: {module_path}")
        print(f"   错误: {e}")
        return False

def main():
    print("=" * 70)
    print("安全修复验证")
    print("=" * 70)
    print()
    
    results = []
    
    # 检查新增文件
    print("1. 检查新增文件...")
    print("-" * 70)
    results.append(check_file_exists(
        "scripts/generate_secret_key.py",
        "密钥生成脚本"
    ))
    results.append(check_file_exists(
        "app/core/input_validation.py",
        "输入验证模块"
    ))
    results.append(check_file_exists(
        "app/core/rate_limiter.py",
        "频率限制模块"
    ))
    results.append(check_file_exists(
        "app/api/deps_security.py",
        "安全依赖模块"
    ))
    results.append(check_file_exists(
        "tests/test_security_fixes.py",
        "安全测试文件"
    ))
    print()
    
    # 检查修改文件
    print("2. 检查修改文件...")
    print("-" * 70)
    results.append(check_file_exists(
        ".env.example",
        ".env示例文件"
    ))
    results.append(check_file_exists(
        "app/core/constants.py",
        "常量定义文件"
    ))
    results.append(check_file_exists(
        "app/core/security.py",
        "安全工具文件"
    ))
    print()
    
    # 检查模块导入
    print("3. 检查模块导入...")
    print("-" * 70)
    results.append(check_module_import(
        "app.core.input_validation",
        "输入验证模块"
    ))
    results.append(check_module_import(
        "app.core.rate_limiter",
        "频率限制模块"
    ))
    results.append(check_module_import(
        "app.api.deps_security",
        "安全依赖模块"
    ))
    results.append(check_module_import(
        "app.core.security",
        "安全工具模块"
    ))
    print()
    
    # 检查常量定义
    print("4. 检查常量定义...")
    print("-" * 70)
    try:
        from app.core.constants import (
            RATE_LIMIT_LOGIN_MAX_REQUESTS,
            RATE_LIMIT_LOGIN_WINDOW_SECONDS,
            RATE_LIMIT_REGISTER_MAX_REQUESTS,
            RATE_LIMIT_REGISTER_WINDOW_SECONDS,
        )
        print(f"✅ 频率限制常量已定义")
        print(f"   - 登录限制: {RATE_LIMIT_LOGIN_MAX_REQUESTS}次/{RATE_LIMIT_LOGIN_WINDOW_SECONDS}秒")
        print(f"   - 注册限制: {RATE_LIMIT_REGISTER_MAX_REQUESTS}次/{RATE_LIMIT_REGISTER_WINDOW_SECONDS}秒")
        results.append(True)
    except ImportError as e:
        print(f"❌ 频率限制常量缺失")
        print(f"   错误: {e}")
        results.append(False)
    print()
    
    # 检查输入验证功能
    print("5. 检查输入验证功能...")
    print("-" * 70)
    try:
        from app.core.input_validation import input_validator
        
        # 测试XSS防护
        malicious = "<script>alert('XSS')</script>"
        safe = input_validator.sanitize_html(malicious)
        if "<script>" not in safe:
            print(f"✅ XSS防护工作正常")
            results.append(True)
        else:
            print(f"❌ XSS防护失败")
            results.append(False)
        
        # 测试用户名验证
        valid, error = input_validator.validate_username("testuser")
        if valid:
            print(f"✅ 用户名验证工作正常")
            results.append(True)
        else:
            print(f"❌ 用户名验证失败: {error}")
            results.append(False)
            
    except Exception as e:
        print(f"❌ 输入验证功能测试失败")
        print(f"   错误: {e}")
        results.append(False)
    print()
    
    # 检查频率限制功能
    print("6. 检查频率限制功能...")
    print("-" * 70)
    try:
        from app.core.rate_limiter import RateLimiter
        limiter = RateLimiter(redis_client=None)
        print(f"✅ 频率限制器创建成功")
        results.append(True)
    except Exception as e:
        print(f"❌ 频率限制器创建失败")
        print(f"   错误: {e}")
        results.append(False)
    print()
    
    # 统计结果
    print("=" * 70)
    print("验证结果")
    print("=" * 70)
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"总计: {total} 项")
    print(f"通过: {passed} 项 ✅")
    print(f"失败: {failed} 项 ❌")
    print(f"通过率: {passed/total*100:.1f}%")
    print()
    
    if failed == 0:
        print("🎉 所有验证通过！安全修复已成功应用。")
        print()
        print("下一步:")
        print("1. 运行测试: python -m pytest tests/test_security_fixes.py -v")
        print("2. 生成密钥: python scripts/generate_secret_key.py")
        print("3. 配置.env文件")
        return 0
    else:
        print("⚠️  部分验证失败，请检查上述错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
