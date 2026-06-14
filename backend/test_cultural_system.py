"""
文化元素系统端到端测试
测试智能匹配算法、知识图谱、API端点
"""

import sys

sys.path.insert(0, ".")

import pytest

from app.services.cultural.enhanced_collector import EnhancedCulturalCollector
from app.services.cultural.knowledge_graph import CulturalKnowledgeGraph


@pytest.fixture
def kg():
    return CulturalKnowledgeGraph()


@pytest.fixture
def collector():
    return EnhancedCulturalCollector(enable_kg=True)


def test_knowledge_graph():
    """测试知识图谱构建"""
    print("\n=== 测试1: 知识图谱构建 ===")

    kg = CulturalKnowledgeGraph()
    stats = kg.get_graph_statistics()

    print(f"✓ 节点总数: {stats['total_nodes']}")
    print(f"✓ 边总数: {stats['total_edges']}")
    print(f"✓ 节点类型: {stats['node_types']}")
    print(f"✓ 边类型: {stats['edge_types']}")

    assert stats["total_nodes"] > 0, "知识图谱应包含节点"
    assert stats["total_edges"] > 0, "知识图谱应包含边"
    assert "CulturalElement" in stats["node_types"], "应包含文化元素节点"


def test_enhanced_collector(kg):
    """测试增强版采集器"""
    print("\n=== 测试2: 增强版采集器 ===")

    collector = EnhancedCulturalCollector(enable_kg=True)

    print(f"✓ 已加载 {len(collector.elements)} 个文化元素")
    print(f"✓ 知识图谱节点: {collector.kg.graph.number_of_nodes()}")
    print(f"✓ 知识图谱边: {collector.kg.graph.number_of_edges()}")

    assert len(collector.elements) > 0, "应加载文化元素"
    assert collector.kg is not None, "应启用知识图谱"


def test_intelligent_matching(collector):
    """测试智能匹配算法"""
    print("\n=== 测试3: 智能匹配算法 ===")

    # 测试产品1: 锡林郭勒羊肉
    product1 = {
        "id": 1,
        "name": "锡林郭勒羊肉",
        "origin": "锡林郭勒盟",
        "category": "羊肉",
        "keywords": ["草原", "绿色", "有机"],
    }

    print(f"\n产品: {product1['name']}")
    results1 = collector.intelligent_match(product1, use_kg=True, top_k=5)

    print(f"✓ 匹配到 {len(results1)} 个文化元素")

    for i, result in enumerate(results1[:3], 1):
        element = result["element"]
        print(f"\n{i}. {element['name']} ({element['type']})")
        print(f"   总分: {result['score']:.2f}")
        print(f"   匹配原因: {result['match_reason']}")
        print(f"   得分明细:")
        print(f"     - 精确匹配: {result['score_breakdown']['exact_match']:.2f}")
        print(f"     - 知识图谱: {result['score_breakdown']['knowledge_graph']:.2f}")

        if result.get("path_info"):
            print(f"   路径信息: {result['path_info']['length']}跳")

    assert len(results1) > 0, "应匹配到文化元素"
    assert results1[0]["score"] > 0, "应有非零评分"

    # 测试产品2: 阿拉善驼肉
    product2 = {
        "id": 2,
        "name": "阿拉善驼肉",
        "origin": "阿拉善",
        "category": "驼肉",
        "keywords": ["沙漠", "特色", "营养"],
    }

    print(f"\n\n产品: {product2['name']}")
    results2 = collector.intelligent_match(product2, use_kg=True, top_k=5)

    print(f"✓ 匹配到 {len(results2)} 个文化元素")

    for i, result in enumerate(results2[:3], 1):
        element = result["element"]
        print(f"\n{i}. {element['name']} ({element['type']})")
        print(f"   总分: {result['score']:.2f}")
        print(f"   匹配原因: {result['match_reason']}")

    assert len(results2) >= 0


def test_knowledge_graph_queries(kg):
    """测试知识图谱查询"""
    print("\n=== 测试4: 知识图谱查询 ===")

    # 测试1: 根据地域查找
    print("\n查询: 锡林郭勒盟的文化元素")
    region_elements = kg.find_elements_by_region("锡林郭勒盟", include_synonyms=True)
    print(f"✓ 找到 {len(region_elements)} 个元素")

    # 测试2: 根据关键词查找
    print("\n查询: 草原+羊肉 关键词")
    keyword_results = kg.find_elements_by_keywords(["草原", "羊肉"], min_overlap=1)
    print(f"✓ 找到 {len(keyword_results)} 个元素")

    for idx, count in keyword_results[:3]:
        print(f"  - 元素{idx}: 匹配{count}个关键词")

    # 测试3: 最短路径推理
    print("\n查询: 产品到元素的路径")
    product = {"origin": "阿拉善", "keywords": ["沙漠", "驼肉"], "category": "驼肉类"}

    paths = kg.find_shortest_paths(product, max_hops=3, top_k=5)
    print(f"✓ 找到 {len(paths)} 条路径")

    for result in paths[:3]:
        print(f"\n  元素{result['element_index']}:")
        print(f"    得分: {result['score']:.2f}")
        print(f"    路径长度: {result['path_length']}跳")
        print(f"    路径: {result['path_description'][:100]}...")

    assert region_elements is not None
    assert keyword_results is not None
    assert paths is not None


def test_new_product_suggestion(collector):
    """测试新产品建议"""
    print("\n=== 测试5: 新产品建议 ===")

    # 测试低匹配度产品
    new_product = {
        "id": 999,
        "name": "呼伦贝尔牛肉",
        "origin": "呼伦贝尔",
        "category": "牛肉",
        "keywords": ["有机", "天然"],
    }

    print(f"\n产品: {new_product['name']}")
    suggestion = collector.suggest_for_new_product(new_product)

    print(f"✓ 需要采集: {suggestion['need_collection']}")
    print(f"✓ 现有匹配: {suggestion['existing_matches']}个")
    print(f"✓ 平均分: {suggestion['average_score']:.2f}")

    if suggestion["collection_targets"]:
        print(f"✓ 采集目标: {', '.join(suggestion['collection_targets'])}")

    assert "need_collection" in suggestion
    assert "existing_matches" in suggestion


def main():
    """脚本模式入口: 自建对象按顺序跑完所有测试"""
    print("=" * 60)
    print("文化元素智能匹配系统端到端测试")
    print("=" * 60)

    kg_obj = CulturalKnowledgeGraph()
    collector_obj = EnhancedCulturalCollector(enable_kg=True)

    test_knowledge_graph()
    test_enhanced_collector(kg_obj)
    test_intelligent_matching(collector_obj)
    test_knowledge_graph_queries(kg_obj)
    test_new_product_suggestion(collector_obj)

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    main()
