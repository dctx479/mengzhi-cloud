"""
AI服务商故障转移服务
"""
from typing import List, Optional
from loguru import logger
from ..services.ai.factory import AIProviderFactory
from ..services.ai.base_provider import ChatCompletionRequest, ChatCompletionResponse

class AIFailoverService:
    """AI服务商故障转移管理"""

    def __init__(self, provider_configs: List[dict]):
        """
        初始化故障转移服务
        provider_configs: [{"provider": "deepseek", "api_key": "xxx", "priority": 1}, ...]
        """
        self.providers = sorted(provider_configs, key=lambda x: x.get('priority', 999))
        self.factory = AIProviderFactory()

    async def chat_completion_with_failover(
        self,
        request: ChatCompletionRequest,
        max_retries: int = 3
    ) -> ChatCompletionResponse:
        """带故障转移的聊天补全"""
        last_error = None

        for provider_config in self.providers:
            provider_name = provider_config['provider']
            api_key = provider_config['api_key']

            try:
                provider = self.factory.create_provider(
                    provider_name=provider_name,
                    api_key=api_key,
                    base_url=provider_config.get('base_url')
                )

                response = await provider.chat_completion(request)
                logger.info(f"成功使用Provider: {provider_name}")
                return response

            except Exception as e:
                logger.warning(f"Provider {provider_name} 失败: {str(e)}")
                last_error = e
                continue

        raise Exception(f"所有Provider均失败，最后错误: {str(last_error)}")
