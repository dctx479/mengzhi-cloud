import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.models.ai_media_generation import MediaProviderType, MediaTaskStatus
from app.services.ai_media_providers import (
    JianyingProviderClient,
    MediaGenerationRequest,
    MediaProviderError,
    SparkDrawingProviderClient,
    TencentZhiyingProviderClient,
    TongyiWanxiangProviderClient,
    WenxinYigeProviderClient,
)


@pytest.fixture
def tongyi_client():
    return TongyiWanxiangProviderClient(
        api_key="test-key",
        api_endpoint="https://example.test/submit",
        config={"query_endpoint": "https://example.test/tasks/{task_id}"},
    )


@pytest.fixture
def image_request():
    return MediaGenerationRequest(
        media_type=MediaProviderType.IMAGE,
        prompt="草原羊肉品牌海报",
        negative_prompt="低清晰度",
        model="wanx-v1",
        width=1024,
        height=1024,
        result_count=2,
        params={"style": "realistic"},
    )


class TestTongyiWanxiangProviderClient:
    def test_build_submit_payload(self, tongyi_client, image_request):
        payload = tongyi_client._build_submit_payload(image_request)

        assert payload["model"] == "wanx-v1"
        assert payload["input"] == {"prompt": "草原羊肉品牌海报", "negative_prompt": "低清晰度"}
        assert payload["parameters"]["n"] == 2
        assert payload["parameters"]["size"] == "1024*1024"
        assert payload["parameters"]["style"] == "realistic"

    @pytest.mark.asyncio
    async def test_submit_task_success(self, tongyi_client, image_request):
        response_payload = {
            "output": {"task_id": "task-123", "task_status": "PENDING"},
            "request_id": "req-123",
        }
        mock_response = Mock()
        mock_response.content = b"{}"
        mock_response.json.return_value = response_payload
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await tongyi_client.submit_task(image_request)

        assert result.provider_task_id == "task-123"
        assert result.status == MediaTaskStatus.PROCESSING
        assert result.raw_response == response_payload

    @pytest.mark.asyncio
    async def test_submit_task_requires_provider_task_id_for_processing(self, tongyi_client, image_request):
        mock_response = Mock()
        mock_response.content = b"{}"
        mock_response.json.return_value = {"output": {"task_status": "PENDING"}}
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            with pytest.raises(MediaProviderError, match="缺少任务ID"):
                await tongyi_client.submit_task(image_request)

    @pytest.mark.asyncio
    async def test_query_task_success_with_results(self, tongyi_client):
        response_payload = {
            "output": {
                "task_id": "task-123",
                "task_status": "SUCCEEDED",
                "results": [{"url": "https://example.test/result.png", "width": 1024, "height": 1024}],
            }
        }
        mock_response = Mock()
        mock_response.content = b"{}"
        mock_response.json.return_value = response_payload
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await tongyi_client.query_task("task-123")

        assert result.provider_task_id == "task-123"
        assert result.status == MediaTaskStatus.SUCCEEDED
        assert len(result.results) == 1
        assert result.results[0].file_url == "https://example.test/result.png"

    def test_unknown_status_raises_error(self, tongyi_client):
        with pytest.raises(MediaProviderError, match="未知任务状态"):
            tongyi_client._build_status_from_payload({"output": {"task_status": "MYSTERY"}})

    def test_nested_error_message_extraction(self, tongyi_client):
        message = tongyi_client._extract_error_message({"output": {"message": "提示词不合规"}})

        assert message == "提示词不合规"



@pytest.mark.parametrize(
    ("client_cls", "media_type"),
    [
        (WenxinYigeProviderClient, MediaProviderType.IMAGE),
        (SparkDrawingProviderClient, MediaProviderType.IMAGE),
        (JianyingProviderClient, MediaProviderType.VIDEO),
        (TencentZhiyingProviderClient, MediaProviderType.VIDEO),
    ],
)
class TestConfigurableHttpMediaProviderClient:
    @pytest.fixture
    def client(self, client_cls):
        return client_cls(
            api_key="test-key",
            api_endpoint="https://example.test/submit",
            app_id="app-123",
            config={
                "query_endpoint": "https://example.test/tasks/{task_id}",
                "headers": {"X-Test": "enabled"},
                "payload_template": {"quality": "high"},
            },
        )

    @pytest.fixture
    def media_request(self, media_type):
        return MediaGenerationRequest(
            media_type=media_type,
            prompt="草原羊肉品牌宣传素材",
            model="default-model",
            width=1024,
            height=768,
            duration=5 if media_type == MediaProviderType.VIDEO else None,
            result_count=1,
            params={"style": "realistic"},
        )

    def test_build_submit_payload(self, client, media_request):
        payload = client._build_submit_payload(media_request)

        assert payload["prompt"] == "草原羊肉品牌宣传素材"
        assert payload["model"] == "default-model"
        assert payload["app_id"] == "app-123"
        assert payload["quality"] == "high"
        assert payload["params"] == {"style": "realistic"}

    @pytest.mark.asyncio
    async def test_submit_task_success(self, client, media_request):
        response_payload = {"data": {"task_id": "task-456", "status": "processing"}}
        mock_response = Mock()
        mock_response.content = b"{}"
        mock_response.json.return_value = response_payload
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            post = mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await client.submit_task(media_request)

        assert result.provider_task_id == "task-456"
        assert result.status == MediaTaskStatus.PROCESSING
        assert post.call_args.kwargs["headers"]["X-Test"] == "enabled"

    @pytest.mark.asyncio
    async def test_query_task_success_with_results(self, client, media_type):
        response_payload = {
            "data": {
                "task_id": "task-456",
                "status": "succeeded",
                "results": [{"url": "https://example.test/result.mp4"}],
            }
        }
        mock_response = Mock()
        mock_response.content = b"{}"
        mock_response.json.return_value = response_payload
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await client.query_task("task-456")

        assert result.provider_task_id == "task-456"
        assert result.status == MediaTaskStatus.SUCCEEDED
        assert result.results[0].file_url == "https://example.test/result.mp4"

    def test_submit_endpoint_must_be_configured(self, client_cls, media_type):
        client = client_cls(api_key="test-key")

        with pytest.raises(MediaProviderError, match=f"{client.provider_display_name}提交地址未配置"):
            client._get_submit_endpoint()
