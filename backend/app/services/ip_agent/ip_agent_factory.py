"""
IP Agent工厂 - 创建和管理IP Agent实例
"""

from typing import Any
from sqlalchemy.orm import Session
import logging

from .base_ip_agent import BaseIPAgent
from .xiaoshu_agent import XiaoshuAgent
from .xiaoshang_agent import XiaoshangAgent
from .ip_router import IPType

logger = logging.getLogger(__name__)


class IPAgentFactory:
    """IP智能体工厂"""

    @staticmethod
    def create_agent(ip_type: IPType, db: Session, llm_client: Any = None) -> BaseIPAgent:
        """
        创建IP Agent实例

        Args:
            ip_type: IP类型 (xiaoshu/xiaoshang)
            db: 数据库会话
            llm_client: LLM客户端 (如果为None则自动获取)

        Returns:
            BaseIPAgent: 对应的IP Agent实例

        Raises:
            ValueError: 不支持的IP类型
        """
        # 延迟导入避免循环依赖
        if llm_client is None:
            from ..ai.deepseek_provider import get_deepseek_client
            import asyncio

            # 同步环境中获取异步client
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            llm_client = loop.run_until_complete(get_deepseek_client())

        # 根据类型创建对应的Agent
        if ip_type == IPType.XIAOSHU:
            logger.info(f"[IPAgentFactory] Creating XiaoshuAgent")
            return XiaoshuAgent(db, llm_client)
        elif ip_type == IPType.XIAOSHANG:
            logger.info(f"[IPAgentFactory] Creating XiaoshangAgent")
            return XiaoshangAgent(db, llm_client)
        else:
            raise ValueError(f"Unsupported IP type: {ip_type}")

    @staticmethod
    def get_available_ips() -> dict:
        """
        获取所有可用的IP列表

        Returns:
            dict: IP信息字典
        """
        return {
            IPType.XIAOSHU.value: {"name": "小数", "description": "草原文化传承者", "focus": "产品咨询、文化故事、选购建议"},
            IPType.XIAOSHANG.value: {"name": "小商", "description": "品牌营销顾问", "focus": "营销策略、内容创作、平台运营"},
        }
