"""
API密钥加密工具
"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import os

class APIKeyEncryption:
    def __init__(self, master_key: str = None):
        """初始化加密器"""
        if master_key is None:
            master_key = os.getenv("ENCRYPTION_KEY", "default-master-key-change-in-production")

        # 使用PBKDF2派生密钥
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"agri-platform-salt",
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self.cipher = Fernet(key)

    def encrypt(self, api_key: str) -> str:
        """加密API密钥"""
        return self.cipher.encrypt(api_key.encode()).decode()

    def decrypt(self, encrypted_key: str) -> str:
        """解密API密钥"""
        return self.cipher.decrypt(encrypted_key.encode()).decode()

    @staticmethod
    def mask_key(api_key: str, visible_chars: int = 4) -> str:
        """脱敏显示API密钥"""
        if len(api_key) <= visible_chars * 2:
            return "*" * len(api_key)
        return f"{api_key[:visible_chars]}{'*' * (len(api_key) - visible_chars * 2)}{api_key[-visible_chars:]}"

# 全局加密器实例
encryptor = APIKeyEncryption()
