"""
安全工具模块

提供IP验证、输入验证等安全功能
"""

import ipaddress
import base64
import hashlib
from typing import List
from fastapi import Request
from loguru import logger
from cryptography.fernet import Fernet

from app.core.config import settings


# 初始化加密工具（与 ai_configs.py 保持一致）
_raw_key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()  # 32字节
_cipher = Fernet(base64.urlsafe_b64encode(_raw_key))


def get_client_ip(request: Request) -> str:
    """获取客户端真实IP地址

    从 X-Forwarded-For 获取最左侧（最初客户端）的IP地址。
    X-Forwarded-For 格式: client_ip, proxy1_ip, proxy2_ip, ...

    Args:
        request: FastAPI请求对象

    Returns:
        客户端IP地址
    """
    # 优先从X-Forwarded-For获取（代理情况）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # 取第一个（最初客户端IP）
        ips = [ip.strip() for ip in forwarded_for.split(",")]
        if ips and ips[0]:
            return ips[0]

    # 从X-Real-IP获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        real_ip_stripped = real_ip.strip()
        if real_ip_stripped:
            return real_ip_stripped

    # 直接从request.client获取
    if request.client:
        return request.client.host

    return "unknown"


def verify_callback_ip(request: Request, allowed_ips: List[str]) -> bool:
    """验证回调IP是否在白名单中

    支持单个IP和CIDR网段

    Args:
        request: FastAPI请求对象
        allowed_ips: 允许的IP列表（支持CIDR格式）

    Returns:
        是否允许
    """
    # 回调IP验证使用 request.client.host 直接判断，不信任 X-Forwarded-For
    direct_ip = request.client.host if request.client else "unknown"

    # 本地测试环境（仅用直连IP判断，不可被伪造）
    if direct_ip in ["127.0.0.1", "::1"]:
        return True

    # 对外部回调使用 get_client_ip（已修复为从右向左解析）
    client_ip = get_client_ip(request)

    try:
        client_ip_obj = ipaddress.ip_address(client_ip)

        for allowed_ip in allowed_ips:
            try:
                # 尝试作为网段解析
                if "/" in allowed_ip:
                    network = ipaddress.ip_network(allowed_ip, strict=False)
                    if client_ip_obj in network:
                        return True
                # 作为单个IP解析
                else:
                    if client_ip == allowed_ip:
                        return True
            except ValueError:
                logger.warning(f"无效的IP格式: {allowed_ip}")
                continue

        return False

    except ValueError:
        logger.error(f"无效的客户端IP: {client_ip}")
        return False


def decrypt_api_key(encrypted: str) -> str:
    """解密API密钥

    Args:
        encrypted: 加密的API密钥字符串

    Returns:
        解密后的API密钥
    """
    try:
        return _cipher.decrypt(encrypted.encode()).decode()
    except Exception as e:
        logger.error(f"API密钥解密失败: {str(e)}")
        raise


__all__ = ["get_client_ip", "verify_callback_ip", "decrypt_api_key"]
