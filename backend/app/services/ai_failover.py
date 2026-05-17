"""
AI服务商故障转移服务
"""
import asyncio
from typing import List, Optional
from loguru import logger
from ..services.ai.factory import AIProviderFactory
from ..services.ai.base_provider import ChatCompletionRequest, ChatCompletionResponse

# 可重试的错误关键词（网络抖动、限流、服务端临时故障）
_RETRYABLE_KEYWORDS = ("timeout", "rate limit", "too many requests", "429", "503", "502", "504", "connection")


class AIFailoverService:
    """AI服务商故障转移管理"""

    def __init__(self, provider_configs: List[dict]):
        """
        初始化故障转移服务
        provider_configs: [{"provider": "deepseek", "api_key": "xxx", "priority": 1}, ...]
        """
        self.providers = sorted(provider_configs, key=lambda x: x.get('priority', 999))
        self.factory = AIProviderFactory()

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        """判断异常是否属于可重试的瞬时故障。"""
        msg = str(exc).lower()
        return any(kw in msg for kw in _RETRYABLE_KEYWORDS)

    async def chat_completion_with_failover(
        self,
        request: ChatCompletionRequest,
        max_retries: int = 3
    ) -> ChatCompletionResponse:
        """带故障转移和指数退避重试的聊天补全。

        对每个 provider 最多重试 max_retries 次（仅可重试错误），
        不可重试错误（如 401 鉴权失败、400 参数错误）立即切换下一个 provider。
        """
        last_error: Optional[Exception] = None

        for provider_config in self.providers:
            provider_name = provider_config.get('provider')
            api_key = provider_config.get('api_key')

            if not provider_name or not api_key:
                logger.warning("跳过配置不完整的Provider: %s", provider_config.get('provider', '<unknown>'))
                continue

            for attempt in range(max_retries):
                try:
                    provider = self.factory.create_provider(
                        provider_name=provider_name,
                        api_key=api_key,
                        base_url=provider_config.get('base_url')
                    )
                    response = await provider.chat_completion(request)
                    logger.info("成功使用Provider: %s (尝试 %d/%d)", provider_name, attempt + 1, max_retries)
                    return response

                except Exception as exc:
                    last_error = exc
                    is_last_attempt = attempt == max_retries - 1

                    if not self._is_retryable(exc) or is_last_attempt:
                        logger.warning(
                            "Provider %s 失败 (尝试 %d/%d, 切换下一个): %s",
                            provider_name, attempt + 1, max_retries, exc,
                        )
                        break  # 切换到下一个 provider

                    wait_seconds = 2 ** attempt  # 1s → 2s → 4s
                    logger.warning(
                        "Provider %s 瞬时故障 (尝试 %d/%d), %.0fs 后重试: %s",
                        provider_name, attempt + 1, max_retries, wait_seconds, exc,
                    )
                    await asyncio.sleep(wait_seconds)

        raise Exception(f"所有Provider均失败，最后错误: {last_error}")

