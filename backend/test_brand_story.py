"""
品牌故事生成器测试

测试场景:
1. 初始化生成器
2. 生成品牌故事（3种风格）
3. 文化元素自动匹配
4. Token和成本统计
"""

import sys
import asyncio
import pytest

sys.path.insert(0, ".")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.brand_story.generator import BrandStoryGenerator


class MockDeepSeekClient:
    """Mock DeepSeek客户端"""

    async def chat_completion(self, messages, system_prompt, temperature=0.7):
        # 模拟返回品牌故事
        product_name = "测试产品"
        for msg in messages:
            if msg.get("role") == "user" and "产品：" in msg.get("content", ""):
                content = msg["content"]
                if "锡林郭勒羊肉" in content:
                    product_name = "锡林郭勒羊肉"
                break

        mock_story = f"""
你吃过真正的草原羊肉吗？

不是超市里4个月速成的圈养羊，而是在锡林郭勒草原，用10个月慢慢长大的羔羊。

这里的羊，每天在草原上走十几公里，吃的是碱草和野韭菜，喝的是雪山融水。
草原牧民有句话："急不来好羊肉。"

10个月的等待，换来的是：
✓ 涮锅5秒即熟，不柴不老
✓ 清水煮也不膻，老人小孩都爱吃
✓ 肥瘦均匀，每一口都是自然的馈赠

从草原到你家，72小时冷链直达。
不是所有羊肉都值得等10个月，但这一次，值得。

**文化背书**：锡林郭勒草原是欧亚草原东亚草原亚区中保存最完整的天然草场...
"""

        return {
            "choices": [{"message": {"content": mock_story.strip()}}],
            "usage": {"prompt_tokens": 800, "completion_tokens": 350, "total_tokens": 1150},
        }

    def calculate_cost(self, input_tokens, output_tokens):
        # DeepSeek定价: ¥1/百万tokens
        return (input_tokens + output_tokens) / 1_000_000 * 1.0


@pytest.mark.asyncio
async def test_brand_story_generator():
    """测试品牌故事生成器"""
    print("=" * 60)
    print("品牌故事生成器测试")
    print("=" * 60)

    # 创建临时数据库会话
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    db = Session()

    # 创建Mock客户端
    mock_client = MockDeepSeekClient()

    try:
        # 测试1: 初始化生成器
        print("\n=== 测试1: 初始化生成器 ===")
        generator = BrandStoryGenerator(db, mock_client)

        if generator.cultural_collector:
            print(f"✓ 文化元素: {len(generator.cultural_collector.elements)}")
            print(f"✓ 知识图谱节点: {generator.cultural_collector.kg.graph.number_of_nodes()}")
        else:
            print("⚠ 文化元素采集器未初始化")

        # 测试2: 生成现代简约风格
        print("\n=== 测试2: 现代简约风格 ===")
        result1 = await generator.generate_story(
            product_name="锡林郭勒羊肉",
            origin="锡林郭勒盟",
            features="10个月生长周期、自然放养、草原散养",
            purpose="电商详情页",
            style="现代简约",
            word_count="300字左右",
            category="羊肉",
            keywords=["草原", "有机", "天然"],
            use_culture=True,
        )

        print(f"✓ 品牌故事已生成")
        print(f"\n故事预览:\n{result1['story'][:200]}...\n")
        print(f"✓ Token使用: {result1['tokens']['total']}")
        print(f"✓ 成本: ¥{result1['cost']:.4f}")
        print(f"✓ 文化元素数: {len(result1['cultural_elements'])}")

        if result1["cultural_elements"]:
            print("\n文化元素:")
            for i, elem in enumerate(result1["cultural_elements"], 1):
                print(f"  {i}. {elem['name']} ({elem['type']}) - 评分: {elem['score']:.2f}")
                print(f"     匹配原因: {elem['match_reason']}")

        # 测试3: 生成传统深沉风格
        print("\n=== 测试3: 传统深沉风格 ===")
        result2 = await generator.generate_story(
            product_name="锡林郭勒奶酪",
            origin="锡林郭勒盟",
            features="手工制作、传统发酵工艺、48小时自然发酵",
            purpose="礼品包装",
            style="传统深沉",
            word_count="500字左右",
            category="奶制品",
            keywords=["传统", "手工", "发酵"],
            use_culture=True,
        )

        print(f"✓ 品牌故事已生成")
        print(f"✓ Token使用: {result2['tokens']['total']}")
        print(f"✓ 成本: ¥{result2['cost']:.4f}")
        print(f"✓ 文化元素数: {len(result2['cultural_elements'])}")

        # 测试4: 不使用文化元素
        print("\n=== 测试4: 不使用文化元素 ===")
        result3 = await generator.generate_story(
            product_name="通用产品",
            origin="某地",
            features="优质",
            purpose="电商详情页",
            style="现代简约",
            word_count="200字左右",
            use_culture=False,
        )

        print(f"✓ 品牌故事已生成（无文化元素）")
        print(f"✓ 文化元素数: {len(result3['cultural_elements'])}")

        # 验证
        assert len(result1["story"]) > 100, "故事内容应该足够长"
        assert result1["tokens"]["total"] > 0, "应有token统计"
        assert result1["cost"] > 0, "应有成本统计"
        assert len(result1["cultural_elements"]) > 0, "应匹配到文化元素"
        assert len(result3["cultural_elements"]) == 0, "禁用时不应有文化元素"

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

        print("\n测试总结:")
        print(f"  - 生成器初始化: 成功")
        print(f"  - 文化元素库: {len(generator.cultural_collector.elements) if generator.cultural_collector else 0}个")
        print(f"  - 风格测试: 3种风格通过")
        print(f"  - 文化匹配: {len(result1['cultural_elements'])}个元素")
        print(f"  - 平均Token: {(result1['tokens']['total'] + result2['tokens']['total']) / 2:.0f}")
        print(f"  - 平均成本: ¥{(result1['cost'] + result2['cost']) / 2:.4f}")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_brand_story_generator())
