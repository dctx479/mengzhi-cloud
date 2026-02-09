"""
OpenAI Provider 实现
"""
import httpx
import json
from typing import AsyncGenerator

from ..base_provider import (
    BaseAIProvider, ChatCompletionRequest, ChatCompletionResponse,
    Usage
)


class OpenAIProvider(BaseAIProvider):
    """OpenAI Provider"""

    @property
    def name(self) -> str:
        return "openai"

    @property
    def supported_models(self) -> list[str]:
        return ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]

    def _get_base_url(self) -> str:
        return self.base_url or "https://api.openai.com/v1"

    async def chat(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """非流式对话"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._get_base_url()}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": request.model or "gpt-3.5-turbo",
                    "messages": [{"role": m.role, "content": m.content} for m in request.messages],
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                    "stream": False,
                }
            )
            response.raise_for_status()
            data = response.json()

            return ChatCompletionResponse(
                id=data["id"],
                content=data["choices"][0]["message"]["content"],
                model=data["model"],
                usage=Usage(
                    prompt_tokens=data["usage"]["prompt_tokens"],
                    completion_tokens=data["usage"]["completion_tokens"],
                    total_tokens=data["usage"]["total_tokens"],
                ),
                finish_reason=data["choices"][0]["finish_reason"],
            )

    async def chat_stream(self, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        """流式对话"""
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{self._get_base_url()}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": request.model or "gpt-3.5-turbo",
                    "messages": [{"role": m.role, "content": m.content} for m in request.messages],
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                    "stream": True,
                }
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line or line.startswith(":"):
                        continue

                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data_str)
                            if chunk["choices"][0]["delta"].get("content"):
                                yield chunk["choices"][0]["delta"]["content"]
                        except json.JSONDecodeError:
                            continue
