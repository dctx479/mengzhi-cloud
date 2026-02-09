"""
安全工具模块

提供IP验证、输入验证等安全功能
"""

import ipaddress
from typing import List
from fastapi import Request
from loguru import logger


def get_client_ip(request: Request) -> str:
    """获取客户端真实IP地址
    
    考虑代理和负载均衡器的情况
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        客户端IP地址
    """
    # 优先从X-Forwarded-For获取（代理情况）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For可能包含多个IP，取第一个
        return forwarded_for.split(",")[0].strip()
    
    # 从X-Real-IP获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
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
    client_ip = get_client_ip(request)
    
    # 本地测试环境
    if client_ip in ["127.0.0.1", "localhost", "::1"]:
        return True
    
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
                    if client_ip == allowed_ip or allowed_ip in ["localhost", "127.0.0.1"]:
                        return True
            except ValueError:
                logger.warning(f"无效的IP格式: {allowed_ip}")
                continue
        
        return False
        
    except ValueError:
        logger.error(f"无效的客户端IP: {client_ip}")
        return False


__all__ = ["get_client_ip", "verify_callback_ip"]
