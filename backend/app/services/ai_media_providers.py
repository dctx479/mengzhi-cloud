"""
AI媒体生成 Provider 抽象与适配器
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import asyncio
import httpx
import logging

from app.models.ai_media_generation import MediaProvider, MediaProviderCode, MediaProviderType, MediaTaskStatus

logger = logging.getLogger(__name__)


class MediaProviderError(Exception):
    """媒体服务商调用错误"""


@dataclass
class MediaGenerationRequest:
    media_type: MediaProviderType
    prompt: str
    negative_prompt: Optional[str] = None
    model: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None
    result_count: int = 1
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MediaGenerationResultItem:
    file_url: str
    thumbnail_url: Optional[str] = None
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MediaGenerationSubmitResult:
    provider_task_id: Optional[str]
    status: MediaTaskStatus
    raw_response: Dict[str, Any] = field(default_factory=dict)
    results: List[MediaGenerationResultItem] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class MediaGenerationQueryResult:
    provider_task_id: Optional[str]
    status: MediaTaskStatus
    raw_response: Dict[str, Any] = field(default_factory=dict)
    results: List[MediaGenerationResultItem] = field(default_factory=list)
    error_message: Optional[str] = None


class BaseMediaProviderClient(ABC):
    default_timeout = 30.0

    def __init__(
        self,
        api_key: str,
        api_endpoint: Optional[str] = None,
        app_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self._api_key = api_key  # 私有存储，避免意外序列化/日志泄露
        self.api_endpoint = api_endpoint
        self.app_id = app_id
        self.config = config or {}

    @property
    def api_key(self) -> str:
        return self._api_key

    @property
    @abstractmethod
    def provider_code(self) -> str:
        pass

    @property
    @abstractmethod
    def supported_media_type(self) -> MediaProviderType:
        pass

    def _ensure_request_type(self, request: MediaGenerationRequest) -> None:
        if request.media_type != self.supported_media_type:
            raise MediaProviderError("服务商不支持当前媒体类型")

    def _get_timeout(self) -> float:
        configured = self.config.get("timeout")
        if isinstance(configured, (int, float)) and configured > 0:
            return float(configured)
        return self.default_timeout

    def _require_api_key(self) -> None:
        if not self.api_key:
            raise MediaProviderError("服务商 API Key 未配置")

    def _build_status_from_payload(self, payload: Dict[str, Any]) -> MediaTaskStatus:
        payload = self._unwrap_payload(payload)
        status_value = str(payload.get("status") or payload.get("task_status") or "").lower()
        if not status_value:
            raise MediaProviderError("服务商响应缺少任务状态")
        if status_value in {"success", "succeeded", "finished", "done", "completed"}:
            return MediaTaskStatus.SUCCEEDED
        if status_value in {"processing", "running", "submitted", "pending", "queueing", "queued"}:
            return MediaTaskStatus.PROCESSING
        if status_value in {"failed", "error", "cancelled", "canceled"}:
            return MediaTaskStatus.FAILED
        raise MediaProviderError(f"服务商返回未知任务状态: {status_value[:100]}")

    def _unwrap_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = payload.get("data")
        if isinstance(data, dict):
            return data
        output = payload.get("output")
        if isinstance(output, dict):
            return output
        return payload

    def _extract_provider_task_id(self, payload: Dict[str, Any]) -> Optional[str]:
        payload = self._unwrap_payload(payload)
        task_id = payload.get("task_id") or payload.get("taskId") or payload.get("id") or payload.get("request_id")
        return str(task_id) if task_id else None

    def _extract_error_message(self, payload: Dict[str, Any]) -> Optional[str]:
        payload = self._unwrap_payload(payload)
        message = (
            payload.get("message")
            or payload.get("error_message")
            or payload.get("errorMessage")
            or payload.get("error")
        )
        if message:
            return str(message)[:1000]
        return None

    def _build_results_from_payload(self, payload: Dict[str, Any]) -> List[MediaGenerationResultItem]:
        payload = self._unwrap_payload(payload)
        candidates = payload.get("results") or payload.get("data") or payload.get("output") or []
        if isinstance(candidates, dict):
            nested = candidates.get("results") or candidates.get("images") or candidates.get("videos")
            candidates = nested if isinstance(nested, list) else [candidates]
        results: List[MediaGenerationResultItem] = []
        for item in candidates:
            if not isinstance(item, dict):
                continue
            file_url = item.get("file_url") or item.get("url") or item.get("fileUrl")
            if not file_url:
                continue
            results.append(
                MediaGenerationResultItem(
                    file_url=file_url,
                    thumbnail_url=item.get("thumbnail_url") or item.get("thumbnailUrl"),
                    file_size=item.get("file_size") or item.get("fileSize"),
                    width=item.get("width"),
                    height=item.get("height"),
                    duration=item.get("duration"),
                    metadata=item,
                )
            )
        return results

    # HTTP 状态码：服务端临时故障，值得重试
    _RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 504}

    async def _http_post(self, url: str, headers: Dict[str, str], json_body: Dict[str, Any]) -> Dict[str, Any]:
        """带指数退避重试的 POST 请求（仅对瞬时故障重试）。"""
        max_retries = 3
        last_exc: Exception = RuntimeError("_http_post: no attempts made")
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(self._get_timeout())) as client:
                    response = await client.post(url, headers=headers, json=json_body)
                    if response.status_code in self._RETRYABLE_HTTP_CODES and attempt < max_retries - 1:
                        wait = 2 ** attempt
                        logger.warning("HTTP %d，%.0fs 后重试 (尝试 %d/%d)", response.status_code, wait, attempt + 1, max_retries)
                        await asyncio.sleep(wait)
                        continue
                    body_preview = response.text[:300] if response.content else ""
                    if not response.is_success:
                        raise httpx.HTTPStatusError(
                            f"HTTP {response.status_code} {body_preview}",
                            request=response.request,
                            response=response,
                        )
                    return response.json() if response.content else {}
            except httpx.TimeoutException as exc:
                last_exc = exc
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
        raise last_exc

    async def _http_get(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """带指数退避重试的 GET 请求（仅对瞬时故障重试）。"""
        max_retries = 3
        last_exc: Exception = RuntimeError("_http_get: no attempts made")
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(self._get_timeout())) as client:
                    response = await client.get(url, headers=headers)
                    if response.status_code in self._RETRYABLE_HTTP_CODES and attempt < max_retries - 1:
                        wait = 2 ** attempt
                        logger.warning("HTTP %d，%.0fs 后重试 (尝试 %d/%d)", response.status_code, wait, attempt + 1, max_retries)
                        await asyncio.sleep(wait)
                        continue
                    body_preview = response.text[:300] if response.content else ""
                    if not response.is_success:
                        raise httpx.HTTPStatusError(
                            f"HTTP {response.status_code} {body_preview}",
                            request=response.request,
                            response=response,
                        )
                    return response.json() if response.content else {}
            except httpx.TimeoutException as exc:
                last_exc = exc
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
        raise last_exc

    async def validate_config(self) -> tuple[bool, Optional[str], Dict[str, Any]]:
        self._require_api_key()
        return True, None, {"provider_code": self.provider_code}

    @abstractmethod
    async def submit_task(self, request: MediaGenerationRequest) -> MediaGenerationSubmitResult:
        """提交生成任务到服务商，子类必须实现。"""

    @abstractmethod
    async def query_task(self, provider_task_id: str) -> MediaGenerationQueryResult:
        """查询服务商任务状态，子类必须实现。"""


class TongyiWanxiangProviderClient(BaseMediaProviderClient):
    provider_code = MediaProviderCode.TONGYI_WANXIANG.value
    supported_media_type = MediaProviderType.IMAGE

    def _build_submit_payload(self, request: MediaGenerationRequest) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": request.model or self.config.get("model") or "wanx-v1",
            "input": {"prompt": request.prompt},
            "parameters": {
                "n": request.result_count,
                "size": f"{request.width}*{request.height}" if request.width and request.height else None,
            },
        }
        if request.negative_prompt:
            payload["input"]["negative_prompt"] = request.negative_prompt
        payload["parameters"].update(request.params or {})
        payload["parameters"] = {key: value for key, value in payload["parameters"].items() if value is not None}
        return payload

    def _get_submit_endpoint(self) -> str:
        endpoint = self.config.get("submit_endpoint") or self.api_endpoint
        if not endpoint:
            raise MediaProviderError("通义万相提交地址未配置")
        return endpoint

    def _get_query_endpoint(self, provider_task_id: str) -> str:
        endpoint = self.config.get("query_endpoint")
        if not endpoint:
            raise MediaProviderError("通义万相查询地址未配置")
        return endpoint.format(task_id=provider_task_id)

    async def validate_config(self) -> tuple[bool, Optional[str], Dict[str, Any]]:
        self._require_api_key()
        endpoint = self.config.get("validate_endpoint") or self.api_endpoint
        if not endpoint:
            return True, None, {"provider_code": self.provider_code, "mode": "local_validation_only"}
        try:
            payload = await self._http_get(endpoint, headers={"Authorization": f"Bearer {self.api_key}"})
            return True, None, payload if isinstance(payload, dict) else {"data": payload}
        except httpx.TimeoutException as exc:
            raise MediaProviderError("通义万相配置验证请求超时") from exc
        except httpx.HTTPStatusError as exc:
            raise MediaProviderError(f"通义万相配置验证失败: {exc}") from exc
        except Exception as exc:
            logger.warning("通义万相配置验证异常: %s", exc)
            raise MediaProviderError(f"通义万相配置验证失败: {str(exc)[:300]}") from exc

    async def submit_task(self, request: MediaGenerationRequest) -> MediaGenerationSubmitResult:
        self._require_api_key()
        self._ensure_request_type(request)
        try:
            payload = await self._http_post(
                self._get_submit_endpoint(),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "X-DashScope-Async": "enable",
                },
                json_body=self._build_submit_payload(request),
            )
        except httpx.TimeoutException as exc:
            raise MediaProviderError("通义万相任务提交请求超时") from exc
        except httpx.HTTPStatusError as exc:
            raise MediaProviderError(f"通义万相任务提交失败: {exc}") from exc
        except Exception as exc:
            logger.warning("通义万相任务提交异常: %s", exc)
            raise MediaProviderError(f"通义万相任务提交失败: {str(exc)[:300]}") from exc
        if not isinstance(payload, dict):
            raise MediaProviderError("通义万相任务提交响应格式无效")
        provider_task_id = self._extract_provider_task_id(payload)
        status = self._build_status_from_payload(payload)
        results = self._build_results_from_payload(payload)
        if status == MediaTaskStatus.PROCESSING and not provider_task_id:
            raise MediaProviderError("通义万相任务提交响应缺少任务ID")
        return MediaGenerationSubmitResult(
            provider_task_id=provider_task_id,
            status=status,
            raw_response=payload,
            results=results,
            error_message=self._extract_error_message(payload),
        )

    async def query_task(self, provider_task_id: str) -> MediaGenerationQueryResult:
        self._require_api_key()
        if not provider_task_id:
            raise MediaProviderError("通义万相任务ID不能为空")
        try:
            payload = await self._http_get(
                self._get_query_endpoint(provider_task_id),
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
        except httpx.TimeoutException as exc:
            raise MediaProviderError("通义万相任务查询请求超时") from exc
        except httpx.HTTPStatusError as exc:
            raise MediaProviderError(f"通义万相任务查询失败: {exc}") from exc
        except Exception as exc:
            logger.warning("通义万相任务查询异常: %s", exc)
            raise MediaProviderError(f"通义万相任务查询失败: {str(exc)[:300]}") from exc
        if not isinstance(payload, dict):
            raise MediaProviderError("通义万相任务查询响应格式无效")
        return MediaGenerationQueryResult(
            provider_task_id=self._extract_provider_task_id(payload) or provider_task_id,
            status=self._build_status_from_payload(payload),
            raw_response=payload,
            results=self._build_results_from_payload(payload),
            error_message=self._extract_error_message(payload),
        )


class ConfigurableHttpMediaProviderClient(BaseMediaProviderClient):
    provider_display_name = "媒体服务商"

    def _get_submit_endpoint(self) -> str:
        endpoint = self.config.get("submit_endpoint") or self.api_endpoint
        if not endpoint:
            raise MediaProviderError(f"{self.provider_display_name}提交地址未配置")
        return endpoint

    def _get_query_endpoint(self, provider_task_id: str) -> str:
        endpoint = self.config.get("query_endpoint")
        if not endpoint:
            raise MediaProviderError(f"{self.provider_display_name}查询地址未配置")
        return endpoint.format(task_id=provider_task_id)

    def _build_headers(self) -> Dict[str, str]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        configured_headers = self.config.get("headers")
        if isinstance(configured_headers, dict):
            headers.update({str(key): str(value) for key, value in configured_headers.items()})
        return headers

    def _build_submit_payload(self, request: MediaGenerationRequest) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "model": request.model or self.config.get("model"),
            "width": request.width,
            "height": request.height,
            "duration": request.duration,
            "result_count": request.result_count,
            "params": request.params or {},
        }
        if self.app_id:
            payload["app_id"] = self.app_id
        template = self.config.get("payload_template")
        if isinstance(template, dict):
            payload = {**template, **payload}
        return {key: value for key, value in payload.items() if value is not None}

    async def validate_config(self) -> tuple[bool, Optional[str], Dict[str, Any]]:
        self._require_api_key()
        endpoint = self.config.get("validate_endpoint")
        if not endpoint:
            return True, None, {"provider_code": self.provider_code, "mode": "local_validation_only"}
        try:
            payload = await self._http_get(endpoint, headers=self._build_headers())
            return True, None, payload if isinstance(payload, dict) else {"data": payload}
        except httpx.TimeoutException as exc:
            raise MediaProviderError(f"{self.provider_display_name}配置验证请求超时") from exc
        except httpx.HTTPStatusError as exc:
            raise MediaProviderError(f"{self.provider_display_name}配置验证失败: {exc}") from exc
        except Exception as exc:
            logger.warning("%s配置验证异常: %s", self.provider_display_name, exc)
            raise MediaProviderError(f"{self.provider_display_name}配置验证失败: {str(exc)[:300]}") from exc

    async def submit_task(self, request: MediaGenerationRequest) -> MediaGenerationSubmitResult:
        self._require_api_key()
        self._ensure_request_type(request)
        try:
            payload = await self._http_post(
                self._get_submit_endpoint(),
                headers=self._build_headers(),
                json_body=self._build_submit_payload(request),
            )
        except httpx.TimeoutException as exc:
            raise MediaProviderError(f"{self.provider_display_name}任务提交请求超时") from exc
        except httpx.HTTPStatusError as exc:
            raise MediaProviderError(f"{self.provider_display_name}任务提交失败: {exc}") from exc
        except Exception as exc:
            logger.warning("%s任务提交异常: %s", self.provider_display_name, exc)
            raise MediaProviderError(f"{self.provider_display_name}任务提交失败: {str(exc)[:300]}") from exc
        if not isinstance(payload, dict):
            raise MediaProviderError(f"{self.provider_display_name}任务提交响应格式无效")
        provider_task_id = self._extract_provider_task_id(payload)
        status = self._build_status_from_payload(payload)
        results = self._build_results_from_payload(payload)
        if status == MediaTaskStatus.PROCESSING and not provider_task_id:
            raise MediaProviderError(f"{self.provider_display_name}任务提交响应缺少任务ID")
        return MediaGenerationSubmitResult(
            provider_task_id=provider_task_id,
            status=status,
            raw_response=payload,
            results=results,
            error_message=self._extract_error_message(payload),
        )

    async def query_task(self, provider_task_id: str) -> MediaGenerationQueryResult:
        self._require_api_key()
        if not provider_task_id:
            raise MediaProviderError(f"{self.provider_display_name}任务ID不能为空")
        try:
            payload = await self._http_get(
                self._get_query_endpoint(provider_task_id),
                headers=self._build_headers(),
            )
        except httpx.TimeoutException as exc:
            raise MediaProviderError(f"{self.provider_display_name}任务查询请求超时") from exc
        except httpx.HTTPStatusError as exc:
            raise MediaProviderError(f"{self.provider_display_name}任务查询失败: {exc}") from exc
        except Exception as exc:
            logger.warning("%s任务查询异常: %s", self.provider_display_name, exc)
            raise MediaProviderError(f"{self.provider_display_name}任务查询失败: {str(exc)[:300]}") from exc
        if not isinstance(payload, dict):
            raise MediaProviderError(f"{self.provider_display_name}任务查询响应格式无效")
        return MediaGenerationQueryResult(
            provider_task_id=self._extract_provider_task_id(payload) or provider_task_id,
            status=self._build_status_from_payload(payload),
            raw_response=payload,
            results=self._build_results_from_payload(payload),
            error_message=self._extract_error_message(payload),
        )


class WenxinYigeProviderClient(ConfigurableHttpMediaProviderClient):
    provider_code = MediaProviderCode.WENXIN_YIGE.value
    supported_media_type = MediaProviderType.IMAGE
    provider_display_name = "文心一格"


class SparkDrawingProviderClient(ConfigurableHttpMediaProviderClient):
    provider_code = MediaProviderCode.SPARK_DRAWING.value
    supported_media_type = MediaProviderType.IMAGE
    provider_display_name = "讯飞星火绘画"


class JianyingProviderClient(ConfigurableHttpMediaProviderClient):
    provider_code = MediaProviderCode.JIANYING.value
    supported_media_type = MediaProviderType.VIDEO
    provider_display_name = "剪映开放平台"


class TencentZhiyingProviderClient(ConfigurableHttpMediaProviderClient):
    provider_code = MediaProviderCode.TENCENT_ZHIYING.value
    supported_media_type = MediaProviderType.VIDEO
    provider_display_name = "腾讯智影"


def build_media_provider_client(provider: MediaProvider, api_key: str) -> BaseMediaProviderClient:
    provider_code = provider.provider_code
    if provider_code == MediaProviderCode.TONGYI_WANXIANG.value:
        return TongyiWanxiangProviderClient(
            api_key=api_key,
            api_endpoint=provider.api_endpoint,
            app_id=provider.app_id,
            config=provider.config,
        )
    if provider_code == MediaProviderCode.WENXIN_YIGE.value:
        return WenxinYigeProviderClient(
            api_key=api_key,
            api_endpoint=provider.api_endpoint,
            app_id=provider.app_id,
            config=provider.config,
        )
    if provider_code == MediaProviderCode.SPARK_DRAWING.value:
        return SparkDrawingProviderClient(
            api_key=api_key,
            api_endpoint=provider.api_endpoint,
            app_id=provider.app_id,
            config=provider.config,
        )
    if provider_code == MediaProviderCode.JIANYING.value:
        return JianyingProviderClient(
            api_key=api_key,
            api_endpoint=provider.api_endpoint,
            app_id=provider.app_id,
            config=provider.config,
        )
    if provider_code == MediaProviderCode.TENCENT_ZHIYING.value:
        return TencentZhiyingProviderClient(
            api_key=api_key,
            api_endpoint=provider.api_endpoint,
            app_id=provider.app_id,
            config=provider.config,
        )
    raise MediaProviderError("不支持的媒体服务商")
