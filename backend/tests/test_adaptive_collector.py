"""
文化元素自适应采集器测试

测试覆盖：
- 产品匹配算法（4维度评分）
- 场景匹配
- 类型匹配
- 新产品元素建议
- 评分边界条件

版本: 1.0
创建日期: 2026-06-12
"""

import pytest
import json
from unittest.mock import Mock, patch, mock_open
from app.services.cultural.adaptive_collector import AdaptiveCulturalCollector


@pytest.fixture
def sample_elements():
    """示例文化元素数据"""
    return [
        {
            "name": "锡林郭勒草原",
            "type": "地理景观",
            "story": "锡林郭勒草原是内蒙古四大草原之一...",
            "origin_region": "锡林郭勒盟",
            "keywords": ["草原", "畜牧", "生态"],
            "metadata": {
                "period": "现代",
                "related_products": ["羊肉", "牛肉", "马奶"],
                "cultural_significance": "蒙古族传统牧区",
                "usage_scenarios": ["品牌故事", "产品溯源"],
            },
        },
        {
            "name": "蒙古包制作",
            "type": "传统工艺",
            "story": "蒙古包是蒙古族传统居住建筑...",
            "origin_region": "呼伦贝尔",
            "keywords": ["蒙古包", "传统工艺", "游牧"],
            "metadata": {
                "period": "古代",
                "related_products": ["羊毛", "皮革"],
                "cultural_significance": "游牧文化象征",
                "usage_scenarios": ["文化展示"],
            },
        },
        {
            "name": "阿拉善驼铃",
            "type": "传统工艺",
            "story": "阿拉善驼铃是沙漠驼队的必备品...",
            "origin_region": "阿拉善",
            "keywords": ["驼铃", "沙漠", "骆驼"],
            "metadata": {
                "period": "古代",
                "related_products": ["驼肉", "驼奶"],
                "cultural_significance": "丝绸之路文化",
                "usage_scenarios": ["品牌故事", "文化背景"],
            },
        },
    ]


@pytest.fixture
def collector(sample_elements):
    """创建采集器实例"""
    with patch("builtins.open", mock_open(read_data=json.dumps(sample_elements))):
        return AdaptiveCulturalCollector()


# ==================== 产品匹配测试 ====================


def test_match_by_product_high_score(collector):
    """测试高匹配度产品（产地+产品类型+关键词全匹配）"""
    product_info = {
        "name": "锡林郭勒羊肉",
        "origin": "锡林郭勒盟",
        "category": "羊肉",
        "keywords": ["草原", "生态", "有机"],
    }

    matches = collector.match_by_product(product_info)

    # 应该找到锡林郭勒草原元素
    assert len(matches) > 0
    best_match = matches[0]

    # 验证最高匹配元素
    assert best_match["element"]["name"] == "锡林郭勒草原"

    # 验证评分（产地40 + 产品30 + 关键词20 + 类型权重 > 70分）
    assert best_match["score"] >= 70
    assert "match_reason" in best_match


def test_match_by_product_medium_score(collector):
    """测试中等匹配度产品（产地+产品匹配，关键词部分匹配）"""
    product_info = {"name": "锡林郭勒牛肉", "origin": "锡林郭勒盟", "category": "牛肉", "keywords": ["优质", "新鲜"]}

    matches = collector.match_by_product(product_info)

    assert len(matches) > 0
    best_match = matches[0]

    # 产地匹配40 + 产品匹配30 + 类型10 = 80分
    assert 50 <= best_match["score"] <= 90


def test_match_by_product_low_score(collector):
    """测试低匹配度产品（仅部分关键词匹配）"""
    product_info = {"name": "阿拉善驼奶", "origin": "阿拉善", "category": "驼奶", "keywords": ["沙漠", "营养"]}

    matches = collector.match_by_product(product_info)

    # 应该匹配到阿拉善驼铃（产地匹配）
    assert len(matches) > 0

    # 验证包含阿拉善相关元素
    alas_matches = [m for m in matches if "阿拉善" in m["element"]["origin_region"]]
    assert len(alas_matches) > 0


def test_match_by_product_no_match(collector):
    """测试无匹配产品"""
    product_info = {"name": "上海大闸蟹", "origin": "上海", "category": "水产", "keywords": ["新鲜", "江南"]}

    matches = collector.match_by_product(product_info)

    # 没有内蒙古外的元素，应该返回空或极低分
    if matches:
        assert matches[0]["score"] < 20


def test_match_scoring_dimensions(collector):
    """测试评分各维度权重"""
    product_info = {"name": "锡林郭勒羊肉", "origin": "锡林郭勒盟", "category": "羊肉", "keywords": ["草原", "生态"]}

    matches = collector.match_by_product(product_info)
    best_match = matches[0]

    # 验证评分组成（实际实现中返回总分，不返回分项）
    # 产地匹配应该贡献40分
    # 产品匹配应该贡献30分
    # 关键词应该有贡献（2个匹配 = 10分）
    # 类型加权10分
    # 总分应该约80-90分
    assert best_match["score"] >= 70
    assert "match_reason" in best_match


# ==================== 场景匹配测试 ====================


def test_match_by_scenario_brand_story(collector):
    """测试品牌故事场景匹配"""
    matches = collector.match_by_scenario("品牌故事")

    assert len(matches) > 0

    # 验证所有返回元素都支持品牌故事场景（match_by_scenario 返回原始元素字典）
    for element in matches:
        scenarios = element["metadata"].get("usage_scenarios", [])
        assert "品牌故事" in scenarios


def test_match_by_scenario_product_traceability(collector):
    """测试产品溯源场景匹配"""
    matches = collector.match_by_scenario("产品溯源")

    # 锡林郭勒草原应该在列表中
    names = [m["name"] for m in matches]
    assert "锡林郭勒草原" in names


def test_match_by_scenario_nonexistent(collector):
    """测试不存在的场景"""
    matches = collector.match_by_scenario("不存在的场景")

    assert len(matches) == 0


# ==================== 类型匹配测试 ====================


def test_match_by_type_geography(collector):
    """测试地理景观类型匹配"""
    matches = collector.match_by_type("地理景观")

    assert len(matches) > 0

    # 验证所有元素都是地理景观类型（match_by_type 返回原始元素字典）
    for element in matches:
        assert element["type"] == "地理景观"


def test_match_by_type_craft(collector):
    """测试传统工艺类型匹配"""
    matches = collector.match_by_type("传统工艺")

    assert len(matches) >= 2

    # 应该包含蒙古包和驼铃
    names = [m["name"] for m in matches]
    assert "蒙古包制作" in names
    assert "阿拉善驼铃" in names


def test_match_by_type_invalid(collector):
    """测试无效类型"""
    matches = collector.match_by_type("不存在的类型")

    assert len(matches) == 0


# ==================== 新产品建议测试 ====================


def test_suggest_for_new_product_with_matches(collector):
    """测试有匹配元素的新产品建议"""
    product_info = {"name": "锡林郭勒羊肉", "origin": "锡林郭勒盟", "category": "羊肉", "keywords": ["草原", "生态"]}

    suggestions = collector.suggest_for_new_product(product_info)

    # 实现返回 primary/secondary/scenarios/message 结构
    assert suggestions["primary"] is not None
    assert suggestions["primary"]["name"] == "锡林郭勒草原"
    assert suggestions["primary"]["match_score"] >= 70
    assert "匹配到" in suggestions["message"]


def test_suggest_for_new_product_no_matches(collector):
    """测试无匹配元素的新产品建议"""
    product_info = {"name": "新疆大枣", "origin": "新疆", "category": "干果", "keywords": ["甜", "营养"]}

    # 样例元素均属类型加权类别(地理景观/传统工艺)，任何产品都会得到低分匹配；
    # 为验证"无匹配"分支，显式让 match_by_product 返回空
    with patch.object(collector, "match_by_product", return_value=[]):
        suggestions = collector.suggest_for_new_product(product_info)

    assert suggestions["primary"] is None
    assert suggestions["secondary"] == []
    assert suggestions["scenarios"] == []
    assert "未找到" in suggestions["message"] or "建议采集" in suggestions["message"]


def test_suggest_collection_priority(collector):
    """测试采集建议的优先级"""
    product_info = {"name": "阿拉善驼肉", "origin": "阿拉善", "category": "驼肉", "keywords": ["沙漠", "特色"]}

    suggestions = collector.suggest_for_new_product(product_info)

    # 阿拉善驼铃产地+产品+关键词匹配，应为 primary
    assert suggestions["primary"]["name"] == "阿拉善驼铃"
    assert suggestions["primary"]["type"] == "传统工艺"
    # primary 为传统工艺 → 推荐"制作工艺展示"场景
    assert "制作工艺展示" in suggestions["scenarios"]


# ==================== 边界条件测试 ====================


def test_empty_product_info(collector):
    """测试空产品信息"""
    product_info = {}

    matches = collector.match_by_product(product_info)

    # 应该返回空列表或默认匹配
    assert isinstance(matches, list)


def test_partial_product_info(collector):
    """测试部分产品信息"""
    product_info = {
        "name": "测试产品",
        "origin": "锡林郭勒盟",
        # 缺少 category 和 keywords
    }

    matches = collector.match_by_product(product_info)

    # 仍然应该基于产地返回部分匹配
    assert len(matches) > 0


def test_special_characters_in_keywords(collector):
    """测试关键词中的特殊字符"""
    product_info = {
        "name": "测试产品",
        "origin": "锡林郭勒盟",
        "category": "羊肉",
        "keywords": ["草原！", "@生态", "#有机"],
    }

    # 不应该抛出异常
    matches = collector.match_by_product(product_info)
    assert isinstance(matches, list)


def test_very_long_keywords_list(collector):
    """测试超长关键词列表"""
    product_info = {
        "name": "测试产品",
        "origin": "锡林郭勒盟",
        "category": "羊肉",
        "keywords": [f"keyword_{i}" for i in range(100)],
    }

    # 应该正常处理，不崩溃
    matches = collector.match_by_product(product_info)
    assert isinstance(matches, list)


# ==================== 性能测试 ====================


def test_matching_performance(collector):
    """测试匹配性能（应该快速响应）"""
    import time

    product_info = {"name": "锡林郭勒羊肉", "origin": "锡林郭勒盟", "category": "羊肉", "keywords": ["草原", "生态"]}

    start_time = time.time()
    matches = collector.match_by_product(product_info)
    elapsed = time.time() - start_time

    # 匹配应该在100毫秒内完成
    assert elapsed < 0.1
    assert len(matches) > 0


# ==================== 数据完整性测试 ====================


def test_match_result_structure(collector):
    """测试匹配结果数据结构完整性"""
    product_info = {"name": "锡林郭勒羊肉", "origin": "锡林郭勒盟", "category": "羊肉", "keywords": ["草原"]}

    matches = collector.match_by_product(product_info)

    if matches:
        match = matches[0]

        # 验证必需字段
        assert "element" in match
        assert "score" in match
        assert "match_reason" in match

        # 验证元素完整性
        element = match["element"]
        assert "name" in element
        assert "type" in element
        assert "story" in element
        assert "origin_region" in element
        assert "keywords" in element
        assert "metadata" in element


def test_score_range_validity(collector):
    """测试评分范围有效性"""
    product_info = {"name": "锡林郭勒羊肉", "origin": "锡林郭勒盟", "category": "羊肉", "keywords": ["草原", "生态"]}

    matches = collector.match_by_product(product_info)

    for match in matches:
        score = match["score"]

        # 评分应该在0-100之间
        assert 0 <= score <= 100

        # 评分应该是合理的数值类型
        assert isinstance(score, (int, float))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
