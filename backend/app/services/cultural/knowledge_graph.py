"""
文化元素知识图谱构建器
使用NetworkX实现轻量级知识图谱，支持多跳关系推理

版本: 1.0
创建日期: 2026-06-12
"""

import json
import networkx as nx
from typing import List, Dict, Tuple, Optional, Set
from pathlib import Path
from collections import defaultdict


class CulturalKnowledgeGraph:
    """文化元素知识图谱"""

    def __init__(self, data_path: Optional[str] = None):
        """
        初始化知识图谱

        Args:
            data_path: 文化元素数据文件路径
        """
        self.graph = nx.MultiDiGraph()
        self.element_index = {}  # element_id -> node_id
        self.region_synonyms = self._load_region_synonyms()
        self.keyword_synonyms = self._load_keyword_synonyms()

        if data_path is None:
            current_dir = Path(__file__).parent
            backend_dir = current_dir.parent.parent.parent
            data_path = backend_dir / "data" / "cultural_elements_extended.json"

        self.data_path = Path(data_path)
        self._build_graph()

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

    def _load_keyword_synonyms(self) -> Dict[str, List[str]]:
        """加载关键词同义词表"""
        return {
            "草原": ["牧场", "草地", "大草原"],
            "沙漠": ["戈壁", "沙地"],
            "骆驼": ["驼", "骆驼"],
            "羊": ["羊群", "绵羊", "山羊"],
            "牛": ["牛群", "黄牛", "奶牛"],
            "马": ["马群", "蒙古马"],
            "游牧": ["牧民", "游牧民族"],
            "蒙古族": ["蒙古", "蒙族"],
        }

    def _build_graph(self):
        """从文化元素数据构建知识图谱"""
        if not self.data_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {self.data_path}")

        with open(self.data_path, "r", encoding="utf-8") as f:
            elements = json.load(f)

        # 1. 添加地域节点
        regions = set()
        for element in elements:
            region = element.get("origin_region", "")
            if region:
                regions.add(region)

        for region in regions:
            region_id = f"region_{self._normalize_name(region)}"
            self.graph.add_node(region_id, type="Region", name=region, canonical=self._get_canonical_region(region))

        # 2. 添加关键词节点
        keywords = set()
        for element in elements:
            for kw in element.get("keywords", []):
                keywords.add(kw)

        for kw in keywords:
            kw_id = f"keyword_{self._normalize_name(kw)}"
            self.graph.add_node(kw_id, type="Keyword", term=kw, canonical=self._get_canonical_keyword(kw))

        # 3. 添加类型节点
        types = set()
        for element in elements:
            element_type = element.get("type", "")
            if element_type:
                types.add(element_type)

        for elem_type in types:
            type_id = f"type_{self._normalize_name(elem_type)}"
            self.graph.add_node(type_id, type="Type", name=elem_type)

        # 4. 添加场景节点
        scenarios = set()
        for element in elements:
            for scenario in element.get("metadata", {}).get("usage_scenarios", []):
                scenarios.add(scenario)

        for scenario in scenarios:
            scenario_id = f"scenario_{self._normalize_name(scenario)}"
            self.graph.add_node(scenario_id, type="Scenario", name=scenario)

        # 5. 添加文化元素节点及其关系
        for idx, element in enumerate(elements):
            element_id = f"element_{idx}"
            self.element_index[idx] = element_id

            # 添加元素节点
            self.graph.add_node(
                element_id,
                type="CulturalElement",
                data_index=idx,
                name=element["name"],
                element_type=element.get("type", ""),
                story_length=len(element.get("story", "")),
            )

            # 元素 -> 地域
            region = element.get("origin_region", "")
            if region:
                region_id = f"region_{self._normalize_name(region)}"
                self.graph.add_edge(element_id, region_id, relation="LOCATED_IN", weight=1.0)

            # 元素 -> 类型
            elem_type = element.get("type", "")
            if elem_type:
                type_id = f"type_{self._normalize_name(elem_type)}"
                self.graph.add_edge(element_id, type_id, relation="HAS_TYPE", weight=1.0)

            # 元素 -> 关键词
            for kw in element.get("keywords", []):
                kw_id = f"keyword_{self._normalize_name(kw)}"
                # 使用TF-IDF权重（简化为频率倒数）
                weight = 1.0 / (element.get("keywords", []).count(kw) + 1)
                self.graph.add_edge(element_id, kw_id, relation="TAGGED_WITH", weight=weight)

            # 元素 -> 场景
            for scenario in element.get("metadata", {}).get("usage_scenarios", []):
                scenario_id = f"scenario_{self._normalize_name(scenario)}"
                self.graph.add_edge(element_id, scenario_id, relation="SUITABLE_FOR", weight=0.8)

        # 6. 添加同义词关系
        self._add_synonym_edges()

        print(f"✅ 知识图谱构建完成:")
        print(f"   节点数: {self.graph.number_of_nodes()}")
        print(f"   边数: {self.graph.number_of_edges()}")
        print(f"   文化元素: {len(self.element_index)}")

    def _normalize_name(self, name: str) -> str:
        """标准化名称（用于生成节点ID）"""
        return name.replace(" ", "_").replace("(", "").replace(")", "")

    def _get_canonical_region(self, region: str) -> str:
        """获取地名的规范形式"""
        for canonical, aliases in self.region_synonyms.items():
            if region in aliases or region == canonical:
                return canonical
        return region

    def _get_canonical_keyword(self, keyword: str) -> str:
        """获取关键词的规范形式"""
        for canonical, aliases in self.keyword_synonyms.items():
            if keyword in aliases or keyword == canonical:
                return canonical
        return keyword

    def _add_synonym_edges(self):
        """添加同义词边"""
        # 地域同义词
        for canonical, aliases in self.region_synonyms.items():
            canonical_id = f"region_{self._normalize_name(canonical)}"
            if canonical_id not in self.graph:
                continue

            for alias in aliases:
                alias_id = f"region_{self._normalize_name(alias)}"
                if alias_id in self.graph:
                    self.graph.add_edge(alias_id, canonical_id, relation="SYNONYM_OF", weight=1.0)

        # 关键词同义词
        for canonical, aliases in self.keyword_synonyms.items():
            canonical_id = f"keyword_{self._normalize_name(canonical)}"
            if canonical_id not in self.graph:
                continue

            for alias in aliases:
                alias_id = f"keyword_{self._normalize_name(alias)}"
                if alias_id in self.graph:
                    self.graph.add_edge(alias_id, canonical_id, relation="SYNONYM_OF", weight=1.0)

    # =========================================================================
    # 查询方法
    # =========================================================================

    def find_elements_by_region(self, region: str, include_synonyms: bool = True) -> List[int]:
        """
        根据地域查找文化元素

        Args:
            region: 地域名称
            include_synonyms: 是否包含同义词

        Returns:
            文化元素索引列表
        """
        region_ids = [f"region_{self._normalize_name(region)}"]

        if include_synonyms:
            canonical = self._get_canonical_region(region)
            canonical_id = f"region_{self._normalize_name(canonical)}"
            if canonical_id in self.graph:
                region_ids.append(canonical_id)

        element_indices = []
        for region_id in region_ids:
            if region_id not in self.graph:
                continue

            # 找到所有指向该地域的元素
            predecessors = self.graph.predecessors(region_id)
            for pred in predecessors:
                node_data = self.graph.nodes[pred]
                if node_data.get("type") == "CulturalElement":
                    element_indices.append(node_data["data_index"])

        return element_indices

    def find_elements_by_keywords(self, keywords: List[str], min_overlap: int = 1) -> List[Tuple[int, int]]:
        """
        根据关键词查找文化元素

        Args:
            keywords: 关键词列表
            min_overlap: 最小重叠数量

        Returns:
            [(element_index, overlap_count), ...]
        """
        element_overlap = defaultdict(int)

        for kw in keywords:
            kw_id = f"keyword_{self._normalize_name(kw)}"
            if kw_id not in self.graph:
                continue

            # 找到所有标记该关键词的元素
            predecessors = self.graph.predecessors(kw_id)
            for pred in predecessors:
                node_data = self.graph.nodes[pred]
                if node_data.get("type") == "CulturalElement":
                    element_overlap[node_data["data_index"]] += 1

        # 过滤并排序
        results = [(idx, count) for idx, count in element_overlap.items() if count >= min_overlap]
        results.sort(key=lambda x: x[1], reverse=True)

        return results

    def find_elements_by_scenario(self, scenario: str) -> List[int]:
        """根据使用场景查找文化元素"""
        scenario_id = f"scenario_{self._normalize_name(scenario)}"
        if scenario_id not in self.graph:
            return []

        element_indices = []
        predecessors = self.graph.predecessors(scenario_id)
        for pred in predecessors:
            node_data = self.graph.nodes[pred]
            if node_data.get("type") == "CulturalElement":
                element_indices.append(node_data["data_index"])

        return element_indices

    def find_shortest_paths(self, product_info: Dict, max_hops: int = 3, top_k: int = 10) -> List[Dict]:
        """
        找到产品到文化元素的最短路径

        Args:
            product_info: 产品信息 {origin, keywords, category}
            max_hops: 最大跳数
            top_k: 返回前K个

        Returns:
            [
                {
                    "element_index": int,
                    "score": float,
                    "path_length": int,
                    "path_description": str
                },
                ...
            ]
        """
        # 构建临时产品节点
        product_node = "product_temp"
        self.graph.add_node(product_node, type="Product", temp=True)

        # 添加产品到图谱的连接
        product_origin = product_info.get("origin", "")
        product_keywords = product_info.get("keywords", [])

        if product_origin:
            region_id = f"region_{self._normalize_name(product_origin)}"
            if region_id in self.graph:
                self.graph.add_edge(product_node, region_id, relation="ORIGIN_IN", weight=1.0)

        for kw in product_keywords:
            kw_id = f"keyword_{self._normalize_name(kw)}"
            if kw_id in self.graph:
                self.graph.add_edge(product_node, kw_id, relation="TAGGED_WITH", weight=0.8)

        # 查找到所有元素的最短路径
        results = []
        for data_index, element_id in self.element_index.items():
            try:
                path = nx.shortest_path(self.graph, product_node, element_id)
                path_length = len(path) - 1

                if path_length <= max_hops:
                    score = self._calculate_path_score(path)
                    path_desc = self._describe_path(path)

                    results.append(
                        {
                            "element_index": data_index,
                            "score": score,
                            "path_length": path_length,
                            "path_description": path_desc,
                        }
                    )

            except nx.NetworkXNoPath:
                continue

        # 清理临时节点
        self.graph.remove_node(product_node)

        # 排序并返回Top-K
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _calculate_path_score(self, path: List[str]) -> float:
        """
        计算路径得分

        评分逻辑:
        - 1跳: 20分
        - 2跳: 15分 × (边权重平均)
        - 3跳: 10分 × (边权重平均)
        """
        if len(path) <= 1:
            return 0.0

        path_length = len(path) - 1

        # 基础分数
        base_scores = {1: 20.0, 2: 15.0, 3: 10.0}
        base_score = base_scores.get(path_length, 5.0)

        # 计算边权重平均
        total_weight = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edges = self.graph.get_edge_data(u, v)
            if edges:
                # 取最大权重边
                max_weight = max(edge.get("weight", 0.5) for edge in edges.values())
                total_weight += max_weight

        avg_weight = total_weight / path_length

        return base_score * avg_weight

    def _describe_path(self, path: List[str]) -> str:
        """生成路径描述"""
        descriptions = []

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            u_data = self.graph.nodes[u]
            v_data = self.graph.nodes[v]

            edges = self.graph.get_edge_data(u, v)
            if edges:
                relation = list(edges.values())[0].get("relation", "RELATED_TO")

                u_name = u_data.get("name", u)
                v_name = v_data.get("name", v_data.get("term", v))

                descriptions.append(f"{u_name} --[{relation}]--> {v_name}")

        return " → ".join(descriptions)

    def get_graph_statistics(self) -> Dict:
        """获取图谱统计信息"""
        node_types = defaultdict(int)
        edge_types = defaultdict(int)

        for node, data in self.graph.nodes(data=True):
            node_types[data.get("type", "Unknown")] += 1

        for u, v, data in self.graph.edges(data=True):
            edge_types[data.get("relation", "Unknown")] += 1

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_types": dict(node_types),
            "edge_types": dict(edge_types),
            "density": nx.density(self.graph),
        }

    def export_graph(self, output_path: str, format: str = "gexf"):
        """
        导出图谱为可视化格式

        Args:
            output_path: 输出文件路径
            format: 格式 (gexf, graphml, gml)
        """
        if format == "gexf":
            nx.write_gexf(self.graph, output_path)
        elif format == "graphml":
            nx.write_graphml(self.graph, output_path)
        elif format == "gml":
            nx.write_gml(self.graph, output_path)
        else:
            raise ValueError(f"不支持的格式: {format}")

        print(f"✅ 图谱已导出到: {output_path}")


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    # 构建知识图谱
    kg = CulturalKnowledgeGraph()

    # 查询示例1: 根据地域查找
    print("\n=== 查询示例1: 锡林郭勒盟的文化元素 ===")
    elements = kg.find_elements_by_region("锡林郭勒盟")
    print(f"找到 {len(elements)} 个元素")

    # 查询示例2: 根据关键词查找
    print("\n=== 查询示例2: 草原+羊肉 关键词 ===")
    results = kg.find_elements_by_keywords(["草原", "羊肉"])
    for idx, count in results[:3]:
        print(f"  元素{idx}: 匹配{count}个关键词")

    # 查询示例3: 最短路径推理
    print("\n=== 查询示例3: 产品到元素的路径 ===")
    product = {"origin": "阿拉善", "keywords": ["沙漠", "驼肉"], "category": "驼肉类"}

    paths = kg.find_shortest_paths(product, max_hops=3, top_k=5)
    for result in paths:
        print(f"\n元素{result['element_index']}:")
        print(f"  得分: {result['score']:.2f}")
        print(f"  路径长度: {result['path_length']}跳")
        print(f"  路径: {result['path_description']}")

    # 统计信息
    print("\n=== 图谱统计 ===")
    stats = kg.get_graph_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
