"""
测试小数Agent文化元素集成

测试场景:
1. 初始化Agent并加载文化元素
2. 查询文化元素
3. 响应内容丰富化
"""

import sys

sys.path.insert(0, ".")

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.ip_agent.xiaoshu_agent import XiaoshuAgent


class MockLLMClient:
    """Mock LLM客户端"""

    async def chat_completion(self, messages, system_prompt, temperature=0.7):
        return {
            "choices": [{"message": {"content": "这是锡林郭勒的特产羊肉，来自广阔的大草原。"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }

    def calculate_cost(self, input_tokens, output_tokens):
        return 0.001


def test_xiaoshu_agent_cultural_integration():
    """测试小数Agent文化元素集成"""
    print("=" * 60)
    print("小数Agent文化元素集成测试")
    print("=" * 60)

    # 创建临时数据库会话
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    db = Session()

    # 创建Mock LLM客户端
    llm_client = MockLLMClient()

    try:
        # 测试1: 初始化Agent
        print("\n=== 测试1: 初始化Agent ===")
        agent = XiaoshuAgent(db, llm_client)

        print(f"✓ Agent类型: {agent.ip_type}")
        print(f"✓ Agent名称: {agent.ip_name}")

        assert agent.cultural_collector, "文化元素采集器未初始化"
        print(f"✓ 文化元素数量: {len(agent.cultural_collector.elements)}")
        print(f"✓ 知识图谱节点: {agent.cultural_collector.kg.graph.number_of_nodes()}")

        # 测试2: 查询文化元素
        print("\n=== 测试2: 查询文化元素 ===")

        cultural_elements = agent.query_cultural_elements(
            product_name="锡林郭勒羊肉", origin="锡林郭勒盟", category="羊肉", keywords=["草原", "有机"], top_k=3
        )

        print(f"✓ 匹配到 {len(cultural_elements)} 个文化元素")

        for i, element in enumerate(cultural_elements, 1):
            print(f"\n{i}. {element['name']} ({element['type']})")
            print(f"   评分: {element['score']:.2f}")
            print(f"   匹配原因: {element['match_reason']}")
            print(f"   故事预览: {element['story'][:80]}...")

        # 测试3: 响应内容丰富化
        print("\n=== 测试3: 响应内容丰富化 ===")

        base_response = "这是来自锡林郭勒的优质羊肉，肉质鲜嫩，营养丰富。"

        enriched_response = agent.enrich_response_with_culture(
            base_response=base_response,
            product_name="锡林郭勒羊肉",
            origin="锡林郭勒盟",
            category="羊肉",
            keywords=["草原"],
        )

        print(f"✓ 原始响应: {base_response}")
        print(f"\n✓ 丰富后响应:\n{enriched_response}")

        # 验证
        assert len(cultural_elements) > 0, "应该匹配到文化元素"
        assert enriched_response != base_response, "响应应该被丰富"
        assert "相关文化背景" in enriched_response, "应包含文化背景部分"

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    test_xiaoshu_agent_cultural_integration()
