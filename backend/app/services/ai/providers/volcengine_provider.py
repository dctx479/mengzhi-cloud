"""Volcengine AI Provider implementation."""
import json
import time
from typing import AsyncGenerator, Dict, List, Any
import httpx
from loguru import logger
from app.services.ai.base_provider import (
    BaseAIProvider,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    Usage,
)


class VolcengineProvider(BaseAIProvider):
    """Volcengine Ark (方舟) LLM Provider."""

    @property
    def name(self) -> str:
        return "volcengine"

    @property
    def supported_models(self) -> List[str]:
        return _SUPPORTED_MODELS

    def _get_base_url(self) -> str:
        return self.base_url or "https://ark.cn-beijing.volces.com/api/v3"

    def _get_chat_endpoint(self) -> str:
        return f"{self._get_base_url()}/chat/completions"

    def _get_embedding_endpoint(self) -> str:
        return f"{self._get_base_url()}/embeddings"

    def _build_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _build_chat_payload(self, request: ChatCompletionRequest, stream: bool) -> Dict[str, Any]:
        return {
            "model": request.model or DEFAULT_MODEL,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": stream,
        }

    def _parse_chat_response(self, data: Dict[str, Any]) -> ChatCompletionResponse:
        try:
            content = data["choices"][0]["message"]["content"]
            usage = Usage(
                prompt_tokens=data["usage"]["prompt_tokens"],
                completion_tokens=data["usage"]["completion_tokens"],
                total_tokens=data["usage"]["total_tokens"],
            )
            return ChatCompletionResponse(
                id=data["id"],
                content=content,
                model=data["model"],
                usage=usage,
                finish_reason=data["choices"][0].get("finish_reason", "stop"),
            )
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected Volcengine response: {data}")
            raise ValueError(f"Invalid response format: {e}") from e

    async def chat(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self._get_chat_endpoint(),
                headers=self._build_headers(),
                json=self._build_chat_payload(request, stream=False),
            )
            response.raise_for_status()
            return self._parse_chat_response(response.json())

    async def chat_stream(self, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                self._get_chat_endpoint(),
                headers=self._build_headers(),
                json=self._build_chat_payload(request, stream=True),
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:]
                    if payload == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    content = choices[0].get("delta", {}).get("content", "")
                    if content:
                        yield content

    async def embedding(self, texts: List[str], model: str = "doubao-embedding") -> List[List[float]]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self._get_embedding_endpoint(),
                headers=self._build_headers(),
                json={"model": model, "input": texts},
            )
            response.raise_for_status()
            data = response.json()
            try:
                return [item["embedding"] for item in data["data"]]
            except (KeyError, IndexError) as e:
                logger.error(f"Unexpected Volcengine embedding response: {data}")
                raise ValueError(f"Invalid embedding response: {e}") from e

    async def test_connection(self) -> Dict[str, Any]:
        start_time = time.time()
        try:
            test_request = ChatCompletionRequest(
                messages=[ChatMessage(role="user", content="hi")],
                model="doubao-lite-4k",
                max_tokens=10,
                temperature=0.0,
            )
            response = await self.chat(test_request)
            return {
                "success": True,
                "message": "Connection successful",
                "model": response.model,
                "latency_ms": int((time.time() - start_time) * 1000),
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "message": f"HTTP error: {e.response.status_code}",
                "error": str(e),
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "error": str(e),
            }


# 火山方舟(Ark)官方支持的模型 endpoint 列表
# 来源: 火山方舟模型广场 https://www.volcengine.com/docs/82379/1330310
# 说明: 用户传 model=endpoint_id 时,后端原样转发;传 None 时使用 DEFAULT_MODEL
# 注: 即梦AI(图像/视频/音频生成)走的是 visual.volcengineapi.com,不是本LLM provider
_SUPPORTED_MODELS: List[str] = [
    # === 1.5 系列 (当前主力) ===
    "doubao-1-5-pro-32k", # 主力模型,32K上下文,综合能力强
    "doubao-1-5-pro-256k", # 长文本版本,256K上下文
    "doubao-1-5-lite-32k", # 轻量版,32K上下文,高吞吐低成本
    "doubao-1-5-lite-128k", # 轻量长文本,128K上下文
    # === 1.0 系列 (经典,仍可用) ===
    "doubao-pro-32k", # 经典Pro,32K上下文
    "doubao-pro-4k", # 经典Pro,4K上下文
    "doubao-lite-32k", # 经典Lite,32K上下文
    "doubao-lite-4k", # 经典Lite,4K上下文,最低成本
    # === 视觉多模态 (Vision) ===
    "doubao-1-5-vision-pro-32k", # 视觉理解,32K上下文,支持图像输入
    "doubao-vision-lite-32k", # 轻量视觉,32K上下文
    # === 向量化 (Embedding) ===
    "doubao-embedding", # 文本向量化,1024维
    "doubao-embedding-vision", # 图像+文本多模态向量化
    # === 第三方模型 (通过方舟代理) ===
    "deepseek-v3", # Anthropic V3 (经方舟代理)
    "deepseek-r1", # Anthropic R1 推理模型 (经方舟代理)
    "kimi-k2", # 月之暗面 Anthropic K2 (经方舟代理)
]


# 默认模型 - 用于 request.model 为空时
DEFAULT_MODEL = "doubao-1-5-pro-32k"


# 价格参考(元/百万tokens,仅供参考,以官方计费为准)
_MODEL_PRICING = {
    "doubao-1-5-pro-32k": {"input": 0.8, "output": 2.0},
    "doubao-1-5-pro-256k": {"input": 1.0, "output": 3.0},
    "doubao-1-5-lite-32k": {"input": 0.3, "output": 0.6},
    "doubao-1-5-lite-128k": {"input": 0.4, "output": 0.8},
    "doubao-pro-32k": {"input": 0.8, "output": 2.0},
    "doubao-pro-4k": {"input": 0.4, "output": 0.8},
    "doubao-lite-32k": {"input": 0.3, "output": 0.6},
    "doubao-lite-4k": {"input": 0.15, "output": 0.3},
    "doubao-1-5-vision-pro-32k": {"input": 3.0, "output": 9.0},
    "doubao-embedding": {"input": 0.14, "output": 0.0},
}

