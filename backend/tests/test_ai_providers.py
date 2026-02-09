"""
AI Provider系统单元测试

测试内容:
1. BaseAIProvider抽象类
2. DeepSeekProvider实现
3. OpenAIProvider实现
4. AIProviderFactory工厂类
5. 配置验证和错误处理

覆盖率目标: >80%
"""

import pytest
import httpx
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import AsyncGenerator

from app.services.ai.base_provider import (
    BaseAIProvider,
    ChatMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    Usage
)
from app.services.ai.providers.deepseek_provider import DeepSeekProvider
from app.services.ai.providers.openai_provider import OpenAIProvider
from app.services.ai.factory import AIProviderFactory


# ==================== Fixtures ====================

@pytest.fixture
def mock_api_key():
    """模拟API密钥"""
    return "test-api-key-12345678"


@pytest.fixture
def mock_base_url():
    """模拟基础URL"""
    return "https://test-api.example.com"


@pytest.fixture
def sample_chat_request():
    """示例聊天请求"""
    return ChatCompletionRequest(
        messages=[
            ChatMessage(role="system", content="You are a helpful assistant."),
            ChatMessage(role="user", content="Hello, how are you?")
        ],
        model="test-model",
        temperature=0.7,
        max_tokens=100
    )


@pytest.fixture
def sample_api_response():
    """示例API响应"""
    return {
        "id": "chatcmpl-123",
        "model": "test-model",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "I'm doing well, thank you!"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 20,
            "completion_tokens": 10,
            "total_tokens": 30
        }
    }


@pytest.fixture
def sample_stream_chunks():
    """示例流式响应块"""
    return [
        'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n',
        'data: {"choices":[{"delta":{"content":" world"}}]}\n\n',
        'data: {"choices":[{"delta":{"content":"!"}}]}\n\n',
        'data: [DONE]\n\n'
    ]


# ==================== BaseAIProvider Tests ====================

class TestBaseAIProvider:
    """BaseAIProvider抽象类测试"""

    def test_cannot_instantiate_abstract_class(self):
        """测试不能直接实例化抽象类"""
        with pytest.raises(TypeError):
            BaseAIProvider(api_key="test-key")

    def test_concrete_implementation_required_methods(self, mock_api_key):
        """测试具体实现必须实现所有抽象方法"""

        class IncompleteProvider(BaseAIProvider):
            @property
            def name(self):
                return "incomplete"

        with pytest.raises(TypeError):
            IncompleteProvider(api_key=mock_api_key)

    def test_provider_initialization(self, mock_api_key, mock_base_url):
        """测试Provider初始化"""

        class TestProvider(BaseAIProvider):
            @property
            def name(self):
                return "test"

            @property
            def supported_models(self):
                return ["model-1", "model-2"]

            async def chat(self, request):
                pass

            async def chat_stream(self, request):
                pass

        provider = TestProvider(
            api_key=mock_api_key,
            base_url=mock_base_url,
            custom_param="value"
        )

        assert provider.api_key == mock_api_key
        assert provider.base_url == mock_base_url
        assert provider.config["custom_param"] == "value"
        assert provider.name == "test"
        assert "model-1" in provider.supported_models

    @pytest.mark.asyncio
    async def test_validate_config_success(self, mock_api_key):
        """测试配置验证成功"""

        class TestProvider(BaseAIProvider):
            @property
            def name(self):
                return "test"

            @property
            def supported_models(self):
                return ["model-1"]

            async def chat(self, request):
                return ChatCompletionResponse(
                    id="test-id",
                    content="test",
                    model="model-1",
                    usage=Usage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
                    finish_reason="stop"
                )

            async def chat_stream(self, request):
                pass

        provider = TestProvider(api_key=mock_api_key)
        is_valid = await provider.validate_config()

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_config_failure(self, mock_api_key):
        """测试配置验证失败"""

        class TestProvider(BaseAIProvider):
            @property
            def name(self):
                return "test"

            @property
            def supported_models(self):
                return ["model-1"]

            async def chat(self, request):
                raise Exception("API Error")

            async def chat_stream(self, request):
                pass

        provider = TestProvider(api_key=mock_api_key)
        is_valid = await provider.validate_config()

        assert is_valid is False


# ==================== DeepSeekProvider Tests ====================

class TestDeepSeekProvider:
    """DeepSeekProvider实现测试"""

    def test_provider_name(self, mock_api_key):
        """测试Provider名称"""
        provider = DeepSeekProvider(api_key=mock_api_key)
        assert provider.name == "deepseek"

    def test_supported_models(self, mock_api_key):
        """测试支持的模型列表"""
        provider = DeepSeekProvider(api_key=mock_api_key)
        assert "deepseek-chat" in provider.supported_models
        assert "deepseek-coder" in provider.supported_models

    def test_default_base_url(self, mock_api_key):
        """测试默认基础URL"""
        provider = DeepSeekProvider(api_key=mock_api_key)
        assert provider._get_base_url() == "https://api.deepseek.com"

    def test_custom_base_url(self, mock_api_key, mock_base_url):
        """测试自定义基础URL"""
        provider = DeepSeekProvider(api_key=mock_api_key, base_url=mock_base_url)
        assert provider._get_base_url() == mock_base_url

    @pytest.mark.asyncio
    async def test_chat_success(self, mock_api_key, sample_chat_request, sample_api_response):
        """测试非流式对话成功"""
        provider = DeepSeekProvider(api_key=mock_api_key)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = sample_api_response
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            response = await provider.chat(sample_chat_request)

            assert response.id == "chatcmpl-123"
            assert response.content == "I'm doing well, thank you!"
            assert response.model == "test-model"
            assert response.usage.total_tokens == 30
            assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_chat_with_default_model(self, mock_api_key):
        """测试使用默认模型"""
        provider = DeepSeekProvider(api_key=mock_api_key)
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="test")],
            model=None  # 不指定模型
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                "id": "test-id",
                "model": "deepseek-chat",
                "choices": [{"message": {"content": "test"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}
            }
            mock_response.raise_for_status = Mock()

            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await provider.chat(request)

            # 验证使用了默认模型
            call_args = mock_post.call_args
            assert call_args[1]["json"]["model"] == "deepseek-chat"

    @pytest.mark.asyncio
    async def test_chat_api_error(self, mock_api_key, sample_chat_request):
        """测试API错误处理"""
        provider = DeepSeekProvider(api_key=mock_api_key)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "API Error", request=Mock(), response=Mock()
            )

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(httpx.HTTPStatusError):
                await provider.chat(sample_chat_request)

    @pytest.mark.asyncio
    async def test_chat_stream_success(self, mock_api_key, sample_chat_request, sample_stream_chunks):
        """测试流式对话成功"""
        provider = DeepSeekProvider(api_key=mock_api_key)

        async def mock_aiter_lines():
            for chunk in sample_stream_chunks:
                yield chunk.strip()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.aiter_lines = mock_aiter_lines

            mock_stream_context = AsyncMock()
            mock_stream_context.__aenter__.return_value = mock_response
            mock_stream_context.__aexit__.return_value = None

            mock_client.return_value.__aenter__.return_value.stream = Mock(
                return_value=mock_stream_context
            )

            chunks = []
            async for chunk in provider.chat_stream(sample_chat_request):
                chunks.append(chunk)

            assert chunks == ["Hello", " world", "!"]

    @pytest.mark.asyncio
    async def test_chat_stream_skip_empty_lines(self, mock_api_key, sample_chat_request):
        """测试流式对话跳过空行"""
        provider = DeepSeekProvider(api_key=mock_api_key)

        async def mock_aiter_lines():
            yield ""
            yield ": comment"
            yield 'data: {"choices":[{"delta":{"content":"test"}}]}'
            yield "data: [DONE]"

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.aiter_lines = mock_aiter_lines

            mock_stream_context = AsyncMock()
            mock_stream_context.__aenter__.return_value = mock_response
            mock_stream_context.__aexit__.return_value = None

            mock_client.return_value.__aenter__.return_value.stream = Mock(
                return_value=mock_stream_context
            )

            chunks = []
            async for chunk in provider.chat_stream(sample_chat_request):
                chunks.append(chunk)

            assert chunks == ["test"]

    @pytest.mark.asyncio
    async def test_chat_stream_invalid_json(self, mock_api_key, sample_chat_request):
        """测试流式对话处理无效JSON"""
        provider = DeepSeekProvider(api_key=mock_api_key)

        async def mock_aiter_lines():
            yield 'data: invalid json'
            yield 'data: {"choices":[{"delta":{"content":"valid"}}]}'
            yield "data: [DONE]"

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.aiter_lines = mock_aiter_lines

            mock_stream_context = AsyncMock()
            mock_stream_context.__aenter__.return_value = mock_response
            mock_stream_context.__aexit__.return_value = None

            mock_client.return_value.__aenter__.return_value.stream = Mock(
                return_value=mock_stream_context
            )

            chunks = []
            async for chunk in provider.chat_stream(sample_chat_request):
                chunks.append(chunk)

            # 应该跳过无效JSON，只返回有效内容
            assert chunks == ["valid"]


# ==================== OpenAIProvider Tests ====================

class TestOpenAIProvider:
    """OpenAIProvider实现测试"""

    def test_provider_name(self, mock_api_key):
        """测试Provider名称"""
        provider = OpenAIProvider(api_key=mock_api_key)
        assert provider.name == "openai"

    def test_supported_models(self, mock_api_key):
        """测试支持的模型列表"""
        provider = OpenAIProvider(api_key=mock_api_key)
        assert "gpt-4" in provider.supported_models
        assert "gpt-4-turbo" in provider.supported_models
        assert "gpt-3.5-turbo" in provider.supported_models

    def test_default_base_url(self, mock_api_key):
        """测试默认基础URL"""
        provider = OpenAIProvider(api_key=mock_api_key)
        assert provider._get_base_url() == "https://api.openai.com/v1"

    def test_custom_base_url(self, mock_api_key, mock_base_url):
        """测试自定义基础URL"""
        provider = OpenAIProvider(api_key=mock_api_key, base_url=mock_base_url)
        assert provider._get_base_url() == mock_base_url

    @pytest.mark.asyncio
    async def test_chat_success(self, mock_api_key, sample_chat_request, sample_api_response):
        """测试非流式对话成功"""
        provider = OpenAIProvider(api_key=mock_api_key)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = sample_api_response
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            response = await provider.chat(sample_chat_request)

            assert response.id == "chatcmpl-123"
            assert response.content == "I'm doing well, thank you!"
            assert response.usage.prompt_tokens == 20

    @pytest.mark.asyncio
    async def test_chat_with_default_model(self, mock_api_key):
        """测试使用默认模型"""
        provider = OpenAIProvider(api_key=mock_api_key)
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="test")],
            model=None
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                "id": "test-id",
                "model": "gpt-3.5-turbo",
                "choices": [{"message": {"content": "test"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}
            }
            mock_response.raise_for_status = Mock()

            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await provider.chat(request)

            # 验证使用了默认模型
            call_args = mock_post.call_args
            assert call_args[1]["json"]["model"] == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_chat_stream_success(self, mock_api_key, sample_chat_request, sample_stream_chunks):
        """测试流式对话成功"""
        provider = OpenAIProvider(api_key=mock_api_key)

        async def mock_aiter_lines():
            for chunk in sample_stream_chunks:
                yield chunk.strip()

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.aiter_lines = mock_aiter_lines

            mock_stream_context = AsyncMock()
            mock_stream_context.__aenter__.return_value = mock_response
            mock_stream_context.__aexit__.return_value = None

            mock_client.return_value.__aenter__.return_value.stream = Mock(
                return_value=mock_stream_context
            )

            chunks = []
            async for chunk in provider.chat_stream(sample_chat_request):
                chunks.append(chunk)

            assert chunks == ["Hello", " world", "!"]


# ==================== AIProviderFactory Tests ====================

class TestAIProviderFactory:
    """AIProviderFactory工厂类测试"""

    def test_get_supported_providers(self):
        """测试获取支持的Provider列表"""
        providers = AIProviderFactory.get_supported_providers()
        assert "deepseek" in providers
        assert "openai" in providers

    def test_create_deepseek_provider(self, mock_api_key):
        """测试创建DeepSeek Provider"""
        provider = AIProviderFactory.create(
            provider_type="deepseek",
            api_key=mock_api_key
        )
        assert isinstance(provider, DeepSeekProvider)
        assert provider.name == "deepseek"

    def test_create_openai_provider(self, mock_api_key):
        """测试创建OpenAI Provider"""
        provider = AIProviderFactory.create(
            provider_type="openai",
            api_key=mock_api_key
        )
        assert isinstance(provider, OpenAIProvider)
        assert provider.name == "openai"

    def test_create_with_base_url(self, mock_api_key, mock_base_url):
        """测试创建Provider时指定base_url"""
        provider = AIProviderFactory.create(
            provider_type="deepseek",
            api_key=mock_api_key,
            base_url=mock_base_url
        )
        assert provider.base_url == mock_base_url

    def test_create_with_custom_kwargs(self, mock_api_key):
        """测试创建Provider时传递自定义参数"""
        provider = AIProviderFactory.create(
            provider_type="deepseek",
            api_key=mock_api_key,
            custom_param="value"
        )
        assert provider.config["custom_param"] == "value"

    def test_create_unknown_provider(self, mock_api_key):
        """测试创建未知Provider抛出异常"""
        with pytest.raises(ValueError, match="Unknown provider"):
            AIProviderFactory.create(
                provider_type="unknown",
                api_key=mock_api_key
            )

    def test_provider_caching(self, mock_api_key):
        """测试Provider实例缓存"""
        # 清空缓存
        AIProviderFactory._instances.clear()

        provider1 = AIProviderFactory.create(
            provider_type="deepseek",
            api_key=mock_api_key
        )
        provider2 = AIProviderFactory.create(
            provider_type="deepseek",
            api_key=mock_api_key
        )

        # 应该返回同一个实例
        assert provider1 is provider2

    def test_provider_caching_different_keys(self):
        """测试不同API密钥创建不同实例"""
        # 清空缓存
        AIProviderFactory._instances.clear()

        provider1 = AIProviderFactory.create(
            provider_type="deepseek",
            api_key="key-12345678"
        )
        provider2 = AIProviderFactory.create(
            provider_type="deepseek",
            api_key="key-87654321"
        )

        # 应该返回不同实例
        assert provider1 is not provider2

    def test_register_custom_provider(self, mock_api_key):
        """测试注册自定义Provider"""

        class CustomProvider(BaseAIProvider):
            @property
            def name(self):
                return "custom"

            @property
            def supported_models(self):
                return ["custom-model"]

            async def chat(self, request):
                pass

            async def chat_stream(self, request):
                pass

        AIProviderFactory.register_provider("custom", CustomProvider)

        assert "custom" in AIProviderFactory.get_supported_providers()

        provider = AIProviderFactory.create(
            provider_type="custom",
            api_key=mock_api_key
        )
        assert isinstance(provider, CustomProvider)
        assert provider.name == "custom"


# ==================== Integration Tests ====================

class TestProviderIntegration:
    """Provider集成测试"""

    @pytest.mark.asyncio
    async def test_full_chat_workflow(self, mock_api_key, sample_api_response):
        """测试完整的对话工作流"""
        # 创建Provider
        provider = AIProviderFactory.create(
            provider_type="deepseek",
            api_key=mock_api_key
        )

        # 准备请求
        request = ChatCompletionRequest(
            messages=[
                ChatMessage(role="system", content="You are helpful."),
                ChatMessage(role="user", content="Hello!")
            ],
            temperature=0.7,
            max_tokens=100
        )

        # Mock API调用
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = sample_api_response
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            # 执行对话
            response = await provider.chat(request)

            # 验证结果
            assert response.content == "I'm doing well, thank you!"
            assert response.usage.total_tokens == 30

    @pytest.mark.asyncio
    async def test_provider_switching(self, mock_api_key, sample_api_response):
        """测试在不同Provider之间切换"""
        # 创建DeepSeek Provider
        deepseek = AIProviderFactory.create(
            provider_type="deepseek",
            api_key=mock_api_key
        )

        # 创建OpenAI Provider
        openai = AIProviderFactory.create(
            provider_type="openai",
            api_key=mock_api_key
        )

        assert deepseek.name == "deepseek"
        assert openai.name == "openai"
        assert deepseek is not openai


# ==================== Error Handling Tests ====================

class TestErrorHandling:
    """错误处理测试"""

    @pytest.mark.asyncio
    async def test_network_timeout(self, mock_api_key, sample_chat_request):
        """测试网络超时"""
        provider = DeepSeekProvider(api_key=mock_api_key)

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )

            with pytest.raises(httpx.TimeoutException):
                await provider.chat(sample_chat_request)

    @pytest.mark.asyncio
    async def test_invalid_api_key(self, sample_chat_request):
        """测试无效API密钥"""
        provider = DeepSeekProvider(api_key="invalid-key")

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Unauthorized", request=Mock(), response=mock_response
            )

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(httpx.HTTPStatusError):
                await provider.chat(sample_chat_request)

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, mock_api_key, sample_chat_request):
        """测试速率限制错误"""
        provider = DeepSeekProvider(api_key=mock_api_key)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Rate limit exceeded", request=Mock(), response=mock_response
            )

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(httpx.HTTPStatusError):
                await provider.chat(sample_chat_request)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app.services.ai", "--cov-report=html"])
