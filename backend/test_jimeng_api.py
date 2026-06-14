"""Jimeng AI API test suite."""
import sys, time
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
sys.path.insert(0, ".")
from app.services.ai.providers.jimeng_provider import (
    JimengAI, JimengAPIError, JimengClient,
    IMAGE_MODELS, VIDEO_MODELS, AUDIO_MODELS, SUPPORTED_MODELS,
)

@pytest.fixture
def client():
    return JimengAI(api_key="mock_api_key", endpoint="https://visual.volcengineapi.com")


@pytest.fixture
def mock_client_cls():
    with patch("httpx.AsyncClient") as cls:
        mock_client = AsyncMock()
        cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        cls.return_value.__aexit__ = AsyncMock(return_value=None)
        yield cls, mock_client


def make_response(json_data, status_error=None):
    r = AsyncMock()
    r.json = MagicMock(return_value=json_data)
    r.raise_for_status = MagicMock(side_effect=status_error) if status_error else MagicMock()
    r.status_code = 200
    return r


# ===== 模型常量测试 =====

def test_image_models_count():
    assert len(IMAGE_MODELS) == 8
    assert "text-to-image-3.0" in IMAGE_MODELS
    assert "text-to-image-3.1" in IMAGE_MODELS
    assert "image-generation-4.0" in IMAGE_MODELS
    assert "image-generation-4.6" in IMAGE_MODELS
    assert "image-to-image-3.0" in IMAGE_MODELS
    assert "material-extraction" in IMAGE_MODELS
    assert "inpainting" in IMAGE_MODELS
    assert "outpainting" in IMAGE_MODELS
    print("OK: Image models (8)")

def test_video_models_count():
    assert len(VIDEO_MODELS) == 5
    assert "video-generation-3.0-pro" in VIDEO_MODELS
    assert "video-generation-3.0-720p" in VIDEO_MODELS
    assert "video-generation-3.0-1080p" in VIDEO_MODELS
    assert "action-imitation" in VIDEO_MODELS
    assert "omni-human-1.5" in VIDEO_MODELS
    print("OK: Video models (5)")

def test_audio_models_count():
    assert len(AUDIO_MODELS) == 1
    assert "tts" in AUDIO_MODELS
    print("OK: Audio models (1)")

def test_supported_models_total(client):
    assert len(SUPPORTED_MODELS) == 14
    assert client.supported_models == SUPPORTED_MODELS
    print("OK: Total models (14)")

def test_model_pricing():
    assert IMAGE_MODELS["text-to-image-3.0"]["price"] == 0.2
    assert IMAGE_MODELS["text-to-image-3.1"]["price"] == 0.2
    assert IMAGE_MODELS["image-generation-4.0"]["price"] == 0.5
    assert IMAGE_MODELS["image-generation-4.6"]["price"] == 0.5
    assert IMAGE_MODELS["material-extraction"]["price"] == 0.5
    print("OK: Model pricing")


# ===== 客户端初始化测试 =====

def test_client_name(client):
    assert client.name == "jimeng"
    print("OK: Client name")

def test_client_default_endpoint(client):
    assert client.endpoint == "https://visual.volcengineapi.com"
    print("OK: Default endpoint")

def test_client_custom_endpoint():
    c = JimengAI(api_key="k", endpoint="https://custom.volcengineapi.com")
    assert c.endpoint == "https://custom.volcengineapi.com"
    print("OK: Custom endpoint")

def test_client_headers(client):
    assert "Authorization" in client.headers
    assert client.headers["Authorization"] == "Bearer mock_api_key"
    assert client.headers["Content-Type"] == "application/json"
    print("OK: Headers")

def test_jimeng_client_alias():
    assert JimengClient is JimengAI
    print("OK: JimengClient alias")


# ===== 图像生成测试 =====

@pytest.mark.asyncio
async def test_text_to_image_v31(client, mock_client_cls):
    cls, mc = mock_client_cls
    data = {"code": 0, "data": {"image_url": "https://img.jimeng.io/1.jpg", "task_id": "t1"}}
    mc.request = AsyncMock(return_value=make_response(data))
    result = await client.text_to_image("a cat", model="text-to-image-3.1", width=1024, height=1024)
    assert result["model"] == "text-to-image-3.1"
    assert result["image_url"] == "https://img.jimeng.io/1.jpg"
    assert result["cost_cny"] == 0.2
    call_args = mc.request.call_args
    assert call_args.kwargs["json"]["prompt"] == "a cat"
    print("OK: text_to_image v3.1")

@pytest.mark.asyncio
async def test_text_to_image_v40(client, mock_client_cls):
    cls, mc = mock_client_cls
    data = {"code": 0, "data": {"image_url": "https://img.jimeng.io/2.jpg", "task_id": "t2"}}
    mc.request = AsyncMock(return_value=make_response(data))
    result = await client.text_to_image("a dog", model="image-generation-4.0", width=512, height=512)
    assert result["model"] == "image-generation-4.0"
    assert result["cost_cny"] == 0.5
    call_args = mc.request.call_args
    assert call_args.kwargs["json"]["aspect_ratio"] == "512:512"
    print("OK: text_to_image v4.0")

@pytest.mark.asyncio
async def test_text_to_image_unknown_model(client, mock_client_cls):
    cls, mc = mock_client_cls
    try:
        await client.text_to_image("test", model="unknown-model")
    except ValueError as e:
        assert "Unknown image model" in str(e)
    print("OK: text_to_image unknown model error")

@pytest.mark.asyncio
async def test_image_to_image(client, mock_client_cls):
    cls, mc = mock_client_cls
    data = {"code": 0, "data": {"image_url": "https://img.jimeng.io/3.jpg", "task_id": "t3"}}
    mc.request = AsyncMock(return_value=make_response(data))
    result = await client.image_to_image("https://ref.jpg", "style transfer", strength=0.8)
    assert result["model"] == "image-to-image-3.0"
    assert result["cost_cny"] == 0.2
    print("OK: image_to_image")


# ===== 视频生成测试 =====

@pytest.mark.asyncio
async def test_generate_video_sync(client, mock_client_cls):
    cls, mc = mock_client_cls
    submit_data = {"code": 0, "data": {"task_id": "vid-1"}}
    poll_data = {"code": 0, "data": {"status": "completed", "video_url": "https://video.jimeng.io/1.mp4"}}
    mc.request = AsyncMock(side_effect=[
        make_response(submit_data),
        make_response(poll_data),
    ])
    result = await client.generate_video("a cat running", model="video-generation-3.0-pro", wait=True)
    assert result["model"] == "video-generation-3.0-pro"
    assert result["status"] == "completed"
    assert result["video_url"] == "https://video.jimeng.io/1.mp4"
    print("OK: generate_video sync (wait=True)")

@pytest.mark.asyncio
async def test_generate_video_async(client, mock_client_cls):
    cls, mc = mock_client_cls
    submit_data = {"code": 0, "data": {"task_id": "vid-2"}}
    mc.request = AsyncMock(return_value=make_response(submit_data))
    result = await client.generate_video("a cat running", wait=False)
    assert result["status"] == "submitted"
    assert result["task_id"] == "vid-2"
    print("OK: generate_video async (wait=False)")


# ===== 音频生成测试 =====

@pytest.mark.asyncio
async def test_text_to_speech(client, mock_client_cls):
    cls, mc = mock_client_cls
    data = {"code": 0, "data": {"audio_url": "https://audio.jimeng.io/1.mp3", "duration_sec": 5}}
    mc.request = AsyncMock(return_value=make_response(data))
    result = await client.text_to_speech("hello world", voice="female_1", speed=1.0)
    assert result["model"] == "tts"
    assert result["audio_url"] == "https://audio.jimeng.io/1.mp3"
    assert result["voice"] == "female_1"
    call_args = mc.request.call_args
    assert call_args.kwargs["json"]["text"] == "hello world"
    print("OK: text_to_speech")


# ===== 错误处理测试 =====

@pytest.mark.asyncio
async def test_api_error_raises(client, mock_client_cls):
    cls, mc = mock_client_cls
    error_data = {"code": 10001, "message": "Invalid API key", "data": {}}
    mc.request = AsyncMock(return_value=make_response(error_data))
    try:
        await client.text_to_image("test")
    except JimengAPIError as e:
        assert e.code == 10001
        assert "Invalid API key" in str(e)
    print("OK: API error raises JimengAPIError")

@pytest.mark.asyncio
async def test_http_error_raises(client, mock_client_cls):
    cls, mc = mock_client_cls
    import httpx
    mc.request = AsyncMock(side_effect=httpx.HTTPStatusError(
        "401",
        request=MagicMock(),
        response=MagicMock(status_code=401),
    ))
    try:
        await client.text_to_image("test")
    except httpx.HTTPStatusError:
     pass
    else:
         assert False, "Expected HTTPStatusError"
    print("OK: HTTP error raises")

@pytest.mark.asyncio
async def test_task_failed_raises(client, mock_client_cls):
    cls, mc = mock_client_cls
    submit_data = {"code": 0, "data": {"task_id": "vid-fail"}}
    poll_data = {"code": 0, "data": {"status": "failed", "error": "GPU quota exceeded"}}
    mc.request = AsyncMock(side_effect=[
        make_response(submit_data),
        make_response(poll_data),
    ])
    try:
        await client.generate_video("test", wait=True)
    except JimengAPIError as e:
        assert "GPU quota exceeded" in str(e)
    print("OK: Task failed raises")


# ===== test_connection 测试 =====

@pytest.mark.asyncio
async def test_test_connection_success(client, mock_client_cls):
    cls, mc = mock_client_cls
    data = {"code": 0, "data": {"image_url": "https://img.jimeng.io/test.jpg", "task_id": "test-t"}}
    mc.request = AsyncMock(return_value=make_response(data))
    result = await client.test_connection()
    assert result["success"] is True
    assert "latency_ms" in result
    print("OK: test_connection success")

@pytest.mark.asyncio
async def test_test_connection_failure(client, mock_client_cls):
    cls, mc = mock_client_cls
    data = {"code": 10001, "message": "Invalid key"}
    mc.request = AsyncMock(return_value=make_response(data))
    result = await client.test_connection()
    assert result["success"] is False
    assert "API error" in result["message"]
    print("OK: test_connection failure")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

