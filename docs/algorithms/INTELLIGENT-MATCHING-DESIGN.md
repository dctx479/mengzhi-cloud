# 产品-文化智能匹配算法设计

## 一、现有算法分析

### 当前4维度评分（AdaptiveCulturalCollector）

| 维度 | 权重 | 计算逻辑 | 优点 | 缺点 |
|------|------|---------|------|------|
| **地域匹配** | 40分 | 产品产地 ⊆ 元素产地 | 直观、高权重合理 | 仅支持精确字符串匹配 |
| **产品关联** | 30分 | 产品类别 ∈ 元素关联产品 | 业务逻辑清晰 | 依赖人工标注 |
| **关键词匹配** | 20分 | 集合交集 × 5分 | 灵活、可扩展 | 无语义理解 |
| **类型加权** | 10分 | 固定类型优先 | 简单高效 | 缺乏动态调整 |

**总分**: 0-100分  
**优点**: 计算快速（<100ms）、可解释性强  
**缺点**: 缺乏语义理解、无法捕获隐式关系

---

## 二、增强算法设计

### 2.1 多层次匹配模型

```
┌─────────────────────────────────────────┐
│  L1: 精确匹配层（现有4维度）           │  40%权重
├─────────────────────────────────────────┤
│  L2: 语义相似度层（嵌入向量）          │  30%权重
├─────────────────────────────────────────┤
│  L3: 知识图谱关系层（路径推理）        │  20%权重
├─────────────────────────────────────────┤
│  L4: 历史行为层（协同过滤）            │  10%权重
└─────────────────────────────────────────┘
```

### 2.2 L1: 精确匹配层（保持现有）

**改进点**:
1. **地域匹配升级**: 支持地名同义词（"锡林郭勒盟" ≈ "锡盟"）
2. **产品关联升级**: 引入产品分类树（"羊肉" → "畜产品" → "农产品"）
3. **关键词加权**: TF-IDF权重替代固定分值

```python
# 地域匹配改进
REGION_SYNONYMS = {
    "锡林郭勒盟": ["锡盟", "锡林郭勒"],
    "呼伦贝尔": ["呼伦贝尔市", "呼伦贝尔盟"],
    # ...
}

def enhanced_region_match(product_origin: str, element_region: str) -> float:
    # 精确匹配：40分
    if product_origin in element_region:
        return 40.0
    
    # 同义词匹配：35分
    for canonical, aliases in REGION_SYNONYMS.items():
        if product_origin in aliases and canonical in element_region:
            return 35.0
    
    # 上级地名匹配：25分（如"呼伦贝尔" vs "内蒙古"）
    if is_parent_region(product_origin, element_region):
        return 25.0
    
    return 0.0
```

### 2.3 L2: 语义相似度层（新增）

**目标**: 捕获隐式语义关联（"沙漠驼肉" ↔ "丝绸之路文化"）

**方案**: 使用中文语义模型计算产品描述与文化故事的相似度

```python
from sentence_transformers import SentenceTransformer

class SemanticMatcher:
    def __init__(self):
        # 使用中文预训练模型
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.element_embeddings = self._precompute_embeddings()
    
    def _precompute_embeddings(self):
        """预计算所有文化元素的嵌入向量"""
        elements = load_cultural_elements()
        texts = [
            f"{e['name']} {e['story'][:200]} {' '.join(e['keywords'])}"
            for e in elements
        ]
        return self.model.encode(texts)
    
    def compute_similarity(self, product_info: Dict) -> List[Tuple[int, float]]:
        """计算产品与所有元素的语义相似度"""
        product_text = f"{product_info['name']} {product_info.get('description', '')} {' '.join(product_info.get('keywords', []))}"
        
        product_embedding = self.model.encode([product_text])[0]
        
        # 余弦相似度
        similarities = cosine_similarity(
            product_embedding.reshape(1, -1),
            self.element_embeddings
        )[0]
        
        # 转换为0-30分
        return [(i, sim * 30) for i, sim in enumerate(similarities)]
```

**性能优化**:
- 元素嵌入预计算（启动时加载）
- 批量计算（GPU加速）
- 缓存热点产品查询

**预期效果**:
- "沙漠驼肉" → "丝绸之路文化"（语义相似度 0.72 → 21.6分）
- "草原羊肉" → "游牧文化"（语义相似度 0.81 → 24.3分）

### 2.4 L3: 知识图谱关系层（核心创新）

#### 图谱Schema设计

```
节点类型:
┌──────────────┬──────────────────────────────┐
│ 节点类型     │ 属性                         │
├──────────────┼──────────────────────────────┤
│ Product      │ id, name, category, origin   │
│ CulturalElement │ id, name, type, story     │
│ Region       │ id, name, level, parent      │
│ Category     │ id, name, parent             │
│ Keyword      │ id, term, frequency          │
│ Scenario     │ id, name, description        │
└──────────────┴──────────────────────────────┘

关系类型:
┌──────────────┬─────────┬──────────────┬────────┐
│ 关系         │ 起点    │ 终点         │ 权重   │
├──────────────┼─────────┼──────────────┼────────┤
│ ORIGIN_IN    │ Product │ Region       │ 1.0    │
│ BELONGS_TO   │ Product │ Category     │ 1.0    │
│ HAS_ELEMENT  │ Product │ CulturalElement│ [0,1]│
│ LOCATED_IN   │ CulturalElement │ Region │ 1.0 │
│ HAS_TYPE     │ CulturalElement │ Category │ 1.0│
│ TAGGED_WITH  │ CulturalElement │ Keyword  │ TF-IDF│
│ SUITABLE_FOR │ CulturalElement │ Scenario │ [0,1]│
│ SYNONYM_OF   │ Keyword │ Keyword      │ 1.0    │
│ PARENT_OF    │ Region  │ Region       │ 1.0    │
└──────────────┴─────────┴──────────────┴────────┘
```

#### 图谱查询示例

**查询1**: 找到与产品关联最紧密的文化元素（1-2跳路径）

```cypher
// Neo4j Cypher查询
MATCH (p:Product {id: $product_id})-[:ORIGIN_IN]->(r:Region)
      <-[:LOCATED_IN]-(e:CulturalElement)
RETURN e, 
       1.0 as region_score

UNION

MATCH (p:Product {id: $product_id})-[:BELONGS_TO]->(c:Category)
      <-[:HAS_TYPE]-(e:CulturalElement)
RETURN e, 
       0.8 as category_score

UNION

MATCH (p:Product)-[:TAGGED_WITH]->(k:Keyword)
      <-[:TAGGED_WITH]-(e:CulturalElement)
RETURN e, 
       0.6 * count(k) as keyword_score

ORDER BY region_score + category_score + keyword_score DESC
LIMIT 10
```

**查询2**: 多跳关系推理（发现隐式关联）

```cypher
// 找到通过共享关键词关联的元素（2跳）
MATCH (p:Product)-[:TAGGED_WITH]->(k:Keyword)<-[:SYNONYM_OF]-(k2:Keyword)
      <-[:TAGGED_WITH]-(e:CulturalElement)
WHERE NOT (p)-[:HAS_ELEMENT]->(e)
RETURN e, 
       count(DISTINCT k) + count(DISTINCT k2) as connection_strength
ORDER BY connection_strength DESC
LIMIT 5
```

**查询3**: 场景导向推荐

```cypher
// 为"品牌故事"场景推荐最合适的文化元素
MATCH (p:Product {id: $product_id})-[:ORIGIN_IN]->(r:Region)
      <-[:LOCATED_IN]-(e:CulturalElement)-[:SUITABLE_FOR]->(s:Scenario {name: "品牌故事"})
RETURN e, 
       e.story as story,
       s.name as scenario
ORDER BY (e)-[:SUITABLE_FOR]->(s).score DESC
LIMIT 3
```

#### Python实现（使用NetworkX）

```python
import networkx as nx
from typing import List, Dict, Tuple

class CulturalKnowledgeGraph:
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self._build_graph()
    
    def _build_graph(self):
        """从数据库构建知识图谱"""
        # 加载节点
        products = load_products()
        elements = load_cultural_elements()
        regions = load_regions()
        keywords = load_keywords()
        
        # 添加节点
        for p in products:
            self.graph.add_node(f"product_{p['id']}", type="Product", **p)
        
        for e in elements:
            self.graph.add_node(f"element_{e['id']}", type="CulturalElement", **e)
        
        for r in regions:
            self.graph.add_node(f"region_{r['id']}", type="Region", **r)
        
        for k in keywords:
            self.graph.add_node(f"keyword_{k['id']}", type="Keyword", **k)
        
        # 添加边
        for p in products:
            # Product -> Region
            self.graph.add_edge(
                f"product_{p['id']}", 
                f"region_{p['origin_id']}", 
                relation="ORIGIN_IN",
                weight=1.0
            )
            
            # Product -> Keyword
            for kw in p.get('keywords', []):
                self.graph.add_edge(
                    f"product_{p['id']}",
                    f"keyword_{kw['id']}",
                    relation="TAGGED_WITH",
                    weight=kw.get('tfidf', 0.5)
                )
        
        for e in elements:
            # CulturalElement -> Region
            self.graph.add_edge(
                f"element_{e['id']}",
                f"region_{e['origin_region_id']}",
                relation="LOCATED_IN",
                weight=1.0
            )
            
            # CulturalElement -> Keyword
            for kw in e.get('keywords', []):
                self.graph.add_edge(
                    f"element_{e['id']}",
                    f"keyword_{kw['id']}",
                    relation="TAGGED_WITH",
                    weight=kw.get('tfidf', 0.5)
                )
    
    def find_related_elements(
        self, 
        product_id: int, 
        max_hops: int = 2,
        top_k: int = 10
    ) -> List[Tuple[int, float, List[str]]]:
        """
        找到与产品相关的文化元素
        
        Returns:
            List[(element_id, score, path)]
        """
        product_node = f"product_{product_id}"
        element_nodes = [
            n for n, attr in self.graph.nodes(data=True)
            if attr['type'] == "CulturalElement"
        ]
        
        results = []
        
        for element_node in element_nodes:
            try:
                # 找到最短路径
                path = nx.shortest_path(
                    self.graph, 
                    product_node, 
                    element_node
                )
                
                if len(path) - 1 <= max_hops:
                    # 计算路径得分
                    score = self._calculate_path_score(path)
                    
                    element_id = int(element_node.split('_')[1])
                    results.append((element_id, score, path))
            
            except nx.NetworkXNoPath:
                continue
        
        # 按得分排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def _calculate_path_score(self, path: List[str]) -> float:
        """计算路径得分"""
        if len(path) == 1:
            return 0.0
        
        total_score = 0.0
        path_length = len(path) - 1
        
        # 路径长度惩罚
        length_penalty = 1.0 / path_length
        
        # 遍历路径上的边
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            
            # 获取边权重
            edges = self.graph.get_edge_data(u, v)
            if edges:
                # 取最大权重边
                max_weight = max(
                    edge['weight'] 
                    for edge in edges.values()
                )
                total_score += max_weight
        
        # 归一化到0-20分
        return (total_score / path_length) * length_penalty * 20
```

### 2.5 L4: 历史行为层（新增）

**目标**: 基于用户行为优化推荐（协同过滤）

**方案**: 记录用户选择的产品-元素对，构建偏好矩阵

```python
class CollaborativeFilter:
    def __init__(self, db: Session):
        self.db = db
        self.user_item_matrix = self._build_matrix()
    
    def _build_matrix(self):
        """构建用户-元素偏好矩阵"""
        # 从历史记录构建
        # user_item_matrix[user_id][element_id] = score
        pass
    
    def get_user_preference_boost(
        self, 
        user_id: int, 
        element_id: int
    ) -> float:
        """获取用户偏好加成（0-10分）"""
        # 基于协同过滤计算
        # 如果该用户曾选择过类似元素，给予加分
        pass
```

---

## 三、综合评分公式

```python
def intelligent_match(product_info: Dict, user_id: Optional[int] = None) -> List[Dict]:
    """智能匹配算法主函数"""
    
    # L1: 精确匹配（40%）
    l1_scores = enhanced_exact_match(product_info)  # 0-100分
    
    # L2: 语义相似度（30%）
    semantic_matcher = SemanticMatcher()
    l2_scores = semantic_matcher.compute_similarity(product_info)  # 0-30分
    
    # L3: 知识图谱（20%）
    kg = CulturalKnowledgeGraph()
    l3_scores = kg.find_related_elements(product_info['id'])  # 0-20分
    
    # L4: 历史行为（10%）
    if user_id:
        cf = CollaborativeFilter()
        l4_scores = cf.get_user_preference_boost(user_id, ...)  # 0-10分
    else:
        l4_scores = [0] * len(l1_scores)
    
    # 综合评分
    final_scores = []
    for element_id in all_elements:
        score = (
            l1_scores[element_id] * 0.4 +
            l2_scores[element_id] * 0.3 +
            l3_scores[element_id] * 0.2 +
            l4_scores[element_id] * 0.1
        )
        
        final_scores.append({
            "element_id": element_id,
            "score": score,
            "breakdown": {
                "exact_match": l1_scores[element_id],
                "semantic": l2_scores[element_id],
                "knowledge_graph": l3_scores[element_id],
                "user_preference": l4_scores[element_id]
            }
        })
    
    # 排序并返回Top-K
    final_scores.sort(key=lambda x: x["score"], reverse=True)
    return final_scores[:10]
```

---

## 四、性能优化策略

### 4.1 缓存策略

```python
from functools import lru_cache
import redis

class MatchCache:
    def __init__(self):
        self.redis_client = redis.Redis()
        self.local_cache = {}
    
    @lru_cache(maxsize=1000)
    def get_cached_match(self, product_id: int) -> Optional[List[Dict]]:
        """获取缓存的匹配结果"""
        # L1: 内存缓存（毫秒级）
        if product_id in self.local_cache:
            return self.local_cache[product_id]
        
        # L2: Redis缓存（10ms级）
        cached = self.redis_client.get(f"match:{product_id}")
        if cached:
            return json.loads(cached)
        
        return None
    
    def set_cache(self, product_id: int, results: List[Dict], ttl: int = 3600):
        """设置缓存"""
        # 双层缓存
        self.local_cache[product_id] = results
        self.redis_client.setex(
            f"match:{product_id}",
            ttl,
            json.dumps(results, ensure_ascii=False)
        )
```

### 4.2 预计算索引

```python
# 启动时构建反向索引
KEYWORD_TO_ELEMENTS = {}  # keyword -> [element_ids]
REGION_TO_ELEMENTS = {}   # region_id -> [element_ids]

def build_inverted_index():
    elements = load_cultural_elements()
    
    for element in elements:
        # 关键词索引
        for kw in element['keywords']:
            if kw not in KEYWORD_TO_ELEMENTS:
                KEYWORD_TO_ELEMENTS[kw] = []
            KEYWORD_TO_ELEMENTS[kw].append(element['id'])
        
        # 地域索引
        region_id = element['origin_region_id']
        if region_id not in REGION_TO_ELEMENTS:
            REGION_TO_ELEMENTS[region_id] = []
        REGION_TO_ELEMENTS[region_id].append(element['id'])
```

### 4.3 批量计算

```python
def batch_match(product_ids: List[int]) -> Dict[int, List[Dict]]:
    """批量匹配（提升吞吐量）"""
    # 批量加载产品信息
    products = load_products_batch(product_ids)
    
    # 批量计算语义相似度（GPU加速）
    semantic_scores = semantic_matcher.batch_compute(products)
    
    # 并行处理
    from concurrent.futures import ThreadPoolExecutor
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(intelligent_match, p): p['id']
            for p in products
        }
        
        results = 
        for future in futures:
            product_id = futures[future]
            results[product_id] = future.result()
    
    return results
```

---

## 五、评估指标

### 5.1 准确性指标

| 指标 | 定义 | 目标值 |
|------|------|--------|
| **Top-1准确率** | 第1个推荐被采纳的比例 | ≥60% |
| **Top-3准确率** | 前3个推荐中有被采纳的比例 | ≥85% |
| **MRR** | Mean Reciprocal Rank | ≥0.7 |
| **NDCG@10** | Normalized DCG | ≥0.75 |

### 5.2 性能指标

| 指标 | 目标值 | 备注 |
|------|--------|------|
| **平均响应时间** | <200ms | 单次匹配 |
| **批量吞吐量** | >100 QPS | 10产品批量 |
| **缓存命中率** | >70% | Redis+内存 |
| **GPU利用率** | >60% | 语义计算 |

### 5.3 业务指标

| 指标 | 定义 | 目标值 |
|------|------|--------|
| **自动匹配率** | 评分≥70分的产品比例 | ≥70% |
| **人工干预率** | 需要人工挑选元素的比例 | <15% |
| **用户满意度** | 采纳推荐的比例 | ≥80% |

---

## 六、实施路线图

### Phase 1: 增强现有算法（1周）
- ✅ 地域匹配升级（同义词、层级）
- ✅ 关键词TF-IDF加权
- ✅ 反向索引构建
- ✅ 缓存系统

### Phase 2: 语义相似度（1周）
- 集成sentence-transformers
- 预计算元素嵌入
- GPU加速推理
- A/B测试验证

### Phase 3: 知识图谱（2周）
- NetworkX图谱构建
- 多跳查询实现
- 路径得分算法
- 图谱可视化

### Phase 4: 协同过滤（1周）
- 用户行为数据收集
- 矩阵分解模型
- 在线更新机制

### Phase 5: 生产部署（1周）
- 性能压测
- 监控告警
- 灰度发布

---

**下一步**: 实现增强算法和知识图谱构建代码
