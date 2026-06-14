"""Volcengine API test suite."""
import sys, time, asyncio, pytest
from unittest.mock import patch, AsyncMock, MagicMock
sys.path.insert(0, ".")
from app.services.ai.providers.volcengine_provider import VolcengineProvider
from app.services.ai.base_provider import (
    ChatCompletionRequest, ChatMessage, ChatCompletionResponse, Usage,
)

@pytest.fixture
def provider():
    return VolcengineProvider(api_key="mock_api_key_for_testing")

@pytest.fixture
def chat_request():
    return ChatCompletionRequest(messages=[ChatMessage(role="user", content="hi")], model="doubao-lite-4k", max_tokens=10, temperature=0.0)

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

@pytest.mark.asyncio
async def test_connection_success(provider, mock_client_cls):
    cls, mc = mock_client_cls
    data = {"id": "c1", "choices": [{"message": {"role": "assistant", "content": "hi"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}, "model": "doubao-lite-4k"}
    mc.post = AsyncMock(return_value=make_response(data))
    r = await provider.test_connection()
    assert r["success"] is True
    assert r["model"] == "doubao-lite-4k"
    print("OK: Connection success")

@pytest.mark.asyncio
async def test_connection_failure(provider, mock_client_cls):
    import httpx
    cls, mc = mock_client_cls
    mc.post = AsyncMock(return_value=make_response({}, httpx.HTTPStatusError("401", request=MagicMock(), response=MagicMock(status_code=401))))
    r = await provider.test_connection()
    assert r["success"] is False
    assert "HTTP error" in r["message"]
    print("OK: Connection failure")

@pytest.mark.asyncio
async def test_chat_basic(provider, chat_request, mock_client_cls):
    cls, mc = mock_client_cls
    data = {"id": "c1", "choices": [{"message": {"role": "assistant", "content": "hello"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}, "model": "doubao-lite-4k"}
    mc.post = AsyncMock(return_value=make_response(data))
    response = await provider.chat(chat_request)
    assert isinstance(response, ChatCompletionResponse)
    assert response.content == "hello"
    assert response.model == "doubao-lite-4k"
    assert response.usage.total_tokens == 30
    print("OK: Chat basic")

@pytest.mark.asyncio
async def test_chat_multi_turn(provider, mock_client_cls):
    cls, mc = mock_client_cls
    req = ChatCompletionRequest(messages=[ChatMessage(role="system", content="s"), ChatMessage(role="user", content="u1"), ChatMessage(role="assistant", content="a1"), ChatMessage(role="user", content="u2")], model="doubao-pro-32k")
    data = {"id": "m1", "choices": [{"message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}, "model": "doubao-pro-32k"}
    mc.post = AsyncMock(return_value=make_response(data))
    await provider.chat(req)
    body = mc.post.call_args.kwargs["json"]
    assert len(body["messages"]) == 4
    assert body["messages"][3]["content"] == "u2"
    print("OK: Chat multi-turn")

@pytest.mark.asyncio
async def test_chat_invalid_response(provider, chat_request, mock_client_cls):
    cls, mc = mock_client_cls
    mc.post = AsyncMock(return_value=make_response({"id": "bad"}))
    try:
        await provider.chat(chat_request)
    except ValueError:
        pass
    else:
        assert False, "Expected ValueError"
    print("OK: Chat invalid response")

@pytest.mark.asyncio
async def test_chat_stream(provider, chat_request, mock_client_cls):
    cls, mc = mock_client_cls
    async def aiter():
        yield "data: " + chr(123) + chr(34) + "id" + chr(34) + ":1" + chr(34) + chr(125)
        yield "data: [DONE]"
    r = AsyncMock()
    r.raise_for_status = MagicMock()
    r.aiter_lines = aiter
    stream_ctx = AsyncMock()
    stream_ctx.__aenter__ = AsyncMock(return_value=r)
    stream_ctx.__aexit__ = AsyncMock(return_value=None)
    mc.stream = MagicMock(return_value=stream_ctx)
    chunks = []
    async for c in provider.chat_stream(chat_request):
        chunks.append(c)
    stream_call = mc.stream.call_args
    assert stream_call.kwargs["json"]["stream"] is True
    print("OK: Chat stream (verified stream=True)")

@pytest.mark.asyncio
async def test_embedding_single(provider, mock_client_cls):
    cls, mc = mock_client_cls
    data = {"data": [{"embedding": [0.1, 0.2, 0.3, 0.4]}]}
    mc.post = AsyncMock(return_value=make_response(data))
    embeddings = await provider.embedding(["hello"])
    assert len(embeddings) == 1
    assert embeddings[0] == [0.1, 0.2, 0.3, 0.4]
    print("OK: Embedding single")

@pytest.mark.asyncio
async def test_embedding_batch(provider, mock_client_cls):
    cls, mc = mock_client_cls
    data = {"data": [{"embedding": [0.1]}, {"embedding": [0.2]}, {"embedding": [0.3]}]}
    mc.post = AsyncMock(return_value=make_response(data))
    embeddings = await provider.embedding(["a", "b", "c"], model="doubao-embedding")
    assert len(embeddings) == 3
    body = mc.post.call_args.kwargs["json"]
    assert body["input"] == ["a", "b", "c"]
    assert body["model"] == "doubao-embedding"
    print("OK: Embedding batch")

@pytest.mark.asyncio
async def test_401_unauthorized(provider, chat_request, mock_client_cls):
    import httpx
    cls, mc = mock_client_cls
    mc.post = AsyncMock(return_value=make_response({}, httpx.HTTPStatusError("401", request=MagicMock(), response=MagicMock(status_code=401))))
    try:
        await provider.chat(chat_request)
    except httpx.HTTPStatusError:
        pass
    else:
        assert False
    print("OK: 401 Unauthorized")

@pytest.mark.asyncio
async def test_429_rate_limit(provider, chat_request, mock_client_cls):
    import httpx
    cls, mc = mock_client_cls
    mc.post = AsyncMock(return_value=make_response({}, httpx.HTTPStatusError("429", request=MagicMock(), response=MagicMock(status_code=429))))
    try:
        await provider.chat(chat_request)
    except httpx.HTTPStatusError:
        pass
    else:
        assert False
    print("OK: 429 Rate limit")

@pytest.mark.asyncio
async def test_timeout(provider, chat_request, mock_client_cls):
    import httpx
    cls, mc = mock_client_cls
    mc.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
    try:
        await provider.chat(chat_request)
    except httpx.TimeoutException:
        pass
    else:
        assert False
    print("OK: Timeout")

def test_provider_name(provider):
    assert provider.name == "volcengine"
    print("OK: Provider name")

def test_supported_models(provider):
    models = provider.supported_models
    # 1.5 series
    assert "doubao-1-5-pro-32k" in models
    assert "doubao-1-5-pro-256k" in models
    assert "doubao-1-5-lite-32k" in models
    assert "doubao-1-5-lite-128k" in models
    # 1.0 series
    assert "doubao-pro-32k" in models
    assert "doubao-lite-4k" in models
    # vision
    assert "doubao-1-5-vision-pro-32k" in models
    # embedding
    assert "doubao-embedding" in models
    assert len(models) >= 10
    print("OK: Supported models (15 total)")

def test_default_base_url(provider):
    assert provider._get_base_url() == "https://ark.cn-beijing.volces.com/api/v3"
    print("OK: Default base URL")

def test_custom_base_url():
    p = VolcengineProvider(api_key="test", base_url="https://custom.endpoint.com/api/v3")
    assert p._get_base_url() == "https://custom.endpoint.com/api/v3"
    print("OK: Custom base URL")

@pytest.mark.asyncio
async def test_concurrent_requests(provider, mock_client_cls):
    cls, mc = mock_client_cls
    data = {"id": "c", "choices": [{"message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}, "model": "doubao-lite-4k"}
    mc.post = AsyncMock(return_value=make_response(data))
    reqs = [ChatCompletionRequest(messages=[ChatMessage(role="user", content=f"Q{i}")], model="doubao-lite-4k") for i in range(5)]
    responses = await asyncio.gather(*[provider.chat(req) for req in reqs])
    assert len(responses) == 5
    print("OK: Concurrent requests (5)")

@pytest.mark.asyncio
async def test_authorization_header(provider, chat_request, mock_client_cls):
    cls, mc = mock_client_cls
    data = {"id": "c", "choices": [{"message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}, "model": "doubao-lite-4k"}
    mc.post = AsyncMock(return_value=make_response(data))
    await provider.chat(chat_request)
    headers = mc.post.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer mock_api_key_for_testing"
    assert headers["Content-Type"] == "application/json"
    print("OK: Authorization header")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])