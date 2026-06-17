"""
文化元素知识图谱查询增强

提供:
- path_query: 两个元素之间的关联路径 (基于共享 region / type / keywords)
- relationship_recommendation: 基于共同邻居的元素推荐 (协同过滤)
- related_products: 通过元素关联的产品
- graph_stats: 知识图谱统计 (节点/边/密度)

设计:
- 不引入图数据库 (Neo4j), 复用 CulturalElement 表的隐式关系
- 边定义: 共享 origin_region / 共享 type / 共享 keyword
- 路径算法: BFS, 最大跳数 3
- 性能: 单元素查询 < 100ms (SQL JOIN + Python BFS)

版本: 1.0
创建日期: 2026-06-17
"""

import json
import logging
from collections import defaultdict, deque
from typing import List, Dict, Any, Optional, Set, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.cultural import CulturalElement, ElementStatus
from app.models.product import Product

logger = logging.getLogger(__name__)


class CulturalGraphQueryService:
    """文化元素知识图谱查询服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_element_or_404(self, element_id: int) -> CulturalElement:
        """获取文化元素, 不存在则 raise ValueError"""
        element = (
            self.db.query(CulturalElement)
            .filter(CulturalElement.id == element_id, CulturalElement.status == ElementStatus.APPROVED)
            .first()
        )
        if not element:
            raise ValueError(f"文化元素 {element_id} 不存在或未审核通过")
        return element

    def parse_keywords(self, keywords_str: Optional[str]) -> List[str]:
        """解析 JSON 关键词数组, 失败返回空列表"""
        if not keywords_str:
            return []
        try:
            kws = json.loads(keywords_str)
            if isinstance(kws, list):
                return [str(k) for k in kws if k]
            return []
        except (json.JSONDecodeError, TypeError):
            return []

    def find_path(
        self,
        source_id: int,
        target_id: int,
        max_hops: int = 3,
    ) -> Dict[str, Any]:
        """查找两个元素之间的关联路径 (BFS)

        边定义:
        - 共享 origin_region (同一产地)
        - 共享 type (同一类型)
        - 共享 keyword (至少 1 个共同关键词)

        Returns:
            {
                "found": bool,
                "paths": [
                    {"hops": int, "nodes": [element_dict, ...]},
                    ...
                ],
                "shortest_hops": int | None,
            }
        """
        if source_id == target_id:
            return {"found": True, "paths": [{"hops": 0, "nodes": [self._element_summary(self.get_element_or_404(source_id))]}],"shortest_hops": 0}

        source = self.get_element_or_404(source_id)
        target = self.get_element_or_404(target_id)

        # 加载所有 approved elements (中小数据规模可全表加载, 大规模需分批)
        all_elements = (
            self.db.query(CulturalElement)
            .filter(CulturalElement.status == ElementStatus.APPROVED)
            .all()
        )

        # 预计算邻接表
        adjacency = self._build_adjacency(all_elements, max_hops)

        # BFS from source to target
        paths = self._bfs_paths(adjacency, source.id, target.id, max_hops)

        return {
            "found": len(paths) > 0,
            "paths": paths[:5],  # 最多返回 5 条路径
            "shortest_hops": min((p["hops"] for p in paths), default=None),
            "total_paths": len(paths),
        }

    def recommend_related(
        self,
        element_id: int,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """基于共同邻居的元素推荐

        算法:
        1. 找到 element 的所有邻居 (共享 region/type/keyword)
        2. 统计邻居的邻居 (二度关系), 排除自己和一邻居
        3. 按 (共享邻居数, 共享属性数) 排序, 返回 top_k

        Returns:
            [
                {
                    "element": element_summary,
                    "shared_neighbors": int,
                    "shared_attributes": int,
                    "score": float,
                },
                ...
            ]
        """
        source = self.get_element_or_404(element_id)

        all_elements = (
            self.db.query(CulturalElement)
            .filter(
                CulturalElement.status == ElementStatus.APPROVED,
                CulturalElement.id != element_id,
            )
            .all()
        )

        # 计算 source 的属性集合
        source_region = source.origin_region
        source_type = source.type
        source_keywords = set(self.parse_keywords(source.keywords))

        # 一跳邻居
        first_hop_neighbors: Set[int] = set()
        # 候选元素 (二度邻居) 及其共同邻居计数
        candidates: Dict[int, Dict[str, int]] = defaultdict(lambda: {"shared_neighbors": 0, "shared_attributes": 0})

        for e in all_elements:
            shared_attrs = 0
            if e.origin_region == source_region:
                shared_attrs += 1
            if e.type == source_type:
                shared_attrs += 1
            e_kws = set(self.parse_keywords(e.keywords))
            if e_kws & source_keywords:
                shared_attrs += 1

            if shared_attrs > 0:
                first_hop_neighbors.add(e.id)
                candidates[e.id]["shared_attributes"] = shared_attrs
                candidates[e.id]["shared_neighbors"] = 1  # 直接邻居

        # 二度邻居
        for neighbor_id in list(first_hop_neighbors):
            neighbor = next((e for e in all_elements if e.id == neighbor_id), None)
            if not neighbor:
                continue
            neighbor_kws = set(self.parse_keywords(neighbor.keywords))
            for e in all_elements:
                if e.id == element_id or e.id in first_hop_neighbors:
                    continue
                # 通过 neighbor 间接关联
                shared_via_neighbor = 0
                if e.origin_region == neighbor.origin_region and e.origin_region == source_region:
                    shared_via_neighbor += 1
                if e.type == neighbor.type and e.type == source_type:
                    shared_via_neighbor += 1
                e_kws = set(self.parse_keywords(e.keywords))
                if e_kws & neighbor_kws & source_keywords:
                    shared_via_neighbor += 1

                if shared_via_neighbor > 0:
                    candidates[e.id]["shared_neighbors"] += 1

        # 排序: (shared_neighbors, shared_attributes) 降序
        sorted_candidates = sorted(
            candidates.items(),
            key=lambda x: (x[1]["shared_neighbors"], x[1]["shared_attributes"]),
            reverse=True,
        )[:top_k]

        # 组装响应
        element_map = {e.id: e for e in all_elements}
        results = []
        for cid, scores in sorted_candidates:
            element = element_map.get(cid)
            if not element:
                continue
            results.append(
                {
                    "element": self._element_summary(element),
                    "shared_neighbors": scores["shared_neighbors"],
                    "shared_attributes": scores["shared_attributes"],
                    "score": round(scores["shared_neighbors"] * 0.7 + scores["shared_attributes"] * 0.3, 2),
                }
            )

        return results

    def get_related_products(
        self,
        element_id: int,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """通过文化元素查找关联产品

        关联规则:
        - 产品产地 (origin_province/origin_city) 包含元素 origin_region
        - 或产品 category 包含元素 type
        """
        element = self.get_element_or_404(element_id)

        # 提取元素信息用于模糊匹配
        region = element.origin_region
        element_type = element.type

        # 1. 按产地匹配
        region_products = (
            self.db.query(Product)
            .filter(
                or_(
                    Product.origin_province.like(f"%{region}%"),
                    Product.origin_city.like(f"%{region}%"),
                )
            )
            .limit(limit)
            .all()
        )

        # 2. 按类别匹配
        category_products = (
            self.db.query(Product)
            .filter(Product.category.like(f"%{element_type}%"))
            .limit(limit)
            .all()
        )

        # 合并去重
        seen = set()
        result = []
        for p in list(region_products) + list(category_products):
            if p.id in seen:
                continue
            seen.add(p.id)
            result.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "category": p.category,
                    "origin_province": p.origin_province,
                    "origin_city": p.origin_city,
                    "match_reason": "region"
                    if any(p.id == rp.id for rp in region_products)
                    else "category",
                }
            )
            if len(result) >= limit:
                break

        return result

    def get_graph_stats(self) -> Dict[str, Any]:
        """知识图谱统计"""
        total = (
            self.db.query(func.count(CulturalElement.id))
            .filter(CulturalElement.status == ElementStatus.APPROVED)
            .scalar()
            or 0
        )

        # 按 type 分组
        type_rows = (
            self.db.query(CulturalElement.type, func.count(CulturalElement.id))
            .filter(CulturalElement.status == ElementStatus.APPROVED)
            .group_by(CulturalElement.type)
            .all()
        )
        by_type = {t: c for t, c in type_rows}

        # 按 region 分组
        region_rows = (
            self.db.query(CulturalElement.origin_region, func.count(CulturalElement.id))
            .filter(CulturalElement.status == ElementStatus.APPROVED)
            .group_by(CulturalElement.origin_region)
            .all()
        )
        by_region = {r: c for r, c in region_rows}

        # 估算边数 (基于 region/type/keyword 共享)
        # 全表扫描, 大数据量时 O(n²) 可能慢, 这里取样估算
        all_elements = (
            self.db.query(CulturalElement)
            .filter(CulturalElement.status == ElementStatus.APPROVED)
            .limit(200)
            .all()
        )
        edge_count = 0
        for i, e1 in enumerate(all_elements):
            for e2 in all_elements[i + 1 :]:
                if self._has_edge(e1, e2):
                    edge_count += 1

        # 缩放: 实际边数 ≈ edge_count * (total/200)²
        if total > 0 and len(all_elements) > 0:
            scale = (total / len(all_elements)) ** 2
            estimated_edges = int(edge_count * scale)
        else:
            estimated_edges = 0

        return {
            "total_nodes": total,
            "by_type": by_type,
            "by_region": by_region,
            "estimated_edges": estimated_edges,
            "density": round(estimated_edges / (total * (total - 1) / 2), 4) if total > 1 else 0,
            "sampled_for_estimation": len(all_elements),
        }

    # ============ 私有方法 ============

    def _build_adjacency(
        self, elements: List[CulturalElement], max_hops: int
    ) -> Dict[int, List[int]]:
        """构建邻接表 (基于共享 region/type/keyword)"""
        adjacency: Dict[int, List[int]] = defaultdict(list)
        # 索引: region/type/keyword → [element_ids]
        region_index: Dict[str, List[int]] = defaultdict(list)
        type_index: Dict[str, List[int]] = defaultdict(list)
        keyword_index: Dict[str, List[int]] = defaultdict(list)

        for e in elements:
            region_index[e.origin_region].append(e.id)
            type_index[e.type].append(e.id)
            for kw in self.parse_keywords(e.keywords):
                keyword_index[kw].append(e.id)

        # 构建边 (O(n²) 但元素数 ≤200 时可接受)
        for i, e1 in enumerate(elements):
            for e2 in elements[i + 1 :]:
                if self._has_edge(e1, e2):
                    adjacency[e1.id].append(e2.id)
                    adjacency[e2.id].append(e1.id)
        return adjacency

    def _has_edge(self, e1: CulturalElement, e2: CulturalElement) -> bool:
        """判断两个元素之间是否存在边"""
        if e1.id == e2.id:
            return False
        if e1.origin_region == e2.origin_region:
            return True
        if e1.type == e2.type:
            return True
        kws1 = set(self.parse_keywords(e1.keywords))
        kws2 = set(self.parse_keywords(e2.keywords))
        if kws1 & kws2:
            return True
        return False

    def _bfs_paths(
        self,
        adjacency: Dict[int, List[int]],
        source: int,
        target: int,
        max_hops: int,
    ) -> List[Dict[str, Any]]:
        """BFS 找所有最短路径"""
        if source == target:
            return [{"hops": 0, "nodes": [source]}]

        queue = deque([(source, [source])])
        visited = {source: [[source]]}  # node -> list of paths
        shortest_paths = []
        shortest_hops = None

        while queue:
            node, path = queue.popleft()
            if len(path) - 1 > max_hops:
                continue
            for neighbor in adjacency.get(node, []):
                if neighbor == target:
                    final_path = path + [neighbor]
                    hops = len(final_path) - 1
                    if shortest_hops is None:
                        shortest_hops = hops
                    if hops == shortest_hops:
                        shortest_paths.append(final_path)
                    continue
                if neighbor in visited and any(len(p) <= len(path) + 1 for p in visited[neighbor]):
                    continue
                new_path = path + [neighbor]
                if neighbor not in visited:
                    visited[neighbor] = [new_path]
                    queue.append((neighbor, new_path))

        # 转换为 element summary
        all_ids = set()
        for p in shortest_paths:
            all_ids.update(p)
        elements_map = {
            e.id: e
            for e in self.db.query(CulturalElement).filter(CulturalElement.id.in_(all_ids)).all()
        }

        return [
            {
                "hops": len(p) - 1,
                "nodes": [self._element_summary(elements_map[nid]) for nid in p if nid in elements_map],
            }
            for p in shortest_paths
        ]

    def _element_summary(self, element: CulturalElement) -> Dict[str, Any]:
        """元素摘要 (用于图查询响应)"""
        return {
            "id": element.id,
            "name": element.name,
            "type": element.type,
            "origin_region": element.origin_region,
            "keywords": self.parse_keywords(element.keywords),
        }
