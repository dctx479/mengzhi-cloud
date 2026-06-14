"""MultimediaProvider 抽象基类 + MultimediaProviderFactory 测试套件。"""
import sys
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

sys.path.insert(0, ".")

from app.services.ai.multimedia_provider import (
    MultimediaProvider,
    MediaCapability,
    UnsupportedCapabilityError,
)
from app.services.ai.multimedia_factory import MultimediaProviderFactory
from app.services.ai.providers.jimeng_provider import JimengAI


# ===== 抽象基类测试 =====

def test_base_class_is_abstract():
    """MultimediaProvider 不能直接实例化"""
    with pytest.raises(TypeError):
        MultimediaProvider(api_key="k")


class _ImageOnlyProvider(MultimediaProvider):
    """仅声明 IMAGE 能力的测试桩"""

    @property
    def name(self):
        return "image-only"

    @property
    def supported_models(self):
        return ["m1"]

    @property
    def capabilities(self):
        return {MediaCapability.IMAGE}

    async def test_connection(self):
        return {"success": True}

    async def generate_image(self, prompt, **opts):
        return {"image_url": "https://img/x.jpg", "prompt": prompt}


@pytest.mark.asyncio
async def test_unsupported_capability_raises():
    """未声明的能力调用时抛 UnsupportedCapabilityError"""
    p = _ImageOnlyProvider(api_key="k")
    assert p.supports(MediaCapability.IMAGE) is True
    assert p.supports(MediaCapability.VIDEO) is False
    assert p.supports(MediaCapability.AUDIO) is False

    result = await p.generate_image("test")
    assert result["image_url"] == "https://img/x.jpg"

    with pytest.raises(UnsupportedCapabilityError):
        await p.generate_video("test")
    with pytest.raises(UnsupportedCapabilityError):
        await p.generate_audio("test")


# ===== JimengAI 接入测试 =====

def test_jimeng_is_multimedia_provider():
    client = JimengAI(api_key="k")
    assert isinstance(client, MultimediaProvider)
    assert client.name == "jimeng"
    assert client.capabilities == {
        MediaCapability.IMAGE,
        MediaCapability.VIDEO,
        MediaCapability.AUDIO,
    }


def test_jimeng_constructor_base_url_and_endpoint():
    """base_url 与 endpoint 两种入参都映射到 self.endpoint"""
    c_endpoint = JimengAI(api_key="k", endpoint="https://e1")
    c_baseurl = JimengAI(api_key="k", base_url="https://e2")
    c_default = JimengAI(api_key="k")
    assert c_endpoint.endpoint == "https://e1"
    assert c_baseurl.endpoint == "https://e2"
    assert c_default.endpoint == "https://visual.volcengineapi.com"


def test_jimeng_generate_video_is_native():
    """JimengAI 的 generate_video 是自身实现, 而非基类默认 (抛异常版)"""
    assert JimengAI.generate_video is not MultimediaProvider.generate_video


@pytest.mark.asyncio
async def test_generate_image_delegates_to_text_to_image():
    client = JimengAI(api_key="k")
    with patch.object(client, "text_to_image", new=AsyncMock(return_value={"image_url": "u"})) as m:
        result = await client.generate_image("猫", model="text-to-image-3.1", width=512)
        m.assert_awaited_once_with("猫", model="text-to-image-3.1", width=512)
        assert result == {"image_url": "u"}


@pytest.mark.asyncio
async def test_generate_audio_delegates_to_text_to_speech():
    client = JimengAI(api_key="k")
    with patch.object(client, "text_to_speech", new=AsyncMock(return_value={"audio_url": "a"})) as m:
        result = await client.generate_audio("你好", voice="female_1")
        m.assert_awaited_once_with("你好", voice="female_1")
        assert result == {"audio_url": "a"}


# ===== 工厂测试 =====

def setup_function():
    """每个测试前清缓存, 避免实例缓存交叉污染"""
    MultimediaProviderFactory.clear_cache()


def test_factory_create_and_cache():
    a = MultimediaProviderFactory.create("jimeng", "key123", base_url="https://x")
    b = MultimediaProviderFactory.create("jimeng", "key123")
    assert a is b  # 同 provider+api_key 命中缓存
    assert isinstance(a, JimengAI)


def test_factory_unknown_provider_raises():
    with pytest.raises(ValueError):
        MultimediaProviderFactory.create("nope", "k")


def test_factory_get_supported_providers():
    assert "jimeng" in MultimediaProviderFactory.get_supported_providers()


def test_factory_register_provider():
    MultimediaProviderFactory.register_provider("image-only", _ImageOnlyProvider)
    try:
        inst = MultimediaProviderFactory.create("image-only", "k")
        assert isinstance(inst, _ImageOnlyProvider)
    finally:
        MultimediaProviderFactory._providers.pop("image-only", None)


def _mock_db_first(config):
    """构造一个 .query().filter()....first() 链返回 config 的 mock db"""
    db = MagicMock()
    query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = query
    query.order_by.return_value = query
    query.first.return_value = config
    return db


def test_resolve_for_enterprise_no_config_returns_none():
    db = _mock_db_first(None)
    result = MultimediaProviderFactory.resolve_for_enterprise(db, enterprise_id=1, provider_type="jimeng")
    assert result is None


def test_resolve_for_enterprise_returns_instance():
    config = MagicMock()
    config.provider = "jimeng"
    config.base_url = "https://visual.volcengineapi.com"
    config.api_key_encrypted = "encrypted"
    db = _mock_db_first(config)
    with patch("app.services.ai.multimedia_factory.decrypt_api_key", return_value="plain_key"):
        result = MultimediaProviderFactory.resolve_for_enterprise(db, enterprise_id=None, provider_type="jimeng")
    assert isinstance(result, JimengAI)
    assert result.api_key == "plain_key"
