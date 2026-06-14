"""
IP智能体单元测试

测试IP路由、Agent响应质量、人格一致性
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.services.ip_agent import IPRouter, IPType, XiaoshuAgent, XiaoshangAgent, IPAgentFactory


class TestIPRouter:
    """测试IP路由器"""

    def test_route_to_xiaoshu_product_inquiry(self):
        """测试产品咨询类消息路由到小数"""
        router = IPRouter()
        assert router.route("推荐一款羊肉") == IPType.XIAOSHU
        assert router.route("呼伦贝尔的特产有什么") == IPType.XIAOSHU
        assert router.route("草原文化有什么特点") == IPType.XIAOSHU

    def test_route_to_xiaoshang_marketing(self):
        """测试营销类消息路由到小商"""
        router = IPRouter()
        assert router.route("怎么写直播脚本") == IPType.XIAOSHANG
        assert router.route("抖音运营策略") == IPType.XIAOSHANG
        assert router.route("品牌文案怎么写") == IPType.XIAOSHANG

    def test_route_default_to_xiaoshu(self):
        """测试无明确关键词时默认路由到小数"""
        router = IPRouter()
        assert router.route("你好") == IPType.XIAOSHU
        assert router.route("今天天气怎么样") == IPType.XIAOSHU

    def test_route_with_conversation_history(self):
        """测试对话历史加权"""
        router = IPRouter()
        history = [
            {"role": "user", "content": "推荐羊肉", "ip_type": "xiaoshu"},
            {"role": "assistant", "content": "咱们草原上...", "ip_type": "xiaoshu"},
            {"role": "user", "content": "怎么吃", "ip_type": "xiaoshu"},
        ]

        # 连续3轮使用小数，即使消息无明确关键词，也应继续路由到小数
        result = router.route("还有别的吗", conversation_history=history)
        assert result == IPType.XIAOSHU

    def test_route_explanation(self):
        """测试路由解释生成"""
        router = IPRouter()
        ip_type = router.route("推荐一款羊肉")
        explanation = router.get_route_explanation("推荐一款羊肉", ip_type)
        assert "推荐" in explanation or "羊肉" in explanation


class TestXiaoshuAgent:
    """测试小数Agent"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_llm_client(self):
        """模拟LLM客户端"""
        client = Mock()
        client.chat_completion = AsyncMock(
            return_value={
                "choices": [{"message": {"content": "咱们草原上的羊肉啊..."}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
            }
        )
        client.calculate_cost = Mock(return_value=0.0015)
        return client

    @pytest.mark.asyncio
    async def test_xiaoshu_response_generation(self, mock_db, mock_llm_client):
        """测试小数响应生成"""
        agent = XiaoshuAgent(mock_db, mock_llm_client)

        response = await agent.generate_response("推荐一款羊肉")

        assert response["content"] is not None
        assert response["metadata"]["ip_type"] == "xiaoshu"
        assert response["metadata"]["ip_name"] == "小数"
        assert response["tokens"]["total"] == 300
        assert response["cost"] == 0.0015

    def test_xiaoshu_system_prompt(self, mock_db, mock_llm_client):
        """测试小数系统提示词"""
        agent = XiaoshuAgent(mock_db, mock_llm_client)
        prompt = agent._get_system_prompt()

        # 验证人设关键词（对齐 prompts_fusion 实际文案）
        assert "小数" in prompt
        assert "蒙古族" in prompt
        assert "呼伦贝尔" in prompt
        assert "传承者" in prompt

    def test_xiaoshu_few_shot_examples(self, mock_db, mock_llm_client):
        """测试小数Few-shot示例"""
        agent = XiaoshuAgent(mock_db, mock_llm_client)
        examples = agent._get_few_shot_examples()

        assert len(examples) >= 3
        assert all("user" in ex and "assistant" in ex for ex in examples)
        # 验证示例中包含人设特征
        assert any("草原" in ex["assistant"] for ex in examples)

    def test_xiaoshu_extract_cultural_elements(self, mock_db, mock_llm_client):
        """测试文化元素提取"""
        agent = XiaoshuAgent(mock_db, mock_llm_client)
        elements = agent._extract_cultural_elements("呼伦贝尔草原的那达慕大会")

        assert "呼伦贝尔" in elements
        assert "草原" in elements
        assert "那达慕" in elements


class TestXiaoshangAgent:
    """测试小商Agent"""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def mock_llm_client(self):
        client = Mock()
        client.chat_completion = AsyncMock(
            return_value={
                "choices": [{"message": {"content": "根据我们的分析..."}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
            }
        )
        client.calculate_cost = Mock(return_value=0.0015)
        return client

    @pytest.mark.asyncio
    async def test_xiaoshang_response_generation(self, mock_db, mock_llm_client):
        """测试小商响应生成"""
        agent = XiaoshangAgent(mock_db, mock_llm_client)

        response = await agent.generate_response("怎么写直播脚本")

        assert response["content"] is not None
        assert response["metadata"]["ip_type"] == "xiaoshang"
        assert response["metadata"]["ip_name"] == "小商"

    def test_xiaoshang_system_prompt(self, mock_db, mock_llm_client):
        """测试小商系统提示词"""
        agent = XiaoshangAgent(mock_db, mock_llm_client)
        prompt = agent._get_system_prompt()

        # 验证人设关键词（对齐 prompts_fusion 实际文案）
        assert "小商" in prompt
        assert "营销" in prompt
        assert "品牌" in prompt
        assert "抖音" in prompt

    def test_xiaoshang_analyze_marketing_intent(self, mock_db, mock_llm_client):
        """测试营销意图分析"""
        agent = XiaoshangAgent(mock_db, mock_llm_client)

        intents = agent._analyze_marketing_intent("怎么写抖音直播脚本")
        assert "content_creation" in intents
        assert "platform_strategy" in intents
        assert "live_streaming" in intents


class TestIPAgentFactory:
    """测试IP Agent工厂"""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def mock_llm_client(self):
        return Mock()

    def test_create_xiaoshu_agent(self, mock_db, mock_llm_client):
        """测试创建小数Agent"""
        agent = IPAgentFactory.create_agent(IPType.XIAOSHU, mock_db, mock_llm_client)
        assert isinstance(agent, XiaoshuAgent)
        assert agent.ip_type == "xiaoshu"
        assert agent.ip_name == "小数"

    def test_create_xiaoshang_agent(self, mock_db, mock_llm_client):
        """测试创建小商Agent"""
        agent = IPAgentFactory.create_agent(IPType.XIAOSHANG, mock_db, mock_llm_client)
        assert isinstance(agent, XiaoshangAgent)
        assert agent.ip_type == "xiaoshang"
        assert agent.ip_name == "小商"

    def test_get_available_ips(self):
        """测试获取可用IP列表"""
        ips = IPAgentFactory.get_available_ips()
        assert "xiaoshu" in ips
        assert "xiaoshang" in ips
        assert ips["xiaoshu"]["name"] == "小数"
        assert ips["xiaoshang"]["name"] == "小商"


class TestIPPersonalityConsistency:
    """测试IP人格一致性"""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def mock_llm_client(self):
        """使用真实响应模拟LLM"""

        def create_xiaoshu_response(*args, **kwargs):
            # 模拟小数的真实回答
            return {
                "choices": [
                    {
                        "message": {
                            "content": "咱们草原上的羊肉啊，要是送礼的话，我推荐您看看呼伦贝尔的羔羊肉！就像老额吉说的，'好草养好羊，好羊出好肉'。"
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            }

        client = Mock()
        client.chat_completion = AsyncMock(side_effect=create_xiaoshu_response)
        client.calculate_cost = Mock(return_value=0.001)
        return client

    @pytest.mark.asyncio
    async def test_xiaoshu_personality_keywords(self, mock_db, mock_llm_client):
        """测试小数人设关键词出现率"""
        agent = XiaoshuAgent(mock_db, mock_llm_client)
        response = await agent.generate_response("推荐羊肉")

        content = response["content"]

        # 检查人设特征词
        personality_keywords = ["咱们草原", "老额吉", "草原上"]
        has_personality = any(kw in content for kw in personality_keywords)

        assert has_personality, "响应缺少小数的人设特征词"


# ============ 运行测试 ============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
