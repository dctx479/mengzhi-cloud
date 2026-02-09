#!/usr/bin/env python3
"""
生成安全的SECRET_KEY

用法:
    python scripts/generate_secret_key.py
    
输出:
    生成一个64字符的URL安全的随机字符串
"""

import secrets
import sys

def generate_secret_key(length: int = 48) -> str:
    """生成安全的密钥
    
    Args:
        length: 密钥长度（字节数），默认48字节会生成64字符的base64字符串
        
    Returns:
        URL安全的base64编码字符串
    """
    return secrets.token_urlsafe(length)

def main():
    print("=" * 70)
    print("SECRET_KEY 生成器")
    print("=" * 70)
    print()
    
    # 生成密钥
    secret_key = generate_secret_key()
    
    print("✅ 已生成强密钥:")
    print()
    print(f"SECRET_KEY={secret_key}")
    print()
    print("=" * 70)
    print("📝 使用说明:")
    print("=" * 70)
    print("1. 复制上面的 SECRET_KEY 行")
    print("2. 粘贴到 .env 文件中，替换现有的 SECRET_KEY")
    print("3. 重启应用以使新密钥生效")
    print()
    print("⚠️  安全提示:")
    print("- 请勿将此密钥提交到版本控制系统")
    print("- 生产环境和开发环境应使用不同的密钥")
    print("- 定期轮换密钥以提高安全性")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
