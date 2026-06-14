# 知识图谱设计
## Knowledge Graph Design v1.0

**文档版本**: 1.0  
**创建日期**: 2026-06-11  
**实施阶段**: Sprint 2 (Week 3-4)

---

## 一、知识图谱概述

### 1.1 核心价值

- **产品文化深度关联**: 建立产品→产地→文化元素的完整链路
- **智能推荐**: 为产品自动推荐相关文化元素
- **故事自动生成**: 基于图谱数据生成品牌故事
- **差异化竞争**: 全国首个草原文化知识图谱

### 1.2 实施策略

**Phase 1 (Sprint 2)**: MySQL关系型实现
- 理由: 快速上线，开发成本低，团队熟悉
- 局限: 复杂图查询性能差

**Phase 2 (Sprint 4-5)**: 可选升级Neo4j
- 条件: 关系查询>3层 或 性能P95>2s
- 收益: 图算法支持，查询性能提升10倍

---

## 二、数据模型设计

### 2.1 实体类型

| 实体 | 属性 | 关系 | 说明 |
|-----|------|------|------|
| 产品 (Product) | id, name, category_id, origin_id, description, cultural_tags | 属于→品类<br>产自→产地 | 核心实体 |
| 产地 (Origin) | id, name, region, description, latitude, longitude | 孕育→文化元素 | 地理实体 |
| 品类 (Category) | id, name, parent_id, level | 父子关系（树形） | 分类实体 |
| 文化元素 (CulturalElement) | id, name, type, story, origin_region, hot_score | 关联→产地 | 知识实体 |
| 品牌 (Brand) | id, name, origin_id | 经营→产品 | 商业实体 |

### 2.2 关系类型

```
产品 --[FROM_ORIGIN]--> 产地
产地 --[HAS_CULTURE]--> 文化元素
产品 --[BELONGS_TO]--> 品类
品牌 --[SELLS]--> 产品
产品 --[RELATED_TO]--> 文化元素 (直接关联，relevance_score)
```

### 2.3 ER图

```
┌─────────┐       ┌─────────┐       ┌──────────────┐
│  品牌    │──1:N──│  产品    │──N:1──│   产地        │
│ Brand   │       │ Product │       │   Origin     │
└─────────┘       └────┬────┘       └──────┬───────┘
                       │                   │
                    N:1│                   │1:N
                       │                   │
                  ┌────▼────┐         ┌────▼─────────┐
                  │  品类    │         │  文化元素     │
                  │Category │         │CulturalElem  │
                  └─────────┘         └──────────────┘
                       │                      ▲
                       └──────────N:N─────────┘
                         (product_culture_links)
```

---

## 三、15个文化元素详细定义

### 3.1 节日类 (Festival)

| 名称 | 产地关联 | 时间 | 故事梗概 (200-300字) |
|-----|---------|------|---------------------|
| **那达慕** | 锡林郭勒/呼伦贝尔 | 农历六月初四 | 蒙古族传统盛会，"娱乐"或"游戏"之意。包含摔跤、赛马、射箭"男儿三艺"。起源于成吉思汗时期军事演练，后演变为庆祝丰收的民族节日。锡林郭勒是那达慕主场地，每年吸引数万牧民参加。 |
| **敖包祭祀** | 内蒙古全域 | 农历五月十三 | 蒙古族祭祀天地神灵的仪式。"敖包"意为"堆子"，用石头堆成。祭祀时献哈达、诵经、洒奶酒，祈求风调雨顺、牲畜兴旺。敖包是草原的地标，也是牧民的精神寄托。 |
| **白月节** | 内蒙古全域 | 农历正月初一 | 蒙古族春节，又称"查干萨日"（白色的节日）。家族团聚，穿新衣，吃手把肉、奶制品。长辈向晚辈发红包，晚辈向长辈献哈达。象征纯洁吉祥的开始。 |

### 3.2 技艺类 (Skill)

| 名称 | 产地关联 | 传承状态 | 故事梗概 |
|-----|---------|---------|---------|
| **蒙古族摔跤** | 锡林郭勒 | 活态传承 | 那达慕三艺之首，穿特制摔跤服"卓得戈"，规则独特无时间限制。冠军被称为"搏克手"（摔跤手），享有崇高地位。培养勇敢、力量、技巧。 |
| **赛马驯马** | 呼伦贝尔/锡林郭勒 | 活态传承 | 蒙古族视马为"天之骄子"，6岁儿童即学骑马。赛马分速度赛和走马赛。驯马讲究与马建立信任，训练周期长达2-3年。马是牧民生活和战斗的伙伴。 |
| **皮具制作** | 呼伦贝尔 | 濒危 | 用牛羊皮制作马鞍、皮靴、皮囊。工艺包括鞣制、缝合、雕花。皮具耐用防寒，是游牧生活必需品。现代工业冲击下，手工艺人稀少。 |
| **蒙古族刺绣** | 通辽/赤峰 | 活态传承 | 在服饰、靴子、帽子上刺绣吉祥图案（云纹、火纹、盘肠）。色彩鲜艳，寓意美好。年轻女性必备技能，绣品常作嫁妆。 |

### 3.3 美食类 (Food)

| 名称 | 产地关联 | 制作方式 | 文化意义 |
|-----|---------|---------|---------|
| **手把肉** | 内蒙古全域 | 清水煮羊肉，保留原味，手抓食用 | 待客最高礼遇，体现游牧民族豪爽性格。吃法有"三吃"：白食（不蘸料）、红食（蘸料）、汤食。 |
| **蒙古族奶茶** | 内蒙古全域 | 砖茶+牛奶+盐，煮制3-5分钟 | 日常饮品，早晨第一件事。咸味解腻，温暖驱寒。"宁可一日无食，不可一日无茶"。 |
| **马奶酒** | 锡林郭勒 | 马奶发酵7-10天，酒精度2-3度 | 珍贵饮品，仅夏季制作。清凉解暑，助消化。敬客时唱敬酒歌，一饮而尽表尊重。 |

### 3.4 故事类 (Story)

| 名称 | 相关地域 | 历史时期 | 故事梗概 |
|-----|---------|---------|---------|
| **敕勒川诗篇** | 呼和浩特 | 南北朝 | "敕勒川，阴山下，天似穹庐，笼盖四野。天苍苍，野茫茫，风吹草低见牛羊。"描绘北方草原壮美景色，流传千年。 |
| **昭君出塞** | 呼和浩特 | 汉代 | 王昭君为汉匈和亲远嫁匈奴，促进民族融合。昭君墓成呼和浩特地标，象征和平友好。 |
| **成吉思汗西征** | 锡林郭勒 | 13世纪 | 成吉思汗统一蒙古各部，建立横跨欧亚的大帝国。锡林郭勒是出征起点，蒙古马和草原培养了铁骑。 |

### 3.5 习俗类 (Custom)

| 名称 | 适用场景 | 礼仪流程 |
|-----|---------|---------|
| **献哈达礼仪** | 迎宾/婚礼/拜年 | 双手捧哈达，平齐额头，鞠躬献上。接受者双手接过挂脖上或手臂。白色哈达最隆重。 |
| **敬酒歌** | 宴会/庆典 | 主人唱敬酒歌，客人接酒碗，用无名指蘸酒向天、地、炉灶弹三下（祭天地祖先），一饮而尽。 |

---

## 四、MySQL实现方案 (Phase 1)

### 4.1 表结构设计

```sql
-- 产品表
CREATE TABLE products (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  category_id BIGINT,
  origin_id BIGINT,
  description TEXT,
  images JSONB,  -- ['url1', 'url2']
  selling_points JSONB,  -- ['特点1', '特点2']
  cultural_tags JSONB,  -- ['那达慕', '手把肉']
  status VARCHAR(20) DEFAULT 'active',
  created_by BIGINT,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (category_id) REFERENCES categories(id),
  FOREIGN KEY (origin_id) REFERENCES origins(id),
  INDEX idx_category (category_id),
  INDEX idx_origin (origin_id)
);

-- 产地表
CREATE TABLE origins (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  region VARCHAR(100),  -- 呼伦贝尔/锡林郭勒/...
  description TEXT,
  latitude DECIMAL(10,7),
  longitude DECIMAL(10,7),
  created_at TIMESTAMP DEFAULT NOW()
);

-- 文化元素表
CREATE TABLE cultural_elements (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL,
  type VARCHAR(50) NOT NULL,  -- festival/skill/food/story/custom/craft
  story TEXT NOT NULL,
  origin_region VARCHAR(100),
  hot_score INT DEFAULT 50,  -- 0-100热度分
  metadata JSONB,  -- {time, status, etc}
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_type (type),
  INDEX idx_hot_score (hot_score DESC)
);

-- 产品-文化关联表
CREATE TABLE product_culture_links (
  product_id BIGINT NOT NULL,
  culture_id BIGINT NOT NULL,
  relevance_score DECIMAL(3,2) DEFAULT 0.50,  -- 0.00-1.00
  link_type VARCHAR(50) DEFAULT 'manual',  -- manual/auto
  created_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (product_id, culture_id),
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
  FOREIGN KEY (culture_id) REFERENCES cultural_elements(id),
  INDEX idx_relevance (relevance_score DESC)
);

-- 产地-文化关联表
CREATE TABLE origin_culture_links (
  origin_id BIGINT NOT NULL,
  culture_id BIGINT NOT NULL,
  PRIMARY KEY (origin_id, culture_id),
  FOREIGN KEY (origin_id) REFERENCES origins(id),
  FOREIGN KEY (culture_id) REFERENCES cultural_elements(id)
);
```

### 4.2 溯源查询实现

```sql
-- 产品文化溯源查询
WITH product_info AS (
  SELECT p.id, p.name, p.origin_id, p.cultural_tags
  FROM products p
  WHERE p.id = :product_id
),
origin_info AS (
  SELECT o.id, o.name, o.region, o.description
  FROM origins o
  JOIN product_info pi ON o.id = pi.origin_id
),
direct_cultures AS (
  -- 产品直接关联的文化元素
  SELECT ce.*, pcl.relevance_score, 'direct' AS link_level
  FROM cultural_elements ce
  JOIN product_culture_links pcl ON ce.id = pcl.culture_id
  WHERE pcl.product_id = :product_id
),
origin_cultures AS (
  -- 产地关联的文化元素
  SELECT ce.*, 0.70 AS relevance_score, 'origin' AS link_level
  FROM cultural_elements ce
  JOIN origin_culture_links ocl ON ce.id = ocl.culture_id
  JOIN product_info pi ON ocl.origin_id = pi.origin_id
)
SELECT 
  pi.name AS product_name,
  oi.name AS origin_name,
  oi.description AS origin_desc,
  JSON_AGG(
    JSON_BUILD_OBJECT(
      'id', COALESCE(dc.id, oc.id),
      'name', COALESCE(dc.name, oc.name),
      'type', COALESCE(dc.type, oc.type),
      'story', COALESCE(dc.story, oc.story),
      'link_level', COALESCE(dc.link_level, oc.link_level),
      'relevance_score', COALESCE(dc.relevance_score, oc.relevance_score)
    ) ORDER BY COALESCE(dc.relevance_score, oc.relevance_score) DESC
  ) AS cultures
FROM product_info pi
JOIN origin_info oi ON 1=1
LEFT JOIN direct_cultures dc ON 1=1
LEFT JOIN origin_cultures oc ON 1=1
GROUP BY pi.name, oi.name, oi.description;
```

### 4.3 推荐算法实现

```python
class RecommendEngine:
    async def recommend_cultures(
        self, 
        product_id: int, 
        top_n: int = 3
    ) -> List[Dict]:
        """为产品推荐文化元素"""
        # 1. 获取产品产地
        product = await self.db.get(Product, product_id)
        
        # 2. 查询该产地所有文化元素
        query = """
            SELECT ce.*, pcl.relevance_score
            FROM cultural_elements ce
            JOIN origin_culture_links ocl ON ce.id = ocl.culture_id
            LEFT JOIN product_culture_links pcl 
              ON ce.id = pcl.culture_id AND pcl.product_id = :product_id
            WHERE ocl.origin_id = :origin_id
            ORDER BY 
              COALESCE(pcl.relevance_score, 0.5) DESC,
              ce.hot_score DESC
            LIMIT :top_n
        """
        
        results = await self.db.execute(
            text(query),
            {"product_id": product_id, "origin_id": product.origin_id, "top_n": top_n}
        )
        
        return [dict(row) for row in results]
```

---

## 五、Neo4j升级方案 (Phase 2, 可选)

### 5.1 节点类型映射

```cypher
// 产品节点
(:Product {
  id: int,
  name: string,
  category: string,
  cultural_tags: [string]
})

// 产地节点
(:Origin {
  id: int,
  name: string,
  region: string,
  latitude: float,
  longitude: float
})

// 文化元素节点
(:CulturalElement {
  id: int,
  name: string,
  type: string,
  story: string,
  hot_score: int
})
```

### 5.2 关系类型映射

```cypher
(:Product)-[:FROM_ORIGIN {since: date}]->(:Origin)
(:Origin)-[:HAS_CULTURE {strength: float}]->(:CulturalElement)
(:Product)-[:RELATED_TO {relevance: float}]->(:CulturalElement)
```

### 5.3 溯源查询优化

```cypher
// Neo4j版本 - 更简洁高效
MATCH (p:Product {id: $productId})
      -[:FROM_ORIGIN]->(o:Origin)
      -[:HAS_CULTURE]->(c:CulturalElement)
OPTIONAL MATCH (p)-[r:RELATED_TO]->(c)
RETURN p, o, 
       COLLECT({
         culture: c,
         link_level: CASE WHEN r IS NOT NULL THEN 'direct' ELSE 'origin' END,
         relevance: COALESCE(r.relevance, 0.7)
       }) AS cultures
ORDER BY relevance DESC
```

### 5.4 迁移策略

**第1步: 双写（Sprint 4 Week 1-2）**
```python
async def create_product(product_data: Dict):
    # 写入PostgreSQL
    pg_product = await pg_repo.create(product_data)
    
    # 同步写入Neo4j
    await neo4j_repo.create_node("Product", product_data)
    
    return pg_product
```

**第2步: 读流量切换（Sprint 5 Week 1）**
```python
# 配置开关
USE_NEO4J = os.getenv("USE_NEO4J", "false") == "true"

async def trace_product(product_id: int):
    if USE_NEO4J:
        return await neo4j_trace_engine.trace(product_id)
    else:
        return await pg_trace_engine.trace(product_id)
```

**第3步: 下线PostgreSQL图谱表（Sprint 5 Week 2）**
- 停止双写
- 删除`product_culture_links`, `origin_culture_links`表
- 保留`products`, `origins`, `cultural_elements`表（基础数据）

---

## 六、数据初始化

### 6.1 文化元素数据导入

```python
# backend/scripts/init_cultural_elements.py

CULTURAL_DATA = [
    {
        "name": "那达慕",
        "type": "festival",
        "story": "蒙古族传统盛会，"娱乐"或"游戏"之意...",
        "origin_region": "锡林郭勒",
        "hot_score": 95,
        "metadata": {"time": "农历六月初四", "status": "活态传承"}
    },
    # ... 其余14个
]

async def init_cultural_elements():
    async with get_db() as db:
        for data in CULTURAL_DATA:
            element = CulturalElement(**data)
            db.add(element)
        await db.commit()
```

### 6.2 产品-文化关联初始化

```python
# 示例：锡林郭勒羊肉关联文化元素
PRODUCT_CULTURE_LINKS = [
    {"product_name": "锡林郭勒羊肉", "culture_name": "那达慕", "relevance": 0.95},
    {"product_name": "锡林郭勒羊肉", "culture_name": "手把肉", "relevance": 0.90},
    {"product_name": "锡林郭勒羊肉", "culture_name": "敖包祭祀", "relevance": 0.85},
]
```

---

## 七、验收标准

| 指标 | 目标值 | 测试方法 |
|-----|--------|---------|
| 文化元素数量 | 15个 | 数据库查询 |
| 溯源路径完整率 | 100% | 抽样测试 |
| 溯源查询响应时间 | <500ms | 压测 |
| 推荐准确率 | ≥85% | 人工评审 |

---

**文档结束**

> 知识图谱是蒙智云的核心差异化能力，需持续丰富文化元素库。
