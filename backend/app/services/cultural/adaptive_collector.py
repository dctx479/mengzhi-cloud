"""
文化元素自适应采集器
根据产品信息动态采集和匹配文化元素

版本: 1.0
创建日期: 2026-06-12
"""

import json
import os
from typing import List, Dict, Optional
from pathlib import Path


class AdaptiveCulturalCollector:
    """自适应文化元素采集器"""

    def __init__(self, data_path: str = None):
        """
        初始化采集器

        Args:
            data_path: 文化元素数据文件路径，默认为 backend/data/cultural_elements_extended.json
        """
        if data_path is None:
            # 默认路径：从当前文件向上查找 backend/data
            current_dir = Path(__file__).parent
            backend_dir = current_dir.parent.parent.parent
            data_path = backend_dir / "data" / "cultural_elements_extended.json"

        self.data_path = Path(data_path)
        self.elements = self._load_elements()

    def _load_elements(self) -> List[Dict]:
        """加载文化元素数据"""
        if not self.data_path.exists():
            raise FileNotFoundError(f"文化元素数据文件不存在: {self.data_path}")

        with open(self.data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def match_by_product(self, product_info: Dict) -> List[Dict]:
        """
        根据产品信息匹配文化元素

        Args:
            product_info: 产品信息字典
                {
                    "name": "呼伦贝尔羔羊肉",
                    "origin": "呼伦贝尔",
                    "category": "羊肉类",
                    "keywords": ["草原", "天然", "无膻"]
                }

        Returns:
            匹配的文化元素列表（按相关度排序，最多返回5个）
        """
        product_name = product_info.get("name", "")
        product_origin = product_info.get("origin", "")
        product_category = product_info.get("category", "")
        product_keywords = product_info.get("keywords", [])

        matched = []

        for element in self.elements:
            score = 0

            # 1. 地域匹配（最高权重：40分）
            element_region = element.get("origin_region", "")
            if product_origin and product_origin in element_region:
                score += 40
            elif any(city in element_region for city in ["呼伦贝尔", "锡林郭勒", "鄂尔多斯", "阿拉善", "赤峰"] if city in product_origin):
                score += 30

            # 2. 产品关联匹配（30分）
            related_products = element.get("metadata", {}).get("related_products", [])
            if product_category in str(related_products):
                score += 30
            elif any(prod in product_name for prod in related_products):
                score += 20

            # 3. 关键词匹配（20分）
            element_keywords = element.get("keywords", [])
            keyword_overlap = set(product_keywords) & set(element_keywords)
            if keyword_overlap:
                score += len(keyword_overlap) * 5

            # 4. 类型加权（10分）
            element_type = element.get("type", "")
            if element_type in ["地理景观", "畜牧知识", "传统工艺"]:
                score += 10  # 与产品溯源直接相关的类型优先

            if score > 0:
                matched.append({
                    "element": element,
                    "score": score,
                    "match_reason": self._generate_match_reason(
                        element, product_info, score
                    )
                })

        # 按分数排序，取前5个
        matched.sort(key=lambda x: x["score"], reverse=True)
        return matched[:5]

    def _generate_match_reason(self, element: Dict, product_info: Dict, score: int) -> str:
        """生成匹配原因说明"""
        reasons = []

        element_region = element.get("origin_region", "")
        product_origin = product_info.get("origin", "")

        if product_origin and product_origin in element_region:
            reasons.append(f"地域高度匹配（{product_origin}）")

        related_products = element.get("metadata", {}).get("related_products", [])
        product_category = product_info.get("category", "")
        if product_category in str(related_products):
            reasons.append(f"产品类别匹配（{product_category}）")

        element_keywords = element.get("keywords", [])
        product_keywords = product_info.get("keywords", [])
        keyword_overlap = set(product_keywords) & set(element_keywords)
        if keyword_overlap:
            reasons.append(f"关键词匹配（{', '.join(list(keyword_overlap)[:3])}）")

        return " | ".join(reasons) if reasons else f"相关度评分: {score}"

    def match_by_scenario(self, scenario: str) -> List[Dict]:
        """
        根据应用场景匹配文化元素

        Args:
            scenario: 应用场景，如 "礼品场景", "节日营销", "品牌故事"

        Returns:
            匹配的文化元素列表
        """
        matched = []

        for element in self.elements:
            usage_scenarios = element.get("metadata", {}).get("usage_scenarios", [])
            if scenario in str(usage_scenarios):
                matched.append(element)

        return matched

    def match_by_type(self, element_type: str) -> List[Dict]:
        """
        根据类型筛选文化元素

        Args:
            element_type: 元素类型，如 "地理景观", "传统工艺", "节庆习俗"

        Returns:
            该类型的所有元素
        """
        return [e for e in self.elements if e.get("type") == element_type]

    def get_all_types(self) -> List[str]:
        """获取所有元素类型"""
        types = set(e.get("type") for e in self.elements)
        return sorted(list(types))

    def get_statistics(self) -> Dict:
        """获取文化元素统计信息"""
        types = {}
        for e in self.elements:
            t = e.get("type", "未分类")
            types[t] = types.get(t, 0) + 1

        return {
            "total": len(self.elements),
            "types": types,
            "type_count": len(types)
        }

    def suggest_for_new_product(self, product_info: Dict) -> Dict:
        """
        为新产品建议最佳文化元素组合

        Args:
            product_info: 产品信息

        Returns:
            推荐方案字典
                {
                    "primary": 主要文化元素（1个，用于品牌故事核心）,
                    "secondary": 辅助文化元素（2-3个，用于产品详情补充）,
                    "scenarios": 应用场景建议
                }
        """
        matched = self.match_by_product(product_info)

        if not matched:
            return {
                "primary": None,
                "secondary": [],
                "scenarios": [],
                "message": "未找到匹配的文化元素，建议采集该产地的文化数据"
            }

        primary = matched[0]["element"]
        secondary = [m["element"] for m in matched[1:4]]

        # 推荐应用场景
        scenarios = []
        if primary.get("type") == "地理景观":
            scenarios.append("产地溯源故事")
        if primary.get("type") == "传统工艺":
            scenarios.append("制作工艺展示")
        if any(e.get("type") == "节庆习俗" for e in secondary):
            scenarios.append("节日礼品营销")

        return {
            "primary": {
                "name": primary.get("name"),
                "type": primary.get("type"),
                "story_excerpt": primary.get("story", "")[:200] + "...",
                "match_score": matched[0]["score"],
                "match_reason": matched[0]["match_reason"]
            },
            "secondary": [
                {
                    "name": e.get("name"),
                    "type": e.get("type"),
                    "match_score": m["score"]
                }
                for e, m in zip(secondary, matched[1:4])
            ],
            "scenarios": scenarios,
            "message": f"为产品匹配到 {len(matched)} 个相关文化元素"
        }


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    # 初始化采集器
    collector = AdaptiveCulturalCollector()

    # 获取统计信息
    stats = collector.get_statistics()
    print("=== 文化元素库统计 ===")
    print(f"总数: {stats['total']} 个")
    print(f"类别: {stats['type_count']} 种")
    print("\n分类详情:")
    for t, count in sorted(stats['types'].items(), key=lambda x: -x[1]):
        print(f"  {t}: {count}个")

    print("\n" + "="*50)

    # 测试产品匹配
    test_product = {
        "name": "呼伦贝尔羔羊肉",
        "origin": "呼伦贝尔",
        "category": "羊肉类",
        "keywords": ["草原", "天然", "无膻"]
    }

    print("\n=== 产品匹配测试 ===")
    print(f"产品: {test_product['name']}")
    print(f"产地: {test_product['origin']}")
    print()

    matches = collector.match_by_product(test_product)
    print(f"匹配到 {len(matches)} 个文化元素:")
    for i, match in enumerate(matches, 1):
        element = match["element"]
        print(f"\n{i}. {element.get('name')} ({element.get('type')})")
        print(f"   评分: {match['score']}")
        print(f"   原因: {match['match_reason']}")

    print("\n" + "="*50)

    # 测试推荐方案
    print("\n=== 新产品推荐方案 ===")
    suggestion = collector.suggest_for_new_product(test_product)
    print(f"推荐结果: {suggestion['message']}")

    if suggestion['primary']:
        print("\n主要文化元素:")
        primary = suggestion['primary']
        print(f"  名称: {primary['name']}")
        print(f"  类型: {primary['type']}")
        print(f"  匹配度: {primary['match_score']}")
        print(f"  匹配原因: {primary['match_reason']}")
        print(f"  故事摘要: {primary['story_excerpt']}")

        print("\n辅助文化元素:")
        for sec in suggestion['secondary']:
            print(f"  - {sec['name']} ({sec['type']}) - 评分{sec['match_score']}")

        print("\n推荐应用场景:")
        for scenario in suggestion['scenarios']:
            print(f"  - {scenario}")
