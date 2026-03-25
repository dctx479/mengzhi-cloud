"""
DeepSeek API客户端 - 与DeepSeek服务集成

版本: 1.0
更新日期: 2026-01-17
"""

import httpx
import json
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger

from app.core.config import settings


class DeepSeekClient:
    """DeepSeek API客户端"""

    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        初始化客户端

        Args:
            api_key: API密钥，默认从配置读取
            api_base: API基础URL，默认从配置读取
        """
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.api_base = api_base or settings.DEEPSEEK_API_BASE
        self.model = "deepseek-chat"
        self.timeout = getattr(settings, 'DEEPSEEK_TIMEOUT', 120.0)
        self.stream_timeout = getattr(settings, 'DEEPSEEK_STREAM_TIMEOUT', 300.0)
        self.max_retries = getattr(settings, 'DEEPSEEK_MAX_RETRIES', 3)

        if not self.api_key or self.api_key == "your-deepseek-api-key-here":
            raise ValueError("DEEPSEEK_API_KEY is not configured. Please set it in .env file")

        if not self.api_base:
            raise ValueError("DEEPSEEK_API_BASE is not configured")

        logger.info(f"DeepSeek client initialized with base: {self.api_base}")

    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "AgriAI-Platform/1.0"
        }

    def _build_messages(self, messages: List[Dict[str, str]], system_prompt: str) -> List[Dict[str, str]]:
        """
        构建消息列表，包含系统提示词

        Args:
            messages: 用户消息列表
            system_prompt: 系统提示词

        Returns:
            完整的消息列表
        """
        full_messages = []

        # 添加系统提示词
        if system_prompt:
            full_messages.append({
                "role": "system",
                "content": system_prompt
            })

        # 添加用户消息
        full_messages.extend(messages)

        return full_messages

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 0.95
    ) -> Dict[str, Any]:
        """
        非流式对话补全

        Args:
            messages: 消息列表
            system_prompt: 系统提示词
            temperature: 温度参数（0-1）
            max_tokens: 最大输出token数
            top_p: nucleus采样参数

        Returns:
            API响应
        """
        full_messages = self._build_messages(messages, system_prompt)

        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": False
        }

        logger.debug(f"Sending chat completion request: {payload['model']}")

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        ) as client:
            try:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=self._build_headers(),
                    json=payload
                )
                response.raise_for_status()
                try:
                    result = response.json()
                except json.JSONDecodeError as je:
                    logger.error(f"Failed to decode JSON response: {je}, response text: {response.text[:200]}")
                    raise ValueError(f"Invalid JSON in API response: {je}") from je
                logger.debug(f"Chat completion response: {result.get('id')}")
                return result
            except httpx.HTTPError as e:
                logger.error(f"DeepSeek API error: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in chat completion: {str(e)}")
                raise
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 0.95
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式对话补全（SSE）

        Args:
            messages: 消息列表
            system_prompt: 系统提示词
            temperature: 温度参数（0-1）
            max_tokens: 最大输出token数
            top_p: nucleus采样参数

        Yields:
            API响应的流式数据块
        """
        full_messages = self._build_messages(messages, system_prompt)

        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": True
        }

        logger.debug(f"Starting stream chat completion: {payload['model']}")

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.stream_timeout, connect=10.0, read=60.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        ) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.api_base}/chat/completions",
                    headers=self._build_headers(),
                    json=payload
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line or line.startswith(":"):
                            continue

                        if line.startswith("data: "):
                            data_str = line[6:].strip()

                            if data_str == "[DONE]":
                                logger.debug("Stream completed")
                                yield {
                                    "object": "text_completion.chunk",
                                    "choices": [{"delta": {"content": "", "finish_reason": "stop"}}],
                                    "model": self.model
                                }
                                break

                            try:
                                chunk = json.loads(data_str)
                                yield chunk
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to parse JSON chunk: {e}")
                                continue

            except httpx.HTTPError as e:
                logger.error(f"DeepSeek API stream error: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in stream chat: {str(e)}")
                raise

    def count_tokens(self, text: str) -> int:
        """
        估算token数量（简易版本）

        Args:
            text: 输入文本

        Returns:
            估算的token数
        """
        # 简易估算：中文字符1个 ≈ 1-1.5 token，英文单词1个 ≈ 1 token
        # 这是一个近似值，实际应该使用tiktoken库
        chinese_chars = len([c for c in text if ord(c) > 127])
        english_words = len(text.split())

        estimated_tokens = int(chinese_chars * 1.2 + english_words * 0.8)
        return max(estimated_tokens, 1)

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: Optional[str] = None
    ) -> float:
        """
        计算API调用成本

        Args:
            input_tokens: 输入token数
            output_tokens: 输出token数
            model: 模型名称（默认为当前模型）

        Returns:
            成本（元）
        """
        _model = model or self.model

        # DeepSeek定价（示例）
        # 实际价格应该从配置或API获取
        pricing = {
            "deepseek-chat": {
                "input": 0.0005,      # 输入：0.0005元/1K tokens
                "output": 0.0015      # 输出：0.0015元/1K tokens
            }
        }

        if _model not in pricing:
            logger.warning(f"Unknown model {_model}, using default pricing")
            pricing[_model] = pricing["deepseek-chat"]

        rates = pricing[_model]
        cost = (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1000

        return round(cost, 6)

    async def health_check(self) -> bool:
        """
        检查API连接状态

        Returns:
            连接是否正常
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=self._build_headers(),
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 10
                    }
                )
                response.raise_for_status()
                logger.info("DeepSeek API health check passed")
                return True
        except Exception as e:
            logger.error(f"DeepSeek API health check failed: {str(e)}")
            return False


# 创建全局客户端实例
_deepseek_client: Optional[DeepSeekClient] = None


async def get_deepseek_client() -> DeepSeekClient:
    """
    获取DeepSeek客户端实例（单例）

    Returns:
        DeepSeek客户端
    """
    global _deepseek_client
    if _deepseek_client is None:
        _deepseek_client = DeepSeekClient()
    return _deepseek_client
