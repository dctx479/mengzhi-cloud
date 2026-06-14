"""
增强版自适应文化元素采集器
集成知识图谱、语义相似度和历史行为的多层次匹配算法

版本: 2.0
创建日期: 2026-06-12
"""

import json
import os
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from collections import defaultdict

from app.services.cultural.knowledge_graph import CulturalKnowledgeGraph


class EnhancedCulturalCollector:
    """增强版文化元素采集器"""

    def __init__(self, data_path: str = None, enable_kg: bool = True):
        """
        初始化采集器

        Args:
            data_path: 文化元素数据文件路径
            enable_kg: 是否启用知识图谱（默认True）
        """
        if data_path is None:
            current_dir = Path(__file__).parent
            backend_dir = current_dir.parent.parent.parent
            data_path = backend_dir / "data" / "cultural_elements_extended.json"

        self.data_path = Path(data_path)
        self.elements = self._load_elements()

        # 知识图谱
        self.kg = CulturalKnowledgeGraph(data_path) if enable_kg else None

        # 地域同义词
        self.region_synonyms = self._load_region_synonyms()

        # 反向索引
        self.region_index = self._build_region_index()
        self.keyword_index = self._build_keyword_index()
        self.type_index = self._build_type_index()

    def _load_elements(self) -> List[Dict]:
        """加载文化元素数据"""
        if not self.data_path.exists():
            raise FileNotFoundError(f"文化元素数据文件不存在: {self.data_path}")

        with open(self.data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_region_synonyms(self) -> Dict[str, List[str]]:
        """加载地名同义词表"""
        return {
            "锡林郭勒盟": ["锡盟", "锡林郭勒"],
            "呼伦贝尔": ["呼伦贝尔市", "呼伦贝尔盟"],
            "鄂尔多斯": ["鄂尔多斯市", "伊克昭盟"],
            "阿拉善": ["阿拉善盟"],
            "赤峰": ["赤峰市"],
            "乌兰察布": ["乌兰察布市"],
            "巴彦淖尔": ["巴彦淖尔市"],
            "通辽": ["通辽市"],
        }

    def _build_region_index(self) -> Dict[str, List[int]]:
        """构建地域反向索引"""
        index = defaultdict(list)
        for idx, element in enumerate(self.elements):
            region = element.get("origin_region", "")
            if region:
                index[region].append(idx)
        return dict(index)

    def _build_keyword_index(self) -> Dict[str, List[int]]:
        """构建关键词反向索引"""
        index = defaultdict(list)
        for idx, element in enumerate(self.elements):
            for kw in element.get("keywords", []):
                index[kw].append(idx)
        return dict(index)

    def _build_type_index(self) -> Dict[str, List[int]]:
        """构建类型反向索引"""
        index = defaultdict(list)
        for idx, element in enumerate(self.elements):
            element_type = element.get("type", "")
            if element_type:
                index[element_type].append(idx)
        return dict(index)

    # =========================================================================
    # L1: 增强的精确匹配层
    # =========================================================================

    def _l1_exact_match(self, product_info: Dict) -> Dict[int, Dict]:
        """
        L1: 增强的精确匹配（40%权重）

        Returns:
            {element_idx: {"score": float, "breakdown": {...}}}
        """
        product_origin = product_info.get("origin", "")
        product_category = product_info.get("category", "")
        product_keywords = set(product_info.get("keywords", []))

        results = {}

        for idx, element in enumerate(self.elements):
            score_breakdown = {
                "region": 0.0,
                "product": 0.0,
                "keyword": 0.0,
                "type": 0.0
            }

            # 1. 地域匹配（40分）
            element_region = element.get("origin_region", "")

            # 精确匹配
            if product_origin and product_origin in element_region:
                score_breakdown["region"] = 40.0

            # 同义词匹配
            elif product_origin:
                canonical = self._get_canonical_region(product_origin)
                if canonical and canonical in element_region:
                    score_breakdown["region"] = 35.0

                # 部分匹配（如"锡林郭勒"匹配"锡林郭勒盟"）
                elif any(alias in element_region for alias in self.region_synonyms.get(canonical, [])):
                    score_breakdown["region"] = 30.0

            # 2. 产品关联匹配（30分）
            related_products = element.get("metadata", {}).get("related_products", [])
            related_products_str = " ".join(related_products).lower()

            if product_category and product_category.lower() in related_products_str:
                score_breakdown["product"] = 30.0
            elif product_category and any(prod in product_info.get("name", "").lower() for prod in related_products):
                score_breakdown["product"] = 20.0

            # 3. 关键词匹配（20分，TF-IDF加权）
            element_keywords = set(element.get("keywords", []))
            keyword_overlap = product_keywords & element_keywords

            if keyword_overlap:
                # 计算加权得分（常见词权重低）
                keyword_score = 0.0
                for kw in keyword_overlap:
                    # 简化的IDF：1 / log(出现次数 + 1)
                    idf = 1.0 / (len(self.keyword_index.get(kw, [])) + 1)
                    keyword_score += idf * 5

                score_breakdown["keyword"] = min(keyword_score, 20.0)

            # 4. 类型加权（10分）
            element_type = element.get("type", "")
            if element_type in ["地理景观", "畜牧知识", "传统工艺"]:
                score_breakdown["type"] = 10.0
            elif element_type in ["民族文化", "历史遗迹"]:
                score_breakdown["type"] = 8.0
            else:
                score_breakdown["type"] = 5.0

            # 总分
            total_score = sum(score_breakdown.values())

            if total_score > 0:
                results[idx] = {
                    "score": total_score,
                    "breakdown": score_breakdown
                }

        return results

    def _get_canonical_region(self, region: str) -> Optional[str]:
        """获取地名的规范形式"""
        for canonical, aliases in self.region_synonyms.items():
            if region in aliases or region == canonical:
                return canonical
        return region

    # =========================================================================
    # L3: 知识图谱关系层
    # =========================================================================

    def _l3_knowledge_graph(self, product_info: Dict) -> Dict[int, Dict]:
        """
        L3: 知识图谱关系推理（20%权重）

        Returns:
            {element_idx: {"score": float, "path_info": {...}}}
        """
        if self.kg is None:
            return {}

        results = {}

        # 使用知识图谱查找路径
        kg_results = self.kg.find_shortest_paths(
            product_info,
            max_hops=3,
            top_k=30  # 多取一些，后续合并时会排序
        )

        for result in kg_results:
            element_idx = result["element_index"]
            score = result["score"]  # 0-20分

            results[element_idx] = {
                "score": score,
                "path_info": {
                    "length": result["path_length"],
                    "description": result["path_description"]
                }
            }

        return results

    # =========================================================================
    # 综合评分
    # =========================================================================

    def intelligent_match(
        self,
        product_info: Dict,
        use_kg: bool = True,
        top_k: int = 10
    ) -> List[Dict]:
        """
        智能匹配算法（多层次）

        Args:
            product_info: 产品信息
                {
                    "id": int,
                    "name": str,
                    "origin": str,
                    "category": str,
                    "keywords": List[str]
                }
            use_kg: 是否使用知识图谱
            top_k: 返回前K个结果

        Returns:
            匹配结果列表
                [
                    {
                        "element": Dict,
                        "score": float,
                        "match_reason": str,
                        "score_breakdown": {
                            "exact_match": float,
                            "knowledge_graph": float
                        }
                    },
                    ...
                ]
        """
        # L1: 精确匹配（40%）
        l1_results = self._l1_exact_match(product_info)

        # L3: 知识图谱（20%）
        l3_results = self._l3_knowledge_graph(product_info) if use_kg and self.kg else {}

        # 合并所有元素索引
        all_indices = set(l1_results.keys()) | set(l3_results.keys())

        # 计算综合得分
        final_results = []

        for idx in all_indices:
            # L1得分（占40%）
            l1_score = l1_results.get(idx, {}).get("score", 0.0) * 0.4

            # L3得分（占20%，映射到总分100）
            l3_score = l3_results.get(idx, {}).get("score", 0.0) * (100.0 / 20.0) * 0.2

            # 总分
            total_score = l1_score + l3_score

            if total_score > 0:
                element = self.elements[idx]

                # 生成匹配原因
                match_reason = self._generate_match_reason_v2(
                    element,
                    product_info,
                    l1_results.get(idx, {}),
                    l3_results.get(idx, {})
                )

                final_results.append({
                    "element": element,
                    "score": total_score,
                    "match_reason": match_reason,
                    "score_breakdown": {
                        "exact_match": l1_score,
                        "knowledge_graph": l3_score
                    },
                    "path_info": l3_results.get(idx, {}).get("path_info")
                })

        # 按分数排序
        final_results.sort(key=lambda x: x["score"], reverse=True)

        return final_results[:top_k]

    def _generate_match_reason_v2(
        self,
        element: Dict,
        product_info: Dict,
        l1_info: Dict,
        l3_info: Dict
    ) -> str:
        """生成增强版匹配原因说明"""
        reasons = []

        # L1原因
        if l1_info:
            breakdown = l1_info.get("breakdown", {})

            if breakdown.get("region", 0) >= 30:
                reasons.append(f"地域高度匹配（{product_info.get('origin', '')}）")

            if breakdown.get("product", 0) >= 20:
                reasons.append(f"产品类别匹配（{product_info.get('category', '')}）")

            if breakdown.get("keyword", 0) > 0:
                product_keywords = set(product_info.get("keywords", []))
                element_keywords = set(element.get("keywords", []))
                overlap = product_keywords & element_keywords
                if overlap:
                    reasons.append(f"关键词匹配（{', '.join(list(overlap)[:3])}）")

        # L3原因
        if l3_info and l3_info.get("score", 0) > 0:
            path_info = l3_info.get("path_info", {})
            path_length = path_info.get("length", 0)
            reasons.append(f"知识图谱关联（{path_length}跳路径）")

        if not reasons:
            return f"相关度评分: {l1_info.get('score', 0):.1f}"

        return " | ".join(reasons)

    # =========================================================================
    # 兼容性方法（保持与旧版接口一致）
    # =========================================================================

    def match_by_product(self, product_info: Dict) -> List[Dict]:
        """
        根据产品信息匹配文化元素（兼容旧版接口）

        Args:
            product_info: 产品信息

        Returns:
            匹配的文化元素列表
        """
        return self.intelligent_match(product_info, use_kg=True, top_k=5)

    def match_by_scenario(self, scenario: str) -> List[Dict]:
        """根据使用场景匹配文化元素"""
        if self.kg:
            element_indices = self.kg.find_elements_by_scenario(scenario)
        else:
            # 回退到简单匹配
            element_indices = []
            for idx, element in enumerate(self.elements):
                scenarios = element.get("metadata", {}).get("usage_scenarios", [])
                if scenario in scenarios:
                    element_indices.append(idx)

        matched = []
        for idx in element_indices:
            matched.append({
                "element": self.elements[idx],
                "score": 80,  # 场景匹配给固定高分
                "match_reason": f"适用于{scenario}场景"
            })

        return matched

    def match_by_type(self, element_type: str) -> List[Dict]:
        """根据类型匹配文化元素"""
        indices = self.type_index.get(element_type, [])

        matched = []
        for idx in indices:
            matched.append({
                "element": self.elements[idx],
                "score": 75,  # 类型匹配给固定分
                "match_reason": f"类型匹配: {element_type}"
            })

        return matched

    def suggest_for_new_product(self, product_info: Dict) -> Dict:
        """为新产品建议文化元素"""
        matches = self.intelligent_match(product_info, use_kg=True, top_k=10)

        # 计算平均分
        if matches:
            avg_score = sum(m["score"] for m in matches) / len(matches)
        else:
            avg_score = 0

        # 判断是否需要采集
        need_collection = avg_score < 30 or len(matches) < 3

        # 确定采集目标
        collection_targets = []
        if need_collection:
            if avg_score == 0:
                collection_targets = ["地理景观", "传统工艺", "畜牧知识"]
            else:
                # 检查缺少哪些类型
                matched_types = set(m["element"]["type"] for m in matches)
                if "地理景观" not in matched_types:
                    collection_targets.append("地理景观")
                if "畜牧知识" not in matched_types and product_info.get("category", "") in ["羊肉", "牛肉", "驼肉"]:
                    collection_targets.append("畜牧知识")

        return {
            "need_collection": need_collection,
            "existing_matches": len(matches),
            "average_score": avg_score,
            "matched_elements": [m["element"] for m in matches[:5]],
            "collection_targets": collection_targets
        }


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    # 初始化增强版采集器
    collector = EnhancedCulturalCollector(enable_kg=True)

    # 测试产品
    product = {
        "id": 1,
        "name": "阿拉善驼肉",
        "origin": "阿拉善",
        "category": "驼肉",
        "keywords": ["沙漠", "特色", "营养"]
    }

    print("=== 智能匹配测试 ===\n")

    # 执行智能匹配
    results = collector.intelligent_match(product, use_kg=True, top_k=5)

    for i, result in enumerate(results, 1):
        print(f"{i}. {result['element']['name']}")
        print(f"   总分: {result['score']:.2f}")
        print(f"   匹配原因: {result['match_reason']}")
        print(f"   得分明细:")
        print(f"     - 精确匹配: {result['score_breakdown']['exact_match']:.2f}")
        print(f"     - 知识图谱: {result['score_breakdown']['knowledge_graph']:.2f}")

        if result.get('path_info'):
            print(f"   路径信息: {result['path_info']['length']}跳")

        print()

    # 新产品建议
    print("\n=== 新产品建议测试 ===\n")
    suggestion = collector.suggest_for_new_product(product)
    print(f"需要采集: {suggestion['need_collection']}")
    print(f"现有匹配: {suggestion['existing_matches']}个")
    print(f"平均分: {suggestion['average_score']:.2f}")
    if suggestion['collection_targets']:
        print(f"采集目标: {', '.join(suggestion['collection_targets'])}")
